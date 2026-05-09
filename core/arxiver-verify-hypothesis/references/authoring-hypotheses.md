# Authoring Hypotheses

A hypothesis is a Python source string passed as `code` to `v2_verify`. The string must define a top-level `build_plugin` callable that the benchmark adapter calls once per seed.

## Signature per benchmark

| benchmark_id | `build_plugin` signature | Returns |
|---|---|---|
| `cifar10` | `build_plugin(params)` | `torch.optim.Optimizer` |
| `sparse_recovery` | `build_plugin()` | `Callable[[np.ndarray, np.ndarray], np.ndarray]` (solver `(A, y) -> x_recovered`) |
| `cot_compression` | `build_plugin(hidden_dim)` | `torch.nn.Module` |

## Required hygiene

**Defer heavy imports.** Top-level `import torch` or `import sklearn` blocks the host-side bootstrap. Put them inside `build_plugin` or inside the returned closure:

```python
def build_plugin(params):
    import torch
    return torch.optim.SGD(params, lr=1e-3)
```

**No mutable module-level state.** Each container is fresh, but multiple seeds inside a single fixture/run share the same Python process. Module-level lists/dicts that accumulate across calls will pollute later seeds.

**Determinism.** If your plugin uses RNGs internally (e.g., random init), seed them explicitly inside `build_plugin`. The adapter sets `torch.manual_seed(seed)` and `np.random.seed(seed)` for you, but plugin-internal RNGs are your responsibility.

**Native floats.** If your closure returns a metric, return a Python `float`, not `numpy.float64`. The cache-key encoder is sensitive to numeric type.

## Common pitfalls

- Returning a class instead of an instance from `build_plugin` (the adapter calls it as a factory, not a constructor).
- Calling the benchmark adapter directly bypassing `v2_verify` — skips bootstrap and cache.
- Reusing a `cache_key` from a different `image_digest` and assuming the report applies. Image rebuilds invalidate.

## Minimal example (sparse_recovery)

```python
code = """
def build_plugin():
    import numpy as np
    from sklearn.linear_model import OrthogonalMatchingPursuit
    def solver(A, y):
        omp = OrthogonalMatchingPursuit(n_nonzero_coefs=15)
        omp.fit(A, y)
        return np.asarray(omp.coef_, dtype=np.float64)
    return solver
"""
```

Then:

```
v2_verify(code=code, benchmark_id="sparse_recovery", seeds=(0,1,2,3,4))
```
