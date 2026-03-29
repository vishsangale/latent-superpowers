#!/usr/bin/env python3
"""Rank local runs or grouped variants under an explicit metric."""

from __future__ import annotations

import json

from ablation_utils import build_parser, group_runs, grouped_payload, load_runs_from_args, parse_variant_keys
from local_run_utils import run_to_dict, varying_param_values  # type: ignore[import-not-found]


def _sort_runs(runs, metric: str, direction: str):
    reverse = direction == "max"
    ranked = [run for run in runs if metric in run.metrics]
    ranked.sort(key=lambda run: run.metrics[metric], reverse=reverse)
    return ranked


def main() -> int:
    parser = build_parser("Rank local runs or grouped variants.")
    parser.add_argument("--metric", required=True, help="Metric used to rank runs")
    parser.add_argument("--direction", choices=["min", "max"], default="max")
    parser.add_argument("--variant-key", action="append", default=[], help="Group by this parameter")
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()

    runs = load_runs_from_args(args)
    variant_keys = parse_variant_keys(args.variant_key)
    if variant_keys:
        groups = group_runs(runs, variant_keys)
        ranked_groups = grouped_payload(groups, args.metric, direction=args.direction)[: args.top]
        payload = {
            "mode": "grouped",
            "metric": args.metric,
            "direction": args.direction,
            "variant_keys": variant_keys,
            "varying_params": varying_param_values(runs),
            "rows": ranked_groups,
        }
    else:
        ranked_runs = _sort_runs(runs, args.metric, args.direction)[: args.top]
        payload = {
            "mode": "per-run",
            "metric": args.metric,
            "direction": args.direction,
            "variant_keys": [],
            "varying_params": varying_param_values(runs),
            "runs": [run_to_dict(run) for run in ranked_runs],
        }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Ranking metric: {args.metric} ({args.direction})")
        if payload["mode"] == "grouped":
            for index, row in enumerate(payload["rows"], start=1):
                print(f"{index}. {row['label']} mean={row['summary']['mean']} count={row['count']}")
        else:
            for index, run in enumerate(payload["runs"], start=1):
                print(f"{index}. {run['name'] or run['run_id']} {args.metric}={run['metrics'].get(args.metric)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
