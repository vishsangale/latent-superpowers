#!/usr/bin/env python3
"""Summarize a local experiment-runner manifest and its result records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiment_runner_utils import load_manifest, load_result_records, summarize_results


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize manifest execution results.")
    parser.add_argument("manifest", help="Path to manifest.json")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    manifest = load_manifest(manifest_path)
    manifest["manifest_path"] = str(manifest_path)
    records = load_result_records(manifest_path.parent / "results.jsonl")
    summary = summarize_results(manifest, records)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            f"Run count={summary['run_count']} completed={summary['completed_count']} "
            f"success={summary['success_count']} failure={summary['failure_count']}"
        )
        if summary["best_run_key"] is not None:
            print(
                f"Best extracted avg_reward={summary['best_extracted_metric']} "
                f"({summary['best_run_key']})"
            )
        if summary["missing_runs"]:
            print(f"Missing: {', '.join(summary['missing_runs'])}")
        if summary["failed_runs"]:
            print(f"Failed: {', '.join(summary['failed_runs'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
