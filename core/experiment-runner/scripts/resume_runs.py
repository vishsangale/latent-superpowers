#!/usr/bin/env python3
"""Resume failed or missing runs from an experiment-runner manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiment_runner_utils import (
    append_result,
    execute_run,
    load_manifest,
    load_result_records,
    result_index,
    summarize_results,
    validate_non_negative_limit,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Resume failed or incomplete runs from a manifest.")
    parser.add_argument("manifest", help="Path to manifest.json")
    parser.add_argument("--max-runs", type=int, help="Resume at most N runs")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()
    validate_non_negative_limit(args.max_runs, flag_name="--max-runs")

    manifest_path = Path(args.manifest).resolve()
    out_dir = manifest_path.parent
    manifest = load_manifest(manifest_path)
    results_path = out_dir / "results.jsonl"
    existing = load_result_records(results_path)
    indexed = result_index(existing)

    pending = [
        run
        for run in manifest["runs"]
        if run["run_key"] not in indexed or indexed[run["run_key"]]["status"] != "success"
    ]
    if args.max_runs is not None:
        pending = pending[: args.max_runs]

    new_records: list[dict[str, object]] = []
    for run in pending:
        record = execute_run(run, out_dir)
        append_result(out_dir, record)
        new_records.append(record)

    combined = existing + new_records
    summary = summarize_results(manifest, combined)
    summary["resumed_count"] = len(new_records)
    summary["manifest_path"] = str(manifest_path)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            f"Resumed {summary['resumed_count']} runs. "
            f"Success={summary['success_count']} Failure={summary['failure_count']} Missing={len(summary['missing_runs'])}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
