"""Load only a locally bounded, approval-hash-checked catalog."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import yaml
from yaml.events import AliasEvent

from .validate import CatalogValidationError, validate_matrix, validate_rule


@dataclass(frozen=True)
class CatalogPolicy:
    root: Path
    approved_sources: Mapping[str, str] = field(default_factory=dict)
    approval_hashes: Mapping[str, Mapping[str, str]] | None = None
    trust: str = "untrusted"


@dataclass(frozen=True)
class Catalog:
    edges: tuple[dict[str, object], ...]
    rules: tuple[dict[str, object], ...]
    digest: str
    trust: str
    source_digests: Mapping[str, str] = field(default_factory=dict)


def load_catalog(path: Path, policy: CatalogPolicy) -> Catalog:
    if policy.trust not in {"bundled", "owner_approved_local", "untrusted", "synthetic"}:
        raise CatalogValidationError("catalog_trust")
    if not isinstance(policy.approved_sources, Mapping):
        raise CatalogValidationError("source_not_fixed")
    root = policy.root.resolve(strict=True)
    matrix_path = _inside_regular(path, root)
    matrix = validate_matrix(_load_yaml(matrix_path))
    rules: list[dict[str, object]] = []
    rule_paths: dict[str, str] = {}
    ids: set[str] = set()
    approved = root / "approved"
    if approved.exists():
        if approved.is_symlink() or not approved.is_dir():
            raise CatalogValidationError("path")
        rule_files = sorted(approved.glob("*.yaml"))
        if len(rule_files) > 100 or sum(item.stat().st_size for item in rule_files) > 32 * 1024 * 1024:
            raise CatalogValidationError("catalog_too_large")
        for rule_path in rule_files:
            item = validate_rule(_load_yaml(_inside_regular(rule_path, root)))
            if item["id"] in ids:
                raise CatalogValidationError("duplicate_rule_id")
            ids.add(item["id"])
            rules.append(item)
            rule_paths[str(item["id"])] = rule_path.relative_to(root).as_posix()
    source_digests = _validate_references(matrix, rules, rule_paths, matrix_path.relative_to(root).as_posix(), policy)
    digest = hashlib.sha256(json.dumps({"matrix": matrix, "rules": rules, "source_digests": source_digests}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return Catalog(matrix, tuple(rules), digest, policy.trust, source_digests)


def _load_yaml(path: Path) -> object:
    try:
        if path.stat().st_size > 2 * 1024 * 1024:
            raise CatalogValidationError("file_too_large")
        text = path.read_text(encoding="utf-8")
        if sum(isinstance(event, AliasEvent) for event in yaml.parse(text, Loader=yaml.SafeLoader)) > 64:
            raise CatalogValidationError("yaml_alias_limit")
        value = yaml.load(text, Loader=_CatalogLoader)
    except CatalogValidationError:
        raise
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise CatalogValidationError("parse") from error
    return value


class _CatalogLoader(yaml.SafeLoader):
    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[object, object]:
        keys: set[object] = set()
        for key_node, _ in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                continue
            key = self.construct_object(key_node, deep=deep)
            try:
                duplicate = key in keys
            except TypeError as error:
                raise CatalogValidationError("parse") from error
            if duplicate:
                raise CatalogValidationError("duplicate_key")
            keys.add(key)
        return super().construct_mapping(node, deep=deep)


def _inside_regular(path: Path, root: Path) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise CatalogValidationError("path") from error
    if root != resolved and root not in resolved.parents:
        raise CatalogValidationError("path")
    if path.is_symlink() or not resolved.is_file():
        raise CatalogValidationError("path")
    return resolved


def _validate_references(edges: tuple[dict[str, object], ...], rules: list[dict[str, object]], rule_paths: Mapping[str, str], matrix_path: str, policy: CatalogPolicy) -> dict[str, str]:
    by_edge = {str(edge["id"]): edge for edge in edges}
    by_rule = {str(rule["id"]): rule for rule in rules}
    for edge in edges:
        if any(rule_id not in by_rule for rule_id in edge["rule_ids"]):
            raise CatalogValidationError("edge_rule_missing")
        if any(edge["id"] not in by_rule[str(rule_id)]["support_edge_ids"] for rule_id in edge["rule_ids"]):
            raise CatalogValidationError("edge_rule_scope")
        _require_approval(str(edge["approval_ref"]), matrix_path, policy)
    referenced: dict[str, str] = {}
    for rule in rules:
        if any(not _source_is_fixed(source, policy) for source in rule["evidence_refs"]):
            raise CatalogValidationError("source_not_fixed")
        for source in rule["evidence_refs"]:
            referenced[str(source)] = policy.approved_sources[str(source)]
            _require_source_approval(str(rule["review_ref"]), str(source), policy.approved_sources[str(source)], policy)
        if any(edge_id not in by_edge for edge_id in rule["support_edge_ids"]):
            raise CatalogValidationError("rule_edge_missing")
        if any(rule["id"] not in by_edge[str(edge_id)]["rule_ids"] for edge_id in rule["support_edge_ids"]):
            raise CatalogValidationError("edge_rule_scope")
        if any(old not in by_rule or old == rule["id"] for old in rule["supersedes"]):
            raise CatalogValidationError("supersedes_missing")
        _require_approval(str(rule["review_ref"]), rule_paths[str(rule["id"])], policy)
    return dict(sorted(referenced.items()))


def _source_is_fixed(source: object, policy: CatalogPolicy) -> bool:
    digest = policy.approved_sources.get(str(source))
    return isinstance(digest, str) and len(digest) == 64 and all(char in "0123456789abcdef" for char in digest)


def _require_approval(ref: str, expected_path: str, policy: CatalogPolicy) -> None:
    if policy.approval_hashes is None:
        if policy.trust == "untrusted":
            return
        raise CatalogValidationError("approval_missing")
    hashes = policy.approval_hashes.get(ref)
    if not hashes:
        raise CatalogValidationError("approval_missing")
    if expected_path not in hashes:
        raise CatalogValidationError("approval_hash")
    actual = hashlib.sha256((policy.root / expected_path).read_bytes()).hexdigest()
    if actual != hashes[expected_path]:
        raise CatalogValidationError("approval_hash")


def _require_source_approval(ref: str, source: str, digest: str, policy: CatalogPolicy) -> None:
    if policy.approval_hashes is None:
        if policy.trust == "untrusted":
            return
        raise CatalogValidationError("approval_missing")
    hashes = policy.approval_hashes.get(ref)
    if hashes is None or hashes.get(f"sources/{source}") != digest:
        raise CatalogValidationError("source_approval")
