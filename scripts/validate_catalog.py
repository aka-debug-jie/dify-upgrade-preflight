#!/usr/bin/env python3
"""Validate catalog structure without treating a planning matrix as supported."""

import argparse
import json
from pathlib import Path

import yaml

from dify_preflight.catalog.load import CatalogPolicy, CatalogValidationError, load_catalog


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, required=True)
    args = parser.parse_args()
    try:
        policy = _policy(args.catalog)
        catalog = load_catalog(args.catalog, policy)
        _require_fixed_anchor(catalog.rules, _source_records(args.catalog))
    except CatalogValidationError as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 1
    print(json.dumps({"ok": True, "edge_count": len(catalog.edges), "rule_count": len(catalog.rules), "catalog_digest": catalog.digest, "catalog_trust": catalog.trust, "supported_edges_claimed": bool(catalog.edges)}))
    return 0


def _policy(catalog_path: Path) -> CatalogPolicy:
    manifest_path = catalog_path.parent / "approval-manifest.yaml"
    if not manifest_path.is_file():
        return CatalogPolicy(root=catalog_path.parent)
    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or not isinstance(manifest.get("approved_sources"), dict) or not isinstance(manifest.get("approval_hashes"), dict):
            raise CatalogValidationError("approval_manifest")
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise CatalogValidationError("approval_manifest") from error
    return CatalogPolicy(
        root=catalog_path.parent,
        approved_sources=manifest["approved_sources"],
        approval_hashes=manifest["approval_hashes"],
        trust="owner_approved_local",
    )


def _source_records(catalog_path: Path) -> dict[str, dict[str, object]]:
    manifest_path = catalog_path.parent / "approval-manifest.yaml"
    if not manifest_path.is_file():
        return {}
    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        records = manifest.get("source_records") if isinstance(manifest, dict) else None
        if not isinstance(records, dict) or not all(isinstance(key, str) and isinstance(value, dict) for key, value in records.items()):
            raise CatalogValidationError("approval_manifest")
        return records
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise CatalogValidationError("approval_manifest") from error


def _require_fixed_anchor(rules: tuple[dict[str, object], ...], records: dict[str, dict[str, object]]) -> None:
    for rule in rules:
        refs = rule.get("evidence_refs", [])
        if not any(records.get(str(ref), {}).get("classification") == "official_fixed" for ref in refs):
            raise CatalogValidationError("source_not_fixed")


if __name__ == "__main__":
    raise SystemExit(main())
