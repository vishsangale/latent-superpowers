# Workflow

1. Profile the real command first.
2. Capture wall time, memory, and GPU utilization in the same run when possible.
3. Summarize one profile before comparing multiple profiles.
4. Use Torch trace analysis only when a trace exists.
5. Recommend changes in ranked order, not as an unstructured list.

## Default order

1. `profile_command.py`
2. `summarize_profile.py`
3. `compare_profiles.py`
4. `summarize_torch_trace.py`
