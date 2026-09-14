from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_worker_queue_development_and_heldout_oracles_are_owner_locked_and_separate() -> None:
    development = yaml.safe_load((ROOT / "tests/fixtures/adjudicated/P05-worker-queue-development-cases.yaml").read_text(encoding="utf-8"))
    heldout_inputs = yaml.safe_load((ROOT / "tests/fixtures/heldout/P05-worker-queue-heldout-inputs.yaml").read_text(encoding="utf-8"))
    heldout_oracle = yaml.safe_load((ROOT / "tests/fixtures/adjudicated/P05-worker-queue-heldout-oracle.yaml").read_text(encoding="utf-8"))

    assert development["status"] == "owner_adjudicated_candidate_development"
    assert len(development["cases"]) == 8
    assert all(case["owner_decision"] == "adjudicated_for_candidate_development" for case in development["cases"])
    assert heldout_inputs["status"] == "owner_locked_heldout_input"
    assert len(heldout_inputs["cases"]) == 3
    assert all("expected" not in case for case in heldout_inputs["cases"])
    assert heldout_oracle["status"] == "owner_adjudicated_heldout_oracle"
    assert {case["case_id"] for case in heldout_inputs["cases"]} == {case["case_id"] for case in heldout_oracle["cases"]}
