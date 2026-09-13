#!/usr/bin/env python3
"""Validate protected planning material without rewriting its baseline."""

import copy
import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def immutable_roadmap(roadmap: dict) -> dict:
    value = copy.deepcopy(roadmap)
    for key in ("current_phase", "updated_at", "product_implementation_started"):
        value.pop(key)
    for phase in value["phases"]:
        for item in [phase, *phase["tasks"]]:
            for key in ("status", "approval_ref", "artifacts"):
                item.pop(key, None)
    return value


def main() -> int:
    lock = json.loads((ROOT / "governance/acceptance-lock.json").read_text())
    mismatches = [name for name, expected in lock["files"].items() if sha256(ROOT / name) != expected]
    roadmap = yaml.safe_load((ROOT / "roadmap.yaml").read_text())
    roadmap_digest = hashlib.sha256(
        json.dumps(immutable_roadmap(roadmap), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if mismatches or roadmap_digest != lock["roadmap_immutable_sha256"]:
        print(json.dumps({"ok": False, "protected_file_mismatches": mismatches, "roadmap_immutable_matches": roadmap_digest == lock["roadmap_immutable_sha256"]}))
        return 1
    print(json.dumps({"ok": True, "protected_file_count": len(lock["files"]), "roadmap_immutable_matches": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
