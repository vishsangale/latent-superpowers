#!/usr/bin/env python3
"""
Classify Hydra CLI overrides into a small set of actionable categories.
"""

from __future__ import annotations

import argparse
import json
import re

SWEEP_HINT_RE = re.compile(r",(?![^\[\{]*[\]\}])")


def classify_override(raw: str) -> dict[str, object]:
    text = raw.strip()
    result: dict[str, object] = {
        "raw": raw,
        "normalized": text,
        "operation": "unknown",
        "target": None,
        "value": None,
        "is_sweep": False,
        "notes": [],
    }

    if not text:
        result["notes"] = ["empty override"]
        return result

    if text.startswith("~"):
        body = text[1:]
        key, _, value = body.partition("=")
        result["operation"] = "delete"
        result["target"] = key.strip() or None
        result["value"] = value.strip() or None
        result["notes"] = ["deletes a key or defaults entry"]
        return result

    prefix = ""
    body = text
    if body.startswith("++"):
        prefix = "++"
        body = body[2:]
        result["operation"] = "force_add_or_override"
    elif body.startswith("+"):
        prefix = "+"
        body = body[1:]
        result["operation"] = "add"

    key, sep, value = body.partition("=")
    key = key.strip()
    value = value.strip() if sep else None

    result["target"] = key or None
    result["value"] = value

    if not sep:
        if prefix:
            result["notes"] = ["override is missing '=' after add prefix"]
        else:
            result["notes"] = ["no '=' found; Hydra override may be incomplete"]
        return result

    if result["operation"] == "unknown":
        if "/" in key and "." not in key.split("/", 1)[0]:
            result["operation"] = "select_group_option"
            result["notes"] = ["looks like a config-group selection"]
        else:
            result["operation"] = "assign"
            result["notes"] = ["looks like a field assignment"]

    if value is not None and (SWEEP_HINT_RE.search(value) or value.startswith("range(") or value.startswith("choice(")):
        result["is_sweep"] = True
        result["notes"].append("value looks like a multirun sweep expression")

    if prefix == "+" and result["operation"] == "select_group_option":
        result["notes"].append("adding a new defaults entry often requires the target group to exist")
    if prefix == "++" and result["operation"] == "assign":
        result["notes"].append("forces creation if the field is missing")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze Hydra CLI overrides.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("overrides", nargs="+", help="Hydra CLI overrides")
    args = parser.parse_args()

    results = [classify_override(item) for item in args.overrides]

    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    for item in results:
        print(f"Override: {item['raw']}")
        print(f"  operation: {item['operation']}")
        print(f"  target: {item['target'] or 'unknown'}")
        print(f"  value: {item['value'] if item['value'] is not None else 'none'}")
        print(f"  is_sweep: {'yes' if item['is_sweep'] else 'no'}")
        for note in item["notes"]:
            print(f"  note: {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
