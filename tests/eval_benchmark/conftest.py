from __future__ import annotations

from pathlib import Path

import pytest

from tests.local_dashboard.conftest import ablation_store  # noqa: F401
from tests.wandb.conftest import sample_runs, wandb_offline_dir  # noqa: F401


@pytest.fixture()
def mlflow_with_history(ablation_store: Path) -> Path:
    artifact_root = ablation_store / "123" / "run_a" / "artifacts"
    artifact_root.mkdir(parents=True, exist_ok=True)
    (artifact_root / "run_a-history.json").write_text(
        '[{"episode": 0, "reward": 0.5, "ctr": 0.1}, {"episode": 1, "reward": 1.0, "ctr": 0.2}]',
        encoding="utf-8",
    )
    (artifact_root / "run_a-train-history.json").write_text(
        '[{"episode": 0, "reward": 0.2}]',
        encoding="utf-8",
    )
    return ablation_store
