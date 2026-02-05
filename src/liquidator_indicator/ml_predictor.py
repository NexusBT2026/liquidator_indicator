"""Machine Learning predictor for liquidation zone behavior.

Predicts whether a zone will hold (price bounces) or break (price penetrates).
Uses historical zone lifecycle data to train a simple logistic regression model.

Compatible with trading system quality metrics (SQN, Sharpe, win rate).
"""
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import pickle
import warnings

warnings.filterwarnings('ignore', category=UserWarning)


class ZonePredictor:
    """ML-based predictor for zone hold/break probability.
    
    Features engineered from zone characteristics:
    - Volume concentration (log-scaled total_usd)
    - Recency (time since zone formation)
    - Cluster density (number of liquidations)
    - Price tightness (spread percentage)
    - Quality score (composite 0-100)
    - Multi-timeframe alignment (if available)
    - Market regime (volatility state)
    - Zone age at prediction time
    - Distance to current price
    
    Target: Binary classification
    - 1 = Zone holds (price bounces/reverses at zone)
    - 0 = Zone breaks (price penetrates through zone)
    """
    
    def __init__(self):
        self.model = LogisticRegression(
            C=1.0,
            solver='lbfgs',
            max_iter=1000,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = [
            'volume_log',           # Log-scaled total_usd
            'recency_hours',        # Hours since zone formation
            'density',              # Number of liquidations in zone
            'tightness',            # 1 / (spread_pct + 0.01)
            'quality_score',        # 0-100 quality rating
            'alignment_score',      # Multi-TF alignment (0-100)
            'zone_age_hours',       # Hours since zone first detected
            'price_distance_pct',   # % distance from current price
            'touch_count',          # Number of times price touched zone
            'funding_extreme'       # 1 if extreme funding, 0 otherwise
        ]
        
    def extract_features(self, zone: Dict, current_price: float, 
                        current_time: pd.Timestamp, touch_count: int = 0,
                        funding_rate: float = 0.0) -> np.ndarray:
        """Extract ML features from a zone dictionary.
        
        Args:
            zone: Zone dict with price_mean, total_usd, count, quality_score, etc.
            current_price: Current market price
            current_time: Current timestamp
            touch_count: Number of times price has touched this zone
            funding_rate: Current funding rate (optional)
            
        Returns:
            Feature vector (1D numpy array)
        """
        # Volume (log-scaled to handle wide range)
        volume_log = np.log1p(zone.get('total_usd', 1))
        
        # Recency (hours since zone formation)
        zone_time = zone.get('last_ts', current_time)
        recency_hours = (current_time - zone_time).total_seconds() / 3600.0
        
        # Density (number of liquidations)
        density = zone.get('count', 1)
        
        # Tightness (inverse of spread percentage, bounded)
        price_mean = zone.get('price_mean', current_price)
        price_min = zone.get('price_min', price_mean)
        price_max = zone.get('price_max', price_mean)
        spread_pct = (price_max - price_min) / price_mean if price_mean > 0 else 0.01
        tightness = 1.0 / (spread_pct + 0.01)  # Higher = tighter zone
        
        # Quality score (0-100)
        quality_score = zone.get('quality_score', 50.0)
        
        # Multi-timeframe alignment (0-100, default 0 if not available)
        alignment_score = zone.get('alignment_score', 0.0)
        
        # Zone age (hours since first detected - use recency as proxy)
        zone_age_hours = recency_hours
        
        # Price distance (% from current price)
        price_distance_pct = abs(price_mean - current_price) / current_price * 100.0
        
        # Touch count (tracked externally)
        touch_count = min(touch_count, 10)  # Cap at 10
        
        # Funding extreme (binary flag)
        funding_extreme = 1.0 if abs(funding_rate) > 0.001 else 0.0
        
        features = np.array([
            volume_log,
            recency_hours,
            density,
            tightness,
            quality_score,
            alignment_score,
            zone_age_hours,
            price_distance_pct,
            touch_count,
            funding_extreme
        ])
        
        return features
    
    def train(self, zone_lifecycle_data: List[Dict]):
        """Train the model on historical zone lifecycle data.
        
        Args:
            zone_lifecycle_data: List of dicts with:
                - zone: Zone dict with features
                - current_price: Price at prediction time
                - current_time: Timestamp of prediction
                - outcome: 1 = held, 0 = broke
                - touch_count: Number of touches before outcome
                - funding_rate: Funding rate at prediction time
        """
        if len(zone_lifecycle_data) < 20:
            raise ValueError(f"Need at least 20 samples to train, got {len(zone_lifecycle_data)}")
        
        # Extract features and labels
        X_list = []
        y_list = []
        
        for record in zone_lifecycle_data:
            features = self.extract_features(
                zone=record['zone'],
                current_price=record['current_price'],
                current_time=record['current_time'],
                touch_count=record.get('touch_count', 0),
                funding_rate=record.get('funding_rate', 0.0)
            )
            X_list.append(features)
            y_list.append(record['outcome'])
        
        X = np.array(X_list)
        y = np.array(y_list)
        
        # Standardize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train logistic regression
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        # Calculate training accuracy
        train_acc = self.model.score(X_scaled, y)
        
        return {
            'train_accuracy': train_acc,
            'n_samples': len(y),
            'hold_ratio': y.sum() / len(y)
        }
    
    def predict(self, zone: Dict, current_price: float, 
                current_time: pd.Timestamp, touch_count: int = 0,
                funding_rate: float = 0.0) -> Dict:
        """Predict zone hold/break probability.
        
        Args:
            zone: Zone dict with features
            current_price: Current market price
            current_time: Current timestamp
            touch_count: Number of times price has touched zone
            funding_rate: Current funding rate
            
        Returns:
            Dict with:
                - hold_probability: 0-100 probability zone holds
                - break_probability: 0-100 probability zone breaks
                - prediction_confidence: 0-100 confidence in prediction
                - prediction: 'HOLD' or 'BREAK'
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet. Call train() first.")
        
        # Extract features
        features = self.extract_features(
            zone=zone,
            current_price=current_price,
            current_time=current_time,
            touch_count=touch_count,
            funding_rate=funding_rate
        )
        
        # Scale features
        X_scaled = self.scaler.transform(features.reshape(1, -1))
        
        # Get probabilities [P(break), P(hold)]
        proba = self.model.predict_proba(X_scaled)[0]
        break_prob = proba[0] * 100.0
        hold_prob = proba[1] * 100.0
        
        # Confidence = distance from 50/50 (max confidence when 100/0 or 0/100)
        confidence = abs(hold_prob - 50.0) * 2.0  # Scale 0-50 to 0-100
        
        # Prediction
        prediction = 'HOLD' if hold_prob > break_prob else 'BREAK'
        
        return {
            'hold_probability': round(hold_prob, 1),
            'break_probability': round(break_prob, 1),
            'prediction_confidence': round(confidence, 1),
            'prediction': prediction
        }
    
    def predict_zones(self, zones_df: pd.DataFrame, current_price: float,
                     current_time: pd.Timestamp, touch_counts: Optional[Dict] = None,
                     funding_rate: float = 0.0) -> pd.DataFrame:
        """Add ML predictions to zones DataFrame.
        
        Args:
            zones_df: DataFrame of zones
            current_price: Current market price
            current_time: Current timestamp
            touch_counts: Dict mapping zone_id -> touch_count
            funding_rate: Current funding rate
            
        Returns:
            zones_df with added columns:
                - hold_probability
                - break_probability
                - prediction_confidence
                - ml_prediction
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet. Call train() first.")
        
        if zones_df.empty:
            return zones_df
        
        touch_counts = touch_counts or {}
        
        zones = zones_df.copy()
        predictions = []
        
        for idx, zone in zones.iterrows():
            zone_id = f"{zone['price_mean']:.0f}"
            touch_count = touch_counts.get(zone_id, 0)
            
            pred = self.predict(
                zone=zone.to_dict(),
                current_price=current_price,
                current_time=current_time,
                touch_count=touch_count,
                funding_rate=funding_rate
            )
            predictions.append(pred)
        
        # Add prediction columns
        zones['hold_probability'] = [p['hold_probability'] for p in predictions]
        zones['break_probability'] = [p['break_probability'] for p in predictions]
        zones['prediction_confidence'] = [p['prediction_confidence'] for p in predictions]
        zones['ml_prediction'] = [p['prediction'] for p in predictions]
        
        return zones
    
    def save(self, path: str):
        """Save trained model to file."""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names
            }, f)
    
    def load(self, path: str):
        """Load trained model from file."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.scaler = data['scaler']
            self.feature_names = data['feature_names']
            self.is_trained = True
    
    @staticmethod
    def generate_synthetic_training_data(n_samples: int = 200) -> List[Dict]:
        """Generate synthetic zone lifecycle data for initial model training.
        
        Creates realistic zone behavior patterns:
        - Strong zones (high quality) tend to hold more often
        - Recent zones more likely to hold
        - Zones with high touch counts more likely to break eventually
        - Tight zones (small spread) more likely to hold
        
        Args:
            n_samples: Number of synthetic samples to generate
            
        Returns:
            List of zone lifecycle records for training
        """
        np.random.seed(42)
        data = []
        
        current_time = pd.Timestamp.now(tz='UTC')
        
        for i in range(n_samples):
            # Generate zone features with realistic correlations
            quality_score = np.random.beta(2, 2) * 100  # Skew toward medium quality
            total_usd = np.random.lognormal(13, 1.5)  # Log-normal volume distribution
            count = int(np.random.gamma(3, 2))  # Gamma distribution for counts
            spread_pct = np.random.gamma(2, 0.002)  # Tight spreads more common
            
            price_mean = 80000 + np.random.randn() * 2000
            price_min = price_mean - (spread_pct * price_mean / 2)
            price_max = price_mean + (spread_pct * price_mean / 2)
            
            zone_age_hours = np.random.exponential(12)  # Recent zones more common
            last_ts = current_time - pd.Timedelta(hours=zone_age_hours)
            
            alignment_score = np.random.beta(1.5, 2) * 100  # Lower alignment more common
            touch_count = int(np.random.poisson(1.5))  # Most zones touched 0-3 times
            
            current_price = price_mean + np.random.randn() * 500
            funding_rate = np.random.normal(0, 0.0005)  # Small funding rates common
            
            zone = {
                'price_mean': price_mean,
                'price_min': price_min,
                'price_max': price_max,
                'total_usd': total_usd,
                'count': count,
                'quality_score': quality_score,
                'alignment_score': alignment_score,
                'last_ts': last_ts
            }
            
            # Outcome logic: Strong zones with high quality, low touch count, recent -> hold
            # Weak zones with low quality, high touch count, old -> break
            hold_score = (
                quality_score / 100.0 * 0.4 +
                (100 - zone_age_hours) / 100.0 * 0.2 +
                alignment_score / 100.0 * 0.2 +
                (5 - touch_count) / 5.0 * 0.1 +
                (1.0 / (spread_pct * 100 + 1)) * 0.1
            )
            
            # Add noise and convert to binary outcome
            hold_score += np.random.normal(0, 0.15)
            outcome = 1 if hold_score > 0.5 else 0
            
            data.append({
                'zone': zone,
                'current_price': current_price,
                'current_time': current_time,
                'outcome': outcome,
                'touch_count': touch_count,
                'funding_rate': funding_rate
            })
        
        return data
    
    def compute_zone_metrics(self, zone_lifecycle_data: List[Dict]) -> Dict:
        """Compute trading system quality metrics from zone lifecycle history.
        
        Metrics compatible with SQN (System Quality Number) and Sharpe ratio:
        - Win rate: % of zones that held
        - Average hold time: Mean time zones stayed valid
        - Expectancy: (avg_win * win_rate) - (avg_loss * loss_rate)
        - SQN-like score: (avg_win / stdev_win) * sqrt(n_trades)
        
        Args:
            zone_lifecycle_data: Historical zone records with outcomes
            
        Returns:
            Dict of performance metrics
        """
        if len(zone_lifecycle_data) < 10:
            return {
                'n_zones': len(zone_lifecycle_data),
                'error': 'Insufficient data for metrics (need 10+ zones)'
            }
        
        outcomes = [r['outcome'] for r in zone_lifecycle_data]
        wins = sum(outcomes)
        losses = len(outcomes) - wins
        
        win_rate = wins / len(outcomes) if len(outcomes) > 0 else 0.0
        
        # Calculate hold times (hours)
        hold_times = []
        for record in zone_lifecycle_data:
            if 'zone_broken_at' in record and record['zone_broken_at'] is not None:
                hold_time = (record['zone_broken_at'] - record['current_time']).total_seconds() / 3600.0
                hold_times.append(hold_time)
        
        avg_hold_time = np.mean(hold_times) if hold_times else 0.0
        
        # Expectancy (simplified: assume win = +1, loss = -1 for zone validity)
        expectancy = win_rate * 1.0 - (1 - win_rate) * 1.0
        
        # SQN-like: quality number for zones
        # Higher = more consistent zone behavior
        if len(outcomes) > 1:
            outcome_array = np.array(outcomes)
            sqn = (outcome_array.mean() / (outcome_array.std() + 1e-6)) * np.sqrt(len(outcomes))
        else:
            sqn = 0.0
        
        return {
            'n_zones': len(outcomes),
            'win_rate': round(win_rate * 100, 1),
            'avg_hold_time_hours': round(avg_hold_time, 2),
            'expectancy': round(expectancy, 3),
            'sqn_score': round(sqn, 2),
            'interpretation': 'Excellent (>2.5)' if sqn > 2.5 else 'Good (1.5-2.5)' if sqn > 1.5 else 'Fair (0.5-1.5)' if sqn > 0.5 else 'Poor (<0.5)'
        }
