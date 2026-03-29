# Workflow

- Start with `plan_runs.py` whenever the run matrix is larger than a single command.
- Use explicit `--set key=v1,v2,...` factors and explicit `--seeds` instead of hidden shell brace expansion.
- Treat the manifest as the source of truth for what was intended to run.
- Use `launch_runs.py` for new work and `resume_runs.py` only after a manifest already exists.
- Use `summarize_manifest.py` to answer "what ran, what failed, and which run looked best from stdout?" without opening logs manually.
