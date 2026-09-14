from pathlib import Path

import yaml

from dify_preflight.catalog.load import Catalog
from dify_preflight.domain import DeploymentSnapshot, Fact, FactOrigin, FactStatus, TruthValue, UpgradeRequest
from dify_preflight.engine.evaluate import build_fact_view, evaluate
from dify_preflight.engine.expressions import evaluate_expression


ROOT = Path(__file__).resolve().parents[2]


def _facts(**values: object) -> dict[str, Fact]:
    return {
        name: Fact(FactStatus.KNOWN, value, FactOrigin.DECLARED, "test", None)
        for name, value in values.items()
    }


def test_worker_candidate_is_candidate_only_and_keeps_old_edge_history() -> None:
    active = yaml.safe_load((ROOT / "catalog/candidates/P05-active-promotion-set.yaml").read_text(encoding="utf-8"))
    worker = yaml.safe_load((ROOT / "catalog/candidates/P05-worker-queue-candidate.yaml").read_text(encoding="utf-8"))

    assert worker["status"] == "owner_scoped_candidate"
    assert worker["candidate_edge"]["id"] == "P05-EDGE-WORKER-1131-1132"
    assert worker["candidate_edge"]["approval_ref"] is None
    assert "P05-EDGE-WORKER-1131-1132" in active["active_candidate_edge_ids"]
    assert "P05-R07" in active["active_candidate_root_ids"]
    assert active["historical_candidate_edge_ids"] == ["P05-EDGE-B"]
    assert active["historical_candidate_root_ids"] == ["P05-R06"]


def test_worker_synthetic_sets_have_the_approved_shape_without_case_oracles() -> None:
    development = yaml.safe_load((ROOT / "tests/fixtures/candidate_semantics/P05-worker-queue-development.yaml").read_text(encoding="utf-8"))
    heldout = yaml.safe_load((ROOT / "tests/fixtures/candidate_semantics/P05-worker-queue-heldout.yaml").read_text(encoding="utf-8"))

    assert development["status"] == "semantic_implementation_fixture_not_owner_adjudication"
    assert len(development["cases"]) == 8
    assert heldout["status"] == "semantic_implementation_fixture_not_owner_adjudication"
    assert heldout["oracle"] == "absent_pending_owner_adjudication"
    assert len(heldout["cases"]) == 3
    assert all("expected" not in case for case in [*development["cases"], *heldout["cases"]])


def test_worker_queue_semantics_requires_complete_official_custom_target_topology() -> None:
    value = yaml.safe_load((ROOT / "catalog/candidates/P05-worker-queue-semantics.yaml").read_text(encoding="utf-8"))
    rule = value["rule"]
    facts = _facts(
        **{
            "proposed.worker.topology_complete": True,
            "proposed.worker.official_entrypoint": True,
            "proposed.worker.custom_queue_override_present": True,
            "proposed.worker.workflow_queue_covered": False,
            "proposed.api_token_last_used_update_enabled": False,
            "proposed.worker.api_token_queue_covered": False,
        }
    )
    assert rule["severity"] == "warning"
    assert rule["phase"] == "before_upgrade"
    assert evaluate_expression(rule["applies"], facts) is TruthValue.TRUE
    assert evaluate_expression(rule["assertion"], facts) is TruthValue.FALSE


def test_worker_queue_semantics_requires_api_token_only_when_feature_enabled() -> None:
    value = yaml.safe_load((ROOT / "catalog/candidates/P05-worker-queue-semantics.yaml").read_text(encoding="utf-8"))
    rule = value["rule"]
    facts = _facts(
        **{
            "proposed.worker.topology_complete": True,
            "proposed.worker.official_entrypoint": True,
            "proposed.worker.custom_queue_override_present": True,
            "proposed.worker.workflow_queue_covered": True,
            "proposed.api_token_last_used_update_enabled": True,
            "proposed.worker.api_token_queue_covered": False,
        }
    )
    assert evaluate_expression(rule["assertion"], facts) is TruthValue.FALSE


def test_missing_topology_or_custom_entrypoint_is_unknown_and_attestation_is_allowlisted() -> None:
    value = yaml.safe_load((ROOT / "catalog/candidates/P05-worker-queue-semantics.yaml").read_text(encoding="utf-8"))
    rule = value["rule"]
    snapshot_facts = {
        "worker.topology_complete": Fact(FactStatus.KNOWN, True, FactOrigin.ATTESTED, "test", None),
        "worker.official_entrypoint": Fact(FactStatus.KNOWN, False, FactOrigin.ATTESTED, "test", None),
        "worker.custom_queue_override_present": Fact(FactStatus.KNOWN, True, FactOrigin.DERIVED, "test", None),
    }
    view = build_fact_view(type("Snapshot", (), {"facts": snapshot_facts, "private_relations": {}})(), "proposed.")
    assert view["proposed.worker.official_entrypoint"].status is FactStatus.UNKNOWN
    assert evaluate_expression(rule["applies"], view) is TruthValue.UNKNOWN


def test_custom_entrypoint_returns_incomplete_in_candidate_evaluation() -> None:
    semantics = yaml.safe_load((ROOT / "catalog/candidates/P05-worker-queue-semantics.yaml").read_text(encoding="utf-8"))["rule"]
    rule = {
        **semantics,
        "support_edge_ids": ["P05-EDGE-WORKER-1131-1132"],
        "evidence_refs": ["P00.S002"],
        "remediation": {"phase": "before_upgrade"},
        "supersedes": [],
    }
    edge = {
        "id": "P05-EDGE-WORKER-1131-1132",
        "source_version": "1.13.1",
        "target_version": "1.13.2",
        "deployment_profile": "compose",
        "compose_version": "2.33",
        "scope": "static_upgrade_plan",
        "required_facts": ["proposed.worker.topology_complete", "proposed.worker.official_entrypoint"],
        "rule_ids": ["P05-R07"],
    }
    current = DeploymentSnapshot("1.0", "deployment_snapshot", True, "b", {"mode": "compose_declared", "compose_version": "2.33"}, {"dify.declared_version": Fact(FactStatus.KNOWN, "1.13.1", FactOrigin.DECLARED, "test", None)}, {}, {}, ())
    proposed = DeploymentSnapshot("1.0", "deployment_snapshot", True, "d", {"mode": "compose_declared", "compose_version": "2.33"}, {
        "dify.declared_version": Fact(FactStatus.KNOWN, "1.13.2", FactOrigin.DECLARED, "test", None),
        "worker.topology_complete": Fact(FactStatus.KNOWN, True, FactOrigin.ATTESTED, "test", None),
        "worker.official_entrypoint": Fact(FactStatus.KNOWN, False, FactOrigin.ATTESTED, "test", None),
        "worker.custom_queue_override_present": Fact(FactStatus.KNOWN, True, FactOrigin.DERIVED, "test", None),
        "worker.workflow_queue_covered": Fact(FactStatus.KNOWN, True, FactOrigin.DERIVED, "test", None),
        "api_token_last_used_update_enabled": Fact(FactStatus.KNOWN, False, FactOrigin.DECLARED, "test", None),
        "worker.api_token_queue_covered": Fact(FactStatus.KNOWN, False, FactOrigin.DERIVED, "test", None),
    }, {}, {}, ())
    report = evaluate(current, UpgradeRequest("1.13.1", "1.13.2", proposed_snapshot=proposed), Catalog((edge,), (rule,), "synthetic", "synthetic"))
    assert report["findings"][0]["result"] == "unknown"
    assert report["verdict"] == "INCOMPLETE"
