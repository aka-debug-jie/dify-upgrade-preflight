import os
from pathlib import Path

import pytest

from dify_preflight.collect import compose as compose_module
from dify_preflight.collect.compose import collect_snapshot, probe_compose
from dify_preflight.collect.safe_io import CaptureError
from dify_preflight.domain import CaptureRequest, FactStatus


def capture(project_dir: Path, *files: Path, **kwargs: object):
    return collect_snapshot(CaptureRequest(project_dir=project_dir, compose_files=files, **kwargs))


def test_compose_probe_supports_json() -> None:
    capability = probe_compose()
    assert capability.version.startswith("2.33.0")
    assert capability.json_output is True


@pytest.mark.parametrize(
    ("expression", "allowed_env", "expected"),
    [
        ("${X-default}", {}, "default"),
        ("${X-default}", {"X": ""}, ""),
        ("${X:-default}", {}, "default"),
        ("${X:-default}", {"X": ""}, "default"),
    ],
)
def test_native_compose_interpolation_oracle(tmp_path: Path, expression: str, allowed_env: dict[str, str], expected: str) -> None:
    compose = tmp_path / "compose.yaml"
    compose.write_text(f"services:\n  api:\n    image: langgenius/dify-api:{expression}\n")
    request = CaptureRequest(project_dir=tmp_path, compose_files=(compose,), allowed_env=allowed_env)
    snapshot = collect_snapshot(request)
    assert snapshot.facts["dify.declared_version"].value == expected
    assert snapshot.public_config["services.api.image_tag"] == expected
    assert snapshot.capture["compose_version"].startswith("2.33.0")


def test_multi_file_merge_and_parent_docker_host_do_not_change_capture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base = tmp_path / "base.yaml"
    override = tmp_path / "override.yaml"
    base.write_text("services:\n  api:\n    image: langgenius/dify-api:1.0.0\n")
    override.write_text("services:\n  api:\n    image: langgenius/dify-api:2.0.0\n")
    monkeypatch.setenv("DOCKER_HOST", "unix:///definitely/not/a/docker.sock")
    snapshot = capture(tmp_path, base, override)
    assert snapshot.public_config["services.api.image_tag"] == "2.0.0"


def test_api_web_conflict_and_missing_compose_are_explicit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    compose = tmp_path / "compose.yaml"
    compose.write_text(
        "services:\n  api:\n    image: langgenius/dify-api:1.0.0\n  web:\n    image: langgenius/dify-web:2.0.0\n"
    )
    snapshot = capture(tmp_path, compose)
    assert snapshot.facts["dify.declared_version"].status is FactStatus.CONFLICTED
    assert snapshot.facts["dify.observed_version"].status is FactStatus.UNKNOWN
    monkeypatch.setattr(compose_module, "probe_compose", lambda: (_ for _ in ()).throw(CaptureError("compose_unavailable")))
    with pytest.raises(CaptureError, match="compose_unavailable"):
        capture(tmp_path, compose)


def test_profile_and_explicit_env_file_are_native_compose_inputs(tmp_path: Path) -> None:
    compose = tmp_path / "compose.yaml"
    env_file = tmp_path / "input.env"
    env_file.write_text("TAG=1.0.0\n")
    compose.write_text(
        "services:\n  api:\n    image: langgenius/dify-api:${TAG}\n  optional:\n    image: busybox:1.36\n    profiles: [optional]\n"
    )
    compose.write_text(
        "services:\n  api:\n    image: langgenius/dify-api:${TAG}\n  weaviate:\n    image: semitechnologies/weaviate:1.24.0\n    profiles: [optional]\n"
    )
    default = collect_snapshot(CaptureRequest(project_dir=tmp_path, compose_files=(compose,), env_files=(env_file,)))
    profiled = collect_snapshot(CaptureRequest(project_dir=tmp_path, compose_files=(compose,), env_files=(env_file,), profiles=("optional",)))
    assert default.facts["vector.ownership"].status is FactStatus.UNKNOWN
    assert profiled.facts["vector.ownership"].value == "bundled"


def test_implicit_project_env_is_disabled(tmp_path: Path) -> None:
    compose = tmp_path / "compose.yaml"
    implicit = tmp_path / ".env"
    implicit.write_text("TAG=CANARY_IMPLICIT_ENV\n")
    compose.write_text("services:\n  api:\n    image: langgenius/dify-api:${TAG:-1.0.0}\n")
    snapshot = collect_snapshot(CaptureRequest(project_dir=tmp_path, compose_files=(compose,)))
    assert snapshot.public_config["services.api.image_tag"] == "1.0.0"


@pytest.mark.parametrize("reserved", ["PATH", "LC_ALL", "HOME", "XDG_CONFIG_HOME", "COMPOSE_DISABLE_ENV_FILE", "DOCKER_HOST"])
def test_reserved_interpolation_variables_are_rejected(tmp_path: Path, reserved: str) -> None:
    compose = tmp_path / "compose.yaml"
    compose.write_text("services:\n  api:\n    image: langgenius/dify-api:${TAG:-1.0.0}\n")
    with pytest.raises(CaptureError, match="reserved_interpolation_variable"):
        collect_snapshot(CaptureRequest(project_dir=tmp_path, compose_files=(compose,), allowed_env={reserved: "malicious"}))


@pytest.mark.parametrize("allowed_env", [{"BAD-NAME": "x"}, {"TAG": 1}])
def test_interpolation_variable_names_and_values_are_validated(tmp_path: Path, allowed_env: dict[str, object]) -> None:
    compose = tmp_path / "compose.yaml"
    compose.write_text("services:\n  api:\n    image: langgenius/dify-api:${TAG:-1.0.0}\n")
    with pytest.raises(CaptureError, match="invalid_interpolation_variable"):
        collect_snapshot(CaptureRequest(project_dir=tmp_path, compose_files=(compose,), allowed_env=allowed_env))  # type: ignore[arg-type]
