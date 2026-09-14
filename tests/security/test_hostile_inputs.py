import hashlib
import shutil
from pathlib import Path
from unittest.mock import patch

import yaml
from dify_preflight.catalog.load import CatalogPolicy, load_catalog
from dify_preflight.domain import DeploymentSnapshot, Fact, FactOrigin, FactStatus, UpgradeRequest
from dify_preflight.engine.evaluate import evaluate
from dify_preflight.snapshot_io import load_snapshot, write_snapshot


ROOT = Path(__file__).resolve().parents[2]


def test_snapshot_loader_rejects_duplicate_keys_and_non_finite_values(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"schema_version":"1.0","schema_version":"1.0"}')
    non_finite = tmp_path / "non-finite.json"
    non_finite.write_text('{"schema_version": NaN}')
    for path in (duplicate, non_finite):
        try:
            load_snapshot(path)
        except ValueError:
            pass
        else:
            raise AssertionError("hostile snapshot unexpectedly loaded")


def test_core_evaluator_does_not_open_socket_or_spawn_process() -> None:
    snapshot = DeploymentSnapshot("1.0", "deployment_snapshot", False, "s", {"mode": "compose_declared", "compose_version": "2.33"}, {
        "dify.declared_version": Fact(FactStatus.KNOWN, "0.0.1", FactOrigin.DECLARED, "test", None),
    }, {}, {}, ())
    catalog = type("Catalog", (), {"edges": (), "rules": (), "digest": "test", "trust": "synthetic"})()
    with patch("socket.socket", side_effect=AssertionError("socket")), patch("subprocess.Popen", side_effect=AssertionError("process")):
        report = evaluate(snapshot, UpgradeRequest("0.0.1", "0.0.2"), catalog)
    assert report["verdict"] == "UNSUPPORTED"


def test_check_input_remains_read_only(tmp_path: Path) -> None:
    snapshot = DeploymentSnapshot("1.0", "deployment_snapshot", False, "s", {"mode": "compose_declared", "collector_version": "test", "compose_version": "2.33"}, {
        "dify.declared_version": Fact(FactStatus.KNOWN, "0.0.1", FactOrigin.DECLARED, "test", None),
    }, {}, {}, ())
    path = tmp_path / "snapshot.json"
    write_snapshot(snapshot, path)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    loaded = load_snapshot(path)
    after = hashlib.sha256(path.read_bytes()).hexdigest()
    assert loaded.snapshot_id == "s"
    assert before == after


def test_cli_check_captures_any_write_attempt(tmp_path: Path, capsys) -> None:
    from dify_preflight.cli import main

    snapshot = DeploymentSnapshot("1.0", "deployment_snapshot", False, "s", {"mode": "compose_declared", "collector_version": "test", "compose_version": "2.33"}, {
        "dify.declared_version": Fact(FactStatus.KNOWN, "0.0.1", FactOrigin.DECLARED, "test", None),
    }, {}, {}, ())
    path = tmp_path / "snapshot.json"
    write_snapshot(snapshot, path)
    real_open = Path.open

    def read_only_open(self: Path, mode: str = "r", *args: object, **kwargs: object):
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            raise AssertionError(f"unexpected write: {self.name}")
        return real_open(self, mode, *args, **kwargs)

    with patch.object(Path, "open", read_only_open):
        assert main(["check", "--snapshot", str(path), "--from", "0.0.1", "--to", "0.0.2", "--catalog", str(ROOT / "catalog")]) == 4
    capsys.readouterr()


def test_mutated_approval_hash_is_rejected(tmp_path: Path) -> None:
    catalog_root = tmp_path / "catalog"
    shutil.copytree(ROOT / "catalog", catalog_root)
    manifest = yaml.safe_load((catalog_root / "approval-manifest.yaml").read_text())
    approvals = manifest["approval_hashes"]
    approvals[manifest["approval_ref"]]["support-matrix.yaml"] = "0" * 64
    policy = CatalogPolicy(
        root=catalog_root,
        approved_sources=manifest["approved_sources"],
        approval_hashes=approvals,
        trust="owner_approved_local",
    )
    try:
        load_catalog(catalog_root / "support-matrix.yaml", policy)
    except ValueError:
        pass
    else:
        raise AssertionError("mutated approval hash unexpectedly loaded")
