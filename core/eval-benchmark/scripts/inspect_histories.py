#!/usr/bin/env python3
"""Inspect available local run histories from MLflow or W&B data."""

from __future__ import annotations

import argparse
import json

from benchmark_utils import build_parser, find_run, history_summary, load_history_details_for_run, load_runs_from_args, sort_runs


def main() -> int:
    parser = build_parser("Inspect benchmark histories.")
    parser.add_argument("run_ids", nargs="*", help="Specific run IDs. Defaults to the top ranked runs.")
    args = parser.parse_args()

    runs = load_runs_from_args(args)
    selected = [find_run(runs, run_id) for run_id in args.run_ids] if args.run_ids else sort_runs(runs, args.metric, args.direction)[: args.limit]
    payload = {
        "metric": args.metric,
        "runs": [],
    }
    for run in selected:
        history_details = load_history_details_for_run(run, wandb_paths=args.wandb_path or None)
        history = history_details["history"]
        payload["runs"].append(
            {
                "run_id": run.run_id,
                "source": run.source,
                "history_summary": history_summary(history),
                "selected_history_path": history_details["selected_path"],
                "candidate_history_paths": history_details["candidate_paths"],
            }
        )

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for row in payload["runs"]:
            print(
                f"{row['run_id']} source={row['source']} "
                f"history_count={row['history_summary']['history_count']} "
                f"metrics={row['history_summary']['metric_keys']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
