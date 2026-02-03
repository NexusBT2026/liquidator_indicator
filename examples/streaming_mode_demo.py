"""Demo: Real-Time Streaming Mode - Live zone tracking with callbacks."""
from liquidator_indicator import Liquidator
import pandas as pd
import numpy as np
import time

print("=" * 70)
print("REAL-TIME STREAMING MODE DEMO")
print("=" * 70)
print("\nSimulating live trade stream with incremental zone updates...\n")

# Create streaming liquidator
L = Liquidator('BTC', mode='streaming', window_minutes=60)

# Register event handlers
def on_zone_formed(zone):
    """Called when new zone is detected."""
    print(f"🟢 NEW ZONE FORMED")
    print(f"   Price: ${zone['price_mean']:.2f}")
    print(f"   Range: ${zone['entry_low']:.2f} - ${zone['entry_high']:.2f}")
    print(f"   Volume: ${zone['total_usd']:,.0f}")
    print(f"   Quality: {zone['quality_score']:.0f}/100 ({zone['quality_label']})")
    print(f"   Strength: {zone['strength']:.3f}")
    print(f"   Side: {zone['dominant_side']}")
    print()

def on_zone_updated(new_zone, old_zone):
    """Called when existing zone is updated."""
    volume_delta = new_zone['total_usd'] - old_zone['total_usd']
    count_delta = new_zone['count'] - old_zone['count']
    
    print(f"🔵 ZONE UPDATED")
    print(f"   Price: ${new_zone['price_mean']:.2f}")
    print(f"   Volume: ${old_zone['total_usd']:,.0f} → ${new_zone['total_usd']:,.0f} ({volume_delta:+,.0f})")
    print(f"   Count: {old_zone['count']} → {new_zone['count']} ({count_delta:+d} trades)")
    print(f"   Strength: {old_zone['strength']:.3f} → {new_zone['strength']:.3f}")
    print()

def on_zone_broken(zone):
    """Called when zone disappears (ages out or price moves away)."""
    print(f"🔴 ZONE BROKEN")
    print(f"   Price: ${zone['price_mean']:.2f}")
    print(f"   Final Volume: ${zone['total_usd']:,.0f}")
    print(f"   Final Strength: {zone['strength']:.3f}")
    print()

L.on_zone_formed(on_zone_formed)
L.on_zone_updated(on_zone_updated)
L.on_zone_broken(on_zone_broken)

# Simulate live trade stream
now = pd.Timestamp.now(tz='UTC')

# Batch 1: Initial trades create zones
print("=" * 70)
print("BATCH 1: Initial trades (t=0s)")
print("=" * 70)

batch1 = []
for i in range(40):
    batch1.append({
        'time': now - pd.Timedelta(minutes=i % 30),
        'px': 80000 + np.random.randn() * 5,
        'sz': 1.5,
        'side': 'A'
    })

for i in range(25):
    batch1.append({
        'time': now - pd.Timedelta(minutes=i % 20),
        'px': 79500 + np.random.randn() * 8,
        'sz': 1.0,
        'side': 'B'
    })

zones = L.update_incremental(batch1)
print(f"Current zones: {len(zones)}")
time.sleep(1)

# Batch 2: More trades strengthen existing zone
print("=" * 70)
print("BATCH 2: Strengthening existing zone (t=1s)")
print("=" * 70)

batch2 = []
for i in range(20):
    batch2.append({
        'time': now - pd.Timedelta(minutes=i % 10),
        'px': 80000 + np.random.randn() * 4,
        'sz': 1.8,
        'side': 'A'
    })

zones = L.update_incremental(batch2)
print(f"Current zones: {len(zones)}")
time.sleep(1)

# Batch 3: New zone appears at different price
print("=" * 70)
print("BATCH 3: New zone forms (t=2s)")
print("=" * 70)

batch3 = []
for i in range(30):
    batch3.append({
        'time': now - pd.Timedelta(minutes=i % 15),
        'px': 80500 + np.random.randn() * 6,
        'sz': 1.3,
        'side': 'B'
    })

zones = L.update_incremental(batch3)
print(f"Current zones: {len(zones)}")
time.sleep(1)

# Batch 4: High-quality zone
print("=" * 70)
print("BATCH 4: High-quality zone (tight cluster, high volume) (t=3s)")
print("=" * 70)

batch4 = []
for i in range(50):
    batch4.append({
        'time': now - pd.Timedelta(minutes=i % 5),
        'px': 81000 + np.random.randn() * 2,
        'sz': 2.5,
        'side': 'A'
    })

zones = L.update_incremental(batch4)
print(f"Current zones: {len(zones)}")

# Summary
print("\n" + "=" * 70)
print("FINAL ZONE SUMMARY")
print("=" * 70)

if not zones.empty:
    print(f"\nTotal active zones: {len(zones)}")
    print("\nTop 3 zones by strength:")
    top_zones = zones.nlargest(3, 'strength')
    
    for idx, zone in top_zones.iterrows():
        print(f"\n  Zone #{idx + 1}:")
        print(f"    Price: ${zone['price_mean']:.2f}")
        print(f"    Entry: ${zone['entry_low']:.2f} - ${zone['entry_high']:.2f}")
        print(f"    Volume: ${zone['total_usd']:,.0f}")
        print(f"    Count: {zone['count']} trades")
        print(f"    Quality: {zone['quality_score']:.0f}/100 ({zone['quality_label']})")
        print(f"    Strength: {zone['strength']:.3f}")
        print(f"    Side: {zone['dominant_side']}")

print("\n" + "=" * 70)
print("💡 USE CASES FOR STREAMING MODE")
print("=" * 70)
print("""
1. Live Trading Bots:
   - React instantly when new liquidation zones form
   - Adjust positions when zones strengthen/weaken
   - Exit when zones break

2. Real-Time Alerts:
   - Send notifications when strong zones appear
   - Alert on zone updates near current price
   - Monitor zone lifecycle for risk management

3. Dashboard Applications:
   - Update UI in real-time as zones change
   - Show live zone formation/breaking events
   - Visualize zone evolution over time

4. Backtesting with Events:
   - Replay historical data trade-by-trade
   - Track exact moment zones formed/broke
   - Measure zone effectiveness

Example Integration:
-------------------
# In your trading bot
L = Liquidator('BTC', mode='streaming')

def alert_new_zone(zone):
    if zone['quality_label'] == 'strong':
        send_telegram_alert(f"Strong zone at ${zone['price_mean']:.2f}")
        
L.on_zone_formed(alert_new_zone)

# In your WebSocket handler
async def on_trade(trade_data):
    zones = L.update_incremental([trade_data])
    # Callbacks automatically triggered!
""")
