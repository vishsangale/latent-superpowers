#!/usr/bin/env python3
"""Inspect a repo for dataset entrypoints, pipeline imports, and missing dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dataset_utils import build_json_flag, inspect_dataset_project


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect dataset entrypoints and imports in a repo.")
    parser.add_argument("repo", nargs="?", default=".", help="Repository root")
    parser.add_argument("--check-imports", action="store_true", help="Attempt to import detected dataset modules")
    build_json_flag(parser)
    args = parser.parse_args()

    payload = inspect_dataset_project(Path(args.repo), check_imports=args.check_imports)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Dataset scripts: {payload['dataset_scripts']}")
        print(f"Dataset choices: {payload['dataset_choices']}")
        print(f"Pipeline modules: {payload['pipeline_modules']}")
        if payload["import_checks"]:
            print(f"Import checks: {payload['import_checks']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
