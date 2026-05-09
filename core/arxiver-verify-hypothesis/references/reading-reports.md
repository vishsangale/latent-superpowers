# Reading Verification Reports

A `VerificationReport` is the output of `v2_verify` (or the cached result returned by `v2_get_report`). It carries the paired-bootstrap statistics over `n_seeds` per-seed `Outcome` pairs (one hypothesis arm, one baseline arm).

## The four verdicts

| Verdict | Definition | Interpretation |
|---|---|---|
| `win` | CI lower bound > 0 at alpha=0.05 | Hypothesis statistically beats baseline. |
| `loss` | CI upper bound < 0 at alpha=0.05 | Hypothesis statistically loses. |
| `tie` | CI overlaps zero | **Inconclusive.** We cannot reject equality with these seeds. NOT "no effect". |
| `error` | At least one seed failed in either arm | Substrate or adapter is broken. Read `stdout_tail`. |

## Why we report CI, not just p-value

p-value tells you whether the difference is statistically distinguishable from zero. CI tells you the **range of plausible effect sizes**. A tiny effect can be statistically significant with enough seeds; a large effect can be inconclusive with too few. Always quote the CI alongside the verdict.

## "tie ≠ no effect" — the most common misreading

`tie` means: with the seeds we ran, we cannot tell whether the hypothesis is better, worse, or the same as baseline. It does NOT mean "the change has no effect" or "the change is safe". A true win can hide behind a tie when `n_seeds` is too small or seed variance is high.

**Action on tie:**
- If `abs(mean_diff)` is comfortably inside the CI and small relative to the metric scale: the change is plausibly noise; document and move on.
- If `abs(mean_diff)` is large but CI still spans zero: rerun with more seeds (e.g., 10 or 20). The verdict can change.

## Cache-key invariance

`(code, benchmark_id, seeds, image_digest, baseline_ref, n_bootstrap, alpha)` ⇒ same `cache_key` ⇒ same report. This is deterministic by design. If two reports for "the same change" disagree, one of those inputs differs — most often `baseline_ref` (a registry version bump invalidates).

## Report fields the agent should always quote

- `verdict`
- `mean_diff`, `ci_low`, `ci_high`, `p_value`
- `n_seeds`, `n_bootstrap`
- `image_digest`, `image_variant`
- `baseline_ref` (read from the report's outcomes; surface explicitly when reporting)
