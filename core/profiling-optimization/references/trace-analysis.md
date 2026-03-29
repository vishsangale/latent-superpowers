# Trace Analysis

- Treat Torch profiler traces as operator-level evidence, not end-to-end truth.
- Group by operator name and category before looking at single events.
- Separate CPU operators from CUDA operators when the trace provides both.
- Long self-time operators are the first candidates for optimization.
- If the command-level profile already shows the run is mostly idle, trace analysis is secondary.
