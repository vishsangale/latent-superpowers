# Metric Discipline

- Always name the metric and the ranking direction.
- Do not compare runs across incompatible objectives without saying so.
- Treat `count=1` groups as anecdotal, not stable.
- Prefer grouped means for ablation conclusions and per-run rankings for quick inspection.
- Missing metrics are a real data-quality problem, not a formatting issue.

## Common mistakes

- Mixing per-step metrics with final summary metrics.
- Ranking by a metric that only exists for a subset of runs.
- Calling a variant "better" when it only has one run and the baseline has many.
