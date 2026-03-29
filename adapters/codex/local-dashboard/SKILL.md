---
name: local-dashboard
description: Use when the task involves browsing local runs in a browser, comparing local MLflow and W&B data, inspecting artifacts, or giving a single-user local dashboard over experiment results without requiring hosted services or API keys.
---

# Local Dashboard

## Overview

Serve a local browser UI over MLflow, W&B, artifacts, and ablation-style comparisons without auth or external services. This Codex adapter is intentionally thin and delegates real functionality to the shared core under `../../../core/local-dashboard`.

## Use This Skill When

- The user wants a local web UI over local experiment runs.
- The task is to browse local MLflow and W&B data without auth or hosted dashboards.
- The user wants run tables, grouped comparisons, and artifact browsing from local files.

## Do Not Use This Skill For

- Hosted W&B or MLflow server debugging.
- Repository planning work that belongs to paper-to-code.
- High-polish frontend design work. The dashboard should optimize for clarity and utility first.

## Operating Principles

- Load local run data into one normalized shape before serving anything.
- Keep the dashboard single-user, local-first, and zero-auth.
- Prefer simple JSON APIs plus a static local frontend.
- Expose grouped comparison and artifact inspection directly in the UI.

## Safety Rules

- Prefer read-only local inspection.
- Do not mutate runs, artifacts, or tracking stores.
- State when sources are partial or when a data backend could not be loaded.

## Shared Commands

- `python ../../../core/local-dashboard/scripts/index_runs.py`: Load local MLflow and W&B sources and emit a normalized dashboard index.
- `python ../../../core/local-dashboard/scripts/serve_dashboard.py`: Serve a local dashboard with JSON APIs and a browser UI for runs, comparisons, and artifacts.

## Shared References

- `../../../core/local-dashboard/references/workflow.md`: Local dashboard loading and serving flow.
- `../../../core/local-dashboard/references/data-model.md`: The normalized run shape and API surface.

## Common Workflows

### Serve a local dashboard

1. Resolve local MLflow and W&B sources.
2. Build a normalized local run index.
3. Start the dashboard server on a chosen host and port.
4. Use the UI or JSON APIs to inspect runs, grouped comparisons, and artifacts.

Helpers: `index_runs.py`, `serve_dashboard.py`

## Expected Outputs

- a local dashboard URL
- source and run counts
- grouped comparison data for one explicit metric
- artifact listings for selected runs
