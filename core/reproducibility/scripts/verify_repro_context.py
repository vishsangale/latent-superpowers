#!/usr/bin/env python3
"""Verify the current repo/runtime against a saved reproducibility context."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from repro_utils import verify_context


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify current state against a saved reproducibility context.")
    parser.add_argument("context", help="Saved context JSON path")
    parser.add_argument("--repo", default=".", help="Repository root to verify")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    saved = json.loads(Path(args.context).read_text(encoding="utf-8"))
    payload = verify_context(saved, Path(args.repo))
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Matches: {payload['matches']}")
        if payload["blocking_issues"]:
            print(f"Blocking issues: {payload['blocking_issues']}")
        if payload["mismatches"]:
            print(f"Mismatches: {sorted(payload['mismatches'])}")
    return 0 if payload["matches"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
