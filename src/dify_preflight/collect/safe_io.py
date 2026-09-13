import os
import stat
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml
from yaml.events import AliasEvent


MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
MAX_FILES = 100
MAX_ALIASES = 64


class CaptureError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class DuplicateKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        explicit_keys: set[Any] = set()
        for key_node, value_node in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                continue
            key = self.construct_object(key_node, deep=deep)
            if key in explicit_keys:
                raise CaptureError("duplicate_key")
            explicit_keys.add(key)
        self.flatten_mapping(node)
        return super().construct_mapping(node, deep=deep)


def project_path(project_dir: Path, path: Path) -> Path:
    root = project_dir.resolve(strict=True)
    candidate = path if path.is_absolute() else root / path
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise CaptureError("path_outside_project") from error
    try:
        mode = candidate.lstat().st_mode
    except FileNotFoundError as error:
        raise CaptureError("input_missing") from error
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise CaptureError("input_not_regular_file")
    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise CaptureError("path_outside_project") from error
    return resolved


def read_checked(project_dir: Path, paths: Iterable[Path]) -> dict[Path, str]:
    checked: dict[Path, str] = {}
    total = 0
    for path in paths:
        resolved = project_path(project_dir, path)
        if resolved in checked:
            continue
        if len(checked) >= MAX_FILES:
            raise CaptureError("too_many_files")
        size = resolved.stat().st_size
        if size > MAX_FILE_BYTES:
            raise CaptureError("file_too_large")
        total += size
        if total > MAX_TOTAL_BYTES:
            raise CaptureError("input_too_large")
        try:
            checked[resolved] = resolved.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise CaptureError("invalid_utf8") from error
    return checked


def parse_compose_preflight(text: str) -> dict[str, Any]:
    try:
        aliases = sum(isinstance(event, AliasEvent) for event in yaml.parse(text, Loader=yaml.SafeLoader))
        if aliases > MAX_ALIASES:
            raise CaptureError("yaml_alias_limit")
        document = yaml.load(text, Loader=DuplicateKeyLoader)
    except CaptureError:
        raise
    except yaml.YAMLError as error:
        raise CaptureError("invalid_yaml") from error
    if not isinstance(document, dict):
        raise CaptureError("invalid_compose_document")
    _reject_unsupported(document)
    return document


def referenced_env_files(document: dict[str, Any], compose_path: Path) -> list[tuple[Path, bool]]:
    references: list[tuple[Path, bool]] = []
    services = document.get("services", {})
    if not isinstance(services, dict):
        raise CaptureError("invalid_services")
    for service in services.values():
        if not isinstance(service, dict) or "env_file" not in service:
            continue
        values = service["env_file"]
        values = values if isinstance(values, list) else [values]
        for value in values:
            if isinstance(value, str):
                references.append((compose_path.parent / value, True))
            elif isinstance(value, dict) and isinstance(value.get("path"), str):
                references.append((compose_path.parent / value["path"], value.get("required", True) is not False))
            else:
                raise CaptureError("invalid_env_file")
    return references


def _reject_unsupported(value: Any) -> None:
    if isinstance(value, dict):
        if "include" in value or "extends" in value:
            raise CaptureError("unsupported_compose_feature")
        for nested in value.values():
            _reject_unsupported(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_unsupported(nested)
