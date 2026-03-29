# Tracking URI

MLflow tracking can point at:

- a local directory such as `./mlruns`
- a file URI such as `file:///path/to/mlruns`
- an HTTP(S) tracking server

## Recommended order

1. Explicit CLI `--tracking-uri`
2. `MLFLOW_TRACKING_URI`
3. local `./mlruns`

## Limits

- The current skill primarily inspects file-backed tracking stores.
- Remote URIs are surfaced in context output, but full remote API inspection is not implemented yet.
