#!/usr/bin/env python3
"""Helpers for inspecting MLflow tracking stores."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


@dataclass
class Experiment:
    experiment_id: str
    name: str
    artifact_location: str | None
    lifecycle_stage: str | None
    path: str


@dataclass
class Run:
    run_id: str
    experiment_id: str
    status: str | None
    artifact_uri: str | None
    start_time: int | None
    end_time: int | None
    params: dict[str, str]
    metrics: dict[str, float]
    tags: dict[str, str]
    path: str


def _load_mlflow_client(tracking_uri: str):
    try:
        from mlflow.tracking import MlflowClient
    except ImportError as exc:
        raise RuntimeError(
            "MLflow client support requires the 'mlflow' package in the active Python environment."
        ) from exc
    return MlflowClient(tracking_uri=tracking_uri)


def _coerce_scalar(raw: str) -> Any:
    text = raw.strip()
    if not text:
        return ""
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    if text in {"null", "None", "~"}:
        return None
    if text.lower() == "true":
        return True
    if text.lower() == "false":
        return False
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return text


def parse_simple_yaml(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = _coerce_scalar(value)
    return data


def normalize_tracking_uri(tracking_uri: str | None = None) -> tuple[str, Path | None, str]:
    raw = tracking_uri or ""
    if not raw:
        default_sqlite = Path.cwd() / "mlflow.db"
        if default_sqlite.exists():
            return (f"sqlite:///{default_sqlite.resolve()}", default_sqlite.resolve(), "sqlite")
        default = Path.cwd() / "mlruns"
        return (str(default.resolve()), default.resolve(), "file")

    if raw.startswith("file://"):
        parsed = Path(urlparse(raw).path).resolve()
        return (raw, parsed, "file")

    if raw.startswith("sqlite:///"):
        parsed = Path(raw.removeprefix("sqlite:///")).expanduser().resolve()
        return (raw, parsed, "sqlite")

    if raw.startswith("http://") or raw.startswith("https://"):
        scheme = "http" if raw.startswith("http://") else "https"
        return (raw, None, scheme)

    parsed = Path(raw).expanduser().resolve()
    return (str(parsed), parsed, "file")


def discover_experiments(store_root: Path | None) -> list[Experiment]:
    if store_root is None or not store_root.exists():
        return []

    experiments: list[Experiment] = []
    for path in sorted(store_root.iterdir()):
        if not path.is_dir() or path.name == ".trash":
            continue
        meta = parse_simple_yaml(path / "meta.yaml")
        if not meta:
            continue
        experiments.append(
            Experiment(
                experiment_id=str(meta.get("experiment_id", path.name)),
                name=str(meta.get("name", path.name)),
                artifact_location=meta.get("artifact_location"),
                lifecycle_stage=meta.get("lifecycle_stage"),
                path=str(path),
            )
        )
    return experiments


def discover_experiments_via_client(tracking_uri: str) -> list[Experiment]:
    client = _load_mlflow_client(tracking_uri)
    experiments = []
    for experiment in client.search_experiments(max_results=1000):
        experiments.append(
            Experiment(
                experiment_id=str(experiment.experiment_id),
                name=experiment.name,
                artifact_location=getattr(experiment, "artifact_location", None),
                lifecycle_stage=getattr(experiment, "lifecycle_stage", None),
                path="",
            )
        )
    return experiments


def _read_metric_file(path: Path) -> float | None:
    if not path.exists():
        return None
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return None
    last = lines[-1].split()
    if len(last) >= 2:
        try:
            return float(last[1])
        except ValueError:
            return None
    try:
        return float(last[0])
    except ValueError:
        return None


def _read_value_dir(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for child in sorted(path.iterdir()):
        if child.is_file():
            values[child.name] = child.read_text(encoding="utf-8").strip()
    return values


def _read_metrics_dir(path: Path) -> dict[str, float]:
    metrics: dict[str, float] = {}
    if not path.exists():
        return metrics
    for child in sorted(path.iterdir()):
        if child.is_file():
            value = _read_metric_file(child)
            if value is not None:
                metrics[child.name] = value
    return metrics


def discover_runs(store_root: Path | None) -> list[Run]:
    runs: list[Run] = []
    for experiment in discover_experiments(store_root):
        experiment_path = Path(experiment.path)
        for path in sorted(experiment_path.iterdir()):
            if not path.is_dir():
                continue
            meta = parse_simple_yaml(path / "meta.yaml")
            if "run_id" not in meta:
                continue
            runs.append(
                Run(
                    run_id=str(meta.get("run_id")),
                    experiment_id=str(meta.get("experiment_id", experiment.experiment_id)),
                    status=meta.get("status"),
                    artifact_uri=meta.get("artifact_uri"),
                    start_time=meta.get("start_time"),
                    end_time=meta.get("end_time"),
                    params=_read_value_dir(path / "params"),
                    metrics=_read_metrics_dir(path / "metrics"),
                    tags=_read_value_dir(path / "tags"),
                    path=str(path),
                )
            )
    return runs


def discover_runs_via_client(
    tracking_uri: str,
    *,
    experiment_id: str | None = None,
    experiment_name: str | None = None,
    experiments: list[Experiment] | None = None,
    run_ids: set[str] | None = None,
    limit: int = 500,
) -> list[Run]:
    client = _load_mlflow_client(tracking_uri)
    selected_experiment_ids: list[str] = []
    if experiment_name and experiments is not None:
        selected_experiment_ids = [
            experiment.experiment_id for experiment in experiments if experiment.name == experiment_name
        ]
    elif experiment_id:
        selected_experiment_ids = [experiment_id]
    elif experiments is not None:
        selected_experiment_ids = [experiment.experiment_id for experiment in experiments]

    if not selected_experiment_ids:
        return []

    payload = client.search_runs(
        experiment_ids=selected_experiment_ids,
        filter_string="",
        max_results=limit,
    )
    runs: list[Run] = []
    for item in payload:
        run_id = item.info.run_id
        if run_ids and run_id not in run_ids:
            continue
        runs.append(
            Run(
                run_id=run_id,
                experiment_id=str(item.info.experiment_id),
                status=getattr(item.info, "status", None),
                artifact_uri=getattr(item.info, "artifact_uri", None),
                start_time=getattr(item.info, "start_time", None),
                end_time=getattr(item.info, "end_time", None),
                params=dict(item.data.params),
                metrics={key: float(value) for key, value in item.data.metrics.items()},
                tags=dict(item.data.tags),
                path="",
            )
        )
    return runs


def filter_runs(
    runs: list[Run],
    *,
    experiment_id: str | None = None,
    experiment_name: str | None = None,
    experiments: list[Experiment] | None = None,
    run_ids: set[str] | None = None,
) -> list[Run]:
    filtered = runs
    if experiment_name and experiments is not None:
        matching_ids = {
            experiment.experiment_id for experiment in experiments if experiment.name == experiment_name
        }
        filtered = [run for run in filtered if run.experiment_id in matching_ids]
    if experiment_id:
        filtered = [run for run in filtered if run.experiment_id == experiment_id]
    if run_ids:
        filtered = [run for run in filtered if run.run_id in run_ids]
    return filtered


def artifact_path_for_run(run: Run) -> Path | None:
    if not run.artifact_uri:
        default = Path(run.path) / "artifacts"
        return default if default.exists() else None
    if run.artifact_uri.startswith("file://"):
        return Path(urlparse(run.artifact_uri).path)
    candidate = Path(run.artifact_uri)
    if candidate.exists():
        return candidate
    default = Path(run.path) / "artifacts"
    return default if default.exists() else None


def list_artifacts_via_client(tracking_uri: str, run_id: str, path: str | None = None) -> list[str]:
    client = _load_mlflow_client(tracking_uri)
    artifacts = client.list_artifacts(run_id, path=path)
    output: list[str] = []
    for artifact in artifacts:
        output.append(artifact.path)
        if artifact.is_dir:
            output.extend(list_artifacts_via_client(tracking_uri, run_id, artifact.path))
    return sorted(output)


def run_to_dict(run: Run) -> dict[str, Any]:
    return asdict(run)


def experiment_to_dict(experiment: Experiment) -> dict[str, Any]:
    return asdict(experiment)
