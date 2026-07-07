from app.api.schemas import RiskLevel


FEATURE_COLUMNS = [
    "customer_age",
    "tenure_months",
    "monthly_spend",
    "num_support_tickets",
    "contract_type",
    "payment_delay_days",
    "usage_frequency",
]


def risk_level_from_probability(probability: float) -> RiskLevel:
    if probability >= 0.7:
        return "high"
    if probability >= 0.35:
        return "medium"
    return "low"

