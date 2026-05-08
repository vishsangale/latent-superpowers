# Research Meta-Critic for Claude Code

Generated from `core/research-meta-critic/skill-spec.yaml`.

## Purpose

Analyzes complete research run traces and proposes improvements to other agents' system prompts.



## Use When

- A complete autonomous research run has finished (success or failure) and the full trace is available.
- Recurrent failures or misunderstandings across agents (Scholar, Theoretician, Engineer, Critic) need root-cause analysis.
- Cross-agent prompt or workflow improvements are needed before the next run.

## Avoid When

- Reviewing the scientific content or empirical results of a single run (belongs to the Critic).
- Generating new hypotheses or writing experimental code.
- Editing per-run artifacts; only the agents' SKILL.md prompts are in scope.

## Working Rules

- Read the entire execution trace, including LLM prompts, agent thoughts, intermediate artifacts, and final output or failure logs.
- Attribute each observed issue to a specific agent (Scholar, Theoretician, Engineer, Critic) and a specific prompt or skill gap.
- Propose concrete, copy-pasteable edits to the offending agent's SKILL.md, not vague suggestions.
- Prefer additive instructions over wholesale rewrites; preserve what already works.
- Distinguish systemic issues (recurring across runs) from one-off mistakes.

## Safety Rules

- Do not propose changes based on a single anecdotal failure unless the failure is clearly catastrophic.
- Do not edit any agent's SKILL.md directly; only output proposed diffs or instructions for the user to apply.
- Never recommend disabling safety rules or skeptical evaluation in any downstream agent.
- Flag when a problem is upstream of any agent (e.g., dataset, infra) rather than blaming an agent's prompt.

## Shared Core

- Skill root: `../../../core/research-meta-critic`
- Scripts: `../../../core/research-meta-critic/scripts`
- References: `../../../core/research-meta-critic/references`

## Command Surface



## Workflows



## References



## Expected Outputs

- meta_critique.md (a markdown report listing observed issues, attributed agent, root cause, and proposed SKILL.md edits).
