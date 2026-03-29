#!/usr/bin/env python3
"""Map a method plan onto a repo and identify gaps."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from paper_plan_utils import build_method_plan, load_plan, repo_gap_map


def main() -> int:
    parser = argparse.ArgumentParser(description="Map a method plan onto a repository.")
    parser.add_argument("plan_or_summary", help="Path to a method-plan JSON or raw summary text file")
    parser.add_argument("--repo", required=True, help="Repository path to inspect")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    source = Path(args.plan_or_summary)
    if source.suffix == ".json":
        plan = load_plan(str(source))
    else:
        plan = json.loads(json.dumps(build_method_plan(str(source)).__dict__))
    gap_map = repo_gap_map(plan, args.repo)

    if args.json:
        print(json.dumps(gap_map, indent=2, sort_keys=True))
    else:
        print(f"repo_path: {gap_map['repo_path']}")
        print(f"missing_components: {gap_map['missing_components']}")
        print("top_matches:")
        for row in gap_map["top_matches"][:10]:
            print(f"- {row['path']} ({row['match_count']} matches)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
