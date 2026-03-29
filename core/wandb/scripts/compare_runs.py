#!/usr/bin/env python3
"""
Placeholder W&B run comparison helper.
"""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare W&B runs.")
    parser.add_argument("--project", help="W&B project")
    parser.add_argument("--metric", help="Ranking metric")
    parser.add_argument("--direction", choices=["min", "max"], help="Optimization direction")
    parser.add_argument("runs", nargs="*", help="Optional run IDs")
    args = parser.parse_args()

    print("TODO: compare W&B runs")
    print(f"project={args.project} metric={args.metric} direction={args.direction} runs={args.runs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
