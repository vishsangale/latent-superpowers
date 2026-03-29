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
    / "check_mlflow_context.py"
)


def test_check_mlflow_context_reports_file_store(mlflow_store: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--tracking-uri", str(mlflow_store), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["mode"] == "file"
    assert payload["experiment_count"] == 2
    assert "recsys" in payload["experiment_names"]
