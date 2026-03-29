#!/usr/bin/env python3
"""Shared helpers for the local dashboard."""

from __future__ import annotations

from pathlib import Path
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
from local_run_utils import load_local_runs, run_to_dict  # type: ignore[import-not-found]


def load_dashboard_state(
    *,
    mlflow_uri: str | None,
    mlflow_experiment_name: str | None,
    mlflow_experiment_id: str | None,
    wandb_paths: list[str] | None,
    wandb_project: str | None,
    wandb_group: str | None,
) -> dict[str, Any]:
    runs = load_local_runs(
        mlflow_tracking_uri=mlflow_uri,
        mlflow_experiment_name=mlflow_experiment_name,
        mlflow_experiment_id=mlflow_experiment_id,
        wandb_paths=wandb_paths,
        wandb_project=wandb_project,
        wandb_group=wandb_group,
    )
    return {
        "sources": sorted({run.source for run in runs}),
        "run_count": len(runs),
        "runs": runs,
    }


def serializable_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "sources": state["sources"],
        "run_count": state["run_count"],
        "runs": [run_to_dict(run) for run in state["runs"]],
    }


def grouped_compare(
    state: dict[str, Any],
    *,
    metric: str,
    direction: str,
    variant_keys: list[str],
) -> list[dict[str, Any]]:
    return grouped_payload(group_runs(state["runs"], variant_keys), metric, direction=direction)


def list_artifacts(state: dict[str, Any], run_id: str) -> dict[str, Any]:
    run = next((run for run in state["runs"] if run.run_id == run_id), None)
    if run is None:
        return {"run_id": run_id, "artifact_root": None, "artifacts": []}
    artifact_root = run.artifact_root
    artifacts: list[str] = []
    if artifact_root:
        candidate = Path(artifact_root)
        if candidate.exists():
            artifacts = [
                str(path.relative_to(candidate))
                for path in sorted(candidate.rglob("*"))
                if path.is_file()
            ]
    return {"run_id": run_id, "artifact_root": artifact_root, "artifacts": artifacts}


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Local Experiment Dashboard</title>
  <style>
    body { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; margin: 24px; color: #111; background: #f6f4ef; }
    h1, h2 { margin: 0 0 12px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    .card { background: white; border: 1px solid #d6d2c4; padding: 16px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #ece8da; vertical-align: top; }
    input, select { font: inherit; padding: 6px 8px; margin-right: 8px; }
    button { font: inherit; padding: 6px 10px; cursor: pointer; }
    .wide { grid-column: 1 / -1; }
    .muted { color: #666; }
    pre { white-space: pre-wrap; background: #faf8f1; padding: 12px; border-radius: 8px; border: 1px solid #ece8da; }
  </style>
</head>
<body>
  <h1>Local Experiment Dashboard</h1>
  <p class="muted">Local MLflow and W&amp;B data, no auth, no external service.</p>
  <div class="grid">
    <section class="card">
      <h2>Summary</h2>
      <pre id="summary">Loading...</pre>
    </section>
    <section class="card">
      <h2>Compare</h2>
      <label>Metric <input id="metric" value="avg_reward"></label>
      <label>Direction
        <select id="direction">
          <option value="max">max</option>
          <option value="min">min</option>
        </select>
      </label>
      <label>Variant key <input id="variantKey" value="env.slate_size"></label>
      <button onclick="loadCompare()">Refresh</button>
      <pre id="compare">Loading...</pre>
    </section>
    <section class="card wide">
      <h2>Runs</h2>
      <table id="runsTable">
        <thead><tr><th>Source</th><th>Name</th><th>Run ID</th><th>Metric</th><th>Artifacts</th></tr></thead>
        <tbody></tbody>
      </table>
    </section>
    <section class="card wide">
      <h2>Artifacts</h2>
      <pre id="artifacts">Select a run.</pre>
    </section>
  </div>
  <script>
    async function getJson(url) {
      const response = await fetch(url);
      return await response.json();
    }

    async function loadSummary() {
      const data = await getJson('/api/summary');
      document.getElementById('summary').textContent = JSON.stringify(data, null, 2);
    }

    async function loadRuns() {
      const data = await getJson('/api/runs');
      const tbody = document.querySelector('#runsTable tbody');
      tbody.innerHTML = '';
      for (const run of data.runs) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${run.source}</td>
          <td>${run.name || ''}</td>
          <td>${run.run_id}</td>
          <td>${run.metrics.avg_reward ?? ''}</td>
          <td><button data-run="${run.run_id}">show</button></td>
        `;
        tr.querySelector('button').addEventListener('click', async () => {
          const artifacts = await getJson('/api/artifacts?run_id=' + encodeURIComponent(run.run_id));
          document.getElementById('artifacts').textContent = JSON.stringify(artifacts, null, 2);
        });
        tbody.appendChild(tr);
      }
    }

    async function loadCompare() {
      const metric = document.getElementById('metric').value;
      const direction = document.getElementById('direction').value;
      const variantKey = document.getElementById('variantKey').value;
      const data = await getJson('/api/compare?metric=' + encodeURIComponent(metric) + '&direction=' + encodeURIComponent(direction) + '&variant_key=' + encodeURIComponent(variantKey));
      document.getElementById('compare').textContent = JSON.stringify(data, null, 2);
    }

    loadSummary();
    loadRuns();
    loadCompare();
  </script>
</body>
</html>
"""
