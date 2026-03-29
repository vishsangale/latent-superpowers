from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "ablation-analysis"
    / "scripts"
    / "collect_runs.py"
)


def test_collect_runs_from_mlflow_store(ablation_store: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--mlflow-uri",
            str(ablation_store),
            "--mlflow-experiment-name",
            "recsys",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["run_count"] == 3
    assert "agent.lr" in payload["varying_params"]
