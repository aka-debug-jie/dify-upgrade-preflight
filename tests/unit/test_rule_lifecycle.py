from dify_preflight.catalog.load import Catalog
from dify_preflight.domain import DeploymentSnapshot, Fact, FactOrigin, FactStatus, UpgradeRequest
from dify_preflight.engine.evaluate import evaluate


def _snapshot(ok: object = False) -> DeploymentSnapshot:
    return DeploymentSnapshot("1.0", "deployment_snapshot", False, "S", {"mode": "compose_declared", "compose_version": "2.33"}, {
        "dify.declared_version": Fact(FactStatus.KNOWN, "1.0.0", FactOrigin.DECLARED, "test", None),
        "component.kind": Fact(FactStatus.KNOWN, "bundled", FactOrigin.DECLARED, "test", None),
        "condition.ok": Fact(FactStatus.KNOWN if ok is not None else FactStatus.UNKNOWN, ok, FactOrigin.DECLARED, "test", None if ok is not None else "missing"),
    }, {}, {}, ())


def _catalog(*, source="1.0.0", target="1.0.1", supersedes=()) -> Catalog:
    edge = {"id": "EDGE-1", "source_version": source, "target_version": target, "required_facts": ["component.kind", "condition.ok"], "rule_ids": ["OLD", "NEW"], "scope": "static_upgrade_plan", "deployment_profile": "compose", "compose_version": "2.33"}
    base = {"status": "approved", "scope": "static_upgrade_plan", "support_edge_ids": ["EDGE-1"], "applies": {"fact": "component.kind", "op": "eq", "value": "bundled"}, "assertion": {"fact": "condition.ok", "op": "eq", "value": True}, "severity": "blocker", "evidence_refs": ["SRC"], "remediation": {"phase": "manual_review"}}
    return Catalog((edge,), ({**base, "id": "OLD", "revision": 1, "supersedes": []}, {**base, "id": "NEW", "revision": 2, "supersedes": list(supersedes)}), "digest", "owner_approved_local")


def test_exact_edge_no_transitive_path_and_unknown_remains_incomplete() -> None:
    report = evaluate(_snapshot(None), UpgradeRequest("1.0.0", "1.0.2"), _catalog())
    assert report["verdict"] == "UNSUPPORTED"
    report = evaluate(_snapshot(None), UpgradeRequest("1.0.0", "1.0.1"), _catalog())
    assert report["verdict"] == "INCOMPLETE"
    assert report["coverage"]["unknown_required_rules"] == ["OLD", "NEW"]


def test_supersedes_only_with_identical_edge_scope() -> None:
    report = evaluate(_snapshot(False), UpgradeRequest("1.0.0", "1.0.1"), _catalog(supersedes=("OLD",)))
    assert [finding["rule_id"] for finding in report["findings"]] == ["NEW"]
    catalog = _catalog(supersedes=("OLD",))
    catalog = Catalog(({**catalog.edges[0], "target_version": "1.0.2"},), catalog.rules, catalog.digest, catalog.trust)
    report = evaluate(_snapshot(False), UpgradeRequest("1.0.0", "1.0.1"), catalog)
    assert report["verdict"] == "UNSUPPORTED"


def test_blocker_and_unknown_are_both_retained_and_digest_is_stable() -> None:
    report_a = evaluate(_snapshot(False), UpgradeRequest("1.0.0", "1.0.1"), _catalog())
    report_b = evaluate(_snapshot(False), UpgradeRequest("1.0.0", "1.0.1"), _catalog())
    assert report_a["verdict"] == "BLOCKED"
    assert report_a["decision_digest"] == report_b["decision_digest"]


def test_v01_v05_v06_verdict_coverage() -> None:
    catalog = _catalog()
    unknown = {**catalog.rules[1], "id": "UNKNOWN", "assertion": {"fact": "missing", "op": "eq", "value": True}}
    edge = {**catalog.edges[0], "rule_ids": ["OLD", "UNKNOWN"]}
    catalog = Catalog((edge,), (catalog.rules[0], unknown), catalog.digest, "owner_approved_local")
    blocked = evaluate(_snapshot(False), UpgradeRequest("1.0.0", "1.0.1"), catalog)
    assert blocked["verdict"] == "BLOCKED"
    assert {item["result"] for item in blocked["findings"]} == {"failed", "unknown"}

    passed = evaluate(_snapshot(True), UpgradeRequest("1.0.0", "1.0.1"), _catalog())
    assert passed["verdict"] == "NO_KNOWN_BLOCKERS"
    assert passed["coverage"]["excluded_checks"]

    prototype = _catalog()
    untrusted = Catalog(prototype.edges, prototype.rules, "digest", "untrusted")
    assert evaluate(_snapshot(True), UpgradeRequest("1.0.0", "1.0.1"), untrusted)["verdict"] == "INCOMPLETE"


def test_required_fact_and_declared_source_mismatch_are_incomplete() -> None:
    snapshot = _snapshot(True)
    snapshot = DeploymentSnapshot(snapshot.schema_version, snapshot.kind, snapshot.synthetic, snapshot.snapshot_id, snapshot.capture, {**snapshot.facts, "dify.declared_version": Fact(FactStatus.KNOWN, "9.9.9", FactOrigin.DECLARED, "test", None)}, {}, {}, ())
    assert evaluate(snapshot, UpgradeRequest("1.0.0", "1.0.1"), _catalog())["verdict"] == "INCOMPLETE"


def test_missing_edge_required_fact_cannot_be_hidden_by_passing_rule() -> None:
    catalog = _catalog()
    edge = {**catalog.edges[0], "required_facts": ["component.kind", "missing"]}
    rules = tuple({**rule, "assertion": {"fact": "component.kind", "op": "eq", "value": "bundled"}} for rule in catalog.rules)
    assert evaluate(_snapshot(True), UpgradeRequest("1.0.0", "1.0.1"), Catalog((edge,), rules, catalog.digest, catalog.trust))["verdict"] == "INCOMPLETE"


def test_unknown_catalog_trust_cannot_pass() -> None:
    prototype = _catalog()
    report = evaluate(_snapshot(True), UpgradeRequest("1.0.0", "1.0.1"), Catalog(prototype.edges, prototype.rules, "digest", "custom"))
    assert report["verdict"] == "INCOMPLETE"
    assert report["provenance"]["catalog_trust"] == "untrusted"


def test_narrower_rule_cannot_retire_old_rule() -> None:
    catalog = _catalog(supersedes=("OLD",))
    narrow = {**catalog.rules[1], "applies": {"fact": "component.kind", "op": "eq", "value": "external"}}
    catalog = Catalog(catalog.edges, (catalog.rules[0], narrow), catalog.digest, catalog.trust)
    report = evaluate(_snapshot(False), UpgradeRequest("1.0.0", "1.0.1"), catalog)
    assert [item["rule_id"] for item in report["findings"]] == ["OLD", "NEW"]
    assert report["verdict"] == "BLOCKED"
