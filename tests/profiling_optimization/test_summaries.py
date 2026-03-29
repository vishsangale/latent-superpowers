from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SUMMARY_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "profiling-optimization"
    / "scripts"
    / "summarize_profile.py"
)
COMPARE_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "profiling-optimization"
    / "scripts"
    / "compare_profiles.py"
)
TRACE_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "profiling-optimization"
    / "scripts"
    / "summarize_torch_trace.py"
)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_summarize_and_compare_profiles(tmp_path: Path) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    _write_json(
        first,
        {
            "exit_code": 0,
            "wall_time_sec": 2.0,
            "peak_rss_mb": 256.0,
            "avg_cpu_percent": 60.0,
            "gpu_summary": {"mean_utilization_gpu": 20.0, "peak_memory_used_mb": 100.0},
        },
    )
    _write_json(
        second,
        {
            "exit_code": 0,
            "wall_time_sec": 1.0,
            "peak_rss_mb": 300.0,
            "avg_cpu_percent": 75.0,
            "gpu_summary": {"mean_utilization_gpu": 40.0, "peak_memory_used_mb": 120.0},
        },
    )
    summary = subprocess.run(
        [sys.executable, str(SUMMARY_SCRIPT), str(first), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(summary.stdout)
    assert payload["recommendations"]

    compare = subprocess.run(
        [sys.executable, str(COMPARE_SCRIPT), str(first), str(second), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    compare_payload = json.loads(compare.stdout)
    assert compare_payload["rows"][0]["path"] == str(second)


def test_summarize_torch_trace(tmp_path: Path) -> None:
    trace = tmp_path / "trace.json"
    _write_json(
        trace,
        {
            "traceEvents": [
                {"name": "aten::mm", "cat": "cpu_op", "dur": 1000},
                {"name": "aten::mm", "cat": "cpu_op", "dur": 500},
                {"name": "cudaLaunchKernel", "cat": "cuda_runtime", "dur": 800},
            ]
        },
    )
    result = subprocess.run(
        [sys.executable, str(TRACE_SCRIPT), str(trace), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["top_ops"][0]["name"] == "aten::mm"
