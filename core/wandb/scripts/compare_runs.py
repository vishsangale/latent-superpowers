#!/usr/bin/env python3
"""Compare local W&B offline runs under explicit filters and metrics."""

from __future__ import annotations

import argparse
import json
from typing import Any

from wandb_run_utils import filter_runs, load_offline_runs, metric_value, run_to_dict, varying_config_keys


def _sort_key(run_metric: Any, direction: str) -> tuple[int, float]:
    if run_metric is None:
        return (1, 0.0)
    numeric = float(run_metric)
    return (0, -numeric if direction == "max" else numeric)


def _render_text(
    runs: list[dict[str, Any]],
    *,
    metric: str | None,
    direction: str,
    varying_keys: dict[str, list[Any]],
) -> str:
    lines = [f"Found {len(runs)} matching run{'s' if len(runs) != 1 else ''}."]
    if metric:
        lines.append(f"Ranking metric: {metric} ({direction})")

    for index, run in enumerate(runs, start=1):
        summary = run["flat_summary"]
        config = run["flat_config"]
        parts = [
            f"{index}. run_id={run['run_id']}",
            f"project={run['project']}",
        ]
        if run.get("group"):
            parts.append(f"group={run['group']}")
        if metric:
            parts.append(f"{metric}={summary.get(metric)}")
        lines.append(" | ".join(parts))
        differing = [
            f"{key}={config[key]}"
            for key in sorted(varying_keys)
            if key in config
        ]
        if differing:
            lines.append(f"   differing config: {', '.join(differing)}")
        lines.append(f"   path: {run['path']}")

    if varying_keys:
        lines.append("Varying config keys:")
        for key, values in sorted(varying_keys.items()):
            lines.append(f"- {key}: {values}")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare local W&B offline runs.")
    parser.add_argument(
        "--offline-dir",
        action="append",
        default=[],
        help="Directory to scan recursively for run-*.wandb files.",
    )
    parser.add_argument(
        "--run-path",
        action="append",
        default=[],
        help="Explicit path to a run-*.wandb file.",
    )
    parser.add_argument("--project", help="Filter by W&B project")
    parser.add_argument("--group", help="Filter by W&B run group")
    parser.add_argument("--metric", help="Ranking metric from run summary")
    parser.add_argument(
        "--direction",
        choices=["min", "max"],
        default="max",
        help="Optimization direction for the ranking metric.",
    )
    parser.add_argument("--limit", type=int, default=10, help="Maximum runs to print.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("runs", nargs="*", help="Optional run IDs to keep.")
    args = parser.parse_args()

    roots = [*args.offline_dir, *args.run_path]
    runs = load_offline_runs(roots or None)
    filtered = filter_runs(
        runs,
        project=args.project,
        group=args.group,
        run_ids=set(args.runs) if args.runs else None,
    )

    ranked = filtered
    if args.metric:
        ranked = sorted(
            filtered,
            key=lambda run: _sort_key(metric_value(run, args.metric), args.direction),
        )
    ranked = ranked[: args.limit]

    payload = {
        "run_count": len(filtered),
        "project": args.project,
        "group": args.group,
        "metric": args.metric,
        "direction": args.direction,
        "varying_config_keys": varying_config_keys(filtered),
        "runs": [run_to_dict(run) for run in ranked],
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            _render_text(
                payload["runs"],
                metric=args.metric,
                direction=args.direction,
                varying_keys=payload["varying_config_keys"],
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
