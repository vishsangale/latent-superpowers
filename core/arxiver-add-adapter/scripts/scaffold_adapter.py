#!/usr/bin/env python3
"""Print copy-pasteable scaffolds for a new arxiver benchmark adapter.

Stdlib-only. Does NOT write files — emits three blocks to stdout that the
user redirects or copy-pastes.
"""
from __future__ import annotations

import argparse


ADAPTER_TEMPLATE = '''\
"""v2 adapter for {benchmark_id}.

Imports torch/sklearn/etc. are deferred into run() so host-side
`import baselines` stays cheap. Dataset must be mounted at
/datasets/{benchmark_id} inside the container — never download=True.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


class _{class_name}Adapter:
    benchmark_id: str = "{benchmark_id}"
    _DATA_ROOT: Path = Path("/datasets/{benchmark_id}")

    def run(
        self,
        plugin_factory: Callable[..., Any],
        # TODO: add benchmark-specific kwargs (epochs, batch_size, ...)
    ) -> tuple[float, dict[str, Any]]:
        if not self._DATA_ROOT.exists():
            raise RuntimeError(
                f"{benchmark_id} dataset not mounted at {{self._DATA_ROOT}}; "
                "stage with scripts/v2_prepare_{benchmark_id}.py"
            )

        # TODO: deferred imports here (e.g., import torch; import sklearn)

        # TODO: build the model/state from plugin_factory(...)
        # TODO: train/evaluate, compute metric (higher-is-better)

        metric: float = 0.0
        extras: dict[str, Any] = {{}}
        return metric, extras


ADAPTER: _{class_name}Adapter = _{class_name}Adapter()
'''

REGISTRY_TEMPLATE = '''\
# Edit src/arxiver/research_agent/v2/verifier/baselines.py
# 1) Add the factory at module scope (alongside _sgd_factory, _omp_factory, etc.):

def _{benchmark_id}_factory(*args: Any, **kwargs: Any) -> Any:
    # TODO: deferred imports
    # TODO: build and return the baseline (signature must match the adapter's plugin_factory)
    raise NotImplementedError


# 2) Add this entry to the REGISTRY dict literal:

\"{benchmark_id}\": BaselineSpec(
    benchmark_id=\"{benchmark_id}\",
    baseline_ref=\"{baseline_ref}\",
    factory=_{benchmark_id}_factory,
),
'''

TEST_TEMPLATE = '''\
"""Unit test for the {benchmark_id} adapter."""
from __future__ import annotations

import pytest

from arxiver.research_agent.v2.verifier.adapters.{benchmark_id} import ADAPTER


@pytest.mark.v2
def test_run_with_stub_plugin_returns_metric_and_extras() -> None:
    def stub_plugin(*args: object, **kwargs: object) -> object:
        # TODO: return whatever the adapter's plugin_factory expects
        ...

    metric, extras = ADAPTER.run(stub_plugin)
    assert isinstance(metric, float)
    assert isinstance(extras, dict)


@pytest.mark.v2
def test_run_raises_when_dataset_missing(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(ADAPTER, "_DATA_ROOT", tmp_path / "missing")
    with pytest.raises(RuntimeError, match="not mounted"):
        ADAPTER.run(lambda *_a, **_kw: None)
'''


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print scaffolds for a new arxiver benchmark adapter."
    )
    parser.add_argument(
        "--benchmark-id", required=True,
        help="snake_case benchmark id (used as module name and dir name).",
    )
    parser.add_argument(
        "--baseline-ref", required=True,
        help="Versioned baseline ref, e.g. 'my_benchmark/sgd@v1'.",
    )
    args = parser.parse_args()

    benchmark_id = args.benchmark_id
    class_name = "".join(part.capitalize() for part in benchmark_id.split("_"))

    print(f"# === src/arxiver/research_agent/v2/verifier/adapters/{benchmark_id}.py ===")
    print(ADAPTER_TEMPLATE.format(benchmark_id=benchmark_id, class_name=class_name))
    print()
    print(f"# === REGISTRY entry (paste into baselines.py) ===")
    print(REGISTRY_TEMPLATE.format(benchmark_id=benchmark_id, baseline_ref=args.baseline_ref))
    print()
    print(f"# === tests/v2/verifier/adapters/test_{benchmark_id}.py ===")
    print(TEST_TEMPLATE.format(benchmark_id=benchmark_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
