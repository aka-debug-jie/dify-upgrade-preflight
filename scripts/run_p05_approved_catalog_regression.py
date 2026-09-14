#!/usr/bin/env python3
"""Run active P05 fixtures through a projection of the formally approved catalog."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dify_preflight.catalog.load import Catalog, CatalogPolicy, load_catalog  # noqa: E402
from dify_preflight.domain import DeploymentSnapshot, Fact, FactOrigin, FactStatus, UpgradeRequest  # noqa: E402
from dify_preflight.engine.evaluate import evaluate  # noqa: E402


def load(path: str) -> dict[str, Any]:
    value = yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def fact(value: Any, case_id: str, name: str) -> Fact:
    if not isinstance(value, dict):
        return Fact(FactStatus.KNOWN, value, FactOrigin.DECLARED, f"synthetic:{case_id}:{name}", None)
    status = FactStatus(value.get("status", "known"))
    origin = FactOrigin(value.get("origin", "declared"))
    return Fact(status, value.get("value") if status is FactStatus.KNOWN else None, origin, f"synthetic:{case_id}:{name}", value.get("reason"))


def snapshot(case_id: str, version: str, values: dict[str, Any], private_relations: dict[str, bool | None] | None = None) -> DeploymentSnapshot:
    facts = {"dify.declared_version": Fact(FactStatus.KNOWN, version, FactOrigin.DECLARED, f"synthetic:{case_id}:version", None)}
    facts.update({key: fact(value, case_id, key) for key, value in values.items()})
    return DeploymentSnapshot("1.0", "deployment_snapshot", True, case_id, {"mode": "compose_declared", "compose_version": "2.33"}, facts, {}, private_relations or {}, ())


def actual(report: dict[str, Any]) -> dict[str, str]:
    if not report["findings"]:
        return {"result": "request_unsupported", "verdict_effect": "unsupported", "report_verdict": report["verdict"]}
    result = report["findings"][0]["result"]
    effect = "warning" if result == "failed" and report["findings"][0]["severity"] == "warning" else "blocked" if result == "failed" else "incomplete" if result == "unknown" else "none"
    return {"result": result, "verdict_effect": effect, "report_verdict": report["verdict"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise SystemExit("output_dir_already_exists")
    manifest = load("catalog/approval-manifest.yaml")
    catalog = load_catalog(ROOT / "catalog/support-matrix.yaml", CatalogPolicy(ROOT / "catalog", manifest["approved_sources"], manifest["approval_hashes"], "owner_approved_local"))
    objects = manifest["approved_object_canonical"]["rules"]
    expected: dict[str, dict[str, str]] = {}
    cases: list[dict[str, Any]] = []
    dev = load("tests/fixtures/adjudicated/P05-development-cases.yaml")
    facts = {item["case_id"]: item for item in load("tests/fixtures/adjudicated/P05-development-facts.yaml")["cases"]}
    held = load("tests/fixtures/heldout/P05-heldout-inputs.yaml")
    held_oracle = {item["case_id"]: item["expected"] for item in load("tests/fixtures/adjudicated/P05-heldout-oracle.yaml")["cases"]}
    for item in dev["cases"]:
        if item["root_cause_id"] != "P05-R06":
            expected[item["case_id"]] = item["expected"] | {"report_verdict": "INCOMPLETE" if item["expected"]["result"] == "unknown" else "UNSUPPORTED" if item["expected"]["result"] == "request_unsupported" else "NO_KNOWN_BLOCKERS" if item["expected"]["verdict_effect"] != "blocked" else "BLOCKED"}
            cases.append(facts[item["case_id"]] | {"expected": expected[item["case_id"]], "group": "development"})
    for item in held["cases"]:
        if item["root_cause_id"] != "P05-R06":
            expected[item["case_id"]] = held_oracle[item["case_id"]] | {"report_verdict": "INCOMPLETE" if held_oracle[item["case_id"]]["result"] == "unknown" else "UNSUPPORTED" if held_oracle[item["case_id"]]["result"] == "request_unsupported" else "NO_KNOWN_BLOCKERS" if held_oracle[item["case_id"]]["verdict_effect"] != "blocked" else "BLOCKED"}
            cases.append(item | {"expected": expected[item["case_id"]], "group": "heldout"})
    worker_facts = {item["case_id"]: item for item in load("tests/fixtures/candidate_semantics/P05-worker-queue-executable-facts.yaml")["cases"]}
    for path, group, oracle_path in [("tests/fixtures/adjudicated/P05-worker-queue-development-cases.yaml", "development", None), ("tests/fixtures/heldout/P05-worker-queue-heldout-inputs.yaml", "heldout", "tests/fixtures/adjudicated/P05-worker-queue-heldout-oracle.yaml")]:
        oracle = {} if oracle_path is None else {item["case_id"]: item["expected"] for item in load(oracle_path)["cases"]}
        for item in load(path)["cases"]:
            value = item.get("expected", oracle.get(item["case_id"]))
            if value is None:
                raise SystemExit("missing_expected")
            normalized = value | {"report_verdict": "INCOMPLETE" if value["result"] == "unknown" else "UNSUPPORTED" if value["result"] == "request_unsupported" else "NO_KNOWN_BLOCKERS"}
            cases.append({"case_id": item["case_id"], "root_cause_id": "P05-R07", "candidate_edge_id": "P05-EDGE-WORKER-1131-1132", "d_facts": worker_facts[item["case_id"]]["d_facts"], "expected": normalized, "group": group, "request": item.get("request", {})})
    results = []
    for item in cases:
        rule_id = item["root_cause_id"]
        edge_id = item["candidate_edge_id"]
        edge = next(edge for edge in catalog.edges if edge["id"] == edge_id)
        rule = next(rule for rule in catalog.rules if rule["id"] == rule_id)
        canonical = objects[rule_id]["canonical_object"]
        projected_edge = dict(edge) | {"required_facts": canonical["required_facts"], "rule_ids": [rule_id]}
        projected = Catalog((projected_edge,), (rule,), catalog.digest, catalog.trust, catalog.source_digests)
        request = item.get("request", {})
        source = request.get("source_version", edge["source_version"])
        target = request.get("target_version", edge["target_version"])
        report = evaluate(
            snapshot(item["case_id"], source, item.get("b_facts", {}), item.get("b_private_relations")),
            UpgradeRequest(source, target, proposed_snapshot=snapshot(item["case_id"], target, item.get("d_facts", {}), item.get("d_private_relations"))),
            projected,
        )
        got = actual(report)
        results.append({"case_id": item["case_id"], "group": item["group"], "rule_id": rule_id, "expected": item["expected"], "actual": got, "verdict": report["verdict"], "passed": got == item["expected"]})
    metrics = {"false_safe": sum(x["expected"]["result"] == "failed" and x["actual"]["result"] in {"passed", "not_applicable"} for x in results), "extra_blocker": sum(x["actual"]["verdict_effect"] == "blocked" and x["expected"]["verdict_effect"] != "blocked" for x in results), "heldout_mismatch": sum(not x["passed"] for x in results if x["group"] == "heldout"), "wrong_unknown": sum(x["expected"]["result"] == "unknown" and x["actual"]["result"] != "unknown" for x in results), "wrong_unsupported": sum(x["expected"]["result"] == "request_unsupported" and x["actual"]["result"] != "request_unsupported" for x in results)}
    output = {"catalog_trust": catalog.trust, "catalog_digest": catalog.digest, "development_count": sum(x["group"] == "development" for x in results), "heldout_count": sum(x["group"] == "heldout" for x in results), **metrics, "failed_case_ids": [x["case_id"] for x in results if not x["passed"]], "results": results}
    args.output_dir.mkdir(parents=True)
    (args.output_dir / "RUN_MANIFEST.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in output.items() if key != "results"}, sort_keys=True))
    return 0 if not output["failed_case_ids"] and not any(metrics.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
