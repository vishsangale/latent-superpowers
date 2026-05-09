# Arxiver Substrate Bringup Workflow

End-to-end walkthrough: take a fresh machine to a green `v2_smoke_test` using only MCP tools.

## Step 1: Inspect substrate status

Call `v2_substrate_status`. The returned `SubstrateStatus` has:
- `docker_ok: bool` — Docker daemon reachable.
- `image_digest: str | null` — sha256 of the most recent `v2-sandbox-cpu` image, or null if never built.
- `image_variant: "cpu" | "gpu" | null` — variant of the cached image.
- `datasets_present: dict[str, bool]` — keyed by `benchmark_id` (e.g. `{"cifar10": false}`).
- `cache_size_bytes: int` — current size of `~/.arxiver/cache/v2/`.

If `docker_ok=false`: stop and tell the user to start Docker. Do not attempt anything else.

## Step 2: Build the sandbox image (if needed)

If `image_digest` is null, call `v2_build_image(variant="cpu")`. Expect 5–10 minutes on first build — large layers (`torch`, `torchvision`, `numpy`, `scikit-learn`). Output is a `BuildResult` with the new digest.

GPU variant is deferred to stripe 0.8; do not request it in Phase 0.

## Step 3: Stage datasets

If `datasets_present.cifar10=false`, run from the **arxiver** checkout:

```bash
python scripts/v2_prepare_datasets.py
```

This downloads the CIFAR-10 archive into `~/.arxiver/datasets/cifar10/`, where the sandbox runner mounts it at `/datasets/cifar10` inside the container.

Other benchmarks (`sparse_recovery`, `cot_compression`) generate their data on-the-fly inside the container — no staging required.

## Step 4: Smoke test

Call `v2_smoke_test`. The returned `SmokeResult` has:
- `passed: bool` — all 6 fixtures matched their expected verdicts.
- `duration_s: float` — wall time. Expect < 90s on a recent CPU.
- `failures: list[str]` — fixture IDs that failed, with their actual verdict.

If `passed=true`: bringup is complete.

If `passed=false`: do not retry. Hand off to `references/troubleshooting.md`.

## Step 5: Confirm with `v2_list_benchmarks`

Optional but useful — surfaces the registered benchmarks (`cifar10`, `sparse_recovery`, `cot_compression`) so the user can pick one for their first hypothesis.
