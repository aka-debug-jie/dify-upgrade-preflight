from collections import Counter
from pathlib import Path

import yaml

from dify_preflight.catalog.load import CatalogPolicy, load_catalog

ROOT = Path(__file__).resolve().parents[2]


def test_p05_candidates_remain_nonexecutable_when_digest_bound_catalog_is_approved() -> None:
    register = yaml.safe_load(
        (ROOT / "catalog/candidates/P05-candidate-register.yaml").read_text(encoding="utf-8")
    )
    matrix = yaml.safe_load((ROOT / "catalog/support-matrix.yaml").read_text(encoding="utf-8"))

    assert register["executable"] is False
    assert len(register["candidates"]) == 6
    assert all(item["status"] == "candidate" for item in register["candidates"])
    assert all(item["approval_ref"] is None for item in register["candidates"])
    assert {edge["id"] for edge in matrix["approved_edges"]} == {"P05-EDGE-A", "P05-EDGE-WORKER-1131-1132"}


def test_p05_only_fixed_evidence_candidates_can_be_review_ready() -> None:
    register = yaml.safe_load(
        (ROOT / "catalog/candidates/P05-candidate-register.yaml").read_text(encoding="utf-8")
    )

    readiness = {item["id"]: item["evidence_status"] for item in register["candidates"]}
    assert readiness == {
        "P05-C01": "review_ready",
        "P05-C02": "review_ready",
        "P05-C03": "insufficient_fixed_evidence",
        "P05-C04": "insufficient_fixed_evidence",
        "P05-C05": "insufficient_fixed_evidence",
        "P05-C06": "insufficient_fixed_evidence",
    }

    by_id = {item["id"]: item for item in register["candidates"]}
    manifest = yaml.safe_load((ROOT / "catalog/approval-manifest.yaml").read_text(encoding="utf-8"))
    expected_worker_refs = {"P00.S002", "P00.S026", "P00.S027", "P00.S028", "P00.S030", "P00.S031", "P00.S057", "P00.S058"}
    assert set(by_id["P05-C02"]["source_refs"]) == expected_worker_refs
    assert expected_worker_refs <= set(manifest["approved_sources"])
    assert by_id["P05-C01"]["source_refs"]


def test_product_catalog_loads_only_approved_directory_with_owner_policy() -> None:
    manifest = yaml.safe_load((ROOT / "catalog/approval-manifest.yaml").read_text(encoding="utf-8"))
    catalog = load_catalog(
        ROOT / "catalog/support-matrix.yaml",
        CatalogPolicy(
            root=ROOT / "catalog",
            approved_sources=manifest["approved_sources"],
            approval_hashes=manifest["approval_hashes"],
            trust="owner_approved_local",
        ),
    )

    assert {rule["id"] for rule in catalog.rules} == {"P05-R01", "P05-R02", "P05-R03", "P05-R04", "P05-R05", "P05-R07"}
    assert {edge["id"] for edge in catalog.edges} == {"P05-EDGE-A", "P05-EDGE-WORKER-1131-1132"}


def test_p05_recovery_package_has_six_roots_and_thirty_pending_cases() -> None:
    candidates = yaml.safe_load(
        (ROOT / "catalog/candidates/P05-recovery-candidates.yaml").read_text(encoding="utf-8")
    )
    cases = yaml.safe_load(
        (ROOT / "tests/fixtures/pending_adjudication/P05-recovery-cases.yaml").read_text(encoding="utf-8")
    )

    assert candidates["status"] == "owner_scoped_candidate"
    assert candidates["semantics_approval_ref"] == "APR-P05-SEMANTICS-20260914-01"
    assert candidates["executable"] is False
    assert len(candidates["candidate_edges"]) == 2
    assert len(candidates["root_causes"]) == 6
    assert len({item["id"] for item in candidates["root_causes"]}) == 6
    assert all(item["approval_ref"] is None for item in candidates["root_causes"])
    assert cases["status"] == "pending_owner_adjudication"
    assert cases["independently_adjudicated"] is False
    assert len(cases["cases"]) >= 30
    assert len({item["id"] for item in cases["cases"]}) == len(cases["cases"])
    assert {item["root_cause_id"] for item in cases["cases"]} == {
        item["id"] for item in candidates["root_causes"]
    }
    counts = Counter(item["root_cause_id"] for item in cases["cases"])
    assert all(counts[item["id"]] >= 5 for item in candidates["root_causes"])
    assert all(item["owner_decision"] is None for item in cases["cases"])


def test_active_p05_recovery_sources_are_publicly_bound() -> None:
    manifest = yaml.safe_load((ROOT / "catalog/approval-manifest.yaml").read_text(encoding="utf-8"))
    fixed_sources = yaml.safe_load(
        (ROOT / "catalog/candidates/P05-R05-fixed-sources.yaml").read_text(encoding="utf-8")
    )
    assert {source["source_id"] for source in fixed_sources["sources"]} == {"P05.S015", "P05.S016", "P05.S017"}
    assert all(source["classification"] == "official_fixed" for source in fixed_sources["sources"])
    candidates = yaml.safe_load(
        (ROOT / "catalog/candidates/P05-recovery-candidates.yaml").read_text(encoding="utf-8")
    )
    active = yaml.safe_load((ROOT / "catalog/candidates/P05-active-promotion-set.yaml").read_text(encoding="utf-8"))
    worker = yaml.safe_load((ROOT / "catalog/candidates/P05-worker-queue-candidate.yaml").read_text(encoding="utf-8"))
    roots = {item["id"]: item for item in candidates["root_causes"]}
    roots[worker["root_cause"]["id"]] = worker["root_cause"]
    assert {
        source
        for root_id in active["active_candidate_root_ids"]
        for root_cause in [roots[root_id]]
        for source in root_cause["source_refs"]
    } <= set(manifest["approved_sources"])
