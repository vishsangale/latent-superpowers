# Adapter Pattern

A v2 adapter wraps a benchmark for the verifier engine. The contract is small and fixed.

## Contract

```python
class _MyBenchmarkAdapter:
    benchmark_id: str = "my_benchmark"

    def run(
        self,
        plugin_factory: Callable[..., Any],
        *,
        # benchmark-specific kwargs (e.g., epochs, batch_size)
    ) -> tuple[float, dict[str, Any]]:
        ...
        return metric, extras


ADAPTER: _MyBenchmarkAdapter = _MyBenchmarkAdapter()
```

The verifier engine looks up `ADAPTER` by module path and calls `run(plugin_factory, ...)` once per seed inside the sandbox.

## Why `benchmark_id` is a class var

It is read by the engine before instantiation in some code paths (e.g., when listing registered benchmarks). It must match the key under which the baseline is registered in `baselines.py`.

## Why imports are deferred

`baselines.py` is imported during `v2_substrate_status` on the host. Top-level `import torch` adds ~1s of bootstrap latency every time the agent checks status. Imports inside `run()` are only paid when verification actually runs (inside the container).

## Why datasets must raise

If the dataset isn't mounted at `/datasets/<benchmark_id>/`, the adapter must raise `RuntimeError`. Silent fallback to `download=True` causes:
- Cache pollution (downloaded data isn't reproducible).
- Hangs in offline CI.
- Mismatched cache keys (downloaded vs. mounted produce different `Outcome.extras`).

The engine catches the `RuntimeError`, marks the seed as `error`, and surfaces it to the user via `stdout_tail`. Loud failure beats silent corruption.

## The (metric, extras) shape

- `metric: float` — a Python `float`, not `numpy.float64`. **Higher is better.** For loss-like natural metrics, return the negation.
- `extras: dict[str, Any]` — small JSON-serializable bag (train loss, dataset sizes, seed, etc.). Surfaces in `Outcome.extras` in the report.

## Annotated examples

### cifar10 (`src/arxiver/research_agent/v2/verifier/adapters/cifar10.py`)
- Reads `/datasets/cifar10` (raises if missing).
- Builds a tiny CNN, calls `plugin_factory(model.parameters())` to get the optimizer.
- Trains 5 epochs, returns test accuracy as a percentage. Higher-is-better.
- `extras = {"train_loss_final", "n_train", "n_test"}`.

### sparse_recovery (`src/arxiver/research_agent/v2/verifier/adapters/sparse_recovery.py`)
- No dataset mount — generates problems on-the-fly.
- `plugin_factory()` returns a solver `(A, y) -> x_recovered`.
- Returns a relative-error-derived score (higher-is-better).
