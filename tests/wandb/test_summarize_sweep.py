from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import create_offline_run


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "wandb"
    / "scripts"
    / "summarize_sweep.py"
)


def test_summarize_sweep_reports_best_run(sample_runs: dict[str, object]) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "smoke-sweep",
            "--offline-dir",
            str(sample_runs["root"]),
            "--project",
            "demo-project",
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
    assert payload["best_run"]["flat_summary"]["avg_reward"] == 2.0
    assert payload["parameter_effects"]["train.num_episodes"]["3"] == 2.0


def test_summarize_sweep_tracks_incomplete_runs(wandb_offline_dir: Path) -> None:
    create_offline_run(
        wandb_offline_dir,
        project="demo-project",
        group="incomplete-sweep",
        num_episodes=2,
        avg_reward=1.5,
        final_ctr=0.2,
        include_avg_reward=False,
    )
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "incomplete-sweep",
            "--offline-dir",
            str(wandb_offline_dir),
            "--project",
            "demo-project",
            "--metric",
            "avg_reward",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["incomplete_run_count"] == 1
    assert payload["best_run"] is None
