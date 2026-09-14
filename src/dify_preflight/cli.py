from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path

import yaml

from dify_preflight.catalog.load import CatalogPolicy, load_catalog
from dify_preflight.collect.compose import collect_snapshot
from dify_preflight.collect.safe_io import CaptureError
from dify_preflight.demo import load_demo
from dify_preflight.domain import CaptureRequest, UpgradeRequest, Verdict
from dify_preflight.engine.evaluate import evaluate
from dify_preflight.engine.verdict import exit_code_for
from dify_preflight.report import render_json, render_markdown, render_text
from dify_preflight.snapshot_io import SnapshotInputError, load_snapshot, write_snapshot


class ContractArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(64, f"{self.prog}: error: {message}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = ContractArgumentParser(prog="dify-preflight", description="Offline, read-only Dify upgrade preflight")
    subparsers = parser.add_subparsers(dest="command", required=True)
    demo = subparsers.add_parser("demo", help="Run a synthetic-only contract demonstration")
    demo.add_argument("--case", choices=("blocked", "resolved", "unknown", "external"), default="blocked")
    demo.add_argument("--format", choices=("json", "text", "markdown"), default="text")

    snapshot = subparsers.add_parser("snapshot", help="Capture a redacted declared Compose snapshot")
    snapshot.add_argument("--project-dir", required=True)
    snapshot.add_argument("-f", "--file", dest="compose_files", action="append", required=True)
    snapshot.add_argument("--env-file", action="append", default=[])
    snapshot.add_argument("--profile", action="append", default=[])
    snapshot.add_argument("--allow-env", action="append", default=[])
    snapshot.add_argument("--catalog", required=True)
    snapshot.add_argument("--output", required=True)

    check = subparsers.add_parser("check", help="Evaluate a redacted snapshot using a local approved catalog")
    check.add_argument("--snapshot", required=True)
    check.add_argument("--proposed-snapshot")
    check.add_argument("--from", dest="source_version", required=True)
    check.add_argument("--to", dest="target_version", required=True)
    check.add_argument("--catalog", required=True)
    check.add_argument("--format", choices=("json", "text", "markdown"), default="text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        if args.command == "demo":
            report, code = load_demo(args.case)
            _emit(report, args.format)
            return code
        if args.command == "snapshot":
            return _snapshot(args)
        return _check(args)
    except KeyboardInterrupt:
        return 130


def _snapshot(args: argparse.Namespace) -> int:
    try:
        _approved_catalog(Path(args.catalog))
        allowed = {name: os.environ[name] for name in args.allow_env if name in os.environ}
        if len(allowed) != len(set(args.allow_env)):
            raise CaptureError("allowed_env_missing")
        request = CaptureRequest(
            project_dir=Path(args.project_dir), compose_files=tuple(Path(item) for item in args.compose_files),
            env_files=tuple(Path(item) for item in args.env_file), profiles=tuple(args.profile), allowed_env=allowed,
            output_path=Path(args.output),
        )
        captured = collect_snapshot(request)
        output = _snapshot_output_path(request)
        write_snapshot(captured, output)
        print(f"Snapshot written: {output.name}")
        return 0
    except (CaptureError, SnapshotInputError, OSError, ValueError):
        print("ERROR: snapshot_capture_failed", file=sys.stderr)
        return 5


def _snapshot_output_path(request: CaptureRequest) -> Path:
    assert request.output_path is not None
    return request.output_path if request.output_path.is_absolute() else request.project_dir / request.output_path


def _check(args: argparse.Namespace) -> int:
    try:
        snapshot = load_snapshot(Path(args.snapshot))
        proposed = load_snapshot(Path(args.proposed_snapshot)) if args.proposed_snapshot else None
        catalog = _approved_catalog(Path(args.catalog))
        report = evaluate(snapshot, UpgradeRequest(args.source_version, args.target_version, proposed_snapshot=proposed), catalog)
        _emit(report, args.format)
        warning = any(item.get("result") == "failed" and item.get("severity") == "warning" for item in report["findings"])
        return exit_code_for(Verdict(report["verdict"]), warning)
    except (SnapshotInputError, OSError, ValueError, yaml.YAMLError):
        return _emit_error(args.format, args.source_version, args.target_version, "input_or_catalog_invalid")


def _approved_catalog(path: Path):
    root = path.parent if path.name in {"approved", "support-matrix.yaml"} else path
    try:
        manifest = yaml.safe_load((root / "approval-manifest.yaml").read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("manifest")
        policy = CatalogPolicy(root=root, approved_sources=manifest["approved_sources"], approval_hashes=manifest["approval_hashes"], trust="owner_approved_local")
        return load_catalog(root / "support-matrix.yaml", policy)
    except (KeyError, OSError, TypeError, ValueError) as error:
        raise ValueError("catalog") from error


def _emit(report: dict[str, object], format_name: str) -> None:
    renderers = {"json": render_json, "text": render_text, "markdown": render_markdown}
    sys.stdout.write(renderers[format_name](report))


def _emit_error(format_name: str, source: str, target: str, code: str) -> int:
    if format_name == "json":
        sys.stdout.write(json.dumps({"schema_version": "1.0", "verdict": "ERROR", "source_version": source, "target_version": target, "error": code}, ensure_ascii=False, sort_keys=True) + "\n")
    else:
        print(f"ERROR: {code}", file=sys.stderr)
    return 5
