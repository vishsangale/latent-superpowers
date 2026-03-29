from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
INSPECT = ROOT / "core" / "dataset-pipeline" / "scripts" / "inspect_dataset_project.py"
PROFILE = ROOT / "core" / "dataset-pipeline" / "scripts" / "profile_dataset.py"
VALIDATE = ROOT / "core" / "dataset-pipeline" / "scripts" / "validate_splits.py"
SNAPSHOT = ROOT / "core" / "dataset-pipeline" / "scripts" / "snapshot_dataset.py"


def test_profile_and_validate_splits(dataset_root: Path) -> None:
    profile = subprocess.run(
        [sys.executable, str(PROFILE), str(dataset_root), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(profile.stdout)
    assert payload["file_count"] == 3

    validate = subprocess.run(
        [
            sys.executable,
            str(VALIDATE),
            str(dataset_root / "train.csv"),
            str(dataset_root / "val.csv"),
            str(dataset_root / "test.jsonl"),
            "--id-key",
            "user_id",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    overlap = json.loads(validate.stdout)
    assert overlap["leakage_detected"] is True
    assert overlap["overlap"]["train_test"] == 1


def test_snapshot_dataset(dataset_root: Path, tmp_path: Path) -> None:
    out_path = tmp_path / "snapshot.json"
    result = subprocess.run(
        [sys.executable, str(SNAPSHOT), str(dataset_root), "--out", str(out_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert out_path.exists()
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["file_count"] == 3

    single_out = tmp_path / "single.json"
    subprocess.run(
        [sys.executable, str(SNAPSHOT), str(dataset_root / "train.csv"), "--out", str(single_out)],
        check=True,
        capture_output=True,
        text=True,
    )
    single_payload = json.loads(single_out.read_text(encoding="utf-8"))
    assert single_payload["file_count"] == 1


def test_inspect_dataset_project_parses_choices_and_imports(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    (repo / "scripts" / "prepare_data.py").write_text(
        "\n".join(
            [
                "from demo.data.pipelines.foo import FooPipeline",
                "choices=['alpha','beta']",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(INSPECT), str(repo), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert "scripts/prepare_data.py" in payload["dataset_scripts"]
    assert payload["dataset_choices"] == ["alpha", "beta"]
    assert "demo.data.pipelines.foo" in payload["pipeline_modules"]


def test_validate_splits_blocks_when_requested_id_missing(dataset_root: Path) -> None:
    val_path = dataset_root / "val.jsonl"
    val_path.write_text(json.dumps({"item_id": 20, "label": 1}) + "\n", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATE),
            str(dataset_root / "train.csv"),
            str(val_path),
            str(dataset_root / "test.jsonl"),
            "--id-key",
            "user_id",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["blocked"] is True


def test_inspect_dataset_project_supports_src_layout(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    module_dir = repo / "src" / "demo" / "data" / "pipelines"
    module_dir.mkdir(parents=True)
    (module_dir / "foo.py").write_text("class FooPipeline: pass\n", encoding="utf-8")
    (repo / "scripts").mkdir(parents=True)
    (repo / "scripts" / "prepare_data.py").write_text(
        "from demo.data.pipelines.foo import FooPipeline\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(INSPECT), str(repo), "--check-imports", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["import_checks"]["demo.data.pipelines.foo"] == "ok"
