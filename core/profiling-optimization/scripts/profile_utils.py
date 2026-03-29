#!/usr/bin/env python3
"""Shared helpers for profiling-optimization commands."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, UTC
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _read_proc_status_value(pid: int, key: str) -> int | None:
    path = Path(f"/proc/{pid}/status")
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{key}:"):
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                return int(parts[1])
    return None


def _read_proc_cpu_seconds(pid: int) -> float | None:
    path = Path(f"/proc/{pid}/stat")
    if not path.exists():
        return None
    fields = path.read_text(encoding="utf-8").split()
    if len(fields) < 17:
        return None
    ticks = os.sysconf(os.sysconf_names["SC_CLK_TCK"])
    utime = int(fields[13])
    stime = int(fields[14])
    return (utime + stime) / ticks


@dataclass
class ProfileSample:
    timestamp: float
    rss_kb: int | None
    cpu_seconds: float | None


@dataclass
class GpuSample:
    timestamp: float
    index: int
    utilization_gpu: float | None
    utilization_memory: float | None
    memory_used_mb: float | None
    memory_total_mb: float | None


def _sample_gpu_once() -> list[GpuSample]:
    if shutil.which("nvidia-smi") is None:
        return []
    command = [
        "nvidia-smi",
        "--query-gpu=index,utilization.gpu,utilization.memory,memory.used,memory.total",
        "--format=csv,noheader,nounits",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return []
    timestamp = time.time()
    samples: list[GpuSample] = []
    for line in result.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 5:
            continue
        samples.append(
            GpuSample(
                timestamp=timestamp,
                index=int(parts[0]),
                utilization_gpu=_to_float(parts[1]),
                utilization_memory=_to_float(parts[2]),
                memory_used_mb=_to_float(parts[3]),
                memory_total_mb=_to_float(parts[4]),
            )
        )
    return samples


def _to_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def profile_command(
    command: list[str],
    *,
    cwd: str | None = None,
    sample_interval: float = 0.25,
    gpu_sample_interval: float = 1.0,
    shell: bool = False,
) -> dict[str, Any]:
    started_at = utc_now()
    start_wall = time.time()
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []

    process = subprocess.Popen(
        command if not shell else " ".join(command),
        cwd=cwd,
        shell=shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    samples: list[ProfileSample] = []
    gpu_samples: list[GpuSample] = []
    stop_event = threading.Event()

    def sample_loop() -> None:
        next_gpu = time.time()
        while not stop_event.is_set():
            rss_kb = _read_proc_status_value(process.pid, "VmRSS")
            cpu_seconds = _read_proc_cpu_seconds(process.pid)
            samples.append(ProfileSample(timestamp=time.time(), rss_kb=rss_kb, cpu_seconds=cpu_seconds))
            if time.time() >= next_gpu:
                gpu_samples.extend(_sample_gpu_once())
                next_gpu = time.time() + gpu_sample_interval
            if process.poll() is not None:
                break
            time.sleep(sample_interval)

    sampler = threading.Thread(target=sample_loop, daemon=True)
    sampler.start()
    stdout, stderr = process.communicate()
    stop_event.set()
    sampler.join(timeout=2.0)
    end_wall = time.time()

    stdout_chunks.append(stdout)
    stderr_chunks.append(stderr)

    wall_time = end_wall - start_wall
    peak_rss_kb = max((sample.rss_kb or 0) for sample in samples) if samples else None
    cpu_util_percent = _average_cpu_percent(samples, wall_time)
    gpu_summary = summarize_gpu_samples(gpu_samples)

    return {
        "command": command,
        "cwd": cwd,
        "shell": shell,
        "started_at": started_at,
        "ended_at": utc_now(),
        "exit_code": process.returncode,
        "wall_time_sec": wall_time,
        "stdout": stdout,
        "stderr": stderr,
        "sample_interval_sec": sample_interval,
        "samples": [asdict(sample) for sample in samples],
        "peak_rss_kb": peak_rss_kb,
        "peak_rss_mb": (peak_rss_kb / 1024.0) if peak_rss_kb else None,
        "avg_cpu_percent": cpu_util_percent,
        "gpu_samples": [asdict(sample) for sample in gpu_samples],
        "gpu_summary": gpu_summary,
    }


def _average_cpu_percent(samples: list[ProfileSample], wall_time_sec: float) -> float | None:
    cpu_values = [sample.cpu_seconds for sample in samples if sample.cpu_seconds is not None]
    if len(cpu_values) < 2 or wall_time_sec <= 0:
        return None
    delta = cpu_values[-1] - cpu_values[0]
    if delta < 0:
        return None
    return (delta / wall_time_sec) * 100.0


def summarize_gpu_samples(samples: list[GpuSample]) -> dict[str, Any]:
    if not samples:
        return {
            "gpu_count": 0,
            "peak_memory_used_mb": None,
            "max_utilization_gpu": None,
            "mean_utilization_gpu": None,
        }
    util_values = [sample.utilization_gpu for sample in samples if sample.utilization_gpu is not None]
    mem_values = [sample.memory_used_mb for sample in samples if sample.memory_used_mb is not None]
    return {
        "gpu_count": len({sample.index for sample in samples}),
        "peak_memory_used_mb": max(mem_values) if mem_values else None,
        "max_utilization_gpu": max(util_values) if util_values else None,
        "mean_utilization_gpu": (sum(util_values) / len(util_values)) if util_values else None,
    }


def load_profile(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_profile(path: str | Path, payload: dict[str, Any]) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return destination


def recommendation_lines(profile: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []
    wall = profile.get("wall_time_sec")
    peak_rss_mb = profile.get("peak_rss_mb")
    avg_cpu = profile.get("avg_cpu_percent")
    gpu_summary = profile.get("gpu_summary", {}) or {}
    gpu_mean = gpu_summary.get("mean_utilization_gpu")
    gpu_peak_mem = gpu_summary.get("peak_memory_used_mb")

    if gpu_mean is not None and gpu_mean < 30 and avg_cpu is not None and avg_cpu < 50:
        recommendations.append("GPU and CPU utilization are both low; check input pipeline, blocking I/O, or launch overhead.")
    if gpu_mean is not None and gpu_mean < 40 and peak_rss_mb and peak_rss_mb > 1024:
        recommendations.append("Memory pressure is visible while GPU utilization stays modest; inspect data loading and host-side preprocessing.")
    if gpu_peak_mem is not None and gpu_peak_mem > 0:
        recommendations.append(f"Peak GPU memory reached about {gpu_peak_mem:.1f} MB; batch size or activation volume may be the next tuning lever.")
    if peak_rss_mb is not None and peak_rss_mb > 2048:
        recommendations.append(f"Peak RSS reached about {peak_rss_mb:.1f} MB; inspect dataset caching, tensors on host, and duplicate copies.")
    if wall is not None and wall > 30 and not recommendations:
        recommendations.append("The command is slow but the coarse signals are inconclusive; capture a Torch profiler trace next.")
    if not recommendations:
        recommendations.append("No dominant bottleneck stands out from the coarse profile; compare against a second profile or inspect a Torch trace.")
    return recommendations


def compare_profile_rows(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for profile in profiles:
        rows.append(
            {
                "path": profile.get("_path"),
                "wall_time_sec": profile.get("wall_time_sec"),
                "peak_rss_mb": profile.get("peak_rss_mb"),
                "avg_cpu_percent": profile.get("avg_cpu_percent"),
                "gpu_mean_utilization": (profile.get("gpu_summary") or {}).get("mean_utilization_gpu"),
                "gpu_peak_memory_mb": (profile.get("gpu_summary") or {}).get("peak_memory_used_mb"),
                "exit_code": profile.get("exit_code"),
            }
        )
    rows.sort(
        key=lambda row: (
            1 if row["wall_time_sec"] is None else 0,
            math.inf if row["wall_time_sec"] is None else float(row["wall_time_sec"]),
        )
    )
    return rows

