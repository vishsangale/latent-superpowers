from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture()
def dataset_root(tmp_path: Path) -> Path:
    root = tmp_path / "dataset"
    root.mkdir()
    (root / "train.csv").write_text(
        "user_id,item_id,label\n1,10,1\n2,11,0\n3,12,1\n",
        encoding="utf-8",
    )
    (root / "val.csv").write_text(
        "user_id,item_id,label\n4,20,1\n5,21,0\n",
        encoding="utf-8",
    )
    (root / "test.jsonl").write_text(
        "\n".join(
            [
                json.dumps({"user_id": 3, "item_id": 12, "label": 1}),
                json.dumps({"user_id": 6, "item_id": 30, "label": 0}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return root
