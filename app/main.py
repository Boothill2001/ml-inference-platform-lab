from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()
settings = get_settings()

app = FastAPI(
    title="ML Inference Platform Lab",
    version=settings.app_version,
    description="Production-style MLOps inference platform demo for customer churn prediction.",
)
app.include_router(router)

