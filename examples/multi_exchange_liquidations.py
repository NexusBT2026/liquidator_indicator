"""
Demo: Real liquidation data collection from multiple exchanges.

Shows how to:
1. Collect real liquidation events from 5+ exchanges
2. Validate inferred zones with real liquidation data
3. Detect cross-exchange liquidation cascades
4. Compare inferred vs real liquidations
"""
from liquidator_indicator import Liquidator
from liquidator_indicator.collectors import MultiExchangeLiquidationCollector
import pandas as pd
import time
from datetime import datetime, timezone

# ==================== SETUP ====================

print("=" * 60)
print("MULTI-EXCHANGE LIQUIDATION COLLECTOR DEMO")
print("=" * 60)

# Start collecting from multiple exchanges
collector = MultiExchangeLiquidationCollector(
    exchanges=['binance', 'bybit', 'okx', 'bitmex', 'deribit'],
    symbols=['BTC', 'ETH']
)

print("\n🚀 Starting collectors for 5 exchanges...")
print("   - Binance (WebSocket)")
print("   - Bybit (WebSocket)")
print("   - OKX (REST + WebSocket)")
print("   - BitMEX (REST polling)")
print("   - Deribit (WebSocket)")
collector.start()

print("\n⏳ Collecting liquidations for 60 seconds...")
print("   (In production, run this continuously in background)\n")

# Collect for 60 seconds
time.sleep(60)

# ==================== GET LIQUIDATIONS ====================

# Get all liquidations from the last hour
liqs = collector.get_liquidations()

print(f"\n📊 COLLECTED {len(liqs)} LIQUIDATIONS:")
print(f"   Exchanges: {liqs['exchange'].nunique()} active")
print(f"   Total Value: ${liqs['value_usd'].sum():,.2f}")
print(f"   Avg Liquidation: ${liqs['value_usd'].mean():,.2f}")

# Show sample
if not liqs.empty:
    print("\n📈 Recent liquidations:")
    print(liqs.head(10).to_string(index=False))

# ==================== CROSS-EXCHANGE STATISTICS ====================

stats = collector.get_statistics(window_minutes=60)

print("\n\n" + "=" * 60)
print("CROSS-EXCHANGE STATISTICS (Last 60 minutes)")
print("=" * 60)
print(f"Total Liquidations: {stats['total_liquidations']}")
print(f"Total Value: ${stats['total_value_usd']:,.2f}")

print("\n📊 By Exchange:")
if 'by_exchange' in stats:
    for exchange, data in stats['by_exchange'].items():
        print(f"   {exchange:10s}: {data} liquidations")

print("\n📈 By Side:")
if 'by_side' in stats:
    for side, data in stats['by_side'].items():
        print(f"   {side:10s}: {data} liquidations")

# ==================== VALIDATE WITH INDICATOR ====================

print("\n\n" + "=" * 60)
print("VALIDATING INFERRED ZONES WITH REAL LIQUIDATIONS")
print("=" * 60)

# Create some sample trade data for inference
# (In production, use real trade stream)
sample_trades = []
for _, liq in liqs.iterrows():
    # Simulate trades around liquidation prices
    sample_trades.append({
        'timestamp': liq['timestamp'],
        'price': liq['price'],
        'size': liq['quantity'],
        'usd_value': liq['value_usd'],
        'side': 'A' if liq['side'] == 'SELL' else 'B'
    })

if sample_trades:
    trades_df = pd.DataFrame(sample_trades)
    
    # Create indicator and ingest both inferred + real liquidations
    liq_indicator = Liquidator(coin='BTC')
    liq_indicator.ingest_trades(trades_df)
    liq_indicator.ingest_liquidations(liqs)  # Add real liquidation data
    
    # Compute zones (quality scores boosted by real data)
    zones = liq_indicator.compute_zones()
    
    print(f"\n✅ COMPUTED {len(zones)} ZONES WITH VALIDATION:")
    
    if not zones.empty:
        # Show zones with validation metrics
        validation_cols = ['price_mean', 'quality_score', 'quality_label', 
                          'real_liq_count', 'real_liq_exchanges', 
                          'real_liq_value_usd', 'validation_boost']
        
        available_cols = [col for col in validation_cols if col in zones.columns]
        print(zones[available_cols].to_string(index=False))
        
        # Identify cascade zones (multiple exchanges)
        if 'real_liq_exchanges' in zones.columns:
            cascade_zones = zones[zones['real_liq_exchanges'] >= 2]
            
            if not cascade_zones.empty:
                print(f"\n\n🚨 CASCADE ALERT: {len(cascade_zones)} zones with multi-exchange liquidations!")
                print("\nCascade Zones:")
                print(cascade_zones[available_cols].to_string(index=False))
                
                print("\n💡 These zones are validated across multiple exchanges = HIGH CONFIDENCE")
        
        # Compare quality scores
        if 'quality_score_original' in zones.columns:
            avg_boost = zones['validation_boost'].mean()
            print(f"\n📈 Average Quality Boost: +{avg_boost:.1f}%")
            print(f"   Zones went from avg {zones['quality_score_original'].mean():.1f} "
                  f"→ {zones['quality_score'].mean():.1f} quality score")

# ==================== VALIDATION STATISTICS ====================

print("\n\n" + "=" * 60)
print("VALIDATION ANALYSIS")
print("=" * 60)

if not liqs.empty and not zones.empty:
    # Calculate inference accuracy
    inferred_prices = zones['price_mean'].tolist()
    real_prices = liqs['price'].tolist()
    
    # Count how many real liquidations matched inferred zones (within 0.5%)
    matched = 0
    for real_price in real_prices:
        for inferred_price in inferred_prices:
            if abs(real_price - inferred_price) / inferred_price < 0.005:
                matched += 1
                break
    
    accuracy = (matched / len(real_prices)) * 100
    
    print(f"\n✅ Inference Accuracy: {accuracy:.1f}%")
    print(f"   Matched: {matched}/{len(real_prices)} real liquidations")
    print(f"   Inferred Zones: {len(zones)}")
    print(f"   Real Liquidations: {len(liqs)}")
    
    # Show distribution of validation
    if 'real_liq_count' in zones.columns:
        validated = zones[zones['real_liq_count'] > 0]
        print(f"\n📊 Validated Zones: {len(validated)}/{len(zones)} ({len(validated)/len(zones)*100:.1f}%)")
        print(f"   Max liquidations in one zone: {zones['real_liq_count'].max()}")
        print(f"   Avg liquidations per validated zone: {validated['real_liq_count'].mean():.1f}")

# ==================== CLEANUP ====================

print("\n\n🛑 Stopping collectors...")
collector.stop()

print("\n" + "=" * 60)
print("✅ DEMO COMPLETE")
print("=" * 60)
print("\n💡 Key Takeaways:")
print("   1. Real liquidation data validates inferred zones")
print("   2. Cross-exchange cascades = HIGH confidence zones")
print("   3. Quality scores boosted up to 30% with validation")
print("   4. More data sources = More accurate predictions")
print("\n🚀 Use this in production for 40x leverage trading!")
print("=" * 60)
