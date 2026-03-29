---
name: mlflow
description: Use when the task involves MLflow experiments, runs, metrics, params, artifacts, tracking URIs, or selecting the best run under explicit evaluation criteria.
---

# MLflow

## Overview

Inspect, compare, and summarize MLflow tracking workflows and local tracking stores. This Codex adapter is intentionally thin and delegates real functionality to the shared core under `../../../core/mlflow`.

## Use This Skill When

- The user mentions mlflow, tracking URIs, experiments, runs, artifacts, model registry, or local mlruns stores.
- The task is to compare runs, inspect experiment history, recover artifacts, or explain local tracking metadata.
- The user wants concise experiment summaries grounded in MLflow metrics, params, tags, and artifacts.

## Do Not Use This Skill For

- Hydra config composition or override-debugging tasks.
- W&B-specific workflows.
- Blind mutation. Deleting runs, editing registry state, or altering experiments should only happen on explicit request.

## Operating Principles

- Resolve the tracking URI before inspecting runs.
- Make the definition of best run explicit.
- Prefer read-only inspection and summaries first.
- Treat local SQLite backends, file-backed stores, and remote tracking servers as distinct debugging modes.

## Safety Rules

- Prefer read-only inspection and summarization.
- Do not mutate runs, artifacts, or registry state unless the user explicitly requests it.
- State missing metrics, partial artifacts, and local-store limitations as analysis risks.

## Shared Commands

- `python ../../../core/mlflow/scripts/check_mlflow_context.py`: Resolve the active tracking URI and summarize the local tracking context for file, SQLite, or remote modes.
- `python ../../../core/mlflow/scripts/search_runs.py`: List MLflow runs with experiment, metric, param, and tag context.
- `python ../../../core/mlflow/scripts/compare_runs.py`: Compare MLflow runs under explicit metrics and filters.
- `python ../../../core/mlflow/scripts/list_artifacts.py`: List local artifacts for a specific MLflow run.

## Shared References

- `../../../core/mlflow/references/workflow.md`: Tracking URI resolution, run gathering, and comparison flow.
- `../../../core/mlflow/references/tracking-uri.md`: Distinguish local SQLite, file-backed tracking stores, and remote MLflow servers.
- `../../../core/mlflow/references/artifacts.md`: Artifact layout expectations and local inspection caveats.

## Common Workflows

### Inspect context

1. Resolve the tracking URI from CLI input, environment, a local SQLite database, or a local mlruns directory.
2. Confirm whether the store is SQLite-backed, file-backed, or remote.
3. Summarize available experiments before selecting one for deeper analysis.

Helpers: `check_mlflow_context.py`

### Compare runs

1. Resolve the target experiment by name or ID.
2. Make the ranking metric explicit.
3. Pull run metrics, params, and tags.
4. Present the comparison and explain why one run beats another.

Helpers: `search_runs.py`, `compare_runs.py`

### Inspect artifacts

1. Resolve the target run ID.
2. Map the run to its local artifact path.
3. Summarize the files available under that artifact root.
4. State when the tracking store does not expose artifacts locally.

Helpers: `list_artifacts.py`

## Expected Outputs

- resolved tracking URI and storage mode
- the experiment or run set being compared
- the ranking metric and any constraints
- a compact run summary, artifact summary, or context summary
