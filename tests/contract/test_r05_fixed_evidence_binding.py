from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_r05_candidate_binds_named_fixed_sources_without_changing_semantics() -> None:
    candidates = yaml.safe_load((ROOT / "catalog/candidates/P05-recovery-candidates.yaml").read_text(encoding="utf-8"))
    sources = yaml.safe_load((ROOT / "catalog/candidates/P05-R05-fixed-sources.yaml").read_text(encoding="utf-8"))
    r05 = next(item for item in candidates["root_causes"] if item["id"] == "P05-R05")

    assert {"P05.S015", "P05.S016", "P05.S017"} <= set(r05["source_refs"])
    assert {item["source_id"] for item in sources["sources"]} == {"P05.S015", "P05.S016", "P05.S017"}
    assert all(item["classification"] == "official_fixed" for item in sources["sources"])
    assert r05["proposed_severity"] == "warning"
    assert r05["proposed_phase"] == "after_upgrade"
