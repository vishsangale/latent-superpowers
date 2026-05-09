---
name: arxiver-verify-hypothesis
description: Use when the user wants to test whether a code change beats the registered baseline on a benchmark, or when interpreting an existing VerificationReport (verdict, CI, p-value).
---

# Arxiver Verify Hypothesis for OpenCode

Generated from `core/arxiver-verify-hypothesis/skill-spec.yaml`.

## Purpose

Author a hypothesis, run it through the v2 verifier, and read the paired-bootstrap report honestly.

This skill is the canonical entry point for hypothesis verification. Always confirm the substrate is green (arxiver-bringup) before invoking v2_verify.

## Use When

- User asks "is this optimizer/solver/projection better than baseline".
- User has a build_plugin() snippet and wants to run it on cifar10 / sparse_recovery / cot_compression.
- User asks what a verdict means ("the report says tie — what does that mean?").
- User wants to retrieve a previous report by cache_key (v2_get_report).

## Avoid When

- Substrate isn't ready (use arxiver-bringup).
- User wants to wrap a brand-new benchmark not in the registry (use arxiver-add-adapter).
- User wants to debug numerics inside a benchmark adapter itself (out of scope here).

## Working Rules

- The hypothesis is a Python source string defining build_plugin(); the benchmark adapter calls it once per seed.
- Verdict semantics are paired-bootstrap, not "did I beat the mean". win = CI lower bound > 0; loss = CI upper bound < 0; tie = CI overlaps zero (INCONCLUSIVE, not "no effect"); error = at least one seed failed in either arm.
- More seeds tighten the CI but do not change a true tie into a win. Reach for n_seeds before declaring a result.
- Cache hits (same code+benchmark+seeds+image_digest+baseline_ref) return the same report — that's a feature, not a bug.

## Safety Rules

- Never reinterpret tie as "my change is fine" or "no regression". A tie means we cannot statistically distinguish the two.
- Never compare reports with different baseline_ref or different image_digest — they're not commensurable.
- Never call benchmark adapters directly (bypasses bootstrap and cache). Always go through v2_verify.
- Never claim a result on n_seeds<5 unless the user explicitly accepts the wider CI.

## Shared Core

- Skill root: `../../../core/arxiver-verify-hypothesis`
- Scripts: `../../../core/arxiver-verify-hypothesis/scripts`
- References: `../../../core/arxiver-verify-hypothesis/references`

## Command Surface

- `python ../../../core/arxiver-verify-hypothesis/scripts/interpret_report.py`: Given verdict and stats fields, prints the conventional reading paragraph.

## Workflows

### Verify an optimizer change on cifar10

1. Confirm v2_substrate_status is green; otherwise hand off to arxiver-bringup.
2. Compose code as a Python string defining build_plugin(params) -> torch.optim.Optimizer.
3. Call v2_verify(code=..., benchmark_id="cifar10", seeds=(0,1,2,3,4)).
4. Read verdict; if tie with abs(mean_diff) > 0.5, recommend more seeds.

Helpers: `interpret_report.py`

### Reinterpret a previous report

1. Call v2_get_report(cache_key=<key>); if None, the report was never computed.
2. Run interpret_report.py with the report's stats fields.
3. Cross-check baseline_ref version against the current registry; warn if stale.

Helpers: `interpret_report.py`

## References

- `../../../core/arxiver-verify-hypothesis/references/reading-reports.md`: Verdict semantics, why CI beats p-value, when to reach for more seeds, common misreadings.
- `../../../core/arxiver-verify-hypothesis/references/authoring-hypotheses.md`: build_plugin signatures per benchmark, common pitfalls (top-level torch import, mutable closure state, non-deterministic init).

## Expected Outputs

- A VerificationReport with verdict in {win, loss, tie, error} and a plain-language reading.
- When inconclusive, a recommendation to rerun with more seeds or to note the change is below the detection threshold.
- When error, the offending stdout_tail and an escalation (likely an arxiver-bringup or adapter-side issue).
