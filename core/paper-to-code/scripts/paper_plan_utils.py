#!/usr/bin/env python3
"""Shared helpers for paper-to-code commands."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Any


SECTION_PATTERNS = {
    "model": [r"\bmodel\b", r"\barchitecture\b", r"\bencoder\b", r"\bdecoder\b", r"\bnetwork\b"],
    "objective": [r"\bloss\b", r"\bobjective\b", r"\breward\b", r"\boptimi[sz]e\b"],
    "data": [r"\bdataset\b", r"\bdata\b", r"\bpreprocess", r"\bfeature\b", r"\bcontext\b"],
    "training": [r"\btrain", r"\boptimization\b", r"\bschedule\b", r"\bepoch\b", r"\bbatch\b"],
    "inference": [r"\binference\b", r"\bserv", r"\bdecode\b", r"\brank\b"],
    "evaluation": [r"\beval", r"\bmetric\b", r"\bbaseline\b", r"\bablation\b", r"\bbenchmark\b"],
    "reproducibility": [r"\bseed\b", r"\breproduce\b", r"\bconfig\b", r"\bcheckpoint\b"],
}


@dataclass
class MethodPlan:
    title: str
    source_path: str
    raw_summary: str
    sections: dict[str, list[str]]
    key_terms: list[str]
    missing_details: list[str]


def read_text_input(path: str) -> str:
    target = Path(path)
    return target.read_text(encoding="utf-8")


def split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]


def extract_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {key: [] for key in SECTION_PATTERNS}
    sentences = split_sentences(text)
    for sentence in sentences:
        lowered = sentence.lower()
        for section, patterns in SECTION_PATTERNS.items():
            if any(re.search(pattern, lowered) for pattern in patterns):
                sections[section].append(sentence)
    return sections


def extract_key_terms(text: str) -> list[str]:
    candidates = re.findall(r"\b[A-Za-z][A-Za-z0-9_-]{3,}\b", text)
    stopwords = {
        "this",
        "that",
        "with",
        "from",
        "into",
        "using",
        "their",
        "they",
        "then",
        "than",
        "which",
        "where",
        "when",
        "baseline",
        "training",
        "evaluation",
        "method",
    }
    ordered: list[str] = []
    for item in candidates:
        lowered = item.lower()
        if lowered in stopwords:
            continue
        if item not in ordered:
            ordered.append(item)
    return ordered[:40]


def infer_missing_details(sections: dict[str, list[str]]) -> list[str]:
    missing = []
    if not sections["model"]:
        missing.append("Model or architecture details are missing or underspecified.")
    if not sections["objective"]:
        missing.append("Objective or loss details are missing or underspecified.")
    if not sections["evaluation"]:
        missing.append("Evaluation details or baseline comparisons are missing.")
    if not sections["training"]:
        missing.append("Training procedure details are missing.")
    return missing


def build_method_plan(path: str) -> MethodPlan:
    raw = read_text_input(path)
    title = Path(path).stem.replace("_", " ").replace("-", " ").title()
    sections = extract_sections(raw)
    return MethodPlan(
        title=title,
        source_path=str(Path(path).resolve()),
        raw_summary=raw,
        sections=sections,
        key_terms=extract_key_terms(raw),
        missing_details=infer_missing_details(sections),
    )


def plan_to_dict(plan: MethodPlan) -> dict[str, Any]:
    return asdict(plan)


def load_plan(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def search_repo(repo_path: str, key_terms: list[str]) -> list[dict[str, Any]]:
    root = Path(repo_path).resolve()
    matches: list[dict[str, Any]] = []
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if ".git" in file_path.parts or "__pycache__" in file_path.parts:
            continue
        if file_path.stat().st_size > 200_000:
            continue
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        file_matches = [term for term in key_terms if term.lower() in text.lower()]
        if file_matches:
            matches.append(
                {
                    "path": str(file_path),
                    "match_count": len(file_matches),
                    "matched_terms": file_matches[:10],
                }
            )
    matches.sort(key=lambda row: (-row["match_count"], row["path"]))
    return matches[:40]


def repo_gap_map(plan: dict[str, Any], repo_path: str) -> dict[str, Any]:
    matches = search_repo(repo_path, plan["key_terms"])
    mapped_sections: dict[str, list[dict[str, Any]]] = {}
    for section, sentences in plan["sections"].items():
        if not sentences:
            continue
        section_terms = extract_key_terms(" ".join(sentences))[:12]
        section_matches = [match for match in matches if any(term in match["matched_terms"] for term in section_terms)]
        mapped_sections[section] = section_matches[:8]

    missing_components = [
        section
        for section, sentences in plan["sections"].items()
        if sentences and not mapped_sections.get(section)
    ]
    return {
        "repo_path": str(Path(repo_path).resolve()),
        "top_matches": matches,
        "mapped_sections": mapped_sections,
        "missing_components": missing_components,
    }


def staged_plan(plan: dict[str, Any], gap_map: dict[str, Any]) -> dict[str, Any]:
    stages = [
        {
            "stage": "Define interfaces and configs",
            "focus": ["model", "training", "reproducibility"],
            "goal": "Create the config and integration surface before large code changes.",
        },
        {
            "stage": "Implement method core",
            "focus": ["model", "objective", "data"],
            "goal": "Add the method-specific modules and training logic.",
        },
        {
            "stage": "Wire evaluation and baselines",
            "focus": ["evaluation"],
            "goal": "Ensure the method can be compared against baselines and ablations.",
        },
        {
            "stage": "Validate and iterate",
            "focus": ["reproducibility", "evaluation"],
            "goal": "Run smoke tests, baseline checks, and ablations before broader experiments.",
        },
    ]
    return {
        "title": plan["title"],
        "missing_details": plan["missing_details"],
        "missing_components": gap_map["missing_components"],
        "stages": stages,
        "top_repo_matches": gap_map["top_matches"][:10],
    }


def evaluation_items(plan: dict[str, Any]) -> dict[str, list[str]]:
    evaluation_sentences = plan["sections"].get("evaluation", [])
    items = {
        "must_have": [
            "Reproduce the primary target metric from the paper summary.",
            "Compare against at least one baseline already present in the repo.",
            "Run a smoke test on a tiny configuration before full experiments.",
        ],
        "ablations": [
            "Ablate the new method component against the nearest baseline.",
            "Measure sensitivity to seeds or one key hyperparameter.",
        ],
        "efficiency": [
            "Measure runtime or memory impact relative to baseline.",
        ],
    }
    if any("robust" in sentence.lower() or "generaliz" in sentence.lower() for sentence in evaluation_sentences):
        items["ablations"].append("Add a robustness or generalization check that matches the paper claim.")
    return items

