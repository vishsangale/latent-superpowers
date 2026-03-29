#!/usr/bin/env python3
"""Profile a local command and save a profile JSON."""

from __future__ import annotations

import argparse
import json

from profile_utils import profile_command, write_profile


def main() -> int:
    parser = argparse.ArgumentParser(description="Profile a local command.")
    parser.add_argument("--out", required=True, help="Output JSON path")
    parser.add_argument("--cwd", help="Working directory for the profiled command")
    parser.add_argument("--sample-interval", type=float, default=0.25)
    parser.add_argument("--gpu-sample-interval", type=float, default=1.0)
    parser.add_argument("--shell", action="store_true", help="Run command through the shell")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable summary JSON")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to profile")
    args = parser.parse_args()

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SystemExit("No command provided to profile.")

    payload = profile_command(
        command,
        cwd=args.cwd,
        sample_interval=args.sample_interval,
        gpu_sample_interval=args.gpu_sample_interval,
        shell=args.shell,
    )
    destination = write_profile(args.out, payload)

    summary = {
        "out_path": str(destination),
        "exit_code": payload["exit_code"],
        "wall_time_sec": payload["wall_time_sec"],
        "peak_rss_mb": payload["peak_rss_mb"],
        "gpu_summary": payload["gpu_summary"],
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Profile written to {destination}")
        print(f"exit_code: {payload['exit_code']}")
        print(f"wall_time_sec: {payload['wall_time_sec']:.3f}")
        print(f"peak_rss_mb: {payload['peak_rss_mb']}")
        print(f"gpu_summary: {payload['gpu_summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
