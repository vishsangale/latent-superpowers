#!/usr/bin/env python3
"""Interactive query to enforce correct citation attribution."""

import argparse

def main():
    parser = argparse.ArgumentParser(description="Ensure attribution accuracy.")
    parser.add_argument("--concept", required=True, help="The ML concept being attributed")
    args = parser.parse_args()

    print(f"Attribution check for [ {args.concept} ]")
    print("Action Required in Output:")
    print("1. Did this paper INTRODUCE the concept, or merely POPULARIZE it?")
    print("2. Are there any prior works that lay the mathematical foundation? If so, cite them.")
    print("\nReminder: Do not use generic statements like 'X was invented by Y' if Y only scaled it.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
