# History Inspection

History support is local and source-aware:

- MLflow: looks for JSON history artifacts under the run artifact root, typically files like `*history*.json`.
- W&B offline: reads the history rows embedded in the offline `.wandb` file.

Selection rules:

- If multiple MLflow history JSONs exist, prefer the non-empty candidate with the largest number of rows and surface the chosen path plus the candidate list in inspection output.
- For W&B offline runs, match on run ID plus project and group when possible so history lookups do not cross project boundaries silently.

Limitations:

- If an MLflow run logged only summary metrics and no JSON history artifact, trajectory inspection will be unavailable.
- Mixed-source comparisons remain useful for summary metrics, but trajectory resolution can differ across backends.
