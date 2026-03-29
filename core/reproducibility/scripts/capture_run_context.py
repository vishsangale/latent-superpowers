#!/usr/bin/env python3
"""Capture local reproducibility context into a JSON snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from repro_utils import capture_context


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture repo, git, Python, and env context.")
    parser.add_argument("repo", nargs="?", default=".", help="Repository root")
    parser.add_argument("--command", help="Command text associated with the capture")
    parser.add_argument("--env-key", action="append", default=[], help="Environment key to include")
    parser.add_argument("--out", help="Optional JSON output path")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    payload = capture_context(Path(args.repo), command=args.command, env_keys=args.env_key or None)
    if args.out:
        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        print(str(out_path))
        return 0
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Commit: {payload['git']['commit']} dirty={payload['git']['dirty']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
