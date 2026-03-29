#!/usr/bin/env python3
"""Plan a local experiment matrix and optionally write a manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiment_runner_utils import build_shared_parser, format_plan, resolve_plan_from_args, write_manifest


def main() -> int:
    parser = build_shared_parser("Plan a local experiment matrix.")
    parser.add_argument("--out-dir", help="Optional directory where a manifest should be written")
    args = parser.parse_args()

    payload, _ = resolve_plan_from_args(args)
    out_dir = Path(args.out_dir).resolve() if args.out_dir else None
    if out_dir:
        manifest_path = write_manifest(out_dir, payload)
        payload["manifest_path"] = str(manifest_path)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_plan(payload))
        if payload.get("manifest_path"):
            print(f"Manifest: {payload['manifest_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
