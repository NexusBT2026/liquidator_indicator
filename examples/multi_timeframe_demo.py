"""Demo: Multi-Timeframe Zone Analysis - Find zones that align across multiple timeframes."""
from liquidator_indicator import Liquidator
import pandas as pd
import numpy as np

# Generate sample trade data
now = pd.Timestamp.now(tz='UTC')
trades = []

# Strong zone: Recent high-volume trades at $80,000 (visible on ALL timeframes)
for i in range(80):
    trades.append({
        'time': now - pd.Timedelta(minutes=i % 45),
        'px': 80000 + np.random.randn() * 4,
        'sz': 2.0,
        'side': 'A'
    })

# Medium zone: Older trades at $79,500 (visible on 15m, 1h, 2h, 1d)
for i in range(40):
    trades.append({
        'time': now - pd.Timedelta(minutes=40 + i * 2),
        'px': 79500 + np.random.randn() * 12,
        'sz': 1.0,
        'side': 'B'
    })

# Long-term zone: Old trades at $78,000 (visible on 2h, 1d only)
for i in range(25):
    trades.append({
        'time': now - pd.Timedelta(hours=4 + i * 0.3),
        'px': 78000 + np.random.randn() * 18,
        'sz': 0.7,
        'side': 'A'
    })

# Short-term zone: Very recent at $80,500 (5m only)
for i in range(12):
    trades.append({
        'time': now - pd.Timedelta(minutes=i % 4),
        'px': 80500 + np.random.randn() * 2,
        'sz': 0.4,
        'side': 'B'
    })

L = Liquidator('BTC')
L.ingest_trades(trades)

# Example 1: Analyze all timeframes
print("=" * 70)
print("Example 1: Multi-Timeframe Zone Analysis")
print("=" * 70)
all_tf_zones = L.compute_multi_timeframe_zones()

print(f"\nFound {len(all_tf_zones)} zones across all timeframes (5m, 15m, 1h, 2h, 1d)\n")

# Group by timeframe
for tf in ['5m', '15m', '1h', '2h', '1d']:
    tf_zones = all_tf_zones[all_tf_zones['timeframe'] == tf]
    print(f"{tf:4s}: {len(tf_zones)} zones")

# Example 2: High-alignment zones (appear in multiple timeframes)
print("\n" + "=" * 70)
print("Example 2: High-Alignment Zones (Strong Multi-TF Confirmation)")
print("=" * 70)
high_alignment = all_tf_zones[all_tf_zones['alignment_score'] >= 75]

print(f"\nFound {len(high_alignment)} zones with 75%+ alignment")
print("\n🎯 Top 3 zones with strongest cross-timeframe confirmation:")

for idx, zone in high_alignment.head(3).iterrows():
    print(f"\n  ${zone['price_mean']:.2f} ({zone['timeframe']})")
    print(f"    Alignment: {zone['alignment_score']:.0f}/100")
    print(f"    Quality: {zone['quality_score']:.1f}/100 ({zone['quality_label']})")
    print(f"    Volume: ${zone['total_usd']:,.0f}")
    print(f"    Entry range: ${zone['entry_low']:.2f} - ${zone['entry_high']:.2f}")

# Example 3: Specific timeframe combinations
print("\n" + "=" * 70)
print("Example 3: Custom Timeframe Analysis (1h, 2h, 1d)")
print("=" * 70)
swing_zones = L.compute_multi_timeframe_zones(timeframes=['1h', '2h', '1d'])

print(f"\nSwing trading zones (longer timeframes): {len(swing_zones)} found")
swing_aligned = swing_zones[swing_zones['alignment_score'] > 50]
print(f"High-alignment swing zones: {len(swing_aligned)}")

# Example 4: Scalping zones (short timeframes)
print("\n" + "=" * 70)
print("Example 4: Scalping Zones (5m, 15m)")
print("=" * 70)
scalp_zones = L.compute_multi_timeframe_zones(timeframes=['5m', '15m'])

print(f"\nScalping zones (short timeframes): {len(scalp_zones)} found")
if not scalp_zones.empty:
    best_scalp = scalp_zones.iloc[0]
    print(f"\nBest scalping zone:")
    print(f"  Price: ${best_scalp['price_mean']:.2f}")
    print(f"  Timeframe: {best_scalp['timeframe']}")
    print(f"  Quality: {best_scalp['quality_score']:.1f}/100")

# Example 5: Filter by quality + alignment
print("\n" + "=" * 70)
print("Example 5: Premium Zones (Strong Quality + High Alignment)")
print("=" * 70)
premium_zones = L.compute_multi_timeframe_zones(min_quality='strong')
premium_zones = premium_zones[premium_zones['alignment_score'] >= 50]

print(f"\nFound {len(premium_zones)} premium zones")
print("(Strong quality + appearing in multiple timeframes)")

if not premium_zones.empty:
    print("\n💎 Premium trading opportunities:")
    for idx, zone in premium_zones.head(5).iterrows():
        print(f"\n  ${zone['price_mean']:.2f} ({zone['timeframe']})")
        print(f"    Alignment: {zone['alignment_score']:.0f}% | Quality: {zone['quality_score']:.1f}/100")
        print(f"    Side: {zone['dominant_side']} | Strength: {zone['strength']:.2f}")

print("\n" + "=" * 70)
print("💡 Trading Strategy Tips:")
print("=" * 70)
print("- High alignment (>75%) = Strong multi-timeframe confirmation")
print("- 5m/15m alignment = Good for scalping entries")
print("- 1h/2h/1d alignment = Swing trade key levels")
print("- Combine alignment_score + quality_score for best setups")
