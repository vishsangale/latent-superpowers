# Hydra Onboarding

## Goal

Introduce Hydra into a training repo without losing clarity around entrypoints, defaults, or run reproducibility.

## Recommended Order

1. Pick one primary entrypoint.
2. Create one config root.
3. Move current default arguments into a single base config.
4. Split only the high-variance dimensions into config groups.
5. Add output-directory and sweep conventions.
6. Validate single-run before multirun.

## Things To Avoid

- adding Hydra to multiple entrypoints at once
- creating both `conf/` and `configs/` in the same migration
- mixing legacy argparse defaults with Hydra defaults for the same field
- introducing sweeps before single-run reproducibility works

## Minimum Validation

- `--cfg job --resolve` works
- one single-run works
- one scalar override works
- one group-selection override works
- one short multirun works
- `.hydra/` metadata is complete enough for recovery
