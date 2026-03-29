#!/usr/bin/env python3
"""Check reachability and configuration for a W&B server."""

from __future__ import annotations

import argparse
import json
import os
from typing import Any
from urllib import error, parse, request

from check_wandb_context import classify_deployment


def normalize_base_url(base_url: str | None) -> str:
    if not base_url:
        return "https://api.wandb.ai"
    return base_url.rstrip("/")


def probe_url(url: str, timeout: float) -> dict[str, Any]:
    try:
        with request.urlopen(url, timeout=timeout) as response:
            headers = dict(response.headers.items())
            return {
                "ok": True,
                "status": getattr(response, "status", None),
                "final_url": response.geturl(),
                "server": headers.get("Server"),
                "content_type": headers.get("Content-Type"),
            }
    except error.HTTPError as exc:
        headers = dict(exc.headers.items())
        return {
            "ok": False,
            "status": exc.code,
            "final_url": exc.geturl(),
            "server": headers.get("Server"),
            "content_type": headers.get("Content-Type"),
            "error": f"HTTP {exc.code}",
        }
    except error.URLError as exc:
        return {
            "ok": False,
            "status": None,
            "final_url": url,
            "error": str(exc.reason),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check reachability for a W&B server.")
    parser.add_argument("--base-url", help="W&B base URL override")
    parser.add_argument("--entity", help="W&B entity override")
    parser.add_argument("--project", help="W&B project override")
    parser.add_argument("--timeout", type=float, default=5.0, help="HTTP timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    base_url = normalize_base_url(args.base_url or os.getenv("WANDB_BASE_URL"))
    root_probe = probe_url(base_url, args.timeout)
    graphql_url = parse.urljoin(base_url + "/", "graphql")
    graphql_probe = probe_url(graphql_url, args.timeout)

    result = {
        "base_url": base_url,
        "deployment": classify_deployment(None if base_url == "https://api.wandb.ai" else base_url),
        "entity": args.entity or os.getenv("WANDB_ENTITY"),
        "project": args.project or os.getenv("WANDB_PROJECT"),
        "api_key_present": bool(os.getenv("WANDB_API_KEY")),
        "root_probe": root_probe,
        "graphql_probe": graphql_probe,
    }
    result["reachable"] = bool(root_probe["ok"] or graphql_probe["ok"])

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"Base URL: {result['base_url']}")
    print(f"Deployment: {result['deployment']}")
    print(f"Entity: {result['entity']}")
    print(f"Project: {result['project']}")
    print(f"API key present: {'yes' if result['api_key_present'] else 'no'}")
    print(
        "Root probe: "
        f"ok={root_probe['ok']} status={root_probe['status']} final_url={root_probe['final_url']}"
    )
    print(
        "GraphQL probe: "
        f"ok={graphql_probe['ok']} status={graphql_probe['status']} final_url={graphql_probe['final_url']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
