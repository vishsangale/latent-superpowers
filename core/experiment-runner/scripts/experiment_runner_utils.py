#!/usr/bin/env python3
"""Shared helpers for planning and executing local experiment matrices."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import itertools
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
from typing import Any
import sys


HYDRA_SCRIPTS = Path(__file__).resolve().parents[2] / "hydra" / "scripts"
hydra_scripts_str = str(HYDRA_SCRIPTS)
if hydra_scripts_str not in sys.path:
    sys.path.insert(0, hydra_scripts_str)

from hydra_repo_utils import discover_hydra_project  # type: ignore[import-not-found]

AVG_REWARD_RE = re.compile(r"Average reward over \d+ episodes:\s*([-+]?\d+(?:\.\d+)?)")


@dataclass
class PlannedRun:
    run_key: str
    label: str
    command: list[str]
    command_text: str
    overrides: dict[str, str]
    seed: str | None
    repeat_index: int
    workdir: str


def iso_now() -> str:
    return datetime.now(tz=UTC).isoformat()


def parse_csv_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def parse_factor_args(raw_values: list[str] | None) -> dict[str, list[str]]:
    factors: dict[str, list[str]] = {}
    for raw in raw_values or []:
        if "=" not in raw:
            raise ValueError(f"Expected KEY=V1,V2 form, got {raw!r}")
        key, values = raw.split("=", 1)
        if key in factors:
            raise ValueError(f"Duplicate factor key {key!r}. Merge the values into one --set.")
        parsed = parse_csv_list(values)
        if not parsed:
            raise ValueError(f"Expected at least one value for factor {key!r}")
        factors[key] = parsed
    return factors


def autodetect_base_command(repo: Path) -> tuple[list[str], dict[str, Any]]:
    details = discover_hydra_project(repo)
    entrypoints = details.get("entrypoints", [])
    if not entrypoints:
        raise RuntimeError(
            f"Could not auto-detect a Hydra entrypoint in {repo}. Pass --base-command explicitly."
        )
    entrypoint = entrypoints[0]
    command = [sys.executable, str(repo / entrypoint["path"])]
    return command, entrypoint


def resolve_base_command(repo: Path, raw_base_command: str | None) -> tuple[list[str], dict[str, Any] | None]:
    if raw_base_command:
        return shlex.split(raw_base_command), None
    return autodetect_base_command(repo)


def matrix_dimensions(factors: dict[str, list[str]], seeds: list[str], repeats: int) -> dict[str, int]:
    dimensions = {key: len(values) for key, values in sorted(factors.items())}
    if seeds:
        dimensions["seeds"] = len(seeds)
    if repeats > 1:
        dimensions["repeats"] = repeats
    return dimensions


def build_plan(
    *,
    repo: Path,
    workdir: Path,
    base_command: list[str],
    factors: dict[str, list[str]],
    seed_key: str,
    seeds: list[str],
    repeats: int,
) -> list[PlannedRun]:
    if repeats <= 0:
        raise ValueError(f"--repeats must be >= 1, got {repeats}")
    factor_items = sorted(factors.items())
    key_order = [key for key, _ in factor_items]
    value_lists = [values for _, values in factor_items]
    grid = list(itertools.product(*value_lists)) if value_lists else [()]

    planned: list[PlannedRun] = []
    index = 0
    for combo in grid:
        combo_overrides = dict(zip(key_order, combo, strict=True))
        resolved_seeds = seeds or [None]
        for seed in resolved_seeds:
            overrides = dict(combo_overrides)
            if seed is not None:
                overrides[seed_key] = str(seed)
            for repeat_index in range(repeats):
                override_args = [f"{key}={value}" for key, value in sorted(overrides.items())]
                command = list(base_command) + override_args
                label_parts = [f"{key}={value}" for key, value in sorted(overrides.items())]
                if repeats > 1:
                    label_parts.append(f"repeat={repeat_index}")
                label = ", ".join(label_parts) if label_parts else "base"
                planned.append(
                    PlannedRun(
                        run_key=f"run_{index:03d}",
                        label=label,
                        command=command,
                        command_text=shlex.join(command),
                        overrides=overrides,
                        seed=str(seed) if seed is not None else None,
                        repeat_index=repeat_index,
                        workdir=str(workdir.resolve()),
                    )
                )
                index += 1
    return planned


def plan_payload(
    *,
    repo: Path,
    workdir: Path,
    base_command: list[str],
    base_command_source: dict[str, Any] | None,
    factors: dict[str, list[str]],
    seed_key: str,
    seeds: list[str],
    repeats: int,
    planned_runs: list[PlannedRun],
) -> dict[str, Any]:
    return {
        "repo": str(repo.resolve()),
        "workdir": str(workdir.resolve()),
        "created_at": iso_now(),
        "base_command": base_command,
        "base_command_text": shlex.join(base_command),
        "base_command_source": base_command_source,
        "factors": factors,
        "seed_key": seed_key,
        "seeds": seeds,
        "repeats": repeats,
        "dimensions": matrix_dimensions(factors, seeds, repeats),
        "run_count": len(planned_runs),
        "runs": [asdict(run) for run in planned_runs],
    }


def default_out_dir(repo: Path) -> Path:
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    return repo / "outputs" / "experiment-runner" / timestamp


def ensure_manifest_dir(path: Path) -> None:
    (path / "stdout").mkdir(parents=True, exist_ok=True)
    (path / "stderr").mkdir(parents=True, exist_ok=True)


def write_manifest(out_dir: Path, payload: dict[str, Any]) -> Path:
    ensure_manifest_dir(out_dir)
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return manifest_path


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_result_records(results_path: Path) -> list[dict[str, Any]]:
    if not results_path.exists():
        return []
    rows = []
    for line in results_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            rows.append(json.loads(stripped))
        except json.JSONDecodeError:
            continue
    return rows


def append_result(out_dir: Path, payload: dict[str, Any]) -> None:
    results_path = out_dir / "results.jsonl"
    with results_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True))
        handle.write("\n")


def result_index(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for record in records:
        index[record["run_key"]] = record
    return index


def extract_metrics_from_stdout(stdout_text: str) -> dict[str, float]:
    metrics: dict[str, float] = {}
    match = AVG_REWARD_RE.search(stdout_text)
    if match:
        metrics["avg_reward"] = float(match.group(1))
    return metrics


def execute_run(run: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    stdout_path = out_dir / "stdout" / f"{run['run_key']}.log"
    stderr_path = out_dir / "stderr" / f"{run['run_key']}.log"
    started_at = iso_now()
    start = datetime.now(tz=UTC)
    env = os.environ.copy()
    repo_pythonpath = run["workdir"]
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        repo_pythonpath if not existing_pythonpath else f"{repo_pythonpath}:{existing_pythonpath}"
    )
    with stdout_path.open("w", encoding="utf-8") as stdout_handle, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr_handle:
        try:
            completed = subprocess.run(
                run["command"],
                cwd=run["workdir"],
                env=env,
                stdout=stdout_handle,
                stderr=stderr_handle,
                text=True,
                check=False,
            )
            return_code = completed.returncode
        except OSError as exc:
            stderr_handle.write(f"{type(exc).__name__}: {exc}\n")
            return_code = 127
    end = datetime.now(tz=UTC)
    stdout_text = stdout_path.read_text(encoding="utf-8", errors="replace")
    finished_at = iso_now()
    return {
        "run_key": run["run_key"],
        "label": run["label"],
        "status": "success" if return_code == 0 else "failed",
        "return_code": return_code,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": round((end - start).total_seconds(), 6),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "command_text": run["command_text"],
        "extracted_metrics": extract_metrics_from_stdout(stdout_text),
    }


def build_shared_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("repo", nargs="?", default=".", help="Target repository root")
    parser.add_argument("--workdir", help="Working directory for launched commands")
    parser.add_argument("--base-command", help="Base command string. Auto-detected from Hydra if omitted.")
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        help="Factor in KEY=V1,V2 form. May be repeated.",
    )
    parser.add_argument("--seed-key", default="train.seed", help="Override key used for seeds")
    parser.add_argument("--seeds", help="Comma-separated seed list")
    parser.add_argument("--repeats", type=int, default=1, help="Repeat each matrix point N times")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def resolve_plan_from_args(args: argparse.Namespace) -> tuple[dict[str, Any], list[PlannedRun]]:
    repo = Path(args.repo).resolve()
    workdir = Path(args.workdir).resolve() if args.workdir else repo
    base_command, source = resolve_base_command(repo, args.base_command)
    factors = parse_factor_args(args.set)
    seeds = parse_csv_list(args.seeds)
    planned_runs = build_plan(
        repo=repo,
        workdir=workdir,
        base_command=base_command,
        factors=factors,
        seed_key=args.seed_key,
        seeds=seeds,
        repeats=args.repeats,
    )
    payload = plan_payload(
        repo=repo,
        workdir=workdir,
        base_command=base_command,
        base_command_source=source,
        factors=factors,
        seed_key=args.seed_key,
        seeds=seeds,
        repeats=args.repeats,
        planned_runs=planned_runs,
    )
    return payload, planned_runs


def validate_non_negative_limit(limit: int | None, *, flag_name: str) -> None:
    if limit is not None and limit < 0:
        raise ValueError(f"{flag_name} must be >= 0, got {limit}")


def format_plan(payload: dict[str, Any]) -> str:
    lines = [
        f"Base command: {payload['base_command_text']}",
        f"Workdir: {payload['workdir']}",
        f"Run count: {payload['run_count']}",
    ]
    if payload["dimensions"]:
        lines.append(f"Dimensions: {payload['dimensions']}")
    for run in payload["runs"][:10]:
        lines.append(f"- {run['run_key']}: {run['label']}")
    if payload["run_count"] > 10:
        lines.append(f"... {payload['run_count'] - 10} more run(s)")
    return "\n".join(lines)


def summarize_results(manifest: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    indexed = result_index(records)
    latest_records = list(indexed.values())
    successes = [record for record in latest_records if record.get("status") == "success"]
    failures = [record for record in latest_records if record.get("status") != "success"]
    missing = [run["run_key"] for run in manifest["runs"] if run["run_key"] not in indexed]
    best_record = None
    candidates = [
        record
        for record in successes
        if "avg_reward" in record.get("extracted_metrics", {})
    ]
    if candidates:
        best_record = max(
            candidates,
            key=lambda item: item.get("extracted_metrics", {}).get("avg_reward", float("-inf")),
        )
    return {
        "manifest_path": manifest.get("manifest_path"),
        "run_count": manifest["run_count"],
        "completed_count": len(latest_records),
        "success_count": len(successes),
        "failure_count": len(failures),
        "missing_runs": missing,
        "best_extracted_metric": (
            best_record.get("extracted_metrics", {}).get("avg_reward") if best_record else None
        ),
        "best_run_key": best_record["run_key"] if best_record else None,
        "failed_runs": [record["run_key"] for record in failures],
    }
