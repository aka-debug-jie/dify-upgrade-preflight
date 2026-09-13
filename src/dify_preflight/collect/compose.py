import json
import os
import signal
import subprocess
import threading
import re
from dataclasses import dataclass
from pathlib import Path
from time import monotonic, sleep
from typing import Any

from dify_preflight.collect.redaction import declared_snapshot
from dify_preflight.collect.safe_io import CaptureError, parse_compose_preflight, project_path, read_checked, referenced_env_files
from dify_preflight.domain import CaptureRequest, DeploymentSnapshot


COMPOSE_TIMEOUT_SECONDS = 15
TOTAL_TIMEOUT_SECONDS = 30
MAX_OUTPUT_BYTES = 32 * 1024 * 1024
COMPOSE_EXECUTABLE = "docker"
CONTROL_ENV = {"PATH", "LC_ALL", "HOME", "XDG_CONFIG_HOME", "PYTHONPATH", "VIRTUAL_ENV", "BASH_ENV", "ENV"}
ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class ComposeCapability:
    version: str
    json_output: bool


def probe_compose(executable: str = "docker") -> ComposeCapability:
    version = _run([executable, "compose", "version", "--short"], {}).strip()
    help_text = _run([executable, "compose", "config", "--help"], {})
    if "--format" not in help_text or "json" not in help_text:
        raise CaptureError("compose_json_unsupported")
    return ComposeCapability(version=version, json_output=True)


def collect_snapshot(request: CaptureRequest) -> DeploymentSnapshot:
    started = monotonic()
    root = request.project_dir.resolve(strict=True)
    compose_paths = tuple(project_path(root, path) for path in request.compose_files)
    if not compose_paths:
        raise CaptureError("compose_file_required")
    explicit_env = tuple(project_path(root, path) for path in request.env_files)
    if request.output_path is not None:
        output = request.output_path if request.output_path.is_absolute() else root / request.output_path
        try:
            output.resolve(strict=False).relative_to(root)
        except ValueError as error:
            raise CaptureError("unsafe_output_path") from error
        if output in {*compose_paths, *explicit_env} or output.exists():
            raise CaptureError("unsafe_output_path")

    compose_text = read_checked(root, compose_paths)
    referenced: list[tuple[Path, bool]] = []
    for path, text in compose_text.items():
        referenced.extend(referenced_env_files(parse_compose_preflight(text), path))
    required_references = [path for path, required in referenced if required]
    optional_references = [path for path, required in referenced if not required and path.exists()]
    read_checked(root, (*explicit_env, *required_references, *optional_references))
    if monotonic() - started > TOTAL_TIMEOUT_SECONDS:
        raise CaptureError("capture_timeout")

    capability = probe_compose()
    model = _compose_config_prevalidated(request, root, compose_paths, explicit_env)
    if monotonic() - started > TOTAL_TIMEOUT_SECONDS:
        raise CaptureError("capture_timeout")
    try:
        return declared_snapshot(model, capability.version, request.attestations)
    except ValueError as error:
        raise CaptureError("invalid_attestation") from error


def _compose_config_prevalidated(request: CaptureRequest, root: Path, compose_paths: tuple[Path, ...], env_paths: tuple[Path, ...]) -> dict[str, Any]:
    args = [COMPOSE_EXECUTABLE, "compose", "--project-directory", str(root)]
    for path in compose_paths:
        args.extend(("-f", str(path)))
    for path in env_paths:
        args.extend(("--env-file", str(path)))
    for profile in request.profiles:
        args.extend(("--profile", profile))
    args.extend(("config", "--format", "json"))
    raw = _run(args, request.allowed_env)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise CaptureError("compose_json_invalid") from error
    if not isinstance(value, dict):
        raise CaptureError("compose_json_invalid")
    return value


def _run(args: list[str], allowed_env: dict[str, str] | Any) -> str:
    interpolation = dict(allowed_env)
    _validate_interpolation_names(interpolation)
    environment = {"PATH": os.environ.get("PATH", os.defpath), "LC_ALL": "C.UTF-8"}
    environment.update(interpolation)
    environment.update({"PATH": os.environ.get("PATH", os.defpath), "LC_ALL": "C.UTF-8", "COMPOSE_DISABLE_ENV_FILE": "1"})
    try:
        process = subprocess.Popen(
            args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            shell=False,
            env=environment,
            start_new_session=True,
        )
    except FileNotFoundError as error:
        raise CaptureError("compose_unavailable") from error
    try:
        stdout, stderr = _bounded_output(process)
    except TimeoutError as error:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        raise CaptureError("compose_timeout") from error
    except OverflowError as error:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        raise CaptureError("compose_output_too_large")
    if process.returncode != 0:
        raise CaptureError("compose_failed")
    try:
        return stdout.decode("utf-8")
    except UnicodeDecodeError as error:
        raise CaptureError("compose_output_invalid_utf8") from error


def _validate_interpolation_names(values: dict[str, str]) -> None:
    for name, value in values.items():
        if not isinstance(name, str) or not ENV_NAME.fullmatch(name) or not isinstance(value, str):
            raise CaptureError("invalid_interpolation_variable")
        if name in CONTROL_ENV or name.startswith(("COMPOSE_", "DOCKER_", "LD_", "DYLD_")):
            raise CaptureError("reserved_interpolation_variable")


def _bounded_output(process: subprocess.Popen[bytes]) -> tuple[bytes, bytes]:
    stdout, stderr = bytearray(), bytearray()
    lock = threading.Lock()
    exceeded = threading.Event()

    def drain(stream: Any, destination: bytearray) -> None:
        while chunk := stream.read(64 * 1024):
            with lock:
                if len(stdout) + len(stderr) + len(chunk) > MAX_OUTPUT_BYTES:
                    exceeded.set()
                    return
                destination.extend(chunk)

    threads = [threading.Thread(target=drain, args=(process.stdout, stdout)), threading.Thread(target=drain, args=(process.stderr, stderr))]
    for thread in threads:
        thread.start()
    deadline = monotonic() + COMPOSE_TIMEOUT_SECONDS
    while process.poll() is None:
        if exceeded.is_set():
            raise OverflowError
        if monotonic() > deadline:
            raise TimeoutError
        sleep(0.01)
    for thread in threads:
        thread.join()
    if exceeded.is_set():
        raise OverflowError
    return bytes(stdout), bytes(stderr)
