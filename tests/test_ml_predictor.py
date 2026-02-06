"""Tests for ML-powered zone hold/break predictions."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
import pandas as pd
import numpy as np
from liquidator_indicator import Liquidator, ZonePredictor

class TestMLPredictor(unittest.TestCase):
    """Test ML prediction functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.now = pd.Timestamp.now(tz='UTC')
        
        # Create sample zone
        self.sample_zone = {
            'price_mean': 80000.0,
            'price_min': 79990.0,
            'price_max': 80010.0,
            'total_usd': 500000.0,
            'count': 15,
            'quality_score': 75.0,
            'alignment_score': 60.0,
            'last_ts': self.now - pd.Timedelta(hours=2)
        }
        
        # Create sample trades
        self.sample_trades = []
        for i in range(30):
            self.sample_trades.append({
                'time': self.now - pd.Timedelta(minutes=i),
                'px': 80000 + np.random.randn() * 10,
                'sz': 1.0,
                'side': 'A' if i % 2 == 0 else 'B'
            })
    
    def test_predictor_initialization(self):
        """Test ZonePredictor initialization."""
        predictor = ZonePredictor()
        
        self.assertFalse(predictor.is_trained)
        self.assertEqual(len(predictor.feature_names), 10)
        self.assertIsNotNone(predictor.model)
        self.assertIsNotNone(predictor.scaler)
    
    def test_feature_extraction(self):
        """Test feature extraction from zone."""
        predictor = ZonePredictor()
        
        features = predictor.extract_features(
            zone=self.sample_zone,
            current_price=80200.0,
            current_time=self.now,
            touch_count=2,
            funding_rate=0.0005
        )
        
        self.assertEqual(len(features), 10)
        self.assertIsInstance(features, np.ndarray)
        
        # Check feature types
        self.assertGreater(features[0], 0)  # volume_log
        self.assertGreaterEqual(features[1], 0)  # recency_hours
        self.assertGreater(features[2], 0)  # density
        self.assertGreater(features[3], 0)  # tightness
        self.assertEqual(features[4], 75.0)  # quality_score
        self.assertEqual(features[5], 60.0)  # alignment_score
        self.assertEqual(features[8], 2)  # touch_count
        self.assertEqual(features[9], 0.0)  # funding_extreme (0.0005 < 0.001)
    
    def test_synthetic_data_generation(self):
        """Test synthetic training data generation."""
        data = ZonePredictor.generate_synthetic_training_data(n_samples=100)
        
        self.assertEqual(len(data), 100)
        
        # Check record structure
        for record in data[:5]:
            self.assertIn('zone', record)
            self.assertIn('current_price', record)
            self.assertIn('current_time', record)
            self.assertIn('outcome', record)
            self.assertIn('touch_count', record)
            self.assertIn('funding_rate', record)
            
            self.assertIn(record['outcome'], [0, 1])
            self.assertIsInstance(record['zone'], dict)
    
    def test_model_training(self):
        """Test model training on synthetic data."""
        predictor = ZonePredictor()
        
        # Generate training data
        training_data = ZonePredictor.generate_synthetic_training_data(n_samples=150)
        
        # Train model
        metrics = predictor.train(training_data)
        
        self.assertTrue(predictor.is_trained)
        self.assertIn('train_accuracy', metrics)
        self.assertIn('n_samples', metrics)
        self.assertIn('hold_ratio', metrics)
        
        self.assertEqual(metrics['n_samples'], 150)
        self.assertGreater(metrics['train_accuracy'], 0.5)  # Better than random
        self.assertGreater(metrics['hold_ratio'], 0.0)
        self.assertLess(metrics['hold_ratio'], 1.0)
    
    def test_prediction(self):
        """Test zone hold/break prediction."""
        predictor = ZonePredictor()
        
        # Train model
        training_data = ZonePredictor.generate_synthetic_training_data(n_samples=100)
        predictor.train(training_data)
        
        # Make prediction
        prediction = predictor.predict(
            zone=self.sample_zone,
            current_price=80100.0,
            current_time=self.now,
            touch_count=1,
            funding_rate=0.0001
        )
        
        self.assertIn('hold_probability', prediction)
        self.assertIn('break_probability', prediction)
        self.assertIn('prediction_confidence', prediction)
        self.assertIn('prediction', prediction)
        
        # Check probability bounds
        self.assertGreaterEqual(prediction['hold_probability'], 0)
        self.assertLessEqual(prediction['hold_probability'], 100)
        self.assertGreaterEqual(prediction['break_probability'], 0)
        self.assertLessEqual(prediction['break_probability'], 100)
        
        # Probabilities sum to ~100
        total_prob = prediction['hold_probability'] + prediction['break_probability']
        self.assertAlmostEqual(total_prob, 100.0, places=0)
        
        # Prediction matches probabilities
        if prediction['hold_probability'] > prediction['break_probability']:
            self.assertEqual(prediction['prediction'], 'HOLD')
        else:
            self.assertEqual(prediction['prediction'], 'BREAK')
    
    def test_predict_zones_dataframe(self):
        """Test predicting on zones DataFrame."""
        predictor = ZonePredictor()
        
        # Train model
        training_data = ZonePredictor.generate_synthetic_training_data(n_samples=100)
        predictor.train(training_data)
        
        # Create zones DataFrame
        zones_df = pd.DataFrame([
            self.sample_zone,
            {**self.sample_zone, 'price_mean': 81000.0, 'quality_score': 45.0}
        ])
        
        # Predict
        zones_ml = predictor.predict_zones(
            zones_df,
            current_price=80500.0,
            current_time=self.now
        )
        
        self.assertEqual(len(zones_ml), 2)
        self.assertIn('hold_probability', zones_ml.columns)
        self.assertIn('break_probability', zones_ml.columns)
        self.assertIn('prediction_confidence', zones_ml.columns)
        self.assertIn('ml_prediction', zones_ml.columns)
    
    def test_zone_metrics(self):
        """Test SQN-style zone performance metrics."""
        predictor = ZonePredictor()
        
        # Create lifecycle data with known outcomes
        lifecycle_data = ZonePredictor.generate_synthetic_training_data(n_samples=50)
        
        metrics = predictor.compute_zone_metrics(lifecycle_data)
        
        self.assertEqual(metrics['n_zones'], 50)
        self.assertIn('win_rate', metrics)
        self.assertIn('avg_hold_time_hours', metrics)
        self.assertIn('expectancy', metrics)
        self.assertIn('sqn_score', metrics)
        self.assertIn('interpretation', metrics)
        
        # Check bounds
        self.assertGreaterEqual(metrics['win_rate'], 0)
        self.assertLessEqual(metrics['win_rate'], 100)
        self.assertGreaterEqual(metrics['avg_hold_time_hours'], 0)
    
    def test_model_persistence(self):
        """Test saving and loading trained model."""
        predictor1 = ZonePredictor()
        
        # Train
        training_data = ZonePredictor.generate_synthetic_training_data(n_samples=100)
        predictor1.train(training_data)
        
        # Make prediction
        pred1 = predictor1.predict(
            zone=self.sample_zone,
            current_price=80100.0,
            current_time=self.now
        )
        
        # Save model
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as f:
            model_path = f.name
        
        predictor1.save(model_path)
        
        # Load model in new instance
        predictor2 = ZonePredictor()
        predictor2.load(model_path)
        
        self.assertTrue(predictor2.is_trained)
        
        # Make same prediction
        pred2 = predictor2.predict(
            zone=self.sample_zone,
            current_price=80100.0,
            current_time=self.now
        )
        
        # Predictions should match
        self.assertEqual(pred1['prediction'], pred2['prediction'])
        self.assertAlmostEqual(pred1['hold_probability'], pred2['hold_probability'], places=1)
        
        # Cleanup
        os.unlink(model_path)


class TestLiquidatorMLIntegration(unittest.TestCase):
    """Test ML integration with Liquidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.now = pd.Timestamp.now(tz='UTC')
        
        # Create sample trades
        self.sample_trades = []
        for i in range(40):
            self.sample_trades.append({
                'time': self.now - pd.Timedelta(minutes=i),
                'px': 80000 + np.random.randn() * 20,
                'sz': 1.0,
                'side': 'A' if i % 3 == 0 else 'B'
            })
    
    def test_enable_ml_predictions(self):
        """Test enabling ML predictions."""
        L = Liquidator('BTC', cutoff_hours=None)
        
        self.assertFalse(L.enable_ml)
        self.assertIsNone(L._ml_predictor)
        
        L.enable_ml_predictions()
        
        self.assertTrue(L.enable_ml)
        self.assertIsNotNone(L._ml_predictor)
        self.assertIsInstance(L._ml_predictor, ZonePredictor)
    
    def test_train_ml_predictor_synthetic(self):
        """Test training ML predictor with synthetic data."""
        L = Liquidator('BTC', cutoff_hours=None)
        L.enable_ml_predictions()
        
        metrics = L.train_ml_predictor(use_synthetic=True, n_synthetic=150)
        
        self.assertEqual(metrics['data_source'], 'synthetic')
        self.assertTrue(L._ml_predictor.is_trained)
        self.assertGreater(metrics['train_accuracy'], 0.5)
        self.assertIn('warning', metrics)  # No real data yet
    
    def test_compute_zones_with_prediction(self):
        """Test computing zones with ML predictions."""
        L = Liquidator('BTC', cutoff_hours=None)
        L.enable_ml_predictions()
        L.train_ml_predictor(use_synthetic=True, n_synthetic=100)
        
        # Ingest trades
        L.ingest_trades(self.sample_trades)
        
        # Compute zones with predictions
        zones_ml = L.compute_zones_with_prediction(current_price=80000.0)
        
        if not zones_ml.empty:
            self.assertIn('hold_probability', zones_ml.columns)
            self.assertIn('break_probability', zones_ml.columns)
            self.assertIn('prediction_confidence', zones_ml.columns)
            self.assertIn('ml_prediction', zones_ml.columns)
    
    def test_zone_touch_tracking(self):
        """Test zone touch counting."""
        L = Liquidator('BTC', cutoff_hours=None)
        L.ingest_trades(self.sample_trades)
        
        # Compute zones
        zones = L.compute_zones()
        
        if not zones.empty:
            zone_price = zones.iloc[0]['price_mean']
            
            # Simulate price touching zone
            L.update_zone_touches(zone_price)
            L.update_zone_touches(zone_price + 10)  # Near zone
            L.update_zone_touches(zone_price - 5)   # Near zone
            
            zone_id = f"{zone_price:.0f}"
            self.assertGreater(L._zone_touch_counts.get(zone_id, 0), 0)
    
    def test_record_zone_outcome(self):
        """Test recording zone outcomes for ML training."""
        L = Liquidator('BTC', cutoff_hours=None)
        L.ingest_trades(self.sample_trades)
        
        # Compute zones
        zones = L.compute_zones()
        
        if not zones.empty:
            zone_price = zones.iloc[0]['price_mean']
            
            # Record outcome
            L.record_zone_outcome(
                zone_price=zone_price,
                outcome='HOLD',
                current_price=zone_price - 50,
                current_time=self.now
            )
            
            self.assertEqual(len(L._zone_lifecycle), 1)
            
            # Check record structure
            record = L._zone_lifecycle[0]
            self.assertEqual(record['outcome'], 1)  # HOLD = 1
            self.assertIn('zone', record)
            self.assertIn('touch_count', record)
    
    def test_ml_metrics(self):
        """Test getting ML performance metrics."""
        L = Liquidator('BTC', cutoff_hours=None)
        L.enable_ml_predictions()
        L.train_ml_predictor(use_synthetic=True)
        
        # Add some synthetic outcomes
        for i in range(20):
            L._zone_lifecycle.append({
                'zone': {'price_mean': 80000 + i * 100, 'total_usd': 100000, 'count': 10,
                        'quality_score': 70, 'alignment_score': 50,
                        'last_ts': self.now},
                'current_price': 80000,
                'current_time': self.now,
                'outcome': 1 if i % 3 != 0 else 0,
                'touch_count': i % 4,
                'funding_rate': 0.0001,
                'zone_broken_at': self.now + pd.Timedelta(hours=i) if i % 3 == 0 else None
            })
        
        metrics = L.get_ml_metrics()
        
        self.assertEqual(metrics['n_zones'], 20)
        self.assertIn('win_rate', metrics)
        self.assertIn('sqn_score', metrics)
    
    def test_backward_compatibility(self):
        """Test that ML is optional and doesn't break existing functionality."""
        # Should work without enabling ML
        L = Liquidator('BTC', cutoff_hours=None)
        L.ingest_trades(self.sample_trades)
        zones = L.compute_zones()
        
        self.assertFalse(L.enable_ml)
        self.assertNotIn('hold_probability', zones.columns)
        
        # Standard functionality should still work
        if not zones.empty:
            self.assertIn('price_mean', zones.columns)
            self.assertIn('quality_score', zones.columns)
            self.assertIn('strength', zones.columns)


class TestMLEdgeCases(unittest.TestCase):
    """Test ML predictor edge cases and error handling."""
    
    def test_training_insufficient_data(self):
        """Test training with insufficient data."""
        predictor = ZonePredictor()
        
        # Try training with too few samples
        insufficient_data = ZonePredictor.generate_synthetic_training_data(n_samples=10)
        
        with self.assertRaises(ValueError):
            predictor.train(insufficient_data)
    
    def test_prediction_before_training(self):
        """Test prediction without training."""
        predictor = ZonePredictor()
        
        with self.assertRaises(ValueError):
            predictor.predict(
                zone={'price_mean': 80000, 'total_usd': 100000, 'count': 10,
                      'quality_score': 70, 'alignment_score': 50,
                      'last_ts': pd.Timestamp.now(tz='UTC')},
                current_price=80000,
                current_time=pd.Timestamp.now(tz='UTC')
            )
    
    def test_empty_zones_dataframe(self):
        """Test prediction on empty zones DataFrame."""
        predictor = ZonePredictor()
        training_data = ZonePredictor.generate_synthetic_training_data(n_samples=100)
        predictor.train(training_data)
        
        empty_df = pd.DataFrame()
        result = predictor.predict_zones(
            empty_df,
            current_price=80000,
            current_time=pd.Timestamp.now(tz='UTC')
        )
        
        self.assertTrue(result.empty)
    
    def test_missing_zone_features(self):
        """Test feature extraction with missing fields."""
        predictor = ZonePredictor()
        
        # Zone with minimal fields
        minimal_zone = {
            'price_mean': 80000.0,
            'total_usd': 100000.0,
            'count': 10
        }
        
        # Should handle missing fields gracefully
        features = predictor.extract_features(
            zone=minimal_zone,
            current_price=80000,
            current_time=pd.Timestamp.now(tz='UTC')
        )
        
        self.assertEqual(len(features), 10)
        self.assertTrue(np.all(np.isfinite(features)))


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("ML PREDICTOR TESTS")
    print("=" * 70 + "\n")
    
    # Run tests
    unittest.main(verbosity=2)
