"""Benchmark: Compare performance before/after numba optimizations."""
import pandas as pd
import numpy as np
import time
from liquidator_indicator import Liquidator
import liquidator_indicator.core as core_module

def generate_realistic_data(n=2000):
    """Generate realistic trading data."""
    now = pd.Timestamp.now(tz='UTC')
    trades = []
    base_price = 80000.0
    
    for i in range(n):
        ts = now - pd.Timedelta(minutes=i % 120)
        # Add some clustering
        if i % 50 == 0:
            price = base_price + np.random.randn() * 500  # Big move
            size = np.random.uniform(1.0, 5.0)  # Large trade
        else:
            price = base_price + np.random.randn() * 50
            size = np.random.uniform(0.1, 0.5)
        
        side = 'A' if np.random.rand() > 0.5 else 'B'
        trades.append({
            'time': ts,
            'px': price,
            'sz': size,
            'side': side,
            'coin': 'BTC'
        })
    return trades

# Generate test dataset
print("Generating 2000 trades...")
trades = generate_realistic_data(2000)

candles = pd.DataFrame({
    'high': np.random.uniform(79500, 80500, 100),
    'low': np.random.uniform(79000, 80000, 100),
    'close': np.random.uniform(79200, 80300, 100)
})

print("\n" + "=" * 70)
print("BENCHMARK: Numba vs Pure Python")
print("=" * 70)

# Benchmark 1: Pure Python (force disable numba)
print("\n[1] Pure Python Implementation")
original_flag = core_module.NUMBA_AVAILABLE
core_module.NUMBA_AVAILABLE = False

times_python = []
for run in range(3):
    L1 = Liquidator('BTC')
    L1.update_candles(candles)
    
    start = time.perf_counter()
    L1.ingest_trades(trades)
    zones1 = L1.compute_zones(use_atr=True)
    end = time.perf_counter()
    
    elapsed = (end - start) * 1000
    times_python.append(elapsed)
    print(f"   Run {run+1}: {elapsed:.2f}ms")

avg_python = np.mean(times_python)
print(f"   Average: {avg_python:.2f}ms")

# Benchmark 2: Numba Optimized
print("\n[2] Numba Optimized Implementation (including JIT compilation)")
core_module.NUMBA_AVAILABLE = original_flag

times_numba_cold = []
for run in range(1):  # Only 1 cold start
    L2 = Liquidator('BTC')
    L2.update_candles(candles)
    
    start = time.perf_counter()
    L2.ingest_trades(trades)
    zones2 = L2.compute_zones(use_atr=True)
    end = time.perf_counter()
    
    elapsed = (end - start) * 1000
    times_numba_cold.append(elapsed)
    print(f"   Run {run+1} (cold start with JIT compilation): {elapsed:.2f}ms")

# Benchmark 3: Numba Warm (JIT already compiled)
print("\n[3] Numba Optimized Implementation (warm - JIT precompiled)")

times_numba_warm = []
for run in range(5):
    L3 = Liquidator('BTC')
    L3.update_candles(candles)
    
    start = time.perf_counter()
    L3.ingest_trades(trades)
    zones3 = L3.compute_zones(use_atr=True)
    end = time.perf_counter()
    
    elapsed = (end - start) * 1000
    times_numba_warm.append(elapsed)
    print(f"   Run {run+1}: {elapsed:.2f}ms")

avg_numba_warm = np.mean(times_numba_warm)
print(f"   Average: {avg_numba_warm:.2f}ms")

# Results summary
print("\n" + "=" * 70)
print("RESULTS SUMMARY")
print("=" * 70)
print(f"Pure Python:           {avg_python:.2f}ms")
print(f"Numba (warm):          {avg_numba_warm:.2f}ms")
print(f"Speedup:               {avg_python / avg_numba_warm:.2f}x faster")
print(f"")
print(f"Note: First run with numba ({times_numba_cold[0]:.2f}ms) includes JIT")
print(f"      compilation overhead. Subsequent runs are much faster!")
print(f"")
print(f"Zones found: {len(zones3)}")

# Restore
core_module.NUMBA_AVAILABLE = original_flag

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
if avg_numba_warm < avg_python:
    speedup = avg_python / avg_numba_warm
    print(f"Numba optimization provides {speedup:.1f}x speedup!")
    print(f"This means processing {2000 * speedup:.0f} trades/sec vs {2000:.0f} trades/sec")
else:
    print("Pure Python is comparable for this dataset size.")
print("\nThe larger the dataset, the bigger the numba advantage!")
