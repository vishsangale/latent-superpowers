#!/usr/bin/env python3
"""Summarize a Torch profiler Chrome trace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _event_iter(payload: dict[str, Any]) -> list[dict[str, Any]]:
    events = payload.get("traceEvents", [])
    return [event for event in events if isinstance(event, dict)]


def _event_name(event: dict[str, Any]) -> str:
    return str(event.get("name") or "<unknown>")


def _event_category(event: dict[str, Any]) -> str:
    return str(event.get("cat") or "<uncategorized>")


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize a Torch profiler Chrome trace.")
    parser.add_argument("trace", help="Chrome trace JSON path")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    payload = json.loads(Path(args.trace).read_text(encoding="utf-8"))
    events = _event_iter(payload)
    op_totals: dict[str, float] = {}
    cat_totals: dict[str, float] = {}
    for event in events:
        duration = float(event.get("dur") or 0.0)
        if duration <= 0:
            continue
        op_totals[_event_name(event)] = op_totals.get(_event_name(event), 0.0) + duration
        cat_totals[_event_category(event)] = cat_totals.get(_event_category(event), 0.0) + duration

    top_ops = sorted(op_totals.items(), key=lambda item: item[1], reverse=True)[: args.top]
    top_categories = sorted(cat_totals.items(), key=lambda item: item[1], reverse=True)[: args.top]
    result = {
        "trace": args.trace,
        "event_count": len(events),
        "top_ops": [{"name": name, "duration_us": duration} for name, duration in top_ops],
        "top_categories": [
            {"category": name, "duration_us": duration} for name, duration in top_categories
        ],
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"trace: {args.trace}")
        print(f"event_count: {len(events)}")
        print("top_ops:")
        for row in result["top_ops"]:
            print(f"- {row['name']}: {row['duration_us']}")
        print("top_categories:")
        for row in result["top_categories"]:
            print(f"- {row['category']}: {row['duration_us']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
