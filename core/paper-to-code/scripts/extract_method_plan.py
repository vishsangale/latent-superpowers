#!/usr/bin/env python3
"""Extract a structured method plan from a paper summary file."""

from __future__ import annotations

import argparse
import json

from paper_plan_utils import build_method_plan, plan_to_dict


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract a method plan from a paper summary.")
    parser.add_argument("summary", help="Path to a markdown or text summary")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    plan = plan_to_dict(build_method_plan(args.summary))
    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(f"title: {plan['title']}")
        print(f"source_path: {plan['source_path']}")
        print("sections:")
        for key, values in plan["sections"].items():
            if values:
                print(f"- {key}: {len(values)} item(s)")
        if plan["missing_details"]:
            print("missing_details:")
            for item in plan["missing_details"]:
                print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
