#!/usr/bin/env python3
"""Validate generated adapters, Python syntax, and the test suite."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "core"
TESTS_DIR = ROOT / "tests"
ADAPTERS_DIR = ROOT / "adapters" / "codex"
QUICK_VALIDATE = (
    Path.home()
    / ".codex"
    / "skills"
    / ".system"
    / "skill-creator"
    / "scripts"
    / "quick_validate.py"
)


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    completed = subprocess.run(cmd, cwd=cwd, check=False, text=True)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def python_files() -> list[str]:
    return sorted(str(path) for path in ROOT.rglob("*.py") if "__pycache__" not in path.parts)


def codex_skill_dirs() -> list[Path]:
    return sorted(path.parent for path in ADAPTERS_DIR.glob("*/SKILL.md"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the latent-superpowers repo.")
    parser.add_argument("--skip-generate", action="store_true", help="Skip adapter regeneration")
    parser.add_argument("--skip-py-compile", action="store_true", help="Skip Python syntax checks")
    parser.add_argument("--skip-tests", action="store_true", help="Skip pytest")
    args = parser.parse_args()

    if not args.skip_generate:
        run([sys.executable, str(ROOT / "tools" / "generate_adapters.py")], cwd=ROOT)

    if not args.skip_py_compile:
        run([sys.executable, "-m", "py_compile", *python_files()])

    if QUICK_VALIDATE.exists():
        for skill_dir in codex_skill_dirs():
            run([sys.executable, str(QUICK_VALIDATE), str(skill_dir)])
    else:
        print(f"Skipping quick skill validation; not found at {QUICK_VALIDATE}", file=sys.stderr)

    if not args.skip_tests:
        run([sys.executable, "-m", "pytest", str(TESTS_DIR), "-q"], cwd=ROOT)

    print("latent-superpowers validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
