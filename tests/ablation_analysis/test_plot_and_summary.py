from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PLOT_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "ablation-analysis"
    / "scripts"
    / "plot_ablations.py"
)
SUMMARY_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "ablation-analysis"
    / "scripts"
    / "summarize_findings.py"
)


def test_plot_and_summary_outputs(ablation_store: Path, tmp_path: Path) -> None:
    out_path = tmp_path / "ablation.svg"
    subprocess.run(
        [
            sys.executable,
            str(PLOT_SCRIPT),
            "--mlflow-uri",
            str(ablation_store),
            "--mlflow-experiment-name",
            "recsys",
            "--metric",
            "avg_reward",
            "--variant-key",
            "agent.lr",
            "--out",
            str(out_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert out_path.exists()
    summary = subprocess.run(
        [
            sys.executable,
            str(SUMMARY_SCRIPT),
            "--mlflow-uri",
            str(ablation_store),
            "--mlflow-experiment-name",
            "recsys",
            "--metric",
            "avg_reward",
            "--variant-key",
            "agent.lr",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(summary.stdout)
    assert "Ablation Findings" in payload["findings_markdown"]
