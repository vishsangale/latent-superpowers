#!/usr/bin/env python3
"""Helpers for discovering project manifests under a workspace results root."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ProjectManifest:
    name: str
    path: str
    repo_root: str | None
    project_results_dir: str
    mlflow_tracking_uri: str | None
    mlflow_experiment_name: str | None
    wandb_paths: list[str]
    wandb_project: str | None
    tensorboard_paths: list[str]
    tensorboard_python: str | None


def load_project_manifest(path: str | Path) -> ProjectManifest:
    manifest_path = Path(path).resolve()
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    sources = data.get("sources", {}) or {}
    mlflow = sources.get("mlflow", {}) or {}
    wandb = sources.get("wandb_offline", {}) or {}
    tensorboard = sources.get("tensorboard", {}) or {}
    return ProjectManifest(
        name=str(data.get("project_name") or manifest_path.parent.name),
        path=str(manifest_path),
        repo_root=data.get("repo_root"),
        project_results_dir=str(data.get("project_results_dir") or manifest_path.parent),
        mlflow_tracking_uri=mlflow.get("tracking_uri"),
        mlflow_experiment_name=mlflow.get("experiment_name"),
        wandb_paths=[str(item) for item in (wandb.get("paths") or [])],
        wandb_project=wandb.get("project"),
        tensorboard_paths=[str(item) for item in (tensorboard.get("paths") or [])],
        tensorboard_python=tensorboard.get("python"),
    )


def discover_project_manifests(results_root: str | Path) -> list[ProjectManifest]:
    root = Path(results_root).expanduser().resolve()
    manifests: list[ProjectManifest] = []
    if not root.exists():
        return manifests

    for manifest_path in sorted(root.glob("*/project.yaml")):
        try:
            manifests.append(load_project_manifest(manifest_path))
        except Exception:
            continue
    return manifests


def manifest_to_dict(manifest: ProjectManifest) -> dict[str, Any]:
    return {
        "name": manifest.name,
        "path": manifest.path,
        "repo_root": manifest.repo_root,
        "project_results_dir": manifest.project_results_dir,
        "mlflow_tracking_uri": manifest.mlflow_tracking_uri,
        "mlflow_experiment_name": manifest.mlflow_experiment_name,
        "wandb_paths": manifest.wandb_paths,
        "wandb_project": manifest.wandb_project,
        "tensorboard_paths": manifest.tensorboard_paths,
        "tensorboard_python": manifest.tensorboard_python,
    }
