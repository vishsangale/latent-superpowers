# Profiling Optimization for Gemini

Generated from `core/profiling-optimization/skill-spec.yaml`.

## Purpose

Profile local training commands, compare runtime and memory behavior, and turn raw traces into bottleneck-focused optimization guidance.

This adapter is a thin wrapper over the shared profiling-optimization core. Prefer invoking the CLI helpers under the shared core before writing ad-hoc profiling logic.

## Use When

- The user wants to know why a training or evaluation command is slow.
- The task is to measure wall time, memory growth, GPU utilization, or compare profile outputs across runs.
- A local Torch profiler trace or command-level runtime profile needs to be summarized into concrete optimization steps.

## Avoid When

- Generic experiment tracking that belongs to W&B or MLflow.
- Repository planning work that belongs to paper-to-code.
- Blind performance claims without a real profile or command output.

## Working Rules

- Measure first, recommend second.
- Prefer repeatable local command profiles over vague bottleneck guesses.
- Separate command-level runtime, memory, and GPU signals from operator-level Torch traces.
- Turn raw numbers into ranked recommendations with explicit assumptions.

## Safety Rules

- Prefer local profiling and read-only inspection.
- Do not change training code unless the user asks for an optimization patch.
- Call out when recommendations are based on sparse or indirect signals.

## Shared Core

- Skill root: `../../../core/profiling-optimization`
- Scripts: `../../../core/profiling-optimization/scripts`
- References: `../../../core/profiling-optimization/references`

## Command Surface

- `python ../../../core/profiling-optimization/scripts/profile_command.py`: Run a local command with wall-time, memory, CPU, and optional GPU sampling, then save a profile JSON.
- `python ../../../core/profiling-optimization/scripts/summarize_profile.py`: Summarize one saved command profile into bottlenecks and recommendations.
- `python ../../../core/profiling-optimization/scripts/compare_profiles.py`: Compare multiple saved command profiles and rank tradeoffs.
- `python ../../../core/profiling-optimization/scripts/summarize_torch_trace.py`: Summarize a Torch profiler Chrome trace into top operators, categories, and hotspots.

## Workflows

### Profile a command

1. Run the exact local command under the profiler wrapper.
2. Capture wall time, CPU, RSS, and optional GPU samples.
3. Summarize the strongest bottlenecks.
4. Recommend the highest-impact next optimization steps.

Helpers: `profile_command.py`, `summarize_profile.py`

### Compare optimization attempts

1. Collect multiple profile JSON files from related runs.
2. Compare wall time, memory, and GPU summaries side by side.
3. Rank the candidates under an explicit objective such as speed or memory.
4. State the tradeoffs clearly.

Helpers: `compare_profiles.py`

### Inspect a Torch trace

1. Parse the Chrome trace events.
2. Rank the most expensive operators and categories.
3. Separate CPU-side and CUDA-side hotspots when possible.
4. Convert the hotspots into concrete optimization directions.

Helpers: `summarize_torch_trace.py`

## References

- `../../../core/profiling-optimization/references/workflow.md`: Profile collection, interpretation, and recommendation flow.
- `../../../core/profiling-optimization/references/heuristics.md`: Runtime, memory, CPU, and GPU bottleneck heuristics.
- `../../../core/profiling-optimization/references/trace-analysis.md`: Torch profiler trace interpretation and limitations.

## Expected Outputs

- the profiled command or trace path
- wall time, peak RSS, and GPU summary when available
- the highest-confidence bottlenecks
- a short ordered list of optimization actions
