#!/usr/bin/env python3
"""Profile local dataset files or directories."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dataset_utils import build_json_flag, profile_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Profile local dataset files or directories.")
    parser.add_argument("path", help="Dataset file or directory")
    build_json_flag(parser)
    args = parser.parse_args()

    payload = profile_path(Path(args.path))
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Path: {payload['path']}")
        if payload["type"] == "directory":
            print(f"Files: {payload['file_count']}")
        else:
            print(f"Rows: {payload['row_count']} Keys: {payload['schema_keys']}")
            if payload["warning"]:
                print(f"Warning: {payload['warning']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
