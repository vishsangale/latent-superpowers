from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def hydra_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "hydra-repo"
    (repo / "conf" / "model").mkdir(parents=True)
    (repo / "outputs" / "2026-03-29" / "00-00-00" / ".hydra").mkdir(parents=True)

    (repo / "train.py").write_text(
        """
import hydra


@hydra.main(version_base=None, config_path="conf", config_name="train")
def main(cfg):
    print(cfg)


if __name__ == "__main__":
    main()
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (repo / "conf" / "train.yaml").write_text(
        """
defaults:
  - model: baseline
  - _self_

seed: 7
hydra:
  run:
    dir: outputs/${now:%Y-%m-%d}/${now:%H-%M-%S}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (repo / "conf" / "model" / "baseline.yaml").write_text(
        """
hidden_dim: 64
dropout: 0.1
""".strip()
        + "\n",
        encoding="utf-8",
    )
    run_dir = repo / "outputs" / "2026-03-29" / "00-00-00"
    (run_dir / ".hydra" / "config.yaml").write_text(
        """
seed: 7
model:
  hidden_dim: 64
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (run_dir / ".hydra" / "hydra.yaml").write_text(
        """
runtime:
  cwd: /tmp/hydra-repo
  output_dir: outputs/2026-03-29/00-00-00
job:
  name: train
  num: 0
run:
  dir: outputs/2026-03-29/00-00-00
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (run_dir / ".hydra" / "overrides.yaml").write_text(
        """
- seed=7
- model=baseline
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "model.ckpt").write_text("checkpoint", encoding="utf-8")
    return repo
