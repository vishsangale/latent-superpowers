# Baseline Registry

The `REGISTRY` mapping in `src/arxiver/research_agent/v2/verifier/baselines.py` is the canonical source of baseline implementations. Every registered benchmark has exactly one `BaselineSpec`.

## BaselineSpec shape

```python
@dataclass(frozen=True, slots=True)
class BaselineSpec:
    benchmark_id: str
    baseline_ref: str          # versioned: "<id>/<impl>@v<N>"
    factory: Callable[..., Any]
```

The `factory` signature varies per benchmark — it must match the `plugin_factory` argument the adapter passes:

| benchmark_id | factory signature |
|---|---|
| `cifar10` | `(params) -> torch.optim.Optimizer` |
| `sparse_recovery` | `() -> Callable[[np.ndarray, np.ndarray], np.ndarray]` |
| `cot_compression` | `(hidden_dim) -> torch.nn.Module` |

Imports inside the factory are mandatory (same reason as adapters — host-side `import baselines` must be cheap).

## Versioning: `@vN`

`baseline_ref` is the only mechanism that invalidates cached reports. The format is `<benchmark_id>/<implementation_name>@v<N>` — for example, `sparse_recovery/omp@v1`.

**When to bump:**
- Changing hyperparameters (e.g., `n_nonzero_coefs=10` → `15`).
- Changing the algorithm (`OMP` → `Lasso`).
- Anything that changes the per-seed metric distribution.

**When NOT to bump:**
- Comments or docstring edits.
- Renaming local variables inside the factory.
- Refactors that provably preserve the metric distribution (rare; when in doubt, bump).

## Invalidation semantics

When `baseline_ref` bumps from `@v1` to `@v2`:
- Cached reports under `@v1` remain on disk and remain readable via `v2_get_report(cache_key=...)` if the agent has a key.
- New `v2_verify` calls compute under `@v2` — the engine will not return a `@v1` report for a `@v2` request.
- There is no rename-in-place; old keys are orphaned by design (they are still valid history).

## Adding a new entry

```python
REGISTRY: Mapping[str, BaselineSpec] = {
    # ... existing entries ...
    "my_benchmark": BaselineSpec(
        benchmark_id="my_benchmark",
        baseline_ref="my_benchmark/<impl_name>@v1",
        factory=_my_baseline_factory,
    ),
}
```

`REGISTRY` is `Mapping[str, BaselineSpec]` (immutable view); add via dict-literal in the source, not at runtime.
