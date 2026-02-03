"""Demo: Zone Quality Scoring - Filter for high-confidence liquidation zones."""
from liquidator_indicator import Liquidator
import pandas as pd
import numpy as np

# Generate sample trade data
now = pd.Timestamp.now(tz='UTC')
trades = []

# Create some high-quality zones (recent, high volume, tight)
for i in range(30):
    trades.append({
        'time': now - pd.Timedelta(minutes=i % 10),
        'px': 80000 + np.random.randn() * 3,
        'sz': 1.5,
        'side': 'A'
    })

# Add medium-quality zones (older, medium volume, moderate spread)
for i in range(15):
    trades.append({
        'time': now - pd.Timedelta(minutes=45 + i % 5),
        'px': 79500 + np.random.randn() * 15,
        'sz': 0.5,
        'side': 'B'
    })

# Add low-quality zones (old, low volume, wide spread)
for i in range(5):
    trades.append({
        'time': now - pd.Timedelta(hours=2, minutes=i * 5),
        'px': 78500 + np.random.randn() * 40,
        'sz': 0.1,
        'side': 'A'
    })

# Example 1: Get all zones with quality scores
print("=" * 70)
print("Example 1: All Zones with Quality Scores")
print("=" * 70)
L = Liquidator('BTC')
L.ingest_trades(trades)
zones_all = L.compute_zones()

print(f"\nFound {len(zones_all)} total zones:\n")
for idx, zone in zones_all.iterrows():
    print(f"Zone {idx+1}: ${zone['price_mean']:.2f}")
    print(f"  Quality: {zone['quality_score']:.1f}/100 ({zone['quality_label']})")
    print(f"  Count: {zone['count']} trades, Volume: ${zone['total_usd']:,.0f}")
    print(f"  Age: {(now - zone['last_ts']).total_seconds() / 60:.0f} minutes")
    print()

# Example 2: Filter for medium+ quality zones only
print("=" * 70)
print("Example 2: Filter for Medium+ Quality Zones")
print("=" * 70)
zones_medium = L.compute_zones(min_quality='medium')
print(f"\nFound {len(zones_medium)} medium+ quality zones")
print(f"Quality scores: {zones_medium['quality_score'].tolist()}\n")

# Example 3: Filter for strong quality zones only (trading signals)
print("=" * 70)
print("Example 3: Strong Quality Zones Only (Trading Signals)")
print("=" * 70)
zones_strong = L.compute_zones(min_quality='strong')
print(f"\nFound {len(zones_strong)} strong quality zones")

if not zones_strong.empty:
    print("\n🎯 High-confidence trading zones:")
    for idx, zone in zones_strong.iterrows():
        print(f"\n  ${zone['entry_low']:.2f} - ${zone['entry_high']:.2f}")
        print(f"  Quality: {zone['quality_score']:.1f}/100")
        print(f"  Strength: {zone['strength']:.2f}")
        print(f"  Dominant side: {zone['dominant_side']}")
else:
    print("\n⚠️  No strong zones found - wait for better setups")

# Example 4: Sort by quality score
print("\n" + "=" * 70)
print("Example 4: Top 3 Highest Quality Zones")
print("=" * 70)
top_zones = zones_all.nlargest(3, 'quality_score')
for idx, zone in enumerate(top_zones.itertuples(), 1):
    print(f"\n#{idx}: ${zone.price_mean:.2f}")
    print(f"   Quality: {zone.quality_score:.1f}")
    print(f"   Volume: ${zone.total_usd:,.0f}")
    print(f"   Tightness: ${zone.price_max - zone.price_min:.2f} spread")

print("\n" + "=" * 70)
print("💡 Use min_quality parameter to focus on actionable zones!")
print("=" * 70)
