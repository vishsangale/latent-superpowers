#!/usr/bin/env python3
"""
Render or reconstruct an effective Hydra config for a target command.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from hydra_repo_utils import discover_hydra_project


def resolve_entrypoint(repo: Path, explicit_entrypoint: str | None, pick_first: bool) -> tuple[dict | None, list[dict]]:
    discovery = discover_hydra_project(repo)
    entrypoints = discovery["entrypoints"]

    if explicit_entrypoint:
        normalized = explicit_entrypoint.strip()
        for entry in entrypoints:
            if entry["path"] == normalized or entry["path"].endswith(normalized):
                return entry, entrypoints
        return {
            "path": normalized,
            "kind": "manual",
            "config_path": None,
            "config_name": None,
            "resolved_config_root": None,
        }, entrypoints

    if not entrypoints:
        return None, entrypoints
    if len(entrypoints) == 1 or pick_first:
        return entrypoints[0], entrypoints
    return None, entrypoints


def build_dry_run_command(
    repo: Path,
    entrypoint: dict,
    python_bin: str,
    cfg_scope: str,
    config_path: str | None,
    config_name: str | None,
    overrides: list[str],
) -> list[str]:
    entrypoint_path = entrypoint["path"]
    command = [python_bin]
    if entrypoint_path.endswith(".py") or (repo / entrypoint_path).exists():
        command.append(entrypoint_path)
    else:
        command.extend(["-m", entrypoint_path])

    if config_path:
        command.extend(["--config-path", config_path])
    if config_name:
        command.extend(["--config-name", config_name])

    command.extend(["--cfg", cfg_scope, "--resolve"])
    command.extend(overrides)
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description="Render an effective Hydra config.")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--entrypoint", help="Entrypoint script or module")
    parser.add_argument("--config-path", help="Optional config path override")
    parser.add_argument("--config-name", help="Optional config name override")
    parser.add_argument(
        "--cfg-scope",
        default="job",
        choices=["job", "hydra", "all"],
        help="Hydra --cfg scope for dry-run output",
    )
    parser.add_argument("--python-bin", default="python3", help="Python executable to use")
    parser.add_argument("--execute", action="store_true", help="Run the dry-run command")
    parser.add_argument("--pick-first", action="store_true", help="Pick the first detected entrypoint")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("overrides", nargs="*", help="Hydra overrides")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    entrypoint, discovered = resolve_entrypoint(repo, args.entrypoint, args.pick_first)
    if entrypoint is None:
        if discovered:
            print("Multiple Hydra entrypoints detected. Re-run with --entrypoint or --pick-first.", file=sys.stderr)
            for item in discovered:
                print(f"- {item['path']}:{item['line']}", file=sys.stderr)
            return 2
        print("No Hydra entrypoint detected. Use --entrypoint to specify one manually.", file=sys.stderr)
        return 2

    effective_config_path = args.config_path or entrypoint.get("config_path")
    effective_config_name = args.config_name or entrypoint.get("config_name")
    command = build_dry_run_command(
        repo=repo,
        entrypoint=entrypoint,
        python_bin=args.python_bin,
        cfg_scope=args.cfg_scope,
        config_path=effective_config_path,
        config_name=effective_config_name,
        overrides=args.overrides,
    )

    result = {
        "repo": str(repo),
        "selected_entrypoint": entrypoint,
        "effective_config_path": effective_config_path,
        "effective_config_name": effective_config_name,
        "cfg_scope": args.cfg_scope,
        "overrides": args.overrides,
        "dry_run_command": command,
        "executed": args.execute,
    }

    if args.execute:
        completed = subprocess.run(
            command,
            cwd=repo,
            text=True,
            capture_output=True,
            check=False,
        )
        result["exit_code"] = completed.returncode
        result["stdout"] = completed.stdout
        result["stderr"] = completed.stderr

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if not args.execute or result.get("exit_code") == 0 else result["exit_code"]

    print(f"Repository: {result['repo']}")
    print(f"Entrypoint: {entrypoint['path']}")
    print(f"Config path: {effective_config_path or 'not provided'}")
    print(f"Config name: {effective_config_name or 'not provided'}")
    print(f"Dry-run command: {shlex.join(command)}")
    if args.execute:
        print(f"Exit code: {result['exit_code']}")
        if result["stdout"]:
            print("Stdout:")
            print(result["stdout"].rstrip())
        if result["stderr"]:
            print("Stderr:", file=sys.stderr)
            print(result["stderr"].rstrip(), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
