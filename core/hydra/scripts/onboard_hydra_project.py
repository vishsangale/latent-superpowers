#!/usr/bin/env python3
"""
Inspect a non-Hydra project and produce an onboarding plan.
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
    detect_project_stack,
    discover_hydra_project,
    discover_python_entrypoints,
    find_existing_config_dirs,
    identify_training_files,
)


def build_plan(repo: Path, config_root: str, config_name: str) -> dict[str, object]:
    discovery = discover_hydra_project(repo)
    stack = detect_project_stack(repo)
    entrypoint_candidates = discover_python_entrypoints(repo)
    training_files = identify_training_files(repo)
    config_dirs = find_existing_config_dirs(repo)

    already_hydra = discovery["likely_hydra_project"]
    recommended_entrypoint = None
    if discovery["entrypoints"]:
        recommended_entrypoint = discovery["entrypoints"][0]["path"]
    elif entrypoint_candidates:
        recommended_entrypoint = entrypoint_candidates[0]["path"]

    proposed_files = [
        f"{config_root}/{config_name}.yaml",
        f"{config_root}/hydra.yaml",
    ]

    integration_steps = []
    if already_hydra:
        integration_steps.extend(
            [
                "Inspect the existing Hydra entrypoint and config root before adding new files.",
                "Normalize the project's current override and output-directory conventions.",
                "Add missing config groups or reproducibility metadata instead of re-onboarding Hydra from scratch.",
            ]
        )
    else:
        integration_steps.extend(
            [
                "Choose a primary training entrypoint and wrap it with @hydra.main.",
                f"Create a config root at {config_root} and seed {config_name}.yaml with the current default arguments.",
                "Move hard-coded training parameters into Hydra config fields and keep only thin CLI logic in Python.",
                "Add a hydra.yaml file for output-directory, job-name, and sweep-directory conventions.",
                "Decide early whether launcher and sweeper plugins are local-only or cluster-aware.",
            ]
        )

    test_plan = [
        f"Run a dry inspection: python3 {recommended_entrypoint or '<entrypoint>'} --config-path {config_root} --config-name {config_name} --cfg job --resolve",
        "Run one no-op or shortest-path training command through Hydra and confirm output lands in a predictable directory.",
        "Run one override that changes a scalar field and one override that changes a config-group selection.",
        "If multirun will be used, test a two-choice sweep and verify run naming and output layout.",
        "Confirm .hydra/config.yaml, .hydra/hydra.yaml, and .hydra/overrides.yaml are produced and sufficient for recovery.",
    ]

    warnings = []
    if not recommended_entrypoint:
        warnings.append("No obvious Python entrypoint found; onboarding will require manual entrypoint selection.")
    if config_dirs:
        warnings.append("Existing config-like directories were found; avoid introducing a second competing config root.")
    if stack["lightning"]:
        warnings.append("PyTorch Lightning is present; check for existing config or trainer abstractions before refactoring arguments.")
    if stack["transformers"]:
        warnings.append("Transformers is present; check for argument classes or TrainingArguments that Hydra should wrap rather than replace.")

    return {
        "repo": str(repo),
        "already_hydra": already_hydra,
        "recommended_entrypoint": recommended_entrypoint,
        "entrypoint_candidates": entrypoint_candidates,
        "training_files": training_files,
        "existing_config_dirs": config_dirs,
        "stack": stack,
        "recommended_config_root": config_root,
        "recommended_config_name": config_name,
        "proposed_files": proposed_files,
        "integration_steps": integration_steps,
        "test_plan": test_plan,
        "warnings": warnings,
        "hydra_discovery": discovery,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Produce a Hydra onboarding plan for a repository.")
    parser.add_argument("repo", nargs="?", default=".", help="Repository root")
    parser.add_argument("--config-root", default="conf", help="Recommended Hydra config root")
    parser.add_argument("--config-name", default="train", help="Recommended primary Hydra config name")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    result = build_plan(repo, args.config_root, args.config_name)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"Repository: {result['repo']}")
    print(f"Already Hydra-enabled: {'yes' if result['already_hydra'] else 'no'}")
    print(f"Recommended entrypoint: {result['recommended_entrypoint'] or 'manual selection required'}")
    if result["existing_config_dirs"]:
        print(f"Existing config directories: {', '.join(result['existing_config_dirs'])}")
    print("Detected stack:")
    for key, value in result["stack"].items():
        if value:
            print(f"- {key}")
    if not any(result["stack"].values()):
        print("- no strong framework signal detected")
    if result["entrypoint_candidates"]:
        print("Entrypoint candidates:")
        for candidate in result["entrypoint_candidates"][:5]:
            print(f"- {candidate['path']}: {', '.join(candidate['reasons'])}")
    print("Integration plan:")
    for step in result["integration_steps"]:
        print(f"- {step}")
    print("Test plan:")
    for step in result["test_plan"]:
        print(f"- {step}")
    if result["warnings"]:
        print("Warnings:")
        for warning in result["warnings"]:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
