# MLflow Workflow

Use this skill to inspect MLflow tracking state without mutating it.

## Practical flow

1. Resolve the tracking URI first.
2. Determine whether the store is file-backed or remote.
3. Select an experiment by name or ID.
4. Compare runs under an explicit metric.
5. Inspect artifacts only after the target run is known.

## Notes

- File-backed local stores are the easiest to inspect deterministically.
- Remote tracking servers may expose more metadata, but they require network and auth that this local skill does not assume.
