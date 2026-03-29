#!/usr/bin/env python3
"""Detect overlap or leakage across train, validation, and test splits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dataset_utils import build_json_flag, validate_splits


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate split overlap across train, val, and test files.")
    parser.add_argument("train")
    parser.add_argument("val")
    parser.add_argument("test")
    parser.add_argument("--id-key", action="append", default=[], help="Preferred ID key. May be repeated.")
    build_json_flag(parser)
    args = parser.parse_args()

    payload = validate_splits(
        Path(args.train),
        Path(args.val),
        Path(args.test),
        id_keys=args.id_key or None,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"ID key: {payload['id_key']}")
        print(f"Blocked: {payload['blocked']}")
        print(f"Overlap: {payload['overlap']}")
        print(f"Leakage detected: {payload['leakage_detected']}")
        if payload["warnings"]:
            print(f"Warnings: {payload['warnings']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
