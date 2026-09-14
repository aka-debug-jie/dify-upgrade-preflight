import json
from pathlib import Path

from dify_preflight.cli import main
from dify_preflight.domain import DeploymentSnapshot, Fact, FactOrigin, FactStatus
from dify_preflight.snapshot_io import write_snapshot


ROOT = Path(__file__).resolve().parents[2]


def test_all_check_formats_hide_untrusted_fact_text(tmp_path: Path, capsys) -> None:
    current, proposed = _snapshots()
    current_path, proposed_path = tmp_path / "current.json", tmp_path / "proposed.json"
    write_snapshot(current, current_path)
    write_snapshot(proposed, proposed_path)
    canary = "CANARY_P07_NEVER_RENDER"
    proposed_path.write_text(proposed_path.read_text().replace('"source_ref": "test"', f'"source_ref": "{canary}"').replace('"reason": null', f'"reason": "{canary}"'))
    args = ("check", "--snapshot", str(current_path), "--proposed-snapshot", str(proposed_path), "--from", "1.16.0", "--to", "1.16.1", "--catalog", str(ROOT / "catalog"))
    for format_name in ("json", "text", "markdown"):
        assert main([*args, "--format", format_name]) == 2
        captured = capsys.readouterr()
        assert canary not in captured.out
        assert canary not in captured.err


def _snapshots() -> tuple[DeploymentSnapshot, DeploymentSnapshot]:
    def fact(value: object, origin: FactOrigin) -> Fact:
        return Fact(FactStatus.KNOWN, value, origin, "test", None)
    capture = {"mode": "compose_declared", "collector_version": "test", "compose_version": "2.33"}
    current = DeploymentSnapshot("1.0", "deployment_snapshot", True, "current", capture, {
        "dify.declared_version": fact("1.16.0", FactOrigin.DECLARED),
        "history.upgraded_from_before_1_15": fact(False, FactOrigin.ATTESTED),
        "migration.legacy_model_types_completed": fact(True, FactOrigin.ATTESTED),
        "plugins.cache_invalidation_available": fact(True, FactOrigin.ATTESTED),
        "plugins.externally_installed": fact(False, FactOrigin.ATTESTED),
    }, {}, {}, ())
    proposed = DeploymentSnapshot("1.0", "deployment_snapshot", True, "proposed", capture, {
        "dify.declared_version": fact("1.16.1", FactOrigin.DECLARED),
        "agent_backend.declared": fact(True, FactOrigin.DECLARED),
        "agent_auth.wiring_complete": fact(True, FactOrigin.DECLARED),
        "agent_runtime.backend": fact("e2b", FactOrigin.DECLARED),
        "agent_sandbox.target_network_topology": fact(True, FactOrigin.DECLARED),
        "plugins.provider_cache_enabled": fact(False, FactOrigin.DECLARED),
    }, {}, {"agent_api_token_is_published_default": False, "agent_api_tokens_same_as_peer": False}, ())
    return current, proposed
