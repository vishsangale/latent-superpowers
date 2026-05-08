---
name: eval-benchmark
description: "Purpose"
---

# Eval Benchmark for OpenCode

Generated from `core/eval-benchmark/skill-spec.yaml`.

## Purpose

Rank local runs, compare candidates against baselines, inspect metric histories, and generate concise benchmark reports across MLflow and W&B data.

This adapter is a thin wrapper over the shared eval-benchmark core. Prefer the shared benchmark helpers over ad hoc manual comparisons so local evaluation work stays explicit and repeatable.

## Use When

- The user wants a leaderboard, regression check, or compact benchmark report over local runs.
- The task is to compare one run against another under explicit metrics and differing params.
- The data lives in local MLflow stores, W&B offline runs, or local JSON artifacts logged by experiments.

## Avoid When

- Raw sweep planning or execution work that belongs to experiment-runner.
- Config composition questions that belong to Hydra.
- Blind statistical significance claims without enough runs.

## Working Rules

- Make the ranking metric explicit and keep baseline or candidate selection concrete.
- Separate summary metrics from full history inspection.
- Surface differing params alongside metric deltas.
- Treat missing history or artifact data as a real evaluation limitation.

## Safety Rules

- Prefer read-only inspection of local tracking stores and artifacts.
- Do not rewrite run metadata or alter artifact contents.
- Call out when comparisons mix sources or when histories are unavailable.

## Shared Core

- Skill root: `../../../core/eval-benchmark`
- Scripts: `../../../core/eval-benchmark/scripts`
- References: `../../../core/eval-benchmark/references`

## Command Surface

- `python ../../../core/eval-benchmark/scripts/leaderboard.py`: Build a local leaderboard across MLflow and W&B runs under an explicit metric.
- `python ../../../core/eval-benchmark/scripts/compare_run_pair.py`: Compare a candidate run against a baseline run, including metric deltas and differing params.
- `python ../../../core/eval-benchmark/scripts/inspect_histories.py`: Inspect per-run histories from MLflow artifacts or W&B offline data and summarize available metrics.
- `python ../../../core/eval-benchmark/scripts/benchmark_report.py`: Produce a compact Markdown benchmark report from local runs and optional baseline selection.

## Workflows

### Produce a benchmark leaderboard

1. Resolve the local MLflow and W&B run sources.
2. Choose the ranking metric and direction explicitly.
3. Rank runs and note varying parameters.
4. Generate a compact Markdown report for the top results.

Helpers: `leaderboard.py`, `benchmark_report.py`

### Check whether a candidate regressed

1. Select explicit baseline and candidate run IDs.
2. Compare key metrics and differing params.
3. Inspect history data when available to distinguish early spikes from stable gains.
4. Surface missing artifacts or missing metrics instead of guessing.

Helpers: `compare_run_pair.py`, `inspect_histories.py`

## References

- `../../../core/eval-benchmark/references/workflow.md`: Benchmark ranking, baseline comparison, and report-writing flow.
- `../../../core/eval-benchmark/references/history-inspection.md`: How history data is recovered from MLflow artifacts and W&B offline runs.

## Expected Outputs

- ranked runs under an explicit metric and direction
- candidate versus baseline deltas for key metrics
- history summaries with available metric keys and final values
- a concise Markdown benchmark report for notes or docs
