from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

FEATURE_COLUMNS = [
    "customer_age",
    "tenure_months",
    "monthly_spend",
    "num_support_tickets",
    "contract_type",
    "payment_delay_days",
    "usage_frequency",
]

NUMERIC_COLUMNS = [
    "customer_age",
    "tenure_months",
    "monthly_spend",
    "num_support_tickets",
    "payment_delay_days",
    "usage_frequency",
]

CATEGORICAL_COLUMNS = ["contract_type"]


def generate_synthetic_churn_data(rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame(
        {
            "customer_age": rng.integers(18, 80, rows),
            "tenure_months": rng.integers(0, 96, rows),
            "monthly_spend": rng.gamma(shape=3.0, scale=25.0, size=rows).round(2),
            "num_support_tickets": rng.poisson(2.0, rows),
            "contract_type": rng.choice(["monthly", "annual", "two_year"], rows, p=[0.55, 0.3, 0.15]),
            "payment_delay_days": rng.poisson(5.0, rows),
            "usage_frequency": rng.poisson(18.0, rows),
        }
    )

    contract_risk = frame["contract_type"].map({"monthly": 0.9, "annual": -0.25, "two_year": -0.8})
    logits = (
        -1.15
        + 0.035 * frame["payment_delay_days"]
        + 0.23 * frame["num_support_tickets"]
        - 0.025 * frame["tenure_months"]
        - 0.035 * frame["usage_frequency"]
        + 0.006 * frame["monthly_spend"]
        + contract_risk
        + rng.normal(0, 0.55, rows)
    )
    probability = 1 / (1 + np.exp(-logits))
    frame["churn"] = rng.binomial(1, probability)
    return frame


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), NUMERIC_COLUMNS),
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_COLUMNS),
        ]
    )


def train_and_save() -> None:
    output_dir = Path("models/artifacts")
    output_dir.mkdir(parents=True, exist_ok=True)

    data = generate_synthetic_churn_data()
    x = data[FEATURE_COLUMNS]
    y = data["churn"]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=y
    )

    models = {
        "v1": Pipeline(
            steps=[
                ("preprocessor", build_preprocessor()),
                ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
            ]
        ),
        "v2": Pipeline(
            steps=[
                ("preprocessor", build_preprocessor()),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=140,
                        max_depth=8,
                        min_samples_leaf=8,
                        random_state=42,
                        class_weight="balanced_subsample",
                    ),
                ),
            ]
        ),
    }

    for version, model in models.items():
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        probabilities = model.predict_proba(x_test)[:, 1]
        metrics = {
            "accuracy": accuracy_score(y_test, predictions),
            "f1": f1_score(y_test, predictions),
            "roc_auc": roc_auc_score(y_test, probabilities),
        }
        artifact_path = output_dir / f"churn_model_{version}.joblib"
        joblib.dump(model, artifact_path)
        print(
            f"Saved {artifact_path} | "
            f"accuracy={metrics['accuracy']:.3f} "
            f"f1={metrics['f1']:.3f} "
            f"roc_auc={metrics['roc_auc']:.3f}"
        )


if __name__ == "__main__":
    train_and_save()

