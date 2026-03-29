#!/usr/bin/env python3
"""
Detect likely Hydra usage in a repository.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from hydra_repo_utils import discover_hydra_project


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect Hydra structure in a repository.")
    parser.add_argument("repo", nargs="?", default=".", help="Repository root to inspect")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    result = discover_hydra_project(repo)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"Repository: {result['repo']}")
    print(f"Likely Hydra project: {'yes' if result['likely_hydra_project'] else 'no'}")

    entrypoints = result["entrypoints"]
    print(f"Entrypoints: {len(entrypoints)}")
    for entry in entrypoints:
        config_root = entry["resolved_config_root"] or "unknown"
        config_name = entry["config_name"] or "unknown"
        print(
            f"- {entry['path']}:{entry['line']} [{entry['kind']}] "
            f"config_root={config_root} config_name={config_name}"
        )

    compose_calls = result["compose_calls"]
    if compose_calls:
        print(f"Compose calls: {len(compose_calls)}")
        for entry in compose_calls:
            print(f"- {entry['path']}:{entry['line']} [{entry['kind']}]")

    config_roots = result["config_roots"]
    print(f"Config roots: {len(config_roots)}")
    for root in config_roots:
        print(f"- {root['path']}")
        if root["top_level_configs"]:
            print(f"  top-level configs: {', '.join(root['top_level_configs'])}")
        if root["groups"]:
            print(f"  groups: {', '.join(root['groups'])}")
        if root["launcher_options"]:
            print(f"  launcher options: {', '.join(root['launcher_options'])}")
        if root["sweeper_options"]:
            print(f"  sweeper options: {', '.join(root['sweeper_options'])}")

    if result["output_patterns"]:
        print("Output patterns:")
        for pattern in result["output_patterns"]:
            details = []
            if pattern["run_dir"] is not None:
                details.append(f"run.dir={pattern['run_dir']}")
            if pattern["sweep_dir"] is not None:
                details.append(f"sweep.dir={pattern['sweep_dir']}")
            if pattern["sweep_subdir"] is not None:
                details.append(f"sweep.subdir={pattern['sweep_subdir']}")
            print(f"- {pattern['path']}: {', '.join(details)}")

    if result["omegaconf_files"]:
        print(f"OmegaConf usage files: {len(result['omegaconf_files'])}")
        for path in result["omegaconf_files"]:
            print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
