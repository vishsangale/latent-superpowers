#!/usr/bin/env python3
"""Validate generated adapters, Python syntax, and the test suite."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "tests"
ADAPTERS_DIR = ROOT / "adapters"
CORE_DIR = ROOT / "core"
CODEX_ADAPTERS_DIR = ADAPTERS_DIR / "codex"
GENERIC_ADAPTERS = {
    "claude-code": "CLAUDE.md",
    "gemini": "GEMINI.md",
    "opencode": "OPENCODE.md",
}


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=capture_output,
    )
    if completed.returncode != 0:
        if capture_output and completed.stdout:
            print(completed.stdout, end="")
        if capture_output and completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        raise SystemExit(completed.returncode)
    return completed


def python_files() -> list[str]:
    return sorted(str(path) for path in ROOT.rglob("*.py") if "__pycache__" not in path.parts)


def skill_specs() -> list[Path]:
    return sorted(CORE_DIR.glob("*/skill-spec.yaml"))


def git_tracked_repo() -> bool:
    return (ROOT / ".git").exists()


def fail(message: str) -> None:
    raise SystemExit(message)


def validate_codex_skill(skill_dir: Path) -> None:
    skill_path = skill_dir / "SKILL.md"
    yaml_path = skill_dir / "agents" / "openai.yaml"

    if not skill_path.exists():
        fail(f"Missing Codex skill file: {skill_path}")
    if not yaml_path.exists():
        fail(f"Missing Codex agent metadata: {yaml_path}")

    content = skill_path.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        fail(f"Codex skill missing frontmatter: {skill_path}")
    parts = content.split("---\n", 2)
    if len(parts) < 3:
        fail(f"Codex skill frontmatter is malformed: {skill_path}")

    frontmatter = yaml.safe_load(parts[1]) or {}
    for key in ("name", "description"):
        if not frontmatter.get(key):
            fail(f"Codex skill frontmatter missing '{key}': {skill_path}")

    required_sections = [
        "## Overview",
        "## Use This Skill When",
        "## Do Not Use This Skill For",
        "## Operating Principles",
        "## Safety Rules",
        "## Shared Commands",
        "## Shared References",
        "## Common Workflows",
        "## Expected Outputs",
    ]
    for section in required_sections:
        if section not in content:
            fail(f"Codex skill missing section '{section}': {skill_path}")

    yaml_data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    interface = yaml_data.get("interface", {})
    for key in ("display_name", "short_description", "default_prompt"):
        if not interface.get(key):
            fail(f"Codex agent metadata missing '{key}': {yaml_path}")


def validate_generic_adapter(adapter_name: str, skill_name: str) -> None:
    filename = GENERIC_ADAPTERS[adapter_name]
    path = ADAPTERS_DIR / adapter_name / skill_name / filename
    if not path.exists():
        fail(f"Missing generated {adapter_name} adapter: {path}")

    content = path.read_text(encoding="utf-8")
    required_sections = [
        "## Purpose",
        "## Use When",
        "## Avoid When",
        "## Working Rules",
        "## Safety Rules",
        "## Shared Core",
        "## Command Surface",
        "## Workflows",
        "## References",
        "## Expected Outputs",
    ]
    for section in required_sections:
        if section not in content:
            fail(f"{adapter_name} adapter missing section '{section}': {path}")


def validate_generated_adapters() -> None:
    for spec_path in skill_specs():
        skill_name = spec_path.parent.name
        validate_codex_skill(CODEX_ADAPTERS_DIR / skill_name)
        for adapter_name in GENERIC_ADAPTERS:
            validate_generic_adapter(adapter_name, skill_name)


def check_adapter_drift() -> None:
    if not git_tracked_repo():
        return

    completed = run(
        ["git", "status", "--porcelain", "--", "adapters"],
        cwd=ROOT,
        capture_output=True,
    )
    if completed.stdout.strip():
        print(completed.stdout, end="")
        fail("Generated adapters changed during validation. Regenerate adapters and commit the result.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the latent-superpowers repo.")
    parser.add_argument("--skip-generate", action="store_true", help="Skip adapter regeneration")
    parser.add_argument("--skip-py-compile", action="store_true", help="Skip Python syntax checks")
    parser.add_argument("--skip-tests", action="store_true", help="Skip pytest")
    args = parser.parse_args()

    if not args.skip_generate:
        run([sys.executable, str(ROOT / "tools" / "generate_adapters.py")], cwd=ROOT)
        check_adapter_drift()

    if not args.skip_py_compile:
        run([sys.executable, "-m", "py_compile", *python_files()])

    validate_generated_adapters()

    if not args.skip_tests:
        run([sys.executable, "-m", "pytest", str(TESTS_DIR), "-q"], cwd=ROOT)

    print("latent-superpowers validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
