# MLflow for Gemini

Generated from `core/mlflow/skill-spec.yaml`.

## Purpose

Inspect, compare, and summarize MLflow tracking workflows and local tracking stores.

This adapter is a thin wrapper over the shared MLflow core. Prefer invoking the CLI helpers under the shared core before writing custom analysis logic.

## Use When

- The user mentions mlflow, tracking URIs, experiments, runs, artifacts, model registry, or local mlruns stores.
- The task is to compare runs, inspect experiment history, recover artifacts, or explain local tracking metadata.
- The user wants concise experiment summaries grounded in MLflow metrics, params, tags, and artifacts.

## Avoid When

- Hydra config composition or override-debugging tasks.
- W&B-specific workflows.
- Blind mutation. Deleting runs, editing registry state, or altering experiments should only happen on explicit request.

## Working Rules

- Resolve the tracking URI before inspecting runs.
- Make the definition of best run explicit.
- Prefer read-only inspection and summaries first.
- Treat file-backed tracking stores and remote tracking servers as distinct debugging modes.

## Safety Rules

- Prefer read-only inspection and summarization.
- Do not mutate runs, artifacts, or registry state unless the user explicitly requests it.
- State missing metrics, partial artifacts, and local-store limitations as analysis risks.

## Shared Core

- Skill root: `../../../core/mlflow`
- Scripts: `../../../core/mlflow/scripts`
- References: `../../../core/mlflow/references`

## Command Surface

- `python ../../../core/mlflow/scripts/check_mlflow_context.py`: Resolve the active tracking URI and summarize the local tracking-store context.
- `python ../../../core/mlflow/scripts/search_runs.py`: List MLflow runs with experiment, metric, param, and tag context.
- `python ../../../core/mlflow/scripts/compare_runs.py`: Compare MLflow runs under explicit metrics and filters.
- `python ../../../core/mlflow/scripts/list_artifacts.py`: List local artifacts for a specific MLflow run.

## Workflows

### Inspect context

1. Resolve the tracking URI from CLI input, environment, or a local mlruns directory.
2. Confirm whether the store is file-backed or remote.
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

## References

- `../../../core/mlflow/references/workflow.md`: Tracking URI resolution, run gathering, and comparison flow.
- `../../../core/mlflow/references/tracking-uri.md`: Distinguish file-backed tracking stores from remote MLflow servers.
- `../../../core/mlflow/references/artifacts.md`: Artifact layout expectations and local inspection caveats.

## Expected Outputs

- resolved tracking URI and storage mode
- the experiment or run set being compared
- the ranking metric and any constraints
- a compact run summary, artifact summary, or context summary
