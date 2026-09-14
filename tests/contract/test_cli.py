import json
import os
import subprocess
import sys
from unittest.mock import patch
from pathlib import Path

from dify_preflight.domain import DeploymentSnapshot, Fact, FactOrigin, FactStatus
from dify_preflight.snapshot_io import write_snapshot

ROOT = Path(__file__).resolve().parents[2]


def cli(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "dify_preflight", *args],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": "src", **(env or {})},
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_invalid_arguments_exit_64() -> None:
    completed = cli("demo", "--case", "missing")
    assert completed.returncode == 64


def test_demo_json_has_clean_stdout_and_blocked_exit() -> None:
    completed = cli("demo", "--case", "blocked", "--format", "json")
    assert completed.returncode == 2
    assert completed.stderr == ""
    assert json.loads(completed.stdout)["verdict"] == "BLOCKED"


def test_demo_text_respects_no_color() -> None:
    completed = cli("demo", "--case", "resolved", "--format", "text", env={"NO_COLOR": "1"})
    assert completed.returncode == 0
    assert "\x1b" not in completed.stdout


def test_check_requires_versions_snapshot_and_approved_catalog() -> None:
    completed = cli("check")
    assert completed.returncode == 64
    assert "--from" in completed.stderr
    assert "--to" in completed.stderr


def test_check_reports_blocked_clean_json_and_keeps_format_verdict(tmp_path: Path) -> None:
    current, proposed = _edge_a_snapshots(blocked=True)
    current_path, proposed_path = tmp_path / "current.json", tmp_path / "proposed.json"
    write_snapshot(current, current_path)
    write_snapshot(proposed, proposed_path)
    args = ("check", "--snapshot", str(current_path), "--proposed-snapshot", str(proposed_path), "--from", "1.16.0", "--to", "1.16.1", "--catalog", str(ROOT / "catalog"))
    json_result = cli(*args, "--format", "json")
    text_result = cli(*args, "--format", "text")
    markdown_result = cli(*args, "--format", "markdown")
    assert json_result.returncode == text_result.returncode == markdown_result.returncode == 2
    assert json_result.stderr == ""
    assert json.loads(json_result.stdout)["verdict"] == "BLOCKED"
    assert "Verdict: BLOCKED" in text_result.stdout
    assert "Fact origins:" in text_result.stdout
    assert "Manual action:" in text_result.stdout
    assert "BLOCKED" in markdown_result.stdout
    assert "Manual action" in markdown_result.stdout


def test_check_unknown_and_unsupported_never_pass(tmp_path: Path) -> None:
    current, _ = _edge_a_snapshots(blocked=False)
    current_path = tmp_path / "current.json"
    write_snapshot(current, current_path)
    incomplete = cli("check", "--snapshot", str(current_path), "--from", "1.16.0", "--to", "1.16.1", "--catalog", str(ROOT / "catalog"), "--format", "json")
    unsupported = cli("check", "--snapshot", str(current_path), "--from", "1.0.0", "--to", "1.0.1", "--catalog", str(ROOT / "catalog"), "--format", "json")
    assert incomplete.returncode == 3
    assert json.loads(incomplete.stdout)["verdict"] == "INCOMPLETE"
    assert unsupported.returncode == 4
    assert json.loads(unsupported.stdout)["verdict"] == "UNSUPPORTED"


def test_check_input_error_is_sanitized_json(tmp_path: Path) -> None:
    secret = "CANARY_P06_DO_NOT_PRINT"
    bad = tmp_path / "bad.json"
    bad.write_text('{"secret": "' + secret + '"}')
    completed = cli("check", "--snapshot", str(bad), "--from", "1.16.0", "--to", "1.16.1", "--catalog", str(ROOT / "catalog"), "--format", "json")
    assert completed.returncode == 5
    assert completed.stderr == ""
    assert json.loads(completed.stdout)["verdict"] == "ERROR"
    assert secret not in completed.stdout


def test_check_does_not_reemit_untrusted_fact_provenance(tmp_path: Path) -> None:
    current, proposed = _edge_a_snapshots(blocked=True)
    current_path, proposed_path = tmp_path / "current.json", tmp_path / "proposed.json"
    write_snapshot(current, current_path)
    write_snapshot(proposed, proposed_path)
    secret = "CANARY_P06_SOURCE_REF"
    proposed_path.write_text(proposed_path.read_text().replace('"source_ref": "test"', f'"source_ref": "{secret}"'))
    completed = cli("check", "--snapshot", str(current_path), "--proposed-snapshot", str(proposed_path), "--from", "1.16.0", "--to", "1.16.1", "--catalog", str(ROOT / "catalog"), "--format", "json")
    assert completed.returncode == 2
    assert secret not in completed.stdout
    assert "snapshot:declared" in completed.stdout


def test_snapshot_contract_uses_explicit_compose_and_never_echoes_input(tmp_path: Path) -> None:
    compose = tmp_path / "compose.yaml"
    compose.write_text("services:\n  api:\n    image: langgenius/dify-api:1.16.0\n")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    docker = fake_bin / "docker"
    docker.write_text("#!/bin/sh\nif [ \"$2\" = \"version\" ]; then echo 2.33.0; elif [ \"$3\" = \"--help\" ]; then echo '--format json'; else echo '{\"services\": {\"api\": {\"image\": \"langgenius/dify-api:1.16.0\"}, \"web\": {\"image\": \"langgenius/dify-web:1.16.0\"}}}'; fi\n")
    docker.chmod(0o755)
    completed = cli("snapshot", "--project-dir", str(tmp_path), "-f", "compose.yaml", "--catalog", str(ROOT / "catalog"), "--output", "snapshot.json", env={"PATH": str(fake_bin)})
    assert completed.returncode == 0
    assert completed.stderr == ""
    assert (tmp_path / "snapshot.json").is_file()
    assert "langgenius" not in completed.stdout


def test_user_interrupt_has_contract_exit_code() -> None:
    from dify_preflight import cli as cli_module

    with patch.object(cli_module, "build_parser", side_effect=KeyboardInterrupt):
        assert cli_module.main([]) == 130


def test_snapshot_refuses_to_overwrite_an_existing_output(tmp_path: Path) -> None:
    compose = tmp_path / "compose.yaml"
    output = tmp_path / "snapshot.json"
    compose.write_text("services: {}\n")
    output.write_text("keep-this")
    completed = cli("snapshot", "--project-dir", str(tmp_path), "-f", "compose.yaml", "--catalog", str(ROOT / "catalog"), "--output", "snapshot.json")
    assert completed.returncode == 5
    assert output.read_text() == "keep-this"


def _edge_a_snapshots(*, blocked: bool) -> tuple[DeploymentSnapshot, DeploymentSnapshot]:
    current_facts = {
        "dify.declared_version": _fact("1.16.0", FactOrigin.DECLARED),
        "history.upgraded_from_before_1_15": _fact(False, FactOrigin.ATTESTED),
        "migration.legacy_model_types_completed": _fact(True, FactOrigin.ATTESTED),
        "plugins.cache_invalidation_available": _fact(True, FactOrigin.ATTESTED),
        "plugins.externally_installed": _fact(False, FactOrigin.ATTESTED),
    }
    proposed_facts = {
        "dify.declared_version": _fact("1.16.1", FactOrigin.DECLARED),
        "agent_backend.declared": _fact(True, FactOrigin.DECLARED),
        "agent_auth.wiring_complete": _fact(True, FactOrigin.DECLARED),
        "agent_runtime.backend": _fact("e2b", FactOrigin.DECLARED),
        "agent_sandbox.target_network_topology": _fact(True, FactOrigin.DECLARED),
        "plugins.provider_cache_enabled": _fact(False, FactOrigin.DECLARED),
    }
    current = DeploymentSnapshot("1.0", "deployment_snapshot", True, "current", _capture(), current_facts, {}, {}, ())
    proposed = DeploymentSnapshot("1.0", "deployment_snapshot", True, "proposed", _capture(), proposed_facts, {}, {
        "agent_api_token_is_published_default": False,
        "agent_api_tokens_same_as_peer": not blocked,
    }, ())
    return current, proposed


def _capture() -> dict[str, object]:
    return {"mode": "compose_declared", "collector_version": "test", "compose_version": "2.33"}


def _fact(value: object, origin: FactOrigin) -> Fact:
    return Fact(FactStatus.KNOWN, value, origin, "test", None)
