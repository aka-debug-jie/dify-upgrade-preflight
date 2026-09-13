#!/usr/bin/env python3
"""Generate only sanitized P03 candidate-baseline provenance from P00 evidence."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path

from dify_preflight.collect.compose import collect_snapshot, probe_compose
from dify_preflight.collect.safe_io import CaptureError
from dify_preflight.domain import CaptureRequest


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = {
    "1.13.1": "f943f1e39bfb357bb0bf4f04204b9efc5cac85dc",
    "1.13.2": "c8560bacb328ef27a3cdaad2175b11df8338120d",
    "1.13.3": "59639ca9b2ba2ba4b32b5feff5149cfc1ad0ba74",
}
RECOVERY_CANDIDATES = {
    "1.16.0": "5c6372d2f76d240265b92fd27c16bc772ffcb107",
    "1.16.1": "6f8ed69ee15f9a2e7189ca066275e973d091d1e9",
    "1.17.0": "09a855dcef24c0edc7431c46c0cfaa494481daf5",
    "1.17.1": "8387590ace4a094de812b7847fc6a4c3a27cd52b",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def attempt(tag: str, number: int, candidates: dict[str, str], source_root: Path) -> dict[str, object]:
    root = source_root / tag / "docker"
    compose = root / "docker-compose.yaml"
    started = time.monotonic()
    try:
        snapshot = collect_snapshot(CaptureRequest(project_dir=root, compose_files=(Path("docker-compose.yaml"),)))
    except CaptureError as error:
        result: dict[str, object] = {"result": "blocked_external", "error_category": error.code}
    else:
        public = dict(sorted(snapshot.public_config.items()))
        result = {
            "result": "ok",
            "public_config": public,
            "public_config_sha256": hashlib.sha256(
                json.dumps(public, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
        }
    return {
        "tag": tag,
        "attempt": number,
        "commit": candidates[tag],
        "compose_sha256": digest(compose),
        "elapsed_seconds": round(time.monotonic() - started, 4),
        **result,
    }


def repeatable_complete_baselines(attempts: list[dict[str, object]], candidates: dict[str, str] = CANDIDATES) -> bool:
    for tag in candidates:
        tag_attempts = [item for item in attempts if item["tag"] == tag]
        if len(tag_attempts) != 2 or any(item["result"] != "ok" for item in tag_attempts):
            return False
        digests = {item["public_config_sha256"] for item in tag_attempts}
        if len(digests) != 1:
            return False
    return len(attempts) == len(candidates) * 2


def main() -> int:
    parser = ArgumentParser()
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    parser.add_argument("--recovery", action="store_true")
    args = parser.parse_args()
    output = ROOT / "artifacts" / "P03" / args.run_id / "BASELINE_PROVENANCE.md"
    if output.exists():
        print(json.dumps({"error": "artifact_already_exists", "output": str(output.relative_to(ROOT))}))
        return 64
    candidates = RECOVERY_CANDIDATES if args.recovery else CANDIDATES
    source_root = (
        ROOT / "artifacts" / "P05" / "20260913T121622Z" / "upstream"
        if args.recovery
        else ROOT / "artifacts" / "P00" / "20260913T075059Z" / "upstream"
    )
    capability = probe_compose()
    attempts = [attempt(tag, number, candidates, source_root) for tag in candidates for number in (1, 2)]
    successful = [item for item in attempts if item["result"] == "ok"]
    repeatable = repeatable_complete_baselines(attempts, candidates)
    lines = [
        "# P03 candidate public-baseline provenance",
        "",
        "This record is generated from P00 immutable local source artifacts only. It does not approve a support edge, rule, or real Dify compatibility claim.",
        "",
        f"- generated_at: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
        f"- command: `{Path(sys.executable).relative_to(ROOT) if Path(sys.executable).is_relative_to(ROOT) else sys.executable} scripts/generate_p03_baselines.py`",
        f"- compose_version: {capability.version}",
        f"- compose_json_output: {capability.json_output}",
        "- interpolation_context: no user values; no implicit .env; no explicit environment variables",
        f"- source_track: {'P05 recovery cache materialization' if args.recovery else 'P00 fixed evidence'}",
        "- persisted_content: source identifiers, source hashes, result categories, and approved public fields only",
        "",
        "## Attempts",
        "",
        "```json",
        json.dumps(attempts, ensure_ascii=False, sort_keys=True, indent=2),
        "```",
        "",
        f"- repeatable_public_baselines: {str(repeatable).lower()}",
        "- outcome: candidate public baselines generated without a simplified YAML fallback."
        if repeatable
        else "- outcome: blocked_external because a fixed source could not pass P02's required safe preflight; no simplified YAML fallback was used.",
    ]
    output.parent.mkdir(parents=True, exist_ok=False)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output.relative_to(ROOT)), "successful_baseline_count": len(successful), "attempt_count": len(attempts)}))
    return 0 if repeatable else 2


if __name__ == "__main__":
    raise SystemExit(main())
