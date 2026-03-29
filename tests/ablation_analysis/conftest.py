from __future__ import annotations

from pathlib import Path

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
    ctr: float,
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
    _write(run_dir / "metrics" / "ctr", f"1000 {ctr} 1\n")
    _write(run_dir / "params" / "agent.lr", lr + "\n")
    _write(run_dir / "params" / "train.seed", seed + "\n")
    _write(run_dir / "params" / "variant", ("fast" if lr == "0.001" else "slow") + "\n")
    _write(run_dir / "tags" / "mlflow.runName", run_id + "\n")
    _write(artifact_dir / "metrics.json", '{"ok": true}\n')


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
    _write_run(exp_dir, experiment_id="123", run_id="run_a", avg_reward=1.2, ctr=0.12, lr="0.001", seed="1")
    _write_run(exp_dir, experiment_id="123", run_id="run_b", avg_reward=1.5, ctr=0.15, lr="0.001", seed="2")
    _write_run(exp_dir, experiment_id="123", run_id="run_c", avg_reward=0.9, ctr=0.09, lr="0.01", seed="1")
    return root
