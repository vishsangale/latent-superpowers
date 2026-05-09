#!/usr/bin/env python3
"""Print the arxiver bringup checklist.

Stdlib-only. Does NOT call docker, MCP, or arxiver. Educational output only.
"""
from __future__ import annotations

import argparse


CHECKLIST = """\
Arxiver Substrate Bringup Checklist
====================================

Drive the substrate through MCP tools — never via raw `docker` commands.

1. v2_substrate_status
   Expect: docker_ok=true, image_digest=<sha256>, datasets_present.cifar10=true.
   If docker_ok=false: stop, ask user to start the Docker daemon.

2. v2_build_image(variant="cpu")  [only if image_digest is null]
   Expect: BuildResult with a new digest. First build takes 5-10 minutes.

3. python scripts/v2_prepare_datasets.py  [only if datasets_present.cifar10=false]
   Run from the arxiver checkout. Stages CIFAR-10 to ~/.arxiver/datasets/cifar10/.

4. v2_smoke_test
   Expect: passed=true, duration_s < 90, failures=[].
   If passed=false: do not retry — see references/troubleshooting.md.

5. (optional) v2_list_benchmarks
   Surfaces the registered benchmarks for the next hypothesis.

Bringup is complete only when step 4 reports passed=true.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the arxiver bringup checklist.")
    parser.parse_args()
    print(CHECKLIST)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
