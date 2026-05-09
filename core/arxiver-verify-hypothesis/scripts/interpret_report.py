#!/usr/bin/env python3
"""Print the canonical reading of a VerificationReport's stats.

Stdlib-only. Does NOT call MCP or arxiver. Educational output only.
"""
from __future__ import annotations

import argparse


def reading(verdict: str, mean_diff: float, ci_low: float, ci_high: float,
            p_value: float, n_seeds: int) -> str:
    header = (
        f"verdict={verdict}  mean_diff={mean_diff:+.4g}  "
        f"CI=[{ci_low:+.4g}, {ci_high:+.4g}]  p={p_value:.4g}  n_seeds={n_seeds}"
    )
    if verdict == "win":
        body = (
            "Hypothesis statistically beats baseline (CI lower bound > 0). "
            "The plausible effect size is in the CI; quote it alongside the verdict."
        )
    elif verdict == "loss":
        body = (
            "Hypothesis statistically loses (CI upper bound < 0). "
            "Do not retry to flip the verdict — investigate the change."
        )
    elif verdict == "tie":
        body = (
            "INCONCLUSIVE. CI overlaps zero — we cannot reject equality with these seeds. "
            "This does NOT mean 'no effect'. If abs(mean_diff) is large relative to the "
            "metric scale, rerun with more seeds (10 or 20)."
        )
    elif verdict == "error":
        body = (
            "At least one seed failed in either arm. Read stdout_tail of the failing "
            "outcomes. Likely substrate-side (arxiver-bringup) or adapter-side."
        )
    else:
        body = f"Unknown verdict {verdict!r}. Expected one of win/loss/tie/error."
    return f"{header}\n\n{body}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the canonical reading of a VerificationReport.")
    parser.add_argument("--verdict", required=True, choices=["win", "loss", "tie", "error"])
    parser.add_argument("--mean-diff", type=float, required=True)
    parser.add_argument("--ci-low", type=float, required=True)
    parser.add_argument("--ci-high", type=float, required=True)
    parser.add_argument("--p-value", type=float, required=True)
    parser.add_argument("--n-seeds", type=int, required=True)
    args = parser.parse_args()
    print(reading(args.verdict, args.mean_diff, args.ci_low, args.ci_high,
                  args.p_value, args.n_seeds))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
