#!/usr/bin/env python3
"""Convert an experiment-runner manifest into a Slurm array script and task map."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex

from slurm_utils import load_array_runs, render_array_script


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan a Slurm job array from a manifest.")
    parser.add_argument("manifest", help="Path to experiment-runner manifest.json")
    parser.add_argument("--job-name", default="array-job")
    parser.add_argument("--partition")
    parser.add_argument("--time", default="01:00:00")
    parser.add_argument("--cpus-per-task", type=int, default=4)
    parser.add_argument("--mem", default="16G")
    parser.add_argument("--gpus", type=int, default=0)
    parser.add_argument("--output-root", default="slurm-array-logs")
    parser.add_argument("--env-setup", action="append", default=[])
    parser.add_argument("--script-out", help="Optional array sbatch output path")
    parser.add_argument("--task-map-out", help="Optional task-map output path")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    runs = load_array_runs(manifest_path)
    if not runs:
        raise SystemExit("Manifest contains no runs; refusing to generate an empty Slurm array.")
    task_lines = [
        " && ".join(
            [
                f"cd {shlex.quote(run['workdir'])}",
                f'export PYTHONPATH="{run["workdir"]}:${{PYTHONPATH:-}}"',
                shlex.join(run["command"]),
            ]
        )
        for run in runs
    ]
    task_map_path = (
        Path(args.task_map_out).resolve()
        if args.task_map_out
        else manifest_path.parent / "slurm-array-tasks.txt"
    )

    script = render_array_script(
        job_name=args.job_name,
        task_count=len(runs),
        time=args.time,
        cpus_per_task=args.cpus_per_task,
        mem=args.mem,
        gpus=args.gpus,
        partition=args.partition,
        output_root=args.output_root,
        task_map_path=str(task_map_path),
        env_setup=args.env_setup,
    )
    script_path = (
        Path(args.script_out).resolve()
        if args.script_out
        else manifest_path.parent / "slurm-array.sbatch"
    )

    if args.task_map_out:
        task_map_path.parent.mkdir(parents=True, exist_ok=True)
        task_map_path.write_text("\n".join(task_lines) + "\n", encoding="utf-8")
    if args.script_out:
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(script, encoding="utf-8")

    payload = {
        "manifest": str(manifest_path),
        "task_count": len(runs),
        "script_path": str(script_path),
        "task_map_path": str(task_map_path),
        "script": script,
        "task_lines_preview": task_lines[: min(5, len(task_lines))],
        "wrote_files": bool(args.script_out or args.task_map_out),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if payload["wrote_files"]:
            print(f"Array script: {payload['script_path']}")
            print(f"Task map: {payload['task_map_path']}")
        else:
            print(script)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
