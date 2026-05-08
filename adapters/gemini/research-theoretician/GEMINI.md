# Research Theoretician for Gemini

Generated from `core/research-theoretician/skill-spec.yaml`.

## Purpose

Generates novel, theoretically sound, and testable research hypotheses.



## Use When

- The Scholar has provided a frontier summary.
- A novel hypothesis needs to be formulated.

## Avoid When

- Writing implementation code.
- Running experiments.

## Working Rules

- Read scholar_memo.md to ground yourself.
- Formulate 1-3 testable hypotheses.
- Provide formal mathematical definitions or abstract algorithmic pseudocode.
- Define baseline framework and metric to beat.

## Safety Rules

- Ensure hypothesis is actionable and executable within a single node.
- Do not propose incremental tuning.
- Do not duplicate work already in scholar_memo.md.

## Shared Core

- Skill root: `../../../core/research-theoretician`
- Scripts: `../../../core/research-theoretician/scripts`
- References: `../../../core/research-theoretician/references`

## Command Surface



## Workflows



## References



## Expected Outputs

- A hypothesis_memo.md containing Core Hypothesis, Theoretical Justification, Proposed Methodology, and Expected Metrics.
