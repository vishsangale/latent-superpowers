# Workflow

- Use `capture_run_context.py` before or after important experiment runs, especially before large sweeps.
- Use `verify_repro_context.py` to answer "am I still on the same code and runtime?" instead of guessing from memory.
- Use `reconstruct_local_run.py` to recover tracked params, metrics, and artifact locations when a run needs to be revisited.
- Use `diff_run_contexts.py` when two runs or snapshots disagree and you need an explicit change surface.
