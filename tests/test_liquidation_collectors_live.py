"""
Live Test: Liquidation Collectors - Real Exchange Connections

Tests all 8 working exchange liquidation collectors with LIVE data.
This script connects to real exchange APIs/WebSockets and collects actual liquidations.

WARNING: This test uses real network connections and may take time.

To run live tests:
    pytest tests/test_liquidation_collectors_live.py -v -m live --run-live

Or run as standalone script:
    python tests/test_liquidation_collectors_live.py
"""
import pytest
import time
import pandas as pd
from datetime import datetime, timezone
from liquidator_indicator.collectors import (
    BinanceLiquidationCollector,
    BybitLiquidationCollector,
    OKXLiquidationCollector,
    BitMEXLiquidationCollector,
    DeribitLiquidationCollector,
    HTXLiquidationCollector,
    PhemexLiquidationCollector,
    MEXCLiquidationCollector,
    MultiExchangeLiquidationCollector
)


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "live: mark test as requiring live network connection")


def pytest_addoption(parser):
    """Add command line option for running live tests."""
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="Run tests that require live network connections"
    )


@pytest.mark.live
@pytest.mark.timeout(60)
def test_binance_live_connection():
    """Test Binance liquidation collector with live WebSocket."""
    collector = BinanceLiquidationCollector(symbols=['BTCUSDT'])
    
    liquidations_received = []
    
    def on_liq(liq):
        liquidations_received.append(liq)
        print(f"Binance: {liq['symbol']} ${liq['price']:,.2f} x {liq['quantity']:.4f}")
    
    collector.callback = on_liq
    collector.start()
    
    # Collect for 30 seconds
    time.sleep(30)
    
    collector.stop()
    
    # Get DataFrame
    df = collector.get_liquidations()
    
    print(f"\nBinance Results:")
    print(f"  Liquidations collected: {len(df)}")
    if not df.empty:
        print(f"  Total value: ${df['value_usd'].sum():,.2f}")
        print(f"  Avg liquidation: ${df['value_usd'].mean():,.2f}")
    
    # Assertions
    assert isinstance(df, pd.DataFrame)
    # Note: May be empty if no liquidations during test period
    if not df.empty:
        assert 'exchange' in df.columns
        assert all(df['exchange'] == 'binance')


@pytest.mark.live
@pytest.mark.timeout(60)
def test_bybit_live_connection():
    """Test Bybit liquidation collector with live WebSocket."""
    collector = BybitLiquidationCollector(symbols=['BTCUSDT'])
    
    liquidations_received = []
    
    def on_liq(liq):
        liquidations_received.append(liq)
        print(f"Bybit: {liq['symbol']} ${liq['price']:,.2f} x {liq['quantity']:.4f}")
    
    collector.callback = on_liq
    collector.start()
    
    time.sleep(30)
    collector.stop()
    
    df = collector.get_liquidations()
    
    print(f"\nBybit Results:")
    print(f"  Liquidations collected: {len(df)}")
    if not df.empty:
        print(f"  Total value: ${df['value_usd'].sum():,.2f}")
    
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert all(df['exchange'] == 'bybit')


@pytest.mark.live
@pytest.mark.timeout(60)
def test_okx_live_connection():
    """Test OKX liquidation collector with REST + WebSocket."""
    collector = OKXLiquidationCollector(symbols=['BTC'])
    
    collector.start()
    time.sleep(30)
    collector.stop()
    
    df = collector.get_liquidations()
    
    print(f"\nOKX Results:")
    print(f"  Liquidations collected: {len(df)}")
    
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert all(df['exchange'] == 'okx')


@pytest.mark.live
@pytest.mark.timeout(60)
def test_bitmex_live_connection():
    """Test BitMEX liquidation collector with REST polling."""
    collector = BitMEXLiquidationCollector(symbols=['XBTUSD'], poll_interval=5)
    
    collector.start()
    time.sleep(30)
    collector.stop()
    
    df = collector.get_liquidations()
    
    print(f"\nBitMEX Results:")
    print(f"  Liquidations collected: {len(df)}")
    
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert all(df['exchange'] == 'bitmex')


@pytest.mark.live
@pytest.mark.timeout(60)
def test_deribit_live_connection():
    """Test Deribit liquidation collector with live WebSocket."""
    collector = DeribitLiquidationCollector(symbols=['BTC'])
    
    collector.start()
    time.sleep(30)
    collector.stop()
    
    df = collector.get_liquidations()
    
    print(f"\nDeribit Results:")
    print(f"  Liquidations collected: {len(df)}")
    
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert all(df['exchange'] == 'deribit')


@pytest.mark.live
@pytest.mark.timeout(60)
def test_htx_live_connection():
    """Test HTX liquidation collector with REST polling."""
    collector = HTXLiquidationCollector(symbols=['BTC'], poll_interval=10)
    
    collector.start()
    time.sleep(30)
    collector.stop()
    
    df = collector.get_liquidations()
    
    print(f"\nHTX Results:")
    print(f"  Liquidations collected: {len(df)}")
    
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert all(df['exchange'] == 'htx')


@pytest.mark.live
@pytest.mark.timeout(120)
def test_multi_exchange_live_collection():
    """Test MultiExchangeLiquidationCollector with all 11 exchanges."""
    print("\n" + "=" * 70)
    print("MULTI-EXCHANGE LIVE TEST (All 11 Exchanges)")
    print("=" * 70)
    
    collector = MultiExchangeLiquidationCollector(
        exchanges=['binance', 'bybit', 'okx', 'bitmex', 'deribit', 
                  'htx', 'gateio', 'kucoin', 'bitfinex', 'phemex', 'mexc'],
        symbols=['BTC', 'ETH']
    )
    
    liquidations_by_exchange = {}
    
    def on_liq(liq):
        exchange = liq['exchange']
        if exchange not in liquidations_by_exchange:
            liquidations_by_exchange[exchange] = 0
        liquidations_by_exchange[exchange] += 1
        print(f"  {exchange.upper():10s} | {liq['symbol']:10s} | ${liq['price']:,.2f}")
    
    collector.callback = on_liq
    collector.start()
    
    print("\nCollecting liquidations for 60 seconds...\n")
    time.sleep(60)
    
    collector.stop()
    
    # Get all liquidations
    df = collector.get_liquidations()
    
    # Get statistics
    stats = collector.get_statistics(window_minutes=60)
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Total Liquidations: {len(df)}")
    print(f"Total Value: ${stats['total_value_usd']:,.2f}")
    print(f"\nBy Exchange:")
    for exchange, count in sorted(liquidations_by_exchange.items()):
        print(f"  {exchange:10s}: {count} liquidations")
    
    print(f"\nActive Exchanges: {df['exchange'].nunique()}/{len(collector._collectors)}")
    
    # Assertions
    assert isinstance(df, pd.DataFrame)
    assert stats['total_liquidations'] == len(df)
    
    if not df.empty:
        # Verify required columns
        required_cols = ['exchange', 'symbol', 'side', 'price', 'quantity', 'value_usd', 'timestamp']
        for col in required_cols:
            assert col in df.columns, f"Missing column: {col}"
        
        # Verify all exchanges are from our list
        valid_exchanges = ['binance', 'bybit', 'okx', 'bitmex', 'deribit', 
                          'htx', 'gateio', 'kucoin', 'bitfinex', 'phemex', 'mexc']
        assert all(df['exchange'].isin(valid_exchanges))
        
        print(f"\n✅ Multi-exchange test PASSED")
    else:
        print(f"\n⚠️  No liquidations collected (market may be quiet)")


@pytest.mark.live
@pytest.mark.timeout(120)
def test_cascade_detection_live():
    """Test cross-exchange cascade detection with live data."""
    print("\n" + "=" * 70)
    print("CASCADE DETECTION TEST")
    print("=" * 70)
    
    collector = MultiExchangeLiquidationCollector(
        exchanges=['binance', 'bybit', 'okx', 'deribit'],
        symbols=['BTC']
    )
    
    collector.start()
    
    print("\nCollecting liquidations for 60 seconds...")
    print("Looking for liquidations at similar prices across exchanges...\n")
    
    time.sleep(60)
    collector.stop()
    
    df = collector.get_liquidations()
    
    if df.empty:
        print("⚠️  No liquidations collected")
        pytest.skip("No liquidations to analyze")
    
    # Group liquidations by price buckets (1% tolerance)
    df['price_bucket'] = (df['price'] / 100).round() * 100
    
    # Find price levels with multiple exchanges
    cascades = df.groupby('price_bucket').agg({
        'exchange': 'nunique',
        'value_usd': 'sum',
        'quantity': 'sum'
    }).query('exchange >= 2').sort_values('value_usd', ascending=False)
    
    print(f"\n" + "=" * 70)
    print("CASCADE ANALYSIS")
    print("=" * 70)
    print(f"Total liquidations: {len(df)}")
    print(f"Unique exchanges: {df['exchange'].nunique()}")
    print(f"Cascade zones found: {len(cascades)}")
    
    if not cascades.empty:
        print(f"\nTop Cascade Zones:")
        for price_bucket, row in cascades.head(5).iterrows():
            exchanges_at_price = df[df['price_bucket'] == price_bucket]['exchange'].unique()
            print(f"  ${price_bucket:,.0f}: {row['exchange']} exchanges ({', '.join(exchanges_at_price)})")
            print(f"    Value: ${row['value_usd']:,.2f}")
        
        print(f"\n✅ CASCADE DETECTION PASSED")
    else:
        print(f"\n⚠️  No cascades detected (needs more liquidations)")


if __name__ == '__main__':
    import pandas as pd
    
    print("=" * 70)
    print("LIQUIDATION COLLECTORS - LIVE TEST SUITE")
    print("=" * 70)
    print("\nThis script tests all 11 exchange collectors with REAL data.")
    print("It will connect to live exchanges and collect actual liquidations.\n")
    
    # Run multi-exchange test
    test_multi_exchange_live_collection()
    
    print("\n" + "=" * 70)
    print("✅ LIVE TESTS COMPLETE")
    print("=" * 70)
