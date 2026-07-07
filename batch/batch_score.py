from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pandas as pd
from loguru import logger
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api.schemas import ChurnPredictionRequest  # noqa: E402
from app.core.metrics import BATCH_RECORDS_PROCESSED_TOTAL  # noqa: E402
from app.services.model_registry import ModelRegistry  # noqa: E402
from app.utils.validation import FEATURE_COLUMNS, risk_level_from_probability  # noqa: E402


def retry(operation: Callable[[], pd.DataFrame], attempts: int = 3, delay_seconds: float = 0.5) -> pd.DataFrame:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as exc:
            last_error = exc
            logger.warning("batch_attempt_failed", attempt=attempt, error=str(exc))
            if attempt < attempts:
                time.sleep(delay_seconds)
    raise RuntimeError("Batch scoring failed after retries") from last_error


def validate_input(frame: pd.DataFrame) -> list[ChurnPredictionRequest]:
    missing = set(FEATURE_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Input CSV missing required columns: {sorted(missing)}")

    records: list[ChurnPredictionRequest] = []
    for index, row in frame.iterrows():
        try:
            records.append(ChurnPredictionRequest(**row[FEATURE_COLUMNS].to_dict()))
        except ValidationError as exc:
            raise ValueError(f"Invalid row at index {index}: {exc}") from exc
    return records


def score_batch(input_path: str, output_path: str) -> pd.DataFrame:
    input_file = Path(input_path)
    output_file = Path(output_path)
    frame = pd.read_csv(input_file)
    records = validate_input(frame)

    registry = ModelRegistry()
    metadata, model = registry.get_production_model()
    scored_at = datetime.now(timezone.utc).isoformat()
    features = pd.DataFrame([record.model_dump(exclude={"model_version"}) for record in records])

    probabilities = model.predict_proba(features)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)

    output = frame.copy()
    output["prediction"] = predictions
    output["churn_probability"] = probabilities.round(4)
    output["risk_level"] = [risk_level_from_probability(float(value)) for value in probabilities]
    output["model_version"] = metadata.version
    output["scored_at"] = scored_at

    if len(output) != len(frame):
        raise ValueError("Output row count does not match input row count")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(output_file, index=False)
    BATCH_RECORDS_PROCESSED_TOTAL.labels(model_version=metadata.version).inc(len(output))
    logger.info(
        "batch_scoring_completed",
        input_path=str(input_file),
        output_path=str(output_file),
        records_processed=len(output),
        model_version=metadata.version,
    )
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch score customer churn records.")
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--output", required=True, help="Output CSV path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    retry(lambda: score_batch(args.input, args.output))


if __name__ == "__main__":
    main()
