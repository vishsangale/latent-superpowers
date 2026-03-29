from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from tests.local_dashboard.conftest import ablation_store  # noqa: F401
from tests.eval_benchmark.conftest import mlflow_with_history  # noqa: F401
from tests.wandb.conftest import sample_runs, wandb_offline_dir  # noqa: F401


ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "core" / "reproducibility" / "scripts" / "capture_run_context.py"
VERIFY = ROOT / "core" / "reproducibility" / "scripts" / "verify_repro_context.py"
RECONSTRUCT = ROOT / "core" / "reproducibility" / "scripts" / "reconstruct_local_run.py"
DIFF = ROOT / "core" / "reproducibility" / "scripts" / "diff_run_contexts.py"


def test_capture_verify_and_diff(git_repo: Path, tmp_path: Path) -> None:
    context_path = tmp_path / "context.json"
    subprocess.run(
        [
            sys.executable,
            str(CAPTURE),
            str(git_repo),
            "--command",
            "python train.py",
            "--env-key",
            "HOME",
            "--out",
            str(context_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    verify = subprocess.run(
        [sys.executable, str(VERIFY), str(context_path), "--repo", str(git_repo), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(verify.stdout)
    assert payload["matches"] is True

    dirty_path = tmp_path / "dirty.json"
    saved = json.loads(context_path.read_text(encoding="utf-8"))
    saved["git"]["dirty"] = True
    dirty_path.write_text(json.dumps(saved), encoding="utf-8")
    diff = subprocess.run(
        [sys.executable, str(DIFF), str(context_path), str(dirty_path), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    diff_payload = json.loads(diff.stdout)
    assert "git.dirty" in diff_payload["diff"]


def test_verify_blocks_when_git_unavailable(tmp_path: Path) -> None:
    repo = tmp_path / "plain-dir"
    repo.mkdir()
    context_path = tmp_path / "plain.json"
    subprocess.run(
        [sys.executable, str(CAPTURE), str(repo), "--out", str(context_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    verify = subprocess.run(
        [sys.executable, str(VERIFY), str(context_path), "--repo", str(repo), "--json"],
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(verify.stdout)
    assert verify.returncode == 1
    assert payload["matches"] is False
    assert payload["blocking_issues"]


def test_reconstruct_local_run_mlflow_and_wandb(
    mlflow_with_history: Path,
    sample_runs: dict[str, object],
) -> None:
    mlflow_result = subprocess.run(
        [
            sys.executable,
            str(RECONSTRUCT),
            "run_a",
            "--mlflow-uri",
            str(mlflow_with_history),
            "--mlflow-experiment-name",
            "recsys",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    mlflow_payload = json.loads(mlflow_result.stdout)
    assert mlflow_payload["history_count"] == 2
    assert mlflow_payload["run"]["source"] == "mlflow"

    wandb_result = subprocess.run(
        [
            sys.executable,
            str(RECONSTRUCT),
            str(sample_runs["run_ids"][0]),
            "--wandb-path",
            str(sample_runs["root"]),
            "--wandb-project",
            "demo-project",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    wandb_payload = json.loads(wandb_result.stdout)
    assert wandb_payload["history_count"] >= 1
    assert wandb_payload["run"]["source"] == "wandb-offline"

    missing = subprocess.run(
        [sys.executable, str(RECONSTRUCT), "missing-run-id"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert missing.returncode != 0
    assert "Could not find run" in missing.stderr


def test_diff_rejects_non_context_schema(git_repo: Path, tmp_path: Path) -> None:
    context_path = tmp_path / "context.json"
    subprocess.run(
        [sys.executable, str(CAPTURE), str(git_repo), "--out", str(context_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    reconstructed_path = tmp_path / "run.json"
    reconstructed_path.write_text(json.dumps({"run": {"run_id": "abc"}}), encoding="utf-8")
    diff = subprocess.run(
        [sys.executable, str(DIFF), str(context_path), str(reconstructed_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert diff.returncode != 0
    assert "only supports captured context snapshots" in diff.stderr
