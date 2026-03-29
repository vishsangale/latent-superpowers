#!/usr/bin/env python3
"""Compare grouped ablations under an explicit metric."""

from __future__ import annotations

import json

from ablation_utils import (
    build_parser,
    find_baseline_label,
    group_runs,
    grouped_payload,
    load_runs_from_args,
    parse_variant_keys,
    selector_to_dict,
)
from local_run_utils import varying_param_values  # type: ignore[import-not-found]


def main() -> int:
    parser = build_parser("Compare grouped ablations.")
    parser.add_argument("--metric", required=True, help="Metric used to compare variants")
    parser.add_argument("--direction", choices=["min", "max"], default="max")
    parser.add_argument(
        "--variant-key",
        action="append",
        default=[],
        help="Parameter key to group by; may be passed multiple times",
    )
    parser.add_argument(
        "--baseline",
        action="append",
        default=[],
        help="Optional baseline selector in KEY=VALUE form; may be passed multiple times",
    )
    args = parser.parse_args()

    runs = load_runs_from_args(args)
    variant_keys = parse_variant_keys(args.variant_key)
    groups = group_runs(runs, variant_keys)
    rows = grouped_payload(groups, args.metric, direction=args.direction)
    baseline_selector = selector_to_dict(args.baseline)
    baseline_label = find_baseline_label(groups, variant_keys, baseline_selector)
    baseline_row = next((row for row in rows if row["label"] == baseline_label), None)
    baseline_mean = baseline_row["summary"]["mean"] if baseline_row else None

    for row in rows:
        mean = row["summary"]["mean"]
        if mean is None or baseline_mean is None:
            row["delta_vs_baseline"] = None
        else:
            row["delta_vs_baseline"] = mean - baseline_mean

    payload = {
        "metric": args.metric,
        "direction": args.direction,
        "variant_keys": variant_keys,
        "baseline_selector": baseline_selector,
        "baseline_label": baseline_label,
        "varying_params": varying_param_values(runs),
        "rows": rows,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Grouped comparison on {args.metric} ({args.direction})")
        if baseline_label:
            print(f"Baseline: {baseline_label}")
        for index, row in enumerate(rows, start=1):
            print(
                f"{index}. {row['label']} mean={row['summary']['mean']} count={row['count']} delta_vs_baseline={row['delta_vs_baseline']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
