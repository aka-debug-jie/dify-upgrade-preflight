import json
from pathlib import Path

from dify_preflight.collect.compose import collect_snapshot
from dify_preflight.domain import CaptureRequest, FactStatus


def test_snapshot_is_declared_redacted_and_leaves_inputs_unchanged(tmp_path: Path) -> None:
    canary = "CANARY_P02_PRIVATE"
    compose = tmp_path / "compose.yaml"
    compose.write_text(
        f"services:\n  api:\n    image: langgenius/dify-api:1.0.0\n    environment:\n      SECRET_KEY: {canary}\n  worker:\n    image: langgenius/dify-api:1.0.0\n"
    )
    original = compose.read_bytes()
    snapshot = collect_snapshot(CaptureRequest(project_dir=tmp_path, compose_files=(compose,)))
    value = snapshot.to_dict()
    assert compose.read_bytes() == original
    assert value["synthetic"] is False
    assert value["capture"]["mode"] == "compose_declared"
    assert value["facts"]["dify.declared_version"]["status"] == "known"
    assert value["facts"]["dify.observed_version"]["status"] == "unknown"
    assert value["facts"]["history.earliest_version"]["status"] == "unknown"
    assert set(value["capture"]) == {"mode", "collector_version", "compose_version", "captured_at"}
    assert set(value) == {"schema_version", "kind", "synthetic", "snapshot_id", "capture", "facts", "public_config", "private_relations", "gaps"}
    assert canary not in json.dumps(value)


def test_bundled_vector_is_declared_but_persisted_data_remains_unknown(tmp_path: Path) -> None:
    compose = tmp_path / "compose.yaml"
    compose.write_text(
        "services:\n  api:\n    image: langgenius/dify-api:1.0.0\n  weaviate:\n    image: semitechnologies/weaviate:1.24.0\n    volumes:\n      - ./data:/var/lib/weaviate\n"
    )
    snapshot = collect_snapshot(CaptureRequest(project_dir=tmp_path, compose_files=(compose,)))
    assert snapshot.facts["vector.ownership"].value == "bundled"
    assert snapshot.facts["vector.persisted_data"].status is FactStatus.UNKNOWN
