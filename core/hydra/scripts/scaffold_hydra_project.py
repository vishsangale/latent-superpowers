#!/usr/bin/env python3
"""
Scaffold a minimal Hydra layout for a new project, with preview by default.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from hydra_repo_utils import (
    discover_hydra_project,
    discover_python_entrypoints,
    extract_argparse_defaults,
    yaml_dump,
)


def choose_entrypoint(repo: Path, explicit: str | None) -> Path | None:
    if explicit:
        candidate = (repo / explicit).resolve()
        return candidate if candidate.exists() else None
    discovery = discover_hydra_project(repo)
    if discovery["entrypoints"]:
        return (repo / discovery["entrypoints"][0]["path"]).resolve()
    candidates = discover_python_entrypoints(repo)
    if candidates:
        return (repo / candidates[0]["path"]).resolve()
    return None


def build_train_config(defaults: list[dict[str, object]]) -> dict[str, object]:
    config: dict[str, object] = {"defaults": ["_self_"]}
    if defaults:
        for item in defaults:
            name = str(item["name"])
            default = item["default"]
            config[name] = default if default is not None else "TODO"
    else:
        config.update(
            {
                "seed": 0,
                "batch_size": 32,
                "learning_rate": 0.001,
            }
        )
    return config


def build_hydra_config() -> dict[str, object]:
    return {
        "hydra": {
            "run": {"dir": "outputs/${now:%Y-%m-%d}/${now:%H-%M-%S}"},
            "sweep": {
                "dir": "multirun/${now:%Y-%m-%d}/${now:%H-%M-%S}",
                "subdir": "${hydra.job.num}",
            },
        }
    }


def build_wrapper_template(entrypoint: Path, config_root: str, config_name: str) -> str:
    module_name = entrypoint.stem if entrypoint.stem.isidentifier() else None
    import_line = f"from {module_name} import main as legacy_main" if module_name else "# TODO: import the original training entrypoint here"
    call_line = "    legacy_main()" if module_name else "    # TODO: call the original training entrypoint with cfg-derived arguments"
    return (
        "import hydra\n"
        "from omegaconf import DictConfig\n\n"
        f"{import_line}\n\n"
        f"@hydra.main(version_base=\"1.3\", config_path=\"{config_root}\", config_name=\"{config_name}\")\n"
        "def main(cfg: DictConfig) -> None:\n"
        "    # TODO: map cfg fields into the legacy training function or class.\n"
        f"{call_line}\n\n"
        "if __name__ == \"__main__\":\n"
        "    main()\n"
    )


def build_scaffold(repo: Path, entrypoint: Path | None, config_root: str, config_name: str) -> dict[str, object]:
    discovery = discover_hydra_project(repo)
    argparse_defaults = extract_argparse_defaults(entrypoint) if entrypoint else []
    root = repo / config_root
    wrapper_name = f"{(entrypoint.stem if entrypoint else 'train')}_hydra.py"
    files = {
        str((root / f"{config_name}.yaml").relative_to(repo)): yaml_dump(build_train_config(argparse_defaults)),
        str((root / "hydra.yaml").relative_to(repo)): yaml_dump(build_hydra_config()),
        wrapper_name: build_wrapper_template(entrypoint or Path("train.py"), config_root, config_name),
    }
    return {
        "repo": str(repo),
        "already_hydra": discovery["likely_hydra_project"],
        "selected_entrypoint": str(entrypoint.relative_to(repo)) if entrypoint else None,
        "config_root": config_root,
        "config_name": config_name,
        "argparse_defaults": argparse_defaults,
        "files": files,
        "test_plan": [
            f"python3 {wrapper_name} --config-path {config_root} --config-name {config_name} --cfg job --resolve",
            f"python3 {wrapper_name}",
            f"python3 {wrapper_name} learning_rate=0.0003",
            f"python3 {wrapper_name} -m seed=0,1",
        ],
    }


def apply_scaffold(scaffold: dict[str, object], repo: Path, force: bool) -> list[str]:
    written: list[str] = []
    files = scaffold["files"]
    assert isinstance(files, dict)
    for relative_path, content in files.items():
        path = repo / relative_path
        if path.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite existing file: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(content), encoding="utf-8")
        written.append(str(path.relative_to(repo)))
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a minimal Hydra project layout.")
    parser.add_argument("repo", nargs="?", default=".", help="Repository root")
    parser.add_argument("--entrypoint", help="Training entrypoint path relative to repo")
    parser.add_argument("--config-root", default="conf", help="Hydra config root to create")
    parser.add_argument("--config-name", default="train", help="Primary Hydra config name")
    parser.add_argument("--apply", action="store_true", help="Write the scaffold files")
    parser.add_argument("--force", action="store_true", help="Overwrite scaffold files if they exist")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    entrypoint = choose_entrypoint(repo, args.entrypoint)
    scaffold = build_scaffold(repo, entrypoint, args.config_root, args.config_name)

    if scaffold["already_hydra"] and args.apply and not args.force:
        print("Repo already appears to use Hydra. Re-run with --force only if you intend to overwrite scaffold paths.", file=sys.stderr)
        return 2

    written_files: list[str] = []
    if args.apply:
        written_files = apply_scaffold(scaffold, repo, args.force)
    result = {**scaffold, "applied": args.apply, "written_files": written_files}

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"Repository: {result['repo']}")
    print(f"Selected entrypoint: {result['selected_entrypoint'] or 'none detected'}")
    print(f"Hydra already present: {'yes' if result['already_hydra'] else 'no'}")
    print(f"Config root: {result['config_root']}")
    print(f"Config name: {result['config_name']}")
    print("Planned files:")
    files = result["files"]
    assert isinstance(files, dict)
    for relative_path in files:
        print(f"- {relative_path}")
    if args.apply:
        print("Written files:")
        for path in written_files:
            print(f"- {path}")
    else:
        print("Preview only. Re-run with --apply to write files.")
    print("Suggested tests:")
    for step in result["test_plan"]:
        print(f"- {step}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
