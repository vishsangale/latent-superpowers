#!/usr/bin/env python3
"""Build a staged baseline implementation plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from paper_plan_utils import build_method_plan, load_plan, repo_gap_map, staged_plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a staged implementation plan from a paper summary.")
    parser.add_argument("plan_or_summary", help="Path to a method-plan JSON or raw summary text file")
    parser.add_argument("--repo", required=True, help="Repository path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    source = Path(args.plan_or_summary)
    if source.suffix == ".json":
        plan = load_plan(str(source))
    else:
        plan = json.loads(json.dumps(build_method_plan(str(source)).__dict__))
    gap_map = repo_gap_map(plan, args.repo)
    payload = staged_plan(plan, gap_map)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"title: {payload['title']}")
        for stage in payload["stages"]:
            print(f"- {stage['stage']}: {stage['goal']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
