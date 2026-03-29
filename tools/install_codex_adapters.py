#!/usr/bin/env python3
"""Install all generated Codex adapters into ~/.codex/skills."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from install_adapter import install_adapter


ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "core"


def main() -> int:
    parser = argparse.ArgumentParser(description="Install all Codex adapters.")
    parser.add_argument("--mode", default="symlink", choices=["symlink", "copy"])
    parser.add_argument("--force", action="store_true", help="Replace existing adapters")
    parser.add_argument("--dest-root", default=str(Path.home() / ".codex" / "skills"))
    args = parser.parse_args()

    dest_root = Path(args.dest_root).expanduser()
    skills = sorted(path.parent.name for path in CORE_DIR.glob("*/skill-spec.yaml"))
    for skill in skills:
        destination = install_adapter(
            skill=skill,
            adapter="codex",
            dest_root=dest_root,
            mode=args.mode,
            force=args.force,
            generate=True,
        )
        print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
