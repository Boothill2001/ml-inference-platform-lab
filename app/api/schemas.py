from typing import Literal

from pydantic import BaseModel, Field, field_validator


ContractType = Literal["monthly", "annual", "two_year"]
RiskLevel = Literal["low", "medium", "high"]


class ChurnPredictionRequest(BaseModel):
    customer_age: int = Field(..., ge=18, le=100)
    tenure_months: int = Field(..., ge=0, le=600)
    monthly_spend: float = Field(..., ge=0, le=10000)
    num_support_tickets: int = Field(..., ge=0, le=1000)
    contract_type: ContractType
    payment_delay_days: int = Field(..., ge=0, le=365)
    usage_frequency: int = Field(..., ge=0, le=10000)
    model_version: str | None = Field(default=None, pattern=r"^v[0-9]+$")

    @field_validator("monthly_spend")
    @classmethod
    def round_monthly_spend(cls, value: float) -> float:
        return round(value, 2)


class ChurnPredictionResponse(BaseModel):
    request_id: str
    prediction: int
    churn_probability: float
    risk_level: RiskLevel
    model_name: str
    model_version: str
    latency_ms: float


class CanaryPredictionResponse(ChurnPredictionResponse):
    routed_model_version: str


class HealthResponse(BaseModel):
    status: str
    service: str


class ReadyResponse(BaseModel):
    ready: bool
    loaded_models: list[str]


class DriftCheckRequest(BaseModel):
    records: list[ChurnPredictionRequest] = Field(..., min_length=1)


class DriftCheckResponse(BaseModel):
    drift_detected: bool
    drift_score: float
    features_with_drift: list[str]

