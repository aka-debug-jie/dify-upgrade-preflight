import hashlib
import json
from pathlib import Path

import yaml

from dify_preflight.catalog.load import CatalogPolicy, load_catalog


ROOT = Path(__file__).resolve().parents[2]


def test_approved_p05_catalog_loads_with_digest_bound_owner_policy() -> None:
    manifest = yaml.safe_load((ROOT / "catalog/approval-manifest.yaml").read_text(encoding="utf-8"))
    policy = CatalogPolicy(
        root=ROOT / "catalog",
        approved_sources=manifest["approved_sources"],
        approval_hashes=manifest["approval_hashes"],
        trust="owner_approved_local",
    )
    catalog = load_catalog(ROOT / "catalog/support-matrix.yaml", policy)
    assert {edge["id"] for edge in catalog.edges} == {"P05-EDGE-A", "P05-EDGE-WORKER-1131-1132"}
    assert {rule["id"] for rule in catalog.rules} == {"P05-R01", "P05-R02", "P05-R03", "P05-R04", "P05-R05", "P05-R07"}

    revision = json.loads((ROOT / "artifacts/P05/20260914T083000Z/R05_REVISED_PROMOTION_OBJECTS.json").read_text(encoding="utf-8"))
    assert manifest["approved_object_digests"]["active_set"] == revision["active_set_object_sha256"]
    assert manifest["approved_object_digests"]["rules"]["P05-R05"] == revision["new_r05_sha256"]
    assert all(len(value) == 64 for value in manifest["approved_sources"].values())
    assert all(
        any(manifest["source_records"][ref]["classification"] == "official_fixed" for ref in rule["evidence_refs"])
        for rule in catalog.rules
    )
    assert hashlib.sha256((ROOT / "catalog/support-matrix.yaml").read_bytes()).hexdigest() == manifest["approval_hashes"][manifest["approval_ref"]]["support-matrix.yaml"]

    by_edge = {edge["id"]: edge for edge in catalog.edges}
    by_rule = {rule["id"]: rule for rule in catalog.rules}
    for edge_id, item in revision["edges"].items():
        edge = by_edge[edge_id]
        actual = {key: edge[key] for key in item["canonical_object"]}
        assert hashlib.sha256(json.dumps(actual, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest() == item["sha256"]
    for rule_id, item in revision["rules"].items():
        rule = by_rule[rule_id]
        actual = {
            key: (
                rule["support_edge_ids"][0] if key == "edge_id"
                else rule["remediation"]["phase"] if key == "phase"
                else rule[key]
            )
            for key in item["canonical_object"]
            if key != "required_facts"
        }
        expected = {key: value for key, value in item["canonical_object"].items() if key != "required_facts"}
        assert actual == expected
        assert manifest["approved_object_digests"]["rules"][rule_id] == item["sha256"]
