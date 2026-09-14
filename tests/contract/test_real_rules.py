import hashlib
import json
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
    pinned = yaml.safe_load((ROOT / "sources/pinned.yaml").read_text(encoding="utf-8"))
    pins = {item["id"]: item for item in pinned["sources"]}
    for candidate_id, expected_refs in {
        "P05-C01": {"P00.S002", "P00.S003", "P00.S008", "P00.S009", "P00.S036", "P00.S054", "P00.S055"},
        "P05-C02": {"P00.S002", "P00.S026", "P00.S027", "P00.S028", "P00.S030", "P00.S031", "P00.S057", "P00.S058"},
    }.items():
        assert set(by_id[candidate_id]["source_refs"]) == expected_refs
        assert all(pins[source]["status"] == "obtained" and len(pins[source]["sha256"]) == 64 for source in expected_refs)


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


def test_p05_recovery_sources_are_locally_fixed_and_unapproved() -> None:
    manifest_path = ROOT / "artifacts/P05/20260913T123039Z/SOURCE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert len(manifest["sources"]) == 14
    source_ids = {source["id"] for source in manifest["sources"]}
    for source in manifest["sources"]:
        artifact = ROOT / source["artifact"]
        assert source["review_status"] == "candidate_not_approved"
        assert source["transport"] == "prior_https_fetch_cache"
        assert source["http_status"] is None
        assert source["final_url"] is None
        assert source["retrieved_at"] is None
        assert artifact.is_file()
        assert hashlib.sha256(artifact.read_bytes()).hexdigest() == source["sha256"]
    fixed_sources = yaml.safe_load(
        (ROOT / "catalog/candidates/P05-R05-fixed-sources.yaml").read_text(encoding="utf-8")
    )
    assert {source["source_id"] for source in fixed_sources["sources"]} == {"P05.S015", "P05.S016", "P05.S017"}
    assert all(source["classification"] == "official_fixed" for source in fixed_sources["sources"])
    source_ids |= {source["source_id"] for source in fixed_sources["sources"]}
    candidates = yaml.safe_load(
        (ROOT / "catalog/candidates/P05-recovery-candidates.yaml").read_text(encoding="utf-8")
    )
    assert {
        source
        for root_cause in candidates["root_causes"]
        for source in root_cause["source_refs"]
    } <= source_ids

    commits = {}
    for source in manifest["sources"]:
        if source["artifact"].endswith("tag-ref.json"):
            value = json.loads((ROOT / source["artifact"]).read_text(encoding="utf-8"))
            commits[value["ref"].removeprefix("refs/tags/")] = value["object"]["sha"]
    assert commits == {
        "1.16.0": "5c6372d2f76d240265b92fd27c16bc772ffcb107",
        "1.16.1": "6f8ed69ee15f9a2e7189ca066275e973d091d1e9",
        "1.17.0": "09a855dcef24c0edc7431c46c0cfaa494481daf5",
        "1.17.1": "8387590ace4a094de812b7847fc6a4c3a27cd52b",
    }
