#!/usr/bin/env python3
"""Generate a dry-run sbatch script from a repo-aware command."""

from __future__ import annotations

import json
from pathlib import Path

from slurm_utils import build_common_parser, build_sbatch_config, render_sbatch, resolve_command


def main() -> int:
    parser = build_common_parser("Generate an sbatch script.")
    parser.add_argument("--out", help="Optional sbatch output path")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    workdir = Path(args.workdir).resolve() if args.workdir else repo
    base_command, source = resolve_command(repo, workdir, args.base_command)
    config = build_sbatch_config(
        repo=repo,
        workdir=workdir,
        base_command=base_command,
        job_name=args.job_name,
        partition=args.partition,
        time=args.time,
        cpus_per_task=args.cpus_per_task,
        mem=args.mem,
        gpus=args.gpus,
        output_root=args.output_root,
        env_setup=args.env_setup,
    )
    script = render_sbatch(config)
    payload = {
        "repo": str(repo),
        "base_command": base_command,
        "base_command_source": source,
        "script": script,
    }
    if args.out:
        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(script, encoding="utf-8")
        print(str(out_path))
        return 0
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(script)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
