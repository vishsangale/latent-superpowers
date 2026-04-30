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


@pytest.fixture()
def ml_architecture_summary(tmp_path: Path) -> Path:
    """A paper summary that describes an architecture using MLP/projection/attention language
    without ever using the words 'model', 'architecture', 'encoder', 'decoder', or 'network'."""
    path = tmp_path / "ml-arch-summary.md"
    path.write_text(
        """
# Fast Weight Memory

The memory is a small MLP with fast weights W1 and W2 as the hidden layer projections.
Key and value projection matrices W_K and W_V transform input tokens into the associative space.
The attention mechanism reads from the hidden memory state using a learned query projection.
A linear layer maps each token to its corresponding momentum, learning rate, and forgetting scalars.
The inner gradient is computed via torch.func.grad applied to a pure function over weight tensors.
Projection weights are outer-loop parameters trained via the language modelling objective.
The hidden size of the MLP is set to 64 by default.
MAC concatenates memory tokens as a prefix so attention can attend to them directly.
The output gate multiplies the attention result elementwise with a second read from the MLP.
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture()
def paper_repo_with_venv(paper_repo: Path) -> Path:
    """Same repo but with a .venv directory full of matching content."""
    venv_site = paper_repo / ".venv" / "lib" / "python3.12" / "site-packages" / "somelib-1.0.dist-info"
    venv_site.mkdir(parents=True)
    (venv_site / "METADATA").write_text(
        # Repeat all the paper terms so this file would win without venv exclusion.
        "model encoder objective reward train evaluation baseline ndcg ctr slate ranking neural\n" * 50,
        encoding="utf-8",
    )
    return paper_repo
