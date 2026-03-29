#!/usr/bin/env python3
"""Resolve W&B context for a repository or shell session."""

from __future__ import annotations

import argparse
import json
import os


def classify_deployment(base_url: str | None) -> str:
    if not base_url:
        return "cloud-default"
    lowered = base_url.lower()
    if "wandb.ai" in lowered:
        return "cloud-custom-base-url"
    return "self-hosted"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Weights & Biases context.")
    parser.add_argument("--entity", help="W&B entity override")
    parser.add_argument("--project", help="W&B project override")
    parser.add_argument("--base-url", help="W&B base URL override")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    base_url = args.base_url or os.getenv("WANDB_BASE_URL")
    result = {
        "entity": args.entity or os.getenv("WANDB_ENTITY"),
        "project": args.project or os.getenv("WANDB_PROJECT"),
        "api_key_present": bool(os.getenv("WANDB_API_KEY")),
        "mode": os.getenv("WANDB_MODE", "online"),
        "base_url": base_url,
        "deployment": classify_deployment(base_url),
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
