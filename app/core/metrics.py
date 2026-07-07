from prometheus_client import Counter, Gauge, Histogram

INFERENCE_REQUEST_TOTAL = Counter(
    "inference_request_total",
    "Total inference requests.",
    ["endpoint", "model_version"],
)

INFERENCE_ERROR_TOTAL = Counter(
    "inference_error_total",
    "Total inference errors.",
    ["endpoint", "error_type"],
)

INFERENCE_LATENCY_SECONDS = Histogram(
    "inference_latency_seconds",
    "Inference request latency in seconds.",
    ["endpoint", "model_version"],
)

PREDICTION_DISTRIBUTION_TOTAL = Counter(
    "prediction_distribution_total",
    "Prediction label distribution.",
    ["prediction", "risk_level"],
)

MODEL_VERSION_REQUEST_TOTAL = Counter(
    "model_version_request_total",
    "Requests routed by model version.",
    ["model_name", "model_version"],
)

BATCH_RECORDS_PROCESSED_TOTAL = Counter(
    "batch_records_processed_total",
    "Batch records processed.",
    ["model_version"],
)

DRIFT_SCORE = Gauge(
    "drift_score",
    "Latest computed drift score.",
)

