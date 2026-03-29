from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "mlflow"
    / "scripts"
    / "search_runs.py"
)


def test_search_runs_filters_experiment_name(mlflow_store: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--tracking-uri",
            str(mlflow_store),
            "--experiment-name",
            "recsys",
            "--metric",
            "avg_reward",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["run_count"] == 2
    assert {run["run_id"] for run in payload["runs"]} == {"run_a", "run_b"}
