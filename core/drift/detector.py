"""
Drift detection system for LLM outputs.

Monitors LLM performance over time and detects degradation/drift.
Adapted from production drift detection systems.
"""

import json
import logging
import os
import sqlite3
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import statistics

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)

try:
    from scipy.stats import ks_2samp, chi2_contingency
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("scipy not available. Install with: pip install scipy")


class DriftDetector:
    """Detects drift in LLM output distributions."""
    
    def __init__(self, baseline_window_size: int = 100, 
                 detection_window_size: int = 50,
                 drift_threshold: float = 0.05,
                 min_samples: int = 20):
        """
        Initialize drift detector.
        
        Args:
            baseline_window_size: Number of samples for baseline distribution
            detection_window_size: Number of recent samples to compare
            drift_threshold: P-value threshold for drift detection (lower = more sensitive)
            min_samples: Minimum samples needed before detection
        """
        self.baseline_window_size = baseline_window_size
        self.detection_window_size = detection_window_size
        self.drift_threshold = drift_threshold
        self.min_samples = min_samples
        
        # Store baseline and recent outputs
        self.baseline_outputs = deque(maxlen=baseline_window_size)
        self.recent_outputs = deque(maxlen=detection_window_size)
        
        # Baseline statistics
        self.baseline_stats = None
        self.baseline_established = False
        
        # Drift history
        self.drift_history = []
        self.last_drift_check = None
        
    def add_output(self, output: Dict) -> Optional[Dict]:
        """
        Add an LLM output and check for drift.
        
        Args:
            output: LLM output dictionary with:
                - text: Output text
                - tokens_used: Number of tokens
                - processing_time_ms: Processing time
                - confidence: Optional confidence score
                
        Returns:
            Drift detection result dict or None if no drift
        """
        # Extract features
        features = self._extract_features(output)
        
        # Add to recent outputs
        self.recent_outputs.append(features)
        
        # Establish baseline if needed
        if not self.baseline_established:
            self.baseline_outputs.append(features)
            
            if len(self.baseline_outputs) >= self.min_samples:
                self._establish_baseline()
                logger.info("Baseline distribution established")
            return None
        
        # Check for drift periodically
        if len(self.recent_outputs) >= self.min_samples:
            drift_result = self._detect_drift()
            
            if drift_result and drift_result.get('drift_detected'):
                self.drift_history.append(drift_result)
                logger.warning(f"Drift detected: {drift_result['drift_score']:.3f}")
                return drift_result
        
        return None
    
    def _extract_features(self, output: Dict) -> Dict:
        """Extract features from LLM output for drift detection."""
        text = output.get('text', output.get('llm_response', ''))
        tokens = output.get('tokens_used', 0)
        processing_time = output.get('processing_time_ms', 0)
        
        features = {
            'text_length': len(text) if text else 0,
            'word_count': len(text.split()) if text else 0,
            'tokens_used': tokens,
            'processing_time_ms': processing_time,
            'avg_chars_per_word': len(text) / max(len(text.split()), 1) if text else 0,
            'has_numbers': bool(text and any(c.isdigit() for c in text)),
            'has_currency': bool(text and any(c in text for c in ['$', '€', '£', '¥'])),
            'has_percentages': '%' in text if text else False,
        }
        
        # Add confidence if available
        if 'confidence' in output:
            features['confidence'] = output['confidence']
        
        return features
    
    def _establish_baseline(self):
        """Establish baseline distribution statistics."""
        if len(self.baseline_outputs) < self.min_samples:
            return
        
        baseline_features = list(self.baseline_outputs)
        
        # Calculate statistics for each feature
        self.baseline_stats = {}
        
        for feature_name in baseline_features[0].keys():
            values = [f[feature_name] for f in baseline_features]
            
            self.baseline_stats[feature_name] = {
                'mean': np.mean(values),
                'std': np.std(values) if len(values) > 1 else 0.0,
                'median': np.median(values),
                'min': np.min(values),
                'max': np.max(values),
                'values': values  # Store for statistical tests
            }
        
        self.baseline_established = True
        logger.info(f"Baseline established with {len(baseline_features)} samples")
    
    def _detect_drift(self) -> Optional[Dict]:
        """
        Detect drift in recent outputs compared to baseline.
        
        Returns:
            Drift detection result dict
        """
        if not self.baseline_established or len(self.recent_outputs) < self.min_samples:
            return None
        
        recent_features = list(self.recent_outputs)
        drift_scores = {}
        drift_detected = False
        
        # Check each feature for drift
        for feature_name in self.baseline_stats.keys():
            baseline_values = self.baseline_stats[feature_name]['values']
            recent_values = [f[feature_name] for f in recent_features]
            
            # Skip if not enough variation
            if np.std(baseline_values) == 0 and np.std(recent_values) == 0:
                continue
            
            # Statistical test for drift
            try:
                if SCIPY_AVAILABLE and len(baseline_values) > 10 and len(recent_values) > 10:
                    # Kolmogorov-Smirnov test (non-parametric)
                    statistic, p_value = ks_2samp(baseline_values, recent_values)
                    
                    drift_scores[feature_name] = {
                        'p_value': float(p_value),
                        'statistic': float(statistic),
                        'drifted': p_value < self.drift_threshold
                    }
                    
                    if p_value < self.drift_threshold:
                        drift_detected = True
                else:
                    # Simple mean/std comparison
                    baseline_mean = self.baseline_stats[feature_name]['mean']
                    baseline_std = self.baseline_stats[feature_name]['std']
                    recent_mean = np.mean(recent_values)
                    
                    # Z-score based detection
                    if baseline_std > 0:
                        z_score = abs((recent_mean - baseline_mean) / baseline_std)
                        drift_scores[feature_name] = {
                            'z_score': float(z_score),
                            'baseline_mean': float(baseline_mean),
                            'recent_mean': float(recent_mean),
                            'drifted': z_score > 2.0  # 2 standard deviations
                        }
                        
                        if z_score > 2.0:
                            drift_detected = True
                    else:
                        # Simple threshold comparison
                        change_pct = abs((recent_mean - baseline_mean) / max(abs(baseline_mean), 1)) * 100
                        drift_scores[feature_name] = {
                            'change_pct': float(change_pct),
                            'baseline_mean': float(baseline_mean),
                            'recent_mean': float(recent_mean),
                            'drifted': change_pct > 20  # 20% change
                        }
                        
                        if change_pct > 20:
                            drift_detected = True
                            
            except Exception as e:
                logger.warning(f"Error detecting drift for {feature_name}: {e}")
                continue
        
        if not drift_detected:
            return None
        
        # Calculate overall drift score
        drifted_features = [f for f, s in drift_scores.items() if s.get('drifted', False)]
        drift_score = len(drifted_features) / max(len(drift_scores), 1)
        
        # Calculate feature-level statistics
        recent_stats = {}
        for feature_name in self.baseline_stats.keys():
            recent_values = [f[feature_name] for f in recent_features]
            recent_stats[feature_name] = {
                'mean': float(np.mean(recent_values)),
                'std': float(np.std(recent_values)) if len(recent_values) > 1 else 0.0,
                'median': float(np.median(recent_values))
            }
        
        result = {
            'drift_detected': True,
            'drift_score': drift_score,
            'drifted_features': drifted_features,
            'drift_scores': drift_scores,
            'baseline_stats': {
                k: {kk: vv for kk, vv in v.items() if kk != 'values'}
                for k, v in self.baseline_stats.items()
            },
            'recent_stats': recent_stats,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'baseline_samples': len(self.baseline_outputs),
            'recent_samples': len(recent_features)
        }
        
        return result
    
    def reset_baseline(self):
        """Reset baseline with current recent outputs."""
        if len(self.recent_outputs) >= self.min_samples:
            self.baseline_outputs.clear()
            self.baseline_outputs.extend(self.recent_outputs)
            self.recent_outputs.clear()
            self._establish_baseline()
            logger.info("Baseline reset with recent outputs")
    
    def get_statistics(self) -> Dict:
        """Get drift detection statistics."""
        return {
            'baseline_established': self.baseline_established,
            'baseline_samples': len(self.baseline_outputs),
            'recent_samples': len(self.recent_outputs),
            'drift_alerts': len(self.drift_history),
            'last_drift_check': self.last_drift_check,
            'baseline_stats': {
                k: {kk: vv for kk, vv in v.items() if kk != 'values'}
                for k, v in (self.baseline_stats or {}).items()
            }
        }
    
    def track_output_quality(self, output: Dict, quality_score: float):
        """
        Track output quality metrics for drift detection.
        
        Args:
            output: LLM output dictionary
            quality_score: Quality score (0.0 to 1.0)
        """
        if not hasattr(self, 'quality_scores'):
            self.quality_scores = deque(maxlen=self.baseline_window_size)
        
        self.quality_scores.append(quality_score)
        
        # Add quality to features for drift detection
        if 'quality_score' not in output:
            output['quality_score'] = quality_score
    
    def track_user_feedback(self, output: Dict, feedback_score: float):
        """
        Track user feedback for drift detection.
        
        Args:
            output: LLM output dictionary
            feedback_score: User feedback score (0.0 to 1.0, or -1 for negative)
        """
        if not hasattr(self, 'feedback_scores'):
            self.feedback_scores = deque(maxlen=self.baseline_window_size)
        
        self.feedback_scores.append(feedback_score)
        
        # Add feedback to features
        if 'feedback_score' not in output:
            output['feedback_score'] = feedback_score
    
    def test_false_positive_rate(self, synthetic_samples: List[Dict]) -> Dict:
        """
        Test false positive rate using synthetic drift samples.
        
        Args:
            synthetic_samples: List of synthetic output samples
            
        Returns:
            Dictionary with false positive rate metrics
        """
        if not self.baseline_established:
            return {"error": "Baseline not established"}
        
        false_positives = 0
        total_tests = len(synthetic_samples)
        
        for sample in synthetic_samples:
            drift_result = self._detect_drift_for_sample(sample)
            if drift_result and drift_result.get('drift_detected'):
                # Check if this is a false positive (synthetic sample should not drift)
                false_positives += 1
        
        false_positive_rate = false_positives / total_tests if total_tests > 0 else 0.0
        
        return {
            'false_positive_rate': false_positive_rate,
            'false_positives': false_positives,
            'total_tests': total_tests,
            'threshold': self.drift_threshold
        }
    
    def _detect_drift_for_sample(self, sample: Dict) -> Optional[Dict]:
        """Internal method to detect drift for a single sample."""
        features = self._extract_features(sample)
        self.recent_outputs.append(features)
        
        if len(self.recent_outputs) >= self.min_samples:
            return self._detect_drift()
        return None


class DriftMonitor:
    """Monitors LLM outputs and manages drift detection."""
    
    def __init__(self, detector: DriftDetector, db_path: Optional[str] = None,
                 alert_callback: Optional[callable] = None):
        """
        Initialize drift monitor.
        
        Args:
            detector: DriftDetector instance
            db_path: Path to SQLite database for storing drift alerts
            alert_callback: Optional callback function for alerts
        """
        self.detector = detector
        self.db_path = db_path or os.getenv('DRIFT_DB_PATH', 'drift_alerts.db')
        self.alert_callback = alert_callback
        
        self.alerts = []
        self.check_interval = 10  # Check every N outputs
        self.output_count = 0
        
        # Initialize database if provided
        if self.db_path:
            self._init_database()
    
    def _init_database(self):
        """Initialize drift alerts database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drift_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                drift_score REAL NOT NULL,
                drifted_features TEXT NOT NULL,
                baseline_samples INTEGER,
                recent_samples INTEGER,
                details TEXT,
                acknowledged BOOLEAN DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON drift_alerts(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_acknowledged ON drift_alerts(acknowledged)')
        
        conn.commit()
        conn.close()
        logger.info(f"Initialized drift alerts database at {self.db_path}")
    
    def add_output(self, output: Dict) -> Optional[Dict]:
        """
        Add output and check for drift.
        
        Args:
            output: LLM output dictionary
            
        Returns:
            Drift alert dict if drift detected, None otherwise
        """
        self.output_count += 1
        
        # Check for drift periodically
        drift_result = self.detector.add_output(output)
        
        if drift_result and drift_result.get('drift_detected'):
            # Store alert
            def convert_to_json_serializable(obj):
                """Convert numpy types to JSON-serializable Python types."""
                if isinstance(obj, (np.integer, np.int64, np.int32)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float64, np.float32)):
                    return float(obj)
                elif isinstance(obj, (np.bool_, np.bool8)):
                    return bool(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {k: convert_to_json_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [convert_to_json_serializable(item) for item in obj]
                return obj
            
            alert = {
                'timestamp': drift_result['timestamp'],
                'drift_score': float(drift_result['drift_score']),
                'drifted_features': drift_result['drifted_features'],
                'baseline_samples': int(drift_result['baseline_samples']),
                'recent_samples': int(drift_result['recent_samples']),
                'details': json.dumps(convert_to_json_serializable(drift_result))
            }
            
            self.alerts.append(alert)
            
            # Store in database
            if self.db_path:
                self._store_alert(alert)
            
            # Call alert callback if provided
            if self.alert_callback:
                try:
                    self.alert_callback(drift_result)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")
            
            return drift_result
        
        return None
    
    def _store_alert(self, alert: Dict):
        """Store drift alert in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Convert details to JSON-serializable format
            details_str = alert['details']
            
            cursor.execute('''
                INSERT INTO drift_alerts (
                    timestamp, drift_score, drifted_features,
                    baseline_samples, recent_samples, details
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                alert['timestamp'],
                alert['drift_score'],
                ','.join(alert['drifted_features']),
                alert['baseline_samples'],
                alert['recent_samples'],
                details_str
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error storing drift alert: {e}")
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """Get recent drift alerts."""
        if self.db_path:
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM drift_alerts
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                alerts = [dict(row) for row in rows]
                
                conn.close()
                return alerts
            except Exception as e:
                logger.error(f"Error retrieving alerts: {e}")
        
        return self.alerts[-limit:] if self.alerts else []
    
    def acknowledge_alert(self, alert_id: int):
        """Mark an alert as acknowledged."""
        if self.db_path:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE drift_alerts
                    SET acknowledged = 1
                    WHERE id = ?
                ''', (alert_id,))
                
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Error acknowledging alert: {e}")
