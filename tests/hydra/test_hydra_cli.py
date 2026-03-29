from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[2] / "core" / "hydra" / "scripts"
DETECT = SCRIPTS / "detect_hydra_project.py"
PLAN = SCRIPTS / "plan_multirun.py"
FIND = SCRIPTS / "find_run_config.py"


def test_detect_hydra_project(hydra_repo: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(DETECT), str(hydra_repo), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["likely_hydra_project"] is True
    assert payload["entrypoints"]
    assert payload["config_roots"][0]["path"] == "conf"
    assert "model" in payload["config_roots"][0]["groups"]


def test_plan_multirun_reports_cardinality() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(PLAN),
            "--entrypoint",
            "train.py",
            "--config-path",
            "conf",
            "--config-name",
            "train",
            "seed=1,2",
            "model=baseline,large",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Estimated total runs: 4" in result.stdout
    assert "Planned multirun command:" in result.stdout


def test_find_run_config_recovers_metadata(hydra_repo: Path) -> None:
    nested_path = hydra_repo / "outputs" / "2026-03-29" / "00-00-00" / "metrics.json"
    nested_path.write_text("{}", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(FIND), str(nested_path), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["run_dir"].endswith("outputs/2026-03-29/00-00-00")
    assert payload["overrides"] == ["seed=7", "model=baseline"]
    assert "model.ckpt" in payload["checkpoint_candidates"]
