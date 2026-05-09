---
name: arxiver-bringup
description: Use when the arxiver verifier substrate is not running, when v2_substrate_status reports not_ready, or when an agent is on a fresh machine and needs the sandbox image / datasets / cache prepared before running any hypothesis.
---

# Arxiver Bringup

## Overview

Walk a fresh machine through arxiver substrate setup until v2_smoke_test reports green. This Codex adapter is intentionally thin and delegates real functionality to the shared core under `../../../core/arxiver-bringup`.

## Use This Skill When

- User says "set up arxiver" / "first time on this machine" / "Phase 0 not running".
- v2_substrate_status returned docker_ok=false or image_digest=null.
- v2_verify failed with a runner/image error suggesting infra (not hypothesis) is broken.
- User asks why a smoke run is failing and wants the canonical setup checklist.

## Do Not Use This Skill For

- Setup is green and the user wants to author or run a hypothesis (use arxiver-verify-hypothesis).
- Diagnosing an unrelated container/network failure not specific to arxiver's image.

## Operating Principles

- Substrate is built lazily — never run hypotheses until v2_smoke_test passes end-to-end.
- Drive the substrate through MCP tools (v2_substrate_status, v2_build_image, v2_smoke_test). Do not shell out to docker directly.
- CIFAR-10 dataset must be staged into ~/.arxiver/datasets/cifar10/ before any cifar10 hypothesis. Use scripts/v2_prepare_datasets.py from the arxiver repo.
- A failing smoke is a substrate bug; do not retry blindly. Inspect verdict and stdout_tail.

## Safety Rules

- Never run "docker build" or "docker run" by hand — always go through v2_build_image.
- Never declare bringup complete without v2_smoke_test reporting passed=true.
- Never edit the sandbox image Dockerfile and skip rebuilding (cache key would mismatch silently).

## Shared Commands

- `python ../../../core/arxiver-bringup/scripts/check_substrate.py`: Prints the bringup checklist with the exact MCP-tool sequence and what "green" looks like for each step.

## Shared References

- `../../../core/arxiver-bringup/references/workflow.md`: End-to-end bringup walkthrough — substrate_status to build_image(cpu) to prepare_datasets to smoke_test.
- `../../../core/arxiver-bringup/references/troubleshooting.md`: Common failures (docker not running, image build OOM, dataset missing, smoke verdict=error) with diagnosis steps.

## Common Workflows

### Set up substrate on a fresh machine

1. Call v2_substrate_status; record docker_ok, image_digest, datasets_present.
2. If docker_ok=false, instruct user to start Docker daemon and stop.
3. If image_digest is null, call v2_build_image(variant=cpu).
4. If cifar10 dataset missing, run python scripts/v2_prepare_datasets.py from the arxiver repo.
5. Call v2_smoke_test; assert passed=true. Otherwise inspect failures and escalate.

Helpers: `check_substrate.py`

### Recover from a failing smoke

1. Inspect SmokeResult.failures — each names a fixture and verdict.
2. For verdict=error, read stdout_tail of the offending fixture's outcomes.
3. For runner errors, re-run v2_substrate_status to verify image still exists.
4. Do not retry the smoke until the named fixture's failure mode is identified.

Helpers: `check_substrate.py`

## Expected Outputs

- A green v2_substrate_status (docker_ok, image_digest, datasets_present).
- A passing v2_smoke_test (all 6 fixtures, duration < 90s).
- Clear escalation when any step fails (which step, what stdout_tail showed).
