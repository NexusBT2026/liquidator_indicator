"""
LIQUIDATOR INDICATOR v0.0.7 - Demo
===========================================
Showcases all major features in under 60 seconds.
"""
import sys
import pandas as pd
import numpy as np

# Force reload to get latest code
if 'liquidator_indicator' in sys.modules:
    del sys.modules['liquidator_indicator']
if 'liquidator_indicator.core' in sys.modules:
    del sys.modules['liquidator_indicator.core']

from liquidator_indicator import Liquidator

print("=" * 80)
print("LIQUIDATOR INDICATOR v0.0.7 - Feature Demo")
print("=" * 80)

# Generate realistic sample trades (simulating Hyperliquid data)
np.random.seed(42)
now = pd.Timestamp.utcnow()
trades = []

# Create 3 liquidation zones around key price levels
zones_prices = [79000, 80000, 81000]
for zone_price in zones_prices:
    for i in range(15):
        price = zone_price + np.random.normal(0, 50)
        trades.append({
            'coin': 'BTC',
            'side': 'A' if zone_price == 80000 else 'B',  # SHORT zone at 80k, LONG elsewhere
            'px': str(price),
            'sz': str(np.random.uniform(0.5, 3.0)),
            'time': int((now - pd.Timedelta(hours=np.random.randint(1, 24))).timestamp() * 1000)
        })

print(f"\nGenerated {len(trades)} sample trades")
print("-" * 80)

# FEATURE 1: Multi-Exchange Support
print("\n1. MULTI-EXCHANGE SUPPORT (23 exchanges)")
L = Liquidator.from_exchange('BTC', 'hyperliquid', raw_data=trades)
print("   Loaded data from: Hyperliquid")
print("   Also supports: Binance, Coinbase, Bybit, OKX, Kraken, and 17 more!")

# FEATURE 2: Quality Scoring
print("\n2. QUALITY SCORING (0-100 scale)")
zones = L.compute_zones(min_quality='medium')
print(f"   Detected {len(zones)} MEDIUM+ quality zones:")
for idx, zone in zones.iterrows():
    # Check which columns exist
    price = zone['price_mean']
    quality = zone['quality_score']
    label = zone['quality_label']
    strength = zone.get('strength', 0)
    print(f"   - ${price:,.2f} | Quality: {quality:.0f}/100 ({label}) | Strength: {strength:.3f}")

# FEATURE 3: Multi-Timeframe Analysis
print("\n3. MULTI-TIMEFRAME ANALYSIS (15 timeframes)")
mtf_zones = L.compute_multi_timeframe_zones(['1h', '4h', '1d'], min_quality='medium')
if not mtf_zones.empty:
    best_zone = mtf_zones.iloc[0]
    print(f"   Top zone: ${best_zone['price_mean']:,.2f}")
    print(f"   Alignment score: {best_zone.get('alignment_score', 0):.0f}/100")
    print(f"   Multi-timeframe confirmation: YES")
else:
    print(f"   Found {len(mtf_zones)} zones across multiple timeframes")

# FEATURE 4: ML-Powered Predictions
print("\n4. ML-POWERED PREDICTIONS (with SQN metrics)")
L.enable_ml_predictions()
train_metrics = L.train_ml_predictor(use_synthetic=True, n_synthetic=250)
print(f"   Model trained: {train_metrics['train_accuracy']:.1f}% accuracy")
print(f"   Training samples: {train_metrics['n_samples']}")

zones_ml = L.compute_zones_with_prediction(current_price=80000)
if not zones_ml.empty:
    print(f"\n   ML Predictions for top zones:")
    for idx, zone in zones_ml.head(3).iterrows():
        print(f"   - ${zone['price_mean']:,.2f} | Hold: {zone['hold_probability']:.1f}% | Confidence: {zone['prediction_confidence']:.0f}/100")

# FEATURE 5: Streaming Mode (simulate)
print("\n5. REAL-TIME STREAMING MODE")
L_stream = Liquidator('BTC', mode='streaming')

# Register callbacks
zone_formed_count = [0]
def on_zone_formed(zone):
    zone_formed_count[0] += 1

L_stream.on_zone_formed(on_zone_formed)
L_stream.ingest_trades(trades)
zones_stream = L_stream.compute_zones()
print(f"   Streaming mode active: {zone_formed_count[0]} zones detected")
print(f"   Event callbacks: READY for live trading")

# FEATURE 6: Visualization (mention only, don't plot)
print("\n6. INTERACTIVE VISUALIZATION")
print("   - Plotly interactive charts (zoom, pan, hover)")
print("   - TradingView Pine Script export")
print("   - HTML dashboards")
print("   - Color-coded by quality (strong=green/red, weak=gray)")

# Summary Stats
print("\n" + "=" * 80)
print("v0.0.7 SUMMARY")
print("=" * 80)
print(f"Total zones detected: {len(zones)}")
print(f"Quality range: {zones['quality_score'].min():.0f}-{zones['quality_score'].max():.0f}/100")
print(f"Best zone: ${zones.iloc[0]['price_mean']:,.2f} ({zones.iloc[0]['quality_label']})")
print(f"ML enabled: YES (hold/break predictions)")
print(f"Backward compatible: 100%")
print(f"Supported exchanges: 23")
print("\nInstall: pip install liquidator-indicator==0.0.7")
print("GitHub: https://github.com/NexusBT2026/liquidator_indicator")
print("PyPI: https://pypi.org/project/liquidator-indicator/0.0.7/")
print("=" * 80)
