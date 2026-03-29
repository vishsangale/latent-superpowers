#!/usr/bin/env python3
"""Inspect artifact producers and manifests from local W&B offline runs."""

from __future__ import annotations

import argparse
import json
from typing import Any

from wandb_run_utils import filter_runs, load_offline_runs, metric_value


def _artifact_matches(event: dict[str, Any], query: str) -> bool:
    name = event.get("name")
    if not name:
        return False
    return name == query or str(name).startswith(query + ":")


def _extract_artifact_payload(event: dict[str, Any]) -> dict[str, Any]:
    manifest = event.get("manifest", {})
    contents = manifest.get("contents", [])
    if isinstance(contents, dict):
        contents = [contents]
    return {
        "name": event.get("name"),
        "type": event.get("type"),
        "digest": event.get("digest"),
        "aliases": event.get("aliases", []),
        "version_index": event.get("version_index"),
        "manifest_entries": contents,
        "finalize": event.get("finalize", False),
    }


def _render_text(payload: dict[str, Any]) -> str:
    lines = [f"Found {payload['match_count']} matching artifact event{'s' if payload['match_count'] != 1 else ''}."]
    for index, match in enumerate(payload["matches"], start=1):
        artifact = match["artifact"]
        run = match["producer_run"]
        lines.append(
            f"{index}. artifact={artifact['name']} | type={artifact['type']} | run_id={run['run_id']} | project={run['project']}"
        )
        if artifact["aliases"]:
            lines.append(f"   aliases: {', '.join(artifact['aliases'])}")
        if artifact["manifest_entries"]:
            paths = [entry.get("path") for entry in artifact["manifest_entries"] if entry.get("path")]
            if paths:
                lines.append(f"   manifest paths: {', '.join(paths)}")
        lines.append("   downstream consumers: unavailable in offline-run inspection")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect artifact lineage from local W&B offline runs.")
    parser.add_argument("artifact", help="Artifact name or version reference")
    parser.add_argument(
        "--offline-dir",
        action="append",
        default=[],
        help="Directory to scan recursively for run-*.wandb files.",
    )
    parser.add_argument("--run-path", action="append", default=[], help="Explicit path to a run-*.wandb file.")
    parser.add_argument("--project", help="Filter by W&B project")
    parser.add_argument("--group", help="Filter by W&B run group")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    roots = [*args.offline_dir, *args.run_path]
    runs = load_offline_runs(roots or None)
    filtered = filter_runs(runs, project=args.project, group=args.group)

    matches = []
    for run in filtered:
        for event in run.artifact_events:
            if not _artifact_matches(event, args.artifact):
                continue
            matches.append(
                {
                    "artifact": _extract_artifact_payload(event),
                    "producer_run": {
                        "run_id": run.run_id,
                        "project": run.project,
                        "group": run.group,
                        "job_type": run.job_type,
                        "path": run.path,
                        "avg_reward": metric_value(run, "avg_reward"),
                    },
                    "downstream_consumers": [],
                }
            )

    payload = {
        "artifact_query": args.artifact,
        "project": args.project,
        "group": args.group,
        "match_count": len(matches),
        "matches": matches,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_render_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
