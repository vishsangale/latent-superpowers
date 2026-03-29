#!/usr/bin/env python3
"""
Explain where a composed Hydra config value comes from.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from hydra_repo_utils import compose_config_with_history, discover_hydra_project, get_nested_value


def choose_config_context(repo: Path, config_root: str | None, config_name: str | None) -> tuple[str | None, str | None]:
    if config_root and config_name:
        return config_root, config_name

    discovery = discover_hydra_project(repo)
    entrypoints = discovery["entrypoints"]
    if entrypoints:
        chosen = entrypoints[0]
        return config_root or chosen.get("resolved_config_root"), config_name or chosen.get("config_name")

    config_roots = discovery["config_roots"]
    if config_roots:
        root = config_root or config_roots[0]["path"]
        candidates = config_roots[0]["top_level_configs"]
        fallback_name = config_name
        if fallback_name is None:
            fallback_name = "train"
            if "train.yaml" in candidates:
                fallback_name = "train"
            elif candidates:
                fallback_name = Path(candidates[0]).stem
        return root, fallback_name

    return config_root, config_name


def main() -> int:
    parser = argparse.ArgumentParser(description="Explain the origin of a Hydra config value.")
    parser.add_argument("target", help="Dotted config path to explain, for example trainer.lr")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--config-root", help="Hydra config root")
    parser.add_argument("--config-name", help="Hydra config name without or with .yaml")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("overrides", nargs="*", help="Hydra overrides to apply before explaining")
    if hasattr(parser, "parse_intermixed_args"):
        args = parser.parse_intermixed_args()
    else:
        args = parser.parse_args()

    repo = Path(args.repo).resolve()
    config_root, config_name = choose_config_context(repo, args.config_root, args.config_name)
    if not config_root or not config_name:
        print("Unable to resolve config root and config name. Pass --config-root and --config-name.", file=sys.stderr)
        return 2

    composition = compose_config_with_history(repo / config_root, config_name, args.overrides)
    final_value = get_nested_value(composition["composed"], args.target)
    history = composition["history"].get(args.target, [])

    result = {
        "repo": str(repo),
        "config_root": config_root,
        "config_name": config_name,
        "target": args.target,
        "final_value": final_value,
        "history": history,
        "files_loaded": composition["files_loaded"],
        "missing_files": composition["missing_files"],
        "group_overrides_applied": composition["group_overrides_applied"],
        "value_overrides_applied": composition["value_overrides_applied"],
        "unresolved_overrides": composition["unresolved_overrides"],
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"Repository: {result['repo']}")
    print(f"Config root: {config_root}")
    print(f"Config name: {config_name}")
    print(f"Target: {args.target}")
    print(f"Final value: {final_value!r}")
    print(f"Files loaded ({len(result['files_loaded'])}):")
    for path in result["files_loaded"]:
        print(f"- {path}")
    if history:
        print("Origin history:")
        for item in history:
            print(f"- {item['source']}: {item['value']!r}")
    else:
        print("Origin history: no direct assignments found for this dotted path")
    if result["missing_files"]:
        print("Missing referenced files:")
        for path in result["missing_files"]:
            print(f"- {path}")
    if result["unresolved_overrides"]:
        print("Unresolved overrides:")
        for raw in result["unresolved_overrides"]:
            print(f"- {raw}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
