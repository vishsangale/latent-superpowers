# W&B Workflow

## Standard Order

1. Verify auth and environment context.
2. Resolve entity and project.
3. Resolve the target run set, group, or sweep.
4. Pick comparison metrics and constraints.
5. Pull summaries first and histories second.
6. Produce a compact result summary.

## Scope Discipline

- Prefer the smallest run set that answers the question.
- Do not rank runs without naming the metric.
- Treat missing metrics and partially logged runs as analysis risks, not edge cases.
