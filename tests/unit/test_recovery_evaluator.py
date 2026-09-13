from dify_preflight.catalog.load import Catalog
from dify_preflight.domain import DeploymentSnapshot, Fact, FactOrigin, FactStatus, UpgradeRequest
from dify_preflight.engine.evaluate import evaluate


def _snapshot(version: str, *, mode: str = "compose_declared", wiring: bool = True, origin: FactOrigin = FactOrigin.DECLARED) -> DeploymentSnapshot:
    return DeploymentSnapshot(
        "1.0",
        "deployment_snapshot",
        False,
        version,
        {"mode": mode, "compose_version": "2.33"},
        {
            "dify.declared_version": Fact(FactStatus.KNOWN, version, origin, "test", None),
            "agent_auth.wiring_complete": Fact(FactStatus.KNOWN, wiring, FactOrigin.DECLARED, "test", None),
        },
        {},
        {},
        (),
    )


def _catalog() -> Catalog:
    edge = {
        "id": "RECOVERY",
        "source_version": "1.16.0",
        "target_version": "1.16.1",
        "required_facts": ["proposed.agent_auth.wiring_complete"],
        "rule_ids": ["RULE"],
        "scope": "static_upgrade_plan",
        "deployment_profile": "compose",
        "compose_version": "2.33",
    }
    rule = {
        "id": "RULE",
        "support_edge_ids": ["RECOVERY"],
        "applies": {"fact": "proposed.agent_auth.wiring_complete", "op": "eq", "value": True},
        "assertion": {"fact": "proposed.agent_auth.wiring_complete", "op": "eq", "value": True},
        "severity": "blocker",
        "evidence_refs": ["SRC"],
        "remediation": {"phase": "before_upgrade"},
        "supersedes": [],
    }
    return Catalog((edge,), (rule,), "digest", "owner_approved_local")


def test_proposed_snapshot_is_separate_and_required_for_proposed_rule() -> None:
    current = _snapshot("1.16.0", wiring=False)
    missing = evaluate(current, UpgradeRequest("1.16.0", "1.16.1"), _catalog())
    assert missing["verdict"] == "INCOMPLETE"
    assert "proposed_snapshot" in missing["coverage"]["unknown_required_rules"]

    report = evaluate(current, UpgradeRequest("1.16.0", "1.16.1", proposed_snapshot=_snapshot("1.16.1", wiring=True)), _catalog())
    assert report["verdict"] == "NO_KNOWN_BLOCKERS"
    assert report["provenance"]["proposed_snapshot_digest"]
    assert report["findings"][0]["fact_evidence"][0]["fact"].startswith("proposed.")


def test_proposed_snapshot_wrong_identity_and_attested_identity_cannot_pass() -> None:
    current = _snapshot("1.16.0")
    wrong = evaluate(current, UpgradeRequest("1.16.0", "1.16.1", proposed_snapshot=_snapshot("1.16.0")), _catalog())
    assert wrong["verdict"] == "INCOMPLETE"
    attested = evaluate(current, UpgradeRequest("1.16.0", "1.16.1", proposed_snapshot=_snapshot("1.16.1", origin=FactOrigin.ATTESTED)), _catalog())
    assert attested["verdict"] == "INCOMPLETE"
