#!/usr/bin/env python3
"""
Generate and install an adapter from latent-superpowers into a live tool directory.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys

from generate_adapters import ADAPTERS_DIR, CORE_DIR, generate_skill


DEFAULT_DEST_ROOTS = {
    "codex": Path.home() / ".codex" / "skills",
}


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def install_adapter(
    skill: str,
    adapter: str,
    dest_root: Path,
    mode: str,
    force: bool,
    generate: bool,
) -> Path:
    spec_path = CORE_DIR / skill / "skill-spec.yaml"
    if not spec_path.exists():
        raise FileNotFoundError(f"Missing skill spec: {spec_path}")

    if generate:
        generate_skill(spec_path)

    source = ADAPTERS_DIR / adapter / skill
    if not source.exists():
        raise FileNotFoundError(f"Missing generated adapter: {source}")

    dest_root.mkdir(parents=True, exist_ok=True)
    destination = dest_root / skill

    if destination.exists() or destination.is_symlink():
        if destination.is_symlink():
            try:
                if destination.resolve() == source.resolve():
                    return destination
            except FileNotFoundError:
                pass
        if not force:
            raise FileExistsError(
                f"Destination already exists: {destination}. Re-run with --force to replace it."
            )
        remove_path(destination)

    if mode == "symlink":
        destination.symlink_to(source, target_is_directory=True)
    elif mode == "copy":
        shutil.copytree(source, destination)
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Install a generated adapter into a live tool directory.")
    parser.add_argument("--skill", required=True, help="Skill name, for example hydra")
    parser.add_argument(
        "--adapter",
        required=True,
        choices=["codex", "claude-code", "gemini", "opencode"],
        help="Adapter family to install",
    )
    parser.add_argument(
        "--dest-root",
        help="Destination root directory. Defaults are only provided for supported live tools like Codex.",
    )
    parser.add_argument(
        "--mode",
        default="symlink",
        choices=["symlink", "copy"],
        help="Install by symlink or by copying files",
    )
    parser.add_argument("--force", action="store_true", help="Replace an existing destination path")
    parser.add_argument(
        "--no-generate",
        action="store_true",
        help="Skip regeneration and install the already-generated adapter",
    )
    args = parser.parse_args()

    dest_root = Path(args.dest_root).expanduser() if args.dest_root else DEFAULT_DEST_ROOTS.get(args.adapter)
    if dest_root is None:
        print(
            f"No default destination is known for adapter '{args.adapter}'. Pass --dest-root explicitly.",
            file=sys.stderr,
        )
        return 2

    destination = install_adapter(
        skill=args.skill,
        adapter=args.adapter,
        dest_root=dest_root,
        mode=args.mode,
        force=args.force,
        generate=not args.no_generate,
    )
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
