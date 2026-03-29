from __future__ import annotations

import json
from pathlib import Path
import shlex
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
INSPECT = ROOT / "core" / "slurm-cluster" / "scripts" / "inspect_slurm_project.py"
SBATCH = ROOT / "core" / "slurm-cluster" / "scripts" / "generate_sbatch.py"
ARRAY = ROOT / "core" / "slurm-cluster" / "scripts" / "plan_job_array.py"
SUMMARIZE = ROOT / "core" / "slurm-cluster" / "scripts" / "summarize_slurm_log.py"
SACCT = ROOT / "core" / "slurm-cluster" / "scripts" / "parse_sacct.py"


def test_inspect_and_generate_sbatch(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    conf = repo / "conf"
    conf.mkdir(parents=True)
    (conf / "train.yaml").write_text("train:\n  seed: 1\n", encoding="utf-8")
    (repo / "main.py").write_text(
        "\n".join(
            [
                "import hydra",
                "from omegaconf import DictConfig",
                "@hydra.main(version_base='1.3', config_path='conf', config_name='train')",
                "def main(cfg: DictConfig) -> None:",
                "    pass",
                "if __name__ == '__main__':",
                "    main()",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    inspect = subprocess.run(
        [sys.executable, str(INSPECT), str(repo), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(inspect.stdout)
    assert payload["entrypoints"][0]["path"] == "main.py"

    sbatch_path = tmp_path / "job.sbatch"
    subprocess.run(
        [
            sys.executable,
            str(SBATCH),
            str(repo),
            "--job-name",
            "demo",
            "--out",
            str(sbatch_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    content = sbatch_path.read_text(encoding="utf-8")
    assert "#SBATCH --job-name=demo" in content
    assert "main.py" in content


def test_plan_job_array_and_log_parsers(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "runs": [
                    {"command": [sys.executable, "-c", "print('a')"], "workdir": str(tmp_path / "one"), "run_key": "run_000"},
                    {"command": [sys.executable, "-c", "print('b')"], "workdir": str(tmp_path / "two"), "run_key": "run_001"},
                ]
            }
        ),
        encoding="utf-8",
    )
    plan = subprocess.run(
        [
            sys.executable,
            str(ARRAY),
            str(manifest),
            "--script-out",
            str(tmp_path / "array.sbatch"),
            "--task-map-out",
            str(tmp_path / "array.txt"),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(plan.stdout)
    assert payload["task_count"] == 2
    assert Path(payload["script_path"]).exists()
    assert Path(payload["task_map_path"]).exists()
    script_content = Path(payload["script_path"]).read_text(encoding="utf-8")
    task_content = Path(payload["task_map_path"]).read_text(encoding="utf-8")
    assert "#SBATCH --array=0-1" in script_content
    assert f"cd {shlex.quote(str(tmp_path / 'one'))}" in task_content
    assert f"cd {shlex.quote(str(tmp_path / 'two'))}" in task_content

    log_path = tmp_path / "slurm.err"
    log_path.write_text("Traceback (most recent call last):\nModuleNotFoundError: No module named 'torch'\n", encoding="utf-8")
    summary = subprocess.run(
        [sys.executable, str(SUMMARIZE), str(log_path), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    summary_payload = json.loads(summary.stdout)
    assert summary_payload["logs"][0]["classification"] == "python-traceback"

    sacct_path = tmp_path / "sacct.txt"
    sacct_path.write_text(
        "JobID|State|Elapsed\n123|COMPLETED|00:01:00\n124|FAILED|00:00:10\n",
        encoding="utf-8",
    )
    sacct = subprocess.run(
        [sys.executable, str(SACCT), str(sacct_path), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    sacct_payload = json.loads(sacct.stdout)
    assert sacct_payload["status_counts"]["FAILED"] == 1


def test_plan_job_array_dry_run_and_empty_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"runs": [{"command": [sys.executable, "-c", "print('x')"], "workdir": str(tmp_path), "run_key": "run_000"}]}), encoding="utf-8")
    dry_run = subprocess.run(
        [sys.executable, str(ARRAY), str(manifest), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(dry_run.stdout)
    assert payload["wrote_files"] is False
    assert not Path(payload["script_path"]).exists()
    assert not Path(payload["task_map_path"]).exists()

    empty_manifest = tmp_path / "empty.json"
    empty_manifest.write_text(json.dumps({"runs": []}), encoding="utf-8")
    empty = subprocess.run(
        [sys.executable, str(ARRAY), str(empty_manifest)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert empty.returncode != 0
    assert "contains no runs" in empty.stderr
