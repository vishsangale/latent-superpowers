from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import wandb


SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "core" / "wandb" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from wandb_run_utils import discover_offline_run_files, load_offline_runs  # noqa: E402


@pytest.fixture()
def wandb_offline_dir(tmp_path: Path) -> Path:
    return tmp_path / "wandb-root"


def create_offline_run(
    wandb_offline_dir: Path,
    *,
    project: str = "demo-project",
    group: str | None = None,
    num_episodes: int = 2,
    avg_reward: float = 1.0,
    final_ctr: float = 0.1,
    tags: list[str] | None = None,
    include_avg_reward: bool = True,
) -> str:
    wandb_offline_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("WANDB_SILENT", "true")
    run = wandb.init(
        project=project,
        dir=str(wandb_offline_dir),
        mode="offline",
        group=group,
        job_type="train",
        tags=tags or [],
        config={
            "train": {"num_episodes": num_episodes},
            "model": {"name": "baseline"},
        },
    )
    run.log(
        {
            "episode": 0,
            "reward": avg_reward / 2,
            "ctr": final_ctr / 2,
        }
    )
    if include_avg_reward:
        run.summary["avg_reward"] = avg_reward
    run.summary["final_ctr"] = final_ctr
    run.finish()
    return run.id


@pytest.fixture()
def sample_runs(wandb_offline_dir: Path) -> dict[str, object]:
    run_ids = [
        create_offline_run(
            wandb_offline_dir,
            project="demo-project",
            group="smoke-sweep",
            num_episodes=2,
            avg_reward=1.5,
            final_ctr=0.2,
            tags=["baseline"],
        ),
        create_offline_run(
            wandb_offline_dir,
            project="demo-project",
            group="smoke-sweep",
            num_episodes=3,
            avg_reward=2.0,
            final_ctr=0.25,
            tags=["candidate"],
        ),
        create_offline_run(
            wandb_offline_dir,
            project="demo-project",
            group="alt-sweep",
            num_episodes=4,
            avg_reward=1.2,
            final_ctr=0.15,
        ),
    ]
    run_files = discover_offline_run_files([str(wandb_offline_dir)])
    return {
        "root": wandb_offline_dir,
        "run_ids": run_ids,
        "run_files": run_files,
        "runs": load_offline_runs([str(wandb_offline_dir)]),
    }
