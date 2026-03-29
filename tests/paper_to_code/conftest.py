from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def paper_summary(tmp_path: Path) -> Path:
    path = tmp_path / "paper-summary.md"
    path.write_text(
        """
# Slate-Aware Policy Learning

The method introduces a slate-aware ranking model for recommendation.
The model uses a neural encoder over user and item context and optimizes a reward-aware objective.
Training uses mini-batches, Adam, and replay-style updates over logged interactions.
Evaluation reports NDCG, CTR, and reward against a random baseline and a contextual baseline.
The paper includes ablations on slate size and reward shaping.
Reproducibility requires fixed seeds, saved configs, and checkpointed policies.
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture()
def paper_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "paper-repo"
    (repo / "src").mkdir(parents=True)
    (repo / "configs").mkdir(parents=True)
    (repo / "README.md").write_text(
        """
# Slate Aware Recsys

Neural encoder ranking model with reward-aware training and replay updates.
Evaluation uses NDCG, CTR, reward, random baseline, and contextual baseline.
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (repo / "src" / "model.py").write_text(
        """
class SlateEncoder:
    def __init__(self):
        self.objective = "reward-aware objective"


def train_minibatch(batch):
    return "Adam replay updates over logged interactions"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (repo / "configs" / "train.yaml").write_text(
        """
seed: 7
checkpoint: checkpoints/latest.pt
metrics:
  - ndcg
  - ctr
  - reward
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return repo
