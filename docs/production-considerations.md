# Production Considerations

This lab runs locally with Docker Compose, but the same architecture maps to cloud-native production patterns.

## Serving

Deploy the API on Kubernetes behind an ingress, API gateway, or service mesh. Use horizontal pod autoscaling based on CPU, request rate, queue depth, and p95 latency. Configure readiness checks to fail if model artifacts cannot be loaded.

## Model Artifacts

Store artifacts in S3, GCS, Azure Blob Storage, or an MLflow registry. Artifacts should be immutable, content-addressed, signed where required, and promoted through staging gates before production.

## Observability

Ship logs to ELK, OpenSearch, Datadog, or cloud logging. Export metrics to Prometheus and visualize them in Grafana. Alert on latency, error rate, low traffic anomalies, canary degradation, and drift.

## Batch

Production batch scoring can run through Airflow, Dagster, Kubeflow, Vertex AI, or scheduled Kubernetes Jobs. Jobs should be idempotent, partition-aware, and auditable.

## Canary And Rollback

Real canary rollout should happen at the service mesh, API gateway, or deployment controller layer. Compare model versions on business metrics, prediction distributions, latency, and error rate before expanding traffic.

## Drift

Production drift detection needs a stable baseline window and a current observation window. It should track feature drift, prediction drift, label drift when labels arrive, and business KPI impact.

## Security And Governance

Add authentication, RBAC, rate limiting, input size limits, and dependency scanning. Do not log raw PII. Audit logs should include request ID, model version, schema version or hash, caller identity, and prediction metadata.

