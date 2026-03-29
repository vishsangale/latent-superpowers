#!/usr/bin/env python3
"""Rank local runs under an explicit benchmark metric."""

from __future__ import annotations

import json

from benchmark_utils import build_parser, leaderboard_payload, load_runs_from_args


def main() -> int:
    parser = build_parser("Build a local benchmark leaderboard.")
    args = parser.parse_args()

    runs = load_runs_from_args(args)
    payload = leaderboard_payload(runs, metric=args.metric, direction=args.direction, limit=args.limit)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Run count: {payload['run_count']}")
        print(f"Metric: {payload['metric']} ({payload['direction']})")
        for index, run in enumerate(payload["runs"], start=1):
            print(
                f"{index}. run_id={run['run_id']} source={run['source']} "
                f"{args.metric}={run['metrics'].get(args.metric)}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
