# Local Dashboard for Claude Code

Generated from `core/local-dashboard/skill-spec.yaml`.

## Purpose

Serve a local browser UI over MLflow, W&B, artifacts, shortlist comparisons, tradeoff views, and grouped experiment analysis without auth or external services.

This adapter is a thin wrapper over the shared local-dashboard core. Prefer invoking the CLI helpers under the shared core before building ad-hoc local viewers.

## Use When

- The user wants a local web UI over local experiment runs.
- The task is to browse local MLflow and W&B data without auth or hosted dashboards.
- The user wants run tables, grouped comparisons, artifact preview, tradeoff views, shortlist comparison, or project rollups from local files.

## Avoid When

- Hosted W&B or MLflow server debugging.
- Repository planning work that belongs to paper-to-code.
- High-polish frontend design work. The dashboard should optimize for clarity and utility first.

## Working Rules

- Load local run data into one normalized shape before serving anything.
- Keep the dashboard single-user, local-first, and zero-auth.
- Prefer simple JSON APIs plus a static local frontend that can refresh local state safely.
- Expose grouped comparison, shortlist comparison, tradeoff analysis, and artifact inspection directly in the UI.

## Safety Rules

- Prefer read-only local inspection.
- Do not mutate runs, artifacts, or tracking stores.
- State when sources are partial or when a data backend could not be loaded.

## Shared Core

- Skill root: `../../../core/local-dashboard`
- Scripts: `../../../core/local-dashboard/scripts`
- References: `../../../core/local-dashboard/references`

## Command Surface

- `python ../../../core/local-dashboard/scripts/index_runs.py`: Load local MLflow and W&B sources and emit a normalized dashboard index.
- `python ../../../core/local-dashboard/scripts/serve_dashboard.py`: Serve a local dashboard with JSON APIs and a browser UI for filtered runs, grouped comparisons, shortlist review, tradeoff views, refresh, and artifact preview.

## Workflows

### Serve a local dashboard

1. Resolve local MLflow and W&B sources.
2. Build a normalized local run index.
3. Start the dashboard server on a chosen host and port.
4. Use the UI or JSON APIs to inspect runs, compare variants with explicit metric direction, review tradeoffs, and preview artifacts.

Helpers: `index_runs.py`, `serve_dashboard.py`

## References

- `../../../core/local-dashboard/references/workflow.md`: Local dashboard loading and serving flow.
- `../../../core/local-dashboard/references/data-model.md`: The normalized run shape and API surface.

## Expected Outputs

- a local dashboard URL
- source health and run counts
- grouped comparison data for one explicit metric and direction
- shortlist and tradeoff views over the current filtered slice
- artifact listings plus preview or download for selected runs
