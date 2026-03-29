#!/usr/bin/env python3
"""Shared helpers for reproducibility commands."""

from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


COMMON_DIR = Path(__file__).resolve().parents[2] / "common"
BENCHMARK_SCRIPTS = Path(__file__).resolve().parents[2] / "eval-benchmark" / "scripts"
for candidate in (COMMON_DIR, BENCHMARK_SCRIPTS):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from benchmark_utils import load_history_details_for_run  # type: ignore[import-not-found]
from local_run_utils import load_local_runs, run_to_dict  # type: ignore[import-not-found]


def _git(repo: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def iso_now() -> str:
    return datetime.now(tz=UTC).isoformat()


def capture_context(repo: Path, *, command: str | None = None, env_keys: list[str] | None = None) -> dict[str, Any]:
    repo = repo.resolve()
    commit = _git(repo, "rev-parse", "HEAD")
    branch = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    dirty_output = _git(repo, "status", "--porcelain")
    git_available = commit is not None and branch is not None and dirty_output is not None
    return {
        "captured_at": iso_now(),
        "repo": str(repo),
        "command": command,
        "git": {
            "available": git_available,
            "commit": commit,
            "branch": branch,
            "dirty": bool(dirty_output) if dirty_output is not None else None,
        },
        "python": {
            "executable": sys.executable,
            "version": sys.version.splitlines()[0],
        },
        "env": {
            key: os.environ.get(key)
            for key in (env_keys or [])
        },
    }


def verify_context(saved: dict[str, Any], repo: Path) -> dict[str, Any]:
    current = capture_context(repo, command=saved.get("command"), env_keys=list(saved.get("env", {}).keys()))
    mismatches = diff_contexts(saved, current)
    blocking_issues = []
    if not saved.get("git", {}).get("available", False):
        blocking_issues.append("saved git state unavailable")
    if not current.get("git", {}).get("available", False):
        blocking_issues.append("current git state unavailable")
    return {
        "saved": saved,
        "current": current,
        "matches": not bool(mismatches) and not bool(blocking_issues),
        "mismatches": mismatches,
        "blocking_issues": blocking_issues,
    }


def diff_contexts(left: dict[str, Any], right: dict[str, Any]) -> dict[str, dict[str, Any]]:
    diffs: dict[str, dict[str, Any]] = {}
    for key in ("command",):
        if left.get(key) != right.get(key):
            diffs[key] = {"left": left.get(key), "right": right.get(key)}
    for section in ("git", "python", "env"):
        left_section = left.get(section, {}) or {}
        right_section = right.get(section, {}) or {}
        for key in sorted(set(left_section) | set(right_section)):
            if left_section.get(key) != right_section.get(key):
                diffs[f"{section}.{key}"] = {"left": left_section.get(key), "right": right_section.get(key)}
    return diffs


def context_schema_kind(payload: dict[str, Any]) -> str:
    if {"git", "python", "env"}.issubset(payload.keys()):
        return "context"
    if "run" in payload:
        return "reconstructed-run"
    return "unknown"


def reconstruct_run(
    run_id: str,
    *,
    mlflow_uri: str | None = None,
    mlflow_experiment_name: str | None = None,
    mlflow_experiment_id: str | None = None,
    wandb_paths: list[str] | None = None,
    wandb_project: str | None = None,
    wandb_group: str | None = None,
) -> dict[str, Any]:
    runs = load_local_runs(
        mlflow_tracking_uri=mlflow_uri,
        mlflow_experiment_name=mlflow_experiment_name,
        mlflow_experiment_id=mlflow_experiment_id,
        wandb_paths=wandb_paths,
        wandb_project=wandb_project,
        wandb_group=wandb_group,
    )
    for run in runs:
        if run.run_id != run_id:
            continue
        history_details = load_history_details_for_run(run, wandb_paths=wandb_paths)
        return {
            "run": run_to_dict(run),
            "history_count": len(history_details["history"]),
            "history_path": history_details["selected_path"],
            "history_candidates": history_details["candidate_paths"],
        }
    raise KeyError(f"Could not find run {run_id!r}")
