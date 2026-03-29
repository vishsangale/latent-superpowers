# Dataset Pipeline for Gemini

Generated from `core/dataset-pipeline/skill-spec.yaml`.

## Purpose

Inspect dataset projects, profile local data files, detect split leakage, and snapshot dataset state for reproducible research.

This adapter is a thin wrapper over the shared dataset-pipeline core. Prefer the shared inspection and validation helpers over ad hoc one-off dataset scripts so pipeline onboarding stays explicit and reproducible.

## Use When

- The repo has data-prep scripts, dataset modules, or local dataset files that need inspection.
- The task is to validate train/val/test splits, find leakage, or profile schemas and null rates.
- The user wants a reproducible snapshot of local dataset files and sizes.

## Avoid When

- Experiment execution work that belongs to experiment-runner.
- Benchmarking trained runs that belongs to eval-benchmark.
- Cluster scheduling that belongs to Slurm.

## Working Rules

- Start by understanding the repo’s data entrypoints and import dependencies before mutating anything.
- Prefer deterministic local file inspection over assumptions about schema or split logic.
- Treat leakage, missing dependencies, and missing files as first-class blockers.
- Produce compact manifests that can be checked into notes or artifacts.

## Safety Rules

- Prefer read-only inspection of repos and datasets.
- Do not rewrite dataset files or inferred split assignments.
- Call out unsupported file formats or missing parsing dependencies explicitly.

## Shared Core

- Skill root: `../../../core/dataset-pipeline`
- Scripts: `../../../core/dataset-pipeline/scripts`
- References: `../../../core/dataset-pipeline/references`

## Command Surface

- `python ../../../core/dataset-pipeline/scripts/inspect_dataset_project.py`: Inspect a repo for dataset scripts, pipeline imports, dataset choices, and missing dependencies.
- `python ../../../core/dataset-pipeline/scripts/profile_dataset.py`: Profile local dataset files or directories across CSV, JSONL, and Parquet when supported.
- `python ../../../core/dataset-pipeline/scripts/validate_splits.py`: Detect overlap or leakage across train, validation, and test files.
- `python ../../../core/dataset-pipeline/scripts/snapshot_dataset.py`: Write a local snapshot manifest with relative paths, sizes, and SHA256 digests.

## Workflows

### Onboard a new dataset repo

1. Inspect dataset entrypoints, pipeline modules, and dependency gaps.
2. Identify the concrete dataset files or roots that exist locally.
3. Profile representative files before making assumptions about schema or split logic.
4. Surface blockers such as missing dependencies, missing modules, or unsupported formats.

Helpers: `inspect_dataset_project.py`, `profile_dataset.py`

### Validate a local split and freeze its state

1. Load the explicit train, validation, and test files.
2. Resolve ID columns or fall back to row hashing when needed.
3. Report overlap counts and leakage risk clearly.
4. Write a snapshot manifest so the checked dataset state can be referenced later.

Helpers: `validate_splits.py`, `snapshot_dataset.py`

## References

- `../../../core/dataset-pipeline/references/workflow.md`: Repo inspection, local profiling, split validation, and dataset snapshot flow.
- `../../../core/dataset-pipeline/references/split-validation.md`: ID-key heuristics, row hashing, and leakage interpretation rules.

## Expected Outputs

- repo-aware dataset entrypoints, dataset names, and dependency gaps
- per-file schema or sample summaries with row counts and null counts
- explicit split overlap or leakage findings
- a reproducible dataset snapshot manifest with sizes and checksums
