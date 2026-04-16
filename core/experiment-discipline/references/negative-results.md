# Negative Result Reporting

Failed experiments carry as much signal as successful ones.

## Documentation Rules
- If an architecture tweak fails to converge or performs worse than baseline, **do not delete the code and forget it**. 
- Document what didn't work and provide hypotheses for why. 
- Log the failed run in tracking software with adequate tags (e.g., `status: failed`, `reason: loss_explosion`).
