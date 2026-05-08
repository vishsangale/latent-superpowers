#!/usr/bin/env python3
"""
Generate thin agent adapters from shared skill specs.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "core"
ADAPTERS_DIR = ROOT / "adapters"


def load_spec(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def normalize_text(item: Any) -> str:
    if isinstance(item, dict):
        parts = []
        for key, value in item.items():
            parts.append(f"{key}: {value}")
        return "; ".join(parts)
    return str(item)


def bullet_list(items: list[str], indent: str = "") -> str:
    return "\n".join(f"{indent}- {normalize_text(item)}" for item in items)


def numbered_steps(items: list[str]) -> str:
    return "\n".join(f"{idx}. {item}" for idx, item in enumerate(items, start=1))


def commands_block(commands: list[dict[str, Any]], script_root: str) -> str:
    lines = []
    for command in commands:
        lines.append(f"- `python {script_root}/{command['name']}`: {command['summary']}")
    return "\n".join(lines)


def references_block(references: list[dict[str, Any]], core_skill_root: str) -> str:
    lines = []
    for reference in references:
        lines.append(f"- `{core_skill_root}/{reference['path']}`: {reference['summary']}")
    return "\n".join(lines)


def workflow_block(workflows: list[dict[str, Any]]) -> str:
    parts = []
    for workflow in workflows:
        parts.append(f"### {workflow['name']}")
        parts.append("")
        parts.append(numbered_steps(workflow["steps"]))
        if workflow.get("helpers"):
            parts.append("")
            helpers = ", ".join(f"`{helper}`" for helper in workflow["helpers"])
            parts.append(f"Helpers: {helpers}")
        parts.append("")
    return "\n".join(parts).rstrip()


def generate_codex_skill(spec: dict[str, Any], core_skill_root: str) -> str:
    return f"""---
name: {spec['name']}
description: {spec['description']}
---

# {spec['title']}

## Overview

{spec['summary']} This Codex adapter is intentionally thin and delegates real functionality to the shared core under `{core_skill_root}`.

## Use This Skill When

{bullet_list(spec['use_when'])}

## Do Not Use This Skill For

{bullet_list(spec['avoid_when'])}

## Operating Principles

{bullet_list(spec['principles'])}

## Safety Rules

{bullet_list(spec['safety_rules'])}

## Shared Commands

{commands_block(spec['commands'], f"{core_skill_root}/scripts")}

## Shared References

{references_block(spec['references'], core_skill_root)}

## Common Workflows

{workflow_block(spec['workflows'])}

## Expected Outputs

{bullet_list(spec['expected_outputs'])}
"""


def generate_openai_yaml(spec: dict[str, Any]) -> str:
    codex = spec["codex"]
    return "\n".join(
        [
            "interface:",
            f'  display_name: "{codex["display_name"]}"',
            f'  short_description: "{codex["short_description"]}"',
            f'  default_prompt: "{codex["default_prompt"]}"',
            "",
        ]
    )


def generate_generic_prompt(spec: dict[str, Any], adapter_name: str, core_skill_root: str) -> str:
    adapter_title = {
        "claude-code": "Claude Code",
        "gemini": "Gemini",
        "opencode": "OpenCode",
    }[adapter_name]
    frontmatter = ""
    if adapter_name == "opencode":
        frontmatter = (
            "---\n"
            f"name: {spec['name']}\n"
            f"description: {spec['description']}\n"
            "---\n\n"
        )
    return f"""{frontmatter}# {spec['title']} for {adapter_title}

Generated from `core/{spec['name']}/skill-spec.yaml`.

## Purpose

{spec['summary']}

{spec['generic_adapter_note'].strip()}

## Use When

{bullet_list(spec['use_when'])}

## Avoid When

{bullet_list(spec['avoid_when'])}

## Working Rules

{bullet_list(spec['principles'])}

## Safety Rules

{bullet_list(spec['safety_rules'])}

## Shared Core

- Skill root: `{core_skill_root}`
- Scripts: `{core_skill_root}/scripts`
- References: `{core_skill_root}/references`

## Command Surface

{commands_block(spec['commands'], f"{core_skill_root}/scripts")}

## Workflows

{workflow_block(spec['workflows'])}

## References

{references_block(spec['references'], core_skill_root)}

## Expected Outputs

{bullet_list(spec['expected_outputs'])}
"""


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate_skill(spec_path: Path) -> list[Path]:
    spec = load_spec(spec_path)
    skill_name = spec["name"]
    written: list[Path] = []

    codex_dir = ADAPTERS_DIR / "codex" / skill_name
    codex_core_path = os.path.relpath(CORE_DIR / skill_name, codex_dir)
    write_file(codex_dir / "SKILL.md", generate_codex_skill(spec, codex_core_path))
    write_file(codex_dir / "agents" / "openai.yaml", generate_openai_yaml(spec))
    written.extend([codex_dir / "SKILL.md", codex_dir / "agents" / "openai.yaml"])

    generic_targets = {
        "claude-code": "CLAUDE.md",
        "gemini": "GEMINI.md",
        "opencode": "SKILL.md",
    }
    for adapter_name, filename in generic_targets.items():
        adapter_dir = ADAPTERS_DIR / adapter_name / skill_name
        adapter_core_path = os.path.relpath(CORE_DIR / skill_name, adapter_dir)
        write_file(
            adapter_dir / filename,
            generate_generic_prompt(spec, adapter_name, adapter_core_path),
        )
        written.append(adapter_dir / filename)

    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate agent adapters from shared skill specs.")
    parser.add_argument("--skill", help="Specific skill name to generate")
    args = parser.parse_args()

    spec_paths = []
    if args.skill:
        spec_paths.append(CORE_DIR / args.skill / "skill-spec.yaml")
    else:
        spec_paths.extend(sorted(CORE_DIR.glob("*/skill-spec.yaml")))

    written: list[Path] = []
    for spec_path in spec_paths:
        if not spec_path.exists():
            raise FileNotFoundError(f"Missing spec: {spec_path}")
        written.extend(generate_skill(spec_path))

    for path in written:
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
