import pandas as pd

from batch.batch_score import score_batch


def test_batch_scoring_output_row_count_matches_input(tmp_path) -> None:
    input_path = "batch/sample_input.csv"
    output_path = tmp_path / "predictions.csv"

    output = score_batch(input_path, str(output_path))
    input_frame = pd.read_csv(input_path)

    assert output_path.exists()
    assert len(output) == len(input_frame)
    assert {"prediction", "churn_probability", "risk_level", "model_version", "scored_at"} <= set(
        output.columns
    )

