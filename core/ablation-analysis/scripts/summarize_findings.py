#!/usr/bin/env python3
"""Produce a concise Markdown ablation summary."""

from __future__ import annotations

import json

from ablation_utils import (
    build_parser,
    group_runs,
    grouped_payload,
    load_runs_from_args,
    markdown_findings,
    parse_variant_keys,
)
from local_run_utils import varying_param_values  # type: ignore[import-not-found]


def main() -> int:
    parser = build_parser("Summarize local ablation findings.")
    parser.add_argument("--metric", required=True, help="Metric to summarize")
    parser.add_argument("--direction", choices=["min", "max"], default="max")
    parser.add_argument("--variant-key", action="append", default=[], help="Group by this parameter")
    args = parser.parse_args()

    runs = load_runs_from_args(args)
    variant_keys = parse_variant_keys(args.variant_key)
    rows = grouped_payload(group_runs(runs, variant_keys), args.metric, direction=args.direction)
    findings = markdown_findings(
        metric=args.metric,
        direction=args.direction,
        grouped_rows=rows,
        varying_params=varying_param_values(runs),
    )

    payload = {
        "metric": args.metric,
        "direction": args.direction,
        "variant_keys": variant_keys,
        "findings_markdown": findings,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(findings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
