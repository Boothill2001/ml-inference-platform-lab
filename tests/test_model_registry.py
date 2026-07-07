from app.services.model_registry import ModelRegistry


def test_model_registry_loads_v1_and_v2() -> None:
    registry = ModelRegistry()
    loaded = registry.list_loaded_models()

    assert "churn_model:v1" in loaded
    assert "churn_model:v2" in loaded


def test_model_registry_gets_production_model() -> None:
    registry = ModelRegistry()
    metadata, model = registry.get_production_model()

    assert metadata.version == "v1"
    assert hasattr(model, "predict_proba")

