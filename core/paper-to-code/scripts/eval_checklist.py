#!/usr/bin/env python3
"""Generate an evaluation checklist from a method plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from paper_plan_utils import build_method_plan, evaluation_items, load_plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an evaluation checklist from a method plan.")
    parser.add_argument("plan_or_summary", help="Path to a method-plan JSON or raw summary text file")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    source = Path(args.plan_or_summary)
    if source.suffix == ".json":
        plan = load_plan(str(source))
    else:
        plan = json.loads(json.dumps(build_method_plan(str(source)).__dict__))
    payload = {"title": plan["title"], "checklist": evaluation_items(plan)}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"title: {payload['title']}")
        for section, items in payload["checklist"].items():
            print(f"{section}:")
            for item in items:
                print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
