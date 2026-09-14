#!/usr/bin/env python3
"""Run owner-adjudicated synthetic P05 facts through the production evaluator."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dify_preflight.catalog.load import Catalog  # noqa: E402
from dify_preflight.domain import (  # noqa: E402
    DeploymentSnapshot,
    Fact,
    FactOrigin,
    FactStatus,
    UpgradeRequest,
)
from dify_preflight.engine.evaluate import evaluate  # noqa: E402


DEVELOPMENT_FACTS = ROOT / "tests/fixtures/adjudicated/P05-development-facts.yaml"
DEVELOPMENT_ORACLE = ROOT / "tests/fixtures/adjudicated/P05-development-cases.yaml"
HELDOUT_INPUTS = ROOT / "tests/fixtures/heldout/P05-heldout-inputs.yaml"
HELDOUT_MANIFEST = ROOT / "tests/fixtures/heldout/P05-heldout-manifest.yaml"
HELDOUT_ORACLE = ROOT / "tests/fixtures/adjudicated/P05-heldout-oracle.yaml"
CANDIDATE_EDGES = ROOT / "catalog/candidates/P05-recovery-candidates.yaml"
CANDIDATE_RULES = ROOT / "catalog/candidates/P05-rule-semantics.yaml"


def _load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"invalid_fixture:{path.relative_to(ROOT)}")
    return value


def _fact(value: object, *, case_id: str, side: str, name: str) -> Fact:
    source_ref = f"synthetic_fixture:{case_id}:{side}:{name}"
    if not isinstance(value, dict):
        return Fact(FactStatus.KNOWN, value, FactOrigin.DECLARED, source_ref, None)
    status = FactStatus(str(value.get("status", "known")))
    origin = FactOrigin(str(value.get("origin", "declared")))
    fact_value = value.get("value") if status is FactStatus.KNOWN else None
    reason = value.get("reason")
    if status is FactStatus.KNOWN and "value" not in value:
        raise ValueError(f"known_fact_without_value:{case_id}:{side}:{name}")
    if status is not FactStatus.KNOWN and not isinstance(reason, str):
        raise ValueError(f"unknown_fact_without_reason:{case_id}:{side}:{name}")
    return Fact(status, fact_value, origin, source_ref, reason)


def _snapshot(
    case: dict[str, Any],
    *,
    side: str,
    version: str,
    capture: dict[str, object],
) -> DeploymentSnapshot:
    facts = {
        "dify.declared_version": Fact(
            FactStatus.KNOWN,
            version,
            FactOrigin.DECLARED,
            f"synthetic_fixture:{case['case_id']}:{side}:dify.declared_version",
            None,
        )
    }
    for name, value in case.get(f"{side}_facts", {}).items():
        facts[str(name)] = _fact(value, case_id=str(case["case_id"]), side=side, name=str(name))
    return DeploymentSnapshot(
        schema_version="1.0",
        kind="deployment_snapshot",
        synthetic=True,
        snapshot_id=f"synthetic-{case['case_id']}-{side}",
        capture=dict(capture),
        facts=facts,
        public_config={},
        private_relations=dict(case.get(f"{side}_private_relations", {})),
        gaps=(),
    )


def _catalog_for(
    case: dict[str, Any],
    edges_by_id: dict[str, dict[str, Any]],
    roots_by_id: dict[str, dict[str, Any]],
    rules_by_id: dict[str, dict[str, Any]],
) -> Catalog:
    edge_source = edges_by_id[str(case["candidate_edge_id"])]
    root = roots_by_id[str(case["root_cause_id"])]
    semantic = rules_by_id[str(case["root_cause_id"])]
    edge = {
        "id": edge_source["id"],
        "source_version": edge_source["source_version"],
        "target_version": edge_source["target_version"],
        "source_commit": edge_source["source_commit"],
        "target_commit": edge_source["target_commit"],
        "deployment_profile": "compose",
        "compose_version": "2.33",
        "scope": "static_upgrade_plan",
        "required_facts": list(root["required_facts"]),
        "rule_ids": [semantic["id"]],
        "case_ids": [case["case_id"]],
        "approval_ref": "synthetic-candidate-evaluation-only",
    }
    rule = {
        "id": semantic["id"],
        "revision": 1,
        "synthetic": True,
        "status": "candidate_evaluation_only",
        "title": root["title"],
        "scope": "static_upgrade_plan",
        "support_edge_ids": [edge["id"]],
        "applies": semantic["applies"],
        "assertion": semantic["assertion"],
        "severity": semantic["severity"],
        "evidence_refs": list(root["source_refs"]),
        "review_ref": semantic["approval_ref"] if "approval_ref" in semantic else "candidate",
        "supersedes": [],
        "remediation": {
            "phase": semantic["phase"],
            "summary": "Synthetic candidate evaluation only.",
            "docs_refs": list(root["source_refs"]),
            "executable": False,
        },
    }
    canonical = json.dumps({"edge": edge, "rule": rule}, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return Catalog((edge,), (rule,), digest, "synthetic")


def _actual(report: dict[str, object]) -> dict[str, str]:
    findings = report["findings"]
    if not isinstance(findings, list):
        raise ValueError("evaluator_findings_not_list")
    verdict = str(report["verdict"])
    if not findings:
        if verdict != "UNSUPPORTED":
            raise ValueError("missing_finding_for_supported_request")
        return {"result": "request_unsupported", "verdict_effect": "unsupported"}
    if len(findings) != 1:
        raise ValueError("case_catalog_did_not_isolate_one_rule")
    finding = findings[0]
    if not isinstance(finding, dict):
        raise ValueError("evaluator_finding_not_mapping")
    result = str(finding["result"])
    if result == "failed":
        effect = "blocked" if finding["severity"] == "blocker" else "warning"
    elif result == "unknown":
        effect = "incomplete"
    else:
        effect = "none"
    return {"result": result, "verdict_effect": effect}


def _request(case: dict[str, Any], edge: dict[str, Any]) -> tuple[str, str]:
    request = case.get("request", {})
    return (
        str(request.get("source_version", edge["source_version"])),
        str(request.get("target_version", edge["target_version"])),
    )


def _run_group(
    inputs: dict[str, Any],
    expected_by_id: dict[str, dict[str, str]],
    *,
    edges_by_id: dict[str, dict[str, Any]],
    roots_by_id: dict[str, dict[str, Any]],
    rules_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, object]]:
    capture = inputs["snapshot_defaults"]["capture"]
    results: list[dict[str, object]] = []
    for case in inputs["cases"]:
        case_id = str(case["case_id"])
        edge = edges_by_id[str(case["candidate_edge_id"])]
        source_version, target_version = _request(case, edge)
        current = _snapshot(case, side="b", version=source_version, capture=capture)
        proposed = _snapshot(case, side="d", version=target_version, capture=capture)
        report = evaluate(
            current,
            UpgradeRequest(source_version, target_version, proposed_snapshot=proposed),
            _catalog_for(case, edges_by_id, roots_by_id, rules_by_id),
        )
        actual = _actual(report)
        expected = expected_by_id[case_id]
        results.append({
            "case_id": case_id,
            "root_cause_id": case["root_cause_id"],
            "candidate_edge_id": case["candidate_edge_id"],
            "expected": expected,
            "actual": actual,
            "passed": actual == expected,
            "verdict": report["verdict"],
            "support_edge_id": report["coverage"]["support_edge_id"],
            "evaluated_rule_count": report["coverage"]["evaluated_rule_count"],
            "decision_digest": report["decision_digest"],
        })
    return results


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _oracle(value: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {str(item["case_id"]): dict(item["expected"]) for item in value["cases"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output_dir = args.output_dir
    if output_dir.exists():
        raise SystemExit("output_dir_already_exists")

    development_inputs = _load(DEVELOPMENT_FACTS)
    development_oracle = _load(DEVELOPMENT_ORACLE)
    heldout_inputs = _load(HELDOUT_INPUTS)
    heldout_manifest = _load(HELDOUT_MANIFEST)
    heldout_oracle = _load(HELDOUT_ORACLE)
    candidates = _load(CANDIDATE_EDGES)
    semantics = _load(CANDIDATE_RULES)

    if any("expected" in item for item in heldout_inputs["cases"]):
        raise SystemExit("heldout_input_contains_oracle")
    development_ids = {str(item["case_id"]) for item in development_inputs["cases"]}
    heldout_ids = {str(item["case_id"]) for item in heldout_inputs["cases"]}
    if len(development_ids) != 26 or len(heldout_ids) != 7 or development_ids & heldout_ids:
        raise SystemExit("fixture_partition_invalid")
    if heldout_ids != set(heldout_manifest["case_ids"]):
        raise SystemExit("heldout_manifest_mismatch")
    development_expected = _oracle(development_oracle)
    heldout_expected = _oracle(heldout_oracle)
    if set(development_expected) != development_ids or set(heldout_expected) != heldout_ids:
        raise SystemExit("oracle_input_id_mismatch")

    edges_by_id = {str(item["id"]): item for item in candidates["candidate_edges"]}
    roots_by_id = {str(item["id"]): item for item in candidates["root_causes"]}
    rules_by_id = {str(item["id"]): item for item in semantics["rules"]}
    development = _run_group(
        development_inputs,
        development_expected,
        edges_by_id=edges_by_id,
        roots_by_id=roots_by_id,
        rules_by_id=rules_by_id,
    )
    heldout = _run_group(
        heldout_inputs,
        heldout_expected,
        edges_by_id=edges_by_id,
        roots_by_id=roots_by_id,
        rules_by_id=rules_by_id,
    )
    all_results = development + heldout
    false_safe = sum(
        item["expected"]["verdict_effect"] == "blocked" and item["actual"]["verdict_effect"] != "blocked"
        for item in all_results
    )
    extra_blockers = sum(
        item["expected"]["verdict_effect"] != "blocked" and item["actual"]["verdict_effect"] == "blocked"
        for item in all_results
    )
    failed = [str(item["case_id"]) for item in all_results if not item["passed"]]

    output_dir.mkdir(parents=True)
    _write_json(output_dir / "DEVELOPMENT_EVALUATION.json", {"count": len(development), "results": development})
    _write_json(output_dir / "HELDOUT_EVALUATION.json", {"count": len(heldout), "results": heldout})
    input_paths = [
        DEVELOPMENT_FACTS,
        DEVELOPMENT_ORACLE,
        HELDOUT_INPUTS,
        HELDOUT_MANIFEST,
        HELDOUT_ORACLE,
        CANDIDATE_EDGES,
        CANDIDATE_RULES,
    ]
    manifest = {
        "schema_version": "1.0",
        "synthetic": True,
        "evaluator": "dify_preflight.engine.evaluate.evaluate",
        "catalog_trust": "synthetic",
        "candidate_only": True,
        "development_count": len(development),
        "heldout_count": len(heldout),
        "passed_count": len(all_results) - len(failed),
        "failed_case_ids": failed,
        "false_safe": false_safe,
        "extra_blockers": extra_blockers,
        "inputs": {path.relative_to(ROOT).as_posix(): _sha256(path) for path in input_paths},
    }
    _write_json(output_dir / "RUN_MANIFEST.json", manifest)
    validation = (
        "# P05 synthetic fixture evaluation\n\n"
        "This run evaluates candidate-only, synthetic B/D facts with "
        "`dify_preflight.engine.evaluate.evaluate`. It does not promote a rule or support edge.\n\n"
        f"- Development: {len(development) - sum(not item['passed'] for item in development)}/{len(development)} passed\n"
        f"- Heldout: {len(heldout) - sum(not item['passed'] for item in heldout)}/{len(heldout)} passed\n"
        f"- False-safe: {false_safe}\n"
        f"- Extra blockers: {extra_blockers}\n"
        f"- Failed case IDs: {failed}\n"
        "- Heldout oracle separation: input file contains no `expected` keys; oracle is under `tests/fixtures/adjudicated/`.\n"
        "- Production/approved catalog mutation: none.\n"
    )
    (output_dir / "VALIDATION.md").write_text(validation, encoding="utf-8")
    print(json.dumps(manifest, sort_keys=True))
    return 0 if not failed and false_safe == 0 and extra_blockers == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
