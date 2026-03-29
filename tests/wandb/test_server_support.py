from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "core" / "wandb" / "scripts"
CHECK_CONTEXT = SCRIPTS_DIR / "check_wandb_context.py"
CHECK_SERVER = SCRIPTS_DIR / "check_wandb_server.py"


class _ProbeHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok": true}')

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_check_wandb_context_reports_base_url() -> None:
    env = os.environ.copy()
    env["WANDB_BASE_URL"] = "http://wandb.internal:8080"
    result = subprocess.run(
        [sys.executable, str(CHECK_CONTEXT), "--json"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    payload = json.loads(result.stdout)
    assert payload["base_url"] == "http://wandb.internal:8080"
    assert payload["deployment"] == "self-hosted"


def test_check_wandb_server_reaches_local_server() -> None:
    port = _free_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), _ProbeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(CHECK_SERVER),
                "--base-url",
                f"http://127.0.0.1:{port}",
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    payload = json.loads(result.stdout)
    assert payload["reachable"] is True
    assert payload["deployment"] == "self-hosted"
    assert payload["root_probe"]["ok"] is True
    assert payload["graphql_probe"]["ok"] is True


def test_check_wandb_server_handles_unreachable_host() -> None:
    port = _free_port()
    result = subprocess.run(
        [
            sys.executable,
            str(CHECK_SERVER),
            "--base-url",
            f"http://127.0.0.1:{port}",
            "--timeout",
            "0.2",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["reachable"] is False
    assert payload["root_probe"]["ok"] is False
