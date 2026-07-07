# Architecture

This repository models a compact production inference platform.

The FastAPI application owns real-time request handling, Pydantic schema validation, model routing, prediction formatting, and Prometheus metric exposure. The model registry isolates artifact loading and version lookup from API and batch workflows. The batch scoring job reuses the same feature contract and registry code so online and offline scoring remain aligned.

## Request Flow

1. A client sends customer features to `/predict`.
2. Pydantic validates shape, ranges, and categorical values.
3. The inference service selects the production model or the requested version.
4. The model returns churn probability and class prediction.
5. The API attaches risk level, request ID, model metadata, and latency.
6. Metrics and structured logs are emitted for observability.

## Canary Flow

`/predict/canary` uses `CanaryRouter` to select `v1` or `v2` based on `CANARY_PERCENTAGE`. This keeps rollout policy separate from inference mechanics.

## Batch Flow

The batch job reads CSV, validates rows, loads the production model from the same registry, writes prediction columns, and verifies output row count equals input row count.

