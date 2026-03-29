# Workflow

- Start with `leaderboard.py` to identify the ranking surface and varying parameters.
- Use `compare_run_pair.py` when the question is "did candidate X beat baseline Y?" rather than "who won overall?"
- Use `inspect_histories.py` whenever artifact-backed history exists; summary metrics alone can hide instability.
- Use `benchmark_report.py` for concise researcher-facing notes after the metric and source scope are fixed.
