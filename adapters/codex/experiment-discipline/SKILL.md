---
name: experiment-discipline
description: Use when the task involves designing an experiment, deciding what metrics to track, setting up logging, selecting baselines, analyzing ablations, or reporting negative results.
---

# Experiment Discipline

## Overview

Enforce methodological rigor in experiment design, logging, ablations, and baseline reporting. This Codex adapter is intentionally thin and delegates real functionality to the shared core under `../../../core/experiment-discipline`.

## Use This Skill When

- The user is starting a new feature branch or experiment and asking what code to write first.
- The agent is generating training loops or tracking integration code.
- The user reports an experiment that works, and the agent needs to verify why.
- The agent must compare a new result against baselines.

## Do Not Use This Skill For

- Purely software engineering refactors with no empirical component.
- Doing raw metric math (use ablation-analysis directly instead).

## Operating Principles

- Eval-first design — Build evaluation infrastructure before running experiments. Metrics and baselines defined upfront, not retrofitted.
- Reproducibility by default — Log seeds, hyperparameters, hardware specs, and software versions. Every result should be re-runnable.
- Ablation requirements — Don't claim a component helps without isolating its contribution. No "kitchen sink" results.
- Baseline honesty — Compare against strong, recent baselines — not strawmen. State clearly when a proper baseline wasn't run and why.
- Negative result reporting — Document what didn't work and why. Failed experiments carry as much signal as successful ones.

## Safety Rules

- Never recommend skipping baselines to save time.
- Never generate a training loop without simultaneously demanding an evaluation strategy.
- If the user provides a "kitchen sink" result, insist on an ablation before declaring victory.

## Shared Commands

- `python ../../../core/experiment-discipline/scripts/check_eval_first.py`: Verifies that an evaluation strategy is specified before proceeding with training logic.
- `python ../../../core/experiment-discipline/scripts/verify_reproducibility.py`: Scans configuration for seed setting and environment tracking requirements.
- `python ../../../core/experiment-discipline/scripts/enforce_baseline.py`: Helper to prompt explicit baseline definition for any newly reported empirical result.

## Shared References

- `../../../core/experiment-discipline/references/eval-first.md`: Best practices for implementing evals before training starts.
- `../../../core/experiment-discipline/references/reproducibility-defaults.md`: Checklists for what must be logged (seeds, hardware, env).
- `../../../core/experiment-discipline/references/baselines-and-ablations.md`: Rules for avoiding 'kitchen sink' claims and ensuring baseline honesty.
- `../../../core/experiment-discipline/references/negative-results.md`: Guidelines on valuing and documenting failed experiments.

## Common Workflows

### Design an experiment

1. Force definition of evaluation metrics and baselines.
2. Ensure reproducibility metadata will be logged.
3. Proceed to training orchestration.

Helpers: `check_eval_first.py`, `verify_reproducibility.py`

### Report an empirical result

1. Explicitly state the baseline.
2. Ensure an ablation separates compounded factors.
3. State clearly if it was a negative result.

Helpers: `enforce_baseline.py`

## Expected Outputs

- Eval scripts and metric definitions proposed before training code.
- Checklists of logged hyperparameters and seeds.
- An isolated ablation plan for complex additions.
- A clear comparison table featuring a strong baseline.
