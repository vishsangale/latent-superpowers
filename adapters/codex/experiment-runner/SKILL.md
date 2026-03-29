---
name: experiment-runner
description: Use when the task involves planning multiple experiment commands, running seeded sweeps, resuming failed local runs, or summarizing which commands succeeded, failed, or need to be rerun.
---

# Experiment Runner

## Overview

Plan, launch, resume, and summarize local experiment matrices with explicit manifests and seeded sweep discipline. This Codex adapter is intentionally thin and delegates real functionality to the shared core under `../../../core/experiment-runner`.

## Use This Skill When

- The user wants to run a local matrix of commands, seeds, or Hydra overrides.
- The task is to generate an explicit run manifest before launching anything.
- The task is to resume failed runs or summarize what already ran.

## Do Not Use This Skill For

- Cluster scheduling work that belongs to the Slurm skill.
- Fine-grained config provenance questions that belong to Hydra.
- Hosted tracking inspection that belongs to W&B or MLflow directly.

## Operating Principles

- Make the run matrix explicit before launching commands.
- Treat seeds as first-class experiment dimensions.
- Persist manifests and per-run stdout or stderr so runs can be resumed instead of reinvented.
- Separate command planning from result interpretation.

## Safety Rules

- Default to planning and dry-run output before executing commands.
- Never hide failed commands or silently drop stderr.
- Keep execution local and sequential unless the user explicitly wants concurrency.

## Shared Commands

- `python ../../../core/experiment-runner/scripts/plan_runs.py`: Build an explicit local run matrix from a base command, override factors, and seeds.
- `python ../../../core/experiment-runner/scripts/launch_runs.py`: Execute a planned run matrix locally and write manifest-backed logs and result records.
- `python ../../../core/experiment-runner/scripts/resume_runs.py`: Resume failed or incomplete runs from an existing manifest.
- `python ../../../core/experiment-runner/scripts/summarize_manifest.py`: Summarize manifest results, durations, and the best extracted metric from local logs.

## Shared References

- `../../../core/experiment-runner/references/workflow.md`: Planning, launch, resume, and analysis flow for local experiment batches.
- `../../../core/experiment-runner/references/manifest-layout.md`: Manifest fields, result records, and log file conventions.

## Common Workflows

### Plan a seeded local sweep

1. Resolve the repo, base command, and working directory.
2. Expand the explicit factor grid and seed list into a manifest.
3. Review the run count, labels, and overrides before launching.
4. Launch locally and preserve stdout, stderr, and result metadata per run.

Helpers: `plan_runs.py`, `launch_runs.py`

### Recover from partial failures

1. Read the existing manifest and result records.
2. Identify failed or missing runs without rebuilding the matrix.
3. Rerun only the missing work.
4. Summarize successes, failures, durations, and extracted metrics.

Helpers: `resume_runs.py`, `summarize_manifest.py`

## Expected Outputs

- the resolved base command and working directory
- the explicit matrix dimensions and run count
- a manifest path plus per-run log locations
- a concise success or failure summary and rerun guidance
