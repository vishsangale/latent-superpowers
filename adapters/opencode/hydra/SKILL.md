# Hydra for OpenCode

Generated from `core/hydra/skill-spec.yaml`.

## Purpose

Inspect, explain, and safely plan Hydra-based experiment configuration workflows.

This adapter is a thin wrapper over the shared Hydra core. Prefer invoking the CLI helpers under core/hydra/scripts/ before writing custom reasoning or mutations.

## Use When

- The user mentions hydra, omegaconf, defaults, multirun, --cfg, launcher, or sweeper.
- The repo has conf/, configs/, @hydra.main, hydra.compose, or OmegaConf config groups.
- The task is to explain effective config values, debug overrides, recover prior run settings, prepare a sweep command, or onboard Hydra into a new project.

## Avoid When

- Generic training-loop debugging that does not depend on Hydra composition.
- Hosted experiment tracking tasks that belong to W&B or MLflow.
- Blind repo mutation. Use planning and preview-first flows unless the user explicitly asks to apply changes.

## Working Rules

- Inspect the local repo before assuming config roots, entrypoints, or launcher plugins.
- Prefer composition and dry-run inspection before execution.
- Treat reproducibility as a first-class output: effective config, entrypoint, overrides, output directory, and checkpoint location.
- Surface ambiguity explicitly when there are multiple config roots, entrypoints, or launchers.

## Safety Rules

- Prefer planning, preview, and dry-run commands before applying or executing anything.
- Do not launch jobs or mutate a repo unless the user explicitly requests that action.
- When scaffolding, keep preview as the default and require an explicit apply step for file writes.

## Shared Core

- Skill root: `../../../core/hydra`
- Scripts: `../../../core/hydra/scripts`
- References: `../../../core/hydra/references`

## Command Surface

- `python ../../../core/hydra/scripts/detect_hydra_project.py`: Identify config roots, entrypoints, config groups, defaults files, and output-directory patterns.
- `python ../../../core/hydra/scripts/render_effective_config.py`: Build a dry-run Hydra command and optionally execute it with --cfg and --resolve.
- `python ../../../core/hydra/scripts/find_run_config.py`: Recover config provenance from a Hydra run directory and surface reproducibility gaps.
- `python ../../../core/hydra/scripts/analyze_overrides.py`: Classify override text into assignment, add, delete, and sweep patterns.
- `python ../../../core/hydra/scripts/plan_multirun.py`: Plan a Hydra multirun command and estimate sweep size when the CLI syntax is enumerable.
- `python ../../../core/hydra/scripts/onboard_hydra_project.py`: Inspect a repo and produce an onboarding plan for Hydra adoption.
- `python ../../../core/hydra/scripts/scaffold_hydra_project.py`: Preview or apply a minimal Hydra scaffold for a new project using current entrypoint defaults.
- `python ../../../core/hydra/scripts/explain_value_origin.py`: Trace a final config value back to config files and CLI overrides.

## Workflows

### Explain a Hydra project

1. Detect the config root and entrypoint.
2. List config groups and the defaults chain.
3. Render or reconstruct the effective config.
4. Explain which file or override controls the requested value.

Helpers: `detect_hydra_project.py`, `render_effective_config.py`

### Debug an override

1. Normalize the exact command the user ran.
2. Separate defaults selection from field assignment overrides.
3. Check for group-name mismatches, interpolation breakage, and missing + or ++.
4. Show the minimal corrected command and the resulting config delta.

Helpers: `analyze_overrides.py`, `render_effective_config.py`

### Plan a sweep or multirun

1. Identify the target entrypoint, config name, and launcher mode.
2. Verify which parameters belong in Hydra sweep syntax versus application config.
3. Produce a readable launch plan with run naming, output layout, and failure points.
4. Do not submit the jobs unless the user explicitly asks.

Helpers: `analyze_overrides.py`, `plan_multirun.py`

### Recover a previous run

1. Locate the Hydra output directory or .hydra metadata.
2. Recover config.yaml, hydra.yaml, and overrides.yaml if present.
3. Reconstruct the original command and effective config.
4. Flag missing provenance such as code SHA, checkpoint path, or launcher metadata.

Helpers: `find_run_config.py`

### Onboard Hydra into a new project

1. Inspect the repo for likely training entrypoints, config directories, and framework conventions.
2. Produce a migration plan covering entrypoint wrapping, config-root layout, parameter migration, and output-directory conventions.
3. Preview a minimal scaffold rather than rewriting the project blindly.
4. Define a minimal validation sequence before any large refactor.

Helpers: `onboard_hydra_project.py`, `scaffold_hydra_project.py`

## References

- `../../../core/hydra/references/workflow.md`: Main inspection and planning workflow.
- `../../../core/hydra/references/repo-discovery.md`: Heuristics for finding Hydra usage in unfamiliar repos.
- `../../../core/hydra/references/validation-checklist.md`: Pre-launch and reproducibility checks.
- `../../../core/hydra/references/onboarding.md`: Recommended Hydra onboarding order and minimum validation plan.

## Expected Outputs

- the relevant entrypoint and config root
- the defaults chain or config groups in play
- the effective config or the exact path to it
- the command to reproduce the run
- a concrete onboarding or test plan when the repo is not yet Hydra-enabled
