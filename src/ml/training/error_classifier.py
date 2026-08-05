"""
Error Classification Model using scikit-learn
"""
import os
import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.multiclass import OneVsRestClassifier
import joblib
from datetime import datetime
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ErrorClassifier:
    ERROR_CATEGORIES = [
        "docker", "kubernetes", "terraform", "yaml",
        "network", "permission", "resource", "syntax", "test_failure", "unknown"
    ]
    
    def __init__(self, model_path: str = "./data/models/error_classifier.pkl"):
        self.model_path = model_path
        self.pipeline: Optional[Pipeline] = None
        self.is_trained = False
        self._load_model()
    
    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.pipeline = joblib.load(self.model_path)
                self.is_trained = True
                logger.info("Loaded pre-trained error classifier")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                self.pipeline = self._create_pipeline()
        else:
            self.pipeline = self._create_pipeline()
    
    def _create_pipeline(self) -> Pipeline:
        return Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=10000, ngram_range=(1, 3),
                min_df=2, max_df=0.95, stop_words='english'
            )),
            ('classifier', OneVsRestClassifier(
                RandomForestClassifier(
                    n_estimators=200, max_depth=20,
                    min_samples_split=5, random_state=42,
                    n_jobs=-1, class_weight='balanced'
                )
            ))
        ])
    
    def prepare_training_data(self, logs: List[Dict]) -> Tuple[List[str], np.ndarray]:
        texts = []
        labels_matrix = []
        for log in logs:
            texts.append(log['text'])
            label_vector = [1 if cat in log.get('labels', []) else 0 for cat in self.ERROR_CATEGORIES]
            labels_matrix.append(label_vector)
        return texts, np.array(labels_matrix)
    
    def train(self, logs: List[Dict], validation_split: float = 0.2) -> Dict:
        logger.info(f"Training error classifier on {len(logs)} samples")
        texts, y = self.prepare_training_data(logs)
        X_train, X_val, y_train, y_val = train_test_split(
            texts, y, test_size=validation_split, random_state=42
        )
        self.pipeline.fit(X_train, y_train)
        self.is_trained = True
        y_pred = self.pipeline.predict(X_val)
        metrics = {}
        for i, category in enumerate(self.ERROR_CATEGORIES):
            tp = np.sum((y_val[:, i] == 1) & (y_pred[:, i] == 1))
            fp = np.sum((y_val[:, i] == 0) & (y_pred[:, i] == 1))
            fn = np.sum((y_val[:, i] == 1) & (y_pred[:, i] == 0))
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            metrics[category] = {
                'precision': round(precision, 3), 'recall': round(recall, 3),
                'f1': round(f1, 3), 'support': int(np.sum(y_val[:, i]))
            }
        try:
            cv_scores = cross_val_score(self.pipeline, texts, np.argmax(y, axis=1), cv=3)
            metrics['cv_accuracy_mean'] = round(float(np.mean(cv_scores)), 3)
            metrics['cv_accuracy_std'] = round(float(np.std(cv_scores)), 3)
        except Exception as e:
            logger.warning(f"Cross-validation failed: {e}")
            metrics['cv_accuracy_mean'] = None
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.pipeline, self.model_path)
        logger.info(f"Model saved to {self.model_path}")
        metrics['training_samples'] = len(logs)
        metrics['validation_samples'] = len(X_val)
        metrics['trained_at'] = datetime.utcnow().isoformat()
        return metrics
    
    def predict(self, log_text: str) -> Dict:
        if not self.is_trained:
            logger.warning("Model not trained yet")
            return {'predicted_categories': [], 'confidence_scores': {}, 'primary_category': 'unknown', 'confidence': 0.0}
        proba = self.pipeline.predict_proba([log_text])
        predictions = []
        confidence_scores = {}
        for i, category in enumerate(self.ERROR_CATEGORIES):
            try:
                # OneVsRest returns list of (n_samples, 2) arrays
                cat_proba = proba[i]
                if hasattr(cat_proba, 'shape') and len(cat_proba.shape) >= 2 and cat_proba.shape[1] > 1:
                    prob = float(cat_proba[0][1])
                elif hasattr(cat_proba, '__len__') and len(cat_proba) > 0:
                    prob = float(cat_proba[0]) if len(cat_proba) == 1 else float(cat_proba[1])
                else:
                    prob = 0.0
            except Exception:
                prob = 0.0
            confidence_scores[category] = round(prob, 3)
            if prob > 0.5:
                predictions.append(category)
        if not predictions:
            primary = max(confidence_scores, key=confidence_scores.get)
            predictions.append(primary)
        else:
            primary = max(predictions, key=lambda x: confidence_scores[x])
        return {
            'predicted_categories': predictions,
            'confidence_scores': confidence_scores,
            'primary_category': primary,
            'confidence': confidence_scores[primary]
        }
    
    def predict_batch(self, log_texts: List[str]) -> List[Dict]:
        return [self.predict(text) for text in log_texts]
    
    def get_feature_importance(self, top_n: int = 20) -> List[Dict]:
        if not self.is_trained:
            return []
        vectorizer = self.pipeline.named_steps['tfidf']
        classifier = self.pipeline.named_steps['classifier']
        feature_names = vectorizer.get_feature_names_out()
        importances = []
        for i, category in enumerate(self.ERROR_CATEGORIES):
            if hasattr(classifier.estimators_[i], 'feature_importances_'):
                top_indices = np.argsort(classifier.estimators_[i].feature_importances_)[-top_n:]
                category_features = [
                    {'feature': feature_names[idx], 'importance': round(float(classifier.estimators_[i].feature_importances_[idx]), 4)}
                    for idx in reversed(top_indices)
                ]
                importances.append({'category': category, 'top_features': category_features})
        return importances