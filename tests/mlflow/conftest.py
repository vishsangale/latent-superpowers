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
    run_name: str,
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
    _write(run_dir / "params" / "lr", lr + "\n")
    _write(run_dir / "params" / "model", "baseline\n")
    _write(run_dir / "tags" / "mlflow.runName", run_name + "\n")
    _write(artifact_dir / "model.txt", f"artifact for {run_id}\n")


@pytest.fixture()
def mlflow_store(tmp_path: Path) -> Path:
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
    _write_run(
        exp_dir,
        experiment_id="123",
        run_id="run_a",
        avg_reward=1.5,
        ctr=0.2,
        lr="0.001",
        run_name="baseline-a",
    )
    _write_run(
        exp_dir,
        experiment_id="123",
        run_id="run_b",
        avg_reward=2.2,
        ctr=0.3,
        lr="0.0005",
        run_name="baseline-b",
    )

    other_dir = root / "456"
    _write(
        other_dir / "meta.yaml",
        "\n".join(
            [
                "artifact_location: file:///tmp/mlartifacts/456",
                "creation_time: 1000",
                "experiment_id: '456'",
                "last_update_time: 1000",
                "lifecycle_stage: active",
                "name: aux",
            ]
        )
        + "\n",
    )
    _write_run(
        other_dir,
        experiment_id="456",
        run_id="run_c",
        avg_reward=0.8,
        ctr=0.1,
        lr="0.01",
        run_name="aux-c",
    )
    return root
