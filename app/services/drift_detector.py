import pandas as pd

from app.api.schemas import ChurnPredictionRequest
from app.core.config import get_settings
from app.core.metrics import DRIFT_SCORE


class DriftDetector:
    baseline_stats = {
        "customer_age": {"mean": 42.0, "std": 12.0},
        "tenure_months": {"mean": 30.0, "std": 18.0},
        "monthly_spend": {"mean": 72.0, "std": 28.0},
        "num_support_tickets": {"mean": 2.0, "std": 2.0},
        "payment_delay_days": {"mean": 5.0, "std": 6.0},
        "usage_frequency": {"mean": 18.0, "std": 9.0},
    }

    def __init__(self, threshold: float | None = None) -> None:
        self.threshold = threshold if threshold is not None else get_settings().drift_threshold

    def check(self, records: list[ChurnPredictionRequest]) -> tuple[bool, float, list[str]]:
        frame = pd.DataFrame([record.model_dump(exclude={"model_version"}) for record in records])
        feature_scores: dict[str, float] = {}

        for feature, stats in self.baseline_stats.items():
            current_mean = float(frame[feature].mean())
            normalized_delta = abs(current_mean - stats["mean"]) / max(stats["std"], 1.0)
            feature_scores[feature] = normalized_delta

        drift_score = round(sum(feature_scores.values()) / len(feature_scores), 4)
        features_with_drift = [
            feature for feature, score in feature_scores.items() if score >= self.threshold
        ]
        DRIFT_SCORE.set(drift_score)
        return drift_score >= self.threshold, drift_score, features_with_drift

