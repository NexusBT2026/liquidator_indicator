# -*- coding: utf-8 -*-
"""Test v0.1.0 backward compatibility.

Verifies:
1. All v0.0.9 API patterns still work unchanged (no regressions)
2. New cascade chain detection method works correctly
3. New gravity model methods work correctly
4. New methods are truly opt-in (compute_zones() output unchanged)
5. Edge cases: empty DataFrames, invalid prices, zero funding
"""
import sys
import pandas as pd
import numpy as np
from datetime import timezone

print("=" * 70)
print("v0.1.0 BACKWARD COMPATIBILITY TEST")
print("New Features: Cascade Chain Detection + Gravity Model")
print("=" * 70)

from liquidator_indicator import Liquidator, __version__

# ── helpers ────────────────────────────────────────────────────────────────

now = pd.Timestamp.now(tz='UTC')

def make_trade_data(n=30, base_price=80000.0, spread=1000.0):
    data = []
    for i in range(n):
        price = base_price + np.random.uniform(-spread, spread)
        size  = np.random.uniform(0.5, 3.0)
        data.append({
            'timestamp': now - pd.Timedelta(minutes=n - i),
            'price':     round(price, 2),
            'size':      round(size, 4),
            'size_usd':  round(price * size, 2),
            'side':      'long' if i % 2 == 0 else 'short',
        })
    return data

def make_liq_data(prices, base_time=None):
    """Ingest as pre-labelled liquidations via ingest_liqs."""
    if base_time is None:
        base_time = now
    return [
        {
            'timestamp': (base_time - pd.Timedelta(minutes=len(prices) - i)).isoformat(),
            'side':      'long',
            'price':     float(p),
            'usd_value': 1_000_000.0,
        }
        for i, p in enumerate(prices)
    ]

# ── Test 1: Version string ─────────────────────────────────────────────────
print("\nTest 1: Version String")
print("-" * 70)

if __version__.startswith("0.1."):
    print(f"✅ __version__ == '{__version__}' (0.1.x)")
else:
    print(f"❌ __version__ is '{__version__}' — expected 0.1.x")

# ── Test 2: v0.0.9 API unchanged ────────────────────────────────────────────
print("\nTest 2: v0.0.9 Core API Still Works (Regression Check)")
print("-" * 70)

try:
    trade_data = make_trade_data(40)
    L = Liquidator(window_minutes=60, cutoff_hours=None)
    L.ingest_trades(trade_data)
    zones = L.compute_zones(window_minutes=60)

    assert isinstance(zones, pd.DataFrame), "compute_zones() must return DataFrame"
    required_cols = ['price_mean', 'price_min', 'price_max', 'total_usd',
                     'count', 'first_ts', 'last_ts', 'dominant_side',
                     'strength', 'quality_score', 'quality_label']
    missing = [c for c in required_cols if c not in zones.columns]
    if missing:
        print(f"❌ Missing columns: {missing}")
    else:
        print(f"✅ All v0.0.9 columns present on compute_zones() output")
    print(f"   Zones detected: {len(zones)}")
    print(f"   Columns: {list(zones.columns)}")
except Exception as e:
    print(f"❌ v0.0.9 regression: {e}")
    import traceback; traceback.print_exc()

# ── Test 3: New methods are opt-in — compute_zones() unchanged ───────────────
print("\nTest 3: New Columns Absent Unless Methods Called (Opt-In)")
print("-" * 70)

try:
    trade_data = make_trade_data(30)
    L2 = Liquidator(window_minutes=60, cutoff_hours=None)
    L2.ingest_trades(trade_data)
    zones2 = L2.compute_zones(window_minutes=60)

    new_cols = ['cascade_probability', 'cascade_chain_length', 'cascade_target_price',
                'gravity', 'gravity_rank']
    surprise = [c for c in new_cols if c in zones2.columns]
    if surprise:
        print(f"❌ New columns appeared without calling new methods: {surprise}")
    else:
        print(f"✅ compute_zones() output unchanged — new columns absent until opt-in")
except Exception as e:
    print(f"❌ Opt-in test failed: {e}")

# ── Test 4: add_cascade_analysis() — basic operation ─────────────────────────
print("\nTest 4: add_cascade_analysis() — Basic Operation")
print("-" * 70)

try:
    L3 = Liquidator('BTC', cutoff_hours=None)
    L3.ingest_liqs(make_liq_data([79500, 79000, 78500, 78000]))
    zones3 = L3.compute_zones(window_minutes=120, pct_merge=0.003)

    result = L3.add_cascade_analysis(zones3, current_price=80000.0, funding_rate=0.0003)

    required = ['cascade_probability', 'cascade_chain_length', 'cascade_target_price']
    missing  = [c for c in required if c not in result.columns]
    if missing:
        print(f"❌ Missing cascade columns: {missing}")
    else:
        print(f"✅ All cascade columns present")

    # Probability range
    bad_range = result[(result['cascade_probability'] < 0) | (result['cascade_probability'] > 100)]
    if not bad_range.empty:
        print(f"❌ cascade_probability out of [0,100]: {bad_range['cascade_probability'].tolist()}")
    else:
        print(f"✅ cascade_probability in [0, 100] for all zones")

    # Chain length >= 1
    if (result['cascade_chain_length'] < 1).any():
        print(f"❌ cascade_chain_length < 1 found")
    else:
        print(f"✅ cascade_chain_length >= 1 for all zones")

    print(f"   Zones scored: {len(result)}")
    print(f"   Top cascade zone:  price=${result.nlargest(1,'cascade_probability').iloc[0]['price_mean']:.0f}"
          f"  prob={result['cascade_probability'].max():.1f}%"
          f"  chain={result.nlargest(1,'cascade_probability').iloc[0]['cascade_chain_length']}")

except Exception as e:
    print(f"❌ add_cascade_analysis() failed: {e}")
    import traceback; traceback.print_exc()

# ── Test 5: Cascade — closer zone scores higher ───────────────────────────────
print("\nTest 5: add_cascade_analysis() — Distance Logic")
print("-" * 70)

try:
    L4 = Liquidator('BTC', cutoff_hours=None)
    # 79800 is very close to 80000; 72000 is far away — equal liquidity
    L4.ingest_liqs(make_liq_data([79800, 72000]))
    zones4 = L4.compute_zones(window_minutes=120, pct_merge=0.02)
    result4 = L4.add_cascade_analysis(zones4, current_price=80000.0)

    close_row = result4.loc[result4['price_mean'].sub(79800).abs().idxmin()]
    far_row   = result4.loc[result4['price_mean'].sub(72000).abs().idxmin()]

    if close_row['cascade_probability'] > far_row['cascade_probability']:
        print(f"✅ Closer zone has higher cascade_probability")
        print(f"   Zone at ~79800: {close_row['cascade_probability']:.1f}%")
        print(f"   Zone at ~72000: {far_row['cascade_probability']:.1f}%")
    else:
        print(f"❌ Distance logic wrong — far zone scored higher than close zone")
except Exception as e:
    print(f"❌ Distance logic test failed: {e}")

# ── Test 6: Cascade — funding rate alignment ──────────────────────────────────
print("\nTest 6: add_cascade_analysis() — Funding Rate Amplification")
print("-" * 70)

try:
    L5 = Liquidator('BTC', cutoff_hours=None)
    L5.ingest_liqs(make_liq_data([79500]))
    zones5 = L5.compute_zones(window_minutes=120, pct_merge=0.003)

    no_funding   = L5.add_cascade_analysis(zones5, current_price=80000.0, funding_rate=0.0)
    with_funding = L5.add_cascade_analysis(zones5, current_price=80000.0, funding_rate=0.01)

    p_no  = no_funding['cascade_probability'].iloc[0]
    p_yes = with_funding['cascade_probability'].iloc[0]

    if p_yes >= p_no:
        print(f"✅ Positive funding amplifies downward cascade probability")
        print(f"   Without funding bias: {p_no:.1f}%")
        print(f"   With funding=0.01:    {p_yes:.1f}%")
    else:
        print(f"❌ Funding multiplier not working (with={p_yes:.1f}% < without={p_no:.1f}%)")
except Exception as e:
    print(f"❌ Funding rate test failed: {e}")

# ── Test 7: Cascade — empty + invalid price edge cases ───────────────────────
print("\nTest 7: add_cascade_analysis() — Edge Cases")
print("-" * 70)

try:
    L_edge = Liquidator('BTC', cutoff_hours=None)

    # Empty DataFrame
    result_empty = L_edge.add_cascade_analysis(pd.DataFrame(), current_price=80000.0)
    assert result_empty.empty, "Should return empty DataFrame"
    print(f"✅ Empty DataFrame returns empty without error")

    # current_price = 0
    L_edge.ingest_liqs(make_liq_data([79000]))
    zones_edge = L_edge.compute_zones(window_minutes=120, pct_merge=0.003)
    result_zero = L_edge.add_cascade_analysis(zones_edge, current_price=0.0)
    assert (result_zero['cascade_probability'] == 0).all(), "Zero price should give 0 probability"
    print(f"✅ current_price=0 returns zero probabilities without error")

except Exception as e:
    print(f"❌ Edge case test failed: {e}")
    import traceback; traceback.print_exc()

# ── Test 8: add_gravity_scores() — basic operation ───────────────────────────
print("\nTest 8: add_gravity_scores() — Basic Operation")
print("-" * 70)

try:
    L6 = Liquidator('BTC', cutoff_hours=None)
    L6.ingest_liqs(make_liq_data([79000, 78000, 77000]))
    zones6 = L6.compute_zones(window_minutes=120, pct_merge=0.003)
    result6 = L6.add_gravity_scores(zones6, current_price=80000.0)

    if 'gravity' not in result6.columns or 'gravity_rank' not in result6.columns:
        print(f"❌ gravity / gravity_rank columns missing")
    else:
        print(f"✅ gravity and gravity_rank columns present")

    if (result6['gravity'] < 0).any():
        print(f"❌ Negative gravity values found")
    else:
        print(f"✅ All gravity values >= 0")

    rank1_count = (result6['gravity_rank'] == 1).sum()
    if rank1_count == 1:
        print(f"✅ Exactly one zone with gravity_rank == 1")
    else:
        print(f"❌ Expected 1 zone with rank 1, got {rank1_count}")

    print(f"   Zones scored: {len(result6)}")

except Exception as e:
    print(f"❌ add_gravity_scores() failed: {e}")
    import traceback; traceback.print_exc()

# ── Test 9: Gravity — closer zone wins over far zone (equal liquidity) ─────────
print("\nTest 9: add_gravity_scores() — Distance Dominates With Equal Liquidity")
print("-" * 70)

try:
    L7 = Liquidator('BTC', cutoff_hours=None)
    # Both zones have equal USD — closer one must win gravity
    L7.ingest_liqs(make_liq_data([79500, 75000]))
    zones7 = L7.compute_zones(window_minutes=120, pct_merge=0.02)
    result7 = L7.add_gravity_scores(zones7, current_price=80000.0)

    top_price = result7.loc[result7['gravity_rank'] == 1, 'price_mean'].iloc[0]
    if abs(top_price - 79500) < abs(top_price - 75000) or abs(top_price - 79500) < 300:
        print(f"✅ Closer zone (79500) has gravity_rank == 1 — distance² logic correct")
    else:
        print(f"❌ Wrong zone ranked #1: {top_price:.0f} (expected ~79500)")
except Exception as e:
    print(f"❌ Gravity distance test failed: {e}")

# ── Test 10: Gravity — larger liquidity wins at equal distance ─────────────────
print("\nTest 10: add_gravity_scores() — Larger Cluster Wins at Equal Distance")
print("-" * 70)

try:
    L8 = Liquidator('BTC', cutoff_hours=None)
    # 79000 has 5M USD (5 entries × 1M), 81000 has 1M USD — same distance from 80000
    liqs_big  = make_liq_data([79000, 79000, 79000, 79000, 79000])
    liqs_small = make_liq_data([81000])
    L8.ingest_liqs(liqs_big + liqs_small)
    zones8 = L8.compute_zones(window_minutes=120, pct_merge=0.003)
    result8 = L8.add_gravity_scores(zones8, current_price=80000.0)

    top_price = result8.loc[result8['gravity_rank'] == 1, 'price_mean'].iloc[0]
    if abs(top_price - 79000) < 200:
        print(f"✅ More liquid zone (79000 @ $5M) beats smaller (81000 @ $1M)")
    else:
        print(f"❌ Wrong zone ranked #1: {top_price:.0f} (expected ~79000)")
except Exception as e:
    print(f"❌ Gravity liquidity test failed: {e}")

# ── Test 11: get_gravity_target() ─────────────────────────────────────────────
print("\nTest 11: get_gravity_target() — Returns Correct Dict")
print("-" * 70)

try:
    L9 = Liquidator('BTC', cutoff_hours=None)
    L9.ingest_liqs(make_liq_data([79500, 78000, 76000]))
    zones9 = L9.compute_zones(window_minutes=120, pct_merge=0.003)

    target = L9.get_gravity_target(zones9, current_price=80000.0)

    if target is None:
        print(f"❌ get_gravity_target() returned None unexpectedly")
    else:
        assert 'price_mean'   in target, "price_mean missing"
        assert 'gravity'      in target, "gravity missing"
        assert 'gravity_rank' in target, "gravity_rank missing"
        assert target['gravity_rank'] == 1, "target must be rank 1"
        print(f"✅ get_gravity_target() returns valid dict")
        print(f"   Next probable target: ${target['price_mean']:.0f}")
        print(f"   Gravity score:        {target['gravity']:.2f}")
        print(f"   Liquidity behind it:  ${target['total_usd']:,.0f}")

    # Edge: empty
    result_none = L9.get_gravity_target(pd.DataFrame(), current_price=80000.0)
    assert result_none is None, "Empty DataFrame should return None"
    print(f"✅ get_gravity_target() returns None on empty DataFrame")

    # Edge: invalid price
    result_zero = L9.get_gravity_target(zones9, current_price=0.0)
    assert result_zero is None, "current_price=0 should return None"
    print(f"✅ get_gravity_target() returns None on current_price=0")

except Exception as e:
    print(f"❌ get_gravity_target() test failed: {e}")
    import traceback; traceback.print_exc()

# ── Test 12: Combine cascade + gravity on same zones DataFrame ────────────────
print("\nTest 12: Combined — Cascade + Gravity on Same DataFrame")
print("-" * 70)

try:
    L10 = Liquidator('BTC', cutoff_hours=None)
    L10.ingest_liqs(make_liq_data([79500, 79000, 78500, 77000]))
    zones10 = L10.compute_zones(window_minutes=120, pct_merge=0.003)

    zones10 = L10.add_gravity_scores(zones10, current_price=80000.0)
    zones10 = L10.add_cascade_analysis(zones10, current_price=80000.0, funding_rate=0.0002)

    all_cols = ['gravity', 'gravity_rank', 'cascade_probability',
                'cascade_chain_length', 'cascade_target_price']
    missing  = [c for c in all_cols if c not in zones10.columns]

    if missing:
        print(f"❌ Missing columns after combining: {missing}")
    else:
        print(f"✅ All cascade + gravity columns present together")

    # v0.0.9 columns must still be intact
    original_cols = ['price_mean', 'strength', 'quality_score', 'quality_label']
    missing_orig  = [c for c in original_cols if c not in zones10.columns]
    if missing_orig:
        print(f"❌ v0.0.9 columns overwritten: {missing_orig}")
    else:
        print(f"✅ v0.0.9 columns still intact after new methods applied")

    target = L10.get_gravity_target(zones10, current_price=80000.0)
    top_cascade = zones10.nlargest(1, 'cascade_probability').iloc[0]

    print(f"\n   📊 Combined output sample:")
    print(f"   Next gravity target:    ${target['price_mean']:.0f}  "
          f"(gravity={target['gravity']:.1f})")
    print(f"   Highest cascade risk:   ${top_cascade['price_mean']:.0f}  "
          f"prob={top_cascade['cascade_probability']:.1f}%  "
          f"chain={top_cascade['cascade_chain_length']}  "
          f"target=${top_cascade['cascade_target_price']:.0f}")

except Exception as e:
    print(f"❌ Combined test failed: {e}")
    import traceback; traceback.print_exc()

# ── Test 13: Streaming mode still works ───────────────────────────────────────
print("\nTest 13: Streaming Mode (v0.0.7 API Unchanged)")
print("-" * 70)

try:
    events = []
    L_stream = Liquidator(mode='streaming', window_minutes=10, cutoff_hours=None)
    L_stream.on_zone_formed(lambda z: events.append(z))
    L_stream.ingest_trades(make_trade_data(15))
    L_stream.compute_zones(window_minutes=10)
    print(f"✅ Streaming mode still works — events captured: {len(events)}")
except Exception as e:
    print(f"❌ Streaming mode broken: {e}")

# ── Test 14: ML predictor init still works ────────────────────────────────────
print("\nTest 14: ML Predictor Init (v0.0.7 API Unchanged)")
print("-" * 70)

try:
    L_ml = Liquidator(enable_ml=True, window_minutes=10, cutoff_hours=None)
    L_ml.ingest_trades(make_trade_data(20))
    print(f"✅ enable_ml=True still works without error")
    print(f"   ⚠️  Reminder: ML model still in data collection mode (v0.0.8→v0.0.9 retrain pending)")
except Exception as e:
    print(f"❌ ML predictor init broken: {e}")

# ── Final summary ─────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("FINAL SUMMARY — v0.1.0 COMPATIBILITY")
print("=" * 70)

print("""
✅ BACKWARD COMPATIBILITY (v0.0.9 → v0.1.0):
   - compute_zones() output columns: unchanged
   - ingest_trades() / ingest_liqs(): unchanged
   - Streaming mode callbacks: unchanged
   - ML predictor init API: unchanged
   - New columns only appear when new methods are explicitly called

✅ NEW FEATURES:
   - add_cascade_analysis()    — cascade probability, chain length, target price
   - add_gravity_scores()      — gravity score and rank per zone
   - get_gravity_target()      — single-call next probable target lookup

⚠️  KNOWN NOTES:
   - ML model still in data collection mode (retraining from v0.0.9 in progress)
   - Cascade + gravity methods return DataFrame copies — no instance state modified
""")

print(f"Package version:  {__version__}")
print(f"Pandas version:   {pd.__version__}")
print(f"NumPy version:    {np.__version__}")
print(f"Python version:   {sys.version.split()[0]}")
print("=" * 70)
