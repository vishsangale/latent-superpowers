#!/usr/bin/env python3
"""Repository inspection helpers for W&B onboarding."""

from __future__ import annotations

from pathlib import Path


SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    ".venv",
    ".venv-hydra",
    "venv",
    "node_modules",
    "outputs",
    "multirun",
}


def _iter_files(repo: Path, suffixes: tuple[str, ...] | None = None) -> list[Path]:
    paths: list[Path] = []
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(repo).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        if rel_parts and rel_parts[0] == "wandb":
            continue
        if suffixes and path.suffix not in suffixes:
            continue
        paths.append(path)
    return sorted(paths)


def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def discover_python_entrypoints(repo: Path) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for path in _iter_files(repo, (".py",)):
        text = read_text_safe(path)
        reasons: list[str] = []
        if "if __name__ == \"__main__\"" in text or "if __name__ == '__main__'" in text:
            reasons.append("main-guard")
        if "@hydra.main" in text:
            reasons.append("hydra-entrypoint")
        if "argparse.ArgumentParser" in text:
            reasons.append("argparse-cli")
        if "wandb.init(" in text:
            reasons.append("wandb-init")
        if reasons:
            candidates.append({"path": str(path.relative_to(repo)), "reasons": reasons})
    return candidates


def identify_training_files(repo: Path) -> list[str]:
    matches: list[str] = []
    keywords = ("train", "trainer", "experiment", "fit")
    for path in _iter_files(repo, (".py", ".yaml", ".yml", ".toml", ".md")):
        rel = str(path.relative_to(repo))
        text = read_text_safe(path)
        if any(keyword in rel.lower() for keyword in keywords):
            matches.append(rel)
            continue
        if any(keyword in text.lower() for keyword in keywords):
            matches.append(rel)
    return sorted(set(matches))


def detect_wandb_files(repo: Path) -> list[str]:
    matches: list[str] = []
    for path in _iter_files(repo, (".py", ".yaml", ".yml", ".toml", ".md", ".txt")):
        rel = str(path.relative_to(repo))
        text = read_text_safe(path)
        parts = [part.lower() for part in Path(rel).parts]
        if "wandb" in rel.lower() or "wandb" in text or "wandb" in parts:
            matches.append(rel)
    return sorted(set(matches))


def detect_config_surfaces(repo: Path) -> list[str]:
    matches: list[str] = []
    for path in _iter_files(repo, (".yaml", ".yml", ".toml", ".json")):
        rel = str(path.relative_to(repo))
        if any(part in {"conf", "config", "configs"} for part in Path(rel).parts):
            matches.append(rel)
    return sorted(set(matches))


def detect_project_stack(repo: Path) -> dict[str, bool]:
    text_blob = "\n".join(read_text_safe(path) for path in _iter_files(repo, (".py", ".toml", ".txt", ".md")))
    return {
        "hydra": "@hydra.main" in text_blob or "hydra-core" in text_blob,
        "wandb": "wandb.init(" in text_blob or "wandb" in text_blob,
        "pytorch": "torch" in text_blob,
        "lightning": "lightning" in text_blob or "pytorch_lightning" in text_blob,
        "transformers": "transformers" in text_blob,
    }
