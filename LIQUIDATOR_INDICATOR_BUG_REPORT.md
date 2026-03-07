# Bug Report: liquidator-indicator v0.0.8

**Report Date:** February 15, 2026  
**Package Version:** 0.0.8  
**Reporter:** QUANT_APP Integration Testing

---

## Executive Summary

Two critical bugs have been identified in the `liquidator-indicator` package:

1. **CRITICAL:** `compute_zones()` corrupts timestamp values, storing them as microseconds but interpreting them as nanoseconds, resulting in 1970 epoch dates instead of correct 2026 dates
2. **DESIGN LIMITATION:** Multi-timeframe zone computation (10m, 1h, 4h simultaneously) is not supported due to time-based filtering conflicts

---

## Bug #1: Timestamp Corruption in compute_zones()

### Severity: CRITICAL
### Impact: Zone strength calculations return 0.0, zones show incorrect timestamps

### Description

The `compute_zones()` method corrupts timestamp values during the clustering phase. Data is stored correctly in `_inferred_liqs` with proper 2026 timestamps, but when zones are computed, the `first_ts` and `last_ts` fields show 1970 epoch dates instead.

### Root Cause

During clustering, timestamp values are being stored as **microseconds** (or an intermediate conversion happens), but when the DataFrame is constructed, pandas interprets these values as **nanoseconds**, causing a 1000x time scale error that shifts dates from 2026 back to 1970.

### Evidence

#### Input Data (Correct):
```python
# Internal _inferred_liqs DataFrame
                         timestamp  side coin    price    usd_value
0 2026-02-15 08:12:26.904000+00:00  long  BTC  70763.0  69448.22346
1 2026-02-15 08:12:30.590000+00:00  long  BTC  70762.0  10490.46650
2 2026-02-15 08:12:37.564000+00:00  long  BTC  70762.0  60483.81950
```

#### Output Data (CORRUPTED):
```python
# Zones DataFrame from compute_zones()
   price_mean  total_usd  count                         first_ts                          last_ts  strength
0  70317.4638  2.717e+07    414 1970-01-21 11:59:04.236869+00:00 1970-01-21 11:59:05.313145+00:00  0.0000258
1  70679.1908  5.412e+06    173 1970-01-21 11:59:03.146904+00:00 1970-01-21 11:59:04.257784+00:00  0.0000258
```

#### Verification of Bug:
```python
# Zone 0 last_ts shows: 1970-01-21 11:59:05.313145+00:00
# Its .value is: 1771145313145000

# If we interpret this as MICROSECONDS instead of nanoseconds:
pd.Timestamp(1771145313145000, unit='us', tz='UTC')
# Result: 2026-02-15 08:48:33.145000+00:00  ✅ MATCHES INTERNAL DATA!

# This timestamp exists in _inferred_liqs:
timestamp  side   coin  price     usd_value
2026-02-15 08:48:33.145000+00:00  short  BTC   70377.0  14908.66368  ✅ EXACT MATCH
```

### Impact on Strength Calculation

The strength formula uses a recency weight:
```python
recency_weight = 1 / (1 + (age_seconds / 3600))
```

With 1970 timestamps:
- Age = ~56 years = ~491,000 hours
- recency_weight ≈ 0.000002
- strength ≈ 0.0 (near zero)

With correct 2026 timestamps:
- Age = ~0-36 minutes = ~0-0.6 hours
- recency_weight ≈ 0.6-1.0
- strength should be 9-12 range

### Reproduction Steps

```python
import pandas as pd
from liquidator_indicator import Liquidator

# Create sample data with correct timestamps
data = [
    {'timestamp': pd.Timestamp('2026-02-15 08:12:26.904000+00:00'), 
     'price': 70763.0, 'size': 0.981, 'size_usd': 69448.22346, 'side': 'long'},
    {'timestamp': pd.Timestamp('2026-02-15 08:12:30.590000+00:00'), 
     'price': 70762.0, 'size': 0.148, 'size_usd': 10490.46650, 'side': 'long'},
    # ... more records
]

# Create liquidator and ingest
liq = Liquidator(window_minutes=10, cutoff_hours=None)
liq.ingest_trades(data)

# Check internal storage (CORRECT)
print(liq._inferred_liqs['timestamp'].iloc[0])
# Output: 2026-02-15 08:12:26.904000+00:00 ✅

# Compute zones (CORRUPTED)
zones = liq.compute_zones(window_minutes=10080)
print(zones.iloc[0]['last_ts'])
# Output: 1970-01-21 11:59:05.313145+00:00 ❌

# Verify corruption
wrong_ts = zones.iloc[0]['last_ts']
correct_ts = pd.Timestamp(wrong_ts.value, unit='us', tz='UTC')
print(correct_ts)
# Output: 2026-02-15 08:48:33.145000+00:00 ✅ (matches internal data)
```

### Suspected Code Location

The bug is likely in the clustering logic around line 95-120 of `liquidator_indicator/core.py` where clusters are built and timestamps are stored:

```python
# Suspected problematic code pattern:
for row in df.itertuples():
    ts = row.timestamp
    # ... clustering logic ...
    cur['ts_last'] = max(cur['ts_last'], ts)  # Stores Timestamp
    cur['ts_first'] = min(cur['ts_first'], ts_value)  # Might store .value?

# Later when building output:
for c in clusters:
    last_ts = c['ts_last']  # Gets integer microseconds instead of Timestamp?
    out_item = {
        'last_ts': last_ts,  # Wrong type/scale
        'strength': self._compute_strength(total_usd, count, last_ts)
    }

zones_df = pd.DataFrame(out)  # Pandas interprets integers as nanoseconds
```

### Suggested Fix

Ensure timestamps remain as `pd.Timestamp` objects throughout clustering:

```python
# Option 1: Force Timestamp conversion when building output
last_ts = c['ts_last']
if not isinstance(last_ts, pd.Timestamp):
    last_ts = pd.Timestamp(last_ts, unit='us', tz='UTC')  # or 'ns' depending on what's stored

# Option 2: Store as Timestamp explicitly
cur['ts_last'] = pd.Timestamp(max(cur['ts_last'], ts))

# Option 3: Post-process DataFrame to fix timestamps
zones_df['last_ts'] = pd.to_datetime(zones_df['last_ts'], unit='us', utc=True)
```

---

## Bug #2: Multi-Timeframe Limitation

### Severity: DESIGN LIMITATION
### Impact: Cannot compute zones for multiple timeframes (10m, 1h, 4h) simultaneously

### Description

The package's `compute_zones(window_minutes=X)` method filters data based on a time window:

```python
cutoff = now_ts - pd.Timedelta(minutes=window_minutes)
df_filtered = df[df['timestamp'] >= cutoff]
```

This design means:
- `compute_zones(window_minutes=10)` only sees last 10 minutes of data
- `compute_zones(window_minutes=60)` only sees last 1 hour of data
- `compute_zones(window_minutes=240)` only sees last 4 hours of data

For **persistent liquidation zones** that should accumulate over time, this filtering removes historical data that should still be relevant.

### Use Case Conflict

**Our Application Requirements:**
- Maintain liquidation zones that persist until "broken through"
- Display zones on multiple timeframes: 10m, 1h, 4h charts
- Each timeframe should show ALL zones, not just recent ones
- Zones should accumulate historical liquidations, not just recent window

**Package Design:**
- Assumes zones are time-bounded and ephemeral
- Filters data to only recent window
- Designed for "current market state" not "historical accumulation"

### Current Workaround

Set `window_minutes` to a very large value (e.g., 10080 = 1 week) to avoid filtering:

```python
# Works but not ideal:
liq = Liquidator(window_minutes=10, cutoff_hours=None)  # Initial window doesn't matter
zones = liq.compute_zones(window_minutes=10080)  # Use large window to bypass filtering
```

**Problem:** This defeats the purpose of having multiple timeframes. We cannot compute:
- 10m zones (only last 10 minutes)
- 1h zones (only last hour)
- 4h zones (only last 4 hours)

All simultaneously from the same `Liquidator` instance.

### Impact

1. **Cannot use multiple timeframes properly** - forced to choose one large window
2. **Zone counts differ from documentation** - 10m window shows far fewer zones than accumulated data should produce
3. **API confusion** - `Liquidator(window_minutes=X)` vs `compute_zones(window_minutes=Y)` both filter data differently

### Suggested Solutions

#### Option 1: Add `persistent_zones` mode
```python
liq = Liquidator(window_minutes=10, cutoff_hours=None, persistent_zones=True)
# In persistent mode, compute_zones() ignores time filtering
zones = liq.compute_zones()  # Returns ALL zones from ALL data
```

#### Option 2: Separate clustering from time filtering
```python
# Compute clusters from ALL data
clusters = liq.compute_clusters()

# Filter clusters by time window for display
zones_10m = liq.filter_zones(clusters, window_minutes=10)
zones_1h = liq.filter_zones(clusters, window_minutes=60)
zones_4h = liq.filter_zones(clusters, window_minutes=240)
```

#### Option 3: Remove time filtering from compute_zones()
```python
# Let the application handle time filtering
zones = liq.compute_zones()  # Returns ALL zones

# Application filters for different timeframes:
now = pd.Timestamp.now(tz='UTC')
zones_10m = zones[zones['last_ts'] >= now - pd.Timedelta(minutes=10)]
zones_1h = zones[zones['last_ts'] >= now - pd.Timedelta(hours=1)]
zones_4h = zones[zones['last_ts'] >= now - pd.Timedelta(hours=4)]
```

---

## Testing Artifacts

All reproduction scripts available in test directory:
- `test_exact_app_replication.py` - Reproduces timestamp bug
- `verify_microseconds_bug.py` - Proves microseconds/nanoseconds conversion issue
- `inspect_package_internals.py` - Shows internal storage vs output discrepancy
- `trace_clustering.py` - Traces time filtering behavior

---

## Environment

- Python: 3.11+
- pandas: 2.x
- liquidator-indicator: 0.0.8
- OS: Windows 11

---

## Questions for Package Maintainer

1. **Is the timestamp corruption a known issue?**
   - Our testing definitively proves timestamps are stored as microseconds but interpreted as nanoseconds

2. **Is multi-timeframe support intended?**
   - Documentation doesn't clarify if `window_minutes` should filter zones or just affect clustering

3. **What is the intended use case for `window_minutes` parameter?**
   - Initial window in `Liquidator(window_minutes=X)`
   - Filtering window in `compute_zones(window_minutes=Y)`
   - Are these meant to work together or separately?

4. **Should zones be persistent or ephemeral?**
   - Our use case requires persistent zones until broken
   - Package seems designed for ephemeral "current market state" zones

---

## Priority Recommendations

1. **HIGH PRIORITY:** Fix timestamp corruption (Bug #1) - makes strength calculations worthless
2. **MEDIUM PRIORITY:** Clarify/fix multi-timeframe support (Bug #2) - impacts API usability
3. **LOW PRIORITY:** Add documentation about time filtering behavior and intended use cases

---

## Verification Request

We have extensive test data and reproduction scripts. Package maintainer can verify:

1. Run `verify_microseconds_bug.py` against your test suite
2. Check if `c['ts_last']` in clustering code stores `.value` instead of `Timestamp`
3. Confirm if multi-timeframe support is intended or if we're using API incorrectly

**We are 95% confident Bug #1 is a package issue. We are 70% confident Bug #2 is a design limitation rather than a bug, but clarification needed.**
