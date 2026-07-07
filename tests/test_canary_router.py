from app.services.canary_router import CanaryRouter


def test_canary_router_returns_supported_versions() -> None:
    router = CanaryRouter(canary_percentage=10, random_seed=7)
    versions = {router.route() for _ in range(100)}

    assert versions <= {"v1", "v2"}
    assert "v1" in versions
    assert "v2" in versions


def test_canary_router_honors_zero_percent() -> None:
    router = CanaryRouter(canary_percentage=0)

    assert {router.route() for _ in range(20)} == {"v1"}

