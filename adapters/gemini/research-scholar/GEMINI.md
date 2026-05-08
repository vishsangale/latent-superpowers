# Research Scholar for Gemini

Generated from `core/research-scholar/skill-spec.yaml`.

## Purpose

Construct a comprehensive frontier summary for a given research domain.



## Use When

- The task involves researching state-of-the-art literature.
- The Theoretician needs a frontier summary to generate hypotheses.

## Avoid When

- Generating hypotheses.
- Implementing code.

## Working Rules

- Query available vector databases and knowledge bases.
- Identify the edge of current knowledge.
- Extract technical gaps.
- Collate significant citations.

## Safety Rules

- Do not generate hypotheses yourself.
- Rely on empirical evidence over intuition.

## Shared Core

- Skill root: `../../../core/research-scholar`
- Scripts: `../../../core/research-scholar/scripts`
- References: `../../../core/research-scholar/references`

## Command Surface



## Workflows



## References



## Expected Outputs

- A scholar_memo.md containing Domain Overview, Current Frontier, Identified Whitespace, and Key Citations.
