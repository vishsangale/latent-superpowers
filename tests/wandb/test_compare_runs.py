from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "wandb"
    / "scripts"
    / "compare_runs.py"
)


def test_compare_runs_ranks_by_metric(sample_runs: dict[str, object]) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--offline-dir",
            str(sample_runs["root"]),
            "--project",
            "demo-project",
            "--group",
            "smoke-sweep",
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
    assert payload["runs"][0]["flat_summary"]["avg_reward"] == 2.0
    assert payload["runs"][0]["flat_config"]["train.num_episodes"] == 3
    assert "train.num_episodes" in payload["varying_config_keys"]


def test_compare_runs_handles_single_explicit_run(sample_runs: dict[str, object]) -> None:
    run_file = sample_runs["run_files"][0]
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--run-path",
            str(run_file),
            "--metric",
            "avg_reward",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Found 1 matching run" in result.stdout
