# Demo Guide

This guide is written for a short recruiter, customer, or stakeholder demo.

## Quick Start On Windows

Double-click:

```text
demo_start.bat
```

The launcher will:

1. Check Python 3.11+.
2. Create `.venv` if needed.
3. Install dependencies from `requirements.txt`.
4. Train demo model artifacts if they are missing.
5. Start the FastAPI server and open the dashboard.

Dashboard:

```text
http://127.0.0.1:8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

## Recommended Demo Flow

1. Open the dashboard and point out the platform status cards.
2. Click `At-risk monthly user`, then `Score customer`.
3. Explain the returned risk level, probability, request ID, model version, and latency.
4. Switch to `Canary`, score again, and show how traffic can route to v1 or v2.
5. Click the canary refresh button to sample multiple routes.
6. Click the drift check button and explain the drift score plus flagged features.
7. Open `/docs` to show typed API contracts.
8. Open `/metrics` to show Prometheus-compatible telemetry.

## Talking Points

- The model is not hidden in a notebook; it is served behind a typed API.
- Online inference and batch scoring share the same model registry.
- Versioning separates production and canary artifacts.
- Canary routing simulates progressive rollout.
- Metrics expose request volume, latency, errors, model version traffic, batch records, and drift score.
- Drift detection demonstrates the monitoring layer needed after deployment.
- Tests and CI/CD make the platform maintainable.

## DeepSeek API Key

Do not paste or commit a real API key into this repository.

If an AI explanation layer is added later, store the key locally in `.env`:

```text
DEEPSEEK_API_KEY=your_local_key_here
```

`.env` is ignored by Git. Keep `.env.example` as a safe placeholder only.

