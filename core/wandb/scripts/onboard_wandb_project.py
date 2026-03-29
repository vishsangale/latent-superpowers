#!/usr/bin/env python3
"""Inspect a repository and produce a W&B onboarding plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from wandb_repo_utils import (  # noqa: E402
    detect_config_surfaces,
    detect_project_stack,
    detect_wandb_files,
    discover_python_entrypoints,
    identify_training_files,
)


def build_plan(repo: Path) -> dict[str, object]:
    stack = detect_project_stack(repo)
    entrypoints = discover_python_entrypoints(repo)
    training_files = identify_training_files(repo)
    wandb_files = detect_wandb_files(repo)
    config_surfaces = detect_config_surfaces(repo)

    already_wandb = any(
        path.endswith(("wandb_logger.py", "conf/wandb/default.yaml")) or "wandb.init(" in path
        for path in wandb_files
    )
    recommended_entrypoint = entrypoints[0]["path"] if entrypoints else None
    likely_logger_hook = next(
        (
            path
            for path in training_files
            if path.endswith(".py")
            and not path.endswith("__init__.py")
            and ("trainer" in path.lower() or path.endswith("wandb_logger.py"))
        ),
        None,
    )
    if not likely_logger_hook:
        likely_logger_hook = next(
            (
                path
                for path in training_files
                if path.endswith(".py")
                and not path.endswith("__init__.py")
                and ("train" in path.lower() or "experiment" in path.lower())
            ),
            None,
        )

    proposed_files: list[str] = []
    if not any(path.endswith("conf/wandb/default.yaml") for path in wandb_files):
        proposed_files.append("conf/wandb/default.yaml")
    if not any(path.endswith("wandb_logger.py") for path in wandb_files):
        proposed_files.append("package/training/wandb_logger.py")

    if already_wandb:
        integration_steps = [
            "Inspect the current wandb.init path and keep W&B initialization behind a small wrapper module.",
            "Verify the config surface exposes project, entity, mode, group, tags, and job_type explicitly.",
            "Confirm the trainer logs per-step metrics, terminal summary metrics, and cleanly calls finish().",
            "Add artifact logging only where checkpoints or evaluation bundles need explicit lineage.",
            "Keep offline mode available for tests and local debugging even if online mode is the default in production.",
        ]
    else:
        integration_steps = [
            "Add wandb as an optional dependency and decide whether the project defaults to offline or online mode.",
            "Create a thin W&B logger wrapper instead of scattering wandb.init and log calls across training code.",
            "Add a config surface for project, entity, mode, group, tags, and artifact behavior.",
            "Initialize W&B in the primary training entrypoint or trainer setup path, then log summary metrics at the end of training.",
            "Document the shortest successful offline command before adding online sync or sweep behavior.",
        ]

    test_plan = [
        "Run the shortest training or evaluation command with W&B enabled in offline mode.",
        "Verify a local offline-run directory is created under the configured wandb output path.",
        "Inspect the resulting run summary and confirm the ranking metric is present.",
        "If artifacts are expected, log one small artifact and verify its producer run and manifest via artifact lineage inspection.",
        "Run compare-runs or summarize-sweep over at least two local runs to verify grouping and metric selection are coherent.",
    ]

    warnings: list[str] = []
    if not recommended_entrypoint:
        warnings.append("No obvious CLI or Python entrypoint was detected; onboarding will need manual entrypoint selection.")
    if len(entrypoints) > 1:
        warnings.append("Multiple entrypoint candidates were found; choose one canonical training command before wiring W&B.")
    if not stack["hydra"] and not config_surfaces:
        warnings.append("No strong config surface was detected; add a stable config entrypoint before expanding W&B options.")
    if any("tensorboard" in path.lower() for path in training_files):
        warnings.append("TensorBoard-like logging may already exist; decide whether W&B wraps or replaces the current metrics sink.")

    return {
        "repo": str(repo),
        "already_wandb_enabled": already_wandb,
        "recommended_entrypoint": recommended_entrypoint,
        "likely_logger_hook": likely_logger_hook,
        "entrypoint_candidates": entrypoints,
        "training_files": training_files,
        "wandb_related_files": wandb_files,
        "config_surfaces": config_surfaces,
        "stack": stack,
        "proposed_files": proposed_files,
        "integration_steps": integration_steps,
        "test_plan": test_plan,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Produce a W&B onboarding plan for a repository.")
    parser.add_argument("repo", nargs="?", default=".", help="Repository root")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    result = build_plan(repo)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"Repository: {result['repo']}")
    print(f"Already W&B-enabled: {'yes' if result['already_wandb_enabled'] else 'no'}")
    print(f"Recommended entrypoint: {result['recommended_entrypoint'] or 'manual selection required'}")
    print(f"Likely logger hook: {result['likely_logger_hook'] or 'manual selection required'}")
    if result["config_surfaces"]:
        print("Config surfaces:")
        for path in result["config_surfaces"][:10]:
            print(f"- {path}")
    if result["wandb_related_files"]:
        print("Existing W&B-related files:")
        for path in result["wandb_related_files"][:10]:
            print(f"- {path}")
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
