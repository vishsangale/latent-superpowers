from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "wandb"
    / "scripts"
    / "onboard_wandb_project.py"
)


def test_onboard_wandb_project_detects_existing_integration(tmp_path: Path) -> None:
    (tmp_path / "conf" / "wandb").mkdir(parents=True)
    (tmp_path / "rl_recsys" / "training").mkdir(parents=True)
    (tmp_path / "experiments").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text(
        "[project]\ndependencies = [\"hydra-core\", \"wandb\"]\n",
        encoding="utf-8",
    )
    (tmp_path / "conf" / "wandb" / "default.yaml").write_text("enabled: true\n", encoding="utf-8")
    (tmp_path / "rl_recsys" / "training" / "wandb_logger.py").write_text(
        "import wandb\n\ndef init_wandb():\n    return wandb.init(project='demo')\n",
        encoding="utf-8",
    )
    (tmp_path / "experiments" / "run.py").write_text(
        "if __name__ == '__main__':\n    print('run')\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["already_wandb_enabled"] is True
    assert payload["recommended_entrypoint"] == "experiments/run.py"
    assert any(path.endswith("conf/wandb/default.yaml") for path in payload["wandb_related_files"])
    assert any("base_url" in step for step in payload["integration_steps"])


def test_onboard_wandb_project_plans_new_integration(tmp_path: Path) -> None:
    (tmp_path / "experiments").mkdir(parents=True)
    (tmp_path / "experiments" / "train.py").write_text(
        "import argparse\n\nif __name__ == '__main__':\n    parser = argparse.ArgumentParser()\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["already_wandb_enabled"] is False
    assert "conf/wandb/default.yaml" in payload["proposed_files"]
    assert any("base_url" in step for step in payload["integration_steps"])
