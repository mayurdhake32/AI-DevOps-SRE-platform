"""
Deployment Failure Prediction Model
"""
import os
import numpy as np
from typing import Dict, List, Optional, Tuple
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score
import joblib
from datetime import datetime
from src.utils.logger import get_logger

logger = get_logger(__name__)

class FailurePredictor:
    FEATURE_COLUMNS = [
        'lines_added', 'lines_deleted', 'files_changed', 'commits_count',
        'test_files_changed', 'config_files_changed', 'dependencies_changed',
        'author_failure_rate', 'hour_of_day', 'day_of_week',
        'avg_file_complexity', 'review_comments_count', 'approval_count',
        'last_deployment_failed', 'time_since_last_deployment_hours'
    ]
    
    def __init__(self, model_path: str = "./data/models/failure_predictor.pkl"):
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self._load_model()
    
    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                data = joblib.load(self.model_path)
                self.model = data['model']
                self.scaler = data['scaler']
                self.is_trained = True
                logger.info("Loaded pre-trained failure predictor")
            except Exception as e:
                logger.error(f"Failed to load: {e}")
                self.model = self._create_model()
        else:
            self.model = self._create_model()
    
    def _create_model(self):
        return GradientBoostingClassifier(
            n_estimators=200, learning_rate=0.1,
            max_depth=5, min_samples_split=10, random_state=42
        )
    
    def extract_features(self, deployment_info: Dict) -> np.ndarray:
        features = []
        for col in self.FEATURE_COLUMNS:
            value = deployment_info.get(col, 0)
            if isinstance(value, bool):
                value = int(value)
            features.append(float(value))
        return np.array(features).reshape(1, -1)
    
    def train(self, deployments: List[Dict], validation_split: float = 0.2) -> Dict:
        logger.info(f"Training failure predictor on {len(deployments)} deployments")
        X = []
        y = []
        for dep in deployments:
            features = []
            for col in self.FEATURE_COLUMNS:
                value = dep.get(col, 0)
                if isinstance(value, bool):
                    value = int(value)
                features.append(float(value))
            X.append(features)
            y.append(1 if dep.get('failed', False) else 0)
        X = np.array(X)
        y = np.array(y)
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42, stratify=y
        )
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        y_pred_proba = self.model.predict_proba(X_val_scaled)[:, 1]
        y_pred = self.model.predict(X_val_scaled)
        auc = roc_auc_score(y_val, y_pred_proba)
        avg_precision = average_precision_score(y_val, y_pred_proba)
        importance = dict(zip(self.FEATURE_COLUMNS, self.model.feature_importances_))
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump({'model': self.model, 'scaler': self.scaler}, self.model_path)
        return {
            'auc_roc': round(auc, 3), 'average_precision': round(avg_precision, 3),
            'training_samples': len(deployments), 'positive_samples': int(sum(y)),
            'feature_importance': {k: round(v, 4) for k, v in importance.items()},
            'trained_at': datetime.utcnow().isoformat()
        }
    
    def predict(self, deployment_info: Dict) -> Dict:
        if not self.is_trained:
            return {
                'failure_probability': 0.5, 'risk_level': 'unknown',
                'should_block': False, 'confidence': 0.0
            }
        features = self.extract_features(deployment_info)
        features_scaled = self.scaler.transform(features)
        proba = self.model.predict_proba(features_scaled)[0][1]
        if proba < 0.3:
            risk_level = 'low'
        elif proba < 0.6:
            risk_level = 'medium'
        elif proba < 0.8:
            risk_level = 'high'
        else:
            risk_level = 'critical'
        return {
            'failure_probability': round(float(proba), 3),
            'risk_level': risk_level,
            'should_block': proba > 0.8,
            'confidence': round(abs(proba - 0.5) * 2, 3),
            'top_risk_factors': self._get_risk_factors(deployment_info)
        }
    
    def _get_risk_factors(self, deployment_info: Dict) -> List[Dict]:
        if not self.is_trained:
            return []
        features = self.extract_features(deployment_info)[0]
        importance = self.model.feature_importances_
        risk_factors = []
        for i, col in enumerate(self.FEATURE_COLUMNS):
            if features[i] > 0 and importance[i] > 0.05:
                risk_factors.append({
                    'factor': col, 'value': float(features[i]),
                    'importance': round(float(importance[i]), 4)
                })
        return sorted(risk_factors, key=lambda x: x['importance'], reverse=True)[:5]