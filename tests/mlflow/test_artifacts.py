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
    / "list_artifacts.py"
)


def test_list_artifacts_for_run(mlflow_store: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "run_b",
            "--tracking-uri",
            str(mlflow_store),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["artifact_count"] == 1
    assert payload["artifacts"] == ["model.txt"]
