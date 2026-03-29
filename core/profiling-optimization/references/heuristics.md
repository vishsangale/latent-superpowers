# Heuristics

- Low GPU utilization with low memory pressure often suggests input or launch overhead.
- High wall time with low CPU and GPU utilization often means the command is blocked or idle.
- High peak RSS with low throughput suggests data or batch shaping overhead.
- High GPU memory saturation with short wall time often points to batch-size or activation pressure.
- One profile is enough to identify hotspots, but not enough to prove a stable improvement.

## Recommendation priorities

1. Fix bottlenecks that dominate wall time.
2. Reduce peak memory if it blocks larger or faster runs.
3. Only micro-optimize operators after command-level bottlenecks are clear.
