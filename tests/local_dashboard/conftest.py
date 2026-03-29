from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_run(
    experiment_dir: Path,
    *,
    experiment_id: str,
    run_id: str,
    avg_reward: float,
    loss: float,
    lr: str,
    seed: str,
) -> None:
    run_dir = experiment_dir / run_id
    artifact_dir = run_dir / "artifacts"
    _write(
        run_dir / "meta.yaml",
        "\n".join(
            [
                f"artifact_uri: file://{artifact_dir}",
                "end_time: 2000",
                f"experiment_id: '{experiment_id}'",
                "lifecycle_stage: active",
                f"run_id: {run_id}",
                "start_time: 1000",
                "status: FINISHED",
            ]
        )
        + "\n",
    )
    _write(run_dir / "metrics" / "avg_reward", f"1000 {avg_reward} 1\n")
    _write(run_dir / "metrics" / "loss", f"1000 {loss} 1\n")
    _write(run_dir / "params" / "agent.lr", lr + "\n")
    _write(run_dir / "params" / "train.seed", seed + "\n")
    _write(run_dir / "tags" / "mlflow.runName", run_id + "\n")
    _write(artifact_dir / "artifact.txt", f"artifact for {run_id}\n")
    _write(artifact_dir / "summary.json", '{"ok": true}\n')


@pytest.fixture()
def ablation_store(tmp_path: Path) -> Path:
    root = tmp_path / "mlruns"
    exp_dir = root / "123"
    _write(
        exp_dir / "meta.yaml",
        "\n".join(
            [
                "artifact_location: file:///tmp/mlartifacts/123",
                "creation_time: 1000",
                "experiment_id: '123'",
                "last_update_time: 1000",
                "lifecycle_stage: active",
                "name: recsys",
            ]
        )
        + "\n",
    )
    _write_run(exp_dir, experiment_id="123", run_id="run_a", avg_reward=1.2, loss=0.9, lr="0.001", seed="1")
    _write_run(exp_dir, experiment_id="123", run_id="run_b", avg_reward=1.5, loss=0.7, lr="0.001", seed="2")
    _write_run(exp_dir, experiment_id="123", run_id="run_c", avg_reward=0.9, loss=1.4, lr="0.01", seed="1")
    return root


@pytest.fixture()
def wandb_store(tmp_path: Path) -> Path:
    root = tmp_path / "wandb"
    code = """
import os
from pathlib import Path
import wandb

root = Path(os.environ["WANDB_DIR"])
run = wandb.init(
    project="recsys",
    group="sweep-a",
    name="wandb_run",
    dir=str(root),
    mode="offline",
    config={"agent": {"lr": 0.02}, "train": {"seed": 7}},
)
wandb.log({"avg_reward": 1.7, "loss": 0.5})
run.finish()
run_dirs = sorted(root.rglob("offline-run-*"))
target = run_dirs[-1]
(target / "preview.md").write_text("# preview\\nwandb artifact preview\\n", encoding="utf-8")
"""
    subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        cwd=tmp_path,
        env={**os.environ, "WANDB_DIR": str(root)},
    )
    return root
