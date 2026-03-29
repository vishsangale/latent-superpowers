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
    / "compare_runs.py"
)


def test_compare_runs_ranks_by_metric(mlflow_store: Path) -> None:
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
            "--direction",
            "max",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["run_count"] == 2
    assert payload["runs"][0]["run_id"] == "run_b"
    assert payload["varying_params"]["lr"] == ["0.0005", "0.001"]
