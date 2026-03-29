from __future__ import annotations

import json
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen


INDEX_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "local-dashboard"
    / "scripts"
    / "index_runs.py"
)
SERVER_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "local-dashboard"
    / "scripts"
    / "serve_dashboard.py"
)


def _pick_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_index_runs(ablation_store: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(INDEX_SCRIPT),
            "--mlflow-uri",
            str(ablation_store),
            "--mlflow-experiment-name",
            "recsys",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["run_count"] == 3


def test_dashboard_endpoints(ablation_store: Path) -> None:
    port = _pick_port()
    process = subprocess.Popen(
        [
            sys.executable,
            str(SERVER_SCRIPT),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--mlflow-uri",
            str(ablation_store),
            "--mlflow-experiment-name",
            "recsys",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        time.sleep(1.0)
        summary = json.loads(urlopen(f"http://127.0.0.1:{port}/api/summary").read().decode("utf-8"))
        runs = json.loads(urlopen(f"http://127.0.0.1:{port}/api/runs").read().decode("utf-8"))
        compare = json.loads(
            urlopen(
                f"http://127.0.0.1:{port}/api/compare?metric=avg_reward&direction=max&variant_key=agent.lr"
            ).read().decode("utf-8")
        )
        html = urlopen(f"http://127.0.0.1:{port}/").read().decode("utf-8")
        assert summary["run_count"] == 3
        assert len(runs["runs"]) == 3
        assert compare["rows"][0]["label"] == "agent.lr=0.001"
        assert "Local Experiment Dashboard" in html
    finally:
        process.terminate()
        process.wait(timeout=5)
