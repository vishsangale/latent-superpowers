# Research Critic for Gemini

Generated from `core/research-critic/skill-spec.yaml`.

## Purpose

Evaluates empirical results and drafts scientific output.



## Use When

- An experiment has completed and metrics/logs are available.
- A scientific paper or failure analysis needs drafting.

## Avoid When

- Generating hypotheses.
- Writing experimental code.

## Working Rules

- Read scholar_memo.md and hypothesis_memo.md.
- Read execution logs and metrics.
- Provide a brutal, objective assessment.
- Draft a formal paper or rigorous failure analysis.

## Safety Rules

- Do not hallucinate results.
- Never declare success based solely on training metrics.
- Check for data leakage or overfitting.
- Provide actionable pivot directions on failure.

## Shared Core

- Skill root: `../../../core/research-critic`
- Scripts: `../../../core/research-critic/scripts`
- References: `../../../core/research-critic/references`

## Command Surface



## Workflows



## References



## Expected Outputs

- paper.tex (if validated) or failure_analysis.md (if invalidated).
