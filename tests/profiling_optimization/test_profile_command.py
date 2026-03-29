from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "profiling-optimization"
    / "scripts"
    / "profile_command.py"
)


def test_profile_command_writes_json(tmp_path: Path) -> None:
    out_path = tmp_path / "profile.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--out",
            str(out_path),
            "--json",
            "--",
            sys.executable,
            "-c",
            "import time; print('ok'); time.sleep(0.1)",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["out_path"] == str(out_path)
    saved = json.loads(out_path.read_text(encoding="utf-8"))
    assert saved["exit_code"] == 0
    assert "ok" in saved["stdout"]
