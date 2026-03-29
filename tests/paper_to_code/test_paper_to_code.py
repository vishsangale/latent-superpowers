from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


EXTRACT = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "paper-to-code"
    / "scripts"
    / "extract_method_plan.py"
)
MAP = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "paper-to-code"
    / "scripts"
    / "map_repo_gaps.py"
)
SCAFFOLD = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "paper-to-code"
    / "scripts"
    / "scaffold_baseline_plan.py"
)
EVAL = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "paper-to-code"
    / "scripts"
    / "eval_checklist.py"
)


def test_extract_method_plan(paper_summary: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(EXTRACT), str(paper_summary), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["sections"]["model"]
    assert payload["sections"]["evaluation"]


def test_map_and_scaffold_plan(paper_summary: Path) -> None:
    repo = "/home/vishsangale/workspace/rl-recsys"
    mapped = subprocess.run(
        [sys.executable, str(MAP), str(paper_summary), "--repo", repo, "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    mapped_payload = json.loads(mapped.stdout)
    assert mapped_payload["top_matches"]

    plan = subprocess.run(
        [sys.executable, str(SCAFFOLD), str(paper_summary), "--repo", repo, "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    plan_payload = json.loads(plan.stdout)
    assert plan_payload["stages"]

    checklist = subprocess.run(
        [sys.executable, str(EVAL), str(paper_summary), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    checklist_payload = json.loads(checklist.stdout)
    assert checklist_payload["checklist"]["must_have"]
