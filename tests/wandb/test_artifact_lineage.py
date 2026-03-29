from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import create_artifact_run


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "wandb"
    / "scripts"
    / "artifact_lineage.py"
)


def test_artifact_lineage_finds_producer_run(wandb_offline_dir: Path) -> None:
    create_artifact_run(
        wandb_offline_dir,
        project="demo-project",
        group="artifact-group",
        artifact_name="synthetic-model",
        aliases=["latest", "best"],
    )
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "synthetic-model",
            "--offline-dir",
            str(wandb_offline_dir),
            "--project",
            "demo-project",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["match_count"] == 1
    assert payload["matches"][0]["artifact"]["name"] == "synthetic-model"
    assert sorted(payload["matches"][0]["artifact"]["aliases"]) == ["best", "latest"]
    assert payload["matches"][0]["producer_run"]["project"] == "demo-project"


def test_artifact_lineage_handles_missing_artifact(sample_runs: dict[str, object]) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "missing-artifact",
            "--offline-dir",
            str(sample_runs["root"]),
            "--project",
            "demo-project",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["match_count"] == 0
