# Self-Hosted W&B

Use this reference when the task is about connecting to an existing W&B server or clarifying whether a project is using the default cloud deployment or a self-hosted instance.

## Context signals

- `WANDB_BASE_URL`: explicit server base URL
- `WANDB_API_KEY`: auth token present in the environment
- `WANDB_ENTITY`: default entity
- `WANDB_PROJECT`: default project
- `WANDB_MODE`: `online`, `offline`, or `disabled`

## Practical flow

1. Resolve context first with `check_wandb_context.py`.
2. If a non-default base URL is expected, verify it with `check_wandb_server.py`.
3. Separate server reachability from run logging logic.
4. Keep an offline fallback path available while server configuration is being debugged.

## Limits

- A reachable base URL does not guarantee valid auth or permission to a project.
- Offline run inspection does not reveal server-side consumers or dashboard state.
- Provisioning a self-hosted W&B server is out of scope for the current skill; this skill currently validates configuration and connectivity only.
