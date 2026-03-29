from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
LEADERBOARD = ROOT / "core" / "eval-benchmark" / "scripts" / "leaderboard.py"
COMPARE = ROOT / "core" / "eval-benchmark" / "scripts" / "compare_run_pair.py"
HISTORIES = ROOT / "core" / "eval-benchmark" / "scripts" / "inspect_histories.py"
REPORT = ROOT / "core" / "eval-benchmark" / "scripts" / "benchmark_report.py"


def test_leaderboard_ranks_mlflow_runs(mlflow_with_history: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(LEADERBOARD),
            "--mlflow-uri",
            str(mlflow_with_history),
            "--mlflow-experiment-name",
            "recsys",
            "--metric",
            "avg_reward",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["runs"][0]["run_id"] == "run_b"
    assert "agent.lr" in payload["varying_params"]


def test_compare_run_pair_reports_metric_delta(mlflow_with_history: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(COMPARE),
            "--mlflow-uri",
            str(mlflow_with_history),
            "--mlflow-experiment-name",
            "recsys",
            "--candidate",
            "run_b",
            "--baseline",
            "run_c",
            "--metric",
            "avg_reward",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["metric_deltas"]["avg_reward"]["delta"] == 0.6
    assert payload["differing_params"]["agent.lr"]["candidate"] == "0.001"


def test_inspect_histories_supports_mlflow_and_wandb(
    mlflow_with_history: Path,
    sample_runs: dict[str, object],
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(HISTORIES),
            "--mlflow-uri",
            str(mlflow_with_history),
            "--mlflow-experiment-name",
            "recsys",
            "--wandb-path",
            str(sample_runs["root"]),
            "--wandb-project",
            "demo-project",
            "--metric",
            "avg_reward",
            "--json",
            "run_a",
            str(sample_runs["run_ids"][0]),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    summaries = {row["run_id"]: row["history_summary"] for row in payload["runs"]}
    assert summaries["run_a"]["history_count"] == 2
    assert summaries["run_a"]["final_values"]["ctr"] == 0.2
    assert summaries[str(sample_runs["run_ids"][0])]["history_count"] >= 1
    run_a_row = next(row for row in payload["runs"] if row["run_id"] == "run_a")
    assert run_a_row["selected_history_path"].endswith("run_a-history.json")
    assert len(run_a_row["candidate_history_paths"]) == 2


def test_benchmark_report_writes_markdown(mlflow_with_history: Path, tmp_path: Path) -> None:
    out_path = tmp_path / "report.md"
    result = subprocess.run(
        [
            sys.executable,
            str(REPORT),
            "--mlflow-uri",
            str(mlflow_with_history),
            "--mlflow-experiment-name",
            "recsys",
            "--metric",
            "avg_reward",
            "--baseline",
            "run_c",
            "--limit",
            "2",
            "--out",
            str(out_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    assert "# Benchmark Report" in content
    assert "leader_vs_baseline" in content
    assert "| 2 |" in content
    assert "| 3 |" not in content


def test_report_handles_missing_metric_without_fake_leader(mlflow_with_history: Path, tmp_path: Path) -> None:
    out_path = tmp_path / "missing-metric.md"
    subprocess.run(
        [
            sys.executable,
            str(REPORT),
            "--mlflow-uri",
            str(mlflow_with_history),
            "--mlflow-experiment-name",
            "recsys",
            "--metric",
            "does_not_exist",
            "--out",
            str(out_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    content = out_path.read_text(encoding="utf-8")
    assert "leader: none" in content
