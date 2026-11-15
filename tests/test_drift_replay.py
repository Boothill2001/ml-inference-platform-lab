import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
fixture = json.loads(
    (Path(__file__).resolve().parents[1] / "app/static/drift-replay.json").read_text(encoding="utf-8")
)


def records_with(**changes):
    return [record | {name: record[name] + delta for name, delta in changes.items()}
            for record in fixture["normal"]]


def check(records):
    response = client.post("/drift/check", json={"records": records})
    assert response.status_code == 200
    return response.json()


def test_drift_replay_updates_decision_and_latest_metrics():
    normal = fixture["normal"]
    phases = [
        (normal, 0.0, 0.0, False),
        (records_with(payment_delay_days=fixture["shift_days"]), 0.25, 1.5, True),
        (normal, 0.0, 0.0, False),
    ]
    for records, aggregate, feature, detected in phases:
        payload = check(records)
        assert payload["sample_size"] == 60
        assert payload["drift_score"] == aggregate
        assert payload["threshold"] == 0.3
        assert payload["aggregate_drift_detected"] is False
        assert payload["drift_detected"] is detected
        assert payload["features_with_drift"] == (["payment_delay_days"] if detected else [])
        scores = payload["feature_scores"]
        assert len(scores) == 6
        assert scores.pop("payment_delay_days") == feature
        assert all(score == 0.0 for score in scores.values())
        metrics = client.get("/metrics").text.splitlines()
        assert f'drift_feature_score{{feature="payment_delay_days"}} {feature}' in metrics
        assert f"drift_score {aggregate}" in metrics
        assert "drift_threshold 0.3" in metrics


def test_feature_includes_exact_threshold():
    payload = check(records_with(monthly_spend=8.4))
    assert payload["feature_scores"]["monthly_spend"] == pytest.approx(payload["threshold"])
    assert payload["features_with_drift"] == ["monthly_spend"]
    assert payload["drift_detected"] is True
    assert payload["aggregate_drift_detected"] is False


def test_aggregate_alert_retains_previous_rule():
    payload = check(records_with(payment_delay_days=12))
    assert payload["drift_score"] > payload["threshold"]
    assert payload["aggregate_drift_detected"] is True
    assert payload["drift_detected"] is True


def test_drift_rejects_empty_batch():
    assert client.post("/drift/check", json={"records": []}).status_code == 422
