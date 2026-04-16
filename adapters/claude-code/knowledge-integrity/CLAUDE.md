# Knowledge Integrity for Claude Code

Generated from `core/knowledge-integrity/skill-spec.yaml`.

## Purpose

Preserve the integrity of information by enforcing precise attribution, clarifying knowledge boundaries, and assessing cascading impacts.

This adapter wraps the knowledge-integrity skill. Prioritize clear reasoning bounds and precise attribution above all.

## Use When

- The user asks about the origin or details of a specific architecture, algorithm, or theorem.
- The agent must synthesize information regarding a time-sensitive issue or recent SOTA development.
- Recommending architectures or benchmarking strategies that are expensive to run.

## Avoid When

- Writing standard boilerplate code where no historical or academic claims are made.
- Tasks that only require experiment tracking (use experiment-runner instead).

## Working Rules

- Attribution precision — Credit the actual origin of an idea, not just the most popular paper. Distinguish "introduced by" from "popularized by."
- Know your boundary — Explicitly flag when reasoning from training knowledge vs. retrieved evidence vs. inference. Don't blur the lines.
- Search before synthesize — When the question is empirical or time-sensitive, retrieve first. Don't generate plausible-sounding answers from priors alone.
- No false authority — Don't present a paraphrased consensus that doesn't exist. If a field is fragmented or unsettled, say that.
- Downstream impact awareness — Flag when a claim, if wrong, could cascade into wasted compute, flawed architectures, or misleading benchmarks.

## Safety Rules

- Never hallucinate an original author if unsure; ask to retrieve evidence instead.
- Never recommend expensive baselines without a clear warning about compute cost.
- Always flag pre-training cutoff date gaps if relying purely on training data.

## Shared Core

- Skill root: `../../../core/knowledge-integrity`
- Scripts: `../../../core/knowledge-integrity/scripts`
- References: `../../../core/knowledge-integrity/references`

## Command Surface

- `python ../../../core/knowledge-integrity/scripts/check_attribution.py`: An interactive checklist helping the agent trace an idea back to its origin.
- `python ../../../core/knowledge-integrity/scripts/boundary_flag.py`: Tool to annotate an explanation with its source boundary type.
- `python ../../../core/knowledge-integrity/scripts/impact_assessment.py`: Assessment wizard measuring the downstream risk of a flawed recommendation.

## Workflows

### State a historical ML fact

1. Isolate the fact.
2. Apply a boundary flag indicating if this is from prior training or retrieved just now.
3. Specify the exact origin vs popularizer.

Helpers: `check_attribution.py`, `boundary_flag.py`

### Recommend a costly benchmark or architecture

1. Perform an impact check.
2. Highlight compute, memory, and time cascading effects if the recommendation is suboptimal.

Helpers: `impact_assessment.py`

## References

- `../../../core/knowledge-integrity/references/attribution-precision.md`: Guidelines for precision in author and paper attribution.
- `../../../core/knowledge-integrity/references/knowledge-boundaries.md`: Tagging rules for Training Data, Retrieved Evidence, and Inference.
- `../../../core/knowledge-integrity/references/downstream-impact.md`: Categorization of cascading risks (Wasted Compute, Misleading Benchmarks).

## Expected Outputs

- Attributions categorized explicitly as "introducer" vs "popularizer".
- Knowledge boundary tags on generated explanations (e.g., `[Training Prior]`).
- Clear warnings about compute and research latency risks.
