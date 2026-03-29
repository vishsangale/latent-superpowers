# Slurm Cluster for Claude Code

Generated from `core/slurm-cluster/skill-spec.yaml`.

## Purpose

Inspect repo entrypoints for cluster readiness, generate sbatch scripts, convert local run manifests into job arrays, and summarize Slurm logs and sacct output.

This adapter is a thin wrapper over the shared slurm-cluster core. Prefer the generated scripts and parsers over ad hoc shell snippets so cluster execution stays explicit and debuggable.

## Use When

- The user wants to launch a repo’s experiments on Slurm.
- The task is to turn a local command or experiment-runner manifest into sbatch or array artifacts.
- The task is to parse Slurm logs or sacct output and explain failures.

## Avoid When

- Purely local execution that belongs to experiment-runner.
- Detailed Hydra config questions that belong to Hydra.
- Hosted tracking dashboards that belong to MLflow or W&B.

## Working Rules

- Default to dry-run planning and script generation before any cluster submission.
- Reuse the repo’s real entrypoints and manifests instead of inventing new shell wrappers.
- Make resources, environment setup, and log paths explicit in generated scripts.
- Turn scheduler output into concrete failure categories instead of raw text dumps.

## Safety Rules

- Do not submit jobs automatically unless the user explicitly asks.
- Preserve generated scripts and array maps so cluster work can be audited later.
- Surface missing Slurm commands or missing cluster access as actionable blockers.

## Shared Core

- Skill root: `../../../core/slurm-cluster`
- Scripts: `../../../core/slurm-cluster/scripts`
- References: `../../../core/slurm-cluster/references`

## Command Surface

- `python ../../../core/slurm-cluster/scripts/inspect_slurm_project.py`: Inspect a repo for Hydra entrypoints, existing Slurm scripts, and cluster-ready execution hints.
- `python ../../../core/slurm-cluster/scripts/generate_sbatch.py`: Generate a single-job sbatch script from a repo-aware command or auto-detected Hydra entrypoint.
- `python ../../../core/slurm-cluster/scripts/plan_job_array.py`: Convert an experiment-runner manifest into a Slurm array script and array task map.
- `python ../../../core/slurm-cluster/scripts/summarize_slurm_log.py`: Parse Slurm logs for common failure signatures like OOM, timeouts, and module errors.
- `python ../../../core/slurm-cluster/scripts/parse_sacct.py`: Parse sacct output into status counts and failed-job summaries.

## Workflows

### Prepare a repo for Slurm

1. Inspect the repo for Hydra entrypoints and existing Slurm patterns.
2. Resolve a concrete base command and working directory.
3. Generate an sbatch script with explicit resources, environment setup, and logs.
4. Review the script before cluster submission.

Helpers: `inspect_slurm_project.py`, `generate_sbatch.py`

### Turn a local sweep into a job array

1. Start from a saved experiment-runner manifest.
2. Generate an array script plus a machine-readable task map.
3. Use the generated logs and sacct summaries to diagnose failures at scale.

Helpers: `plan_job_array.py`, `summarize_slurm_log.py`, `parse_sacct.py`

## References

- `../../../core/slurm-cluster/references/workflow.md`: Repo inspection, sbatch generation, array planning, and log triage flow.
- `../../../core/slurm-cluster/references/failure-patterns.md`: Common Slurm failure signatures and how the parser classifies them.

## Expected Outputs

- repo-aware cluster entrypoints and existing Slurm hints
- generated sbatch or job-array scripts with explicit resources and working directory
- parsed sacct summaries with status counts and failed jobs
- concise failure diagnoses from Slurm stdout or stderr logs
