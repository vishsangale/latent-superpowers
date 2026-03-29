#!/usr/bin/env python3
"""Compare multiple saved command profiles."""

from __future__ import annotations

import argparse
import json

from profile_utils import compare_profile_rows, load_profile


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare multiple profile JSON files.")
    parser.add_argument("profiles", nargs="+", help="Profile JSON paths")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    payloads = []
    for path in args.profiles:
        payload = load_profile(path)
        payload["_path"] = path
        payloads.append(payload)
    rows = compare_profile_rows(payloads)
    payload = {"profile_count": len(rows), "rows": rows}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for index, row in enumerate(rows, start=1):
            print(
                f"{index}. {row['path']} wall={row['wall_time_sec']} rss_mb={row['peak_rss_mb']} cpu={row['avg_cpu_percent']} gpu={row['gpu_mean_utilization']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
