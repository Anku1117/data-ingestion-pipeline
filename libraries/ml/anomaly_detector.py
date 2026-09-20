from __future__ import annotations

from typing import Any

from libraries.logging.logging import get_logger
from libraries.ml.feature_extractor import FeatureExtractor
from libraries.ml.models import AnomalyResult, FeatureVector

logger = get_logger(__name__)


class AnomalyDetector:
    """Baseline anomaly detector using statistical methods.

    Uses simple statistical thresholds as a baseline before
    integrating with scikit-learn Isolation Forest.
    """

    def __init__(self, threshold: float = 2.0) -> None:
        self._threshold = threshold
        self._feature_extractor = FeatureExtractor()
        self._baseline_mean: FeatureVector | None = None
        self._baseline_std: FeatureVector | None = None
        self._model_version = "1.0"
        self._sample_count = 0
        logger.info("AnomalyDetector initialized threshold=%.1f", threshold)

    def update_baseline(self, features: FeatureVector) -> None:
        """Update running baseline statistics."""
        if self._baseline_mean is None:
            self._baseline_mean = features
            self._baseline_std = FeatureVector()
            self._sample_count = 1
            return

        self._sample_count += 1
        alpha = 1.0 / self._sample_count

        mean = self._baseline_mean
        for field_name in features.model_fields:
            old_val = getattr(mean, field_name)
            new_val = getattr(features, field_name)
            setattr(mean, field_name, old_val + alpha * (new_val - old_val))

    def detect(self, events: list[dict[str, Any]]) -> AnomalyResult:
        features = self._feature_extractor.extract(events)
        self.update_baseline(features)

        if self._baseline_mean is None or self._sample_count < 10:
            return AnomalyResult(
                anomaly_score=0.0,
                is_anomaly=False,
                features=features.model_dump(),
                explanation="Insufficient baseline data",
                model_version=self._model_version,
            )

        score = self._compute_z_score(features)
        is_anomaly = score > self._threshold

        explanation = self._generate_explanation(features, score, is_anomaly)

        return AnomalyResult(
            anomaly_score=min(score / (self._threshold * 2), 1.0),
            is_anomaly=is_anomaly,
            features=features.model_dump(),
            explanation=explanation,
            model_version=self._model_version,
        )

    def _compute_z_score(self, features: FeatureVector) -> float:
        if self._baseline_mean is None:
            return 0.0

        total_z = 0.0
        feature_count = 0

        for field_name in features.model_fields:
            mean_val = getattr(self._baseline_mean, field_name)
            current_val = getattr(features, field_name)

            if (
                isinstance(mean_val, int | float)
                and isinstance(current_val, int | float)
                and mean_val > 0
            ):
                z = abs(current_val - mean_val) / max(mean_val, 0.001)
                total_z += z
                feature_count += 1

        return total_z / max(feature_count, 1)

    def _generate_explanation(
        self, features: FeatureVector, score: float, is_anomaly: bool
    ) -> str:
        if not is_anomaly:
            return "Normal behavior"

        anomalies = []
        if self._baseline_mean:
            for field_name in features.model_fields:
                current = getattr(features, field_name)
                mean = getattr(self._baseline_mean, field_name)
                if (
                    isinstance(current, int | float)
                    and isinstance(mean, int | float)
                    and mean > 0
                    and current > mean * 1.5
                ):
                    anomalies.append(
                        f"{field_name}: {current:.1f} (baseline: {mean:.1f})"
                    )

        if anomalies:
            return "Anomalous: " + "; ".join(anomalies[:5])
        return f"Anomaly detected (score: {score:.2f})"
