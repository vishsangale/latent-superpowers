# Artifacts

For file-backed MLflow stores, a run's `artifact_uri` usually resolves to a local directory.

## Practical expectations

- Artifact listing is straightforward when `artifact_uri` points at a local path.
- If the run does not have a local artifact root, say so explicitly.
- Remote artifact stores are out of scope for the current local inspector.
