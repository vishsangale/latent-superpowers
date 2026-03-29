#!/usr/bin/env python3
"""Resolve MLflow context for a repository or shell session."""

from __future__ import annotations

import argparse
import json
import os

from mlflow_store_utils import discover_experiments, discover_experiments_via_client, normalize_tracking_uri


def main() -> int:
    parser = argparse.ArgumentParser(description="Check MLflow tracking context.")
    parser.add_argument("--tracking-uri", help="MLflow tracking URI override")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    resolved_uri, store_root, mode = normalize_tracking_uri(
        args.tracking_uri or os.getenv("MLFLOW_TRACKING_URI")
    )
    if mode == "file":
        experiments = discover_experiments(store_root)
    else:
        experiments = discover_experiments_via_client(resolved_uri)

    result = {
        "tracking_uri": resolved_uri,
        "registry_uri": os.getenv("MLFLOW_REGISTRY_URI"),
        "mode": mode,
        "store_root": str(store_root) if store_root else None,
        "experiment_count": len(experiments),
        "experiment_names": [experiment.name for experiment in experiments],
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
