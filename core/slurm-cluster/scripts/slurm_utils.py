#!/usr/bin/env python3
"""Shared helpers for Slurm planning and diagnostics."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shlex
from typing import Any
import sys


HYDRA_SCRIPTS = Path(__file__).resolve().parents[2] / "hydra" / "scripts"
EXPERIMENT_RUNNER_SCRIPTS = Path(__file__).resolve().parents[2] / "experiment-runner" / "scripts"
for candidate in (HYDRA_SCRIPTS, EXPERIMENT_RUNNER_SCRIPTS):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from hydra_repo_utils import discover_hydra_project  # type: ignore[import-not-found]
from experiment_runner_utils import load_manifest, resolve_base_command  # type: ignore[import-not-found]


IGNORE_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules"}
SBATCH_RE = re.compile(r"^#SBATCH\s+(.*)$", re.MULTILINE)
SACCT_SPLIT_RE = re.compile(r"\s*\|\s*")


@dataclass
class SbatchConfig:
    job_name: str
    partition: str | None
    time: str
    cpus_per_task: int
    mem: str
    gpus: int
    output_root: str
    env_setup: list[str]
    command: list[str]
    workdir: str


def display_path(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def iter_repo_files(repo: Path, suffixes: set[str]) -> list[Path]:
    files = []
    for root, dirs, filenames in os.walk(repo):
        dirs[:] = [name for name in dirs if name not in IGNORE_DIRS and not name.startswith(".")]
        root_path = Path(root)
        for filename in filenames:
            candidate = root_path / filename
            if candidate.suffix.lower() in suffixes:
                files.append(candidate)
    return sorted(files)


def inspect_slurm_project(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    hydra = discover_hydra_project(repo)
    slurm_files: list[str] = []
    sbatch_hints: list[dict[str, Any]] = []
    for candidate in iter_repo_files(repo, {".sh", ".bash", ".py", ".yaml", ".yml"}):
        text = candidate.read_text(encoding="utf-8", errors="replace")
        if "#SBATCH" in text or "sbatch " in text or "sacct " in text or "submitit" in text:
            rel = display_path(candidate, repo)
            slurm_files.append(rel)
            hints = SBATCH_RE.findall(text)
            if hints:
                sbatch_hints.append({"path": rel, "directives": hints})
    return {
        "repo": str(repo),
        "entrypoints": hydra.get("entrypoints", []),
        "config_roots": hydra.get("config_roots", []),
        "slurm_files": slurm_files,
        "sbatch_hints": sbatch_hints,
    }


def render_sbatch(config: SbatchConfig) -> str:
    lines = [
        "#!/usr/bin/env bash",
        f"#SBATCH --job-name={config.job_name}",
        f"#SBATCH --time={config.time}",
        f"#SBATCH --cpus-per-task={config.cpus_per_task}",
        f"#SBATCH --mem={config.mem}",
        f"#SBATCH --output={config.output_root}/%x-%j.out",
        f"#SBATCH --error={config.output_root}/%x-%j.err",
    ]
    if config.partition:
        lines.append(f"#SBATCH --partition={config.partition}")
    if config.gpus > 0:
        lines.append(f"#SBATCH --gpus={config.gpus}")
    lines.extend(
        [
            "",
            "set -euo pipefail",
            f"mkdir -p {shlex.quote(config.output_root)}",
            f"cd {shlex.quote(config.workdir)}",
            f'export PYTHONPATH="{config.workdir}:${{PYTHONPATH:-}}"',
        ]
    )
    lines.extend(config.env_setup)
    lines.append("")
    lines.append(shlex.join(config.command))
    return "\n".join(lines) + "\n"


def build_sbatch_config(
    *,
    repo: Path,
    workdir: Path,
    base_command: list[str],
    job_name: str,
    partition: str | None,
    time: str,
    cpus_per_task: int,
    mem: str,
    gpus: int,
    output_root: str,
    env_setup: list[str],
) -> SbatchConfig:
    return SbatchConfig(
        job_name=job_name,
        partition=partition,
        time=time,
        cpus_per_task=cpus_per_task,
        mem=mem,
        gpus=gpus,
        output_root=output_root,
        env_setup=env_setup,
        command=base_command,
        workdir=str(workdir.resolve()),
    )


def load_array_runs(manifest_path: Path) -> list[dict[str, Any]]:
    payload = load_manifest(manifest_path)
    return payload["runs"]


def render_array_script(
    *,
    job_name: str,
    task_count: int,
    time: str,
    cpus_per_task: int,
    mem: str,
    gpus: int,
    partition: str | None,
    output_root: str,
    task_map_path: str,
    env_setup: list[str],
) -> str:
    lines = [
        "#!/usr/bin/env bash",
        f"#SBATCH --job-name={job_name}",
        f"#SBATCH --array=0-{task_count - 1}",
        f"#SBATCH --time={time}",
        f"#SBATCH --cpus-per-task={cpus_per_task}",
        f"#SBATCH --mem={mem}",
        f"#SBATCH --output={output_root}/%x-%A_%a.out",
        f"#SBATCH --error={output_root}/%x-%A_%a.err",
    ]
    if partition:
        lines.append(f"#SBATCH --partition={partition}")
    if gpus > 0:
        lines.append(f"#SBATCH --gpus={gpus}")
    lines.extend(
        [
            "",
            "set -euo pipefail",
            f"mkdir -p {shlex.quote(output_root)}",
        ]
    )
    lines.extend(env_setup)
    lines.extend(
        [
            f'TASK=$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" {shlex.quote(task_map_path)})',
            'eval "$TASK"',
            "",
        ]
    )
    return "\n".join(lines)


def classify_log(text: str) -> str:
    lowered = text.lower()
    if "out of memory" in lowered or "oom" in lowered or "cgroup" in lowered and "kill" in lowered:
        return "oom"
    if "time limit" in lowered or "timelimit" in lowered:
        return "timeout"
    if "traceback (most recent call last)" in lowered:
        return "python-traceback"
    if "module not found" in lowered or "command not found" in lowered:
        return "module"
    if "node failure" in lowered or "launch failed" in lowered:
        return "node-failure"
    return "unknown"


def summarize_log(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "path": str(path),
        "classification": classify_log(text),
        "traceback_present": "Traceback (most recent call last)" in text,
        "line_count": len(text.splitlines()),
    }


def parse_sacct_text(text: str) -> dict[str, Any]:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return {"rows": [], "status_counts": {}}
    if "|" in lines[0]:
        header = [part.strip() for part in SACCT_SPLIT_RE.split(lines[0].strip()) if part.strip()]
        rows = []
        for line in lines[1:]:
            parts = [part.strip() for part in SACCT_SPLIT_RE.split(line.strip())]
            if len(parts) != len(header):
                continue
            rows.append(dict(zip(header, parts, strict=True)))
    else:
        header = lines[0].split()
        rows = []
        for line in lines[1:]:
            parts = line.split()
            if len(parts) < len(header):
                continue
            rows.append(dict(zip(header, parts[: len(header)], strict=True)))
    status_key = "State" if rows and "State" in rows[0] else "STATE"
    status_counts: dict[str, int] = {}
    for row in rows:
        state = row.get(status_key, "UNKNOWN")
        status_counts[state] = status_counts.get(state, 0) + 1
    return {
        "rows": rows,
        "status_counts": status_counts,
    }


def build_common_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("repo", nargs="?", default=".", help="Repository root")
    parser.add_argument("--workdir", help="Working directory override")
    parser.add_argument("--base-command", help="Base command string. Auto-detected from Hydra if omitted.")
    parser.add_argument("--job-name", default="job", help="Slurm job name")
    parser.add_argument("--partition", help="Partition name")
    parser.add_argument("--time", default="01:00:00", help="Time limit")
    parser.add_argument("--cpus-per-task", type=int, default=4)
    parser.add_argument("--mem", default="16G")
    parser.add_argument("--gpus", type=int, default=0)
    parser.add_argument("--output-root", default="slurm-logs")
    parser.add_argument("--env-setup", action="append", default=[], help="Shell line to add before the command")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def resolve_command(repo: Path, workdir: Path, raw_base_command: str | None) -> tuple[list[str], dict[str, Any] | None]:
    return resolve_base_command(repo, raw_base_command)
