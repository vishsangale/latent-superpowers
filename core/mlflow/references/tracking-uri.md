# Tracking URI

MLflow tracking can point at:

- a local SQLite database such as `sqlite:///./mlflow.db`
- a local directory such as `./mlruns`
- a file URI such as `file:///path/to/mlruns`
- an HTTP(S) tracking server

## Recommended order

1. Explicit CLI `--tracking-uri`
2. `MLFLOW_TRACKING_URI`
3. local `sqlite:///./mlflow.db`
4. local `./mlruns`

## Limits

- Local SQLite is the preferred local backend for new projects.
- File-backed `./mlruns` still works for inspection, but MLflow is deprecating filesystem tracking backends.
- Remote HTTP(S) URIs are surfaced in context output. Basic experiment and run inspection works when the active Python environment has the `mlflow` package available.
