#!/usr/bin/env python3
"""Create a snapshot manifest for a local dataset root."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dataset_utils import build_json_flag, snapshot_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="Snapshot a local dataset root.")
    parser.add_argument("path", help="Dataset root or file")
    parser.add_argument("--out", help="Optional manifest output path")
    build_json_flag(parser)
    args = parser.parse_args()

    payload = snapshot_dataset(Path(args.path))
    if args.out:
        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        print(str(out_path))
        return 0
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Files: {payload['file_count']} Total bytes: {payload['total_size_bytes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
