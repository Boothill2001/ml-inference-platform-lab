import pytest
from pydantic import ValidationError

from app.api.schemas import ChurnPredictionRequest


def test_prediction_request_validates_contract_type() -> None:
    with pytest.raises(ValidationError):
        ChurnPredictionRequest(
            customer_age=32,
            tenure_months=14,
            monthly_spend=79.5,
            num_support_tickets=3,
            contract_type="weekly",
            payment_delay_days=8,
            usage_frequency=12,
        )


def test_prediction_request_accepts_valid_payload() -> None:
    request = ChurnPredictionRequest(
        customer_age=32,
        tenure_months=14,
        monthly_spend=79.5,
        num_support_tickets=3,
        contract_type="monthly",
        payment_delay_days=8,
        usage_frequency=12,
    )
    assert request.contract_type == "monthly"

