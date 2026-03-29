#!/usr/bin/env python3
"""List MLflow runs from a local file-backed tracking store."""

from __future__ import annotations

import argparse
import json
import os

from mlflow_store_utils import (
    discover_experiments,
    discover_runs,
    filter_runs,
    normalize_tracking_uri,
    run_to_dict,
)


def _sort_value(run: dict[str, object], metric: str | None, direction: str) -> tuple[int, float]:
    if not metric:
        return (0, 0.0)
    metrics = run["metrics"]
    value = metrics.get(metric)
    if value is None:
        return (1, 0.0)
    numeric = float(value)
    return (0, -numeric if direction == "max" else numeric)


def main() -> int:
    parser = argparse.ArgumentParser(description="List MLflow runs from a local tracking store.")
    parser.add_argument("--tracking-uri", help="MLflow tracking URI override")
    parser.add_argument("--experiment-id", help="Filter by experiment ID")
    parser.add_argument("--experiment-name", help="Filter by experiment name")
    parser.add_argument("--metric", help="Sort by metric")
    parser.add_argument("--direction", choices=["min", "max"], default="max")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("runs", nargs="*", help="Optional run IDs to keep")
    args = parser.parse_args()

    _, store_root, _ = normalize_tracking_uri(args.tracking_uri or os.getenv("MLFLOW_TRACKING_URI"))
    experiments = discover_experiments(store_root)
    runs = discover_runs(store_root)
    filtered = filter_runs(
        runs,
        experiment_id=args.experiment_id,
        experiment_name=args.experiment_name,
        experiments=experiments,
        run_ids=set(args.runs) if args.runs else None,
    )
    payload_runs = [run_to_dict(run) for run in filtered]
    payload_runs.sort(key=lambda run: _sort_value(run, args.metric, args.direction))
    payload_runs = payload_runs[: args.limit]

    payload = {
        "tracking_uri": args.tracking_uri or os.getenv("MLFLOW_TRACKING_URI"),
        "experiment_id": args.experiment_id,
        "experiment_name": args.experiment_name,
        "metric": args.metric,
        "direction": args.direction,
        "run_count": len(filtered),
        "runs": payload_runs,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Found {payload['run_count']} matching run{'s' if payload['run_count'] != 1 else ''}.")
        for index, run in enumerate(payload_runs, start=1):
            line = f"{index}. run_id={run['run_id']} experiment_id={run['experiment_id']}"
            if args.metric:
                line += f" {args.metric}={run['metrics'].get(args.metric)}"
            print(line)
            if run["params"]:
                print(f"   params: {run['params']}")
            if run["tags"]:
                print(f"   tags: {run['tags']}")
            print(f"   path: {run['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
