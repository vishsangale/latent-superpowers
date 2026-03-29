#!/usr/bin/env python3
"""Serve a local dashboard for MLflow and W&B local data."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import threading
from urllib.parse import parse_qs, urlparse

from dashboard_data_utils import (
    HTML,
    find_run,
    grouped_compare,
    list_artifacts,
    load_dashboard_state,
    normalize_variant_keys,
    read_artifact_preview,
    serializable_state,
)


@dataclass
class DashboardConfig:
    mlflow_uri: str | None
    mlflow_experiment_name: str | None
    mlflow_experiment_id: str | None
    wandb_paths: list[str] | None
    wandb_project: str | None
    wandb_group: str | None
    host: str


class AppState:
    def __init__(self, config: DashboardConfig) -> None:
        self.config = config
        self._lock = threading.Lock()
        self._state: dict[str, object] = {}
        self.reload()

    def _load(self) -> dict[str, object]:
        state = load_dashboard_state(
            mlflow_uri=self.config.mlflow_uri,
            mlflow_experiment_name=self.config.mlflow_experiment_name,
            mlflow_experiment_id=self.config.mlflow_experiment_id,
            wandb_paths=self.config.wandb_paths,
            wandb_project=self.config.wandb_project,
            wandb_group=self.config.wandb_group,
        )
        warnings = list(state.get("warnings", []))
        if self.config.host not in {"127.0.0.1", "localhost", "::1"}:
            warnings.append(
                f"Dashboard is bound to {self.config.host}. This server is zero-auth and exposes local run metadata."
            )
        state["warnings"] = warnings
        return state

    def reload(self) -> dict[str, object]:
        fresh = self._load()
        with self._lock:
            self._state = fresh
            return self._state

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return self._state


def make_handler(app_state: AppState):
    class Handler(BaseHTTPRequestHandler):
        def _json(self, payload, status: int = 200):
            encoded = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _html(self, payload: str):
            encoded = payload.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _raw_file(self, path: Path):
            mime_type, _ = mimetypes.guess_type(path.name)
            payload = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime_type or "application/octet-stream")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Content-Disposition", f'inline; filename="{path.name}"')
            self.end_headers()
            self.wfile.write(payload)

        def do_POST(self):  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/api/refresh":
                payload = serializable_state(app_state.reload())
                self._json(
                    {
                        "ok": True,
                        "run_count": payload["run_count"],
                        "sources": payload["sources"],
                        "warnings": payload["warnings"],
                    }
                )
                return
            self.send_error(404, "Not found")

        def do_GET(self):  # noqa: N802
            state = app_state.snapshot()
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._html(HTML)
                return
            if parsed.path == "/api/summary":
                payload = serializable_state(state)
                self._json(
                    {
                        "sources": payload["sources"],
                        "source_details": payload["source_details"],
                        "warnings": payload["warnings"],
                        "run_count": payload["run_count"],
                        "status_counts": payload["status_counts"],
                        "available_metrics": payload["available_metrics"],
                        "available_variant_keys": payload["available_variant_keys"],
                        "timestamps": payload["timestamps"],
                    }
                )
                return
            if parsed.path == "/api/runs":
                self._json(serializable_state(state))
                return
            if parsed.path == "/api/compare":
                query = parse_qs(parsed.query)
                metric = query.get("metric", ["avg_reward"])[0]
                direction = query.get("direction", ["max"])[0]
                variant_keys = normalize_variant_keys(query.get("variant_key", []))
                source = query.get("source", [None])[0]
                search = query.get("search", [None])[0]
                run_ids = query.get("run_id", [])
                payload = {
                    "metric": metric,
                    "direction": direction,
                    "variant_keys": variant_keys,
                    "rows": grouped_compare(
                        state,
                        metric=metric,
                        direction=direction,
                        variant_keys=variant_keys,
                        source=source,
                        search=search,
                        run_ids=run_ids,
                    ),
                }
                self._json(payload)
                return
            if parsed.path == "/api/artifacts":
                query = parse_qs(parsed.query)
                run_id = query.get("run_id", [None])[0]
                if not run_id:
                    self.send_error(400, "run_id is required")
                    return
                self._json(list_artifacts(state, run_id))
                return
            if parsed.path == "/api/artifact-preview":
                query = parse_qs(parsed.query)
                run_id = query.get("run_id", [None])[0]
                relative_path = query.get("path", [None])[0]
                if not run_id or not relative_path:
                    self.send_error(400, "run_id and path are required")
                    return
                self._json(read_artifact_preview(state, run_id, relative_path))
                return
            if parsed.path == "/artifact-file":
                query = parse_qs(parsed.query)
                run_id = query.get("run_id", [None])[0]
                relative_path = query.get("path", [None])[0]
                if not run_id or not relative_path:
                    self.send_error(400, "run_id and path are required")
                    return
                run = find_run(state, run_id)
                if run is None or not run.artifact_root:
                    self.send_error(404, "unknown run")
                    return
                candidate = (Path(run.artifact_root).resolve() / relative_path).resolve()
                root = Path(run.artifact_root).resolve()
                if candidate != root and root not in candidate.parents:
                    self.send_error(400, "invalid artifact path")
                    return
                if not candidate.is_file():
                    self.send_error(404, "artifact not found")
                    return
                self._raw_file(candidate)
                return
            self.send_error(404, "Not found")

        def log_message(self, format, *args):  # noqa: A003
            return

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the local dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--mlflow-uri", help="MLflow tracking URI")
    parser.add_argument("--mlflow-experiment-name", help="MLflow experiment name")
    parser.add_argument("--mlflow-experiment-id", help="MLflow experiment ID")
    parser.add_argument("--wandb-path", action="append", default=[], help="Offline W&B run path")
    parser.add_argument("--wandb-project", help="Offline W&B project filter")
    parser.add_argument("--wandb-group", help="Offline W&B group filter")
    args = parser.parse_args()

    app_state = AppState(
        DashboardConfig(
            mlflow_uri=args.mlflow_uri,
            mlflow_experiment_name=args.mlflow_experiment_name,
            mlflow_experiment_id=args.mlflow_experiment_id,
            wandb_paths=args.wandb_path or None,
            wandb_project=args.wandb_project,
            wandb_group=args.wandb_group,
            host=args.host,
        )
    )

    server = ThreadingHTTPServer((args.host, args.port), make_handler(app_state))
    print(f"Serving local dashboard on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
