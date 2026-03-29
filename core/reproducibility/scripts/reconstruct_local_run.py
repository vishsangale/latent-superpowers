#!/usr/bin/env python3
"""Reconstruct a local MLflow or W&B run into a concise reproducibility report."""

from __future__ import annotations

import argparse
import json

from repro_utils import reconstruct_run


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconstruct a local tracked run.")
    parser.add_argument("run_id", help="Run ID to reconstruct")
    parser.add_argument("--mlflow-uri", help="MLflow tracking URI")
    parser.add_argument("--mlflow-experiment-name", help="MLflow experiment name")
    parser.add_argument("--mlflow-experiment-id", help="MLflow experiment ID")
    parser.add_argument("--wandb-path", action="append", default=[], help="Path containing W&B offline runs")
    parser.add_argument("--wandb-project", help="Filter W&B project")
    parser.add_argument("--wandb-group", help="Filter W&B group")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    try:
        payload = reconstruct_run(
            args.run_id,
            mlflow_uri=args.mlflow_uri,
            mlflow_experiment_name=args.mlflow_experiment_name,
            mlflow_experiment_id=args.mlflow_experiment_id,
            wandb_paths=args.wandb_path or None,
            wandb_project=args.wandb_project,
            wandb_group=args.wandb_group,
        )
    except KeyError as exc:
        raise SystemExit(str(exc))
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"Run {payload['run']['run_id']} source={payload['run']['source']} "
            f"history_count={payload['history_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
