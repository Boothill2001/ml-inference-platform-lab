from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


VALID_PAYLOAD = {
    "customer_age": 32,
    "tenure_months": 14,
    "monthly_spend": 79.5,
    "num_support_tickets": 3,
    "contract_type": "monthly",
    "payment_delay_days": 8,
    "usage_frequency": 12,
}


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_serves_frontend() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Customer Churn Inference Platform" in response.text


def test_ready_returns_loaded_models() -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is True
    assert "churn_model:v1" in body["loaded_models"]
    assert "churn_model:v2" in body["loaded_models"]


def test_predict_returns_expected_schema() -> None:
    response = client.post("/predict", json=VALID_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["prediction"] in [0, 1]
    assert 0 <= body["churn_probability"] <= 1
    assert body["risk_level"] in ["low", "medium", "high"]
    assert body["model_name"] == "churn_model"
    assert body["model_version"] == "v1"
    assert body["request_id"]


def test_predict_rejects_invalid_input() -> None:
    payload = VALID_PAYLOAD | {"customer_age": 12}
    response = client.post("/predict", json=payload)

    assert response.status_code == 422


def test_canary_predict_returns_routed_model_version() -> None:
    response = client.post("/predict/canary", json=VALID_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["routed_model_version"] in ["v1", "v2"]
    assert body["model_version"] == body["routed_model_version"]


def test_drift_check_returns_score() -> None:
    response = client.post("/drift/check", json={"records": [VALID_PAYLOAD]})

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["drift_detected"], bool)
    assert body["drift_score"] >= 0
    assert isinstance(body["features_with_drift"], list)
