#!/usr/bin/env python3
"""List local artifacts for a specific MLflow run."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from mlflow_store_utils import (
    artifact_path_for_run,
    discover_experiments,
    discover_experiments_via_client,
    discover_runs,
    discover_runs_via_client,
    list_artifacts_via_client,
    normalize_tracking_uri,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="List local artifacts for an MLflow run.")
    parser.add_argument("run_id", help="Target MLflow run ID")
    parser.add_argument("--tracking-uri", help="MLflow tracking URI override")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    resolved_uri, store_root, mode = normalize_tracking_uri(
        args.tracking_uri or os.getenv("MLFLOW_TRACKING_URI")
    )

    artifact_files: list[str] = []
    artifact_root: Path | None = None
    if mode == "file":
        runs = discover_runs(store_root)
        run = next((run for run in runs if run.run_id == args.run_id), None)
        artifact_root = artifact_path_for_run(run) if run else None
        if artifact_root and artifact_root.exists():
            artifact_files = [
                str(path.relative_to(artifact_root))
                for path in sorted(artifact_root.rglob("*"))
                if path.is_file()
            ]
    else:
        experiments = discover_experiments_via_client(resolved_uri)
        runs = discover_runs_via_client(resolved_uri, experiments=experiments, limit=1000)
        run = next((run for run in runs if run.run_id == args.run_id), None)
        artifact_files = list_artifacts_via_client(resolved_uri, args.run_id) if run else []

    payload = {
        "run_id": args.run_id,
        "tracking_uri": resolved_uri,
        "artifact_root": str(artifact_root) if artifact_root else None,
        "artifact_count": len(artifact_files),
        "artifacts": artifact_files,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"run_id: {args.run_id}")
        print(f"artifact_root: {payload['artifact_root']}")
        print(f"artifact_count: {payload['artifact_count']}")
        for artifact in artifact_files:
            print(f"- {artifact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
