---
name: epistemic-rigor
description: Use when the task involves presenting factual claims, citing research papers or SOTA benchmarks, resolving conflicting information, or making inferential leaps that carry epistemic uncertainty.
---

# Epistemic Rigor for OpenCode

Generated from `core/epistemic-rigor/skill-spec.yaml`.

## Purpose

Validate claims, handle uncertainty gracefully, and avoid hallucinated citations by rigorously linking assertions to evidence.

This adapter wraps the epistemic-rigor skill. Prefer using the provided CLI helpers to verify your claims and citations before drafting your responses.

## Use When

- The user asks for factual claims, benchmarks, or citations in an ML/research context.
- The assistant is summarizing literature or synthesizing evidence from multiple sources.
- Conflicting claims exist in the project or external knowledge, requiring resolution or disclosure.

## Avoid When

- Executing straightforward code commands where no factual claims are being presented.
- Doing purely formatting or linting tasks.

## Working Rules

- Claim-evidence binding — Every factual claim must link to a verifiable source or reproducible experiment. No unsupported assertions.
- Uncertainty disclosure — State confidence levels explicitly. Distinguish "established consensus," "emerging evidence," and "speculative inference."
- Contradiction surfacing — When sources conflict, present the disagreement rather than silently picking a side.
- Recency awareness — Flag when cited evidence may be outdated given how fast ML moves (e.g., SOTA benchmarks, scaling laws).
- Anti-hallucination checkpoint — Before presenting a citation, paper, or result, verify it exists. If unverifiable, say so.

## Safety Rules

- Never fabricate citations, URLs, or paper titles.
- Never present a speculated finding as established consensus.
- If a source cannot be located, explicitly disclaim that it is unverifiable.
- Do not pick sides in unresolved academic disputes; present the conflict objectively.

## Shared Core

- Skill root: `../../../core/epistemic-rigor`
- Scripts: `../../../core/epistemic-rigor/scripts`
- References: `../../../core/epistemic-rigor/references`

## Command Surface

- `python ../../../core/epistemic-rigor/scripts/verify_citation.py`: Verifies if a given URL or arXiv ID exists to prevent hallucinated citations.
- `python ../../../core/epistemic-rigor/scripts/evaluate_uncertainty.py`: Assists in evaluating the confidence level of a given claim.
- `python ../../../core/epistemic-rigor/scripts/check_recency.py`: Flags if a cited date/benchmark is potentially outdated given recent SOTA changes.

## Workflows

### Verify a citation and bind claim

1. Isolate the factual claim being made.
2. Identify the supporting source (paper, link, or dataset).
3. Use verify_citation.py to confirm the URL or arXiv ID exists.
4. Present the bound claim and source.

Helpers: `verify_citation.py`

### Disclose uncertainty

1. Identify the confidence level of the information.
2. Determine if it's consensus, emerging, or speculative.
3. Highlight contradictions if multiple sources disagree.
4. Clearly state the uncertainty to the user.

Helpers: `evaluate_uncertainty.py`

## References

- `../../../core/epistemic-rigor/references/claim-binding.md`: Guidelines for binding factual claims to verifiable sources or experiments.
- `../../../core/epistemic-rigor/references/uncertainty-disclosure.md`: Taxonomy of confidence levels and strategies for surfacing contradictions.
- `../../../core/epistemic-rigor/references/hallucination-prevention.md`: Strict rules for the Anti-hallucination checkpoint and checking recency.

## Expected Outputs

- A claim accompanied by a verified citation or data reference.
- An uncertainty or confidence annotation (consensus vs emerging vs speculative).
- A warning if evidence relies on out-of-date information.
- A summary of opposing viewpoints when contradictions exist.
