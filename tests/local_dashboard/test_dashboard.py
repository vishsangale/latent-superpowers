from __future__ import annotations

import json
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


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


def _wait_for_server(port: int, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(f"http://127.0.0.1:{port}/api/summary", timeout=1) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.1)
    raise AssertionError("dashboard server did not become ready in time")


def _get_json(port: int, path: str) -> dict:
    with urlopen(f"http://127.0.0.1:{port}{path}") as response:
        return json.loads(response.read().decode("utf-8"))


def test_index_runs_mixed_sources(ablation_store: Path, wandb_store: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(INDEX_SCRIPT),
            "--mlflow-uri",
            str(ablation_store),
            "--mlflow-experiment-name",
            "recsys",
            "--wandb-path",
            str(wandb_store),
            "--wandb-project",
            "recsys",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["run_count"] == 4
    assert sorted(payload["sources"]) == ["mlflow", "wandb-offline"]
    assert "loss" in payload["available_metrics"]
    assert "agent.lr" in payload["available_variant_keys"]


def test_dashboard_endpoints_and_refresh(ablation_store: Path, wandb_store: Path) -> None:
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
            "--wandb-path",
            str(wandb_store),
            "--wandb-project",
            "recsys",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        _wait_for_server(port)

        summary = _get_json(port, "/api/summary")
        runs = _get_json(port, "/api/runs")
        compare_max = _get_json(port, "/api/compare?metric=avg_reward&direction=max&variant_key=agent.lr")
        compare_min = _get_json(port, "/api/compare?metric=loss&direction=min&variant_key=agent.lr")
        compare_scoped = _get_json(
            port,
            "/api/compare?metric=avg_reward&direction=max&variant_key=agent.lr&run_id=run_a&run_id=run_b",
        )
        artifacts = _get_json(port, "/api/artifacts?run_id=run_a")
        preview = _get_json(
            port,
            "/api/artifact-preview?run_id=run_a&path=" + quote("artifact.txt"),
        )
        with urlopen(
            f"http://127.0.0.1:{port}/artifact-file?run_id=run_a&path=" + quote("artifact.txt")
        ) as response:
            artifact_body = response.read().decode("utf-8")
        html = urlopen(f"http://127.0.0.1:{port}/").read().decode("utf-8")

        assert summary["run_count"] == 4
        assert "Local Experiment Dashboard" in html
        assert len(runs["runs"]) == 4
        assert compare_max["rows"][0]["label"] == "agent.lr=0.02"
        assert compare_min["rows"][0]["label"] == "agent.lr=0.02"
        assert compare_scoped["rows"][0]["count"] == 2
        assert artifacts["artifacts"]
        assert "artifact for run_a" in preview["text"]
        assert artifact_body == "artifact for run_a\n"

        try:
            urlopen(
                f"http://127.0.0.1:{port}/artifact-file?run_id=run_a&path=" + quote("../secret.txt")
            )
        except HTTPError as exc:
            assert exc.code == 400
        else:  # pragma: no cover - defensive branch
            raise AssertionError("expected invalid artifact path to fail")

        experiment_dir = ablation_store / "123"
        from .conftest import _write_run  # local helper reuse

        _write_run(
            experiment_dir,
            experiment_id="123",
            run_id="run_d",
            avg_reward=2.2,
            loss=0.3,
            lr="0.05",
            seed="3",
        )
        refresh_request = Request(f"http://127.0.0.1:{port}/api/refresh", method="POST")
        refreshed = json.loads(urlopen(refresh_request).read().decode("utf-8"))
        assert refreshed["run_count"] == 5

        summary_after = _get_json(port, "/api/summary")
        assert summary_after["run_count"] == 5
        assert any(detail["source"] == "wandb-offline" for detail in summary_after["source_details"])
    finally:
        process.terminate()
        process.wait(timeout=5)


def test_dashboard_warns_on_non_loopback_host(ablation_store: Path) -> None:
    port = _pick_port()
    process = subprocess.Popen(
        [
            sys.executable,
            str(SERVER_SCRIPT),
            "--host",
            "0.0.0.0",
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
        _wait_for_server(port)
        summary = _get_json(port, "/api/summary")
        assert any("zero-auth" in warning for warning in summary["warnings"])
    finally:
        process.terminate()
        process.wait(timeout=5)
