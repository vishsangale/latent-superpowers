#!/usr/bin/env python3
"""Shared helpers for eval-benchmark commands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
import statistics
import sys


COMMON_DIR = Path(__file__).resolve().parents[2] / "common"
WANDB_SCRIPTS = Path(__file__).resolve().parents[2] / "wandb" / "scripts"
for candidate in (COMMON_DIR, WANDB_SCRIPTS):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from local_run_utils import NormalizedRun, load_local_runs, run_to_dict, varying_param_values  # type: ignore[import-not-found]
from wandb_run_utils import load_offline_runs  # type: ignore[import-not-found]


def build_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--mlflow-uri", help="MLflow tracking URI")
    parser.add_argument("--mlflow-experiment-name", help="MLflow experiment name")
    parser.add_argument("--mlflow-experiment-id", help="MLflow experiment ID")
    parser.add_argument(
        "--wandb-path",
        action="append",
        default=[],
        help="Path containing local W&B offline runs; may be repeated",
    )
    parser.add_argument("--wandb-project", help="Filter W&B offline runs by project")
    parser.add_argument("--wandb-group", help="Filter W&B offline runs by group")
    parser.add_argument("--metric", default="avg_reward", help="Primary ranking metric")
    parser.add_argument("--direction", choices=["min", "max"], default="max")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def load_runs_from_args(args: argparse.Namespace) -> list[NormalizedRun]:
    return load_local_runs(
        mlflow_tracking_uri=args.mlflow_uri,
        mlflow_experiment_name=args.mlflow_experiment_name,
        mlflow_experiment_id=args.mlflow_experiment_id,
        wandb_paths=args.wandb_path or None,
        wandb_project=args.wandb_project,
        wandb_group=args.wandb_group,
    )


def sort_runs(runs: list[NormalizedRun], metric: str, direction: str) -> list[NormalizedRun]:
    reverse = direction == "max"
    present = [run for run in runs if metric in run.metrics]
    missing = [run for run in runs if metric not in run.metrics]
    present.sort(key=lambda run: run.metrics[metric], reverse=reverse)
    return present + missing


def runs_payload(runs: list[NormalizedRun]) -> list[dict[str, Any]]:
    return [run_to_dict(run) for run in runs]


def _find_history_jsons(root: Path) -> list[Path]:
    return sorted(
        [
            path
            for path in root.rglob("*.json")
            if "history" in path.name.lower()
        ]
    )


def _coerce_history_payload(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict) and isinstance(data.get("history"), list):
        return [item for item in data["history"] if isinstance(item, dict)]
    return []


def load_history_details_for_run(
    run: NormalizedRun,
    *,
    wandb_paths: list[str] | None = None,
) -> dict[str, Any]:
    if run.source == "mlflow" and run.artifact_root:
        artifact_root = Path(run.artifact_root.replace("file://", ""))
        if artifact_root.exists():
            candidates: list[dict[str, Any]] = []
            for candidate in _find_history_jsons(artifact_root):
                try:
                    payload = json.loads(candidate.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                history = _coerce_history_payload(payload)
                if history:
                    candidates.append(
                        {
                            "path": str(candidate),
                            "history": history,
                            "history_count": len(history),
                        }
                    )
            if candidates:
                candidates.sort(
                    key=lambda item: (
                        -item["history_count"],
                        0 if "eval" in Path(item["path"]).name.lower() else 1,
                        item["path"],
                    )
                )
                chosen = candidates[0]
                return {
                    "history": chosen["history"],
                    "selected_path": chosen["path"],
                    "candidate_paths": [item["path"] for item in candidates],
                }
        return {"history": [], "selected_path": None, "candidate_paths": []}

    if run.source == "wandb-offline" and wandb_paths:
        for offline_run in load_offline_runs(wandb_paths):
            if offline_run.run_id != run.run_id:
                continue
            if run.project is not None and offline_run.project != run.project:
                continue
            if run.group is not None and offline_run.group != run.group:
                continue
            return {
                "history": [row for row in offline_run.history if isinstance(row, dict)],
                "selected_path": offline_run.path,
                "candidate_paths": [offline_run.path],
            }
    return {"history": [], "selected_path": None, "candidate_paths": []}


def load_history_for_run(run: NormalizedRun, *, wandb_paths: list[str] | None = None) -> list[dict[str, Any]]:
    return load_history_details_for_run(run, wandb_paths=wandb_paths)["history"]


def history_summary(history: list[dict[str, Any]]) -> dict[str, Any]:
    metric_keys: set[str] = set()
    numeric_final: dict[str, float] = {}
    for row in history:
        for key, value in row.items():
            if isinstance(value, (int, float)):
                metric_keys.add(key)
                numeric_final[key] = float(value)
    if history:
        for key in sorted(metric_keys):
            value = numeric_final.get(key)
            if isinstance(value, (int, float)):
                numeric_final[key] = float(value)
    return {
        "history_count": len(history),
        "metric_keys": sorted(metric_keys),
        "final_values": numeric_final,
    }


def find_run(runs: list[NormalizedRun], run_id: str) -> NormalizedRun:
    for run in runs:
        if run.run_id == run_id:
            return run
    raise KeyError(f"Could not find run {run_id!r}")


def metric_deltas(candidate: NormalizedRun, baseline: NormalizedRun) -> dict[str, dict[str, float | None]]:
    keys = sorted(set(candidate.metrics) | set(baseline.metrics))
    deltas: dict[str, dict[str, float | None]] = {}
    for key in keys:
        candidate_value = candidate.metrics.get(key)
        baseline_value = baseline.metrics.get(key)
        delta = None
        if candidate_value is not None and baseline_value is not None:
            delta = float(candidate_value) - float(baseline_value)
        deltas[key] = {
            "candidate": float(candidate_value) if candidate_value is not None else None,
            "baseline": float(baseline_value) if baseline_value is not None else None,
            "delta": delta,
        }
    return deltas


def differing_params(candidate: NormalizedRun, baseline: NormalizedRun) -> dict[str, dict[str, Any]]:
    keys = sorted(set(candidate.params) | set(baseline.params))
    differences = {}
    for key in keys:
        left = candidate.params.get(key)
        right = baseline.params.get(key)
        if left != right:
            differences[key] = {"candidate": left, "baseline": right}
    return differences


def leaderboard_payload(runs: list[NormalizedRun], *, metric: str, direction: str, limit: int) -> dict[str, Any]:
    ranked = sort_runs(runs, metric, direction)
    payload_runs = runs_payload(ranked[:limit])
    return {
        "metric": metric,
        "direction": direction,
        "run_count": len(runs),
        "varying_params": varying_param_values(runs),
        "runs": payload_runs,
    }


def report_markdown(
    *,
    runs: list[NormalizedRun],
    metric: str,
    direction: str,
    baseline_run: NormalizedRun | None = None,
    limit: int = 10,
) -> str:
    ranked = sort_runs(runs, metric, direction)
    ranked_present = [run for run in ranked if metric in run.metrics]
    lines = ["# Benchmark Report", "", f"- metric: `{metric}` ({direction})", f"- run_count: `{len(runs)}`"]
    if ranked_present:
        best = ranked_present[0]
        lines.append(f"- leader: `{best.run_id}` with `{metric}={best.metrics.get(metric)}`")
    else:
        lines.append("- leader: none (no runs contained the requested metric)")
    if baseline_run is not None and ranked_present:
        leader = ranked_present[0]
        deltas = metric_deltas(leader, baseline_run)
        if metric in deltas and deltas[metric]["delta"] is not None:
            lines.append(
                f"- leader_vs_baseline: `{deltas[metric]['delta']:+.4f}` on `{metric}` relative to `{baseline_run.run_id}`"
            )
    varying = varying_param_values(runs)
    if varying:
        lines.extend(["", "## Varying Params"])
        for key in sorted(varying):
            lines.append(f"- `{key}`: {varying[key]}")
    lines.extend(["", "## Leaderboard", "", "| Rank | Run | Source | Metric |", "| --- | --- | --- | ---: |"])
    for index, run in enumerate(ranked[:limit], start=1):
        value = run.metrics.get(metric)
        rendered = f"{value:.4f}" if isinstance(value, (int, float)) else "-"
        lines.append(f"| {index} | {run.run_id} | {run.source} | {rendered} |")
    return "\n".join(lines)
