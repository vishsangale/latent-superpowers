#!/usr/bin/env python3
"""
Recover Hydra run provenance from an output directory.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from hydra_repo_utils import find_hydra_run_dir, load_run_metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Recover Hydra run config provenance.")
    parser.add_argument("run_dir", help="Hydra run directory or child path")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    requested = Path(args.run_dir).resolve()
    run_dir = find_hydra_run_dir(requested)
    if run_dir is None:
        print(f"No Hydra run directory found at or above {requested}", file=sys.stderr)
        return 2

    result = {
        "requested_path": str(requested),
        **load_run_metadata(run_dir),
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"Requested path: {result['requested_path']}")
    print(f"Hydra run directory: {result['run_dir']}")
    print(f"Hydra metadata directory: {result['hydra_dir'] or 'missing'}")
    print("Metadata files:")
    for key, value in result["metadata_files"].items():
        print(f"- {key}: {value or 'missing'}")
    print(f"Overrides ({len(result['overrides'])}):")
    for override in result["overrides"]:
        print(f"- {override}")
    if result["top_level_config_keys"]:
        print(f"Top-level config keys: {', '.join(result['top_level_config_keys'])}")
    if result["runtime_summary"]:
        print("Runtime summary:")
        for key, value in result["runtime_summary"].items():
            if value is not None:
                print(f"- {key}: {value}")
    print(f"Checkpoint candidates ({len(result['checkpoint_candidates'])}):")
    for candidate in result["checkpoint_candidates"]:
        print(f"- {candidate}")
    if result["reproducibility_gaps"]:
        print("Reproducibility gaps:")
        for gap in result["reproducibility_gaps"]:
            print(f"- {gap}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
