from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "ablation-analysis"
    / "scripts"
    / "compare_ablations.py"
)


def test_compare_ablations_groups_variants(ablation_store: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--mlflow-uri",
            str(ablation_store),
            "--mlflow-experiment-name",
            "recsys",
            "--metric",
            "avg_reward",
            "--variant-key",
            "agent.lr",
            "--baseline",
            "agent.lr=0.01",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["baseline_label"] == "agent.lr=0.01"
    assert payload["rows"][0]["label"] == "agent.lr=0.001"
    assert payload["rows"][0]["delta_vs_baseline"] > 0
