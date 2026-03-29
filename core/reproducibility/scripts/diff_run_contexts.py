#!/usr/bin/env python3
"""Diff two saved reproducibility contexts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from repro_utils import context_schema_kind, diff_contexts


def main() -> int:
    parser = argparse.ArgumentParser(description="Diff two saved reproducibility contexts.")
    parser.add_argument("left")
    parser.add_argument("right")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    left = json.loads(Path(args.left).read_text(encoding="utf-8"))
    right = json.loads(Path(args.right).read_text(encoding="utf-8"))
    left_kind = context_schema_kind(left)
    right_kind = context_schema_kind(right)
    if left_kind != "context" or right_kind != "context":
        raise SystemExit(
            f"diff_run_contexts.py only supports captured context snapshots. "
            f"Got left={left_kind}, right={right_kind}."
        )
    payload = {
        "diff": diff_contexts(left, right),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Changed fields: {sorted(payload['diff'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
