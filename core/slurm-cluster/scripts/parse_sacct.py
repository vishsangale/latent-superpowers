#!/usr/bin/env python3
"""Parse sacct output into status counts and row summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from slurm_utils import parse_sacct_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse sacct output.")
    parser.add_argument("path", help="Path to a sacct output file")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    payload = parse_sacct_text(Path(args.path).read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Status counts: {payload['status_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
