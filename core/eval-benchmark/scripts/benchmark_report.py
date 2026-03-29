#!/usr/bin/env python3
"""Generate a concise Markdown benchmark report from local runs."""

from __future__ import annotations

import argparse
from pathlib import Path

from benchmark_utils import build_parser, find_run, load_runs_from_args, report_markdown


def main() -> int:
    parser = build_parser("Generate a Markdown benchmark report.")
    parser.add_argument("--baseline", help="Optional baseline run ID")
    parser.add_argument("--out", help="Optional Markdown output path")
    args = parser.parse_args()

    runs = load_runs_from_args(args)
    baseline = find_run(runs, args.baseline) if args.baseline else None
    markdown = report_markdown(
        runs=runs,
        metric=args.metric,
        direction=args.direction,
        baseline_run=baseline,
        limit=args.limit,
    )
    if args.out:
        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(markdown, encoding="utf-8")
        print(str(out_path))
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
