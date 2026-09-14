from pathlib import Path

import yaml

from dify_preflight.domain import Fact, FactOrigin, FactStatus
from dify_preflight.engine.expressions import evaluate_expression


ROOT = Path(__file__).resolve().parents[2]


def _facts(**values: object) -> dict[str, Fact]:
    return {name: Fact(FactStatus.KNOWN, value, FactOrigin.DECLARED, "test", None) for name, value in values.items()}


def test_candidate_rules_use_owner_scoped_semantics() -> None:
    value = yaml.safe_load((ROOT / "catalog/candidates/P05-rule-semantics.yaml").read_text())
    by_id = {item["id"]: item for item in value["rules"]}

    r01 = _facts(**{"proposed.agent_backend.declared": True, "proposed.private.agent_api_token_is_published_default": True})
    assert evaluate_expression(by_id["P05-R01"]["applies"], r01).value == "TRUE"
    assert evaluate_expression(by_id["P05-R01"]["assertion"], r01).value == "FALSE"

    r02 = _facts(**{"proposed.agent_backend.declared": True, "proposed.private.agent_api_tokens_same_as_peer": True, "proposed.agent_auth.wiring_complete": False})
    assert evaluate_expression(by_id["P05-R02"]["assertion"], r02).value == "FALSE"

    r03 = _facts(**{"proposed.agent_backend.declared": True, "proposed.agent_runtime.backend": "enterprise", "proposed.agent_sandbox.target_network_topology": False})
    assert evaluate_expression(by_id["P05-R03"]["applies"], r03).value == "FALSE"

    r04 = _facts(**{"plugins.externally_installed": True, "proposed.plugins.provider_cache_enabled": False, "plugins.cache_invalidation_available": False})
    assert evaluate_expression(by_id["P05-R04"]["applies"], r04).value == "FALSE"

    r06 = _facts(**{"vector.ownership": "bundled", "vector.persisted_data": True, "vector.staged_upgrade_completed": False})
    assert evaluate_expression(by_id["P05-R06"]["assertion"], r06).value == "FALSE"
