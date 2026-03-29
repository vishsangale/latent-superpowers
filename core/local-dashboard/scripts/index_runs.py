#!/usr/bin/env python3
"""Build a normalized run index for the local dashboard."""

from __future__ import annotations

import argparse
import json

from dashboard_data_utils import (
    load_dashboard_state,
    load_workspace_state,
    serializable_state,
    workspace_payload,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Index local runs for the dashboard.")
    parser.add_argument("--results-root", help="Workspace results root with per-project manifests")
    parser.add_argument("--mlflow-uri", help="MLflow tracking URI")
    parser.add_argument("--mlflow-experiment-name", help="MLflow experiment name")
    parser.add_argument("--mlflow-experiment-id", help="MLflow experiment ID")
    parser.add_argument("--wandb-path", action="append", default=[], help="Offline W&B run path")
    parser.add_argument("--wandb-project", help="Offline W&B project filter")
    parser.add_argument("--wandb-group", help="Offline W&B group filter")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.results_root:
        state = load_workspace_state(results_root=args.results_root)
        payload = workspace_payload(state)
    else:
        state = load_dashboard_state(
            mlflow_uri=args.mlflow_uri,
            mlflow_experiment_name=args.mlflow_experiment_name,
            mlflow_experiment_id=args.mlflow_experiment_id,
            wandb_paths=args.wandb_path or None,
            wandb_project=args.wandb_project,
            wandb_group=args.wandb_group,
        )
        payload = serializable_state(state)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if args.results_root:
            print(
                f"Indexed {len(payload['projects'])} project(s) from {payload['results_root'] or args.results_root}."
            )
        else:
            print(f"Indexed {payload['run_count']} runs from {', '.join(payload['sources']) or 'no sources'}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
