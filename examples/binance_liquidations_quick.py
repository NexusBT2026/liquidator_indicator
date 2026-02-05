"""
Quick Start: Single exchange liquidation collector.

Shows the simplest way to collect and use real liquidation data.
"""
from liquidator_indicator import Liquidator
from liquidator_indicator.collectors import BinanceLiquidationCollector
import time

print("🚀 Binance Liquidation Collector - Quick Start\n")

# ==================== SETUP ====================

# Callback to print each liquidation as it happens
def on_liquidation(liq_data):
    print(f"💥 {liq_data['exchange'].upper()} | "
          f"{liq_data['symbol']:10s} | "
          f"{liq_data['side']:5s} | "
          f"${liq_data['price']:,.2f} | "
          f"${liq_data['value_usd']:,.2f}")

# Start collecting
collector = BinanceLiquidationCollector(
    symbols=['BTCUSDT', 'ETHUSDT'],
    callback=on_liquidation  # Print each liquidation
)

print("Starting Binance liquidation stream...")
print("Symbol     | Side  | Price         | Value USD")
print("-" * 60)

collector.start()

# Collect for 30 seconds
time.sleep(30)

# ==================== USE DATA ====================

# Get all liquidations
liqs = collector.get_liquidations()

print(f"\n\n📊 Collected {len(liqs)} liquidations")
print(f"Total value: ${liqs['value_usd'].sum():,.2f}")

# Feed to indicator
liq_indicator = Liquidator(coin='BTC')
liq_indicator.ingest_liquidations(liqs)

# If you also have trade data, ingest it
# liq_indicator.ingest_trades(your_trade_data)

# Compute zones (boosted by real liquidation data)
zones = liq_indicator.compute_zones()

print(f"\n✅ Computed {len(zones)} zones")

if not zones.empty and 'real_liq_count' in zones.columns:
    validated = zones[zones['real_liq_count'] > 0]
    print(f"   {len(validated)} zones validated with real liquidations")

# Stop collector
collector.stop()
print("\n✅ Done!")
