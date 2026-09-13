"""Bounded, deterministic three-way comparison of approved public fields."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Final

from dify_preflight.domain import Comparability, ConfigChange, ConfigChangeKind, MISSING, PublicConfig


_SERVICE_FIELD: Final = re.compile(
    r"^services\.[A-Za-z0-9_-]+\.(?:image_tag|present|depends_on\.[A-Za-z0-9_-]+|ports|volumes|secrets|configs)$"
)
_RECOVERY_FIELD: Final = re.compile(r"^(?:agent_sandbox\.target_network_topology|plugins\.provider_cache_enabled)$")
_KEYED_FIELDS: Final = {
    ".ports": ("host_ip", "target", "published", "protocol"),
    ".volumes": ("target",),
    ".secrets": ("target",),
    ".configs": ("target",),
}


def compare_three_way(
    base: PublicConfig,
    local: PublicConfig,
    target: PublicConfig,
    proposed: PublicConfig | None = None,
) -> list[ConfigChange]:
    """Compare only registered public fields; no I/O or policy decisions occur here."""
    paths = sorted(set(base) | set(local) | set(target) | (set(proposed) if proposed is not None else set()))
    return [_compare_path(path, base, local, target, proposed) for path in paths]


def _compare_path(
    path: str,
    base: PublicConfig,
    local: PublicConfig,
    target: PublicConfig,
    proposed: PublicConfig | None,
) -> ConfigChange:
    values = (
        base.get(path, MISSING),
        local.get(path, MISSING),
        target.get(path, MISSING),
        proposed.get(path, MISSING) if proposed is not None else MISSING,
    )
    if not (_SERVICE_FIELD.fullmatch(path) or _RECOVERY_FIELD.fullmatch(path)):
        return ConfigChange(
            path,
            ConfigChangeKind.UNKNOWN_COMPARISON,
            Comparability.UNKNOWN,
            MISSING,
            MISSING,
            MISSING,
            MISSING,
            "field_not_registered",
        )
    if any(_contains_redaction(value) for value in values):
        return ConfigChange(path, ConfigChangeKind.UNKNOWN_COMPARISON, Comparability.UNKNOWN, *values, "redacted_value_is_not_comparable")
    try:
        normalized = tuple(_normalize(path, value) for value in values)
    except ValueError as exc:
        return ConfigChange(path, ConfigChangeKind.UNKNOWN_COMPARISON, Comparability.UNKNOWN, *values, str(exc))
    kind = _classify(*normalized[:3])
    reason = "proposed_configuration_not_supplied" if proposed is None else "public_field_comparison"
    return ConfigChange(path, kind, Comparability.PUBLIC, *values, reason)


def _classify(base: object, local: object, target: object) -> ConfigChangeKind:
    if _equal(base, local) and _equal(local, target):
        return ConfigChangeKind.UNCHANGED
    if _equal(base, local):
        return ConfigChangeKind.UPSTREAM_ONLY
    if _equal(base, target):
        return ConfigChangeKind.LOCAL_ONLY
    if _equal(local, target):
        return ConfigChangeKind.SAME_CHANGE
    return ConfigChangeKind.DIVERGENT_CHANGE


def _equal(left: object, right: object) -> bool:
    if left is MISSING or right is MISSING:
        return left is right
    return _stable(left) == _stable(right)


def _normalize(path: str, value: object) -> object:
    if value is MISSING or value is None or isinstance(value, (str, int, float, bool)):
        return value
    for suffix, key_fields in _KEYED_FIELDS.items():
        if path.endswith(suffix):
            return _keyed_list(value, key_fields)
    raise ValueError("registered_field_has_unsupported_value")


def _keyed_list(value: object, key_fields: tuple[str, ...]) -> tuple[tuple[object, object], ...]:
    if not isinstance(value, list):
        raise ValueError("keyed_field_has_non_list_value")
    normalized: list[tuple[object, object]] = []
    seen: set[object] = set()
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError("keyed_field_item_is_not_object")
        if "target" not in item:
            raise ValueError("keyed_field_has_missing_or_duplicate_key")
        key = tuple(item.get(field) for field in key_fields)
        if key in seen:
            raise ValueError("keyed_field_has_missing_or_duplicate_key")
        seen.add(key)
        normalized.append((key, _json_value(item)))
    return tuple(sorted(normalized, key=lambda pair: _stable(pair[0])))


def _json_value(value: object) -> object:
    try:
        return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    except (TypeError, ValueError) as exc:
        raise ValueError("field_value_is_not_json_compatible") from exc


def _stable(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _contains_redaction(value: object) -> bool:
    if value == "REDACTED":
        return True
    if isinstance(value, Mapping):
        return any(_contains_redaction(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_redaction(item) for item in value)
    return False
