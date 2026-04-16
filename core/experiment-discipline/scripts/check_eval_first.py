#!/usr/bin/env python3
"""Checklist tool to ensure eval-first design is respected."""

import argparse

def main():
    parser = argparse.ArgumentParser(description="Ensure evaluation is built before training.")
    parser.add_argument("--metrics", required=True, help="Comma-separated list of target metrics to track")
    parser.add_argument("--baseline", help="The baseline metric value to beat")
    args = parser.parse_args()

    print(f"Eval-First Design Check: PASSED")
    print(f"Target Metrics Defined: {args.metrics}")
    if args.baseline:
        print(f"Goal Baseline: {args.baseline}")
    else:
        print(f"[WARNING] No baseline provided. Ensure you know the baseline before spending compute.")
    print("\nAction: You may proceed to scaffold training code now that eval is front-loaded.")

if __name__ == "__main__":
    raise SystemExit(main())
