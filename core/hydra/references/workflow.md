# Hydra Workflow

## Purpose

Use this workflow to inspect and explain Hydra configuration behavior without jumping straight to execution.

## Standard Order

1. Detect Hydra signals in the repo.
2. Identify entrypoints and config roots.
3. Inspect defaults lists and config groups.
4. Reconstruct the effective config.
5. Explain the value path or failure source.
6. Only then plan or propose execution.

## Common Questions

### Where does this value come from?

- Check the defaults chain first.
- Then check file-local values.
- Then inspect command-line overrides.
- Then inspect interpolation and environment-variable expansion.

### Why did this override fail?

- Wrong group name
- Wrong package path
- Missing `+` or `++`
- Invalid sweep syntax
- Defaults entry pointing to a missing config

### How should multirun be planned?

- Separate application config from Hydra config.
- Confirm launcher or sweeper plugins before suggesting syntax.
- Show the final command and the expected output directory pattern.
