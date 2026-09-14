"""Bounded JSON import/export for already-redacted deployment snapshots."""

from __future__ import annotations

import json
import math
from pathlib import Path

from dify_preflight.domain import DeploymentSnapshot, Fact, FactOrigin, FactStatus

MAX_SNAPSHOT_BYTES = 2 * 1024 * 1024


class SnapshotInputError(ValueError):
    """A deliberately non-diagnostic error for untrusted snapshot input."""


def load_snapshot(path: Path) -> DeploymentSnapshot:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_SNAPSHOT_BYTES:
            raise SnapshotInputError("snapshot_path")
        raw = path.read_text(encoding="utf-8")
        value = json.loads(raw, object_pairs_hook=_no_duplicate_keys, parse_constant=_reject_constant)
    except SnapshotInputError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise SnapshotInputError("snapshot_parse") from error
    return _snapshot(value)


def write_snapshot(snapshot: DeploymentSnapshot, path: Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as handle:
            json.dump(snapshot.to_dict(), handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    except (OSError, TypeError, ValueError) as error:
        raise SnapshotInputError("snapshot_output") from error


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SnapshotInputError("snapshot_duplicate_key")
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise SnapshotInputError("snapshot_non_finite")


def _snapshot(value: object) -> DeploymentSnapshot:
    expected = {"schema_version", "kind", "synthetic", "snapshot_id", "capture", "facts", "public_config", "private_relations", "gaps"}
    if not isinstance(value, dict) or set(value) != expected:
        raise SnapshotInputError("snapshot_schema")
    if value["schema_version"] != "1.0" or value["kind"] != "deployment_snapshot" or not isinstance(value["synthetic"], bool):
        raise SnapshotInputError("snapshot_schema")
    if not isinstance(value["snapshot_id"], str) or not isinstance(value["capture"], dict):
        raise SnapshotInputError("snapshot_schema")
    if not isinstance(value["facts"], dict) or not isinstance(value["public_config"], dict) or not isinstance(value["private_relations"], dict) or not isinstance(value["gaps"], list):
        raise SnapshotInputError("snapshot_schema")
    capture = value["capture"]
    if capture.get("mode") not in {"synthetic", "compose_declared", "live_opt_in"} or not isinstance(capture.get("collector_version"), str):
        raise SnapshotInputError("snapshot_capture")
    facts = {name: _fact(name, item) for name, item in value["facts"].items()}
    if any(not isinstance(name, str) or name.startswith("private.") for name in facts):
        raise SnapshotInputError("snapshot_fact")
    if any(not isinstance(name, str) or relation not in {True, False, None} for name, relation in value["private_relations"].items()):
        raise SnapshotInputError("snapshot_private_relation")
    if not all(isinstance(item, dict) for item in value["gaps"]):
        raise SnapshotInputError("snapshot_gaps")
    if not all(_scalar_or_none(item) for item in value["public_config"].values()):
        raise SnapshotInputError("snapshot_public_config")
    return DeploymentSnapshot(
        schema_version="1.0", kind="deployment_snapshot", synthetic=value["synthetic"], snapshot_id=value["snapshot_id"],
        capture=capture, facts=facts, public_config=value["public_config"], private_relations=value["private_relations"], gaps=tuple(value["gaps"]),
    )


def _fact(name: object, value: object) -> Fact:
    if not isinstance(name, str) or not isinstance(value, dict) or set(value) != {"status", "value", "origin", "source_ref", "reason"}:
        raise SnapshotInputError("snapshot_fact")
    try:
        status = FactStatus(value["status"])
        origin = FactOrigin(value["origin"])
    except (TypeError, ValueError) as error:
        raise SnapshotInputError("snapshot_fact") from error
    if not isinstance(value["source_ref"], str) or (value["reason"] is not None and not isinstance(value["reason"], str)):
        raise SnapshotInputError("snapshot_fact")
    if status is FactStatus.KNOWN:
        if not _scalar(value["value"]):
            raise SnapshotInputError("snapshot_fact")
    elif value["value"] is not None:
        raise SnapshotInputError("snapshot_fact")
    # source_ref and reason originate in an untrusted snapshot.  Decisions do
    # not need their text, and rendering either field could disclose a path or
    # a secret embedded by a malformed producer.
    return Fact(status, value["value"], origin, f"snapshot:{origin.value}", None)


def _scalar(value: object) -> bool:
    return isinstance(value, (str, int, float, bool)) and not (isinstance(value, float) and not math.isfinite(value))


def _scalar_or_none(value: object) -> bool:
    return value is None or _scalar(value)
