---
name: wandb
description: Use when the task involves W&B projects, runs, groups, sweeps, configs, metrics, artifacts, offline sync issues, or selecting the best run under explicit evaluation criteria.
---

# Weights & Biases

## Overview

Inspect, compare, and summarize Weights & Biases experiment tracking workflows. This Codex adapter is intentionally thin and delegates real functionality to the shared core under `../../../core/wandb`.

## Use This Skill When

- The user mentions wandb, W&B, runs, groups, sweeps, artifacts, entities, or projects.
- The task is to compare runs, summarize a sweep, explain a dashboard discrepancy, or track down a checkpoint or artifact lineage.
- The user wants concise experiment summaries grounded in logged metrics, configs, and artifacts.

## Do Not Use This Skill For

- Hydra config composition or override-debugging tasks.
- MLflow tracking or model-registry workflows.
- Blind mutation. Launching sweeps, deleting runs, or editing metadata should only happen on explicit request.

## Operating Principles

- Resolve entity, project, run set, and metric selection before comparing anything.
- Make the definition of best run explicit.
- Prefer selective history pulls over full histories unless the task requires step-level inspection.
- Treat offline and online W&B usage as separate modes with different debugging steps.

## Safety Rules

- Prefer read-only inspection and summarization.
- Do not mutate runs, artifacts, or sweeps unless the user explicitly requests it.
- State missing metrics, partial histories, and logging inconsistencies as analysis risks.

## Shared Commands

- `python ../../../core/wandb/scripts/check_wandb_context.py`: Verify auth and resolve W&B entity or project context.
- `python ../../../core/wandb/scripts/compare_runs.py`: Compare runs under explicit metrics and filters.
- `python ../../../core/wandb/scripts/summarize_sweep.py`: Summarize a W&B sweep with winners, tradeoffs, and incomplete runs.
- `python ../../../core/wandb/scripts/artifact_lineage.py`: Inspect artifact versions, producer runs, and checkpoint lineage.

## Shared References

- `../../../core/wandb/references/workflow.md`: Project resolution, run gathering, and comparison flow.
- `../../../core/wandb/references/metrics-and-selection.md`: Metric choice, ranking discipline, and common comparison pitfalls.
- `../../../core/wandb/references/reporting.md`: Templates for concise W&B experiment summaries.

## Common Workflows

### Compare runs

1. Resolve the entity, project, and target run set.
2. Make the ranking metric explicit.
3. Pull summary metrics and config deltas.
4. Present the comparison and explain why one run beats another.

Helpers: `check_wandb_context.py`, `compare_runs.py`

### Summarize a sweep

1. Resolve the sweep and constituent runs.
2. Rank runs with a clear metric and optional constraints.
3. Highlight parameter trends, incomplete runs, and suspicious outliers.
4. Produce a concise researcher-facing summary.

Helpers: `check_wandb_context.py`, `summarize_sweep.py`

### Trace an artifact

1. Resolve the artifact name and version.
2. Identify the producing run and relevant aliases.
3. Identify downstream consumers when available.
4. Report the exact artifact or checkpoint lineage.

Helpers: `artifact_lineage.py`

## Expected Outputs

- resolved entity or project context
- the run set being compared
- the ranking metric and any constraints
- a compact run summary, sweep summary, or artifact lineage summary
