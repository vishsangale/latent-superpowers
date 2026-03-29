# Repo Discovery

## Search Targets

- `@hydra.main`
- `hydra.compose`
- `OmegaConf`
- `defaults:`
- `hydra.run.dir`
- `hydra.sweep.dir`
- config directories such as `conf/`, `configs/`, `config/`

## Outputs To Collect

- entrypoint script or module
- config path and config name
- config groups and defaults chains
- launcher or sweeper plugins
- output directory conventions

## Ambiguity Rules

- If the repo has multiple entrypoints, present them all and ask only if needed.
- If the config root is inferred rather than explicit, state that clearly.
- If a launcher plugin is referenced but not installed, separate planning from execution.
