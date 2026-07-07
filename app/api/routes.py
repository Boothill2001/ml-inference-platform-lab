from fastapi import APIRouter, HTTPException, Response
from loguru import logger
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.schemas import (
    CanaryPredictionResponse,
    ChurnPredictionRequest,
    ChurnPredictionResponse,
    DriftCheckRequest,
    DriftCheckResponse,
    HealthResponse,
    ReadyResponse,
)
from app.core.config import get_settings
from app.core.metrics import INFERENCE_ERROR_TOTAL
from app.services.canary_router import CanaryRouter
from app.services.drift_detector import DriftDetector
from app.services.inference_service import InferenceService
from app.services.model_registry import ModelRegistry, ModelRegistryError

router = APIRouter()
settings = get_settings()
registry = ModelRegistry(settings.model_registry_path)
inference_service = InferenceService(registry)
canary_router = CanaryRouter(settings.canary_percentage)
drift_detector = DriftDetector(settings.drift_threshold)


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.app_name)


@router.get("/ready", response_model=ReadyResponse)
def ready() -> ReadyResponse:
    loaded_models = registry.list_loaded_models()
    return ReadyResponse(ready=bool(loaded_models), loaded_models=loaded_models)


@router.post("/predict", response_model=ChurnPredictionResponse)
def predict(request: ChurnPredictionRequest) -> ChurnPredictionResponse:
    try:
        return inference_service.predict(request, endpoint="predict")
    except ModelRegistryError as exc:
        INFERENCE_ERROR_TOTAL.labels(endpoint="predict", error_type="model_registry").inc()
        logger.exception("prediction_failed")
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        INFERENCE_ERROR_TOTAL.labels(endpoint="predict", error_type=type(exc).__name__).inc()
        logger.exception("prediction_failed")
        raise HTTPException(status_code=500, detail="Prediction failed") from exc


@router.post("/predict/canary", response_model=CanaryPredictionResponse)
def predict_canary(request: ChurnPredictionRequest) -> CanaryPredictionResponse:
    routed_version = canary_router.route()
    try:
        response = inference_service.predict(
            request, endpoint="predict_canary", forced_version=routed_version
        )
        return CanaryPredictionResponse(
            **response.model_dump(),
            routed_model_version=routed_version,
        )
    except ModelRegistryError as exc:
        INFERENCE_ERROR_TOTAL.labels(endpoint="predict_canary", error_type="model_registry").inc()
        logger.exception("canary_prediction_failed")
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        INFERENCE_ERROR_TOTAL.labels(
            endpoint="predict_canary", error_type=type(exc).__name__
        ).inc()
        logger.exception("canary_prediction_failed")
        raise HTTPException(status_code=500, detail="Canary prediction failed") from exc


@router.post("/drift/check", response_model=DriftCheckResponse)
def check_drift(request: DriftCheckRequest) -> DriftCheckResponse:
    drift_detected, drift_score, features = drift_detector.check(request.records)
    return DriftCheckResponse(
        drift_detected=drift_detected,
        drift_score=drift_score,
        features_with_drift=features,
    )


@router.get("/metrics")
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

