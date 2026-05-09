# Arxiver Add Adapter for Claude Code

Generated from `core/arxiver-add-adapter/skill-spec.yaml`.

## Purpose

Wrap a new benchmark in the v2 verifier and register a versioned baseline.

This skill modifies the arxiver substrate itself. Run pytest -m v2 in the arxiver repo after the change to confirm nothing broke.

## Use When

- User says "add benchmark X" / "wrap an existing v1 benchmark in v2" / "register a new baseline".
- User wants to bump a baseline implementation (which requires a baseline_ref version bump).
- User asks for the adapter pattern / what an adapter must implement.

## Avoid When

- User wants to author a hypothesis against an existing benchmark (use arxiver-verify-hypothesis).
- User wants to tune the baseline's hyperparameters without changing semantics — that's still a baseline_ref bump; treat as an add-adapter task.
- Substrate isn't running (use arxiver-bringup first).

## Working Rules

- Adapter contract is fixed and small — class with benchmark_id (str class var) and run(plugin_factory, **kwargs) returning (metric, extras).
- The (metric, extras) pair is the only output the engine reads. Higher metric must mean better; if the natural metric is loss-like, return its negative.
- Datasets mount at /datasets/<benchmark_id> inside the container; adapter must raise if missing — do not silently default to download=True.
- All torch/sklearn/etc. imports go INSIDE run(). Module top-level stays import-cheap so host-side import baselines is fast.
- baseline_ref is versioned (e.g., "sparse_recovery/omp@v1"). Bumping the version is the only mechanism for invalidating cached reports — never silently change baseline behavior at the same ref.

## Safety Rules

- Never use download=True for any dataset — fail loudly if not mounted.
- Never share state across run() invocations (no module-level caches, no global RNG mutation).
- Never coerce metric through numpy types — return a native Python float (cache-key encoding is sensitive).
- Never reuse a baseline_ref string when changing the implementation; bump the @vN suffix.

## Shared Core

- Skill root: `../../../core/arxiver-add-adapter`
- Scripts: `../../../core/arxiver-add-adapter/scripts`
- References: `../../../core/arxiver-add-adapter/references`

## Command Surface

- `python ../../../core/arxiver-add-adapter/scripts/scaffold_adapter.py`: Prints a copy-pasteable adapter skeleton, baseline registry entry, and unit-test stub, parameterized by --benchmark-id and --baseline-ref.

## Workflows

### Add a new benchmark adapter

1. Confirm the benchmark's metric direction (higher-is-better) and dataset requirements.
2. Run scaffold_adapter.py --benchmark-id <id> --baseline-ref <id>/<impl>@v1 to print skeletons.
3. Drop the adapter into v2/verifier/adapters/<id>.py with deferred imports inside run().
4. Add the BaselineSpec to baselines.py REGISTRY.
5. Author the unit test under tests/v2/verifier/adapters/ with a stub plugin returning a known metric.
6. If a dataset is needed, add scripts/v2_prepare_<id>.py and document the mount path.

Helpers: `scaffold_adapter.py`

### Bump a baseline implementation

1. Edit the baseline factory in baselines.py to the new implementation.
2. Bump baseline_ref from @vN to @v(N+1) in the same REGISTRY entry.
3. Note that all cached reports referencing the previous ref are now orphaned (still readable via v2_get_report, but new v2_verify calls will compute fresh).

## References

- `../../../core/arxiver-add-adapter/references/adapter-pattern.md`: Annotated walkthrough of the cifar10 and sparse_recovery adapters, with the contract called out.
- `../../../core/arxiver-add-adapter/references/baseline-registry.md`: How to add a BaselineSpec, the @vN versioning rule, and what triggers a version bump.

## Expected Outputs

- A new file at src/arxiver/research_agent/v2/verifier/adapters/<benchmark_id>.py with the adapter class and an ADAPTER module-level instance.
- A new entry in src/arxiver/research_agent/v2/verifier/baselines.py REGISTRY with a versioned baseline_ref.
- A unit test under tests/v2/verifier/adapters/ that exercises run() with a stub plugin.
- (If a dataset is required) a staging script under scripts/v2_prepare_<id>.py mirroring the cifar10 pattern.
