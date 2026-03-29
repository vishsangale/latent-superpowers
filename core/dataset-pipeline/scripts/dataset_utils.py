#!/usr/bin/env python3
"""Shared helpers for dataset-pipeline commands."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any


IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "site-packages",
    "venv",
}
DATASET_SUFFIXES = {".csv", ".jsonl", ".parquet"}
ID_KEYS = ("id", "user_id", "item_id", "session_id", "interaction_id")
CHOICES_RE = re.compile(r"choices\s*=\s*\[(.*?)\]", re.DOTALL)
STRING_RE = re.compile(r"['\"](.*?)['\"]")
IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([a-zA-Z0-9_\.]+)", re.MULTILINE)


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def iter_repo_files(repo: Path, suffixes: set[str]) -> list[Path]:
    files: list[Path] = []
    for root, dirs, filenames in os.walk(repo):
        dirs[:] = [name for name in dirs if name not in IGNORE_DIRS and not name.startswith(".")]
        root_path = Path(root)
        for filename in filenames:
            path = root_path / filename
            if path.suffix.lower() in suffixes:
                files.append(path)
    return sorted(files)


def display_path(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def parse_dataset_choices(text: str) -> list[str]:
    match = CHOICES_RE.search(text)
    if not match:
        return []
    return [item for item in STRING_RE.findall(match.group(1)) if item]


def import_targets(text: str) -> list[str]:
    modules = []
    for match in IMPORT_RE.findall(text):
        if ".data" in match or "dataset" in match or "pipeline" in match:
            modules.append(match)
    return sorted(set(modules))


def inspect_dataset_project(repo: Path, *, check_imports: bool = False) -> dict[str, Any]:
    repo = repo.resolve()
    python_files = iter_repo_files(repo, {".py"})
    dataset_scripts = [
        display_path(path, repo)
        for path in python_files
        if any(token in path.name.lower() for token in ("data", "dataset", "prepare"))
    ]
    dataset_choices: set[str] = set()
    pipeline_modules: set[str] = set()
    import_checks: dict[str, str] = {}
    for path in python_files:
        text = safe_read_text(path)
        for choice in parse_dataset_choices(text):
            dataset_choices.add(choice)
        for module in import_targets(text):
            pipeline_modules.add(module)

    if check_imports:
        import_roots = [repo]
        src_root = repo / "src"
        if src_root.exists():
            import_roots.append(src_root)
        inserted = False
        inserted_paths: list[str] = []
        for root in reversed(import_roots):
            root_str = str(root)
            if root_str not in sys.path:
                sys.path.insert(0, root_str)
                inserted_paths.append(root_str)
                inserted = True
        for module in sorted(pipeline_modules):
            try:
                importlib.import_module(module)
                import_checks[module] = "ok"
            except Exception as exc:
                import_checks[module] = f"{type(exc).__name__}: {exc}"
        if inserted:
            for inserted_path in inserted_paths:
                if inserted_path in sys.path:
                    sys.path.remove(inserted_path)

    data_files = [
        display_path(path, repo)
        for path in iter_repo_files(repo, DATASET_SUFFIXES)
    ]
    return {
        "repo": str(repo),
        "dataset_scripts": dataset_scripts,
        "dataset_choices": sorted(dataset_choices),
        "pipeline_modules": sorted(pipeline_modules),
        "import_checks": import_checks,
        "local_data_files": data_files,
    }


def _csv_rows(path: Path) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    total = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            total += 1
            rows.append(dict(row))
    return rows, total


def _jsonl_rows(path: Path) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    total = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            total += 1
            payload = json.loads(stripped)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows, total


def _parquet_rows(path: Path) -> tuple[list[dict[str, Any]], int, str | None]:
    try:
        import pyarrow.parquet as pq
    except ImportError:
        return [], 0, "pyarrow is required for Parquet profiling."
    table = pq.read_table(path)
    rows = table.to_pylist()
    return [row for row in rows if isinstance(row, dict)], len(rows), None


def load_rows(path: Path) -> tuple[list[dict[str, Any]], int, str | None]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        rows, total = _csv_rows(path)
        return rows, total, None
    if suffix == ".jsonl":
        rows, total = _jsonl_rows(path)
        return rows, total, None
    if suffix == ".parquet":
        rows, total, warning = _parquet_rows(path)
        return rows, total, warning
    raise ValueError(f"Unsupported dataset file type: {path.suffix}")


def null_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for key, value in row.items():
            if value in (None, ""):
                counts[key] = counts.get(key, 0) + 1
    return counts


def profile_path(path: Path) -> dict[str, Any]:
    path = path.resolve()
    if path.is_dir():
        files = [candidate for candidate in sorted(path.rglob("*")) if candidate.suffix.lower() in DATASET_SUFFIXES]
        return {
            "path": str(path),
            "type": "directory",
            "file_count": len(files),
            "files": [profile_path(candidate) for candidate in files],
        }

    rows, total_rows, warning = load_rows(path)
    schema_keys = sorted({key for row in rows for key in row})
    return {
        "path": str(path),
        "type": "file",
        "format": path.suffix.lower().lstrip("."),
        "row_count": total_rows,
        "schema_keys": schema_keys,
        "null_counts": null_counts(rows),
        "sample_rows": rows[:3],
        "warning": warning,
    }


def canonical_row(row: dict[str, Any]) -> str:
    return json.dumps(row, sort_keys=True, separators=(",", ":"))


def row_id_set(rows: list[dict[str, Any]], *, id_keys: list[str] | None = None) -> tuple[str, set[str]]:
    chosen_keys = id_keys or list(ID_KEYS)
    for key in chosen_keys:
        values = [row.get(key) for row in rows if key in row]
        if len(values) == len(rows):
            return key, {str(value) for value in values}
    return "__row_hash__", {hashlib.sha256(canonical_row(row).encode("utf-8")).hexdigest() for row in rows}


def validate_splits(train_path: Path, val_path: Path, test_path: Path, *, id_keys: list[str] | None = None) -> dict[str, Any]:
    train_rows, train_total, train_warning = load_rows(train_path)
    val_rows, val_total, val_warning = load_rows(val_path)
    test_rows, test_total, test_warning = load_rows(test_path)
    warnings = [warning for warning in (train_warning, val_warning, test_warning) if warning]
    if warnings:
        return {
            "id_key": None,
            "train_count": train_total,
            "val_count": val_total,
            "test_count": test_total,
            "overlap": None,
            "leakage_detected": None,
            "sample_overlap": None,
            "blocked": True,
            "warnings": warnings,
        }

    candidate_keys = id_keys or list(ID_KEYS)
    shared_key = None
    for key in candidate_keys:
        if all(rows and all(key in row for row in rows) for rows in (train_rows, val_rows, test_rows)):
            shared_key = key
            break
    if id_keys and shared_key is None:
        return {
            "id_key": None,
            "train_count": train_total,
            "val_count": val_total,
            "test_count": test_total,
            "overlap": None,
            "leakage_detected": None,
            "sample_overlap": None,
            "blocked": True,
            "warnings": [f"Requested id keys {id_keys} were not present in all splits."],
        }

    key = shared_key or "__row_hash__"
    if key == "__row_hash__":
        train_ids = {hashlib.sha256(canonical_row(row).encode("utf-8")).hexdigest() for row in train_rows}
        val_ids = {hashlib.sha256(canonical_row(row).encode("utf-8")).hexdigest() for row in val_rows}
        test_ids = {hashlib.sha256(canonical_row(row).encode("utf-8")).hexdigest() for row in test_rows}
    else:
        train_ids = {str(row[key]) for row in train_rows}
        val_ids = {str(row[key]) for row in val_rows}
        test_ids = {str(row[key]) for row in test_rows}
    train_val = sorted(train_ids & val_ids)
    train_test = sorted(train_ids & test_ids)
    val_test = sorted(val_ids & test_ids)
    return {
        "id_key": key,
        "train_count": train_total,
        "val_count": val_total,
        "test_count": test_total,
        "overlap": {
            "train_val": len(train_val),
            "train_test": len(train_test),
            "val_test": len(val_test),
        },
        "leakage_detected": any((train_val, train_test, val_test)),
        "blocked": False,
        "warnings": [],
        "sample_overlap": {
            "train_val": train_val[:5],
            "train_test": train_test[:5],
            "val_test": val_test[:5],
        },
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_dataset(root: Path) -> dict[str, Any]:
    root = root.resolve()
    if root.is_file():
        files = [root]
        base = root.parent
    else:
        files = [path for path in sorted(root.rglob("*")) if path.is_file()]
        base = root
    entries = []
    for path in files:
        entries.append(
            {
                "path": display_path(path, base),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {
        "root": str(root),
        "file_count": len(entries),
        "total_size_bytes": sum(entry["size_bytes"] for entry in entries),
        "files": entries,
    }


def build_json_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
