import time
import uuid
from typing import Any

import pandas as pd
from loguru import logger

from app.api.schemas import ChurnPredictionRequest, ChurnPredictionResponse
from app.core.metrics import (
    INFERENCE_LATENCY_SECONDS,
    INFERENCE_REQUEST_TOTAL,
    MODEL_VERSION_REQUEST_TOTAL,
    PREDICTION_DISTRIBUTION_TOTAL,
)
from app.services.model_registry import ModelRegistry
from app.utils.validation import FEATURE_COLUMNS, risk_level_from_probability


class InferenceService:
    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry

    def predict(
        self,
        request: ChurnPredictionRequest,
        *,
        endpoint: str = "predict",
        forced_version: str | None = None,
    ) -> ChurnPredictionResponse:
        started = time.perf_counter()
        request_id = str(uuid.uuid4())
        model_version = forced_version or request.model_version

        if model_version:
            metadata, model = self.registry.get_model_by_version(model_version)
        else:
            metadata, model = self.registry.get_production_model()

        frame = self._to_frame(request)
        probability = float(model.predict_proba(frame)[0][1])
        prediction = int(probability >= 0.5)
        risk_level = risk_level_from_probability(probability)
        latency_seconds = time.perf_counter() - started

        INFERENCE_REQUEST_TOTAL.labels(endpoint=endpoint, model_version=metadata.version).inc()
        INFERENCE_LATENCY_SECONDS.labels(endpoint=endpoint, model_version=metadata.version).observe(
            latency_seconds
        )
        PREDICTION_DISTRIBUTION_TOTAL.labels(
            prediction=str(prediction), risk_level=risk_level
        ).inc()
        MODEL_VERSION_REQUEST_TOTAL.labels(
            model_name=metadata.name, model_version=metadata.version
        ).inc()

        logger.info(
            "prediction_completed",
            request_id=request_id,
            model_name=metadata.name,
            model_version=metadata.version,
            prediction=prediction,
            churn_probability=round(probability, 4),
            latency_ms=round(latency_seconds * 1000, 2),
        )

        return ChurnPredictionResponse(
            request_id=request_id,
            prediction=prediction,
            churn_probability=round(probability, 4),
            risk_level=risk_level,
            model_name=metadata.name,
            model_version=metadata.version,
            latency_ms=round(latency_seconds * 1000, 2),
        )

    @staticmethod
    def _to_frame(request: ChurnPredictionRequest) -> pd.DataFrame:
        values: dict[str, Any] = request.model_dump(exclude={"model_version"})
        return pd.DataFrame([values], columns=FEATURE_COLUMNS)

