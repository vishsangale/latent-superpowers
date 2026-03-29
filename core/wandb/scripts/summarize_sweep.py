#!/usr/bin/env python3
"""
Placeholder W&B sweep summary helper.
"""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize a W&B sweep.")
    parser.add_argument("sweep", help="Sweep ID or path")
    parser.add_argument("--metric", help="Ranking metric")
    args = parser.parse_args()

    print("TODO: summarize W&B sweep")
    print(f"sweep={args.sweep} metric={args.metric}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
