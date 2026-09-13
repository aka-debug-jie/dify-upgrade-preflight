import json
import os
from io import BytesIO
from pathlib import Path

import pytest

from dify_preflight.collect.compose import MAX_OUTPUT_BYTES, _bounded_output, collect_snapshot
from dify_preflight.collect.safe_io import CaptureError
from dify_preflight.domain import CaptureRequest


def request(project_dir: Path, compose: Path, **kwargs: object) -> CaptureRequest:
    return CaptureRequest(project_dir=project_dir, compose_files=(compose,), **kwargs)


@pytest.mark.parametrize(
    "contents",
    [
        "services:\n  api:\n    image: x\n    environment:\n      X: one\n      X: two\n",
        "include: https://example.invalid/compose.yml\nservices: {}\n",
        "services:\n  api:\n    extends: external.yml\n",
        "services:\n  api:\n    image: !unsafe x\n",
    ],
)
def test_rejects_unsafe_yaml_before_compose(tmp_path: Path, contents: str) -> None:
    compose = tmp_path / "compose.yaml"
    compose.write_text(contents)
    with pytest.raises(CaptureError):
        collect_snapshot(request(tmp_path, compose))


def test_rejects_symlink_and_fifo_inputs(tmp_path: Path) -> None:
    target = tmp_path / "outside.yaml"
    target.write_text("services: {}\n")
    link = tmp_path / "compose.yaml"
    link.symlink_to(target)
    with pytest.raises(CaptureError):
        collect_snapshot(request(tmp_path, link))

    fifo = tmp_path / "compose.fifo"
    os.mkfifo(fifo)
    with pytest.raises(CaptureError):
        collect_snapshot(request(tmp_path, fifo))


def test_rejects_paths_and_env_files_outside_project(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.env"
    outside.write_text("X=outside\n")
    compose = tmp_path / "compose.yaml"
    compose.write_text("services:\n  api:\n    image: langgenius/dify-api:1.0.0\n    env_file: ../outside.env\n")
    with pytest.raises(CaptureError):
        collect_snapshot(request(tmp_path, compose))
    with pytest.raises(CaptureError):
        collect_snapshot(CaptureRequest(project_dir=tmp_path, compose_files=(outside,)))


def test_rejects_alias_bomb_before_native_compose(tmp_path: Path) -> None:
    compose = tmp_path / "compose.yaml"
    aliases = "\n".join(f"  service{i}: *base" for i in range(65))
    compose.write_text(f"base: &base {{image: busybox:1.36}}\nservices:\n{aliases}\n")
    with pytest.raises(CaptureError):
        collect_snapshot(request(tmp_path, compose))


def test_accepts_bounded_merge_and_checks_merged_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / "inside.env"
    env_file.write_text("SAFE=1\n")
    compose = tmp_path / "compose.yaml"
    compose.write_text(
        "x-base: &base\n  image: langgenius/dify-api:1.0.0\n  env_file: inside.env\nservices:\n  api:\n    <<: *base\n"
    )
    assert collect_snapshot(request(tmp_path, compose)).facts["dify.declared_version"].value == "1.0.0"

    compose.write_text(
        "x-base: &base\n  image: langgenius/dify-api:1.0.0\nservices:\n  api:\n    <<: *base\n    image: langgenius/dify-api:2.0.0\n"
    )
    assert collect_snapshot(request(tmp_path, compose)).facts["dify.declared_version"].value == "2.0.0"

    outside = tmp_path.parent / "outside-merged.env"
    outside.write_text("SECRET=CANARY_MERGED_ESCAPE\n")
    compose.write_text(
        "x-base: &base\n  image: langgenius/dify-api:1.0.0\n  env_file: ../outside-merged.env\nservices:\n  api:\n    <<: *base\n"
    )
    with pytest.raises(CaptureError, match="path_outside_project"):
        collect_snapshot(request(tmp_path, compose))


def test_rejects_output_collision_and_does_not_leak_unknown_environment_values(tmp_path: Path) -> None:
    canary = "CANARY_P02_DO_NOT_PERSIST"
    compose = tmp_path / "compose.yaml"
    compose.write_text(
        f"services:\n  api:\n    image: langgenius/dify-api:1.0.0\n    environment:\n      PRIVATE_UNKNOWN: {canary}\n"
    )
    with pytest.raises(CaptureError):
        collect_snapshot(request(tmp_path, compose, output_path=compose))
    with pytest.raises(CaptureError):
        collect_snapshot(request(tmp_path, compose, output_path=tmp_path.parent / "outside.json"))

    snapshot = collect_snapshot(request(tmp_path, compose))
    assert canary not in json.dumps(snapshot.to_dict())
    assert snapshot.private_relations == {
        "agent_api_token_is_published_default": None,
        "agent_api_tokens_same_as_peer": None,
    }


def test_command_text_is_not_executed(tmp_path: Path) -> None:
    sentinel = tmp_path / "executed"
    compose = tmp_path / "compose.yaml"
    compose.write_text(
        f"services:\n  api:\n    image: langgenius/dify-api:1.0.0\n    command: ['sh', '-c', 'touch {sentinel}']\n"
    )
    collect_snapshot(request(tmp_path, compose))
    assert not sentinel.exists()


def test_compose_failure_does_not_echo_canary(tmp_path: Path) -> None:
    canary = "CANARY_P02_COMPOSE_STDERR"
    compose = tmp_path / "compose.yaml"
    compose.write_text(f"services:\n  api:\n    image: {canary}\n    ports: invalid-port\n")
    with pytest.raises(CaptureError) as error:
        collect_snapshot(request(tmp_path, compose))
    assert canary not in str(error.value)


def test_output_limit_rejects_before_preserving_oversized_output() -> None:
    class Process:
        stdout = BytesIO(b"x" * (MAX_OUTPUT_BYTES + 1))
        stderr = BytesIO()

        @staticmethod
        def poll() -> int:
            return 0

    with pytest.raises(OverflowError):
        _bounded_output(Process())
