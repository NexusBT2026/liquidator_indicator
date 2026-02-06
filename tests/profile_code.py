"""Profile liquidator_indicator to identify bottlenecks."""
import cProfile
import pstats
import io
import pandas as pd
import numpy as np
from liquidator_indicator import Liquidator

# Generate realistic test data
def generate_large_dataset(n=5000):
    now = pd.Timestamp.now(tz='UTC')
    trades = []
    base_price = 80000.0
    
    for i in range(n):
        ts = now - pd.Timedelta(minutes=i % 120)  # Spread over 2 hours
        price = base_price + np.random.randn() * 200
        size = np.random.uniform(0.05, 3.0)
        side = 'A' if np.random.rand() > 0.5 else 'B'
        trades.append({
            'time': ts,
            'px': price,
            'sz': size,
            'side': side,
            'coin': 'BTC'
        })
    return trades

print("Generating test data...")
trades = generate_large_dataset(5000)

# Add candles for ATR testing
candles = pd.DataFrame({
    'high': np.random.uniform(79500, 80500, 200),
    'low': np.random.uniform(79000, 80000, 200),
    'close': np.random.uniform(79200, 80300, 200)
})

print("Starting profiling...\n")

# Profile the hot path
profiler = cProfile.Profile()
profiler.enable()

L = Liquidator('BTC', pct_merge=0.003, zone_vol_mult=1.5)
L.update_candles(candles)
L.ingest_trades(trades)
zones = L.compute_zones(use_atr=True)

profiler.disable()

# Print results
s = io.StringIO()
ps = pstats.Stats(profiler, stream=s)
ps.strip_dirs()
ps.sort_stats('cumulative')
ps.print_stats(30)  # Top 30 functions

print("=" * 80)
print("TOP 30 HOTSPOTS (by cumulative time)")
print("=" * 80)
print(s.getvalue())

# Also sort by total time
s2 = io.StringIO()
ps2 = pstats.Stats(profiler, stream=s2)
ps2.strip_dirs()
ps2.sort_stats('tottime')
ps2.print_stats(20)

print("\n" + "=" * 80)
print("TOP 20 HOTSPOTS (by total time)")
print("=" * 80)
print(s2.getvalue())

print(f"\n✅ Found {len(zones)} zones")
print(f"✅ Processing {len(trades)} trades")
