#!/usr/bin/env python3
"""
Shared helpers for inspecting local W&B offline run files.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


def _require_wandb() -> tuple[Any, Any]:
    try:
        from wandb.proto import wandb_internal_pb2
        from wandb.sdk.internal import datastore
    except ImportError as exc:  # pragma: no cover - exercised by CLI usage
        raise RuntimeError(
            "wandb is required to inspect offline runs. Install it with `pip install wandb`."
        ) from exc
    return datastore, wandb_internal_pb2


@dataclass
class OfflineRun:
    path: str
    run_id: str | None
    project: str | None
    entity: str | None
    group: str | None
    job_type: str | None
    name: str | None
    state: str | None
    start_time: float | None
    tags: list[str]
    config: dict[str, Any]
    summary: dict[str, Any]
    history: list[dict[str, Any]]
    files: list[str]
    artifact_events: list[dict[str, Any]]


def parse_value_json(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def assign_nested(target: dict[str, Any], keys: Iterable[str], value: Any) -> None:
    key_list = list(keys)
    if not key_list:
        return

    cursor = target
    for key in key_list[:-1]:
        existing = cursor.get(key)
        if not isinstance(existing, dict):
            existing = {}
            cursor[key] = existing
        cursor = existing
    cursor[key_list[-1]] = value


def flatten_dict(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, value in data.items():
        dotted = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(flatten_dict(value, dotted))
        else:
            flat[dotted] = value
    return flat


def discover_offline_run_files(paths: list[str] | None = None) -> list[Path]:
    roots = [Path(path) for path in (paths or ["."])]
    seen: set[Path] = set()
    run_files: list[Path] = []

    for root in roots:
        if root.is_file() and root.name.startswith("run-") and root.suffix == ".wandb":
            resolved = root.resolve()
            if resolved not in seen:
                seen.add(resolved)
                run_files.append(resolved)
            continue

        if not root.exists():
            continue

        candidates = root.rglob("run-*.wandb")
        for candidate in sorted(candidates):
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                run_files.append(resolved)

    return run_files


def _extract_config(run_record: Any) -> dict[str, Any]:
    config: dict[str, Any] = {}
    if not hasattr(run_record, "config"):
        return config

    for update in run_record.config.update:
        if not update.key:
            continue
        config[update.key] = parse_value_json(update.value_json)
    return config


def _extract_summary(summary_record: Any, target: dict[str, Any]) -> None:
    for update in summary_record.update:
        keys = list(update.nested_key) or ([update.key] if update.key else [])
        assign_nested(target, keys, parse_value_json(update.value_json))


def _extract_history(history_record: Any) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for item in history_record.item:
        keys = list(item.nested_key) or ([item.key] if item.key else [])
        assign_nested(row, keys, parse_value_json(item.value_json))
    return row


def _extract_files(files_record: Any) -> list[str]:
    paths: list[str] = []
    if hasattr(files_record, "files"):
        for file_record in files_record.files:
            if getattr(file_record, "path", None):
                paths.append(file_record.path)
    return paths


def _message_to_dict(message: Any) -> dict[str, Any]:
    try:
        from google.protobuf.json_format import MessageToDict
    except ImportError as exc:  # pragma: no cover - protobuf ships with wandb env
        raise RuntimeError("protobuf json_format is required for artifact parsing.") from exc
    return MessageToDict(message, preserving_proto_field_name=True)


def load_offline_run(path: str | Path) -> OfflineRun:
    datastore, wandb_internal_pb2 = _require_wandb()

    run_path = Path(path).resolve()
    store = datastore.DataStore()
    store.open_for_scan(run_path)

    run_id: str | None = None
    project: str | None = None
    entity: str | None = None
    group: str | None = None
    job_type: str | None = None
    name: str | None = None
    state: str | None = None
    start_time: float | None = None
    tags: list[str] = []
    config: dict[str, Any] = {}
    summary: dict[str, Any] = {}
    history: list[dict[str, Any]] = []
    files: list[str] = []
    artifact_events: list[dict[str, Any]] = []

    while True:
        raw = store.scan_data()
        if raw is None:
            break

        record = wandb_internal_pb2.Record()
        record.ParseFromString(raw)
        kind = record.WhichOneof("record_type")

        if kind == "run":
            run_id = getattr(record.run, "run_id", None) or run_id
            project = getattr(record.run, "project", None) or project
            entity = getattr(record.run, "entity", None) or entity
            group = getattr(record.run, "run_group", None) or group
            job_type = getattr(record.run, "job_type", None) or job_type
            name = getattr(record.run, "display_name", None) or name
            state = getattr(record.run, "_state", None) or state
            tags = list(getattr(record.run, "tags", [])) or tags
            config = _extract_config(record.run)
            if record.run.HasField("start_time"):
                start_time = record.run.start_time.seconds + (
                    record.run.start_time.nanos / 1_000_000_000
                )
        elif kind == "summary":
            _extract_summary(record.summary, summary)
        elif kind == "history":
            history.append(_extract_history(record.history))
        elif kind == "files":
            files.extend(_extract_files(record.files))
        elif kind == "artifact":
            artifact_events.append(_message_to_dict(record.artifact))

    return OfflineRun(
        path=str(run_path),
        run_id=run_id,
        project=project,
        entity=entity,
        group=group,
        job_type=job_type,
        name=name,
        state=state,
        start_time=start_time,
        tags=tags,
        config=config,
        summary=summary,
        history=history,
        files=sorted(set(files)),
        artifact_events=artifact_events,
    )


def load_offline_runs(paths: list[str] | None = None) -> list[OfflineRun]:
    return [load_offline_run(path) for path in discover_offline_run_files(paths)]


def filter_runs(
    runs: list[OfflineRun],
    *,
    project: str | None = None,
    group: str | None = None,
    run_ids: set[str] | None = None,
) -> list[OfflineRun]:
    filtered = runs
    if project:
        filtered = [run for run in filtered if run.project == project]
    if group:
        filtered = [run for run in filtered if run.group == group]
    if run_ids:
        filtered = [run for run in filtered if run.run_id in run_ids]
    return filtered


def metric_value(run: OfflineRun, metric: str) -> Any:
    flat_summary = flatten_dict(run.summary)
    return flat_summary.get(metric)


def varying_config_keys(runs: list[OfflineRun]) -> dict[str, list[Any]]:
    values: dict[str, list[Any]] = {}
    for run in runs:
        for key, value in flatten_dict(run.config).items():
            bucket = values.setdefault(key, [])
            if value not in bucket:
                bucket.append(value)
    return {key: bucket for key, bucket in values.items() if len(bucket) > 1}


def run_to_dict(run: OfflineRun) -> dict[str, Any]:
    result = asdict(run)
    result["flat_config"] = flatten_dict(run.config)
    result["flat_summary"] = flatten_dict(run.summary)
    return result
