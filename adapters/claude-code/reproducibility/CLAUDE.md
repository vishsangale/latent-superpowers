# Reproducibility for Claude Code

Generated from `core/reproducibility/skill-spec.yaml`.

## Purpose

Capture local run context, verify current state against a saved context, reconstruct tracked runs, and diff reproducibility snapshots.

This adapter is a thin wrapper over the shared reproducibility core. Prefer these helpers over ad hoc shell notes so local experiment provenance stays machine-checkable.

## Use When

- The user wants an exact record of repo state, Python environment, and key env vars before or after a run.
- The task is to verify whether the current machine still matches a prior context capture.
- The task is to reconstruct local MLflow or W&B runs into a concise reproducibility report.

## Avoid When

- Raw experiment execution that belongs to experiment-runner.
- Config composition debugging that belongs to Hydra.
- Hosted tracking dashboards that belong to MLflow or W&B directly.

## Working Rules

- Capture concrete facts, not vague prose, about code state, runtime, and environment variables.
- Treat dirty git state and dependency drift as first-class reproducibility risks.
- Reconstruct tracked runs from local artifacts and metadata before asking the user to remember commands.
- Make diffs explicit so drift is attributable instead of anecdotal.

## Safety Rules

- Prefer read-only inspection of repos, env vars, and tracking data.
- Do not rewrite git history or mutate tracking stores.
- Only include env keys explicitly requested by the user or the command flags.

## Shared Core

- Skill root: `../../../core/reproducibility`
- Scripts: `../../../core/reproducibility/scripts`
- References: `../../../core/reproducibility/references`

## Command Surface

- `python ../../../core/reproducibility/scripts/capture_run_context.py`: Capture repo, git, Python, and selected environment details into a JSON snapshot.
- `python ../../../core/reproducibility/scripts/verify_repro_context.py`: Compare the current repo and runtime against a saved reproducibility context.
- `python ../../../core/reproducibility/scripts/reconstruct_local_run.py`: Reconstruct a local MLflow or W&B run into a concise reproducibility report.
- `python ../../../core/reproducibility/scripts/diff_run_contexts.py`: Diff two saved reproducibility contexts and surface the fields that changed.

## Workflows

### Freeze local state before a run

1. Capture the current repo, git, Python, and selected env state.
2. Save the context next to the planned run or manifest.
3. Re-run verification later to detect drift before comparing results.

Helpers: `capture_run_context.py`, `verify_repro_context.py`

### Recover how a tracked run was produced

1. Resolve the run from local MLflow or W&B data.
2. Extract params, metrics, tags, and artifact references.
3. Compare that recovered view against the current local context or another saved snapshot.

Helpers: `reconstruct_local_run.py`, `diff_run_contexts.py`

## References

- `../../../core/reproducibility/references/workflow.md`: Capture, verify, reconstruct, and diff flow for local experiments.
- `../../../core/reproducibility/references/drift-checks.md`: What counts as code, environment, and tracking drift.

## Expected Outputs

- a JSON context snapshot with repo, git, Python, and selected env data
- a drift report showing matches and mismatches against a saved context
- a reconstructed local run report with metrics, params, tags, and artifact references
- a structured diff between two saved reproducibility captures
