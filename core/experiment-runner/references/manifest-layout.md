# Manifest Layout

- `manifest.json`: top-level plan metadata plus the full ordered run list.
- `results.jsonl`: append-only execution records with return code, timestamps, duration, log paths, and extracted metrics.
- `stdout/`: one file per run with captured stdout.
- `stderr/`: one file per run with captured stderr.

Each planned run includes:
- `run_key`: stable identifier inside the manifest
- `label`: compact human-readable variant label
- `command`: argument vector used for execution
- `command_text`: shell-joined command for logs and debugging
- `overrides`: explicit factor values applied to the run
- `seed`: resolved seed value when present

Each result record includes:
- `run_key`
- `status`
- `return_code`
- `started_at`
- `finished_at`
- `duration_seconds`
- `stdout_path`
- `stderr_path`
- `extracted_metrics`
