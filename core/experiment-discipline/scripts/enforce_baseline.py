#!/usr/bin/env python3
"""Interactive prompt to enforce baseline clarity."""

import argparse

def main():
    parser = argparse.ArgumentParser(description="Enforce baseline comparison.")
    parser.add_argument("--result", required=True, help="The new result achieved")
    args = parser.parse_args()

    print(f"Result presented: {args.result}")
    print("\n[MANDATORY] Please ensure your report includes:")
    print("1. What was the exact baseline compared against?")
    print("2. Is the baseline a current SOTA or a strawman?")
    print("3. Was a proper ablation performed if multiple factors changed?")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
