#!/usr/bin/env python3
"""Inspect a repo for Slurm readiness and existing cluster hints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from slurm_utils import inspect_slurm_project


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a repo for Slurm execution hints.")
    parser.add_argument("repo", nargs="?", default=".", help="Repository root")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    payload = inspect_slurm_project(Path(args.repo))
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Entrypoints: {len(payload['entrypoints'])}")
        print(f"Slurm files: {payload['slurm_files']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
