# Workflow

1. Resolve local run sources first.
   - MLflow: prefer an explicit tracking URI and experiment name.
   - W&B: point at local offline run directories and make the project explicit when possible.
2. Normalize runs before grouping them.
3. Choose one ranking metric and one direction.
4. Inspect varying parameters before drawing conclusions.
5. Group by the smallest set of factors that answers the research question.
6. Report sample counts and missing metrics with the result, not as an afterthought.

## Default local analysis order

1. `collect_runs.py`
2. `rank_variants.py`
3. `compare_ablations.py`
4. `plot_ablations.py`
5. `summarize_findings.py`
