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
