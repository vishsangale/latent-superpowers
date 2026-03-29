from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
PLAN_SCRIPT = ROOT / "core" / "experiment-runner" / "scripts" / "plan_runs.py"


def test_plan_runs_with_matrix(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(PLAN_SCRIPT),
            str(tmp_path),
            "--base-command",
            f"{sys.executable} train.py",
            "--set",
            "env.slate_size=5,10",
            "--set",
            "agent.epsilon=0.1,0.2",
            "--seeds",
            "1,2",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["run_count"] == 8
    assert payload["dimensions"] == {"agent.epsilon": 2, "env.slate_size": 2, "seeds": 2}


def test_plan_runs_autodetects_hydra_entrypoint(tmp_path: Path) -> None:
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
    result = subprocess.run(
        [sys.executable, str(PLAN_SCRIPT), str(repo), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["run_count"] == 1
    assert payload["base_command"][-1].endswith("main.py")


def test_plan_runs_rejects_invalid_repeat_and_duplicate_factor(tmp_path: Path) -> None:
    bad_repeat = subprocess.run(
        [
            sys.executable,
            str(PLAN_SCRIPT),
            str(tmp_path),
            "--base-command",
            f"{sys.executable} train.py",
            "--repeats",
            "0",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert bad_repeat.returncode != 0
    assert "--repeats must be >= 1" in bad_repeat.stderr

    duplicate = subprocess.run(
        [
            sys.executable,
            str(PLAN_SCRIPT),
            str(tmp_path),
            "--base-command",
            f"{sys.executable} train.py",
            "--set",
            "env.slate_size=5",
            "--set",
            "env.slate_size=10",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert duplicate.returncode != 0
    assert "Duplicate factor key" in duplicate.stderr
