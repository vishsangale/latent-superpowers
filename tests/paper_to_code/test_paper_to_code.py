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


def test_model_section_captures_mlp_projection_attention_language(ml_architecture_summary: Path) -> None:
    """Model section must capture sentences about MLP, projections, attention, hidden size,
    and linear layers even when words like 'model'/'architecture'/'encoder' are absent."""
    result = subprocess.run(
        [sys.executable, str(EXTRACT), str(ml_architecture_summary), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    model_sentences = payload["sections"]["model"]
    assert len(model_sentences) >= 5, (
        f"Model section only captured {len(model_sentences)} sentences. "
        f"Expected >= 5 sentences about MLP, projection, attention, hidden, linear.\n"
        f"Got: {model_sentences}"
    )


def test_venv_excluded_from_repo_search(paper_summary: Path, paper_repo_with_venv: Path) -> None:
    """Top repo matches must not include .venv/ paths even when they contain more matches."""
    result = subprocess.run(
        [sys.executable, str(MAP), str(paper_summary), "--repo", str(paper_repo_with_venv), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    for match in payload["top_matches"]:
        assert ".venv" not in match["path"], f".venv file leaked into top_matches: {match['path']}"


def test_staged_plan_references_missing_components(paper_summary: Path, paper_repo: Path) -> None:
    """Staged plan stages must reference the missing component names, not just generic text."""
    result = subprocess.run(
        [sys.executable, str(SCAFFOLD), str(paper_summary), "--repo", str(paper_repo), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    missing = payload.get("missing_components", [])
    if missing:
        stage_text = " ".join(s["stage"] + " " + s["goal"] for s in payload["stages"]).lower()
        for component in missing:
            assert component.lower() in stage_text, (
                f"Missing component '{component}' not referenced in any stage. "
                f"Stages must be specific to gap map findings."
            )


def test_common_words_excluded_from_key_terms(paper_summary: Path) -> None:
    """Generic ML words that appear everywhere must not be in key_terms."""
    result = subprocess.run(
        [sys.executable, str(EXTRACT), str(paper_summary), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    key_terms_lower = [t.lower() for t in payload["key_terms"]]
    too_generic = {"learning", "test", "time", "paper", "note", "each", "over", "also", "does", "have"}
    found = too_generic & set(key_terms_lower)
    assert not found, f"Generic words leaked into key_terms: {found}"


def test_map_and_scaffold_plan(paper_summary: Path, paper_repo: Path) -> None:
    mapped = subprocess.run(
        [sys.executable, str(MAP), str(paper_summary), "--repo", str(paper_repo), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    mapped_payload = json.loads(mapped.stdout)
    assert mapped_payload["top_matches"]

    plan = subprocess.run(
        [sys.executable, str(SCAFFOLD), str(paper_summary), "--repo", str(paper_repo), "--json"],
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
