---
name: paper-to-code
description: "Purpose"
---

# Paper To Code for OpenCode

Generated from `core/paper-to-code/skill-spec.yaml`.

## Purpose

Turn paper summaries or method notes into implementation plans, repo gap maps, and evaluation checklists.

This adapter is a thin wrapper over the shared paper-to-code core. Prefer invoking the CLI helpers under the shared core before writing an ad-hoc plan.

## Use When

- The user wants to implement a paper or new method in an existing repo.
- The task is to extract architecture, loss, data, training, and evaluation requirements from a paper summary or notes.
- The user wants a repo-aware baseline plan rather than a generic reading of the paper.

## Avoid When

- Pure experiment comparison that belongs to ablation-analysis.
- Low-level config work that belongs to Hydra.
- Claiming implementation completeness when the paper summary is incomplete.

## Working Rules

- Extract concrete requirements before mapping the repo.
- Separate what the paper requires from what the repo already has.
- Produce staged plans with explicit missing pieces and risks.
- Treat evaluation design as part of implementation, not an afterthought.

## Safety Rules

- Prefer planning and mapping before code mutation.
- State missing paper details and uncertain assumptions explicitly.
- Do not pretend the paper is fully specified if the input summary is partial.

## Shared Core

- Skill root: `../../../core/paper-to-code`
- Scripts: `../../../core/paper-to-code/scripts`
- References: `../../../core/paper-to-code/references`

## Command Surface

- `python ../../../core/paper-to-code/scripts/extract_method_plan.py`: Parse a paper summary or method note into structured implementation requirements.
- `python ../../../core/paper-to-code/scripts/map_repo_gaps.py`: Search a repo for matching components and identify missing method requirements.
- `python ../../../core/paper-to-code/scripts/scaffold_baseline_plan.py`: Turn a method plan and repo map into a staged implementation plan.
- `python ../../../core/paper-to-code/scripts/eval_checklist.py`: Generate a concrete evaluation and ablation checklist from a method plan.

## Workflows

### Build a repo-aware implementation plan

1. Parse the method summary into architecture, objective, data, training, and evaluation requirements.
2. Search the repo for existing matches and likely owner files.
3. Mark missing components and risky assumptions.
4. Emit a staged implementation plan with validation points.

Helpers: `extract_method_plan.py`, `map_repo_gaps.py`, `scaffold_baseline_plan.py`

### Define the evaluation work

1. Identify the paper’s target metrics, baselines, and robustness claims.
2. Turn them into a concrete local evaluation checklist.
3. Separate must-have evals from nice-to-have ablations.

Helpers: `extract_method_plan.py`, `eval_checklist.py`

## References

- `../../../core/paper-to-code/references/workflow.md`: Paper decomposition, repo mapping, and staged planning flow.
- `../../../core/paper-to-code/references/component-taxonomy.md`: The method components this skill extracts and maps.
- `../../../core/paper-to-code/references/eval-checklist.md`: Evaluation categories, baselines, and ablation expectations.

## Expected Outputs

- a structured method plan
- a repo gap map
- a staged implementation plan
- an evaluation checklist with concrete items
