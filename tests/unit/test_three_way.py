from dify_preflight.diff.three_way import compare_three_way
from dify_preflight.domain import Comparability, ConfigChangeKind, MISSING


PATH = "services.api.image_tag"


def one(a: object, b: object, c: object, d: object | None = None):
    proposed = None if d is None else {PATH: d}
    return compare_three_way({PATH: a}, {PATH: b}, {PATH: c}, proposed)[0]


def test_d01_to_d05_truth_table_and_missing_proposed() -> None:
    assert one("1", "1", "1").kind is ConfigChangeKind.UNCHANGED
    assert one("1", "1", "2").kind is ConfigChangeKind.UPSTREAM_ONLY
    assert one("1", "2", "1").kind is ConfigChangeKind.LOCAL_ONLY
    assert one("1", "2", "2").kind is ConfigChangeKind.SAME_CHANGE
    change = one("1", "2", "3")
    assert change.kind is ConfigChangeKind.DIVERGENT_CHANGE
    assert change.proposed is MISSING
    assert change.reason == "proposed_configuration_not_supplied"


def test_supplied_proposed_values_and_proposed_only_paths_are_retained() -> None:
    proposed_only = "services.web.image_tag"
    changes = compare_three_way(
        {PATH: "1"},
        {PATH: "1"},
        {PATH: "2"},
        {PATH: "2", proposed_only: None},
    )
    by_path = {change.path: change for change in changes}
    assert by_path[PATH].kind is ConfigChangeKind.UPSTREAM_ONLY
    assert by_path[PATH].proposed == "2"
    assert by_path[PATH].reason == "public_field_comparison"
    assert by_path[proposed_only].proposed is None
    assert by_path[proposed_only].base is MISSING


def test_d06_preserves_missing_null_empty_false_and_zero() -> None:
    changes = compare_three_way(
        {"services.api.image_tag": None, "services.web.image_tag": "", "services.worker.image_tag": False},
        {"services.api.image_tag": "", "services.web.image_tag": None, "services.worker.image_tag": 0},
        {"services.api.image_tag": None, "services.web.image_tag": "", "services.worker.image_tag": False},
    )
    assert [change.kind for change in changes] == [ConfigChangeKind.LOCAL_ONLY] * 3
    missing = compare_three_way({}, {PATH: ""}, {PATH: None})[0]
    assert missing.base is MISSING
    assert missing.kind is ConfigChangeKind.DIVERGENT_CHANGE


def test_command_is_not_a_public_field_and_does_not_leak() -> None:
    path = "services.api.command"
    change = compare_three_way({path: ["run", "web"]}, {path: ["web", "run"]}, {path: ["run", "web"]})[0]
    assert change.kind is ConfigChangeKind.UNKNOWN_COMPARISON
    assert change.base is MISSING
    assert change.local is MISSING


def test_ports_and_volumes_compare_by_registered_unique_keys() -> None:
    ports = "services.api.ports"
    volumes = "services.api.volumes"
    changes = compare_three_way(
        {ports: [{"target": 80, "published": "8080", "protocol": "tcp", "host_ip": "127.0.0.1"}], volumes: [{"type": "bind", "source": "./a", "target": "/data"}]},
        {ports: [{"target": 80, "published": "8080", "protocol": "tcp", "host_ip": "127.0.0.1"}], volumes: [{"target": "/data", "source": "./a", "type": "bind"}]},
        {ports: [{"target": 80, "published": "8081", "protocol": "tcp", "host_ip": "127.0.0.1"}], volumes: [{"target": "/data", "source": "./a", "type": "bind"}]},
    )
    assert [change.kind for change in changes] == [ConfigChangeKind.UPSTREAM_ONLY, ConfigChangeKind.UNCHANGED]


def test_port_key_allows_omitted_optional_host_ip() -> None:
    path = "services.api.ports"
    change = compare_three_way(
        {path: [{"target": 80, "published": "8080", "protocol": "tcp"}]},
        {path: [{"published": "8080", "protocol": "tcp", "target": 80}]},
        {path: [{"target": 80, "published": "8080", "protocol": "tcp"}]},
    )[0]
    assert change.kind is ConfigChangeKind.UNCHANGED


def test_unknown_or_duplicate_keyed_values_are_not_compared() -> None:
    path = "services.api.volumes"
    change = compare_three_way({path: [{"target": "/a"}, {"target": "/a"}]}, {path: []}, {path: []})[0]
    assert change.kind is ConfigChangeKind.UNKNOWN_COMPARISON
    assert change.comparability is Comparability.UNKNOWN


def test_unregistered_fields_are_unknown_comparisons() -> None:
    change = compare_three_way({"services.api.environment": "x"}, {"services.api.environment": "x"}, {"services.api.environment": "x"})[0]
    assert change.kind is ConfigChangeKind.UNKNOWN_COMPARISON


def test_registered_recovery_public_booleans_are_comparable() -> None:
    changes = compare_three_way(
        {
            "services.local_sandbox.present": False,
            "agent_sandbox.target_network_topology": False,
            "plugins.provider_cache_enabled": False,
        },
        {
            "services.local_sandbox.present": False,
            "agent_sandbox.target_network_topology": False,
            "plugins.provider_cache_enabled": False,
        },
        {
            "services.local_sandbox.present": True,
            "agent_sandbox.target_network_topology": True,
            "plugins.provider_cache_enabled": True,
        },
    )
    assert [item.kind for item in changes] == [ConfigChangeKind.UPSTREAM_ONLY] * 3
