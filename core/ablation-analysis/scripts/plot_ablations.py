#!/usr/bin/env python3
"""Generate a local SVG plot for ablation comparisons."""

from __future__ import annotations

import json
from pathlib import Path

from ablation_utils import (
    build_parser,
    group_runs,
    grouped_payload,
    load_runs_from_args,
    parse_variant_keys,
    write_svg_bar_chart,
)


def main() -> int:
    parser = build_parser("Generate a local SVG ablation plot.")
    parser.add_argument("--metric", required=True, help="Metric to plot")
    parser.add_argument("--direction", choices=["min", "max"], default="max")
    parser.add_argument("--variant-key", action="append", default=[], help="Group by this parameter")
    parser.add_argument("--out", required=True, help="Output SVG path")
    parser.add_argument("--title", default="Ablation Comparison")
    args = parser.parse_args()

    runs = load_runs_from_args(args)
    variant_keys = parse_variant_keys(args.variant_key)
    rows = grouped_payload(group_runs(runs, variant_keys), args.metric, direction=args.direction)
    out_path = Path(args.out).resolve()
    write_svg_bar_chart(rows, metric=args.metric, out_path=out_path, title=args.title)

    payload = {
        "metric": args.metric,
        "variant_keys": variant_keys,
        "row_count": len(rows),
        "out_path": str(out_path),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Wrote {len(rows)} plotted rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
