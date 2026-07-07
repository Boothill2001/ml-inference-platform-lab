import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
from loguru import logger


@dataclass(frozen=True)
class ModelMetadata:
    name: str
    version: str
    stage: str
    artifact_path: str
    framework: str
    created_at: str
    description: str


class ModelRegistryError(RuntimeError):
    pass


class ModelRegistry:
    def __init__(self, registry_path: str = "models/model_registry.json") -> None:
        self.registry_path = Path(registry_path)
        self.metadata: dict[str, ModelMetadata] = {}
        self.models: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        if not self.registry_path.exists():
            raise ModelRegistryError(f"Registry file not found: {self.registry_path}")

        payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
        for item in payload.get("models", []):
            metadata = ModelMetadata(**item)
            key = self._key(metadata.name, metadata.version)
            artifact_path = Path(metadata.artifact_path)
            if not artifact_path.exists():
                raise ModelRegistryError(
                    f"Artifact missing for {key}: {metadata.artifact_path}. "
                    "Run `python models/train_model.py` to generate artifacts."
                )
            self.metadata[key] = metadata
            self.models[key] = joblib.load(artifact_path)
            logger.info("loaded_model", model_name=metadata.name, model_version=metadata.version)

    def get_production_model(self, model_name: str = "churn_model") -> tuple[ModelMetadata, Any]:
        for metadata in self.metadata.values():
            if metadata.name == model_name and metadata.stage == "production":
                return metadata, self.models[self._key(metadata.name, metadata.version)]
        raise ModelRegistryError(f"No production model found for {model_name}")

    def get_model_by_version(
        self, version: str, model_name: str = "churn_model"
    ) -> tuple[ModelMetadata, Any]:
        key = self._key(model_name, version)
        if key not in self.models:
            raise ModelRegistryError(f"Model not found: {key}")
        return self.metadata[key], self.models[key]

    def list_loaded_models(self) -> list[str]:
        return sorted(self.models.keys())

    @staticmethod
    def _key(name: str, version: str) -> str:
        return f"{name}:{version}"

