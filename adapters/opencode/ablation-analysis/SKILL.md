---
name: ablation-analysis
description: "Purpose"
---

# Ablation Analysis for OpenCode

Generated from `core/ablation-analysis/skill-spec.yaml`.

## Purpose

Collect, compare, rank, plot, and summarize local experiment ablations across MLflow and W&B data.

This adapter is a thin wrapper over the shared ablation-analysis core. Prefer invoking the CLI helpers under the shared core before writing custom comparison logic.

## Use When

- The user wants to compare variants, ablations, or hyperparameter choices across local runs.
- The task is to rank runs, detect varying factors, compute deltas, or generate plots and concise experiment summaries.
- The data lives in local MLflow tracking stores, W&B offline runs, or collected JSON exports.

## Avoid When

- Low-level training configuration work that belongs to Hydra.
- Hosted dashboard troubleshooting that belongs to W&B or MLflow directly.
- Blind statistical claims. Surface sample-size limits and metric ambiguity explicitly.

## Working Rules

- Normalize runs into a common local shape before comparing anything.
- Make the ranking metric and direction explicit.
- Separate per-run ranking from grouped variant comparisons.
- Treat tiny sample counts and missing metrics as real analysis risks.

## Safety Rules

- Prefer read-only local inspection and analysis.
- Do not mutate tracking backends or run metadata.
- State when conclusions are based on too few runs or on mixed experiment sources.

## Shared Core

- Skill root: `../../../core/ablation-analysis`
- Scripts: `../../../core/ablation-analysis/scripts`
- References: `../../../core/ablation-analysis/references`

## Command Surface

- `python ../../../core/ablation-analysis/scripts/collect_runs.py`: Load and normalize local MLflow and W&B runs into a common analysis shape.
- `python ../../../core/ablation-analysis/scripts/rank_variants.py`: Rank runs or grouped variants under an explicit metric and direction.
- `python ../../../core/ablation-analysis/scripts/compare_ablations.py`: Compare grouped ablations, aggregate metric deltas, and identify winners and baselines.
- `python ../../../core/ablation-analysis/scripts/plot_ablations.py`: Generate a local SVG plot for per-run or grouped ablation comparisons.
- `python ../../../core/ablation-analysis/scripts/summarize_findings.py`: Produce a concise researcher-facing Markdown summary from local run data.

## Workflows

### Compare a local experiment set

1. Resolve the local MLflow or W&B run sources.
2. Normalize runs into a common analysis shape.
3. Make the ranking metric and direction explicit.
4. Identify varying factors and compare grouped variants.

Helpers: `collect_runs.py`, `rank_variants.py`, `compare_ablations.py`

### Produce a compact research summary

1. Group runs by the ablation factors that matter.
2. Rank variants with explicit metric discipline.
3. Generate a compact table, a local plot, and a Markdown conclusion.
4. Call out missing metrics, tiny sample counts, and outliers.

Helpers: `compare_ablations.py`, `summarize_findings.py`, `plot_ablations.py`

## References

- `../../../core/ablation-analysis/references/workflow.md`: Local run loading, grouping, ranking, and reporting flow.
- `../../../core/ablation-analysis/references/metric-discipline.md`: Metric choice, direction, and small-sample caveats.
- `../../../core/ablation-analysis/references/reporting.md`: Templates for ablation tables, plots, and concise findings.

## Expected Outputs

- the run sources included in the analysis
- the metric and ranking direction
- the varying parameters or grouping keys
- a ranked table, grouped comparison, plot path, or concise findings summary
