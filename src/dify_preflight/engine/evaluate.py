"""Pure catalog evaluation over already-captured deployment snapshots."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

from dify_preflight.catalog.load import Catalog
from dify_preflight.domain import DecisionInput, DeploymentSnapshot, Fact, FactOrigin, FactStatus, TruthValue, UpgradeRequest
from dify_preflight.engine.expressions import evaluate_expression
from dify_preflight.engine.verdict import verdict_for


ATTESTED_FACTS = frozenset({
    "plugins.externally_installed",
    "plugins.cache_invalidation_available",
    "history.upgraded_from_before_1_15",
    "migration.legacy_model_types_completed",
    "vector.persisted_data",
    "vector.staged_upgrade_completed",
})


def build_fact_view(snapshot: DeploymentSnapshot, prefix: str = "") -> dict[str, Fact]:
    view: dict[str, Fact] = {}
    for key, fact in snapshot.facts.items():
        if fact.origin is FactOrigin.ATTESTED and key not in ATTESTED_FACTS:
            view[f"{prefix}{key}"] = Fact(FactStatus.UNKNOWN, None, fact.origin, fact.source_ref, "attestation_not_allowed_for_fact")
        else:
            view[f"{prefix}{key}"] = fact
    for key, value in snapshot.private_relations.items():
        view[f"{prefix}private.{key}"] = Fact(
            FactStatus.KNOWN if value is not None else FactStatus.UNKNOWN,
            value,
            FactOrigin.DERIVED,
            key,
            None if value is not None else "relation_unavailable",
        )
    return view


def evaluate(snapshot: DeploymentSnapshot, request: UpgradeRequest, catalog: Catalog) -> dict[str, object]:
    trusted = catalog.trust in {"bundled", "owner_approved_local", "synthetic"}
    matches = [
        edge for edge in catalog.edges
        if edge["source_version"] == request.source_version
        and edge["target_version"] == request.target_version
        and edge["scope"] == request.scope
    ]
    if len(matches) != 1:
        return _report(snapshot, request, catalog, [], None, DecisionInput(False, False, False, False, False))
    edge = matches[0]
    if edge.get("deployment_profile") != "compose":
        return _report(snapshot, request, catalog, [], edge, DecisionInput(False, False, False, True, False), ["deployment_profile"])

    rules = _active_rules([rule for rule in catalog.rules if rule["id"] in edge["rule_ids"] and edge["id"] in rule["support_edge_ids"]])
    facts = build_fact_view(snapshot)
    proposed_reason = _proposed_reason(request.proposed_snapshot, request.target_version, edge, rules)
    if request.proposed_snapshot is not None:
        proposed = build_fact_view(request.proposed_snapshot, "proposed.")
        if proposed_reason is not None:
            proposed = {
                key: Fact(FactStatus.UNKNOWN, None, fact.origin, fact.source_ref, proposed_reason)
                for key, fact in proposed.items()
            }
        facts.update(proposed)

    findings: list[dict[str, object]] = []
    unknown: list[str] = []
    failed_blocker = False
    has_warning = False
    for rule in rules:
        applies = evaluate_expression(rule["applies"], facts)
        assertion = evaluate_expression(rule["assertion"], facts) if applies is TruthValue.TRUE else None
        result = (
            "not_applicable" if applies is TruthValue.FALSE
            else "unknown" if applies is TruthValue.UNKNOWN or assertion is TruthValue.UNKNOWN
            else "failed" if assertion is TruthValue.FALSE
            else "passed"
        )
        if result == "unknown":
            unknown.append(str(rule["id"]))
        if result == "failed" and rule["severity"] == "blocker":
            failed_blocker = True
        if result == "failed" and rule["severity"] == "warning":
            has_warning = True
        refs = _fact_refs(rule)
        findings.append({
            "rule_id": rule["id"],
            "result": result,
            "severity": rule["severity"],
            "message": f"Rule {rule['id']} evaluated as {result}.",
            "fact_refs": refs,
            "fact_evidence": _fact_evidence(refs, facts),
            "evidence_refs": rule["evidence_refs"],
            "remediation_phase": rule["remediation"]["phase"],
        })
    required_unknown = (
        bool(unknown)
        or not trusted
        or _required_fact_missing(edge, facts)
        or _source_mismatch(snapshot, request)
        or _edge_identity_incomplete(snapshot, edge)
        or proposed_reason is not None
    )
    if proposed_reason is not None:
        unknown.append("proposed_snapshot")
    if not trusted:
        unknown.append("catalog_trust")
    return _report(
        snapshot,
        request,
        catalog,
        findings,
        edge,
        DecisionInput(False, True, failed_blocker, required_unknown, has_warning),
        unknown,
    )


def _active_rules(rules: list[dict[str, object]]) -> list[dict[str, object]]:
    by_id = {str(rule["id"]): rule for rule in rules}
    superseded = {
        str(old)
        for rule in rules
        for old in rule["supersedes"]
        if set(rule["support_edge_ids"]) == set(by_id[str(old)]["support_edge_ids"])
        and _canonical(rule["applies"]) == _canonical(by_id[str(old)]["applies"])
    }
    return [rule for rule in rules if rule["id"] not in superseded]


def _proposed_reason(
    proposed: DeploymentSnapshot | None,
    target: str,
    edge: Mapping[str, object],
    rules: list[dict[str, object]],
) -> str | None:
    needs_proposed = any(name.startswith("proposed.") for name in edge["required_facts"])
    needs_proposed = needs_proposed or any(name.startswith("proposed.") for rule in rules for name in _fact_refs(rule))
    if not needs_proposed:
        return None
    if proposed is None:
        return "proposed_snapshot_missing"
    declared = proposed.facts.get("dify.declared_version")
    if (
        proposed.capture.get("mode") != "compose_declared"
        or proposed.capture.get("compose_version") != edge.get("compose_version")
        or declared is None
        or declared.status is not FactStatus.KNOWN
        or declared.origin is FactOrigin.ATTESTED
        or declared.value != target
    ):
        return "proposed_snapshot_identity_invalid"
    return None


def _required_fact_missing(edge: Mapping[str, object], facts: Mapping[str, Fact]) -> bool:
    return any(name not in facts or facts[name].status is not FactStatus.KNOWN for name in edge["required_facts"])


def _source_mismatch(snapshot: DeploymentSnapshot, request: UpgradeRequest) -> bool:
    declared = snapshot.facts.get("dify.declared_version")
    return (
        declared is None
        or declared.status is not FactStatus.KNOWN
        or declared.origin is not FactOrigin.DECLARED
        or declared.value != request.source_version
    )


def _edge_identity_incomplete(snapshot: DeploymentSnapshot, edge: Mapping[str, object]) -> bool:
    return snapshot.capture.get("mode") != "compose_declared" or snapshot.capture.get("compose_version") != edge.get("compose_version")


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fact_refs(rule: Mapping[str, object]) -> list[str]:
    def walk(expr: object) -> list[str]:
        if not isinstance(expr, Mapping):
            return []
        if "fact" in expr:
            return [str(expr["fact"])]
        children = expr.get("all") or expr.get("any") or [expr.get("not")]
        return [item for child in children for item in walk(child)]
    return sorted(set(walk(rule["applies"]) + walk(rule["assertion"])))


def _fact_evidence(refs: list[str], facts: Mapping[str, Fact]) -> list[dict[str, str]]:
    return [
        {
            "fact": ref,
            "origin": facts[ref].origin.value if ref in facts else "unknown",
            "source_ref": facts[ref].source_ref if ref in facts else "missing",
        }
        for ref in refs
    ]


def _report(
    snapshot: DeploymentSnapshot,
    request: UpgradeRequest,
    catalog: Catalog,
    findings: list[dict[str, object]],
    edge: Mapping[str, object] | None,
    decision: DecisionInput,
    unknown: list[str] | None = None,
) -> dict[str, object]:
    trust = catalog.trust if catalog.trust in {"bundled", "owner_approved_local", "untrusted", "synthetic"} else "untrusted"
    report: dict[str, object] = {
        "schema_version": "1.0",
        "synthetic": snapshot.synthetic,
        "scope": request.scope,
        "source_version": request.source_version,
        "target_version": request.target_version,
        "verdict": verdict_for(decision).value,
        "findings": findings,
        "changes": [],
        "coverage": {
            "support_edge_id": edge["id"] if edge else None,
            "required_rule_count": len(edge["rule_ids"]) if edge else 0,
            "evaluated_rule_count": len(findings),
            "unknown_required_rules": list(unknown or []),
            "excluded_checks": ["running_images", "database_state", "backup_restore_validity"],
        },
        "provenance": {
            "catalog_digest": catalog.digest,
            "snapshot_digest": _snapshot_digest(snapshot),
            "proposed_snapshot_digest": _snapshot_digest(request.proposed_snapshot) if request.proposed_snapshot else None,
            "tool_version": "0.0.0",
            "canonicalization_version": "1",
            "catalog_trust": trust,
        },
    }
    report["decision_digest"] = _digest(report)
    return report


def _snapshot_digest(snapshot: DeploymentSnapshot | None) -> str:
    if snapshot is None:
        return ""
    value = snapshot.to_dict()
    value.pop("snapshot_id")
    value.pop("capture")
    return _digest(value)


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
