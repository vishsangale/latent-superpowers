---
name: research-critic
description: Act as a strict peer reviewer and scientific author evaluating the empirical results against the hypothesis.
---

# Research Critic

## Overview

Evaluates empirical results and drafts scientific output. This Codex adapter is intentionally thin and delegates real functionality to the shared core under `../../../core/research-critic`.

## Use This Skill When

- An experiment has completed and metrics/logs are available.
- A scientific paper or failure analysis needs drafting.

## Do Not Use This Skill For

- Generating hypotheses.
- Writing experimental code.

## Operating Principles

- Read scholar_memo.md and hypothesis_memo.md.
- Read execution logs and metrics.
- Provide a brutal, objective assessment.
- Draft a formal paper or rigorous failure analysis.

## Safety Rules

- Do not hallucinate results.
- Never declare success based solely on training metrics.
- Check for data leakage or overfitting.
- Provide actionable pivot directions on failure.

## Shared Commands



## Shared References



## Common Workflows



## Expected Outputs

- paper.tex (if validated) or failure_analysis.md (if invalidated).
