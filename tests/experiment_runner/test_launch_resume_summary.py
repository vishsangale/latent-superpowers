from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
LAUNCH_SCRIPT = ROOT / "core" / "experiment-runner" / "scripts" / "launch_runs.py"
RESUME_SCRIPT = ROOT / "core" / "experiment-runner" / "scripts" / "resume_runs.py"
SUMMARY_SCRIPT = ROOT / "core" / "experiment-runner" / "scripts" / "summarize_manifest.py"


def test_launch_resume_and_summary(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    script = repo / "toy.py"
    script.write_text(
        "\n".join(
            [
                "from __future__ import annotations",
                "import pathlib",
                "import sys",
                "flag = pathlib.Path('fail_once.flag')",
                "mode = sys.argv[1] if len(sys.argv) > 1 else 'ok'",
                "if mode == 'fail-once' and not flag.exists():",
                "    flag.write_text('seen', encoding='utf-8')",
                "    print('first failure')",
                "    raise SystemExit(1)",
                "print('Done. Average reward over 1 episodes: 3.500')",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out_dir = repo / "outputs"
    launch = subprocess.run(
        [
            sys.executable,
            str(LAUNCH_SCRIPT),
            str(repo),
            "--base-command",
            f"{sys.executable} {script} fail-once",
            "--out-dir",
            str(out_dir),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    launch_payload = json.loads(launch.stdout)
    assert launch_payload["failure_count"] == 1

    manifest_path = out_dir / "manifest.json"
    resume = subprocess.run(
        [sys.executable, str(RESUME_SCRIPT), str(manifest_path), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    resume_payload = json.loads(resume.stdout)
    assert resume_payload["success_count"] == 1
    assert resume_payload["failure_count"] == 0

    summary = subprocess.run(
        [sys.executable, str(SUMMARY_SCRIPT), str(manifest_path), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    summary_payload = json.loads(summary.stdout)
    assert summary_payload["best_extracted_metric"] == 3.5
    assert summary_payload["best_run_key"] == "run_000"


def test_launch_records_spawn_failure_and_zero_limit(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    out_dir = repo / "outputs"
    result = subprocess.run(
        [
            sys.executable,
            str(LAUNCH_SCRIPT),
            str(repo),
            "--base-command",
            "missing_executable",
            "--out-dir",
            str(out_dir),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["failure_count"] == 1
    results_path = out_dir / "results.jsonl"
    assert results_path.exists()
    assert "run_000" in results_path.read_text(encoding="utf-8")

    zero_limit = subprocess.run(
        [
            sys.executable,
            str(LAUNCH_SCRIPT),
            str(repo),
            "--base-command",
            f"{sys.executable} -c print('ok')",
            "--out-dir",
            str(repo / 'zero-limit'),
            "--max-runs",
            "0",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    zero_payload = json.loads(zero_limit.stdout)
    assert zero_payload["completed_count"] == 0


def test_summary_ignores_partial_results_line(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    manifest_path = repo / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "run_count": 1,
                "runs": [
                    {
                        "run_key": "run_000",
                        "label": "base",
                        "command": [sys.executable, "-c", "print('ok')"],
                        "command_text": f"{sys.executable} -c print('ok')",
                        "overrides": {},
                        "seed": None,
                        "repeat_index": 0,
                        "workdir": str(repo),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (repo / "results.jsonl").write_text('{"run_key":"run_000","status":"success"}\n{"broken"\n', encoding="utf-8")
    summary = subprocess.run(
        [sys.executable, str(SUMMARY_SCRIPT), str(manifest_path), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(summary.stdout)
    assert payload["success_count"] == 1
