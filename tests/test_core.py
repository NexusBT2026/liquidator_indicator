import pytest
import pandas as pd
from liquidator_indicator import Liquidator


def test_cluster_basic():
    L = Liquidator('BTC', cutoff_hours=None)  # Disable cutoff for test data
    sample = [
        {'timestamp':'2026-01-31T12:00:00Z','side':'long','price':80000,'usd_value':500000},
        {'timestamp':'2026-01-31T12:01:00Z','side':'long','price':79960,'usd_value':300000},
        {'timestamp':'2026-01-31T12:05:00Z','side':'short','price':78000,'usd_value':200000},
    ]
    L.ingest_liqs(sample)
    z = L.compute_zones(window_minutes=120, pct_merge=0.005)
    assert not z.empty
    assert 'strength' in z.columns


# ---------------------------------------------------------------------------
# Cascade chain detection tests
# ---------------------------------------------------------------------------

def _make_liq(*, prices, current_price=80000.0, pct_merge=0.005):
    """Helper: ingest a list of prices as long liquidations and return zones."""
    L = Liquidator('BTC', cutoff_hours=None)
    sample = [
        {
            'timestamp': f'2026-01-31T12:0{i}:00Z',
            'side': 'long',
            'price': p,
            'usd_value': 1_000_000,
        }
        for i, p in enumerate(prices)
    ]
    L.ingest_liqs(sample)
    zones = L.compute_zones(window_minutes=120, pct_merge=pct_merge)
    return L, zones


def test_cascade_columns_present():
    """add_cascade_analysis() must add the three required columns."""
    L, zones = _make_liq(prices=[79000, 78500, 78000, 77000])
    result = L.add_cascade_analysis(zones, current_price=80000.0)
    assert 'cascade_probability' in result.columns
    assert 'cascade_chain_length' in result.columns
    assert 'cascade_target_price' in result.columns


def test_cascade_probability_range():
    """cascade_probability must be in [0, 100] for all zones."""
    L, zones = _make_liq(prices=[79000, 78500, 78000, 77500])
    result = L.add_cascade_analysis(zones, current_price=80000.0)
    assert (result['cascade_probability'] >= 0).all()
    assert (result['cascade_probability'] <= 100).all()


def test_cascade_chain_length_minimum():
    """Every zone is at least a chain of length 1 (itself)."""
    L, zones = _make_liq(prices=[79000, 78500, 78000])
    result = L.add_cascade_analysis(zones, current_price=80000.0)
    assert (result['cascade_chain_length'] >= 1).all()


def test_cascade_closer_zone_higher_probability():
    """A zone closer to current_price should have higher cascade_probability."""
    prices = [79500, 75000]   # 79500 is much closer to 80000 than 75000
    L, zones = _make_liq(prices=prices, pct_merge=0.02)
    result = L.add_cascade_analysis(zones, current_price=80000.0)
    close_prob = result.loc[result['price_mean'].sub(79500).abs().idxmin(), 'cascade_probability']
    far_prob   = result.loc[result['price_mean'].sub(75000).abs().idxmin(), 'cascade_probability']
    assert close_prob > far_prob, "Closer zone should have higher cascade probability"


def test_cascade_chain_links_tight_zones():
    """Zones within chain_gap_pct of each other should form a chain longer than 1."""
    # Prices ~0.6% apart: too far to merge at default pct_merge (0.3%) but well
    # inside the 1.5% chain_gap_pct, so they should link into a multi-zone chain.
    prices = [79000, 78500, 78000]
    L, zones = _make_liq(prices=prices, pct_merge=0.003)
    result = L.add_cascade_analysis(zones, current_price=80000.0, chain_gap_pct=0.015)
    max_chain = result['cascade_chain_length'].max()
    assert max_chain > 1, "Tight zones should form a multi-zone chain"


def test_cascade_funding_bias_increases_probability():
    """High positive funding rate should increase cascade_probability for zones below price."""
    L, zones = _make_liq(prices=[79500])
    without_funding = L.add_cascade_analysis(zones, current_price=80000.0, funding_rate=0.0)
    with_funding    = L.add_cascade_analysis(zones, current_price=80000.0, funding_rate=0.01)
    prob_no_funding = without_funding['cascade_probability'].iloc[0]
    prob_funding    = with_funding['cascade_probability'].iloc[0]
    assert prob_funding >= prob_no_funding, "Positive funding should boost downward cascade probability"


def test_cascade_empty_zones_returns_empty():
    """Passing an empty DataFrame should return an empty DataFrame without errors."""
    L = Liquidator('BTC', cutoff_hours=None)
    result = L.add_cascade_analysis(pd.DataFrame(), current_price=80000.0)
    assert result.empty


def test_cascade_invalid_price_adds_zero_probability():
    """current_price <= 0 should add zero probability columns without raising."""
    L, zones = _make_liq(prices=[79000, 78000])
    result = L.add_cascade_analysis(zones, current_price=0.0)
    assert 'cascade_probability' in result.columns
    assert (result['cascade_probability'] == 0).all()


def test_cascade_target_price_in_correct_direction():
    """cascade_target_price for zones below current_price should be <= zone price."""
    prices = [79000, 78500, 78000]
    L, zones = _make_liq(prices=prices, pct_merge=0.015)
    result = L.add_cascade_analysis(zones, current_price=80000.0, chain_gap_pct=0.015)
    for _, row in result.iterrows():
        if row['price_mean'] < 80000.0:
            assert row['cascade_target_price'] <= row['price_mean'], (
                "Cascade target for a zone below price should not be above that zone"
            )


# ---------------------------------------------------------------------------
# Gravity model tests
# ---------------------------------------------------------------------------

def test_gravity_columns_present():
    """add_gravity_scores() must add gravity and gravity_rank columns."""
    L, zones = _make_liq(prices=[79000, 78000, 77000])
    result = L.add_gravity_scores(zones, current_price=80000.0)
    assert 'gravity' in result.columns
    assert 'gravity_rank' in result.columns


def test_gravity_non_negative():
    """Gravity values must all be >= 0."""
    L, zones = _make_liq(prices=[79000, 78000, 77000])
    result = L.add_gravity_scores(zones, current_price=80000.0)
    assert (result['gravity'] >= 0).all()


def test_gravity_closer_zone_higher_gravity():
    """A zone closer to current_price should have higher gravity (rank 1) than a far one."""
    # Two zones with equal liquidity; the closer one must win on gravity
    L = Liquidator('BTC', cutoff_hours=None)
    sample = [
        {'timestamp': '2026-01-31T12:00:00Z', 'side': 'long', 'price': 79500, 'usd_value': 1_000_000},
        {'timestamp': '2026-01-31T12:01:00Z', 'side': 'long', 'price': 75000, 'usd_value': 1_000_000},
    ]
    L.ingest_liqs(sample)
    zones = L.compute_zones(window_minutes=120, pct_merge=0.02)
    result = L.add_gravity_scores(zones, current_price=80000.0)
    top = result.loc[result['gravity_rank'] == 1, 'price_mean'].iloc[0]
    assert abs(top - 79500) < abs(top - 75000) or top == pytest.approx(79500, rel=0.02), \
        "Zone closer to current price should have gravity_rank == 1"


def test_gravity_larger_cluster_wins_over_smaller_equidistant():
    """For equal distances, the zone with more liquidity should rank higher."""
    L = Liquidator('BTC', cutoff_hours=None)
    # Place both zones at the same distance from current price (symmetrically)
    sample = [
        {'timestamp': '2026-01-31T12:00:00Z', 'side': 'long',  'price': 79000, 'usd_value': 5_000_000},
        {'timestamp': '2026-01-31T12:01:00Z', 'side': 'short', 'price': 81000, 'usd_value': 1_000_000},
    ]
    L.ingest_liqs(sample)
    zones = L.compute_zones(window_minutes=120, pct_merge=0.005)
    result = L.add_gravity_scores(zones, current_price=80000.0)
    top = result.loc[result['gravity_rank'] == 1, 'price_mean'].iloc[0]
    assert abs(top - 79000) < 200, "More liquid zone should have highest gravity"


def test_gravity_rank_is_unique_per_zone():
    """gravity_rank 1 should appear exactly once."""
    L, zones = _make_liq(prices=[79000, 78000, 77000, 76000])
    result = L.add_gravity_scores(zones, current_price=80000.0)
    assert (result['gravity_rank'] == 1).sum() == 1


def test_gravity_empty_zones_returns_empty():
    """Passing an empty DataFrame should return empty without errors."""
    L = Liquidator('BTC', cutoff_hours=None)
    result = L.add_gravity_scores(pd.DataFrame(), current_price=80000.0)
    assert result.empty


def test_gravity_invalid_price_returns_zero():
    """current_price <= 0 should add zero gravity without raising."""
    L, zones = _make_liq(prices=[79000, 78000])
    result = L.add_gravity_scores(zones, current_price=0.0)
    assert 'gravity' in result.columns
    assert (result['gravity'] == 0).all()


def test_get_gravity_target_returns_dict():
    """get_gravity_target() should return a dict with price_mean and gravity keys."""
    L, zones = _make_liq(prices=[79000, 78500, 78000])
    target = L.get_gravity_target(zones, current_price=80000.0)
    assert target is not None
    assert 'price_mean' in target
    assert 'gravity' in target
    assert 'gravity_rank' in target
    assert target['gravity_rank'] == 1


def test_get_gravity_target_empty_returns_none():
    """get_gravity_target() on an empty DataFrame should return None."""
    L = Liquidator('BTC', cutoff_hours=None)
    result = L.get_gravity_target(pd.DataFrame(), current_price=80000.0)
    assert result is None

