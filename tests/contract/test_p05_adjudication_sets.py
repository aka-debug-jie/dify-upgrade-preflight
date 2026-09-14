from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_owner_adjudicated_development_and_heldout_sets_are_disjoint() -> None:
    development = yaml.safe_load((ROOT / "tests/fixtures/adjudicated/P05-development-cases.yaml").read_text())
    heldout = yaml.safe_load((ROOT / "tests/fixtures/heldout/P05-heldout-manifest.yaml").read_text())
    pending = yaml.safe_load((ROOT / "tests/fixtures/pending_adjudication/P05-recovery-cases.yaml").read_text())

    assert development["status"] == "owner_adjudicated_candidate_development"
    assert len(development["cases"]) == 26
    assert all(item["owner_decision"] == "adjudicated_for_candidate_development" for item in development["cases"])
    assert heldout["status"] == "owner_selected_heldout"
    assert len(heldout["case_ids"]) == 7
    development_ids = {item["case_id"] for item in development["cases"]}
    heldout_ids = set(heldout["case_ids"])
    assert not development_ids & heldout_ids
    assert development_ids | heldout_ids == {item["id"] for item in pending["cases"]}
    assert all(item["owner_decision"] is None for item in pending["cases"])
