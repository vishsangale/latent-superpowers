from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INSTALL = ROOT / "tools" / "install_adapter.py"


def test_install_codex_wrapper_rewrites_core_paths(tmp_path: Path) -> None:
    dest_root = tmp_path / "codex-skills"
    subprocess.run(
        [
            sys.executable,
            str(INSTALL),
            "--skill",
            "hydra",
            "--adapter",
            "codex",
            "--mode",
            "symlink",
            "--dest-root",
            str(dest_root),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    skill_dir = dest_root / "hydra"
    content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    assert "../../../core/hydra" not in content
    assert (skill_dir / ".adapter-source").is_symlink()
    assert (skill_dir / "agents" / "openai.yaml").exists()
    core_reference = content.split("under `", 1)[1].split("`", 1)[0]
    resolved = (skill_dir / core_reference).resolve()
    assert resolved == (ROOT / "core" / "hydra").resolve()
