#!/usr/bin/env python3
"""Shared helpers for ablation-analysis commands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
import statistics
import sys


COMMON_DIR = Path(__file__).resolve().parents[2] / "common"
common_dir_str = str(COMMON_DIR)
if common_dir_str not in sys.path:
    sys.path.insert(0, common_dir_str)

from local_run_utils import (  # type: ignore[import-not-found]
    NormalizedRun,
    load_local_runs,
    metric_summary,
    run_label,
    run_to_dict,
    varying_param_values,
)


def build_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--mlflow-uri", help="MLflow tracking URI")
    parser.add_argument("--mlflow-experiment-name", help="MLflow experiment name")
    parser.add_argument("--mlflow-experiment-id", help="MLflow experiment ID")
    parser.add_argument(
        "--wandb-path",
        action="append",
        default=[],
        help="Path containing local offline W&B runs; may be passed multiple times",
    )
    parser.add_argument("--wandb-project", help="Filter offline W&B runs by project")
    parser.add_argument("--wandb-group", help="Filter offline W&B runs by group")
    parser.add_argument("--limit-per-source", type=int, default=1000)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def load_runs_from_args(args: argparse.Namespace) -> list[NormalizedRun]:
    return load_local_runs(
        mlflow_tracking_uri=args.mlflow_uri,
        mlflow_experiment_name=args.mlflow_experiment_name,
        mlflow_experiment_id=args.mlflow_experiment_id,
        wandb_paths=args.wandb_path or None,
        wandb_project=args.wandb_project,
        wandb_group=args.wandb_group,
        limit_per_source=args.limit_per_source,
    )


def parse_variant_keys(raw_values: list[str] | None) -> list[str]:
    return [value for value in (raw_values or []) if value]


def group_runs(runs: list[NormalizedRun], variant_keys: list[str]) -> dict[str, list[NormalizedRun]]:
    groups: dict[str, list[NormalizedRun]] = {}
    for run in runs:
        label = run_label(run, variant_keys if variant_keys else None)
        groups.setdefault(label, []).append(run)
    return groups


def grouped_payload(
    groups: dict[str, list[NormalizedRun]],
    metric: str,
    *,
    direction: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label, grouped_runs in groups.items():
        summary = metric_summary(grouped_runs, metric)
        best_run = _best_run(grouped_runs, metric, direction)
        rows.append(
            {
                "label": label,
                "count": len(grouped_runs),
                "metric": metric,
                "summary": summary,
                "best_run_id": best_run.run_id if best_run else None,
                "best_run_name": best_run.name if best_run else None,
                "runs": [run_to_dict(run) for run in grouped_runs],
            }
        )
    rows.sort(key=lambda row: _sort_group_row(row, direction))
    return rows


def _best_run(runs: list[NormalizedRun], metric: str, direction: str) -> NormalizedRun | None:
    candidates = [run for run in runs if metric in run.metrics]
    if not candidates:
        return None
    reverse = direction == "max"
    return sorted(candidates, key=lambda run: run.metrics[metric], reverse=reverse)[0]


def _sort_group_row(row: dict[str, Any], direction: str) -> tuple[int, float]:
    mean = row["summary"]["mean"]
    if mean is None:
        return (1, 0.0)
    numeric = float(mean)
    return (0, -numeric if direction == "max" else numeric)


def selector_to_dict(items: list[str] | None) -> dict[str, str]:
    selector: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise ValueError(f"Expected KEY=VALUE selector, got {item!r}")
        key, value = item.split("=", 1)
        selector[key] = value
    return selector


def find_baseline_label(
    groups: dict[str, list[NormalizedRun]],
    variant_keys: list[str],
    selector: dict[str, str],
) -> str | None:
    if not selector:
        return None
    for label, grouped_runs in groups.items():
        run = grouped_runs[0]
        if all(str(run.params.get(key)) == value for key, value in selector.items()):
            return label
    return None


def markdown_findings(
    *,
    metric: str,
    direction: str,
    grouped_rows: list[dict[str, Any]],
    varying_params: dict[str, list[Any]],
) -> str:
    lines = [f"# Ablation Findings", "", f"- metric: `{metric}` ({direction})"]
    if grouped_rows:
        winner = grouped_rows[0]
        lines.append(
            f"- top variant: `{winner['label']}` with mean `{winner['summary']['mean']}` over `{winner['count']}` run(s)"
        )
    if varying_params:
        lines.append("- varying parameters:")
        for key in sorted(varying_params):
            lines.append(f"  - `{key}`: {varying_params[key]}")
    lines.extend(["", "## Variant Table", "", "| Variant | Count | Mean | Min | Max | Stddev |", "| --- | ---: | ---: | ---: | ---: | ---: |"])
    for row in grouped_rows:
        summary = row["summary"]
        lines.append(
            f"| {row['label']} | {row['count']} | {_fmt(summary['mean'])} | {_fmt(summary['min'])} | {_fmt(summary['max'])} | {_fmt(summary['stddev'])} |"
        )
    return "\n".join(lines)


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def dump_payload(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        raise RuntimeError("Text rendering should be handled by the caller.")


def write_svg_bar_chart(
    rows: list[dict[str, Any]],
    *,
    metric: str,
    out_path: Path,
    title: str,
) -> None:
    width = 1000
    height = 80 + (len(rows) * 50)
    left_pad = 260
    bar_max = max((row["summary"]["mean"] or 0.0) for row in rows) if rows else 1.0
    bar_max = bar_max or 1.0

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<style>',
        "text { font-family: monospace; font-size: 14px; fill: #1d1d1d; }",
        ".title { font-size: 18px; font-weight: 700; }",
        ".bar { fill: #2a6fdb; }",
        ".axis { stroke: #444; stroke-width: 1; }",
        "</style>",
        f'<text x="20" y="30" class="title">{title}</text>',
        f'<text x="20" y="52">{metric}</text>',
        f'<line x1="{left_pad}" y1="60" x2="{left_pad}" y2="{height - 20}" class="axis" />',
    ]
    for index, row in enumerate(rows):
        y = 90 + (index * 50)
        value = row["summary"]["mean"] or 0.0
        bar_width = int((value / bar_max) * (width - left_pad - 80))
        svg.append(f'<text x="20" y="{y}">{row["label"]}</text>')
        svg.append(f'<rect x="{left_pad}" y="{y - 14}" width="{bar_width}" height="20" class="bar" />')
        svg.append(f'<text x="{left_pad + bar_width + 10}" y="{y}">{value:.4f}</text>')
    svg.append("</svg>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(svg), encoding="utf-8")

