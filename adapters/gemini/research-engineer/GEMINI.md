# Research Engineer for Gemini

Generated from `core/research-engineer/skill-spec.yaml`.

## Purpose

Translates a theoretical hypothesis into a robust, executable experiment workspace.



## Use When

- A hypothesis_memo.md is ready for implementation.
- An execution error needs debugging.

## Avoid When

- Generating hypotheses.
- Reviewing final metrics and writing papers.

## Working Rules

- Read hypothesis_memo.md.
- Generate all necessary code and configuration.
- Enforce strict experiment tracking.
- Apply surgical fixes during debugging.

## Safety Rules

- Code must contain proper error handling.
- Hardcode metrics tracking.
- If you encounter the same error multiple times (e.g., 3), explicitly abort and output engineer_failure_log.md.

## Shared Core

- Skill root: `../../../core/research-engineer`
- Scripts: `../../../core/research-engineer/scripts`
- References: `../../../core/research-engineer/references`

## Command Surface



## Workflows



## References



## Expected Outputs

- A runnable experiment directory with train.py, requirements.txt/Dockerfile, etc.
