#!/usr/bin/env python3
"""Shared helpers for loading local experiment runs into a normalized shape."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import subprocess
from typing import Any
import statistics
import sys


ROOT = Path(__file__).resolve().parents[2]
MLFLOW_SCRIPTS = ROOT / "core" / "mlflow" / "scripts"
WANDB_SCRIPTS = ROOT / "core" / "wandb" / "scripts"
TENSORBOARD_HELPER = ROOT / "core" / "common" / "tensorboard_loader_helper.py"
for candidate in (MLFLOW_SCRIPTS, WANDB_SCRIPTS):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from mlflow_store_utils import (  # type: ignore[import-not-found]
    artifact_path_for_run as mlflow_artifact_path_for_run,
    discover_experiments,
    discover_experiments_via_client,
    discover_runs,
    discover_runs_via_client,
    filter_runs as filter_mlflow_runs,
    normalize_tracking_uri,
)
from wandb_run_utils import (  # type: ignore[import-not-found]
    filter_runs as filter_wandb_runs,
    flatten_dict,
    load_offline_runs,
    metric_value as wandb_metric_value,
)


@dataclass
class NormalizedRun:
    source: str
    project: str | None
    experiment: str | None
    run_id: str
    name: str | None
    group: str | None
    status: str | None
    start_time: float | int | None
    end_time: float | int | None
    metrics: dict[str, float]
    params: dict[str, Any]
    tags: dict[str, Any]
    artifact_root: str | None
    path: str
    history_count: int


def run_to_dict(run: NormalizedRun) -> dict[str, Any]:
    return asdict(run)


def varying_param_values(runs: list[NormalizedRun]) -> dict[str, list[Any]]:
    values: dict[str, list[Any]] = {}
    for run in runs:
        for key, value in run.params.items():
            bucket = values.setdefault(key, [])
            if value not in bucket:
                bucket.append(value)
    return {key: bucket for key, bucket in values.items() if len(bucket) > 1}


def metric_values(runs: list[NormalizedRun], metric: str) -> list[float]:
    return [float(run.metrics[metric]) for run in runs if metric in run.metrics]


def metric_summary(runs: list[NormalizedRun], metric: str) -> dict[str, float | int | None]:
    values = metric_values(runs, metric)
    if not values:
        return {
            "count": len(runs),
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "stddev": None,
        }
    stddev = statistics.pstdev(values) if len(values) > 1 else 0.0
    return {
        "count": len(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "stddev": stddev,
    }


def run_label(run: NormalizedRun, variant_keys: list[str] | None = None) -> str:
    if variant_keys:
        parts = []
        for key in variant_keys:
            parts.append(f"{key}={run.params.get(key, '<missing>')}")
        return ", ".join(parts)
    return run.name or run.run_id


def load_mlflow_runs_normalized(
    *,
    tracking_uri: str | None = None,
    experiment_name: str | None = None,
    experiment_id: str | None = None,
    limit: int = 1000,
) -> list[NormalizedRun]:
    resolved_uri, store_root, mode = normalize_tracking_uri(tracking_uri)
    if mode == "file":
        experiments = discover_experiments(store_root)
        raw_runs = discover_runs(store_root)
        filtered = filter_mlflow_runs(
            raw_runs,
            experiment_id=experiment_id,
            experiment_name=experiment_name,
            experiments=experiments,
        )
    else:
        experiments = discover_experiments_via_client(resolved_uri)
        filtered = discover_runs_via_client(
            resolved_uri,
            experiment_id=experiment_id,
            experiment_name=experiment_name,
            experiments=experiments,
            limit=limit,
        )

    experiment_names = {experiment.experiment_id: experiment.name for experiment in experiments}
    normalized: list[NormalizedRun] = []
    for run in filtered[:limit]:
        artifact_root = None
        if mode == "file":
            artifact_path = mlflow_artifact_path_for_run(run)
            artifact_root = str(artifact_path) if artifact_path else None
        else:
            artifact_root = run.artifact_uri
        workspace_mlflow_dir = run.tags.get("workspace.mlflow_dir")
        if workspace_mlflow_dir:
            artifact_root = workspace_mlflow_dir
        normalized.append(
            NormalizedRun(
                source="mlflow",
                project=experiment_names.get(run.experiment_id),
                experiment=experiment_names.get(run.experiment_id),
                run_id=run.run_id,
                name=run.tags.get("mlflow.runName"),
                group=None,
                status=str(run.status) if run.status is not None else None,
                start_time=run.start_time,
                end_time=run.end_time,
                metrics=dict(run.metrics),
                params=dict(run.params),
                tags=dict(run.tags),
                artifact_root=artifact_root,
                path=run.path,
                history_count=0,
            )
        )
    return normalized


def load_wandb_runs_normalized(
    *,
    paths: list[str] | None = None,
    project: str | None = None,
    group: str | None = None,
    limit: int = 1000,
) -> list[NormalizedRun]:
    raw_runs = load_offline_runs(paths)
    filtered = filter_wandb_runs(raw_runs, project=project, group=group)
    normalized: list[NormalizedRun] = []
    for run in filtered[:limit]:
        summary_metrics = {
            key: float(value)
            for key, value in flatten_dict(run.summary).items()
            if isinstance(value, (int, float))
        }
        normalized.append(
            NormalizedRun(
                source="wandb-offline",
                project=run.project,
                experiment=run.project,
                run_id=run.run_id or Path(run.path).stem,
                name=run.name,
                group=run.group,
                status=run.state,
                start_time=run.start_time,
                end_time=None,
                metrics=summary_metrics,
                params=flatten_dict(run.config),
                tags={"entity": run.entity, "job_type": run.job_type, "tags": run.tags},
                artifact_root=str(Path(run.path).resolve().parent),
                path=run.path,
                history_count=len(run.history),
            )
        )
    return normalized


def load_tensorboard_runs_normalized(
    *,
    paths: list[str] | None = None,
    project: str | None = None,
    python_executable: str | None = None,
    limit: int = 1000,
) -> list[NormalizedRun]:
    if not paths:
        return []
    roots = [Path(path).expanduser().resolve() for path in paths]
    has_event_files = any(root.exists() and next(root.rglob("events.out.tfevents.*"), None) for root in roots)
    if not has_event_files:
        return []

    if python_executable:
        executable = Path(python_executable).expanduser()
        stem = executable.name.lower()
        if stem.startswith("python"):
            command = [str(executable), str(TENSORBOARD_HELPER)]
        else:
            command = [str(executable)]
    else:
        command = [sys.executable, str(TENSORBOARD_HELPER)]
    for path in paths:
        command.extend(["--path", path])

    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    normalized: list[NormalizedRun] = []
    for item in payload.get("runs", [])[:limit]:
        normalized.append(
            NormalizedRun(
                source="tensorboard",
                project=project or item.get("project"),
                experiment=item.get("experiment"),
                run_id=str(item["run_id"]),
                name=item.get("name"),
                group=item.get("group"),
                status=item.get("status"),
                start_time=item.get("start_time"),
                end_time=item.get("end_time"),
                metrics={
                    key: float(value)
                    for key, value in (item.get("metrics") or {}).items()
                    if isinstance(value, (int, float))
                },
                params=dict(item.get("params") or {}),
                tags=dict(item.get("tags") or {}),
                artifact_root=item.get("artifact_root"),
                path=str(item.get("path") or item.get("artifact_root") or ""),
                history_count=int(item.get("history_count") or 0),
            )
        )
    return normalized


def load_local_runs(
    *,
    mlflow_tracking_uri: str | None = None,
    mlflow_experiment_name: str | None = None,
    mlflow_experiment_id: str | None = None,
    wandb_paths: list[str] | None = None,
    wandb_project: str | None = None,
    wandb_group: str | None = None,
    tensorboard_paths: list[str] | None = None,
    tensorboard_project: str | None = None,
    tensorboard_python: str | None = None,
    limit_per_source: int = 1000,
) -> list[NormalizedRun]:
    runs: list[NormalizedRun] = []
    if mlflow_tracking_uri or mlflow_experiment_name or mlflow_experiment_id:
        runs.extend(
            load_mlflow_runs_normalized(
                tracking_uri=mlflow_tracking_uri,
                experiment_name=mlflow_experiment_name,
                experiment_id=mlflow_experiment_id,
                limit=limit_per_source,
            )
        )
    if wandb_paths:
        runs.extend(
            load_wandb_runs_normalized(
                paths=wandb_paths,
                project=wandb_project,
                group=wandb_group,
                limit=limit_per_source,
            )
        )
    if tensorboard_paths:
        runs.extend(
            load_tensorboard_runs_normalized(
                paths=tensorboard_paths,
                project=tensorboard_project,
                python_executable=tensorboard_python,
                limit=limit_per_source,
            )
        )
    return runs
