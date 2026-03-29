#!/usr/bin/env python3
"""Summarize one saved command profile."""

from __future__ import annotations

import argparse
import json

from profile_utils import load_profile, recommendation_lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize one profile JSON.")
    parser.add_argument("profile", help="Profile JSON path")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    profile = load_profile(args.profile)
    payload = {
        "profile": args.profile,
        "exit_code": profile.get("exit_code"),
        "wall_time_sec": profile.get("wall_time_sec"),
        "peak_rss_mb": profile.get("peak_rss_mb"),
        "avg_cpu_percent": profile.get("avg_cpu_percent"),
        "gpu_summary": profile.get("gpu_summary"),
        "recommendations": recommendation_lines(profile),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"profile: {args.profile}")
        print(f"exit_code: {payload['exit_code']}")
        print(f"wall_time_sec: {payload['wall_time_sec']}")
        print(f"peak_rss_mb: {payload['peak_rss_mb']}")
        print(f"avg_cpu_percent: {payload['avg_cpu_percent']}")
        print(f"gpu_summary: {payload['gpu_summary']}")
        for line in payload["recommendations"]:
            print(f"- {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
