#!/usr/bin/env python3
"""Shared helpers for the local dashboard."""

from __future__ import annotations

import json
from pathlib import Path
import statistics
from typing import Any
import sys


CORE_ROOT = Path(__file__).resolve().parents[2]
COMMON_DIR = CORE_ROOT / "common"
ABLATION_SCRIPTS = CORE_ROOT / "ablation-analysis" / "scripts"
for candidate in (COMMON_DIR, ABLATION_SCRIPTS):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from ablation_utils import group_runs, grouped_payload  # type: ignore[import-not-found]
from local_run_utils import (  # type: ignore[import-not-found]
    NormalizedRun,
    load_mlflow_runs_normalized,
    load_tensorboard_runs_normalized,
    load_wandb_runs_normalized,
    run_to_dict,
    varying_param_values,
)
from workspace_results_utils import (  # type: ignore[import-not-found]
    ProjectManifest,
    discover_project_manifests,
    manifest_to_dict,
)


TEXT_SUFFIXES = {
    ".csv",
    ".json",
    ".log",
    ".md",
    ".py",
    ".txt",
    ".tsv",
    ".yaml",
    ".yml",
}
IMAGE_SUFFIXES = {".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}
MAX_TEXT_PREVIEW_BYTES = 200_000
SENSITIVE_TOKENS = ("api_key", "apikey", "credential", "password", "secret", "token")


def normalize_variant_keys(raw_values: list[str] | None) -> list[str]:
    keys: list[str] = []
    for value in raw_values or []:
        for item in value.split(","):
            key = item.strip()
            if key and key not in keys:
                keys.append(key)
    return keys


def _metric_keys(runs: list[NormalizedRun]) -> list[str]:
    counts: dict[str, int] = {}
    for run in runs:
        for key in run.metrics:
            counts[key] = counts.get(key, 0) + 1
    return [key for key, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in SENSITIVE_TOKENS)


def _redact_mapping(data: Any) -> Any:
    if isinstance(data, dict):
        payload: dict[str, Any] = {}
        for key, value in data.items():
            if _is_sensitive_key(str(key)):
                payload[key] = "<redacted>"
            else:
                payload[key] = _redact_mapping(value)
        return payload
    if isinstance(data, list):
        return [_redact_mapping(item) for item in data]
    return data


def safe_run_to_dict(run: NormalizedRun) -> dict[str, Any]:
    payload = run_to_dict(run)
    payload["params"] = _redact_mapping(payload.get("params", {}))
    payload["tags"] = _redact_mapping(payload.get("tags", {}))
    return payload


def _status_counts(runs: list[NormalizedRun]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for run in runs:
        key = (run.status or "unknown").lower()
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _timestamp_bounds(runs: list[NormalizedRun]) -> dict[str, float | int | None]:
    starts = [run.start_time for run in runs if run.start_time is not None]
    ends = [run.end_time for run in runs if run.end_time is not None]
    return {
        "min_start_time": min(starts) if starts else None,
        "max_start_time": max(starts) if starts else None,
        "max_end_time": max(ends) if ends else None,
    }


def _source_detail(
    *,
    source: str,
    source_runs: list[NormalizedRun],
    warning: str | None,
    config: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source": source,
        "run_count": len(source_runs),
        "status_counts": _status_counts(source_runs),
        "warning": warning,
        "config": config,
    }


def load_dashboard_state(
    *,
    project_name: str | None = None,
    repo_root: str | None = None,
    project_results_dir: str | None = None,
    mlflow_uri: str | None,
    mlflow_experiment_name: str | None,
    mlflow_experiment_id: str | None,
    wandb_paths: list[str] | None,
    wandb_project: str | None,
    wandb_group: str | None,
    tensorboard_paths: list[str] | None = None,
    tensorboard_python: str | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    runs: list[NormalizedRun] = []
    source_details: list[dict[str, Any]] = []

    if mlflow_uri or mlflow_experiment_name or mlflow_experiment_id:
        try:
            mlflow_runs = load_mlflow_runs_normalized(
                tracking_uri=mlflow_uri,
                experiment_name=mlflow_experiment_name,
                experiment_id=mlflow_experiment_id,
            )
            runs.extend(mlflow_runs)
            source_details.append(
                _source_detail(
                    source="mlflow",
                    source_runs=mlflow_runs,
                    warning=None,
                    config={
                        "tracking_uri": mlflow_uri,
                        "experiment_name": mlflow_experiment_name,
                        "experiment_id": mlflow_experiment_id,
                    },
                )
            )
        except Exception as exc:  # pragma: no cover
            warning = f"Failed to load MLflow runs: {exc}"
            warnings.append(warning)
            source_details.append(
                _source_detail(
                    source="mlflow",
                    source_runs=[],
                    warning=warning,
                    config={
                        "tracking_uri": mlflow_uri,
                        "experiment_name": mlflow_experiment_name,
                        "experiment_id": mlflow_experiment_id,
                    },
                )
            )

    if wandb_paths:
        try:
            wandb_runs = load_wandb_runs_normalized(
                paths=wandb_paths,
                project=wandb_project,
                group=wandb_group,
            )
            runs.extend(wandb_runs)
            source_details.append(
                _source_detail(
                    source="wandb-offline",
                    source_runs=wandb_runs,
                    warning=None,
                    config={
                        "paths": wandb_paths,
                        "project": wandb_project,
                        "group": wandb_group,
                    },
                )
            )
        except Exception as exc:  # pragma: no cover
            warning = f"Failed to load offline W&B runs: {exc}"
            warnings.append(warning)
            source_details.append(
                _source_detail(
                    source="wandb-offline",
                    source_runs=[],
                    warning=warning,
                    config={
                        "paths": wandb_paths,
                        "project": wandb_project,
                        "group": wandb_group,
                    },
                )
            )

    if tensorboard_paths:
        try:
            tensorboard_runs = load_tensorboard_runs_normalized(
                paths=tensorboard_paths,
                project=project_name,
                python_executable=tensorboard_python,
            )
            runs.extend(tensorboard_runs)
            source_details.append(
                _source_detail(
                    source="tensorboard",
                    source_runs=tensorboard_runs,
                    warning=None,
                    config={
                        "paths": tensorboard_paths,
                        "python": tensorboard_python,
                    },
                )
            )
        except Exception as exc:  # pragma: no cover
            warning = f"Failed to load TensorBoard runs: {exc}"
            warnings.append(warning)
            source_details.append(
                _source_detail(
                    source="tensorboard",
                    source_runs=[],
                    warning=warning,
                    config={
                        "paths": tensorboard_paths,
                        "python": tensorboard_python,
                    },
                )
            )

    runs.sort(key=lambda run: ((run.start_time or 0), run.run_id), reverse=True)
    return {
        "project_name": project_name or mlflow_experiment_name or wandb_project,
        "repo_root": repo_root,
        "project_results_dir": project_results_dir,
        "sources": [detail["source"] for detail in source_details if detail["run_count"] > 0],
        "source_details": source_details,
        "warnings": warnings,
        "run_count": len(runs),
        "status_counts": _status_counts(runs),
        "available_metrics": _metric_keys(runs),
        "available_variant_keys": sorted(varying_param_values(runs)),
        "timestamps": _timestamp_bounds(runs),
        "runs": runs,
    }


def serializable_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "project_name": state.get("project_name"),
        "repo_root": state.get("repo_root"),
        "project_results_dir": state.get("project_results_dir"),
        "sources": state["sources"],
        "source_details": state["source_details"],
        "warnings": state["warnings"],
        "run_count": state["run_count"],
        "status_counts": state["status_counts"],
        "available_metrics": state["available_metrics"],
        "available_variant_keys": state["available_variant_keys"],
        "timestamps": state["timestamps"],
        "runs": [safe_run_to_dict(run) for run in state["runs"]],
    }


def _project_summary(manifest: ProjectManifest, state: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": manifest.name,
        "repo_root": manifest.repo_root,
        "project_results_dir": manifest.project_results_dir,
        "manifest": manifest_to_dict(manifest),
        "run_count": state["run_count"],
        "sources": state["sources"],
        "source_details": state["source_details"],
        "warnings": state["warnings"],
        "status_counts": state["status_counts"],
        "available_metrics": state["available_metrics"],
        "timestamps": state["timestamps"],
    }


def load_workspace_state(*, results_root: str) -> dict[str, Any]:
    manifests = discover_project_manifests(results_root)
    project_states: dict[str, dict[str, Any]] = {}
    project_summaries: list[dict[str, Any]] = []
    warnings: list[str] = []

    for manifest in manifests:
        project_state = load_dashboard_state(
            project_name=manifest.name,
            repo_root=manifest.repo_root,
            project_results_dir=manifest.project_results_dir,
            mlflow_uri=manifest.mlflow_tracking_uri,
            mlflow_experiment_name=manifest.mlflow_experiment_name,
            mlflow_experiment_id=None,
            wandb_paths=manifest.wandb_paths,
            wandb_project=manifest.wandb_project,
            wandb_group=None,
            tensorboard_paths=manifest.tensorboard_paths,
            tensorboard_python=manifest.tensorboard_python,
        )
        project_states[manifest.name] = project_state
        project_summaries.append(_project_summary(manifest, project_state))

    if not manifests:
        warnings.append(f"No project manifests found under {results_root}.")

    default_project = project_summaries[0]["name"] if project_summaries else None
    return {
        "mode": "workspace",
        "results_root": str(Path(results_root).expanduser().resolve()),
        "warnings": warnings,
        "projects": project_summaries,
        "project_states": project_states,
        "default_project": default_project,
    }


def workspace_payload(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("mode") == "workspace":
        return {
            "mode": "workspace",
            "results_root": state["results_root"],
            "warnings": state["warnings"],
            "projects": state["projects"],
            "default_project": state["default_project"],
        }
    project_name = state.get("project_name") or "current"
    return {
        "mode": "single",
        "results_root": None,
        "warnings": state.get("warnings", []),
        "projects": [
            {
                "name": project_name,
                "repo_root": state.get("repo_root"),
                "project_results_dir": state.get("project_results_dir"),
                "manifest": None,
                "run_count": state["run_count"],
                "sources": state["sources"],
                "source_details": state["source_details"],
                "warnings": state["warnings"],
                "status_counts": state["status_counts"],
                "available_metrics": state["available_metrics"],
                "timestamps": state["timestamps"],
            }
        ],
        "default_project": project_name,
    }


def resolve_project_state(state: dict[str, Any], project_name: str | None = None) -> dict[str, Any]:
    if state.get("mode") != "workspace":
        return state
    selected = project_name or state.get("default_project")
    if selected and selected in state["project_states"]:
        return state["project_states"][selected]
    if state["project_states"]:
        first_key = next(iter(state["project_states"]))
        return state["project_states"][first_key]
    return load_dashboard_state(
        project_name=project_name,
        repo_root=None,
        project_results_dir=None,
        mlflow_uri=None,
        mlflow_experiment_name=None,
        mlflow_experiment_id=None,
        wandb_paths=None,
        wandb_project=None,
        wandb_group=None,
        tensorboard_paths=None,
        tensorboard_python=None,
    )


def filtered_runs(
    state: dict[str, Any],
    *,
    source: str | None = None,
    search: str | None = None,
    run_ids: list[str] | None = None,
) -> list[NormalizedRun]:
    runs = list(state["runs"])
    if source and source != "all":
        runs = [run for run in runs if run.source == source]
    if run_ids:
        allowed = set(run_ids)
        runs = [run for run in runs if run.run_id in allowed]
    if search:
        needle = search.lower()
        filtered: list[NormalizedRun] = []
        for run in runs:
            haystack = json.dumps(
                {
                    "name": run.name,
                    "run_id": run.run_id,
                    "group": run.group,
                    "project": run.project,
                    "experiment": run.experiment,
                    "status": run.status,
                    "params": run.params,
                    "tags": run.tags,
                },
                sort_keys=True,
            ).lower()
            if needle in haystack:
                filtered.append(run)
        runs = filtered
    return runs


def grouped_compare(
    state: dict[str, Any],
    *,
    metric: str,
    direction: str,
    variant_keys: list[str],
    source: str | None = None,
    search: str | None = None,
    run_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    runs = filtered_runs(state, source=source, search=search, run_ids=run_ids)
    rows = grouped_payload(group_runs(runs, variant_keys), metric, direction=direction)
    run_lookup = {run.run_id: run for run in runs}
    for row in rows:
        row_ids = {item["run_id"] for item in row["runs"]}
        row["runs"] = [safe_run_to_dict(run_lookup[run_id]) for run_id in row_ids if run_id in run_lookup]
    return rows


def find_run(state: dict[str, Any], run_id: str) -> NormalizedRun | None:
    return next((run for run in state["runs"] if run.run_id == run_id), None)


def _safe_artifact_path(root: str | None, relative_path: str | None = None) -> Path | None:
    if not root:
        return None
    base = Path(root).expanduser().resolve()
    if not base.exists():
        return None
    if relative_path is None:
        return base
    candidate = (base / relative_path).resolve()
    if candidate != base and base not in candidate.parents:
        return None
    if not candidate.exists():
        return None
    return candidate


def _artifact_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        return "image"
    if suffix in TEXT_SUFFIXES:
        return "text"
    return "binary"


def list_artifacts(state: dict[str, Any], run_id: str) -> dict[str, Any]:
    run = find_run(state, run_id)
    if run is None:
        return {"run_id": run_id, "artifact_root": None, "artifacts": []}

    root = _safe_artifact_path(run.artifact_root)
    artifacts: list[dict[str, Any]] = []
    if root and root.is_dir():
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            stat = path.stat()
            kind = _artifact_kind(path)
            artifacts.append(
                {
                    "path": str(path.relative_to(root)),
                    "kind": kind,
                    "size_bytes": stat.st_size,
                    "modified_time": stat.st_mtime,
                    "previewable": kind in {"image", "text"},
                }
            )
    return {
        "run_id": run_id,
        "artifact_root": str(root) if root else run.artifact_root,
        "artifacts": artifacts,
    }


def read_artifact_preview(state: dict[str, Any], run_id: str, relative_path: str) -> dict[str, Any]:
    run = find_run(state, run_id)
    if run is None:
        return {"run_id": run_id, "path": relative_path, "error": "unknown run"}

    target = _safe_artifact_path(run.artifact_root, relative_path)
    if target is None or not target.is_file():
        return {"run_id": run_id, "path": relative_path, "error": "artifact not found"}

    kind = _artifact_kind(target)
    payload: dict[str, Any] = {
        "run_id": run_id,
        "path": relative_path,
        "kind": kind,
        "download_path": relative_path,
    }
    if kind == "image":
        payload["image_path"] = relative_path
        return payload
    if kind == "text":
        with target.open("r", encoding="utf-8", errors="replace") as handle:
            raw = handle.read(MAX_TEXT_PREVIEW_BYTES + 1)
        if target.suffix.lower() == ".json":
            try:
                raw = json.dumps(json.loads(raw), indent=2, sort_keys=True)
            except Exception:
                pass
        payload["text"] = raw[:MAX_TEXT_PREVIEW_BYTES]
        payload["truncated"] = len(raw) > MAX_TEXT_PREVIEW_BYTES
        return payload
    payload["message"] = "Binary preview is not supported in the dashboard."
    return payload


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Local Experiment Dashboard</title>
  <style>
    :root {
      --bg: #f4eee2;
      --ink: #1a1510;
      --muted: #6d6257;
      --paper: #fffdf8;
      --paper-2: #fff7ef;
      --line: #ddcfbc;
      --accent: #b84c17;
      --good: #1f7a4d;
      --good-soft: #dff2e7;
      --warn: #9b5b00;
      --warn-soft: #fff0d6;
      --danger: #993535;
      --danger-soft: #fde7e7;
      --shadow: 0 18px 40px rgba(46, 30, 16, 0.08);
      --radius: 18px;
    }
    * { box-sizing: border-box; }
    html, body { margin: 0; }
    body {
      font-family: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(255,255,255,0.78), rgba(244,238,226,0) 32%),
        linear-gradient(180deg, #f6efe4 0%, var(--bg) 100%);
    }
    .page {
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr);
      min-height: 100vh;
      gap: 20px;
      padding: 20px;
    }
    .panel {
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }
    .card { padding: 18px; }
    .sidebar {
      display: grid;
      gap: 16px;
      align-content: start;
      position: sticky;
      top: 20px;
      max-height: calc(100vh - 40px);
    }
    .stack, .project-list, .health-list, .compare-list, .short-grid, .artifact-list, .kv-table {
      display: grid;
      gap: 12px;
    }
    .eyebrow {
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0.1em;
      font-size: 11px;
      margin-bottom: 10px;
    }
    h1, h2, h3, p { margin: 0; }
    h1 { font-size: 32px; line-height: 1.05; margin-bottom: 12px; }
    h2 { font-size: 19px; }
    .copy, .muted, .tiny {
      color: var(--muted);
      line-height: 1.5;
    }
    .tiny { font-size: 12px; }
    .project-card, .stat, .health-item, .compare-row, .short-card, .artifact-item, .kv-row {
      border: 1px solid var(--line);
      border-radius: 14px;
      background: var(--paper-2);
    }
    .project-card, .stat, .health-item, .compare-row, .short-card, .artifact-item { padding: 12px; }
    .project-card.active {
      background: linear-gradient(135deg, rgba(184,76,23,0.12), rgba(255,255,255,0.85));
      border-color: var(--accent);
    }
    .project-button {
      all: unset;
      display: block;
      width: 100%;
      cursor: pointer;
    }
    .project-name { font-size: 14px; font-weight: 700; margin-bottom: 6px; }
    .stats {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }
    .stat .label {
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 6px;
    }
    .stat .value { font-size: 26px; font-weight: 700; line-height: 1; }
    .main { display: grid; gap: 18px; }
    .hero {
      display: grid;
      grid-template-columns: 1.3fr 0.9fr;
      gap: 18px;
    }
    .hero-main, .hero-side { padding: 22px; }
    .hero-main {
      background:
        linear-gradient(140deg, rgba(184, 76, 23, 0.11), rgba(255,255,255,0) 52%),
        linear-gradient(180deg, #fffdf8, #fff7ef);
      min-height: 220px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }
    .hero-side {
      background:
        linear-gradient(160deg, rgba(23,76,115,0.08), rgba(255,255,255,0) 46%),
        var(--paper);
    }
    .chip-row, .status-row, .toolbar, .detail-tabs, .artifact-actions, .inline-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }
    .chip, .badge, .source-pill, .tab {
      border-radius: 999px;
      border: 1px solid var(--line);
      padding: 7px 11px;
      font-size: 12px;
      background: rgba(255,255,255,0.9);
      cursor: pointer;
    }
    .chip.active, .source-pill.active, .tab.active {
      background: var(--accent);
      color: white;
      border-color: var(--accent);
    }
    .badge.info { background: white; }
    .badge.warn { background: var(--warn-soft); color: var(--warn); border-color: #f1d39d; }
    .badge.error { background: var(--danger-soft); color: var(--danger); border-color: #efc6c6; }
    .badge.good { background: var(--good-soft); color: var(--good); border-color: #cbe4d6; }
    .controls {
      display: grid;
      grid-template-columns: 1.15fr 0.9fr 0.8fr 0.6fr 1.05fr 0.8fr auto;
      gap: 10px;
      margin-bottom: 12px;
    }
    input, select, button {
      width: 100%;
      font: inherit;
      border-radius: 10px;
      padding: 10px 12px;
      border: 1px solid var(--line);
    }
    input, select { background: white; color: var(--ink); }
    button {
      background: var(--accent);
      color: white;
      border-color: var(--accent);
      cursor: pointer;
      font-weight: 700;
    }
    button.secondary {
      background: white;
      color: var(--accent);
      border-color: var(--line);
      font-weight: 600;
    }
    .layout {
      display: grid;
      grid-template-columns: 1.45fr 0.95fr;
      gap: 18px;
    }
    .section-head {
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 16px;
      margin-bottom: 14px;
    }
    .table-wrap { overflow: auto; }
    table { width: 100%; border-collapse: collapse; }
    th, td {
      padding: 10px 8px;
      border-bottom: 1px solid #efe4d5;
      text-align: left;
      vertical-align: top;
      font-size: 13px;
    }
    th {
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    tbody tr:hover td { background: #fff7ef; }
    .run-name { font-weight: 700; margin-bottom: 3px; }
    .metric-value { color: var(--good); font-weight: 700; font-size: 14px; }
    .bar-shell {
      height: 10px;
      border-radius: 999px;
      background: #eadfce;
      overflow: hidden;
      margin: 8px 0;
    }
    .bar-fill {
      height: 100%;
      border-radius: 999px;
      background: linear-gradient(90deg, var(--accent), #e68b4c);
    }
    .winner {
      border: 1px solid #cbe4d6;
      background: var(--good-soft);
      border-radius: 14px;
      padding: 14px;
      margin-bottom: 12px;
    }
    .viz-shell, .summary-shell, .preview-shell {
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fbf7ef;
      padding: 12px;
      white-space: pre-wrap;
      font-size: 12px;
      overflow: auto;
    }
    .viz-svg {
      width: 100%;
      min-height: 320px;
      background: white;
      border: 1px solid var(--line);
      border-radius: 12px;
    }
    .short-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .detail-hero {
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
      background: linear-gradient(140deg, rgba(23,76,115,0.05), rgba(255,255,255,0));
      margin-bottom: 12px;
    }
    .detail-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
      margin-top: 12px;
    }
    .kv-row {
      display: grid;
      grid-template-columns: minmax(0, 0.85fr) minmax(0, 1.15fr);
      gap: 10px;
      padding: 10px 12px;
      font-size: 12px;
    }
    .preview-image {
      max-width: 100%;
      border-radius: 12px;
      border: 1px solid var(--line);
      background: white;
    }
    .empty { color: var(--muted); padding: 12px 0; font-size: 13px; }
    @media (max-width: 1400px) {
      .page { grid-template-columns: 1fr; }
      .sidebar { position: static; max-height: none; }
    }
    @media (max-width: 1180px) {
      .hero, .layout { grid-template-columns: 1fr; }
      .controls { grid-template-columns: 1fr 1fr; }
      .stats, .detail-grid, .short-grid { grid-template-columns: 1fr 1fr; }
    }
    @media (max-width: 760px) {
      .page { padding: 12px; }
      .controls, .stats, .detail-grid, .short-grid { grid-template-columns: 1fr; }
      .kv-row { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="page">
    <aside class="sidebar">
      <section class="panel card">
        <div class="eyebrow">Workspace Scope</div>
        <h2>Projects</h2>
        <p class="copy" style="margin-top:8px;">Select one project on the left. All views on the right are scoped only to that project.</p>
        <div class="summary-shell" id="workspaceMeta" style="margin-top:12px;">Loading workspace...</div>
      </section>
      <section class="panel card">
        <div class="section-head">
          <div>
            <h2>Workspace Projects</h2>
            <p class="copy">Discovered from workspace results manifests.</p>
          </div>
        </div>
        <div class="project-list" id="projectList"></div>
      </section>
    </aside>

    <main class="main">
      <section class="hero">
        <section class="panel hero-main">
          <div>
            <div class="eyebrow">Local Research Surface</div>
            <h1>Local Experiment Dashboard</h1>
            <p class="copy">
              Project-scoped local dashboard over MLflow, offline W&amp;B, workspace run folders, artifacts, tradeoffs, and shortlist review.
            </p>
          </div>
          <div class="chip-row" id="sourceTabs"></div>
        </section>
        <section class="panel hero-side">
          <div class="section-head">
            <div>
              <h2 id="projectTitle">Loading project...</h2>
              <p class="copy" id="projectSubtitle">Preparing current project view.</p>
            </div>
          </div>
          <div class="stats">
            <div class="stat"><div class="label">Visible Runs</div><div class="value" id="statRuns">-</div></div>
            <div class="stat"><div class="label">Loaded Sources</div><div class="value" id="statSources">-</div></div>
            <div class="stat"><div class="label">Best Metric</div><div class="value" id="statTopMetric">-</div></div>
            <div class="stat"><div class="label">Missing Metric</div><div class="value" id="statMissingMetric">-</div></div>
          </div>
          <div class="status-row" id="statusBadges"></div>
        </section>
      </section>

      <section class="panel card">
        <div class="section-head">
          <div>
            <h2>Research Filters</h2>
            <p class="copy">Operate inside the selected project only. Use an explicit metric direction and grouping key.</p>
          </div>
        </div>
        <div class="controls">
          <input id="runSearch" placeholder="Search run name, id, group, params, or tags">
          <input id="metricInput" placeholder="Metric key">
          <select id="metricSelect"></select>
          <select id="directionSelect">
            <option value="max">max</option>
            <option value="min">min</option>
          </select>
          <input id="variantInput" placeholder="Variant keys, comma separated">
          <select id="statusSelect"></select>
          <button id="refreshButton">Reload Workspace</button>
        </div>
        <div class="toolbar">
          <div class="chip-row" id="metricChips"></div>
          <div class="chip-row" id="quickVariantRow"></div>
        </div>
      </section>

      <div class="layout">
        <div class="stack">
          <section class="panel card">
            <div class="section-head">
              <div>
                <h2>Variant Compare</h2>
                <p class="copy">Grouped comparison for the current project and filtered slice.</p>
              </div>
              <div class="toolbar">
                <button class="secondary" id="exportCompareButton">Export Compare</button>
                <button class="secondary" id="clearGroupButton">Clear Cohort</button>
              </div>
            </div>
            <div class="winner" id="compareWinner">Loading grouped comparison...</div>
            <div class="compare-list" id="compareList"></div>
          </section>

          <section class="panel card">
            <div class="section-head">
              <div>
                <h2>Tradeoff View</h2>
                <p class="copy">Scatter the active metric against a second metric inside the current project slice.</p>
              </div>
              <select id="secondaryMetricSelect" style="max-width:260px;"></select>
            </div>
            <div class="viz-shell">
              <div class="toolbar" style="margin-bottom:10px;">
                <div class="tiny">X: active metric · Y: secondary metric</div>
                <div class="tiny" id="tradeoffMeta">Loading tradeoff view...</div>
              </div>
              <div id="tradeoffShell"></div>
            </div>
          </section>

          <section class="panel card">
            <div class="section-head">
              <div>
                <h2>Runs</h2>
                <p class="copy">Ranked inside the selected project. Pin candidates and open a run for inspection.</p>
              </div>
              <button class="secondary" id="exportRunsButton">Export Runs</button>
            </div>
            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Run</th>
                    <th>Source / Status</th>
                    <th>Active Metric</th>
                    <th>Workspace Context</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody id="runsTableBody"></tbody>
              </table>
            </div>
            <div id="runsEmpty" class="empty" style="display:none;">No runs match the current filters.</div>
          </section>
        </div>

        <div class="stack">
          <section class="panel card">
            <div class="section-head">
              <div>
                <h2>Source Health</h2>
                <p class="copy">Backend coverage, warnings, and status mix for the selected project.</p>
              </div>
            </div>
            <div class="health-list" id="healthList"></div>
          </section>

          <section class="panel card">
            <div class="section-head">
              <div>
                <h2>Shortlist Compare</h2>
                <p class="copy">Pinned runs side by side with differing params only.</p>
              </div>
            </div>
            <div class="short-grid" id="shortlistGrid"></div>
            <div class="summary-shell" id="shortlistDiff">Pin up to three runs to compare differing params.</div>
          </section>

          <section class="panel card">
            <div class="section-head">
              <div>
                <h2>Run Inspector</h2>
                <p class="copy">Selected run detail, artifacts, params, tags, and local path context.</p>
              </div>
            </div>
            <div id="selectedRunShell"><div class="empty">Select a run from the table.</div></div>
          </section>

          <section class="panel card">
            <div class="section-head">
              <div>
                <h2>Summary Debug</h2>
                <p class="copy">Compact project summary payload for sanity checks.</p>
              </div>
            </div>
            <div class="summary-shell" id="summaryShell">Loading...</div>
          </section>
        </div>
      </div>
    </main>
  </div>
  <script>
    let workspaceData = null;
    let projectCache = {};
    let currentProject = null;
    let selectedSource = 'all';
    let selectedRunId = null;
    let activeTab = 'metrics';
    let activeGroupRunIds = null;
    let pinnedRunIds = [];
    let activeArtifactPath = null;

    async function getJson(url, options) {
      const response = await fetch(url, options);
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || ('HTTP ' + response.status));
      }
      return await response.json();
    }

    function escapeHtml(value) {
      return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
    }

    function formatMetric(value) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return '-';
      return Number(value).toFixed(3);
    }

    function formatTimestamp(value) {
      if (!value) return '-';
      const millis = Number(value) < 10_000_000_000 ? Number(value) * 1000 : Number(value);
      return new Date(millis).toLocaleString();
    }

    function downloadJson(filename, payload) {
      const blob = new Blob([JSON.stringify(payload, null, 2)], {type: 'application/json'});
      const href = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = href;
      anchor.download = filename;
      anchor.click();
      URL.revokeObjectURL(href);
    }

    function currentSummary() {
      return projectCache[currentProject] ? projectCache[currentProject].summary : null;
    }

    function currentRuns() {
      const payload = projectCache[currentProject];
      return payload ? payload.runs.runs : [];
    }

    function activeMetric() {
      return document.getElementById('metricInput').value.trim() || 'avg_reward';
    }

    function activeDirection() {
      return document.getElementById('directionSelect').value || 'max';
    }

    function activeVariantKeys() {
      const raw = document.getElementById('variantInput').value.trim();
      if (!raw) return [];
      return raw.split(',').map(item => item.trim()).filter(Boolean);
    }

    function activeSearch() {
      return document.getElementById('runSearch').value.trim().toLowerCase();
    }

    function activeStatus() {
      return document.getElementById('statusSelect').value || 'all';
    }

    function activeSecondaryMetric() {
      return document.getElementById('secondaryMetricSelect').value || '';
    }

    function selectedProjectMeta() {
      return ((workspaceData && workspaceData.projects) || []).find(project => project.name === currentProject) || null;
    }

    async function loadWorkspace(forceProjectReload=false) {
      workspaceData = await getJson('/api/workspace');
      renderWorkspaceMeta();
      renderProjectRail();
      const defaultProject = currentProject && (workspaceData.projects || []).some(project => project.name === currentProject)
        ? currentProject
        : workspaceData.default_project || (workspaceData.projects && workspaceData.projects[0] && workspaceData.projects[0].name);
      if (defaultProject) {
        await selectProject(defaultProject, forceProjectReload);
      }
    }

    async function selectProject(projectName, force=false) {
      currentProject = projectName;
      selectedSource = 'all';
      activeGroupRunIds = null;
      activeArtifactPath = null;
      if (!projectCache[projectName] || force) {
        const [summary, runs] = await Promise.all([
          getJson('/api/summary?project=' + encodeURIComponent(projectName)),
          getJson('/api/runs?project=' + encodeURIComponent(projectName)),
        ]);
        projectCache[projectName] = {summary, runs};
      }
      const summary = currentSummary();
      const metrics = summary.available_metrics || [];
      if (!document.getElementById('metricInput').value && metrics.length) {
        document.getElementById('metricInput').value = metrics[0];
      }
      if (!document.getElementById('variantInput').value && summary.available_variant_keys && summary.available_variant_keys.length) {
        document.getElementById('variantInput').value = summary.available_variant_keys[0];
      }
      selectedRunId = currentRuns()[0] ? currentRuns()[0].run_id : null;
      renderProjectRail();
      await renderAll();
    }

    function renderWorkspaceMeta() {
      const root = document.getElementById('workspaceMeta');
      if (!workspaceData) {
        root.textContent = 'Loading workspace...';
        return;
      }
      root.textContent = JSON.stringify({
        mode: workspaceData.mode,
        results_root: workspaceData.results_root,
        project_count: (workspaceData.projects || []).length,
        warnings: workspaceData.warnings || [],
      }, null, 2);
    }

    function renderProjectRail() {
      const root = document.getElementById('projectList');
      root.innerHTML = '';
      const projects = (workspaceData && workspaceData.projects) || [];
      if (!projects.length) {
        root.innerHTML = '<div class="empty">No projects discovered yet. Point the dashboard at a workspace results root with project manifests.</div>';
        return;
      }
      for (const project of projects) {
        const shell = document.createElement('div');
        shell.className = 'project-card' + (project.name === currentProject ? ' active' : '');
        const warnings = (project.warnings || []).length ? `<div class="badge warn" style="display:inline-flex;margin-top:8px;">${project.warnings.length} warning(s)</div>` : '';
        shell.innerHTML = `
          <button class="project-button" type="button">
            <div class="project-name">${escapeHtml(project.name)}</div>
            <div class="tiny">${escapeHtml(project.repo_root || project.project_results_dir || 'no repo root')}</div>
            <div class="tiny" style="margin-top:6px;">${project.run_count} run(s) · ${(project.sources || []).join(', ') || 'no sources'}</div>
            ${warnings}
          </button>
        `;
        shell.querySelector('button').onclick = async () => {
          await selectProject(project.name);
        };
        root.appendChild(shell);
      }
    }

    function sourceFilteredRuns() {
      let runs = currentRuns().slice();
      if (selectedSource !== 'all') {
        runs = runs.filter(run => run.source === selectedSource);
      }
      const status = activeStatus();
      if (status !== 'all') {
        runs = runs.filter(run => String(run.status || 'unknown').toLowerCase() === status);
      }
      if (activeGroupRunIds) {
        const allowed = new Set(activeGroupRunIds);
        runs = runs.filter(run => allowed.has(run.run_id));
      }
      const search = activeSearch();
      if (!search) return runs;
      return runs.filter(run => {
        const haystack = JSON.stringify({
          name: run.name,
          run_id: run.run_id,
          group: run.group,
          project: run.project,
          experiment: run.experiment,
          params: run.params,
          tags: run.tags,
        }).toLowerCase();
        return haystack.includes(search);
      });
    }

    function rankedRuns(runs) {
      const metric = activeMetric();
      const direction = activeDirection();
      return runs.slice().sort((left, right) => {
        const leftValue = left.metrics && left.metrics[metric] !== undefined ? Number(left.metrics[metric]) : null;
        const rightValue = right.metrics && right.metrics[metric] !== undefined ? Number(right.metrics[metric]) : null;
        if (leftValue === null && rightValue === null) return 0;
        if (leftValue === null) return 1;
        if (rightValue === null) return -1;
        return direction === 'max' ? rightValue - leftValue : leftValue - rightValue;
      });
    }

    function topRun(runs) {
      return rankedRuns(runs)[0] || null;
    }

    function renderProjectHeader() {
      const summary = currentSummary();
      const meta = selectedProjectMeta();
      document.getElementById('projectTitle').textContent = currentProject || 'No project selected';
      document.getElementById('projectSubtitle').textContent = meta
        ? ((meta.repo_root || meta.project_results_dir || '') + ' · ' + ((meta.sources || []).join(', ') || 'no sources'))
        : 'Preparing current project view.';
      document.getElementById('summaryShell').textContent = summary ? JSON.stringify(summary, null, 2) : 'No project data loaded.';
    }

    function renderSourceTabs() {
      const root = document.getElementById('sourceTabs');
      root.innerHTML = '';
      const summary = currentSummary();
      const values = ['all', ...((summary && summary.sources) || [])];
      for (const source of values) {
        const button = document.createElement('button');
        button.className = 'source-pill' + (selectedSource === source ? ' active' : '');
        button.textContent = source === 'all' ? 'all sources' : source;
        button.onclick = async () => {
          selectedSource = source;
          activeGroupRunIds = null;
          await renderAll();
        };
        root.appendChild(button);
      }
    }

    function renderMetricControls() {
      const summary = currentSummary();
      const metrics = (summary && summary.available_metrics) || [];
      const select = document.getElementById('metricSelect');
      const current = activeMetric();
      select.innerHTML = '';
      for (const metric of metrics) {
        const option = document.createElement('option');
        option.value = metric;
        option.textContent = metric;
        if (metric === current) option.selected = true;
        select.appendChild(option);
      }
      if (current && !metrics.includes(current)) {
        const option = document.createElement('option');
        option.value = current;
        option.textContent = current + ' (custom)';
        option.selected = true;
        select.appendChild(option);
      }
      const chips = document.getElementById('metricChips');
      chips.innerHTML = '';
      for (const metric of metrics.slice(0, 10)) {
        const chip = document.createElement('div');
        chip.className = 'chip' + (metric === current ? ' active' : '');
        chip.textContent = metric;
        chip.onclick = async () => {
          document.getElementById('metricInput').value = metric;
          select.value = metric;
          await renderAll();
        };
        chips.appendChild(chip);
      }
    }

    function renderVariantChips() {
      const summary = currentSummary();
      const root = document.getElementById('quickVariantRow');
      root.innerHTML = '';
      const current = activeVariantKeys();
      for (const key of ((summary && summary.available_variant_keys) || []).slice(0, 12)) {
        const chip = document.createElement('div');
        chip.className = 'chip' + (current.length === 1 && current[0] === key ? ' active' : '');
        chip.textContent = key;
        chip.onclick = async () => {
          document.getElementById('variantInput').value = key;
          await renderAll();
        };
        root.appendChild(chip);
      }
    }

    function renderStatusControl() {
      const summary = currentSummary();
      const select = document.getElementById('statusSelect');
      const current = activeStatus();
      const options = ['all', ...Object.keys((summary && summary.status_counts) || {})];
      select.innerHTML = '';
      for (const value of options) {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = value === 'all' ? 'all statuses' : value;
        if (value === current) option.selected = true;
        select.appendChild(option);
      }
    }

    function renderSecondaryMetricControl() {
      const summary = currentSummary();
      const select = document.getElementById('secondaryMetricSelect');
      const metrics = ((summary && summary.available_metrics) || []).filter(metric => metric !== activeMetric());
      const preferred = metrics[0] || '';
      select.innerHTML = '';
      for (const metric of metrics) {
        const option = document.createElement('option');
        option.value = metric;
        option.textContent = metric;
        if (metric === preferred) option.selected = true;
        select.appendChild(option);
      }
    }

    function updateStats(runs) {
      const summary = currentSummary();
      const metric = activeMetric();
      const best = topRun(runs);
      const missingMetric = runs.filter(run => !run.metrics || run.metrics[metric] === undefined).length;
      document.getElementById('statRuns').textContent = runs.length;
      document.getElementById('statSources').textContent = selectedSource === 'all' ? (((summary && summary.sources) || []).length) : 1;
      document.getElementById('statTopMetric').textContent = best ? formatMetric(best.metrics[metric]) : '-';
      document.getElementById('statMissingMetric').textContent = String(missingMetric);
      const badges = document.getElementById('statusBadges');
      badges.innerHTML = '';
      const items = [
        currentProject ? {label: 'project: ' + currentProject, kind: 'good'} : null,
        {label: 'view: ' + (selectedSource === 'all' ? 'all sources' : selectedSource), kind: 'info'},
        {label: 'metric: ' + metric + ' (' + activeDirection() + ')', kind: 'info'},
        activeVariantKeys().length ? {label: 'group by: ' + activeVariantKeys().join(', '), kind: 'info'} : null,
        activeGroupRunIds ? {label: 'cohort: ' + activeGroupRunIds.length + ' run(s)', kind: 'good'} : null,
        missingMetric ? {label: 'missing metric: ' + missingMetric, kind: 'warn'} : null,
      ].filter(Boolean);
      for (const item of items) {
        const badge = document.createElement('div');
        badge.className = 'badge ' + item.kind;
        badge.textContent = item.label;
        badges.appendChild(badge);
      }
    }

    function renderHealth() {
      const summary = currentSummary();
      const root = document.getElementById('healthList');
      root.innerHTML = '';
      for (const detail of ((summary && summary.source_details) || [])) {
        const shell = document.createElement('div');
        shell.className = 'health-item';
        const statusBits = Object.entries(detail.status_counts || {}).map(([key, value]) => key + ': ' + value).join(' · ');
        shell.innerHTML = `
          <strong>${escapeHtml(detail.source)}</strong>
          <div class="tiny">${detail.run_count} run(s)</div>
          <div class="tiny">${escapeHtml(statusBits || 'no runs loaded')}</div>
          ${detail.warning ? `<div class="badge error" style="display:inline-flex;margin-top:8px;">${escapeHtml(detail.warning)}</div>` : `<div class="badge good" style="display:inline-flex;margin-top:8px;">loaded</div>`}
        `;
        root.appendChild(shell);
      }
      for (const warning of ((summary && summary.warnings) || [])) {
        const shell = document.createElement('div');
        shell.className = 'health-item';
        shell.innerHTML = `<strong>warning</strong><div class="tiny">${escapeHtml(warning)}</div>`;
        root.appendChild(shell);
      }
    }

    async function renderCompare() {
      const url = new URL('/api/compare', window.location.origin);
      url.searchParams.set('project', currentProject);
      url.searchParams.set('metric', activeMetric());
      url.searchParams.set('direction', activeDirection());
      for (const key of activeVariantKeys()) url.searchParams.append('variant_key', key);
      if (selectedSource !== 'all') url.searchParams.set('source', selectedSource);
      if (activeSearch()) url.searchParams.set('search', activeSearch());
      if (activeGroupRunIds) {
        for (const runId of activeGroupRunIds) url.searchParams.append('run_id', runId);
      }
      const payload = await getJson(url.toString());
      const winner = document.getElementById('compareWinner');
      const root = document.getElementById('compareList');
      root.innerHTML = '';
      if (!payload.rows.length) {
        winner.innerHTML = '<strong>No grouped compare yet</strong><div class="tiny">Choose a populated metric and at least one useful grouping key.</div>';
        return;
      }
      const best = payload.rows[0];
      winner.innerHTML = `<strong>${escapeHtml(best.label)}</strong><div class="tiny">${best.count} run(s) · mean ${formatMetric(best.mean)} · best ${formatMetric(best.best)}</div>`;
      const maxAbsBest = Math.max(...payload.rows.map(row => Math.abs(Number(row.best || 0))), 1e-9);
      for (const row of payload.rows) {
        const shell = document.createElement('div');
        shell.className = 'compare-row';
        const width = Math.max(6, Math.min(100, Math.abs(Number(row.best || 0)) / maxAbsBest * 100));
        shell.innerHTML = `
          <div class="variant-top">
            <strong>${escapeHtml(row.label)}</strong>
            <div class="metric-value">${formatMetric(row.best)}</div>
          </div>
          <div class="bar-shell"><div class="bar-fill" style="width:${width}%"></div></div>
          <div class="tiny">${row.count} run(s) · mean ${formatMetric(row.mean)} · std ${formatMetric(row.stddev)}</div>
          <div class="inline-actions"><button class="secondary" type="button">Focus Cohort</button></div>
        `;
        shell.querySelector('button').onclick = async () => {
          activeGroupRunIds = row.runs.map(run => run.run_id);
          await renderAll();
        };
        root.appendChild(shell);
      }
    }

    function renderTradeoff() {
      const root = document.getElementById('tradeoffShell');
      const meta = document.getElementById('tradeoffMeta');
      const xMetric = activeMetric();
      const yMetric = activeSecondaryMetric();
      const runs = sourceFilteredRuns().filter(run => (
        run.metrics && run.metrics[xMetric] !== undefined && run.metrics[yMetric] !== undefined
      ));
      if (!xMetric || !yMetric || !runs.length) {
        meta.textContent = 'Need two populated metrics in the filtered slice.';
        root.innerHTML = '<div class="empty">No runs have both metrics for the current slice.</div>';
        return;
      }
      const xValues = runs.map(run => Number(run.metrics[xMetric]));
      const yValues = runs.map(run => Number(run.metrics[yMetric]));
      const minX = Math.min(...xValues);
      const maxX = Math.max(...xValues);
      const minY = Math.min(...yValues);
      const maxY = Math.max(...yValues);
      const width = 760;
      const height = 320;
      const pad = 38;
      const xSpan = Math.max(maxX - minX, 1e-9);
      const ySpan = Math.max(maxY - minY, 1e-9);
      const dots = runs.map(run => {
        const x = pad + ((Number(run.metrics[xMetric]) - minX) / xSpan) * (width - pad * 2);
        const y = height - pad - ((Number(run.metrics[yMetric]) - minY) / ySpan) * (height - pad * 2);
        return `<g><circle cx="${x}" cy="${y}" r="6" fill="#b84c17" opacity="0.82"></circle><text x="${x + 8}" y="${y - 8}" font-size="11" fill="#6d6257">${escapeHtml(run.name || run.run_id)}</text></g>`;
      }).join('');
      meta.textContent = runs.length + ' run(s) · X ' + xMetric + ' · Y ' + yMetric;
      root.innerHTML = `
        <svg class="viz-svg" viewBox="0 0 ${width} ${height}">
          <line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" stroke="#ddcfbc" />
          <line x1="${pad}" y1="${pad}" x2="${pad}" y2="${height - pad}" stroke="#ddcfbc" />
          <text x="${width / 2}" y="${height - 8}" text-anchor="middle" font-size="12" fill="#6d6257">${escapeHtml(xMetric)}</text>
          <text x="12" y="${height / 2}" transform="rotate(-90 12 ${height / 2})" text-anchor="middle" font-size="12" fill="#6d6257">${escapeHtml(yMetric)}</text>
          ${dots}
        </svg>
      `;
    }

    function renderRuns() {
      const runs = rankedRuns(sourceFilteredRuns());
      const body = document.getElementById('runsTableBody');
      body.innerHTML = '';
      document.getElementById('runsEmpty').style.display = runs.length ? 'none' : 'block';
      for (const run of runs) {
        const pinned = pinnedRunIds.includes(run.run_id);
        const metric = activeMetric();
        const workspaceRunId = (run.tags && (run.tags['workspace.run_id'] || run.tags.workspace_run_id)) || run.name || run.run_id;
        const row = document.createElement('tr');
        row.innerHTML = `
          <td>
            <div class="run-name">${escapeHtml(run.name || run.run_id)}</div>
            <div class="tiny">${escapeHtml(workspaceRunId)}</div>
          </td>
          <td>
            <div>${escapeHtml(run.source || '-')}</div>
            <div class="tiny">${escapeHtml(String(run.status || 'unknown'))}</div>
          </td>
          <td><div class="metric-value">${formatMetric(run.metrics && run.metrics[metric])}</div></td>
          <td>
            <div class="tiny">${escapeHtml(run.project || run.experiment || '-')}</div>
            <div class="tiny">${escapeHtml((run.group || '-') + ' · ' + (run.path || '-'))}</div>
          </td>
          <td>
            <div class="inline-actions">
              <button class="secondary" type="button" data-action="inspect">Inspect</button>
              <button class="secondary" type="button" data-action="pin">${pinned ? 'Unpin' : 'Pin'}</button>
            </div>
          </td>
        `;
        row.querySelector('[data-action="inspect"]').onclick = async () => {
          selectedRunId = run.run_id;
          activeArtifactPath = null;
          await renderInspector();
        };
        row.querySelector('[data-action="pin"]').onclick = () => {
          if (pinned) {
            pinnedRunIds = pinnedRunIds.filter(item => item !== run.run_id);
          } else if (pinnedRunIds.length < 3) {
            pinnedRunIds = [...pinnedRunIds, run.run_id];
          }
          renderShortlist();
          renderRuns();
        };
        body.appendChild(row);
      }
    }

    function renderShortlist() {
      const root = document.getElementById('shortlistGrid');
      const diffRoot = document.getElementById('shortlistDiff');
      root.innerHTML = '';
      const runs = currentRuns().filter(run => pinnedRunIds.includes(run.run_id));
      if (!runs.length) {
        root.innerHTML = '<div class="empty">No pinned runs yet.</div>';
        diffRoot.textContent = 'Pin up to three runs to compare differing params.';
        return;
      }
      for (const run of runs) {
        const shell = document.createElement('div');
        shell.className = 'short-card';
        shell.innerHTML = `
          <div class="run-name">${escapeHtml(run.name || run.run_id)}</div>
          <div class="tiny">${escapeHtml(run.run_id)}</div>
          <div class="tiny" style="margin-top:8px;">${escapeHtml(activeMetric())}: ${formatMetric(run.metrics && run.metrics[activeMetric()])}</div>
        `;
        root.appendChild(shell);
      }
      const differing = {};
      const keys = new Set();
      runs.forEach(run => Object.keys(run.params || {}).forEach(key => keys.add(key)));
      for (const key of keys) {
        const values = runs.map(run => JSON.stringify((run.params || {})[key]));
        if (new Set(values).size > 1) {
          differing[key] = runs.map(run => ({run_id: run.run_id, value: (run.params || {})[key]}));
        }
      }
      diffRoot.textContent = JSON.stringify(differing, null, 2);
    }

    async function renderInspector() {
      const root = document.getElementById('selectedRunShell');
      const run = currentRuns().find(item => item.run_id === selectedRunId);
      if (!run) {
        root.innerHTML = '<div class="empty">Select a run from the table.</div>';
        return;
      }
      const artifacts = await getJson('/api/artifacts?project=' + encodeURIComponent(currentProject) + '&run_id=' + encodeURIComponent(run.run_id));
      let previewHtml = '<div class="empty">Choose an artifact preview.</div>';
      if (activeArtifactPath) {
        const preview = await getJson('/api/artifact-preview?project=' + encodeURIComponent(currentProject) + '&run_id=' + encodeURIComponent(run.run_id) + '&path=' + encodeURIComponent(activeArtifactPath));
        if (preview.text) {
          previewHtml = `<div class="preview-shell">${escapeHtml(preview.text)}</div>`;
        } else if (preview.image_path) {
          previewHtml = `<img class="preview-image" src="/artifact-file?project=${encodeURIComponent(currentProject)}&run_id=${encodeURIComponent(run.run_id)}&path=${encodeURIComponent(preview.image_path)}" alt="artifact preview">`;
        } else if (preview.message) {
          previewHtml = `<div class="preview-shell">${escapeHtml(preview.message)}</div>`;
        }
      }
      root.innerHTML = `
        <div class="detail-hero">
          <strong>${escapeHtml(run.name || run.run_id)}</strong>
          <div class="tiny">${escapeHtml(run.run_id)} · ${escapeHtml(run.source)} · ${escapeHtml(String(run.status || 'unknown'))}</div>
          <div class="detail-grid">
            <div class="stat"><div class="label">Workspace Run</div><div class="value" style="font-size:16px;">${escapeHtml((run.tags && (run.tags['workspace.run_id'] || run.tags.workspace_run_id)) || run.run_id)}</div></div>
            <div class="stat"><div class="label">Project</div><div class="value" style="font-size:16px;">${escapeHtml(run.project || run.experiment || '-')}</div></div>
            <div class="stat"><div class="label">Started</div><div class="value" style="font-size:16px;">${escapeHtml(formatTimestamp(run.start_time))}</div></div>
            <div class="stat"><div class="label">Artifacts</div><div class="value" style="font-size:16px;">${artifacts.artifacts.length}</div></div>
          </div>
        </div>
        <div class="detail-tabs">
          <div class="tab ${activeTab === 'metrics' ? 'active' : ''}" data-tab="metrics">metrics</div>
          <div class="tab ${activeTab === 'params' ? 'active' : ''}" data-tab="params">params</div>
          <div class="tab ${activeTab === 'tags' ? 'active' : ''}" data-tab="tags">tags</div>
          <div class="tab ${activeTab === 'artifacts' ? 'active' : ''}" data-tab="artifacts">artifacts</div>
        </div>
        <div id="detailBody"></div>
      `;
      root.querySelectorAll('.tab').forEach(tab => {
        tab.onclick = async () => {
          activeTab = tab.dataset.tab;
          await renderInspector();
        };
      });
      const body = root.querySelector('#detailBody');
      if (activeTab === 'metrics') {
        body.innerHTML = `<div class="kv-table">${Object.entries(run.metrics || {}).map(([key, value]) => `<div class="kv-row"><div>${escapeHtml(key)}</div><div>${escapeHtml(formatMetric(value))}</div></div>`).join('')}</div>`;
      } else if (activeTab === 'params') {
        body.innerHTML = `<div class="kv-table">${Object.entries(run.params || {}).map(([key, value]) => `<div class="kv-row"><div>${escapeHtml(key)}</div><div>${escapeHtml(JSON.stringify(value))}</div></div>`).join('')}</div>`;
      } else if (activeTab === 'tags') {
        body.innerHTML = `<div class="kv-table">${Object.entries(run.tags || {}).map(([key, value]) => `<div class="kv-row"><div>${escapeHtml(key)}</div><div>${escapeHtml(JSON.stringify(value))}</div></div>`).join('')}</div>`;
      } else {
        body.innerHTML = `
          <div class="artifact-list">
            ${(artifacts.artifacts || []).map(artifact => `
              <div class="artifact-item">
                <div><strong>${escapeHtml(artifact.path)}</strong></div>
                <div class="tiny">${escapeHtml(artifact.kind)} · ${artifact.size_bytes} bytes</div>
                <div class="artifact-actions">
                  <button class="secondary" type="button" data-path="${escapeHtml(artifact.path)}">Preview</button>
                  <a href="/artifact-file?project=${encodeURIComponent(currentProject)}&run_id=${encodeURIComponent(run.run_id)}&path=${encodeURIComponent(artifact.path)}" target="_blank" rel="noreferrer">open</a>
                </div>
              </div>
            `).join('') || '<div class="empty">No artifacts found for this run.</div>'}
          </div>
          <div style="margin-top:12px;">${previewHtml}</div>
        `;
        body.querySelectorAll('button[data-path]').forEach(button => {
          button.onclick = async () => {
            activeArtifactPath = button.dataset.path;
            await renderInspector();
          };
        });
      }
    }

    async function renderAll() {
      renderProjectHeader();
      renderSourceTabs();
      renderMetricControls();
      renderVariantChips();
      renderStatusControl();
      renderSecondaryMetricControl();
      const runs = sourceFilteredRuns();
      updateStats(runs);
      renderHealth();
      await renderCompare();
      renderTradeoff();
      renderRuns();
      renderShortlist();
      await renderInspector();
    }

    function bindControls() {
      document.getElementById('metricSelect').addEventListener('change', async event => {
        document.getElementById('metricInput').value = event.target.value;
        await renderAll();
      });
      document.getElementById('secondaryMetricSelect').addEventListener('change', renderTradeoff);
      document.getElementById('directionSelect').addEventListener('change', renderAll);
      document.getElementById('variantInput').addEventListener('change', renderAll);
      document.getElementById('statusSelect').addEventListener('change', renderAll);
      document.getElementById('metricInput').addEventListener('change', renderAll);
      document.getElementById('runSearch').addEventListener('input', renderAll);
      document.getElementById('refreshButton').addEventListener('click', async () => {
        await getJson('/api/refresh', {method: 'POST'});
        projectCache = {};
        await loadWorkspace(true);
      });
      document.getElementById('clearGroupButton').addEventListener('click', async () => {
        activeGroupRunIds = null;
        await renderAll();
      });
      document.getElementById('exportRunsButton').addEventListener('click', () => {
        downloadJson((currentProject || 'project') + '-runs.json', rankedRuns(sourceFilteredRuns()));
      });
      document.getElementById('exportCompareButton').addEventListener('click', async () => {
        const url = new URL('/api/compare', window.location.origin);
        url.searchParams.set('project', currentProject);
        url.searchParams.set('metric', activeMetric());
        url.searchParams.set('direction', activeDirection());
        for (const key of activeVariantKeys()) url.searchParams.append('variant_key', key);
        downloadJson((currentProject || 'project') + '-compare.json', await getJson(url.toString()));
      });
    }

    async function init() {
      bindControls();
      await loadWorkspace();
    }

    init().catch(error => {
      document.body.innerHTML = '<pre style="padding:24px;color:#993535;">' + escapeHtml(String(error)) + '</pre>';
    });
  </script>
</body>
</html>
"""
