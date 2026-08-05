"""Tests for Error Classifier"""
import pytest
import tempfile
import os
from src.ml.training.error_classifier import ErrorClassifier

class TestErrorClassifier:
    @pytest.fixture
    def classifier(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, "test_model.pkl")
            yield ErrorClassifier(model_path=model_path)

    def test_predict_untrained(self, classifier):
        result = classifier.predict("docker build failed")
        assert result["primary_category"] == "unknown"

    def test_train_and_predict(self, classifier):
        training_data = [
            {"text": "docker build failed: no such image", "labels": ["docker"]},
            {"text": "pod crashed with OOMKilled", "labels": ["kubernetes"]},
            {"text": "terraform state lock error", "labels": ["terraform"]},
            {"text": "yaml syntax error: mapping values", "labels": ["yaml"]},
            {"text": "docker daemon not running", "labels": ["docker", "permission"]},
            {"text": "kubernetes service not found", "labels": ["kubernetes", "network"]},
            {"text": "terraform provider error aws", "labels": ["terraform", "network"]},
            {"text": "docker pull access denied", "labels": ["docker", "permission"]},
            {"text": "pod imagepullbackoff", "labels": ["kubernetes", "docker"]},
            {"text": "terraform invalid resource", "labels": ["terraform", "syntax"]},
        ]
        metrics = classifier.train(training_data, validation_split=0.2)
        assert "training_samples" in metrics
        prediction = classifier.predict("docker container exited with error")
        assert prediction["primary_category"] in ["docker", "kubernetes", "terraform", "yaml"]
        assert 0 <= prediction["confidence"] <= 1

    def test_predict_batch(self, classifier):
        texts = ["docker error", "kubernetes pod failed", "terraform apply error"]
        results = classifier.predict_batch(texts)
        assert len(results) == 3
        for result in results:
            assert "primary_category" in result