#!/usr/bin/env python3
"""Read TensorBoard event logs into a lightweight JSON schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

from tensorboard.backend.event_processing.event_accumulator import EventAccumulator


def _discover_run_dirs(paths: list[str]) -> list[tuple[Path, Path]]:
    roots = [Path(path).expanduser().resolve() for path in paths]
    discovered: list[tuple[Path, Path]] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for event_file in sorted(root.rglob("events.out.tfevents.*")):
            run_dir = event_file.parent.resolve()
            if run_dir in seen:
                continue
            seen.add(run_dir)
            discovered.append((root, run_dir))
    return discovered


def _parse_name_params(name: str) -> dict[str, Any]:
    params: dict[str, Any] = {}
    seed_match = re.search(r"_s(\d+)$", name)
    if seed_match:
        params["train.seed"] = int(seed_match.group(1))
    epsilon_match = re.search(r"_e([0-9.]+)", name)
    if epsilon_match:
        try:
            params["epsilon"] = float(epsilon_match.group(1))
        except ValueError:
            params["epsilon"] = epsilon_match.group(1)
    for dataset in ("fmnist", "cifar10"):
        if dataset in name.lower():
            params["dataset"] = dataset
    variant = re.sub(r"_(e[0-9.]+|s\d+)$", "", name)
    if variant != name:
        params["variant"] = variant
    return params


def _load_run(root: Path, run_dir: Path) -> dict[str, Any]:
    accumulator = EventAccumulator(str(run_dir))
    accumulator.Reload()
    scalar_tags = accumulator.Tags().get("scalars", [])
    metrics: dict[str, float] = {}
    history_count = 0
    start_time = None
    end_time = None
    for tag in scalar_tags:
        values = accumulator.Scalars(tag)
        if not values:
            continue
        history_count = max(history_count, len(values))
        metrics[tag.replace("/", ".")] = float(values[-1].value)
        wall_times = [event.wall_time for event in values]
        first = min(wall_times)
        last = max(wall_times)
        start_time = first if start_time is None else min(start_time, first)
        end_time = last if end_time is None else max(end_time, last)

    relative = run_dir.relative_to(root)
    group = relative.parts[0] if len(relative.parts) > 1 else None
    name = run_dir.name
    return {
        "source": "tensorboard",
        "project": None,
        "experiment": group,
        "run_id": str(relative).replace("/", "__"),
        "name": name,
        "group": group,
        "status": "finished" if metrics else "unknown",
        "start_time": start_time,
        "end_time": end_time,
        "metrics": metrics,
        "params": _parse_name_params(name),
        "tags": {
            "tensorboard.root": str(root),
            "tensorboard.relative_dir": str(relative),
            "tensorboard.scalar_tags": scalar_tags,
        },
        "artifact_root": str(run_dir),
        "path": str(run_dir),
        "history_count": history_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Load TensorBoard runs into JSON.")
    parser.add_argument("--path", action="append", default=[], required=True)
    args = parser.parse_args()

    runs = [_load_run(root, run_dir) for root, run_dir in _discover_run_dirs(args.path)]
    print(json.dumps({"runs": runs}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
