#!/usr/bin/env python3
"""
Shared helpers for Hydra skill scripts.
"""

from __future__ import annotations

import ast
from copy import deepcopy
import os
import re
from pathlib import Path
from typing import Any

IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "site-packages",
    "venv",
}
CONFIG_DIR_NAMES = {"conf", "config", "configs"}
YAML_SUFFIXES = {".yaml", ".yml"}
CHECKPOINT_SUFFIXES = {
    ".bin",
    ".ckpt",
    ".joblib",
    ".onnx",
    ".pickle",
    ".pkl",
    ".pt",
    ".pth",
    ".safetensors",
}
ENTRYPOINT_NAME_HINTS = (
    "train",
    "main",
    "run",
    "fit",
    "launch",
    "cli",
    "experiment",
)

HYDRA_MAIN_RE = re.compile(r"@hydra\.main\s*\((?P<args>.*?)\)", re.DOTALL)
HYDRA_COMPOSE_RE = re.compile(r"\bhydra\.compose\s*\((?P<args>.*?)\)", re.DOTALL)
DEFAULTS_RE = re.compile(r"(?m)^\s*defaults\s*:")


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def display_path(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def iter_repo_files(repo: Path, suffixes: set[str]) -> list[Path]:
    files: list[Path] = []
    for root, dirs, filenames in os.walk(repo):
        dirs[:] = [name for name in dirs if name not in IGNORE_DIRS and not name.startswith(".")]
        root_path = Path(root)
        for filename in filenames:
            path = root_path / filename
            if path.suffix.lower() in suffixes:
                files.append(path)
    return sorted(files)


def optional_yaml_load(path: Path) -> Any:
    try:
        import yaml
    except ImportError:
        return None

    try:
        return yaml.safe_load(safe_read_text(path))
    except Exception:
        return None


def nested_get(data: Any, *keys: str) -> Any:
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def extract_kwarg_string(arg_text: str, key: str) -> str | None:
    pattern = re.compile(rf"{re.escape(key)}\s*=\s*(['\"])(.*?)\1", re.DOTALL)
    match = pattern.search(arg_text)
    if not match:
        return None
    return match.group(2)


def build_entrypoint_record(repo: Path, file_path: Path, match: re.Match[str], kind: str) -> dict[str, Any]:
    args_text = match.group("args")
    line = safe_read_text(file_path).count("\n", 0, match.start()) + 1
    config_path = extract_kwarg_string(args_text, "config_path")
    config_name = extract_kwarg_string(args_text, "config_name")
    version_base = extract_kwarg_string(args_text, "version_base")
    resolved_root = resolve_config_root(repo, file_path, config_path)
    return {
        "path": display_path(file_path, repo),
        "line": line,
        "kind": kind,
        "config_path": config_path,
        "config_name": config_name,
        "version_base": version_base,
        "resolved_config_root": display_path(resolved_root, repo) if resolved_root else None,
    }


def resolve_config_root(repo: Path, file_path: Path, config_path: str | None) -> Path | None:
    if config_path is None:
        return None
    if config_path in ("", "."):
        return file_path.parent
    candidate = (file_path.parent / config_path).resolve()
    if candidate.exists():
        return candidate
    fallback = (repo / config_path).resolve()
    if fallback.exists():
        return fallback
    return candidate


def infer_config_root_from_yaml(yaml_path: Path, repo: Path) -> Path:
    relative = yaml_path.relative_to(repo)
    current = repo
    chosen: Path | None = None
    for part in relative.parts[:-1]:
        current = current / part
        if part in CONFIG_DIR_NAMES:
            chosen = current
    return chosen or yaml_path.parent


def summarize_config_root(root: Path) -> dict[str, Any]:
    groups: set[str] = set()
    top_level_configs: set[str] = set()
    defaults_files: set[str] = set()
    launcher_options: set[str] = set()
    sweeper_options: set[str] = set()

    for path in iter_repo_files(root, YAML_SUFFIXES):
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if DEFAULTS_RE.search(safe_read_text(path)):
            defaults_files.add(str(relative))
        if len(relative.parts) == 1:
            top_level_configs.add(relative.name)
            continue
        group = relative.parts[0]
        groups.add(group)
        if relative.parts[:2] == ("hydra", "launcher") and path.suffix.lower() in YAML_SUFFIXES:
            launcher_options.add(path.stem)
        if relative.parts[:2] == ("hydra", "sweeper") and path.suffix.lower() in YAML_SUFFIXES:
            sweeper_options.add(path.stem)

    return {
        "path": str(root),
        "groups": sorted(groups),
        "top_level_configs": sorted(top_level_configs),
        "defaults_files": sorted(defaults_files),
        "launcher_options": sorted(launcher_options),
        "sweeper_options": sorted(sweeper_options),
    }


def discover_hydra_project(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    python_files = iter_repo_files(repo, {".py"})
    yaml_files = iter_repo_files(repo, YAML_SUFFIXES)

    entrypoints: list[dict[str, Any]] = []
    compose_calls: list[dict[str, Any]] = []
    omegaconf_files: list[str] = []
    config_roots: dict[Path, dict[str, Any]] = {}
    output_patterns: list[dict[str, Any]] = []

    for py_file in python_files:
        text = safe_read_text(py_file)
        if "OmegaConf" in text:
            omegaconf_files.append(display_path(py_file, repo))
        for match in HYDRA_MAIN_RE.finditer(text):
            record = build_entrypoint_record(repo, py_file, match, "hydra.main")
            entrypoints.append(record)
            resolved_root = record.get("resolved_config_root")
            if resolved_root:
                root_path = (repo / resolved_root).resolve()
                config_roots[root_path] = summarize_config_root(root_path)
        for match in HYDRA_COMPOSE_RE.finditer(text):
            compose_calls.append(build_entrypoint_record(repo, py_file, match, "hydra.compose"))

    for yaml_file in yaml_files:
        text = safe_read_text(yaml_file)
        if DEFAULTS_RE.search(text):
            root = infer_config_root_from_yaml(yaml_file, repo)
            config_roots[root.resolve()] = summarize_config_root(root.resolve())

        data = optional_yaml_load(yaml_file)
        if not isinstance(data, dict):
            continue

        run_dir = nested_get(data, "hydra", "run", "dir")
        if run_dir is None and "hydra.run.dir" in data:
            run_dir = data.get("hydra.run.dir")
        sweep_dir = nested_get(data, "hydra", "sweep", "dir")
        if sweep_dir is None and "hydra.sweep.dir" in data:
            sweep_dir = data.get("hydra.sweep.dir")
        sweep_subdir = nested_get(data, "hydra", "sweep", "subdir")
        if sweep_subdir is None and "hydra.sweep.subdir" in data:
            sweep_subdir = data.get("hydra.sweep.subdir")

        if run_dir is not None or sweep_dir is not None or sweep_subdir is not None:
            output_patterns.append(
                {
                    "path": display_path(yaml_file, repo),
                    "run_dir": run_dir,
                    "sweep_dir": sweep_dir,
                    "sweep_subdir": sweep_subdir,
                }
            )

    return {
        "repo": str(repo),
        "likely_hydra_project": bool(entrypoints or compose_calls or config_roots),
        "entrypoints": sorted(entrypoints, key=lambda item: (item["path"], item["line"])),
        "compose_calls": sorted(compose_calls, key=lambda item: (item["path"], item["line"])),
        "omegaconf_files": sorted(set(omegaconf_files)),
        "config_roots": [
            {
                "path": display_path(Path(root), repo),
                "groups": details["groups"],
                "top_level_configs": details["top_level_configs"],
                "defaults_files": details["defaults_files"],
                "launcher_options": details["launcher_options"],
                "sweeper_options": details["sweeper_options"],
            }
            for root, details in sorted(config_roots.items(), key=lambda item: str(item[0]))
        ],
        "output_patterns": sorted(output_patterns, key=lambda item: item["path"]),
    }


def discover_python_entrypoints(repo: Path, limit: int = 20) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for py_file in iter_repo_files(repo, {".py"}):
        text = safe_read_text(py_file)
        relative = display_path(py_file, repo)
        reasons: list[str] = []

        lower_name = py_file.stem.lower()
        if any(hint in lower_name for hint in ENTRYPOINT_NAME_HINTS):
            reasons.append("filename looks like an entrypoint")
        if 'if __name__ == "__main__":' in text:
            reasons.append("has __main__ guard")
        if "argparse" in text:
            reasons.append("uses argparse")
        if "typer" in text:
            reasons.append("uses typer")
        if "click" in text:
            reasons.append("uses click")
        if re.search(r"\bdef\s+(train|main|run|fit)\s*\(", text):
            reasons.append("defines a likely training or main function")

        if reasons:
            candidates.append({"path": relative, "reasons": reasons})

    return candidates[:limit]


def find_existing_config_dirs(repo: Path, limit: int = 20) -> list[str]:
    matches: list[str] = []
    for root, dirs, _ in os.walk(repo):
        dirs[:] = [name for name in dirs if name not in IGNORE_DIRS and not name.startswith(".")]
        for dirname in dirs:
            if dirname in CONFIG_DIR_NAMES:
                path = Path(root) / dirname
                matches.append(display_path(path, repo))
                if len(matches) >= limit:
                    return sorted(matches)
    return sorted(matches)


def detect_project_stack(repo: Path) -> dict[str, bool]:
    stack = {
        "pytorch": False,
        "lightning": False,
        "transformers": False,
        "jax": False,
        "tensorflow": False,
    }
    for py_file in iter_repo_files(repo, {".py"}):
        text = safe_read_text(py_file)
        if "import torch" in text or "from torch" in text:
            stack["pytorch"] = True
        if "lightning" in text or "pytorch_lightning" in text:
            stack["lightning"] = True
        if "transformers" in text:
            stack["transformers"] = True
        if "import jax" in text or "from jax" in text:
            stack["jax"] = True
        if "import tensorflow" in text or "from tensorflow" in text:
            stack["tensorflow"] = True
    return stack


def identify_training_files(repo: Path, limit: int = 20) -> list[str]:
    matches: list[str] = []
    pattern = re.compile(r"\b(train|trainer|fit|epoch|optimizer|dataloader|checkpoint)\b", re.IGNORECASE)
    for py_file in iter_repo_files(repo, {".py"}):
        text = safe_read_text(py_file)
        if pattern.search(py_file.name) or pattern.search(text):
            matches.append(display_path(py_file, repo))
            if len(matches) >= limit:
                break
    return matches


def extract_argparse_defaults(entrypoint_path: Path) -> list[dict[str, Any]]:
    try:
        tree = ast.parse(safe_read_text(entrypoint_path), filename=str(entrypoint_path))
    except SyntaxError:
        return []

    defaults: list[dict[str, Any]] = []
    seen: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "add_argument":
            continue

        option_names = []
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value.startswith("--"):
                option_names.append(arg.value)
        if not option_names:
            continue

        canonical = option_names[-1].lstrip("-").replace("-", "_")
        if canonical in seen:
            continue
        seen.add(canonical)

        default_value = None
        action_value = None
        for keyword in node.keywords:
            if keyword.arg == "default":
                default_value = literal_or_none(keyword.value)
            elif keyword.arg == "action":
                action_value = literal_or_none(keyword.value)

        if action_value == "store_true" and default_value is None:
            default_value = False
        elif action_value == "store_false" and default_value is None:
            default_value = True

        defaults.append(
            {
                "name": canonical,
                "flags": option_names,
                "default": default_value,
                "action": action_value,
            }
        )
    return defaults


def literal_or_none(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def yaml_dump(data: Any) -> str:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to dump YAML") from exc
    return yaml.safe_dump(data, sort_keys=False)


def parse_default_entry(entry: Any) -> dict[str, Any]:
    if entry == "_self_":
        return {"kind": "self"}
    if isinstance(entry, str):
        normalized = entry.strip()
        if normalized in {"_self_", ""}:
            return {"kind": "self"}
        if normalized.startswith("optional "):
            normalized = normalized[len("optional ") :].strip()
        if normalized.startswith("override "):
            normalized = normalized[len("override ") :].strip()
        if "/" in normalized:
            group, option = normalized.rsplit("/", 1)
            return {"kind": "select", "group": group.lstrip("/"), "option": option}
        return {"kind": "unknown", "raw": entry}
    if isinstance(entry, dict) and entry:
        key, value = next(iter(entry.items()))
        group = str(key).strip()
        if group.startswith("optional "):
            group = group[len("optional ") :].strip()
        if group.startswith("override "):
            group = group[len("override ") :].strip()
        group = group.split("@", 1)[0].lstrip("/")
        return {"kind": "select", "group": group, "option": value}
    return {"kind": "unknown", "raw": entry}


def split_override_kinds(overrides: list[str], config_root: Path) -> tuple[dict[str, str], list[dict[str, Any]], list[str]]:
    group_overrides: dict[str, str] = {}
    value_overrides: list[dict[str, Any]] = []
    unresolved: list[str] = []

    for raw in overrides:
        text = raw.strip()
        if not text:
            continue
        if text.startswith("~"):
            unresolved.append(raw)
            continue

        body = text
        operation = "assign"
        if body.startswith("++"):
            body = body[2:]
            operation = "force_add_or_override"
        elif body.startswith("+"):
            body = body[1:]
            operation = "add"

        key, sep, value = body.partition("=")
        key = key.strip()
        value = value.strip() if sep else None
        if not sep or not key:
            unresolved.append(raw)
            continue

        group_dir = config_root / key
        if "/" not in key and "." not in key and group_dir.is_dir():
            group_overrides[key] = value
            continue

        value_overrides.append(
            {
                "raw": raw,
                "operation": operation,
                "target": key,
                "value": value,
            }
        )
    return group_overrides, value_overrides, unresolved


def compose_config_with_history(
    config_root: Path,
    config_name: str,
    overrides: list[str] | None = None,
) -> dict[str, Any]:
    config_root = config_root.resolve()
    overrides = overrides or []
    group_overrides, value_overrides, unresolved_overrides = split_override_kinds(overrides, config_root)

    composed: dict[str, Any] = {}
    history: dict[str, list[dict[str, Any]]] = {}
    files_loaded: list[str] = []
    missing_files: list[str] = []

    config_path = config_root / ensure_yaml_suffix(config_name)
    _compose_file(
        config_path=config_path,
        config_root=config_root,
        composed=composed,
        history=history,
        files_loaded=files_loaded,
        missing_files=missing_files,
        group_overrides=group_overrides,
        visited=set(),
    )

    for override in value_overrides:
        value = parse_cli_scalar(override["value"])
        apply_value_override(composed, history, override["target"], value, override["raw"])

    return {
        "config_root": str(config_root),
        "config_name": ensure_yaml_suffix(config_name),
        "composed": composed,
        "history": history,
        "files_loaded": files_loaded,
        "missing_files": missing_files,
        "group_overrides_applied": group_overrides,
        "value_overrides_applied": value_overrides,
        "unresolved_overrides": unresolved_overrides,
    }


def _compose_file(
    config_path: Path,
    config_root: Path,
    composed: dict[str, Any],
    history: dict[str, list[dict[str, Any]]],
    files_loaded: list[str],
    missing_files: list[str],
    group_overrides: dict[str, str],
    visited: set[Path],
    package_prefix: tuple[str, ...] = (),
) -> None:
    config_path = config_path.resolve()
    if config_path in visited:
        return
    visited.add(config_path)

    if not config_path.exists():
        missing_files.append(display_path(config_path, config_root))
        return

    raw_data = optional_yaml_load(config_path)
    if raw_data is None:
        raw_data = {}
    if not isinstance(raw_data, dict):
        raw_data = {}
    data = deepcopy(raw_data)
    defaults = data.pop("defaults", []) or []
    if not isinstance(defaults, list):
        defaults = []

    files_loaded.append(display_path(config_path, config_root))

    self_applied = False
    for entry in defaults:
        parsed = parse_default_entry(entry)
        kind = parsed.get("kind")
        if kind == "self":
            merge_with_history(
                composed,
                data,
                history,
                display_path(config_path, config_root),
                prefix=package_prefix,
            )
            self_applied = True
            continue
        if kind != "select":
            continue

        group = str(parsed["group"])
        option = parsed.get("option")
        if group in group_overrides:
            option = group_overrides[group]
        if option in (None, "null"):
            continue
        child_path = config_root / group / ensure_yaml_suffix(str(option))
        _compose_file(
            config_path=child_path,
            config_root=config_root,
            composed=composed,
            history=history,
            files_loaded=files_loaded,
            missing_files=missing_files,
            group_overrides=group_overrides,
            visited=visited,
            package_prefix=tuple(part for part in group.split("/") if part),
        )

    if not self_applied:
        merge_with_history(
            composed,
            data,
            history,
            display_path(config_path, config_root),
            prefix=package_prefix,
        )


def merge_with_history(
    target: dict[str, Any],
    incoming: dict[str, Any],
    history: dict[str, list[dict[str, Any]]],
    source: str,
    prefix: tuple[str, ...] = (),
) -> None:
    for key, value in incoming.items():
        path = prefix + (str(key),)
        dotted = ".".join(path)
        if isinstance(value, dict):
            existing = target.get(key)
            if not isinstance(existing, dict):
                target[key] = {}
            history.setdefault(dotted, []).append({"source": source, "value": deepcopy(value)})
            merge_with_history(target[key], value, history, source, path)
        else:
            target[key] = deepcopy(value)
            history.setdefault(dotted, []).append({"source": source, "value": deepcopy(value)})


def ensure_yaml_suffix(name: str) -> str:
    return name if Path(name).suffix.lower() in YAML_SUFFIXES else f"{name}.yaml"


def parse_cli_scalar(raw: str | None) -> Any:
    if raw is None:
        return None
    text = raw.strip()
    if text.lower() == "true":
        return True
    if text.lower() == "false":
        return False
    if text.lower() == "null":
        return None
    if text.startswith("[") or text.startswith("{"):
        try:
            import yaml

            return yaml.safe_load(text)
        except Exception:
            return text
    if "," in text:
        return [parse_cli_scalar(part) for part in text.split(",")]
    try:
        if "." in text or "e" in text.lower():
            return float(text)
        return int(text)
    except ValueError:
        return text


def apply_value_override(
    composed: dict[str, Any],
    history: dict[str, list[dict[str, Any]]],
    target_path: str,
    value: Any,
    source: str,
) -> None:
    keys = [part for part in target_path.split(".") if part]
    if not keys:
        return
    current = composed
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = deepcopy(value)
    history.setdefault(target_path, []).append({"source": f"override:{source}", "value": deepcopy(value)})


def get_nested_value(data: dict[str, Any], dotted_path: str) -> Any:
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def find_hydra_run_dir(start: Path) -> Path | None:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in [current, *current.parents]:
        if (candidate / ".hydra").is_dir():
            return candidate
    return None


def parse_overrides(path: Path | None) -> list[str]:
    if path is None or not path.exists():
        return []
    data = optional_yaml_load(path)
    if isinstance(data, list):
        return [str(item) for item in data]

    overrides: list[str] = []
    for raw_line in safe_read_text(path).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            overrides.append(line[2:].strip())
        else:
            overrides.append(line)
    return overrides


def list_checkpoint_candidates(run_dir: Path, max_depth: int = 4, limit: int = 20) -> list[str]:
    matches: list[str] = []
    for root, dirs, filenames in os.walk(run_dir):
        root_path = Path(root)
        try:
            depth = len(root_path.relative_to(run_dir).parts)
        except ValueError:
            continue
        if depth > max_depth:
            dirs[:] = []
            continue
        dirs[:] = [name for name in dirs if name != ".hydra"]
        for filename in filenames:
            path = root_path / filename
            if path.suffix.lower() in CHECKPOINT_SUFFIXES:
                matches.append(str(path.relative_to(run_dir)))
                if len(matches) >= limit:
                    return sorted(matches)
    return sorted(matches)


def load_run_metadata(run_dir: Path) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    hydra_dir = run_dir / ".hydra"
    config_path = hydra_dir / "config.yaml"
    hydra_path = hydra_dir / "hydra.yaml"
    overrides_path = hydra_dir / "overrides.yaml"

    config_data = optional_yaml_load(config_path) if config_path.exists() else None
    hydra_data = optional_yaml_load(hydra_path) if hydra_path.exists() else None

    top_level_keys: list[str] = []
    if isinstance(config_data, dict):
        top_level_keys = sorted(str(key) for key in config_data.keys())

    runtime_summary = {}
    if isinstance(hydra_data, dict):
        runtime_summary = {
            "cwd": nested_get(hydra_data, "runtime", "cwd"),
            "output_dir": nested_get(hydra_data, "runtime", "output_dir"),
            "job_name": nested_get(hydra_data, "job", "name"),
            "job_num": nested_get(hydra_data, "job", "num"),
            "run_dir": nested_get(hydra_data, "run", "dir"),
            "sweep_dir": nested_get(hydra_data, "sweep", "dir"),
            "sweep_subdir": nested_get(hydra_data, "sweep", "subdir"),
        }

    checkpoint_candidates = list_checkpoint_candidates(run_dir)
    reproducibility_gaps: list[str] = []
    if not hydra_dir.is_dir():
        reproducibility_gaps.append("missing .hydra directory")
    if not config_path.exists():
        reproducibility_gaps.append("missing .hydra/config.yaml")
    if not hydra_path.exists():
        reproducibility_gaps.append("missing .hydra/hydra.yaml")
    if not overrides_path.exists():
        reproducibility_gaps.append("missing .hydra/overrides.yaml")
    if not checkpoint_candidates:
        reproducibility_gaps.append("no obvious checkpoint artifacts found under the run directory")

    return {
        "run_dir": str(run_dir),
        "hydra_dir": str(hydra_dir) if hydra_dir.is_dir() else None,
        "metadata_files": {
            "config_yaml": str(config_path) if config_path.exists() else None,
            "hydra_yaml": str(hydra_path) if hydra_path.exists() else None,
            "overrides_yaml": str(overrides_path) if overrides_path.exists() else None,
        },
        "overrides": parse_overrides(overrides_path),
        "top_level_config_keys": top_level_keys,
        "runtime_summary": runtime_summary,
        "checkpoint_candidates": checkpoint_candidates,
        "reproducibility_gaps": reproducibility_gaps,
    }
