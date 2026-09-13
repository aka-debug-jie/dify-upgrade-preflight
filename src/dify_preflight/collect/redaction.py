from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from dify_preflight.domain import DeploymentSnapshot, Fact, FactOrigin, FactStatus


SAFE_SERVICES = ("api", "worker", "web", "weaviate", "agent_backend", "local_sandbox", "agent_ssrf_proxy")
PUBLISHED_AGENT_TOKEN = "dify-agent-run-token-for-dev-only"
ATTESTATION_FACTS = frozenset({
    "plugins.externally_installed",
    "plugins.cache_invalidation_available",
    "history.upgraded_from_before_1_15",
    "migration.legacy_model_types_completed",
    "vector.persisted_data",
    "vector.staged_upgrade_completed",
})


def declared_snapshot(
    model: Mapping[str, Any],
    compose_version: str,
    attestations: Mapping[str, bool] | None = None,
) -> DeploymentSnapshot:
    attestations = {} if attestations is None else attestations
    _validate_attestations(attestations)
    services = model.get("services", {}) if isinstance(model.get("services", {}), Mapping) else {}
    public_config: dict[str, str | bool] = {}
    tags: dict[str, str] = {}
    for name in SAFE_SERVICES:
        service = services.get(name)
        public_config[f"services.{name}.present"] = isinstance(service, Mapping)
        if isinstance(service, Mapping) and isinstance(service.get("image"), str):
            tag = _image_tag(service["image"])
            if tag is not None:
                public_config[f"services.{name}.image_tag"] = tag
                tags[name] = tag

    api_web_tags = {tags[name] for name in ("api", "web") if name in tags}
    if len(api_web_tags) == 1:
        declared = _known(next(iter(api_web_tags)), "compose:image_tag")
    elif len(api_web_tags) > 1:
        declared = Fact(FactStatus.CONFLICTED, None, FactOrigin.DECLARED, "compose:image_tag", "API and Web image tags disagree")
    else:
        declared = _unknown("compose:image_tag", "No unambiguous API/Web declared image tag")

    relations = _agent_relations(services)
    topology = _agent_topology(model, services)
    cache_enabled = _provider_cache_enabled(services)
    bundled = "weaviate" in services
    facts: dict[str, Fact] = {
        "dify.declared_version": declared,
        "dify.observed_version": _unknown("runtime_not_observed"),
        "history.earliest_version": _unknown("history_not_observed"),
        "migration.legacy_model_types": _unknown("migration_history_not_observed"),
        "agent_backend.declared": _known(isinstance(services.get("agent_backend"), Mapping), "compose:services.agent_backend"),
        "agent_auth.wiring_complete": _known(relations["wiring_complete"], "compose:agent_auth_wiring")
        if relations["wiring_complete"] is not None else _unknown("agent_auth_wiring_not_provable"),
        "agent_sandbox.target_network_topology": _known(topology, "compose:agent_networks")
        if topology is not None else _unknown("agent_network_topology_not_provable"),
        "plugins.provider_cache_enabled": _known(cache_enabled, "compose:provider_cache")
        if cache_enabled is not None else _unknown("provider_cache_not_declared"),
        "vector.ownership": _known("bundled", "compose:services.weaviate")
        if bundled else _unknown("vector_ownership_not_declared"),
        "vector.persisted_data": _unknown("mount_declaration_is_not_data_observation"),
    }
    for key, value in attestations.items():
        facts[key] = Fact(FactStatus.KNOWN, value, FactOrigin.ATTESTED, "capture:attestation", None)
    if topology is not None:
        public_config["agent_sandbox.target_network_topology"] = topology
    if cache_enabled is not None:
        public_config["plugins.provider_cache_enabled"] = cache_enabled
    return DeploymentSnapshot(
        schema_version="1.0",
        kind="deployment_snapshot",
        synthetic=False,
        snapshot_id=f"capture-{uuid4().hex}",
        capture={
            "mode": "compose_declared",
            "collector_version": "0.1.0-recovery",
            "compose_version": compose_version,
            "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        },
        facts=facts,
        public_config=public_config,
        private_relations={
            "agent_api_token_is_published_default": relations["is_published_default"],
            "agent_api_tokens_same_as_peer": relations["same_as_peer"],
        },
        gaps=(
            {"id": "runtime_images", "reason": "Runtime images are not observed in static collection", "affects": ["dify.observed_version"], "required_for_scope": False},
            {"id": "database_state", "reason": "Database state is outside static collection", "affects": ["migration.legacy_model_types"], "required_for_scope": False},
        ),
    )


def _validate_attestations(values: Mapping[str, bool]) -> None:
    if not isinstance(values, Mapping) or any(key not in ATTESTATION_FACTS or not isinstance(value, bool) for key, value in values.items()):
        raise ValueError("attestation")


def _agent_relations(services: Mapping[str, Any]) -> dict[str, bool | None]:
    backend = services.get("agent_backend")
    if not isinstance(backend, Mapping):
        return {"is_published_default": None, "same_as_peer": None, "wiring_complete": None}
    backend_token = _environment(backend).get("DIFY_AGENT_API_TOKEN")
    peers = []
    complete = True
    for name in ("api", "worker"):
        service = services.get(name)
        if not isinstance(service, Mapping):
            complete = False
            continue
        peers.append(_environment(service).get("AGENT_BACKEND_API_TOKEN"))
    values = [backend_token, *peers]
    if not all(isinstance(value, str) and value for value in values):
        return {
            "is_published_default": backend_token == PUBLISHED_AGENT_TOKEN if isinstance(backend_token, str) and backend_token else None,
            "same_as_peer": None,
            "wiring_complete": False if complete else None,
        }
    return {
        "is_published_default": backend_token == PUBLISHED_AGENT_TOKEN,
        "same_as_peer": len(set(values)) == 1,
        "wiring_complete": complete,
    }


def _provider_cache_enabled(services: Mapping[str, Any]) -> bool | None:
    values = []
    for name in ("api", "worker"):
        service = services.get(name)
        if not isinstance(service, Mapping):
            return None
        value = _environment(service).get("PLUGIN_MODEL_PROVIDERS_CACHE_ENABLED")
        if not isinstance(value, str) or value.lower() not in {"true", "false"}:
            return None
        values.append(value.lower() == "true")
    return values[0] if len(set(values)) == 1 else None


def _agent_topology(model: Mapping[str, Any], services: Mapping[str, Any]) -> bool | None:
    local = services.get("local_sandbox")
    if not isinstance(local, Mapping):
        return False
    if "network_mode" in local:
        return None
    local_networks = _networks(local)
    backend_networks = _networks(services.get("agent_backend"))
    proxy_networks = _networks(services.get("agent_ssrf_proxy"))
    if local_networks is None or backend_networks is None or proxy_networks is None:
        return None
    expected_local = {"agent_sandbox_network", "local_sandbox_proxy_network"}
    expected_proxy = {"default", "local_sandbox_proxy_network"}
    if set(local_networks) != expected_local or "agent_sandbox_network" not in backend_networks or set(proxy_networks) != expected_proxy:
        return False
    root_networks = model.get("networks", {})
    if not isinstance(root_networks, Mapping):
        return None
    for name in expected_local:
        definition = root_networks.get(name)
        if not isinstance(definition, Mapping) or definition.get("internal") is not True or definition.get("external") is True:
            return False
    env = _environment(local)
    return env.get("HTTP_PROXY") == "http://agent_ssrf_proxy:3128" and env.get("HTTPS_PROXY") == "http://agent_ssrf_proxy:3128"


def _networks(service: object) -> list[str] | None:
    if not isinstance(service, Mapping) or "network_mode" in service:
        return None
    value = service.get("networks", [])
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    if isinstance(value, Mapping) and all(isinstance(item, str) for item in value):
        return list(value)
    return None


def _environment(service: Mapping[str, Any]) -> dict[str, str | None]:
    value = service.get("environment", {})
    if isinstance(value, Mapping):
        return {str(key): item if isinstance(item, str) else None for key, item in value.items()}
    if isinstance(value, list):
        result: dict[str, str | None] = {}
        for item in value:
            if not isinstance(item, str) or "=" not in item:
                return {}
            key, raw = item.split("=", 1)
            result[key] = raw
        return result
    return {}


def _known(value: str | bool, source: str) -> Fact:
    return Fact(FactStatus.KNOWN, value, FactOrigin.DECLARED, source, None)


def _unknown(reason: str, detail: str | None = None) -> Fact:
    return Fact(FactStatus.UNKNOWN, None, FactOrigin.DECLARED, "static_collection", detail or reason)


def _image_tag(image: str) -> str | None:
    if "@" in image or ":" not in image.rsplit("/", 1)[-1]:
        return None
    return image.rsplit(":", 1)[-1]
