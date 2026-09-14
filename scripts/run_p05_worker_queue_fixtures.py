#!/usr/bin/env python3
"""Evaluate owner-adjudicated P05-R07 synthetic fixtures with the production evaluator."""

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
from dify_preflight.domain import DeploymentSnapshot, Fact, FactOrigin, FactStatus, UpgradeRequest  # noqa: E402
from dify_preflight.engine.evaluate import evaluate  # noqa: E402


DEVELOPMENT = ROOT / "tests/fixtures/adjudicated/P05-worker-queue-development-cases.yaml"
HELDOUT_INPUTS = ROOT / "tests/fixtures/heldout/P05-worker-queue-heldout-inputs.yaml"
HELDOUT_ORACLE = ROOT / "tests/fixtures/adjudicated/P05-worker-queue-heldout-oracle.yaml"
FACTS = ROOT / "tests/fixtures/candidate_semantics/P05-worker-queue-executable-facts.yaml"
CANDIDATE = ROOT / "catalog/candidates/P05-worker-queue-candidate.yaml"
SEMANTICS = ROOT / "catalog/candidates/P05-worker-queue-semantics.yaml"


def _load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"invalid_yaml:{path.relative_to(ROOT)}")
    return value


def _fact(value: dict[str, Any], case_id: str, name: str) -> Fact:
    status = FactStatus(str(value.get("status", "known")))
    origin = FactOrigin(str(value.get("origin", "declared")))
    if status is FactStatus.KNOWN:
        if "value" not in value:
            raise ValueError(f"known_fact_without_value:{case_id}:{name}")
        return Fact(status, value["value"], origin, f"synthetic:{case_id}:{name}", None)
    reason = value.get("reason")
    if not isinstance(reason, str):
        raise ValueError(f"unknown_fact_without_reason:{case_id}:{name}")
    return Fact(status, None, origin, f"synthetic:{case_id}:{name}", reason)


def _snapshot(case_id: str, version: str, facts: dict[str, Any], capture: dict[str, Any]) -> DeploymentSnapshot:
    snapshot_facts: dict[str, Fact] = {
        "dify.declared_version": Fact(FactStatus.KNOWN, version, FactOrigin.DECLARED, f"synthetic:{case_id}:version", None)
    }
    snapshot_facts.update({name: _fact(value, case_id, name) for name, value in facts.items()})
    return DeploymentSnapshot("1.0", "deployment_snapshot", True, f"synthetic-{case_id}-{version}", capture, snapshot_facts, {}, {}, ())


def _catalog(candidate: dict[str, Any], semantics: dict[str, Any]) -> Catalog:
    candidate_edge = candidate["candidate_edge"]
    root = candidate["root_cause"]
    rule_semantics = semantics["rule"]
    edge = {
        **candidate_edge,
        "compose_version": "2.33",
        "required_facts": root["required_facts"],
        "rule_ids": [root["id"]],
    }
    rule = {
        **rule_semantics,
        "revision": 1,
        "synthetic": True,
        "status": "candidate_evaluation_only",
        "title": root["title"],
        "scope": candidate_edge["scope"],
        "support_edge_ids": [candidate_edge["id"]],
        "evidence_refs": root["source_refs"],
        "review_ref": semantics["approval_ref"],
        "supersedes": [],
        "remediation": {"phase": rule_semantics["phase"], "summary": "Synthetic candidate evaluation only."},
    }
    digest = hashlib.sha256(json.dumps({"edge": edge, "rule": rule}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return Catalog((edge,), (rule,), digest, "synthetic")


def _actual(report: dict[str, Any]) -> dict[str, str]:
    findings = report["findings"]
    verdict = str(report["verdict"])
    if not findings:
        return {"result": "request_unsupported", "verdict_effect": "unsupported", "report_verdict": verdict}
    finding = findings[0]
    result = str(finding["result"])
    effect = "warning" if result == "failed" else "incomplete" if result == "unknown" else "none"
    return {"result": result, "verdict_effect": effect, "report_verdict": verdict}


def _run(cases: list[dict[str, Any]], expected: dict[str, dict[str, str]], facts_by_id: dict[str, dict[str, Any]], catalog: Catalog, capture: dict[str, Any], default_edge: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for case in cases:
        case_id = str(case["case_id"])
        request = case.get("request", {})
        source = str(request.get("source_version", default_edge["source_version"]))
        target = str(request.get("target_version", default_edge["target_version"]))
        proposed = _snapshot(case_id, target, facts_by_id[case_id]["d_facts"], capture)
        current = _snapshot(case_id, source, {}, capture)
        report = evaluate(current, UpgradeRequest(source, target, proposed_snapshot=proposed), catalog)
        actual = _actual(report)
        target_expected = expected[case_id]
        results.append({
            "case_id": case_id,
            "expected": target_expected,
            "actual": actual,
            "verdict": report["verdict"],
            "passed": actual == target_expected,
            "decision_digest": report["decision_digest"],
        })
    return results


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise SystemExit("output_dir_already_exists")

    development = _load(DEVELOPMENT)
    heldout_inputs = _load(HELDOUT_INPUTS)
    heldout_oracle = _load(HELDOUT_ORACLE)
    facts = _load(FACTS)
    candidate = _load(CANDIDATE)
    semantics = _load(SEMANTICS)
    if any("expected" in item for item in heldout_inputs["cases"]):
        raise SystemExit("heldout_input_contains_oracle")

    facts_by_id = {str(item["case_id"]): item for item in facts["cases"]}
    dev_expected = {str(item["case_id"]): dict(item["expected"]) for item in development["cases"]}
    heldout_expected = {str(item["case_id"]): dict(item["expected"]) for item in heldout_oracle["cases"]}
    if set(dev_expected) | set(heldout_expected) != set(facts_by_id):
        raise SystemExit("fact_mapping_case_ids_mismatch")

    catalog = _catalog(candidate, semantics)
    capture = facts["snapshot_defaults"]["capture"]
    development_results = _run(development["cases"], dev_expected, facts_by_id, catalog, capture, candidate["candidate_edge"])
    heldout_results = _run(heldout_inputs["cases"], heldout_expected, facts_by_id, catalog, capture, candidate["candidate_edge"])
    results = development_results + heldout_results
    metrics = {
        "false_safe_count": sum(item["expected"]["result"] == "failed" and item["actual"]["result"] in {"passed", "not_applicable"} for item in results),
        "extra_blocker_count": sum(item["actual"]["report_verdict"] == "BLOCKED" and item["expected"]["report_verdict"] != "BLOCKED" for item in results),
        "wrong_unknown_count": sum(item["expected"]["result"] == "unknown" and item["actual"]["result"] != "unknown" for item in results),
        "wrong_not_applicable_count": sum(item["expected"]["result"] == "not_applicable" and item["actual"]["result"] != "not_applicable" for item in results),
        "wrong_unsupported_count": sum(item["expected"]["result"] == "request_unsupported" and item["actual"]["result"] != "request_unsupported" for item in results),
    }
    failed = [item["case_id"] for item in results if not item["passed"]]
    status = "PASS" if not failed and not any(metrics.values()) else "CHANGES_REQUIRED"
    args.output_dir.mkdir(parents=True)
    _write(args.output_dir / "DEVELOPMENT_RESULTS.json", {"results": development_results})
    _write(args.output_dir / "HELDOUT_RESULTS.json", {"results": heldout_results})
    manifest = {
        "synthetic": True,
        "candidate_only": True,
        "evaluator": "dify_preflight.engine.evaluate.evaluate",
        "development_count": len(development_results),
        "heldout_count": len(heldout_results),
        "status": status,
        "failed_case_ids": failed,
        **metrics,
    }
    _write(args.output_dir / "RUN_MANIFEST.json", manifest)
    print(json.dumps(manifest, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
