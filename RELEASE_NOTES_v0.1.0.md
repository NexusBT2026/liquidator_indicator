# Release Notes — v0.1.0

**Release Date:** March 15, 2026
**Type:** Minor release — new analytical features, 100% backward compatible

---

## What's New

### Cascade Chain Detection — `add_cascade_analysis()`

The existing volume-spike cascade detector could already identify individual cascade *events*.
v0.1.0 completes this with full **cascade chain prediction**: when a liquidation zone is triggered,
the model now walks adjacent zones and scores how far the cascade is likely to travel.

```python
zones = L.compute_zones()
zones_with_cascade = L.add_cascade_analysis(
    zones,
    current_price=80000,
    funding_rate=0.0003,   # positive = longs paying = bearish bias
)

# New columns on every zone:
# cascade_probability   — 0-100 score: how likely this zone triggers a chain
# cascade_chain_length  — how many consecutive zones get swept
# cascade_target_price  — end price of the chain
```

**Score formula:**
```
cascade_probability = trigger_score × strength_score × chain_factor × funding_multiplier
```

- `trigger_score` — exponential decay with distance from current price
- `strength_score` — normalised zone liquidity relative to largest zone
- `chain_factor` — `log1p(chain_length)` — longer chains score higher
- `funding_multiplier` — amplified when funding bias aligns with cascade direction

**Parameters:**
| Parameter | Default | Description |
|---|---|---|
| `cascade_window_pct` | 0.05 (5%) | Max distance from price for trigger candidates |
| `chain_gap_pct` | 0.01 (1%) | Max gap between consecutive zones for chain to continue |
| `funding_rate` | 0.0 | Current funding rate (positive = bearish bias) |

---

### Gravity Model — `add_gravity_scores()` and `get_gravity_target()`

Price is attracted toward liquidity clusters. The closer and larger a cluster is, the stronger
its pull. This is now calculated explicitly using the **liquidity gravity formula**.

```python
zones_with_gravity = L.add_gravity_scores(zones, current_price=80000)

# New columns on every zone:
# gravity       — raw gravitational force (larger = stronger price magnet)
# gravity_rank  — 1 = strongest pull = next probable target
```

**Formula:**
```
gravity = total_usd / distance²
```

A $6M cluster 500 points away pulls 24× harder than a $1M cluster at the same distance.
A $6M cluster 250 points away pulls 4× harder than the same cluster at 500 points.

**Quick target lookup:**
```python
target = L.get_gravity_target(zones, current_price=80000)
# Returns: {'price_mean': 70915.0, 'gravity': 24800.0, 'gravity_rank': 1, ...}
```

---

## Combining Both Features

```python
zones = L.compute_zones()

# Add gravity scores to find next probable target
zones = L.add_gravity_scores(zones, current_price=current_px)

# Add cascade analysis to score chain risk
zones = L.add_cascade_analysis(zones, current_price=current_px, funding_rate=funding)

# Get the single most probable next target
target = L.get_gravity_target(zones, current_price=current_px)
print(f"Next target: {target['price_mean']:.0f}  |  Gravity rank: {target['gravity_rank']}")

# Find highest cascade risk zone
top_cascade = zones.nlargest(1, 'cascade_probability').iloc[0]
print(f"Cascade risk zone: {top_cascade['price_mean']:.0f}  |  Probability: {top_cascade['cascade_probability']:.1f}%")
print(f"Chain length: {top_cascade['cascade_chain_length']}  |  Target: {top_cascade['cascade_target_price']:.0f}")
```

---

## Backward Compatibility

- ✅ All existing `compute_zones()` output is unchanged
- ✅ `add_cascade_analysis()` and `add_gravity_scores()` are opt-in — call them only when needed
- ✅ Neither method modifies the `Liquidator` instance state
- ✅ Both return a copy of the input DataFrame with new columns appended
- ✅ Both handle empty DataFrames and invalid `current_price` gracefully

---

## Tests

19 tests in `tests/test_core.py` — all passing (Python 3.12, pytest 8.4.2).

New tests cover:
- Column presence, probability range, chain length minimum
- Closer zone → higher cascade probability
- Tightly spaced zones form multi-zone chains
- Funding bias amplification
- Gravity ordering (closer + larger = rank 1)
- `get_gravity_target()` return shape and correctness
- Edge cases: empty DataFrame, `current_price=0`

---

## Contributors

- [@ViWarshawski](https://github.com/ViWarshawski) — core development
- [@arosstale](https://github.com/arosstale) — code quality improvements (v0.0.9)

---

## Upgrade

```bash
pip install --upgrade liquidator-indicator
```
