# Workflow

- Start with `inspect_dataset_project.py` on the repo before touching dataset files. It answers whether the repo even has real data entrypoints and whether they import cleanly.
- Use `profile_dataset.py` on concrete local files or roots to understand schema, row counts, and null patterns.
- Use `validate_splits.py` before trusting a benchmark split; leakage is a research bug, not a housekeeping detail.
- Use `snapshot_dataset.py` after the data state is known-good so future runs can refer to an explicit manifest.
