#!/usr/bin/env python3
"""
Plan a Hydra multirun command without executing it.
"""

from __future__ import annotations

import argparse
import json
import math
import shlex

from analyze_overrides import classify_override


def estimate_sweep_cardinality(value: str | None) -> int | None:
    if value is None:
        return None
    stripped = value.strip()
    if stripped.startswith("range(") or stripped.startswith("choice(") or stripped.startswith("interval("):
        return None
    if "," not in stripped:
        return 1
    return len([part for part in stripped.split(",") if part.strip()])


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan a Hydra multirun command.")
    parser.add_argument("--entrypoint", help="Entrypoint script or module")
    parser.add_argument("--config-path", help="Hydra config path")
    parser.add_argument("--config-name", help="Hydra config name")
    parser.add_argument("--python-bin", default="python3", help="Python executable to use")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("overrides", nargs="*", help="Hydra overrides")
    args = parser.parse_args()

    command = [args.python_bin]
    if args.entrypoint:
        command.append(args.entrypoint)
    else:
        command.append("<entrypoint>")
    if args.config_path:
        command.extend(["--config-path", args.config_path])
    if args.config_name:
        command.extend(["--config-name", args.config_name])
    command.append("-m")
    command.extend(args.overrides)

    analyses = [classify_override(item) for item in args.overrides]
    sweep_dimensions = []
    cardinalities = []
    for item in analyses:
        if item["is_sweep"]:
            cardinality = estimate_sweep_cardinality(item["value"])
            sweep_dimensions.append(
                {
                    "target": item["target"],
                    "value": item["value"],
                    "estimated_cardinality": cardinality,
                }
            )
            if cardinality is not None:
                cardinalities.append(cardinality)

    estimated_total = math.prod(cardinalities) if cardinalities else None
    result = {
        "command": command,
        "command_string": shlex.join(command),
        "sweep_dimensions": sweep_dimensions,
        "estimated_total_runs": estimated_total,
        "notes": [
            "This command is planning-only and does not execute Hydra.",
            "Estimated run count is omitted when sweep expressions are dynamic or not enumerable from CLI text alone.",
        ],
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"Planned multirun command: {result['command_string']}")
    if sweep_dimensions:
        print("Sweep dimensions:")
        for dimension in sweep_dimensions:
            count = dimension["estimated_cardinality"]
            count_text = str(count) if count is not None else "unknown"
            print(f"- {dimension['target']}: {dimension['value']} (estimated choices: {count_text})")
    else:
        print("Sweep dimensions: none detected from CLI syntax")
    print(
        "Estimated total runs: "
        + (str(estimated_total) if estimated_total is not None else "unknown")
    )
    for note in result["notes"]:
        print(f"- {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
