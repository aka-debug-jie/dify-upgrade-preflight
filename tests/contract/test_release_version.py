from dify_preflight import __version__
from dify_preflight.domain import DeploymentSnapshot, Fact, FactOrigin, FactStatus, UpgradeRequest
from dify_preflight.engine.evaluate import evaluate


def test_release_version_is_bound_to_report_provenance() -> None:
    snapshot = DeploymentSnapshot(
        "1.0",
        "deployment_snapshot",
        True,
        "release-version",
        {"mode": "compose_declared", "compose_version": "2.33"},
        {"dify.declared_version": Fact(FactStatus.KNOWN, "0.0.0", FactOrigin.SYNTHETIC, "test", None)},
        {},
        {},
        (),
    )
    catalog = type("Catalog", (), {"edges": (), "rules": (), "digest": "synthetic", "trust": "synthetic"})()

    report = evaluate(snapshot, UpgradeRequest("0.0.0", "0.0.1"), catalog)

    assert __version__ == "0.1.0b0"
    assert report["provenance"]["tool_version"] == __version__
