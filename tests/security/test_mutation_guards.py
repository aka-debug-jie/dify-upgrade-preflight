from dify_preflight.catalog.load import Catalog
from dify_preflight.domain import DeploymentSnapshot, Fact, FactOrigin, FactStatus, UpgradeRequest
from dify_preflight.engine.evaluate import evaluate


def _snapshot(value: object, status: FactStatus = FactStatus.KNOWN) -> DeploymentSnapshot:
    return DeploymentSnapshot(
        "1.0", "deployment_snapshot", True, "s",
        {"mode": "compose_declared", "compose_version": "2.33"},
        {"dify.declared_version": Fact(FactStatus.KNOWN, "1.0.0", FactOrigin.DECLARED, "test", None), "condition": Fact(status, value, FactOrigin.SYNTHETIC, "test", None)},
        {},
        {},
        (),
    )


def test_exact_version_mutation_cannot_match_a_neighbouring_edge() -> None:
    edge = {"id": "EDGE", "source_version": "1.0.0", "target_version": "1.0.1", "scope": "static_upgrade_plan", "deployment_profile": "compose", "compose_version": "2.33", "required_facts": ["dify.declared_version"], "rule_ids": []}
    assert evaluate(_snapshot(True), UpgradeRequest("1.0.1", "1.0.2"), Catalog((edge,), (), "synthetic", "synthetic"))["verdict"] == "UNSUPPORTED"


def test_unknown_mutation_cannot_become_a_pass() -> None:
    edge = {"id": "EDGE", "source_version": "1.0.0", "target_version": "1.0.1", "scope": "static_upgrade_plan", "deployment_profile": "compose", "compose_version": "2.33", "required_facts": ["dify.declared_version"], "rule_ids": ["RULE"]}
    rule = {"id": "RULE", "support_edge_ids": ["EDGE"], "supersedes": [], "applies": {"fact": "condition", "op": "eq", "value": True}, "assertion": {"fact": "condition", "op": "eq", "value": True}, "severity": "blocker", "evidence_refs": ["synthetic"], "remediation": {"phase": "manual_review", "summary": "synthetic"}}
    report = evaluate(_snapshot(None, FactStatus.UNKNOWN), UpgradeRequest("1.0.0", "1.0.1"), Catalog((edge,), (rule,), "synthetic", "synthetic"))
    assert report["verdict"] == "INCOMPLETE"
    assert report["findings"][0]["result"] == "unknown"
