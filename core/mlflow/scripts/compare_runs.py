#!/usr/bin/env python3
"""Compare MLflow runs under an explicit metric and experiment filter."""

from __future__ import annotations

import argparse
import json
import os
from typing import Any

from mlflow_store_utils import discover_experiments, discover_runs, filter_runs, normalize_tracking_uri, run_to_dict


def _sort_key(metric_value: float | None, direction: str) -> tuple[int, float]:
    if metric_value is None:
        return (1, 0.0)
    return (0, -metric_value if direction == "max" else metric_value)


def _varying_params(runs: list[dict[str, Any]]) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for run in runs:
        for key, value in run["params"].items():
            bucket = values.setdefault(key, [])
            if value not in bucket:
                bucket.append(value)
    return {key: sorted(value) for key, value in values.items() if len(value) > 1}


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare MLflow runs.")
    parser.add_argument("--tracking-uri", help="MLflow tracking URI override")
    parser.add_argument("--experiment-id", help="Filter by experiment ID")
    parser.add_argument("--experiment-name", help="Filter by experiment name")
    parser.add_argument("--metric", required=True, help="Ranking metric")
    parser.add_argument("--direction", choices=["min", "max"], default="max")
    parser.add_argument("--limit", type=int, default=10)
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
    payload_runs.sort(
        key=lambda run: _sort_key(
            float(run["metrics"][args.metric]) if args.metric in run["metrics"] else None,
            args.direction,
        )
    )
    payload = {
        "metric": args.metric,
        "direction": args.direction,
        "run_count": len(filtered),
        "varying_params": _varying_params(payload_runs),
        "runs": payload_runs[: args.limit],
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Found {payload['run_count']} matching run{'s' if payload['run_count'] != 1 else ''}.")
        print(f"Ranking metric: {args.metric} ({args.direction})")
        for index, run in enumerate(payload["runs"], start=1):
            print(f"{index}. run_id={run['run_id']} {args.metric}={run['metrics'].get(args.metric)}")
            if payload["varying_params"]:
                differing = {
                    key: run["params"][key]
                    for key in sorted(payload["varying_params"])
                    if key in run["params"]
                }
                if differing:
                    print(f"   differing params: {differing}")
            print(f"   path: {run['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
