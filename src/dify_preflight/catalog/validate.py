"""Structural validation for the deliberately small catalog format."""

from __future__ import annotations

from collections.abc import Mapping
import math
import re
from typing import Any


class CatalogValidationError(ValueError):
    """A sanitized catalog validation category, never raw rule contents."""


_RULE_FIELDS = frozenset({
    "schema_version", "id", "revision", "synthetic", "status", "title", "scope", "support_edge_ids",
    "applies", "assertion", "severity", "evidence_refs", "review_ref", "supersedes", "remediation",
})
_EDGE_FIELDS = frozenset({
    "id", "source_version", "target_version", "source_commit", "target_commit", "deployment_profile",
    "compose_version", "scope", "required_facts", "rule_ids", "case_ids", "approval_ref",
})
_OPS = frozenset({"eq", "ne", "in", "version_lt", "version_lte", "version_gt", "version_gte"})


def validate_matrix(value: object) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, Mapping) or set(value) != {"schema_version", "catalog_version", "approved_edges"}:
        raise CatalogValidationError("matrix_schema")
    if value["schema_version"] != "1.0" or not isinstance(value["catalog_version"], str) or not isinstance(value["approved_edges"], list):
        raise CatalogValidationError("matrix_schema")
    edges: list[dict[str, Any]] = []
    ids: set[str] = set()
    identities: set[tuple[str, str, str]] = set()
    for edge in value["approved_edges"]:
        if not isinstance(edge, Mapping) or set(edge) != _EDGE_FIELDS:
            raise CatalogValidationError("edge_schema")
        if not all(isinstance(edge[key], str) and edge[key] for key in _EDGE_FIELDS - {"required_facts", "rule_ids", "case_ids"}):
            raise CatalogValidationError("edge_schema")
        identity = (edge["source_version"], edge["target_version"], edge["scope"])
        if edge["scope"] != "static_upgrade_plan" or edge["source_version"] == edge["target_version"] or edge["id"] in ids or identity in identities:
            raise CatalogValidationError("edge_scope")
        if not re.fullmatch(r"[0-9a-f]{40}", edge["source_commit"]) or not re.fullmatch(r"[0-9a-f]{40}", edge["target_commit"]):
            raise CatalogValidationError("edge_schema")
        if any(len(edge[key]) == 0 or not all(isinstance(item, str) and item for item in edge[key]) for key in ("required_facts", "rule_ids", "case_ids")):
            raise CatalogValidationError("edge_schema")
        ids.add(edge["id"])
        identities.add(identity)
        edges.append(dict(edge))
    return tuple(edges)


def validate_rule(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _RULE_FIELDS:
        raise CatalogValidationError("rule_schema")
    if value["schema_version"] != "1.0":
        raise CatalogValidationError("schema_version")
    if value["status"] != "approved" or value["synthetic"] is not False or value["scope"] != "static_upgrade_plan":
        raise CatalogValidationError("rule_status")
    if not isinstance(value["id"], str) or not value["id"] or not isinstance(value["revision"], int) or value["revision"] < 1:
        raise CatalogValidationError("rule_schema")
    for key in ("support_edge_ids", "evidence_refs"):
        if not isinstance(value[key], list) or not value[key] or not all(isinstance(item, str) and item for item in value[key]):
            raise CatalogValidationError("source_missing" if key == "evidence_refs" else "rule_schema")
    if not isinstance(value["review_ref"], str) or not value["review_ref"]:
        raise CatalogValidationError("approval_missing")
    if not isinstance(value["supersedes"], list) or not all(isinstance(item, str) and item for item in value["supersedes"]):
        raise CatalogValidationError("rule_schema")
    if value["severity"] not in {"blocker", "warning", "info"}:
        raise CatalogValidationError("rule_schema")
    nodes = [0]
    _validate_expression(value["applies"], depth=1, nodes=nodes)
    _validate_expression(value["assertion"], depth=1, nodes=nodes)
    remediation = value["remediation"]
    if not isinstance(remediation, Mapping) or set(remediation) != {"phase", "summary", "docs_refs", "executable"}:
        raise CatalogValidationError("remediation_schema")
    if remediation["phase"] not in {"before_upgrade", "during_upgrade", "after_upgrade", "manual_review"} or remediation["executable"] is not False:
        raise CatalogValidationError("executable_remediation")
    if not isinstance(remediation["summary"], str) or not remediation["summary"] or not isinstance(remediation["docs_refs"], list) or not remediation["docs_refs"]:
        raise CatalogValidationError("remediation_schema")
    return dict(value)


def _validate_expression(value: object, *, depth: int, nodes: list[int] | None = None) -> None:
    nodes = [0] if nodes is None else nodes
    nodes[0] += 1
    if nodes[0] > 64:
        raise CatalogValidationError("expression_nodes")
    if depth > 8 or not isinstance(value, Mapping):
        raise CatalogValidationError("expression_depth" if depth > 8 else "expression")
    keys = set(value)
    if keys == {"all"} or keys == {"any"}:
        children = value["all"] if "all" in value else value["any"]
        if not isinstance(children, list) or not children:
            raise CatalogValidationError("empty_boolean")
        if len(children) > 64:
            raise CatalogValidationError("expression_nodes")
        for child in children:
            _validate_expression(child, depth=depth + 1, nodes=nodes)
        return
    if keys == {"not"}:
        _validate_expression(value["not"], depth=depth + 1, nodes=nodes)
        return
    if keys != {"fact", "op", "value"} or not isinstance(value["fact"], str) or not value["fact"] or value["op"] not in _OPS:
        raise CatalogValidationError("expression")
    if value["op"] == "in":
        if not isinstance(value["value"], list) or not value["value"] or not all(_is_scalar(item) for item in value["value"]):
            raise CatalogValidationError("expression")
    elif not _is_scalar(value["value"]):
        raise CatalogValidationError("expression")
    if value["op"].startswith("version_") and not isinstance(value["value"], str):
        raise CatalogValidationError("expression")


def _is_scalar(value: object) -> bool:
    return isinstance(value, (str, int, bool)) or isinstance(value, float) and math.isfinite(value)
