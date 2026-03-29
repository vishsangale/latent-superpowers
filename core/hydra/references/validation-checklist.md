# Validation Checklist

## Before Recommending A Command

- Confirm the entrypoint and config root.
- Confirm the config name.
- Confirm whether the request is single-run or multirun.
- Confirm whether the launcher is local or remote.
- Confirm where outputs and checkpoints will land.

## Before Claiming Reproducibility

- Effective config available
- Original overrides available
- Entry script identified
- Code revision known or explicitly missing
- Output directory and checkpoint path identified

## Safety Rule

Prefer dry-run config rendering to execution whenever the user's request is explanation, planning, or debugging.
