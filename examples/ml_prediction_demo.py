"""Demo: ML-Powered Zone Hold/Break Predictions

Shows how to use machine learning to predict whether liquidation zones
will hold (price bounces) or break (price penetrates through).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from liquidator_indicator import Liquidator, ZonePredictor
import pandas as pd
import numpy as np

print("=" * 80)
print("ML-POWERED ZONE PREDICTIONS - Demo")
print("=" * 80)
print()

# Generate sample trade data
now = pd.Timestamp.now(tz='UTC')
trades = []

for i in range(25):
    trades.append({
        'time': now - pd.Timedelta(minutes=i % 8),
        'px': 80000 + np.random.randn() * 5,
        'sz': 1.2,
        'side': 'A'
    })

for i in range(12):
    trades.append({
        'time': now - pd.Timedelta(minutes=20 + i % 5),
        'px': 79500 + np.random.randn() * 20,
        'sz': 0.6,
        'side': 'B'
    })

print(f"Generated {len(trades)} sample trades")
print()

# Setup
L = Liquidator('BTC', cutoff_hours=None)
L.enable_ml_predictions()
print("ML predictions enabled")
print()

# Train
print("Training ML predictor with synthetic data...")
metrics = L.train_ml_predictor(use_synthetic=True, n_synthetic=250)
print(f"  Data source: {metrics['data_source']}")
print(f"  Training accuracy: {metrics['train_accuracy']:.1%}")
print(f"  Samples: {metrics['n_samples']}")
print()

# Compute zones
L.ingest_trades(trades)
zones = L.compute_zones()
print(f"Found {len(zones)} zones")
print()

# Add ML predictions
current_price = 79800
zones_ml = L.compute_zones_with_prediction(current_price=current_price)
print("ML predictions added")
print()

# Display results
print("=" * 80)
print("ZONE PREDICTIONS")
print("=" * 80)
print()

for idx, zone in zones_ml.iterrows():
    print(f"Zone {idx+1}: ${zone['price_mean']:.2f}")
    print(f"  Side: {zone['dominant_side'].upper()}")
    print(f"  Quality: {zone['quality_label'].upper()} ({zone['quality_score']:.1f}/100)")
    print()
    print(f"  ML PREDICTION: {zone['ml_prediction']}")
    print(f"     Hold probability: {zone['hold_probability']:.1f}%")
    print(f"     Break probability: {zone['break_probability']:.1f}%")
    print(f"     Confidence: {zone['prediction_confidence']:.1f}/100")
    print()
    
    # Trading recommendation
    if zone['ml_prediction'] == 'HOLD' and zone['prediction_confidence'] > 60:
        print(f"  TRADING SIGNAL: High confidence FADE setup")
        if zone['dominant_side'] == 'long':
            print(f"     -> SHORT near ${zone['entry_high']:.2f}")
        else:
            print(f"     -> LONG near ${zone['entry_low']:.2f}")
    elif zone['ml_prediction'] == 'BREAK' and zone['prediction_confidence'] > 60:
        print(f"  CAUTION: Zone likely to break")
    else:
        print(f"  Moderate confidence - wait for confirmation")
    
    print()
    print("-" * 80)
    print()

# Test lifecycle tracking
print("=" * 80)
print("ZONE LIFECYCLE TRACKING")
print("=" * 80)
print()
print("Simulating price touching Zone 1...")
L.update_zone_touches(zones_ml.iloc[0]['price_mean'])
print(f"Zone 1 touched")
print()

print("Recording Zone 1 outcome (HOLD)...")
L.record_zone_outcome(
    zone_price=zones_ml.iloc[0]['price_mean'],
    outcome='HOLD',
    current_price=current_price,
    current_time=now
)
print("Outcome recorded")
print()

# Get metrics
print("=" * 80)
print("ML PERFORMANCE METRICS")
print("=" * 80)
print()

# Accumulate outcomes for metrics
for i in range(15):
    L.record_zone_outcome(
        zone_price=80000 + i * 100,
        outcome='HOLD' if np.random.rand() > 0.4 else 'BREAK',
        current_price=80000,
        current_time=now
    )

metrics = L.get_ml_metrics()
print(f"Total zones tracked: {metrics['n_zones']}")

if 'error' in metrics:
    print(f"Note: {metrics['error']}")
else:
    print(f"Win rate: {metrics['win_rate']}%")
    print(f"SQN score: {metrics['sqn_score']:.2f} ({metrics['interpretation']})")
print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print("ML predictions add intelligence to zone analysis:")
print("  * Predict which zones will hold vs break")
print("  * Confidence scores for trade decisions")
print("  * SQN-style performance metrics")
print("  * Learn from real zone outcomes over time")
print()
print("=" * 80)
