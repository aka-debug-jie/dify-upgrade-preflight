import hashlib
from pathlib import Path

import pytest
import yaml

from dify_preflight.catalog.load import CatalogPolicy, CatalogValidationError, load_catalog


def _write_catalog(tmp_path: Path, *, rule_changes: dict | None = None) -> tuple[Path, CatalogPolicy]:
    root = tmp_path / "catalog"
    approved = root / "approved"
    approved.mkdir(parents=True)
    rule = {
        "schema_version": "1.0", "id": "RULE-1", "revision": 1, "synthetic": False,
        "status": "approved", "title": "bounded rule", "scope": "static_upgrade_plan",
        "support_edge_ids": ["EDGE-1"],
        "applies": {"fact": "component.kind", "op": "eq", "value": "bundled"},
        "assertion": {"fact": "condition.ok", "op": "eq", "value": True},
        "severity": "blocker", "evidence_refs": ["SRC-1"], "review_ref": "APR-RULE-1",
        "supersedes": [],
        "remediation": {"phase": "manual_review", "summary": "Review manually", "docs_refs": ["SRC-1"], "executable": False},
    }
    if rule_changes:
        rule.update(rule_changes)
    rule_path = approved / "rule-1.yaml"
    rule_path.write_text(yaml.safe_dump(rule, sort_keys=False))
    matrix = {
        "schema_version": "1.0", "catalog_version": "test", "approved_edges": [{
            "id": "EDGE-1", "source_version": "1.0.0", "target_version": "1.0.1",
            "source_commit": "a" * 40, "target_commit": "b" * 40, "deployment_profile": "compose",
            "compose_version": "2.33", "scope": "static_upgrade_plan", "required_facts": ["component.kind", "condition.ok"],
            "rule_ids": ["RULE-1"], "case_ids": ["CASE-1"], "approval_ref": "APR-EDGE-1",
        }],
    }
    matrix_path = root / "support-matrix.yaml"
    matrix_path.write_text(yaml.safe_dump(matrix, sort_keys=False))
    policy = CatalogPolicy(
        root=root, approved_sources={"SRC-1": "1" * 64},
        approval_hashes={"APR-RULE-1": {"approved/rule-1.yaml": hashlib.sha256(rule_path.read_bytes()).hexdigest(), "sources/SRC-1": "1" * 64}, "APR-EDGE-1": {"support-matrix.yaml": hashlib.sha256(matrix_path.read_bytes()).hexdigest()}},
        trust="owner_approved_local",
    )
    return matrix_path, policy


def test_catalog_requires_exact_approval_hash_and_fixed_source(tmp_path: Path) -> None:
    matrix, policy = _write_catalog(tmp_path)
    catalog = load_catalog(matrix, policy)
    assert catalog.trust == "owner_approved_local"
    assert catalog.rules[0]["id"] == "RULE-1"

    policy = CatalogPolicy(root=policy.root, approved_sources={}, approval_hashes=policy.approval_hashes, trust=policy.trust)
    with pytest.raises(CatalogValidationError, match="source_not_fixed"):
        load_catalog(matrix, policy)
    with pytest.raises(CatalogValidationError, match="source_not_fixed"):
        load_catalog(matrix, CatalogPolicy(root=matrix.parent, approved_sources=frozenset({"SRC-1"}), approval_hashes=policy.approval_hashes, trust=policy.trust))  # type: ignore[arg-type]


@pytest.mark.parametrize("change, expected", [
    ({"id": "RULE-1"}, "duplicate_rule_id"),
    ({"schema_version": "9.9"}, "schema_version"),
    ({"applies": {"script": "ignored"}}, "expression"),
    ({"applies": {"all": []}}, "empty_boolean"),
    ({"evidence_refs": []}, "source_missing"),
])
def test_untrusted_catalog_shapes_are_controlled_errors(tmp_path: Path, change: dict, expected: str) -> None:
    matrix, policy = _write_catalog(tmp_path, rule_changes=change)
    if expected == "duplicate_rule_id":
        rule = (matrix.parent / "approved/rule-1.yaml").read_text()
        (matrix.parent / "approved/rule-2.yaml").write_text(rule)
    with pytest.raises(CatalogValidationError, match=expected):
        load_catalog(matrix, policy)


def test_catalog_does_not_follow_files_outside_root(tmp_path: Path) -> None:
    matrix, policy = _write_catalog(tmp_path)
    outside = tmp_path / "outside.yaml"
    outside.write_text((matrix.parent / "approved/rule-1.yaml").read_text())
    (matrix.parent / "approved/rule-1.yaml").unlink()
    (matrix.parent / "approved/rule-1.yaml").symlink_to(outside)
    with pytest.raises(CatalogValidationError, match="path"):
        load_catalog(matrix, policy)


def test_catalog_content_change_invalidates_exact_approval_hash(tmp_path: Path) -> None:
    matrix, policy = _write_catalog(tmp_path)
    rule_path = matrix.parent / "approved/rule-1.yaml"
    rule_path.write_text(rule_path.read_text() + "\n")
    with pytest.raises(CatalogValidationError, match="approval_hash"):
        load_catalog(matrix, policy)


def test_duplicate_yaml_key_is_rejected_before_trust_checks(tmp_path: Path) -> None:
    matrix, policy = _write_catalog(tmp_path)
    rule_path = matrix.parent / "approved/rule-1.yaml"
    rule_path.write_text(rule_path.read_text() + "\nid: OTHER\n")
    with pytest.raises(CatalogValidationError, match="duplicate_key"):
        load_catalog(matrix, policy)


def test_catalog_rejects_asymmetric_edge_membership_and_invalid_trust(tmp_path: Path) -> None:
    matrix, policy = _write_catalog(tmp_path)
    rule_path = matrix.parent / "approved/rule-1.yaml"
    rule = yaml.safe_load(rule_path.read_text())
    rule["support_edge_ids"] = ["EDGE-2"]
    rule_path.write_text(yaml.safe_dump(rule, sort_keys=False))
    with pytest.raises(CatalogValidationError, match="edge_rule_scope"):
        load_catalog(matrix, policy)
    with pytest.raises(CatalogValidationError, match="catalog_trust"):
        load_catalog(matrix, CatalogPolicy(root=policy.root, trust="custom"))


def test_non_scalar_yaml_key_is_a_controlled_catalog_error(tmp_path: Path) -> None:
    matrix, policy = _write_catalog(tmp_path)
    (matrix.parent / "approved/rule-1.yaml").write_text("? [bad]\n: value\n")
    with pytest.raises(CatalogValidationError, match="parse"):
        load_catalog(matrix, policy)


def test_total_expression_nodes_and_source_digest_are_bounded(tmp_path: Path) -> None:
    matrix, policy = _write_catalog(tmp_path)
    rule_path = matrix.parent / "approved/rule-1.yaml"
    rule = yaml.safe_load(rule_path.read_text())
    rule["applies"] = {"all": [{"fact": f"f{i}", "op": "eq", "value": True} for i in range(63)]}
    rule_path.write_text(yaml.safe_dump(rule, sort_keys=False))
    with pytest.raises(CatalogValidationError, match="expression_nodes"):
        load_catalog(matrix, policy)
    clean_matrix, clean_policy = _write_catalog(tmp_path / "source")
    with pytest.raises(CatalogValidationError, match="source_not_fixed"):
        load_catalog(clean_matrix, CatalogPolicy(root=clean_policy.root, approved_sources={"SRC-1": "not-a-digest"}, approval_hashes=clean_policy.approval_hashes, trust=clean_policy.trust))


def test_catalog_digest_binds_referenced_source_digests_and_rejects_duplicate_exact_edges(tmp_path: Path) -> None:
    matrix, policy = _write_catalog(tmp_path)
    first = load_catalog(matrix, policy)
    with pytest.raises(CatalogValidationError, match="source_approval"):
        load_catalog(
            matrix,
            CatalogPolicy(
                root=policy.root,
                approved_sources={"SRC-1": "2" * 64},
                approval_hashes=policy.approval_hashes,
                trust=policy.trust,
            ),
        )
    approved = CatalogPolicy(
        root=policy.root,
        approved_sources={"SRC-1": "2" * 64},
        approval_hashes={"APR-RULE-1": {"approved/rule-1.yaml": hashlib.sha256((policy.root / "approved/rule-1.yaml").read_bytes()).hexdigest(), "sources/SRC-1": "2" * 64}, "APR-EDGE-1": policy.approval_hashes["APR-EDGE-1"]},
        trust=policy.trust,
    )
    changed = load_catalog(matrix, approved)
    assert first.digest != changed.digest
    assert first.source_digests == {"SRC-1": "1" * 64}

    value = yaml.safe_load(matrix.read_text())
    duplicate = dict(value["approved_edges"][0])
    duplicate["id"] = "EDGE-2"
    value["approved_edges"].append(duplicate)
    matrix.write_text(yaml.safe_dump(value, sort_keys=False))
    with pytest.raises(CatalogValidationError, match="edge_scope"):
        load_catalog(matrix, policy)


@pytest.mark.parametrize("value", ["2026-09-13", "!!binary aGVsbG8=", ".nan", ".inf"])
def test_non_json_expression_values_are_controlled_errors(tmp_path: Path, value: str) -> None:
    matrix, policy = _write_catalog(tmp_path)
    rule_path = matrix.parent / "approved/rule-1.yaml"
    text = rule_path.read_text().replace("value: bundled", f"value: {value}")
    rule_path.write_text(text)
    with pytest.raises(CatalogValidationError, match="expression"):
        load_catalog(matrix, policy)
