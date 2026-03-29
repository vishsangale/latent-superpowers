#!/usr/bin/env python3
"""Summarize Slurm stdout or stderr logs into coarse failure categories."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from slurm_utils import summarize_log


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize Slurm logs.")
    parser.add_argument("logs", nargs="+", help="Log file paths")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    payload = {"logs": [summarize_log(Path(path)) for path in args.logs]}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for row in payload["logs"]:
            print(f"{row['path']}: {row['classification']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
