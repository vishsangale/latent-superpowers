#!/usr/bin/env python3
"""Serve a local dashboard for MLflow and W&B local data."""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from urllib.parse import parse_qs, urlparse

from dashboard_data_utils import HTML, grouped_compare, list_artifacts, load_dashboard_state, serializable_state


def make_handler(state):
    class Handler(BaseHTTPRequestHandler):
        def _json(self, payload):
            encoded = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
            self.send_response(200)
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

        def do_GET(self):  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._html(HTML)
                return
            if parsed.path == "/api/summary":
                payload = serializable_state(state)
                self._json({"sources": payload["sources"], "run_count": payload["run_count"]})
                return
            if parsed.path == "/api/runs":
                self._json(serializable_state(state))
                return
            if parsed.path == "/api/compare":
                query = parse_qs(parsed.query)
                metric = query.get("metric", ["avg_reward"])[0]
                direction = query.get("direction", ["max"])[0]
                variant_keys = [value for value in query.get("variant_key", []) if value]
                payload = {
                    "metric": metric,
                    "direction": direction,
                    "variant_keys": variant_keys,
                    "rows": grouped_compare(
                        state,
                        metric=metric,
                        direction=direction,
                        variant_keys=variant_keys,
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

    state = load_dashboard_state(
        mlflow_uri=args.mlflow_uri,
        mlflow_experiment_name=args.mlflow_experiment_name,
        mlflow_experiment_id=args.mlflow_experiment_id,
        wandb_paths=args.wandb_path or None,
        wandb_project=args.wandb_project,
        wandb_group=args.wandb_group,
    )

    server = ThreadingHTTPServer((args.host, args.port), make_handler(state))
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
