#!/usr/bin/env python3
"""Launch a local experiment matrix and persist manifest-backed logs."""

from __future__ import annotations

import json
from pathlib import Path

from experiment_runner_utils import (
    append_result,
    build_shared_parser,
    default_out_dir,
    execute_run,
    load_manifest,
    resolve_plan_from_args,
    summarize_results,
    validate_non_negative_limit,
    write_manifest,
)


def main() -> int:
    parser = build_shared_parser("Launch a local experiment matrix.")
    parser.add_argument("--out-dir", help="Output directory for manifest and logs")
    parser.add_argument("--manifest", help="Existing manifest to execute instead of planning a new one")
    parser.add_argument("--max-runs", type=int, help="Launch at most N runs")
    parser.add_argument("--continue-on-error", action="store_true", help="Keep launching after failures")
    args = parser.parse_args()
    validate_non_negative_limit(args.max_runs, flag_name="--max-runs")

    if args.manifest:
        manifest_path = Path(args.manifest).resolve()
        manifest = load_manifest(manifest_path)
        out_dir = manifest_path.parent
    else:
        manifest, _ = resolve_plan_from_args(args)
        out_dir = Path(args.out_dir).resolve() if args.out_dir else default_out_dir(Path(args.repo).resolve())
        manifest_path = write_manifest(out_dir, manifest)
        manifest["manifest_path"] = str(manifest_path)

    run_list = manifest["runs"][: args.max_runs] if args.max_runs is not None else manifest["runs"]
    records: list[dict[str, object]] = []
    for run in run_list:
        record = execute_run(run, out_dir)
        append_result(out_dir, record)
        records.append(record)
        if record["status"] != "success" and not args.continue_on_error:
            break

    summary = summarize_results(manifest, records)
    summary["out_dir"] = str(out_dir)
    summary["manifest_path"] = str(manifest_path)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            f"Executed {summary['completed_count']}/{summary['run_count']} runs "
            f"({summary['success_count']} success, {summary['failure_count']} failed)."
        )
        print(f"Manifest: {summary['manifest_path']}")
        print(f"Logs: {out_dir}")
        if summary["best_run_key"] is not None:
            print(
                f"Best extracted avg_reward: {summary['best_extracted_metric']} "
                f"({summary['best_run_key']})"
            )
        if summary["failed_runs"]:
            print(f"Failed runs: {', '.join(summary['failed_runs'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
