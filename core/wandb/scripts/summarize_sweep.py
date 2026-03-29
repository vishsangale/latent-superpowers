#!/usr/bin/env python3
"""Summarize grouped local W&B runs with ranking and parameter trends."""

from __future__ import annotations

import argparse
import json
from statistics import mean
from typing import Any

from wandb_run_utils import (
    filter_runs,
    load_offline_runs,
    metric_value,
    run_to_dict,
    varying_config_keys,
)


def _sort_key(metric: Any, direction: str) -> tuple[int, float]:
    if metric is None:
        return (1, 0.0)
    numeric = float(metric)
    return (0, -numeric if direction == "max" else numeric)


def _parameter_effects(
    complete_runs: list[dict[str, Any]],
    *,
    varying_keys: dict[str, list[Any]],
    metric: str,
) -> dict[str, dict[str, float]]:
    effects: dict[str, dict[str, float]] = {}
    for key in sorted(varying_keys):
        buckets: dict[str, list[float]] = {}
        for run in complete_runs:
            flat_config = run["flat_config"]
            flat_summary = run["flat_summary"]
            if key not in flat_config or metric not in flat_summary:
                continue
            value = flat_config[key]
            if isinstance(value, (list, dict)):
                continue
            buckets.setdefault(str(value), []).append(float(flat_summary[metric]))
        if buckets:
            effects[key] = {value: mean(values) for value, values in buckets.items()}
    return effects


def _render_text(payload: dict[str, Any]) -> str:
    lines = [
        f"Found {payload['run_count']} run{'s' if payload['run_count'] != 1 else ''} in group {payload['group']}.",
        f"Ranking metric: {payload['metric']} ({payload['direction']})",
        f"Complete runs: {payload['complete_run_count']}",
        f"Incomplete runs: {payload['incomplete_run_count']}",
    ]
    if payload["best_run"]:
        best = payload["best_run"]
        lines.append(
            "Best run: "
            f"run_id={best['run_id']} | {payload['metric']}={best['flat_summary'].get(payload['metric'])}"
        )
    if payload["incomplete_run_ids"]:
        lines.append(f"Incomplete run IDs: {', '.join(payload['incomplete_run_ids'])}")
    if payload["parameter_effects"]:
        lines.append("Parameter effects:")
        for key, values in payload["parameter_effects"].items():
            lines.append(f"- {key}: {values}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize grouped local W&B runs.")
    parser.add_argument("sweep", help="Sweep or group identifier. In offline mode this is treated as a group.")
    parser.add_argument(
        "--offline-dir",
        action="append",
        default=[],
        help="Directory to scan recursively for run-*.wandb files.",
    )
    parser.add_argument("--project", help="Filter by W&B project")
    parser.add_argument("--metric", required=True, help="Ranking metric from run summary")
    parser.add_argument(
        "--direction",
        choices=["min", "max"],
        default="max",
        help="Optimization direction for the ranking metric.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    runs = load_offline_runs(args.offline_dir or None)
    grouped = filter_runs(runs, project=args.project, group=args.sweep)
    ranked = sorted(grouped, key=lambda run: _sort_key(metric_value(run, args.metric), args.direction))
    complete = [run for run in ranked if metric_value(run, args.metric) is not None]
    incomplete = [run for run in ranked if metric_value(run, args.metric) is None]

    complete_payload = [run_to_dict(run) for run in complete]
    varying_keys = varying_config_keys(grouped)
    payload = {
        "group": args.sweep,
        "project": args.project,
        "metric": args.metric,
        "direction": args.direction,
        "run_count": len(grouped),
        "complete_run_count": len(complete),
        "incomplete_run_count": len(incomplete),
        "incomplete_run_ids": [run.run_id for run in incomplete if run.run_id],
        "best_run": complete_payload[0] if complete_payload else None,
        "ranked_runs": complete_payload,
        "parameter_effects": _parameter_effects(
            complete_payload,
            varying_keys=varying_keys,
            metric=args.metric,
        ),
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_render_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
