from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_owner_scoped_candidate_semantics_use_target_d_and_fixed_fact_names() -> None:
    value = yaml.safe_load((ROOT / "catalog/candidates/P05-recovery-candidates.yaml").read_text(encoding="utf-8"))
    roots = {item["id"]: item for item in value["root_causes"]}

    assert value["status"] == "owner_scoped_candidate"
    assert roots["P05-R01"]["proposed_severity"] == "warning"
    assert roots["P05-R01"]["required_facts"] == [
        "proposed.agent_backend.declared",
        "proposed.private.agent_api_token_is_published_default",
    ]
    assert roots["P05-R02"]["required_facts"] == [
        "proposed.agent_backend.declared",
        "proposed.private.agent_api_tokens_same_as_peer",
        "proposed.agent_auth.wiring_complete",
    ]
    assert roots["P05-R03"]["required_facts"] == [
        "proposed.agent_backend.declared",
        "proposed.agent_runtime.backend",
        "proposed.agent_sandbox.target_network_topology",
    ]
    assert roots["P05-R04"]["required_facts"] == [
        "plugins.externally_installed",
        "proposed.plugins.provider_cache_enabled",
        "plugins.cache_invalidation_available",
    ]
