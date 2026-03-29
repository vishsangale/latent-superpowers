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
      --warn-soft: #f9e5d9;
      --shadow: 0 18px 40px rgba(46, 30, 16, 0.08);
      --radius: 18px;
    }
    * { box-sizing: border-box; }
    html, body { margin: 0; }
    body {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(255, 255, 255, 0.75), rgba(243, 235, 223, 0) 32%),
        linear-gradient(180deg, #f6efe4 0%, var(--bg) 100%);
    }
    .page {
      max-width: 1520px;
      margin: 0 auto;
      padding: 28px 22px 38px;
    }
    .hero {
      display: grid;
      grid-template-columns: 1.25fr 0.95fr;
      gap: 18px;
      margin-bottom: 18px;
    }
    .panel {
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }
    .hero-main {
      padding: 22px;
      background:
        linear-gradient(140deg, rgba(184, 76, 23, 0.11), rgba(255,255,255,0) 52%),
        linear-gradient(180deg, #fffdf8, #fff7ef);
      min-height: 188px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
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
    h1 {
      font-size: 36px;
      line-height: 1.05;
      margin-bottom: 12px;
    }
    .hero-copy {
      max-width: 70ch;
      color: var(--muted);
      line-height: 1.55;
      font-size: 14px;
    }
    .hero-foot {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 18px;
    }
    .source-pill, .chip {
      border-radius: 999px;
      border: 1px solid var(--line);
      padding: 7px 11px;
      font-size: 12px;
      background: rgba(255,255,255,0.8);
    }
    .source-pill.active, .chip.active {
      background: var(--accent);
      color: white;
      border-color: var(--accent);
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .stat {
      background: var(--paper-2);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px;
    }
    .stat .label {
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 6px;
    }
    .stat .value {
      font-size: 28px;
      font-weight: 700;
      line-height: 1;
    }
    .layout {
      display: grid;
      grid-template-columns: 1.45fr 0.95fr;
      gap: 18px;
    }
    .stack { display: grid; gap: 18px; }
    .card {
      padding: 18px;
    }
    .section-head {
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 16px;
      margin-bottom: 14px;
    }
    .section-head h2 { font-size: 20px; }
    .section-copy {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
      max-width: 64ch;
    }
    .controls {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr)) auto;
      gap: 10px;
      margin-bottom: 14px;
    }
    label {
      display: grid;
      gap: 6px;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }
    input, select {
      width: 100%;
      font: inherit;
      color: var(--ink);
      background: white;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px 12px;
    }
    button {
      font: inherit;
      font-weight: 700;
      border-radius: 10px;
      border: 1px solid var(--accent);
      padding: 10px 14px;
      background: var(--accent);
      color: white;
      cursor: pointer;
      align-self: end;
    }
    button.secondary {
      background: white;
      color: var(--accent);
      border-color: var(--line);
      font-weight: 600;
    }
    .filter-bar {
      display: grid;
      grid-template-columns: 1fr auto auto;
      gap: 10px;
      margin-bottom: 14px;
    }
    .toggle-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .chip {
      cursor: pointer;
      user-select: none;
    }
    .split {
      display: grid;
      grid-template-columns: 1fr;
      gap: 12px;
    }
    .compare-hero {
      display: grid;
      gap: 12px;
      margin-bottom: 14px;
    }
    .winner {
      border: 1px solid #cbe4d6;
      background: var(--good-soft);
      border-radius: 14px;
      padding: 14px;
    }
    .winner strong {
      display: block;
      font-size: 18px;
      margin-bottom: 4px;
    }
    .winner .meta {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
    }
    .compare-list {
      display: grid;
      gap: 10px;
    }
    .variant-row {
      border: 1px solid var(--line);
      background: var(--paper-2);
      border-radius: 14px;
      padding: 12px;
    }
    .variant-top {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: baseline;
      margin-bottom: 8px;
    }
    .variant-label {
      font-size: 14px;
      font-weight: 700;
      word-break: break-word;
    }
    .variant-metric {
      color: var(--good);
      font-weight: 700;
      white-space: nowrap;
    }
    .bar-shell {
      height: 10px;
      border-radius: 999px;
      background: #eadfce;
      overflow: hidden;
      margin-bottom: 8px;
    }
    .bar-fill {
      height: 100%;
      border-radius: 999px;
      background: linear-gradient(90deg, var(--accent), #e68b4c);
    }
    .variant-meta {
      color: var(--muted);
      font-size: 12px;
    }
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
    .run-name {
      font-weight: 700;
      margin-bottom: 3px;
    }
    .run-id, .tiny {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }
    .metric-value {
      color: var(--good);
      font-weight: 700;
      font-size: 14px;
    }
    .metric-sub {
      color: var(--muted);
      font-size: 12px;
      margin-top: 3px;
    }
    .empty {
      color: var(--muted);
      padding: 14px 0;
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
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
      margin-top: 12px;
    }
    .mini-stat {
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 10px;
      background: var(--paper-2);
    }
    .mini-stat .label {
      color: var(--muted);
      font-size: 11px;
      margin-bottom: 5px;
    }
    .mini-stat .value {
      font-size: 16px;
      font-weight: 700;
    }
    .detail-tabs {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 12px;
    }
    .tab {
      cursor: pointer;
      border-radius: 999px;
      border: 1px solid var(--line);
      padding: 8px 12px;
      font-size: 12px;
      background: white;
    }
    .tab.active {
      background: var(--accent-2);
      color: white;
      border-color: var(--accent-2);
    }
    .kv-table {
      display: grid;
      gap: 8px;
      max-height: 520px;
      overflow: auto;
    }
    .kv-row {
      display: grid;
      grid-template-columns: minmax(0, 0.85fr) minmax(0, 1.15fr);
      gap: 10px;
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 10px 12px;
      background: var(--paper-2);
      font-size: 12px;
    }
    .kv-key {
      color: var(--muted);
      word-break: break-word;
    }
    .kv-value {
      word-break: break-word;
    }
    .artifact-list {
      display: grid;
      gap: 8px;
      max-height: 380px;
      overflow: auto;
    }
    .artifact-item {
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 10px 12px;
      background: var(--paper-2);
      font-size: 12px;
      word-break: break-word;
    }
    .summary-shell {
      border: 1px solid var(--line);
      background: #fbf7ef;
      border-radius: 14px;
      padding: 12px;
      white-space: pre-wrap;
      font-size: 12px;
      max-height: 280px;
      overflow: auto;
    }
    .status-line {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 10px;
    }
    .badge {
      padding: 5px 8px;
      border-radius: 999px;
      font-size: 11px;
      border: 1px solid var(--line);
      background: white;
    }
    @media (max-width: 1180px) {
      .hero, .layout { grid-template-columns: 1fr; }
    }
    @media (max-width: 860px) {
      .controls { grid-template-columns: 1fr 1fr; }
      .filter-bar { grid-template-columns: 1fr; }
      .detail-grid { grid-template-columns: 1fr; }
      .stats { grid-template-columns: 1fr 1fr; }
      h1 { font-size: 30px; }
    }
    @media (max-width: 620px) {
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
            A no-auth browser console for your local MLflow and offline W&amp;B data. Filter by source, compare variants,
            inspect run internals, and find artifacts without leaving the machine.
          </p>
        </div>
        <div class="hero-foot" id="sourceTabs"></div>
      </section>
      <section class="panel hero-side">
        <div class="section-head">
          <div>
            <h2>At A Glance</h2>
            <p class="section-copy">Current view under the active source and search filters.</p>
          </div>
        </div>
        <div class="stats">
          <div class="stat"><div class="label">Visible Runs</div><div class="value" id="statRuns">-</div></div>
          <div class="stat"><div class="label">Sources</div><div class="value" id="statSources">-</div></div>
          <div class="stat"><div class="label">Best Metric</div><div class="value" id="statTopMetric">-</div></div>
          <div class="stat"><div class="label">Best Run</div><div class="value" id="statTopRun">-</div></div>
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
              <p class="section-copy">Narrow the local dataset before comparing variants or opening a run.</p>
            </div>
          </div>
          <div class="filter-bar">
            <input id="runSearch" placeholder="Search run name, run id, group, or parameter value">
            <input id="metricFilter" value="avg_reward" placeholder="Metric key">
            <input id="variantFilter" value="env.slate_size" placeholder="Variant key">
          </div>
          <div class="toggle-row" id="quickVariantRow"></div>
        </section>

        <section class="panel card">
          <div class="section-head">
            <div>
              <h2>Variant Compare</h2>
              <p class="section-copy">Grouped local comparison using the active source filter, search, metric, and variant key.</p>
            </div>
            <button onclick="renderCompare()">Refresh Compare</button>
          </div>
          <div class="compare-hero">
            <div class="winner" id="compareWinner">Loading grouped comparison...</div>
            <div class="compare-list" id="compareList"></div>
          </div>
        </section>

        <section class="panel card">
          <div class="section-head">
            <div>
              <h2>Runs</h2>
              <p class="section-copy">Sorted by the active metric. Select a run to inspect metrics, params, tags, and artifacts.</p>
            </div>
          </div>
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Source</th>
                <th>Primary Metric</th>
                <th>Context</th>
                <th>Open</th>
              </tr>
            </thead>
            <tbody id="runsTableBody"></tbody>
          </table>
          <div id="runsEmpty" class="empty" style="display:none;">No runs match the current filters.</div>
        </section>
      </div>

      <div class="stack">
        <section class="panel card">
          <div class="section-head">
            <div>
              <h2>Run Inspector</h2>
              <p class="section-copy">Focused detail for the currently selected run.</p>
            </div>
          </div>
          <div id="selectedRunShell">
            <div class="empty">Select a run from the table.</div>
          </div>
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
    let selectedRunId = null;
    let selectedSource = 'all';
    let activeTab = 'metrics';
    let summaryData = null;

    async function getJson(url) {
      const response = await fetch(url);
      return await response.json();
    }

    function formatMetric(value) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return '-';
      return Number(value).toFixed(3);
    }

    function getMetricKey() {
      return document.getElementById('metricFilter').value.trim() || 'avg_reward';
    }

    function getVariantKey() {
      return document.getElementById('variantFilter').value.trim() || 'env.slate_size';
    }

    function getSearchText() {
      return document.getElementById('runSearch').value.trim().toLowerCase();
    }

    function renderSourceTabs(sources) {
      const root = document.getElementById('sourceTabs');
      root.innerHTML = '';
      const values = ['all', ...sources];
      for (const source of values) {
        const button = document.createElement('button');
        button.className = 'source-pill' + (selectedSource === source ? ' active' : '');
        button.textContent = source === 'all' ? 'all sources' : source;
        button.onclick = () => {
          selectedSource = source;
          renderSourceTabs(summaryData.sources || []);
          renderAll();
        };
        root.appendChild(button);
      }
    }

    function filteredRuns() {
      const search = getSearchText();
      return allRuns.filter(run => {
        if (selectedSource !== 'all' && run.source !== selectedSource) return false;
        if (!search) return true;
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

    function topRun(runs) {
      const metric = getMetricKey();
      const ranked = runs.filter(run => run.metrics && run.metrics[metric] !== undefined)
        .sort((a, b) => Number(b.metrics[metric]) - Number(a.metrics[metric]));
      return ranked[0] || null;
    }

    function uniqueVariantKeys(runs) {
      const counts = new Map();
      for (const run of runs) {
        for (const key of Object.keys(run.params || {})) {
          counts.set(key, (counts.get(key) || 0) + 1);
        }
      }
      return [...counts.entries()]
        .filter(([, count]) => count >= 2)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 8)
        .map(([key]) => key);
    }

    function updateStats(runs) {
      document.getElementById('statRuns').textContent = runs.length;
      document.getElementById('statSources').textContent = selectedSource === 'all'
        ? (summaryData.sources || []).length
        : 1;
      const top = topRun(runs);
      document.getElementById('statTopMetric').textContent = top ? formatMetric(top.metrics[getMetricKey()]) : '-';
      document.getElementById('statTopRun').textContent = top ? (top.name || top.run_id).slice(0, 18) : '-';
      const badges = document.getElementById('statusBadges');
      badges.innerHTML = '';
      const items = [
        selectedSource === 'all' ? 'view: all sources' : 'view: ' + selectedSource,
        'metric: ' + getMetricKey(),
        'variant: ' + getVariantKey(),
        getSearchText() ? 'search: ' + getSearchText() : null,
      ].filter(Boolean);
      for (const item of items) {
        const badge = document.createElement('div');
        badge.className = 'badge';
        badge.textContent = item;
        badges.appendChild(badge);
      }
    }

    function renderQuickVariants(runs) {
      const root = document.getElementById('quickVariantRow');
      root.innerHTML = '';
      const variantKey = getVariantKey();
      const keys = uniqueVariantKeys(runs);
      if (variantKey && !keys.includes(variantKey)) keys.unshift(variantKey);
      for (const key of keys.slice(0, 10)) {
        const chip = document.createElement('div');
        chip.className = 'chip' + (key === variantKey ? ' active' : '');
        chip.textContent = key;
        chip.onclick = () => {
          document.getElementById('variantFilter').value = key;
          renderAll();
        };
        root.appendChild(chip);
      }
    }

    function groupRuns(runs, variantKey, metric) {
      const groups = new Map();
      for (const run of runs) {
        const label = run.params && run.params[variantKey] !== undefined
          ? variantKey + '=' + run.params[variantKey]
          : variantKey + '=<missing>';
        if (!groups.has(label)) groups.set(label, []);
        groups.get(label).push(run);
      }
      const rows = [];
      for (const [label, items] of groups.entries()) {
        const metricValues = items
          .filter(run => run.metrics && run.metrics[metric] !== undefined)
          .map(run => Number(run.metrics[metric]));
        const mean = metricValues.length
          ? metricValues.reduce((a, b) => a + b, 0) / metricValues.length
          : null;
        const best = items
          .filter(run => run.metrics && run.metrics[metric] !== undefined)
          .sort((a, b) => Number(b.metrics[metric]) - Number(a.metrics[metric]))[0] || null;
        rows.push({
          label,
          count: items.length,
          mean,
          best,
          items,
        });
      }
      rows.sort((a, b) => (b.mean ?? -Infinity) - (a.mean ?? -Infinity));
      return rows;
    }

    function renderCompare() {
      const runs = filteredRuns();
      const metric = getMetricKey();
      const variantKey = getVariantKey();
      const rows = groupRuns(runs, variantKey, metric);
      const winner = document.getElementById('compareWinner');
      const list = document.getElementById('compareList');
      list.innerHTML = '';
      if (!rows.length) {
        winner.textContent = 'No grouped comparison rows match the current filters.';
        return;
      }
      const top = rows[0];
      winner.innerHTML = `
        <strong>${top.label}</strong>
        <div class="meta">
          Top grouped mean on <strong>${metric}</strong>: ${formatMetric(top.mean)} across ${top.count} run(s).
          Best run: ${top.best ? (top.best.name || top.best.run_id) : '-'}.
        </div>
      `;
      const maxMean = Math.max(...rows.map(row => row.mean || 0), 1);
      for (const row of rows) {
        const shell = document.createElement('div');
        shell.className = 'variant-row';
        const width = row.mean ? Math.max(2, (row.mean / maxMean) * 100) : 0;
        shell.innerHTML = `
          <div class="variant-top">
            <div class="variant-label">${row.label}</div>
            <div class="variant-metric">${formatMetric(row.mean)}</div>
          </div>
          <div class="bar-shell"><div class="bar-fill" style="width:${width}%"></div></div>
          <div class="variant-meta">
            ${row.count} run(s) · best run ${row.best ? (row.best.name || row.best.run_id) : '-'}
          </div>
        `;
        shell.onclick = () => {
          if (row.best) {
            selectedRunId = row.best.run_id;
            activeTab = 'metrics';
            renderInspector();
          }
        };
        list.appendChild(shell);
      }
    }

    function renderRuns() {
      const metric = getMetricKey();
      const runs = filteredRuns().sort((a, b) => {
        return Number(b.metrics?.[metric] ?? -Infinity) - Number(a.metrics?.[metric] ?? -Infinity);
      });
      const tbody = document.getElementById('runsTableBody');
      const empty = document.getElementById('runsEmpty');
      tbody.innerHTML = '';
      if (!runs.length) {
        empty.style.display = 'block';
        return;
      }
      empty.style.display = 'none';
      for (const run of runs) {
        const context = [
          run.project || run.experiment || 'unknown',
          run.group ? ('group=' + run.group) : null,
          run.params?.['env.slate_size'] !== undefined ? ('slate=' + run.params['env.slate_size']) : null,
          run.params?.['train.seed'] !== undefined ? ('seed=' + run.params['train.seed']) : null,
        ].filter(Boolean).join(' · ');
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>
            <div class="run-name">${run.name || run.run_id}</div>
            <div class="run-id">${run.run_id}</div>
          </td>
          <td><span class="badge">${run.source}</span></td>
          <td>
            <div class="metric-value">${formatMetric(run.metrics?.[metric])}</div>
            <div class="metric-sub">${metric}</div>
          </td>
          <td class="tiny">${context}</td>
          <td><button class="secondary">inspect</button></td>
        `;
        tr.querySelector('button').onclick = () => {
          selectedRunId = run.run_id;
          activeTab = 'metrics';
          renderInspector();
        };
        tbody.appendChild(tr);
      }
    }

    function kvRows(data) {
      const entries = Object.entries(data || {});
      if (!entries.length) {
        return '<div class="empty">No data in this section.</div>';
      }
      return '<div class="kv-table">' + entries
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([key, value]) => `
          <div class="kv-row">
            <div class="kv-key">${key}</div>
            <div class="kv-value">${typeof value === 'object' ? JSON.stringify(value) : String(value)}</div>
          </div>
        `).join('') + '</div>';
    }

    async function renderInspector() {
      const root = document.getElementById('selectedRunShell');
      const run = allRuns.find(item => item.run_id === selectedRunId);
      if (!run) {
        root.innerHTML = '<div class="empty">Select a run from the table.</div>';
        return;
      }
      const artifacts = await getJson('/api/artifacts?run_id=' + encodeURIComponent(run.run_id));
      const tabs = ['metrics', 'params', 'tags', 'artifacts'];
      const sectionHtml = {
        metrics: kvRows(run.metrics),
        params: kvRows(run.params),
        tags: kvRows(run.tags),
        artifacts: artifacts.artifacts.length
          ? '<div class="artifact-list">' + artifacts.artifacts.map(item => `<div class="artifact-item">${item}</div>`).join('') + '</div>'
          : '<div class="empty">No local artifacts found for this run.</div>',
      };
      root.innerHTML = `
        <div class="detail-hero">
          <div class="eyebrow">${run.source}</div>
          <h3>${run.name || run.run_id}</h3>
          <div class="tiny">${run.project || run.experiment || 'unknown project'} · ${run.run_id}</div>
          <div class="detail-grid">
            <div class="mini-stat"><div class="label">avg_reward</div><div class="value">${formatMetric(run.metrics?.avg_reward)}</div></div>
            <div class="mini-stat"><div class="label">status</div><div class="value">${run.status || 'unknown'}</div></div>
            <div class="mini-stat"><div class="label">artifacts</div><div class="value">${artifacts.artifacts.length}</div></div>
          </div>
        </div>
        <div class="detail-tabs">
          ${tabs.map(tab => `<div class="tab ${activeTab === tab ? 'active' : ''}" data-tab="${tab}">${tab}</div>`).join('')}
        </div>
        <div id="detailTabBody">${sectionHtml[activeTab]}</div>
      `;
      root.querySelectorAll('.tab').forEach(node => {
        node.onclick = () => {
          activeTab = node.dataset.tab;
          renderInspector();
        };
      });
    }

    function renderSummary() {
      const payload = {
        run_count: summaryData.run_count,
        sources: summaryData.sources,
        selected_source: selectedSource,
        search: getSearchText() || null,
        metric: getMetricKey(),
        variant_key: getVariantKey(),
      };
      document.getElementById('summaryShell').textContent = JSON.stringify(payload, null, 2);
    }

    function renderAll() {
      const runs = filteredRuns();
      updateStats(runs);
      renderQuickVariants(runs);
      renderCompare();
      renderRuns();
      renderSummary();
      if (selectedRunId && !runs.some(run => run.run_id === selectedRunId)) {
        selectedRunId = null;
      }
      renderInspector();
    }

    async function bootstrap() {
      summaryData = await getJson('/api/summary');
      const runsData = await getJson('/api/runs');
      allRuns = runsData.runs;
      renderSourceTabs(summaryData.sources || []);
      document.getElementById('runSearch').addEventListener('input', renderAll);
      document.getElementById('metricFilter').addEventListener('change', renderAll);
      document.getElementById('variantFilter').addEventListener('change', renderAll);
      renderAll();
    }

    bootstrap();
  </script>
</body>
</html>
"""
