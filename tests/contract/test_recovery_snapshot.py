import json
from pathlib import Path

import pytest

from dify_preflight.collect.compose import collect_snapshot
from dify_preflight.collect.safe_io import CaptureError
from dify_preflight.domain import CaptureRequest, FactOrigin, FactStatus


def test_recovery_snapshot_derives_only_fixed_relations_and_attestations(tmp_path: Path) -> None:
    canary = "CANARY_RECOVERY_TOKEN"
    compose = tmp_path / "compose.yaml"
    compose.write_text(
        "services:\n"
        "  api:\n"
        "    image: langgenius/dify-api:1.16.1\n"
        "    environment:\n"
        "      AGENT_BACKEND_API_TOKEN: dify-agent-run-token-for-dev-only\n"
        "      PLUGIN_MODEL_PROVIDERS_CACHE_ENABLED: 'true'\n"
        "  worker:\n"
        "    image: langgenius/dify-api:1.16.1\n"
        "    environment:\n"
        "      AGENT_BACKEND_API_TOKEN: dify-agent-run-token-for-dev-only\n"
        "      PRIVATE_CANARY: " + canary + "\n"
        "      PLUGIN_MODEL_PROVIDERS_CACHE_ENABLED: 'true'\n"
        "  agent_backend:\n"
        "    image: langgenius/dify-agent-backend:1.16.1\n"
        "    environment:\n"
        "      DIFY_AGENT_API_TOKEN: dify-agent-run-token-for-dev-only\n"
        "    networks: [agent_sandbox_network]\n"
        "  local_sandbox:\n"
        "    image: langgenius/dify-agent-local-sandbox:1.16.1\n"
        "    environment:\n"
        "      HTTP_PROXY: http://agent_ssrf_proxy:3128\n"
        "      HTTPS_PROXY: http://agent_ssrf_proxy:3128\n"
        "    networks: [agent_sandbox_network, local_sandbox_proxy_network]\n"
        "  agent_ssrf_proxy:\n"
        "    image: ubuntu/squid:latest\n"
        "    networks: [default, local_sandbox_proxy_network]\n"
        "networks:\n"
        "  agent_sandbox_network: {internal: true}\n"
        "  local_sandbox_proxy_network: {internal: true}\n",
        encoding="utf-8",
    )
    snapshot = collect_snapshot(
        CaptureRequest(
            project_dir=tmp_path,
            compose_files=(compose,),
            attestations={
                "history.upgraded_from_before_1_15": True,
                "migration.legacy_model_types_completed": False,
                "vector.persisted_data": True,
                "vector.staged_upgrade_completed": False,
                "plugins.externally_installed": True,
                "plugins.cache_invalidation_available": False,
            },
        )
    )
    assert snapshot.private_relations["agent_api_token_is_published_default"] is True
    assert snapshot.private_relations["agent_api_tokens_same_as_peer"] is True
    assert snapshot.facts["agent_sandbox.target_network_topology"].value is True
    assert snapshot.facts["agent_runtime.backend"].value == "local"
    assert snapshot.facts["plugins.provider_cache_enabled"].value is True
    assert snapshot.facts["history.upgraded_from_before_1_15"].origin is FactOrigin.ATTESTED
    assert snapshot.facts["migration.legacy_model_types_completed"].value is False
    assert snapshot.facts["vector.persisted_data"].status is FactStatus.KNOWN
    assert canary not in json.dumps(snapshot.to_dict())


def test_recovery_snapshot_rejects_unapproved_attestation_keys(tmp_path: Path) -> None:
    compose = tmp_path / "compose.yaml"
    compose.write_text("services: {api: {image: langgenius/dify-api:1.16.1}}\n", encoding="utf-8")
    with pytest.raises(CaptureError, match="invalid_attestation"):
        collect_snapshot(
            CaptureRequest(
                project_dir=tmp_path,
                compose_files=(compose,),
                attestations={"dify.declared_version": True},
            )
        )


def test_unknown_recovery_public_fields_are_omitted_not_projected_false(tmp_path: Path) -> None:
    compose = tmp_path / "compose.yaml"
    compose.write_text("services: {api: {image: langgenius/dify-api:1.16.1}, worker: {image: langgenius/dify-api:1.16.1}}\n", encoding="utf-8")
    snapshot = collect_snapshot(CaptureRequest(project_dir=tmp_path, compose_files=(compose,)))
    assert snapshot.facts["agent_sandbox.target_network_topology"].status is FactStatus.KNOWN
    assert snapshot.facts["agent_sandbox.target_network_topology"].value is False
    assert "plugins.provider_cache_enabled" not in snapshot.public_config


def test_agent_runtime_backend_is_unknown_for_conflicting_or_unclassified_compose(tmp_path: Path) -> None:
    compose = tmp_path / "compose.yaml"
    compose.write_text(
        "services:\n"
        "  api:\n"
        "    image: langgenius/dify-api:1.16.1\n"
        "    environment:\n"
        "      ENTERPRISE_ENABLED: 'true'\n"
        "      E2B_API_KEY: synthetic-only\n",
        encoding="utf-8",
    )
    snapshot = collect_snapshot(CaptureRequest(project_dir=tmp_path, compose_files=(compose,)))
    assert snapshot.facts["agent_runtime.backend"].status is FactStatus.UNKNOWN
