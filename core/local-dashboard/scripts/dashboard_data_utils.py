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
    load_wandb_runs_normalized,
    run_to_dict,
    varying_param_values,
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
    mlflow_uri: str | None,
    mlflow_experiment_name: str | None,
    mlflow_experiment_id: str | None,
    wandb_paths: list[str] | None,
    wandb_project: str | None,
    wandb_group: str | None,
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
        except Exception as exc:  # pragma: no cover - exercised in CLI usage
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
        except Exception as exc:  # pragma: no cover - exercised in CLI usage
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

    runs.sort(key=lambda run: ((run.start_time or 0), run.run_id), reverse=True)
    return {
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
        "sources": state["sources"],
        "source_details": state["source_details"],
        "warnings": state["warnings"],
        "run_count": state["run_count"],
        "status_counts": state["status_counts"],
        "available_metrics": state["available_metrics"],
        "available_variant_keys": state["available_variant_keys"],
        "timestamps": state["timestamps"],
        "runs": [run_to_dict(run) for run in state["runs"]],
    }


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
    return grouped_payload(group_runs(runs, variant_keys), metric, direction=direction)


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
            artifacts.append(
                {
                    "path": str(path.relative_to(root)),
                    "kind": _artifact_kind(path),
                    "size_bytes": stat.st_size,
                    "modified_time": stat.st_mtime,
                    "previewable": _artifact_kind(path) in {"image", "text"},
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

    root = _safe_artifact_path(run.artifact_root)
    target = _safe_artifact_path(run.artifact_root, relative_path)
    if root is None or target is None or not target.is_file():
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
        raw = target.read_text(encoding="utf-8", errors="replace")
        if target.suffix.lower() == ".json":
            try:
                raw = json.dumps(json.loads(raw), indent=2, sort_keys=True)
            except Exception:
                pass
        payload["text"] = raw[:MAX_TEXT_PREVIEW_BYTES]
        payload["truncated"] = len(raw.encode("utf-8")) > MAX_TEXT_PREVIEW_BYTES
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
      --bg: #f3ebdf;
      --paper: #fffdf8;
      --paper-2: #fff7ef;
      --ink: #181410;
      --muted: #6d6257;
      --line: #ddcfbc;
      --accent: #b84c17;
      --accent-2: #174c73;
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
        radial-gradient(circle at top left, rgba(255, 255, 255, 0.78), rgba(243, 235, 223, 0) 32%),
        linear-gradient(180deg, #f6efe4 0%, var(--bg) 100%);
    }
    .page {
      max-width: 1600px;
      margin: 0 auto;
      padding: 28px 22px 42px;
    }
    .hero, .layout {
      display: grid;
      gap: 18px;
    }
    .hero {
      grid-template-columns: 1.3fr 0.9fr;
      margin-bottom: 18px;
    }
    .layout {
      grid-template-columns: 1.45fr 0.95fr;
    }
    .stack { display: grid; gap: 18px; }
    .panel {
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }
    .card { padding: 18px; }
    .hero-main {
      padding: 22px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      min-height: 208px;
      background:
        linear-gradient(140deg, rgba(184, 76, 23, 0.11), rgba(255,255,255,0) 52%),
        linear-gradient(180deg, #fffdf8, #fff7ef);
    }
    .hero-side {
      padding: 18px;
      display: grid;
      gap: 12px;
      background:
        linear-gradient(160deg, rgba(23, 76, 115, 0.08), rgba(255,255,255,0) 46%),
        var(--paper);
    }
    .eyebrow {
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0.1em;
      font-size: 11px;
      margin-bottom: 10px;
    }
    h1, h2, h3, p { margin: 0; }
    h1 { font-size: 36px; line-height: 1.05; margin-bottom: 12px; }
    h2 { font-size: 20px; }
    .hero-copy, .section-copy {
      color: var(--muted);
      line-height: 1.55;
      font-size: 13px;
    }
    .section-head {
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 16px;
      margin-bottom: 14px;
    }
    .hero-foot, .toggle-row, .status-line, .detail-tabs {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .source-pill, .chip, .badge, .tab {
      border-radius: 999px;
      border: 1px solid var(--line);
      padding: 7px 11px;
      font-size: 12px;
      background: rgba(255,255,255,0.88);
      cursor: pointer;
    }
    .source-pill.active, .chip.active, .tab.active {
      background: var(--accent);
      color: white;
      border-color: var(--accent);
    }
    .badge.info { background: white; }
    .badge.warn { background: var(--warn-soft); border-color: #f1d39d; color: var(--warn); }
    .badge.error { background: var(--danger-soft); border-color: #efc6c6; color: var(--danger); }
    .badge.good { background: var(--good-soft); border-color: #cbe4d6; color: var(--good); }
    .stats {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .stat, .mini-stat, .short-card, .health-item, .variant-row, .artifact-item, .kv-row {
      border: 1px solid var(--line);
      border-radius: 14px;
      background: var(--paper-2);
    }
    .stat, .mini-stat, .short-card, .health-item { padding: 12px; }
    .stat .label, .mini-stat .label {
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 6px;
    }
    .stat .value { font-size: 28px; font-weight: 700; line-height: 1; }
    .mini-stat .value { font-size: 16px; font-weight: 700; }
    .controls {
      display: grid;
      grid-template-columns: 1.2fr 0.9fr 0.55fr 1.1fr auto auto;
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
    input, select {
      background: white;
      color: var(--ink);
    }
    button {
      background: var(--accent);
      border-color: var(--accent);
      color: white;
      cursor: pointer;
      font-weight: 700;
    }
    button.secondary {
      background: white;
      color: var(--accent);
      border-color: var(--line);
      font-weight: 600;
    }
    .toolbar {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      align-items: center;
    }
    .grid-2 {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    .health-list, .compare-list, .short-grid, .artifact-list, .kv-table {
      display: grid;
      gap: 10px;
    }
    .health-item strong, .short-card strong, .variant-label { font-size: 14px; }
    .tiny, .muted { color: var(--muted); font-size: 12px; line-height: 1.45; }
    .table-wrap { overflow: auto; }
    table {
      width: 100%;
      border-collapse: collapse;
    }
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
    .variant-top {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: baseline;
    }
    .variant-metric { color: var(--good); font-weight: 700; white-space: nowrap; }
    .variant-meta { color: var(--muted); font-size: 12px; display: grid; gap: 4px; }
    .winner {
      border: 1px solid #cbe4d6;
      background: var(--good-soft);
      border-radius: 14px;
      padding: 14px;
      margin-bottom: 12px;
    }
    .winner strong { display: block; font-size: 18px; margin-bottom: 4px; }
    .empty {
      color: var(--muted);
      padding: 12px 0;
      font-size: 13px;
    }
    .detail-hero {
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
      background: linear-gradient(140deg, rgba(23, 76, 115, 0.05), rgba(255,255,255,0));
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
    .kv-key { color: var(--muted); word-break: break-word; }
    .kv-value { word-break: break-word; }
    .artifact-item {
      padding: 10px 12px;
      font-size: 12px;
      display: grid;
      gap: 8px;
    }
    .artifact-row {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: start;
    }
    .artifact-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .preview-shell, .summary-shell {
      border: 1px solid var(--line);
      background: #fbf7ef;
      border-radius: 14px;
      padding: 12px;
      white-space: pre-wrap;
      font-size: 12px;
      max-height: 320px;
      overflow: auto;
    }
    .preview-image {
      max-width: 100%;
      border-radius: 12px;
      border: 1px solid var(--line);
      background: white;
    }
    .short-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
    .short-card .title {
      font-weight: 700;
      margin-bottom: 6px;
    }
    .compare-table {
      margin-top: 12px;
      border-top: 1px solid #efe4d5;
      padding-top: 10px;
    }
    @media (max-width: 1240px) {
      .hero, .layout { grid-template-columns: 1fr; }
    }
    @media (max-width: 980px) {
      .controls { grid-template-columns: 1fr 1fr; }
      .grid-2, .detail-grid, .short-grid { grid-template-columns: 1fr; }
    }
    @media (max-width: 640px) {
      .page { padding: 16px 12px 28px; }
      .controls { grid-template-columns: 1fr; }
      .stats { grid-template-columns: 1fr; }
      .kv-row { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="page">
    <section class="hero">
      <section class="panel hero-main">
        <div>
          <div class="eyebrow">Local Research Surface</div>
          <h1>Local Experiment Dashboard</h1>
          <p class="hero-copy">
            A local-first dashboard for MLflow and offline W&amp;B runs. Compare variants with explicit metric direction,
            shortlist candidate runs, inspect provenance, preview artifacts, and refresh the index without leaving the machine.
          </p>
        </div>
        <div class="hero-foot" id="sourceTabs"></div>
      </section>
      <section class="panel hero-side">
        <div class="section-head">
          <div>
            <h2>At A Glance</h2>
            <p class="section-copy">Current slice under the active filters and compare direction.</p>
          </div>
        </div>
        <div class="stats">
          <div class="stat"><div class="label">Visible Runs</div><div class="value" id="statRuns">-</div></div>
          <div class="stat"><div class="label">Loaded Sources</div><div class="value" id="statSources">-</div></div>
          <div class="stat"><div class="label">Best Metric</div><div class="value" id="statTopMetric">-</div></div>
          <div class="stat"><div class="label">Missing Metric</div><div class="value" id="statMissingMetric">-</div></div>
        </div>
        <div class="status-line" id="statusBadges"></div>
      </section>
    </section>

    <div class="layout">
      <div class="stack">
        <section class="panel card">
          <div class="section-head">
            <div>
              <h2>Research Filters</h2>
              <p class="section-copy">Use a real metric, explicit ranking direction, and one or more grouping keys.</p>
            </div>
          </div>
          <div class="controls">
            <input id="runSearch" placeholder="Search run name, id, group, project, params, or tags">
            <input id="metricInput" placeholder="Metric key">
            <select id="metricSelect"></select>
            <select id="directionSelect">
              <option value="max">max</option>
              <option value="min">min</option>
            </select>
            <input id="variantInput" placeholder="Variant keys, comma separated">
            <button id="refreshButton">Reload Data</button>
          </div>
          <div class="grid-2">
            <div>
              <div class="tiny" style="margin-bottom:8px;">Suggested Metrics</div>
              <div class="toggle-row" id="metricChips"></div>
            </div>
            <div>
              <div class="tiny" style="margin-bottom:8px;">Suggested Variant Keys</div>
              <div class="toggle-row" id="quickVariantRow"></div>
            </div>
          </div>
        </section>

        <section class="panel card">
          <div class="toolbar">
            <div>
              <h2>Variant Compare</h2>
              <p class="section-copy">Backend-driven grouped comparison with count, spread, and drilldown into cohort members.</p>
            </div>
            <div class="status-line">
              <button class="secondary" id="clearGroupButton">Clear Cohort Filter</button>
            </div>
          </div>
          <div class="winner" id="compareWinner">Loading grouped comparison...</div>
          <div class="compare-list" id="compareList"></div>
        </section>

        <section class="panel card">
          <div class="section-head">
            <div>
              <h2>Runs</h2>
              <p class="section-copy">Sorted by the active metric and direction. Pin up to three runs for side-by-side review.</p>
            </div>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Run</th>
                  <th>Source / Status</th>
                  <th>Active Metric</th>
                  <th>Context</th>
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
              <p class="section-copy">Loaded backends, run counts, warnings, and status coverage.</p>
            </div>
          </div>
          <div class="health-list" id="healthList"></div>
        </section>

        <section class="panel card">
          <div class="section-head">
            <div>
              <h2>Shortlist Compare</h2>
              <p class="section-copy">Pinned runs for side-by-side review of active metric, provenance, and differing params.</p>
            </div>
          </div>
          <div class="short-grid" id="shortlistGrid"></div>
          <div class="compare-table" id="shortlistDiff"></div>
        </section>

        <section class="panel card">
          <div class="section-head">
            <div>
              <h2>Run Inspector</h2>
              <p class="section-copy">Focused detail for the currently selected run.</p>
            </div>
          </div>
          <div id="selectedRunShell"><div class="empty">Select a run from the table.</div></div>
        </section>

        <section class="panel card">
          <div class="section-head">
            <div>
              <h2>Summary Debug</h2>
              <p class="section-copy">Compact backend snapshot for sanity checks and schema debugging.</p>
            </div>
          </div>
          <div class="summary-shell" id="summaryShell">Loading...</div>
        </section>
      </div>
    </div>
  </div>
  <script>
    let allRuns = [];
    let summaryData = null;
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
      return String(value)
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

    function formatCount(value) {
      if (value === null || value === undefined) return '-';
      return String(value);
    }

    function formatTimestamp(value) {
      if (!value) return '-';
      const millis = Number(value) < 10_000_000_000 ? Number(value) * 1000 : Number(value);
      return new Date(millis).toLocaleString();
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

    function sourceFilteredRuns() {
      let runs = allRuns.slice();
      if (selectedSource !== 'all') {
        runs = runs.filter(run => run.source === selectedSource);
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
          status: run.status,
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

    function updateStats(runs) {
      const metric = activeMetric();
      const best = topRun(runs);
      const missingMetric = runs.filter(run => !run.metrics || run.metrics[metric] === undefined).length;
      document.getElementById('statRuns').textContent = runs.length;
      document.getElementById('statSources').textContent = selectedSource === 'all'
        ? (summaryData.sources || []).length
        : 1;
      document.getElementById('statTopMetric').textContent = best ? formatMetric(best.metrics[metric]) : '-';
      document.getElementById('statMissingMetric').textContent = String(missingMetric);

      const badges = document.getElementById('statusBadges');
      badges.innerHTML = '';
      const items = [
        { label: 'view: ' + (selectedSource === 'all' ? 'all sources' : selectedSource), kind: 'info' },
        { label: 'metric: ' + metric + ' (' + activeDirection() + ')', kind: 'info' },
        { label: 'group by: ' + (activeVariantKeys().join(', ') || '<none>'), kind: 'info' },
        activeGroupRunIds ? { label: 'cohort filter: ' + activeGroupRunIds.length + ' run(s)', kind: 'good' } : null,
        activeSearch() ? { label: 'search active', kind: 'info' } : null,
        missingMetric ? { label: 'missing metric: ' + missingMetric, kind: 'warn' } : null,
      ].filter(Boolean);
      for (const item of items) {
        const badge = document.createElement('div');
        badge.className = 'badge ' + item.kind;
        badge.textContent = item.label;
        badges.appendChild(badge);
      }
    }

    function renderSourceTabs() {
      const root = document.getElementById('sourceTabs');
      root.innerHTML = '';
      const values = ['all', ...(summaryData.sources || [])];
      for (const source of values) {
        const button = document.createElement('button');
        button.className = 'source-pill' + (selectedSource === source ? ' active' : '');
        button.textContent = source === 'all' ? 'all sources' : source;
        button.onclick = async () => {
          selectedSource = source;
          activeGroupRunIds = null;
          renderSourceTabs();
          await renderAll();
        };
        root.appendChild(button);
      }
    }

    function renderMetricControls(runs) {
      const select = document.getElementById('metricSelect');
      const metrics = summaryData.available_metrics || [];
      const current = activeMetric();
      select.innerHTML = '';
      for (const metric of metrics) {
        const option = document.createElement('option');
        option.value = metric;
        option.textContent = metric;
        if (metric === current) option.selected = true;
        select.appendChild(option);
      }
      if (!metrics.includes(current) && current) {
        const option = document.createElement('option');
        option.value = current;
        option.textContent = current + ' (custom)';
        option.selected = true;
        select.appendChild(option);
      }
      document.getElementById('metricChips').innerHTML = '';
      for (const metric of metrics.slice(0, 10)) {
        const chip = document.createElement('div');
        chip.className = 'chip' + (metric === current ? ' active' : '');
        chip.textContent = metric;
        chip.onclick = async () => {
          document.getElementById('metricInput').value = metric;
          select.value = metric;
          await renderAll();
        };
        document.getElementById('metricChips').appendChild(chip);
      }
    }

    function renderVariantChips() {
      const root = document.getElementById('quickVariantRow');
      root.innerHTML = '';
      const current = activeVariantKeys();
      const keys = summaryData.available_variant_keys || [];
      for (const key of keys.slice(0, 14)) {
        const isActive = current.length === 1 && current[0] === key;
        const chip = document.createElement('div');
        chip.className = 'chip' + (isActive ? ' active' : '');
        chip.textContent = key;
        chip.onclick = async () => {
          document.getElementById('variantInput').value = key;
          await renderAll();
        };
        root.appendChild(chip);
      }
    }

    function renderHealth() {
      const root = document.getElementById('healthList');
      root.innerHTML = '';
      const details = summaryData.source_details || [];
      for (const detail of details) {
        const shell = document.createElement('div');
        shell.className = 'health-item';
        const statusBits = [];
        for (const [key, value] of Object.entries(detail.status_counts || {})) {
          statusBits.push(key + ': ' + value);
        }
        shell.innerHTML = `
          <strong>${escapeHtml(detail.source)}</strong>
          <div class="muted">${detail.run_count} run(s)</div>
          <div class="tiny">${escapeHtml(statusBits.join(' · ') || 'no runs loaded')}</div>
          ${detail.warning ? `<div class="badge error" style="margin-top:8px;display:inline-flex;">${escapeHtml(detail.warning)}</div>` : '<div class="badge good" style="margin-top:8px;display:inline-flex;">loaded</div>'}
        `;
        root.appendChild(shell);
      }
      if ((summaryData.warnings || []).length) {
        for (const warning of summaryData.warnings) {
          const shell = document.createElement('div');
          shell.className = 'health-item';
          shell.innerHTML = `<strong>warning</strong><div class="tiny">${escapeHtml(warning)}</div>`;
          root.appendChild(shell);
        }
      }
    }

    async function renderCompare() {
      const list = document.getElementById('compareList');
      const winner = document.getElementById('compareWinner');
      list.innerHTML = '';
      const metric = activeMetric();
      const direction = activeDirection();
      const variantKeys = activeVariantKeys();
      if (!variantKeys.length) {
        winner.textContent = 'Enter at least one variant key to render grouped comparison.';
        return;
      }
      const params = new URLSearchParams({ metric, direction });
      params.set('source', selectedSource);
      if (activeSearch()) params.set('search', activeSearch());
      for (const key of variantKeys) params.append('variant_key', key);
      const payload = await getJson('/api/compare?' + params.toString());
      const rows = payload.rows || [];
      if (!rows.length) {
        winner.textContent = 'No grouped comparison rows match the current filters.';
        return;
      }

      const top = rows[0];
      const missingMetric = top.count - (top.summary.count || 0);
      winner.innerHTML = `
        <strong>${escapeHtml(top.label)}</strong>
        <div class="muted">
          ${direction === 'max' ? 'Top' : 'Lowest'} grouped ${escapeHtml(metric)} mean ${formatMetric(top.summary.mean)}
          across ${top.count} run(s), stddev ${formatMetric(top.summary.stddev)}, missing metric in ${missingMetric} run(s).
        </div>
      `;

      const maxMagnitude = Math.max(...rows.map(row => Math.abs(Number(row.summary.mean || 0))), 1);
      for (const row of rows) {
        const shell = document.createElement('div');
        shell.className = 'variant-row';
        const width = row.summary.mean !== null ? Math.max(2, (Math.abs(Number(row.summary.mean)) / maxMagnitude) * 100) : 0;
        const missing = row.count - (row.summary.count || 0);
        shell.innerHTML = `
          <div class="variant-top">
            <div class="variant-label">${escapeHtml(row.label)}</div>
            <div class="variant-metric">${formatMetric(row.summary.mean)}</div>
          </div>
          <div class="bar-shell"><div class="bar-fill" style="width:${width}%"></div></div>
          <div class="variant-meta">
            <div>${row.count} run(s) · metric count ${row.summary.count} · stddev ${formatMetric(row.summary.stddev)}</div>
            <div>best ${escapeHtml(row.best_run_name || row.best_run_id || '-')} · min ${formatMetric(row.summary.min)} · max ${formatMetric(row.summary.max)}${missing ? ' · missing metric ' + missing : ''}</div>
          </div>
        `;
        shell.onclick = async () => {
          activeGroupRunIds = row.runs.map(item => item.run_id);
          selectedRunId = row.best_run_id;
          activeTab = 'metrics';
          activeArtifactPath = null;
          await renderAll();
        };
        list.appendChild(shell);
      }
    }

    function pinRun(runId) {
      if (pinnedRunIds.includes(runId)) {
        pinnedRunIds = pinnedRunIds.filter(item => item !== runId);
      } else {
        pinnedRunIds = [...pinnedRunIds.slice(-2), runId];
      }
    }

    function contextText(run) {
      const keys = activeVariantKeys();
      const items = [
        run.project || run.experiment || 'unknown',
        run.group ? ('group=' + run.group) : null,
        run.status ? ('status=' + run.status) : null,
      ];
      for (const key of keys.slice(0, 2)) {
        if (run.params && run.params[key] !== undefined) {
          items.push(key + '=' + run.params[key]);
        }
      }
      if (run.params && run.params['train.seed'] !== undefined) {
        items.push('seed=' + run.params['train.seed']);
      }
      return items.filter(Boolean).join(' · ');
    }

    function renderRuns() {
      const tbody = document.getElementById('runsTableBody');
      const empty = document.getElementById('runsEmpty');
      const runs = rankedRuns(sourceFilteredRuns());
      tbody.innerHTML = '';
      if (!runs.length) {
        empty.style.display = 'block';
        return;
      }
      empty.style.display = 'none';
      const metric = activeMetric();
      for (const run of runs) {
        const tr = document.createElement('tr');
        const pinned = pinnedRunIds.includes(run.run_id);
        tr.innerHTML = `
          <td>
            <div class="run-name">${escapeHtml(run.name || run.run_id)}</div>
            <div class="tiny">${escapeHtml(run.run_id)}</div>
          </td>
          <td>
            <div><span class="badge info">${escapeHtml(run.source)}</span></div>
            <div class="tiny" style="margin-top:4px;">${escapeHtml(run.status || 'unknown')}</div>
          </td>
          <td>
            <div class="metric-value">${formatMetric(run.metrics && run.metrics[metric])}</div>
            <div class="tiny">${escapeHtml(metric)}</div>
          </td>
          <td class="tiny">${escapeHtml(contextText(run))}</td>
          <td>
            <div class="artifact-actions">
              <button class="secondary" data-action="inspect">inspect</button>
              <button class="secondary" data-action="pin">${pinned ? 'unpin' : 'pin'}</button>
            </div>
          </td>
        `;
        const buttons = tr.querySelectorAll('button');
        buttons[0].onclick = async () => {
          selectedRunId = run.run_id;
          activeTab = 'metrics';
          activeArtifactPath = null;
          await renderInspector();
        };
        buttons[1].onclick = async () => {
          pinRun(run.run_id);
          await renderAll();
        };
        tbody.appendChild(tr);
      }
    }

    function kvRows(data) {
      const entries = Object.entries(data || {});
      if (!entries.length) {
        return '<div class="empty">No data in this section.</div>';
      }
      return '<div class="kv-table">' + entries.sort((a, b) => a[0].localeCompare(b[0])).map(([key, value]) => `
        <div class="kv-row">
          <div class="kv-key">${escapeHtml(key)}</div>
          <div class="kv-value">${escapeHtml(typeof value === 'object' ? JSON.stringify(value) : String(value))}</div>
        </div>
      `).join('') + '</div>';
    }

    function shortlistRuns() {
      return pinnedRunIds
        .map(runId => allRuns.find(run => run.run_id === runId))
        .filter(Boolean);
    }

    function renderShortlist() {
      const grid = document.getElementById('shortlistGrid');
      const diff = document.getElementById('shortlistDiff');
      const runs = shortlistRuns();
      grid.innerHTML = '';
      if (!runs.length) {
        grid.innerHTML = '<div class="empty">Pin up to three runs from the table to compare them here.</div>';
        diff.innerHTML = '';
        return;
      }
      const metric = activeMetric();
      for (const run of runs) {
        const shell = document.createElement('div');
        shell.className = 'short-card';
        shell.innerHTML = `
          <div class="title">${escapeHtml(run.name || run.run_id)}</div>
          <div class="tiny">${escapeHtml(run.run_id)}</div>
          <div class="tiny">${escapeHtml(run.source)} · ${escapeHtml(run.status || 'unknown')}</div>
          <div style="margin-top:8px;font-weight:700;">${escapeHtml(metric)} = ${formatMetric(run.metrics && run.metrics[metric])}</div>
        `;
        grid.appendChild(shell);
      }
      if (runs.length < 2) {
        diff.innerHTML = '<div class="empty">Pin at least two runs to render a param diff.</div>';
        return;
      }
      const valueMap = new Map();
      for (const run of runs) {
        for (const [key, value] of Object.entries(run.params || {})) {
          if (!valueMap.has(key)) valueMap.set(key, new Set());
          valueMap.get(key).add(String(value));
        }
      }
      const varying = [...valueMap.entries()].filter(([, values]) => values.size > 1).map(([key]) => key).slice(0, 12);
      diff.innerHTML = varying.length
        ? '<div class="kv-table">' + varying.map(key => `
            <div class="kv-row">
              <div class="kv-key">${escapeHtml(key)}</div>
              <div class="kv-value">${runs.map(run => `<strong>${escapeHtml(run.name || run.run_id)}</strong>: ${escapeHtml(String(run.params && run.params[key] !== undefined ? run.params[key] : '<missing>'))}`).join('<br>')}</div>
            </div>
          `).join('') + '</div>'
        : '<div class="empty">Pinned runs do not differ on the first visible param slice.</div>';
    }

    async function renderInspector() {
      const root = document.getElementById('selectedRunShell');
      const run = allRuns.find(item => item.run_id === selectedRunId);
      if (!run) {
        root.innerHTML = '<div class="empty">Select a run from the table.</div>';
        return;
      }
      const artifacts = await getJson('/api/artifacts?run_id=' + encodeURIComponent(run.run_id));
      let preview = null;
      if (activeTab === 'artifacts' && activeArtifactPath) {
        preview = await getJson(
          '/api/artifact-preview?run_id='
            + encodeURIComponent(run.run_id)
            + '&path='
            + encodeURIComponent(activeArtifactPath)
        );
      }
      const tabs = ['metrics', 'params', 'tags', 'artifacts'];
      const metric = activeMetric();
      const artifactHtml = artifacts.artifacts.length
        ? '<div class="artifact-list">' + artifacts.artifacts.map(item => `
            <div class="artifact-item">
              <div class="artifact-row">
                <div>
                  <div><strong>${escapeHtml(item.path)}</strong></div>
                  <div class="tiny">${escapeHtml(item.kind)} · ${item.size_bytes} bytes</div>
                </div>
                <div class="artifact-actions">
                  ${item.previewable ? `<button class="secondary" data-preview="${escapeHtml(item.path)}">preview</button>` : ''}
                  <button class="secondary" data-download="${escapeHtml(item.path)}">download</button>
                </div>
              </div>
            </div>
          `).join('') + '</div>'
        : '<div class="empty">No local artifacts found for this run.</div>';
      let previewHtml = '';
      if (preview && !preview.error) {
        if (preview.kind === 'text') {
          previewHtml = `<div class="preview-shell">${escapeHtml(preview.text || '')}</div>`;
        } else if (preview.kind === 'image') {
          previewHtml = `<img class="preview-image" src="/artifact-file?run_id=${encodeURIComponent(run.run_id)}&path=${encodeURIComponent(preview.path)}" alt="${escapeHtml(preview.path)}">`;
        } else {
          previewHtml = `<div class="preview-shell">${escapeHtml(preview.message || 'Binary preview unavailable.')}</div>`;
        }
      }
      const sectionHtml = {
        metrics: kvRows(run.metrics),
        params: kvRows(run.params),
        tags: kvRows(run.tags),
        artifacts: artifactHtml + (previewHtml ? `<div style="margin-top:12px;">${previewHtml}</div>` : ''),
      };
      root.innerHTML = `
        <div class="detail-hero">
          <div class="eyebrow">${escapeHtml(run.source)}</div>
          <h3>${escapeHtml(run.name || run.run_id)}</h3>
          <div class="tiny">${escapeHtml(contextText(run))}</div>
          <div class="detail-grid">
            <div class="mini-stat"><div class="label">${escapeHtml(metric)}</div><div class="value">${formatMetric(run.metrics && run.metrics[metric])}</div></div>
            <div class="mini-stat"><div class="label">status</div><div class="value">${escapeHtml(run.status || 'unknown')}</div></div>
            <div class="mini-stat"><div class="label">history rows</div><div class="value">${formatCount(run.history_count || 0)}</div></div>
            <div class="mini-stat"><div class="label">started</div><div class="value">${escapeHtml(formatTimestamp(run.start_time))}</div></div>
          </div>
          <div class="status-line" style="margin-top:10px;">
            <div class="badge info">project: ${escapeHtml(run.project || run.experiment || 'unknown')}</div>
            <div class="badge info">artifact root: ${escapeHtml(artifacts.artifact_root || 'missing')}</div>
          </div>
        </div>
        <div class="detail-tabs">
          ${tabs.map(tab => `<div class="tab ${activeTab === tab ? 'active' : ''}" data-tab="${tab}">${tab}</div>`).join('')}
        </div>
        <div id="detailTabBody">${sectionHtml[activeTab]}</div>
      `;
      root.querySelectorAll('.tab').forEach(node => {
        node.onclick = async () => {
          activeTab = node.dataset.tab;
          if (activeTab !== 'artifacts') activeArtifactPath = null;
          await renderInspector();
        };
      });
      root.querySelectorAll('button[data-preview]').forEach(node => {
        node.onclick = async () => {
          activeArtifactPath = node.dataset.preview;
          activeTab = 'artifacts';
          await renderInspector();
        };
      });
      root.querySelectorAll('button[data-download]').forEach(node => {
        node.onclick = () => {
          const path = node.dataset.download;
          window.open('/artifact-file?run_id=' + encodeURIComponent(run.run_id) + '&path=' + encodeURIComponent(path), '_blank');
        };
      });
    }

    function renderSummary() {
      const payload = {
        run_count: summaryData.run_count,
        source_details: summaryData.source_details,
        warnings: summaryData.warnings,
        selected_source: selectedSource,
        metric: activeMetric(),
        direction: activeDirection(),
        variant_keys: activeVariantKeys(),
        active_group_run_ids: activeGroupRunIds,
        pinned_run_ids: pinnedRunIds,
        timestamps: summaryData.timestamps,
      };
      document.getElementById('summaryShell').textContent = JSON.stringify(payload, null, 2);
    }

    async function reloadData() {
      summaryData = await getJson('/api/summary');
      const runsData = await getJson('/api/runs');
      allRuns = runsData.runs || [];
      renderSourceTabs();
      renderMetricControls(allRuns);
      renderVariantChips();
      renderHealth();
    }

    async function renderAll() {
      const runs = sourceFilteredRuns();
      updateStats(runs);
      renderMetricControls(runs);
      renderVariantChips();
      renderRuns();
      renderShortlist();
      renderSummary();
      await renderCompare();
      if (selectedRunId && !allRuns.some(run => run.run_id === selectedRunId)) {
        selectedRunId = null;
      }
      await renderInspector();
    }

    async function bootstrap() {
      await reloadData();
      document.getElementById('runSearch').addEventListener('input', () => renderAll());
      document.getElementById('metricInput').addEventListener('change', () => renderAll());
      document.getElementById('metricSelect').addEventListener('change', async event => {
        document.getElementById('metricInput').value = event.target.value;
        await renderAll();
      });
      document.getElementById('directionSelect').addEventListener('change', () => renderAll());
      document.getElementById('variantInput').addEventListener('change', () => renderAll());
      document.getElementById('clearGroupButton').onclick = async () => {
        activeGroupRunIds = null;
        await renderAll();
      };
      document.getElementById('refreshButton').onclick = async () => {
        await getJson('/api/refresh', { method: 'POST' });
        activeGroupRunIds = null;
        await reloadData();
        await renderAll();
      };
      if ((summaryData.available_metrics || []).length && !document.getElementById('metricInput').value.trim()) {
        document.getElementById('metricInput').value = summaryData.available_metrics[0];
      }
      if ((summaryData.available_variant_keys || []).length && !document.getElementById('variantInput').value.trim()) {
        document.getElementById('variantInput').value = summaryData.available_variant_keys.slice(0, 1).join(', ');
      }
      await renderAll();
    }

    bootstrap();
  </script>
</body>
</html>
"""
