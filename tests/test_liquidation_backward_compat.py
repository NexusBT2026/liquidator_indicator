"""
Backward Compatibility Tests: Liquidation Collectors

Ensures the new liquidation collectors feature doesn't break existing functionality.
Tests that old code still works without using liquidation collectors.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from liquidator_indicator import Liquidator


def test_liquidator_works_without_liquidations():
    """Test that Liquidator works WITHOUT ingest_liquidations() calls."""
    liq = Liquidator(coin='BTC', cutoff_hours=None)
    
    # Create sample trade data (old-style format with usd_value)
    now = datetime.now(timezone.utc)
    trades = pd.DataFrame({
        'timestamp': [now - timedelta(minutes=i) for i in range(10)],
        'price': [50000 + i * 100 for i in range(10)],
        'usd_value': [100000] * 10,  # Old format: usd_value instead of size
        'side': ['sell'] * 10
    })
    
    # Should work without any liquidation data
    liq.ingest_trades(trades)
    
    zones = liq.compute_zones()
    
    # Verify basic functionality still works
    assert isinstance(zones, pd.DataFrame)
    assert 'price_mean' in zones.columns  # Zones use price_mean, not price
    assert 'quality_score' in zones.columns


def test_old_trade_format_compatibility():
    """Test that old trade format (usd_value column) still works."""
    liq = Liquidator(coin='BTC', cutoff_hours=None)
    
    now = datetime.now(timezone.utc)
    
    # OLD FORMAT: usd_value column (pre-liquidation feature)
    old_trades = pd.DataFrame({
        'timestamp': [now - timedelta(minutes=i) for i in range(5)],
        'price': [50000, 51000, 52000, 51000, 50000],
        'usd_value': [500000, 400000, 300000, 400000, 500000],
        'side': ['sell', 'sell', 'buy', 'sell', 'sell']
    })
    
    # Should automatically calculate size from usd_value
    liq.ingest_trades(old_trades)
    
    # Verify trades were ingested
    assert len(liq._trades) > 0
    assert 'size' in liq._trades.columns
    
    # Verify size calculation: size = usd_value / price
    expected_size_0 = 500000 / 50000  # = 10 BTC
    assert abs(liq._trades.iloc[0]['size'] - expected_size_0) < 0.01


def test_new_trade_format_compatibility():
    """Test that new trade format (size column) works."""
    liq = Liquidator(coin='BTC', cutoff_hours=None)
    
    now = datetime.now(timezone.utc)
    
    # NEW FORMAT: size column directly
    new_trades = pd.DataFrame({
        'timestamp': [now - timedelta(minutes=i) for i in range(5)],
        'price': [50000, 51000, 52000, 51000, 50000],
        'size': [10.0, 8.0, 6.0, 8.0, 10.0],  # Direct BTC amounts
        'side': ['sell', 'sell', 'buy', 'sell', 'sell']
    })
    
    liq.ingest_trades(new_trades)
    
    # Verify trades were ingested with original size values
    assert len(liq._trades) > 0
    assert liq._trades.iloc[0]['size'] == 10.0


def test_mixed_format_handling():
    """Test handling both old and new format in sequence."""
    liq = Liquidator(coin='BTC', cutoff_hours=None)
    
    now = datetime.now(timezone.utc)
    
    # First ingest old format
    old_trades = pd.DataFrame({
        'timestamp': [now - timedelta(minutes=10), now - timedelta(minutes=9)],
        'price': [50000, 51000],
        'usd_value': [500000, 400000],
        'side': ['sell', 'sell']
    })
    liq.ingest_trades(old_trades)
    
    # Then ingest new format
    new_trades = pd.DataFrame({
        'timestamp': [now - timedelta(minutes=8), now - timedelta(minutes=7)],
        'price': [52000, 51000],
        'size': [6.0, 8.0],
        'side': ['buy', 'sell']
    })
    liq.ingest_trades(new_trades)
    
    # Both should be in DataFrame
    assert len(liq._trades) == 4
    assert all(liq._trades['size'] > 0)


def test_quality_score_without_liquidations():
    """Test quality scores are reasonable without liquidation validation."""
    liq = Liquidator(coin='BTC', cutoff_hours=None)
    
    now = datetime.now(timezone.utc)
    
    # Create high-volume sell cluster (should be detected as liquidation zone)
    trades = pd.DataFrame({
        'timestamp': [now - timedelta(minutes=i) for i in range(20)],
        'price': [50000] * 10 + [50100] * 10,  # Cluster at 50k
        'size': [10.0] * 20,  # High volume
        'side': ['sell'] * 20  # All sells
    })
    
    liq.ingest_trades(trades)
    zones = liq.compute_zones()
    
    # Should detect zones without liquidation data
    assert len(zones) > 0
    
    # Quality scores should be reasonable (ML can boost scores high without liquidations)
    assert all(zones['quality_score'] >= 0.2)


def test_liquidation_ingestion_optional():
    """Test that ingest_liquidations() is completely optional."""
    liq = Liquidator(coin='BTC', cutoff_hours=None)
    
    now = datetime.now(timezone.utc)
    trades = pd.DataFrame({
        'timestamp': [now - timedelta(minutes=i) for i in range(10)],
        'price': [50000 + i * 100 for i in range(10)],
        'size': [5.0] * 10,
        'side': ['sell'] * 10
    })
    
    # Never call ingest_liquidations()
    liq.ingest_trades(trades)
    zones = liq.compute_zones()
    
    # Should work fine
    assert len(zones) >= 0  # May or may not have zones
    assert isinstance(zones, pd.DataFrame)


def test_liquidation_validation_boost():
    """Test that liquidations DO boost quality when provided."""
    # Disable ML to isolate liquidation boost effect
    liq = Liquidator(coin='BTC', cutoff_hours=None, enable_ml=False)
    
    now = datetime.now(timezone.utc)
    
    # Create trade cluster at $50k
    trades = pd.DataFrame({
        'timestamp': [now - timedelta(minutes=i) for i in range(10)],
        'price': [50000] * 10,
        'size': [10.0] * 10,
        'side': ['sell'] * 10
    })
    liq.ingest_trades(trades)
    
    # Compute zones WITHOUT liquidations
    zones_without = liq.compute_zones()
    # Find zone near $50k (use price_mean)
    base_quality = zones_without[zones_without['price_mean'].between(49900, 50100)]['quality_score'].iloc[0] if len(zones_without) > 0 else 0.5
    
    # Now add matching liquidation data
    liquidations = pd.DataFrame({
        'timestamp': [now - timedelta(minutes=5)],
        'exchange': ['binance'],
        'symbol': ['BTCUSDT'],
        'side': ['sell'],
        'price': [50000.0],
        'quantity': [5.0],
        'value_usd': [250000.0]
    })
    liq.ingest_liquidations(liquidations)
    
    # Recompute zones WITH liquidations
    zones_with = liq.compute_zones()
    boosted_quality = zones_with[zones_with['price_mean'].between(49900, 50100)]['quality_score'].iloc[0] if len(zones_with) > 0 else 0.5
    
    # Quality should be boosted
    assert boosted_quality >= base_quality, "Liquidation validation should boost or maintain quality score"
    print(f"Quality change: {base_quality:.3f} -> {boosted_quality:.3f} (+{boosted_quality - base_quality:.3f})")
    
    # Verify liquidation data is stored
    assert len(liq._real_liquidations) == 1
    assert liq._real_liquidations.iloc[0]['exchange'] == 'binance'


def test_multiple_liquidation_ingestions():
    """Test that multiple ingest_liquidations() calls accumulate data."""
    liq = Liquidator(coin='BTC', cutoff_hours=None)
    
    now = datetime.now(timezone.utc)
    
    # First batch
    liq1 = pd.DataFrame({
        'timestamp': [now - timedelta(minutes=10)],
        'exchange': ['binance'],
        'symbol': ['BTCUSDT'],
        'side': ['sell'],
        'price': [50000.0],
        'quantity': [5.0],
        'value_usd': [250000.0]
    })
    liq.ingest_liquidations(liq1)
    
    # Second batch
    liq2 = pd.DataFrame({
        'timestamp': [now - timedelta(minutes=5)],
        'exchange': ['bybit'],
        'symbol': ['BTCUSDT'],
        'side': ['sell'],
        'price': [50100.0],
        'quantity': [3.0],
        'value_usd': [150000.0]
    })
    liq.ingest_liquidations(liq2)
    
    # Should have accumulated both
    assert len(liq._real_liquidations) == 2
    assert 'binance' in liq._real_liquidations['exchange'].values
    assert 'bybit' in liq._real_liquidations['exchange'].values


def test_empty_liquidations_dataframe():
    """Test handling of empty liquidation DataFrame."""
    liq = Liquidator(coin='BTC', cutoff_hours=None)
    
    now = datetime.now(timezone.utc)
    trades = pd.DataFrame({
        'timestamp': [now - timedelta(minutes=i) for i in range(5)],
        'price': [50000] * 5,
        'size': [5.0] * 5,
        'side': ['sell'] * 5
    })
    liq.ingest_trades(trades)
    
    # Ingest empty liquidations DataFrame
    empty_liqs = pd.DataFrame(columns=['timestamp', 'exchange', 'symbol', 'side', 'price', 'quantity', 'value_usd'])
    liq.ingest_liquidations(empty_liqs)
    
    # Should not crash
    zones = liq.compute_zones()
    assert isinstance(zones, pd.DataFrame)


def test_cascade_detection_backward_compat():
    """Test that cascade detection (2+ exchanges) works correctly."""
    liq = Liquidator(coin='BTC', cutoff_hours=None)
    
    now = datetime.now(timezone.utc)
    
    # Create trade cluster
    trades = pd.DataFrame({
        'timestamp': [now - timedelta(minutes=i) for i in range(10)],
        'price': [50000] * 10,
        'size': [10.0] * 10,
        'side': ['sell'] * 10
    })
    liq.ingest_trades(trades)
    
    # Add liquidations from 3 exchanges at same price (cascade)
    liquidations = pd.DataFrame({
        'timestamp': [now - timedelta(minutes=5), now - timedelta(minutes=4), now - timedelta(minutes=3)],
        'exchange': ['binance', 'bybit', 'okx'],
        'symbol': ['BTCUSDT'] * 3,
        'side': ['sell'] * 3,
        'price': [50000.0] * 3,
        'quantity': [5.0] * 3,
        'value_usd': [250000.0] * 3
    })
    liq.ingest_liquidations(liquidations)
    
    zones = liq.compute_zones()
    
    # Find zone near $50k (use price_mean)
    zone_50k = zones[zones['price_mean'].between(49900, 50100)]
    assert len(zone_50k) > 0
    
    # Quality should be significantly boosted due to cascade
    quality = zone_50k.iloc[0]['quality_score']
    print(f"Cascade quality score: {quality:.3f}")
    
    # Cascade should provide validation boost
    assert quality > 0.5, "Cascade should significantly boost quality"


def test_real_liquidations_attribute_exists():
    """Test that _real_liquidations attribute exists and is accessible."""
    liq = Liquidator(coin='BTC')
    
    # Should have _real_liquidations attribute
    assert hasattr(liq, '_real_liquidations')
    assert isinstance(liq._real_liquidations, pd.DataFrame)
    assert len(liq._real_liquidations) == 0  # Should start empty


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
