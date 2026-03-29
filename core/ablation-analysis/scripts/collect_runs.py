#!/usr/bin/env python3
"""Collect local runs into a normalized ablation-analysis payload."""

from __future__ import annotations

from ablation_utils import build_parser, load_runs_from_args
from local_run_utils import run_to_dict, varying_param_values  # type: ignore[import-not-found]


def main() -> int:
    parser = build_parser("Collect local runs for ablation analysis.")
    args = parser.parse_args()
    runs = load_runs_from_args(args)

    payload = {
        "run_count": len(runs),
        "sources": sorted({run.source for run in runs}),
        "varying_params": varying_param_values(runs),
        "runs": [run_to_dict(run) for run in runs],
    }

    if args.json:
        import json

        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Collected {payload['run_count']} runs from {', '.join(payload['sources']) or 'no sources'}.")
        if payload["varying_params"]:
            print("Varying parameters:")
            for key in sorted(payload["varying_params"]):
                print(f"- {key}: {payload['varying_params'][key]}")
        for run in runs:
            print(f"- {run.source}: {run.name or run.run_id} ({run.run_id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
