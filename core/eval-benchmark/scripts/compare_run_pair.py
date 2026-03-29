#!/usr/bin/env python3
"""Compare a candidate run against a baseline run."""

from __future__ import annotations

import argparse
import json

from benchmark_utils import build_parser, differing_params, find_run, load_runs_from_args, metric_deltas


def main() -> int:
    parser = build_parser("Compare a candidate run against a baseline.")
    parser.add_argument("--candidate", required=True, help="Candidate run ID")
    parser.add_argument("--baseline", required=True, help="Baseline run ID")
    args = parser.parse_args()

    runs = load_runs_from_args(args)
    candidate = find_run(runs, args.candidate)
    baseline = find_run(runs, args.baseline)
    payload = {
        "candidate": candidate.run_id,
        "baseline": baseline.run_id,
        "metric": args.metric,
        "metric_deltas": metric_deltas(candidate, baseline),
        "differing_params": differing_params(candidate, baseline),
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        primary = payload["metric_deltas"].get(args.metric, {})
        print(
            f"{candidate.run_id} vs {baseline.run_id}: "
            f"{args.metric} delta={primary.get('delta')}"
        )
        if payload["differing_params"]:
            print(f"Differing params: {sorted(payload['differing_params'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
