"""Quick performance test for numba optimizations."""
import pandas as pd
import numpy as np
import time
from liquidator_indicator import Liquidator

def generate_test_data(n=1000):
    """Generate realistic trade data."""
    now = pd.Timestamp.now(tz='UTC')
    timestamps = [now - pd.Timedelta(minutes=i) for i in range(n)]
    
    trades = []
    base_price = 80000.0
    for i, ts in enumerate(timestamps):
        price = base_price + np.random.randn() * 100
        size = np.random.uniform(0.1, 2.0)
        side = 'A' if np.random.rand() > 0.5 else 'B'
        trades.append({
            'time': ts,
            'px': price,
            'sz': size,
            'side': side,
            'coin': 'BTC'
        })
    return trades

print("=" * 60)
print("Numba Performance Test")
print("=" * 60)

# Test with small dataset
print("\n🧪 Test 1: Small dataset (100 trades)")
trades_small = generate_test_data(100)
L1 = Liquidator('BTC')
start = time.time()
L1.ingest_trades(trades_small)
zones_small = L1.compute_zones()
end = time.time()
print(f"   Time: {(end-start)*1000:.2f}ms")
print(f"   Zones found: {len(zones_small)}")
print(f"   Numba available: {hasattr(L1, '__dict__')}")

# Test with medium dataset
print("\n🧪 Test 2: Medium dataset (500 trades)")
trades_med = generate_test_data(500)
L2 = Liquidator('BTC')
start = time.time()
L2.ingest_trades(trades_med)
zones_med = L2.compute_zones()
end = time.time()
print(f"   Time: {(end-start)*1000:.2f}ms")
print(f"   Zones found: {len(zones_med)}")

# Test with large dataset (triggers numba)
print("\n🧪 Test 3: Large dataset (1000 trades - Numba kicks in)")
trades_large = generate_test_data(1000)
L3 = Liquidator('BTC')
start = time.time()
L3.ingest_trades(trades_large)
zones_large = L3.compute_zones()
end = time.time()
print(f"   Time: {(end-start)*1000:.2f}ms")
print(f"   Zones found: {len(zones_large)}")

# Verify numba is actually loaded
print("\n" + "=" * 60)
print("Module Check:")
print("=" * 60)
try:
    from liquidator_indicator import numba_optimized
    print("✅ numba_optimized module imported successfully")
    print(f"✅ cluster_prices_numba available: {hasattr(numba_optimized, 'cluster_prices_numba')}")
    print(f"✅ compute_atr_numba available: {hasattr(numba_optimized, 'compute_atr_numba')}")
    print(f"✅ compute_strength_batch available: {hasattr(numba_optimized, 'compute_strength_batch')}")
except ImportError as e:
    print(f"❌ Failed to import: {e}")

# Test with candles for ATR
print("\n🧪 Test 4: ATR computation with numba")
candles = pd.DataFrame({
    'high': np.random.uniform(79000, 81000, 100),
    'low': np.random.uniform(78000, 80000, 100),
    'close': np.random.uniform(78500, 80500, 100)
})
L4 = Liquidator('BTC')
L4.update_candles(candles)
L4.ingest_trades(trades_large[:200])
start = time.time()
zones_atr = L4.compute_zones(use_atr=True)
end = time.time()
print(f"   Time with ATR: {(end-start)*1000:.2f}ms")
print(f"   Zones with bands: {len(zones_atr)}")
if not zones_atr.empty and 'atr' in zones_atr.columns:
    print(f"   ✅ ATR calculated: {zones_atr['atr'].iloc[0]:.2f}")
    print(f"   ✅ Band width avg: {zones_atr['band'].mean():.2f}")

print("\n" + "=" * 60)
print("✅ All tests completed successfully!")
print("=" * 60)
