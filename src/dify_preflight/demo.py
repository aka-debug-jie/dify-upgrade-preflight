import copy
import hashlib
import json
from collections.abc import Mapping
from importlib.resources import files
from typing import Any

import yaml

from dify_preflight.domain import DecisionInput, Fact, FactOrigin, FactStatus, Report, TruthValue
from dify_preflight.engine.expressions import evaluate_expression
from dify_preflight.engine.verdict import exit_code_for, verdict_for


def load_demo(case: str) -> tuple[Report, int]:
    snapshot = json.loads(_data("synthetic_snapshot.json"))
    rule = yaml.safe_load(_data("synthetic_rule.yaml"))
    expected = json.loads(_data("synthetic_report.json"))
    _apply_case(snapshot, case)
    report = evaluate_demo(snapshot, rule, expected["provenance"])
    return report, exit_code_for(verdict_for(_decision_for(report)))


def evaluate_demo(snapshot: Mapping[str, Any], rule: Mapping[str, Any], provenance: Mapping[str, Any]) -> Report:
    facts = {
        name: Fact(
            FactStatus(item["status"]), item["value"], FactOrigin(item["origin"]), item["source_ref"], item["reason"]
        )
        for name, item in snapshot["facts"].items()
    }
    applies = evaluate_expression(rule["applies"], facts)
    assertion = evaluate_expression(rule["assertion"], facts) if applies is TruthValue.TRUE else None
    result, message, severity = _finding_for(applies, assertion, rule["severity"])
    decision = DecisionInput(
        fatal_error=False,
        supported=True,
        failed_blocker=applies is TruthValue.TRUE and assertion is TruthValue.FALSE,
        required_unknown=applies is TruthValue.UNKNOWN or assertion is TruthValue.UNKNOWN,
        has_warning=False,
    )
    verdict = verdict_for(decision)
    finding = {
        "rule_id": rule["id"],
        "result": result,
        "severity": severity,
        "message": message,
        "fact_refs": ["vector.ownership", "demo.condition_resolved"],
        "fact_evidence": [
            {
                "fact": name,
                "origin": facts[name].origin.value,
                "source_ref": facts[name].source_ref,
            }
            for name in ("vector.ownership", "demo.condition_resolved")
        ],
        "evidence_refs": rule["evidence_refs"],
        "remediation_phase": rule["remediation"]["phase"],
    }
    report: Report = {
        "schema_version": "1.0",
        "synthetic": True,
        "scope": "static_upgrade_plan",
        "source_version": snapshot["facts"]["dify.declared_version"]["value"],
        "target_version": "0.0.2",
        "verdict": verdict.value,
        "findings": [finding],
        "changes": [],
        "coverage": {
            "support_edge_id": rule["support_edge_ids"][0],
            "required_rule_count": 1,
            "evaluated_rule_count": 1,
            "unknown_required_rules": [rule["id"]] if decision.required_unknown else [],
            "excluded_checks": ["running_images", "database_state", "backup_restore_validity"],
        },
        "provenance": {
            **provenance,
            "snapshot_digest": _snapshot_digest(snapshot),
        },
    }
    report["decision_digest"] = _digest(report)
    return report


def _data(name: str) -> str:
    return (files("dify_preflight") / "data" / name).read_text(encoding="utf-8")


def _apply_case(snapshot: dict[str, Any], case: str) -> None:
    if case == "blocked":
        return
    if case == "resolved":
        snapshot["facts"]["demo.condition_resolved"]["value"] = True
        return
    if case == "unknown":
        snapshot["facts"]["demo.condition_resolved"].update({"status": "unknown", "value": None, "reason": "Synthetic scenario omits this fact"})
        return
    if case == "external":
        snapshot["facts"]["vector.ownership"]["value"] = "external"
        return
    raise ValueError(f"unknown demo case: {case}")


def _finding_for(applies: TruthValue, assertion: TruthValue | None, severity: str) -> tuple[str, str, str]:
    if applies is TruthValue.FALSE:
        return "not_applicable", "DEMO: synthetic bundled-only prerequisite does not apply to an external component.", "info"
    if applies is TruthValue.UNKNOWN or assertion is TruthValue.UNKNOWN:
        return "unknown", "DEMO: a synthetic prerequisite cannot be evaluated because a required fact is unknown.", severity
    if assertion is TruthValue.FALSE:
        return "failed", "DEMO: a synthetic prerequisite is unresolved. This is not a Dify upgrade finding.", severity
    return "passed", "DEMO: a synthetic prerequisite is resolved. This is not a Dify upgrade finding.", severity


def _decision_for(report: Mapping[str, Any]) -> DecisionInput:
    return DecisionInput(False, True, report["verdict"] == "BLOCKED", report["verdict"] == "INCOMPLETE", False)


def _snapshot_digest(snapshot: Mapping[str, Any]) -> str:
    value = {key: copy.deepcopy(item) for key, item in snapshot.items() if key not in {"snapshot_id", "capture"}}
    return _digest(value)


def _digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
