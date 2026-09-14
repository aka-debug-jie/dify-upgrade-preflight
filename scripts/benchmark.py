#!/usr/bin/env python3
"""Record reproducible, synthetic P07 performance samples."""

from __future__ import annotations

import argparse
import json
import math
import platform
import resource
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from time import perf_counter

from dify_preflight.catalog.load import Catalog
from dify_preflight.collect.compose import collect_snapshot
from dify_preflight.domain import DeploymentSnapshot, Fact, FactOrigin, FactStatus, CaptureRequest, UpgradeRequest
from dify_preflight.engine.evaluate import evaluate


PROFILES = {
    "help": {"service_count": 0, "fact_count": 0, "rule_count": 0, "max_seconds": 0.5, "max_rss_mib": None},
    "medium": {"service_count": 60, "fact_count": 2_000, "rule_count": 250, "max_seconds": 2.0, "max_rss_mib": 200},
    "stress": {"service_count": 200, "fact_count": 10_000, "rule_count": 1_000, "max_seconds": 8.0, "max_rss_mib": 384},
    "compose": {"service_count": 60, "fact_count": 0, "rule_count": 0, "max_seconds": 10.0, "max_rss_mib": None},
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthetic P07 benchmark; no deployment input is read.")
    parser.add_argument("--profile", choices=tuple(PROFILES), required=True)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--reference-id")
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.warmup < 0 or args.runs < 1:
        parser.error("--warmup must be >= 0 and --runs must be >= 1")
    if args.worker:
        print(json.dumps(_worker(args.profile), sort_keys=True))
        return 0
    result = _measure(args.profile, args.warmup, args.runs, args.reference_id)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        sys.stdout.write(rendered)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(rendered)
    return 0 if result["summary"]["threshold_pass"] else 1


def _measure(profile: str, warmup: int, runs: int, reference_id: str | None) -> dict[str, object]:
    for _ in range(warmup):
        _run_child(profile)
    samples = [_run_child(profile) for _ in range(runs)]
    durations = sorted(float(sample["seconds"]) for sample in samples)
    rss_values = sorted(float(sample["peak_rss_mib"]) for sample in samples)
    config = PROFILES[profile]
    p95 = _percentile(durations, 0.95)
    max_rss = max(rss_values)
    threshold_pass = p95 <= config["max_seconds"] and (config["max_rss_mib"] is None or max_rss <= config["max_rss_mib"])
    return {
        "schema_version": "1.0",
        "profile": profile,
        "synthetic": True,
        "reference_environment_id": reference_id,
        "workload": {**config, "serialized_snapshot_bytes": samples[0]["serialized_snapshot_bytes"]},
        "environment": _environment(),
        "warmup_runs": warmup,
        "samples": samples,
        "summary": {
            "p50_seconds": _percentile(durations, 0.50),
            "p95_seconds": p95,
            "max_seconds": max(durations),
            "max_peak_rss_mib": max_rss,
            "threshold_pass": threshold_pass,
        },
    }


def _run_child(profile: str) -> dict[str, object]:
    if profile == "help":
        started = perf_counter()
        completed = subprocess.run(
            [str(Path(sys.executable).parent / "dify-preflight"), "--help"],
            capture_output=True,
            text=True,
            check=False,
            env={"PATH": str(Path(sys.executable).parent) + ":" + str(Path("/usr/bin")) + ":" + str(Path("/bin")), "LC_ALL": "C.UTF-8"},
        )
        if completed.returncode != 0:
            raise RuntimeError("benchmark_help_failed")
        return {
            "seconds": perf_counter() - started,
            "peak_rss_mib": 0.0,
            "exit_code": 0,
            "verdict": "HELP",
            "finding_results": {},
            "serialized_snapshot_bytes": 0,
        }
    started = perf_counter()
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--profile", profile, "--worker"],
        capture_output=True,
        text=True,
        check=False,
        env={"PATH": str(Path(sys.executable).parent) + ":" + str(Path("/usr/bin")) + ":" + str(Path("/bin")), "LC_ALL": "C.UTF-8"},
    )
    if completed.returncode != 0:
        raise RuntimeError("benchmark_worker_failed")
    value = json.loads(completed.stdout)
    if not isinstance(value, dict):
        raise RuntimeError("benchmark_worker_invalid")
    value["seconds"] = perf_counter() - started
    return value


def _worker(profile: str) -> dict[str, object]:
    started = perf_counter()
    if profile == "compose":
        snapshot = _compose_snapshot()
        report = {"verdict": "SNAPSHOT", "findings": []}
        serialized_bytes = len(json.dumps(snapshot.to_dict(), sort_keys=True, separators=(",", ":")).encode())
    else:
        snapshot, catalog = _core_workload(profile)
        report = evaluate(snapshot, UpgradeRequest("1.16.0", "1.16.1"), catalog)
        serialized_bytes = len(json.dumps(snapshot.to_dict(), sort_keys=True, separators=(",", ":")).encode())
    elapsed = perf_counter() - started
    self_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    child_rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024
    findings = report.get("findings", [])
    return {
        "seconds": elapsed,
        "peak_rss_mib": max(self_rss, child_rss),
        "exit_code": 0,
        "verdict": report["verdict"],
        "finding_results": dict(Counter(item["result"] for item in findings)),
        "serialized_snapshot_bytes": serialized_bytes,
    }


def _core_workload(profile: str) -> tuple[DeploymentSnapshot, Catalog]:
    config = PROFILES[profile]
    fact_count = int(config["fact_count"])
    rule_count = int(config["rule_count"])
    facts: dict[str, Fact] = {
        "dify.declared_version": Fact(FactStatus.KNOWN, "1.16.0", FactOrigin.DECLARED, "synthetic:benchmark", None)
    }
    for index in range(fact_count):
        status = (FactStatus.KNOWN, FactStatus.KNOWN, FactStatus.UNKNOWN)[index % 3]
        value = bool(index % 2) if status is FactStatus.KNOWN else None
        facts[f"benchmark.fact.{index:05d}"] = Fact(status, value, FactOrigin.SYNTHETIC, "synthetic:benchmark", None if status is FactStatus.KNOWN else "synthetic_unknown")
    snapshot = DeploymentSnapshot(
        "1.0", "deployment_snapshot", True, f"benchmark-{profile}",
        {"mode": "compose_declared", "collector_version": "benchmark", "compose_version": "2.33"},
        facts,
        {f"services.service-{index:03d}.present": True for index in range(int(config["service_count"]))},
        {},
        (),
    )
    rules = []
    for index in range(rule_count):
        first = f"benchmark.fact.{index % fact_count:05d}"
        second = f"benchmark.fact.{(index + 1) % fact_count:05d}"
        rules.append({
            "id": f"BENCH-R{index:04d}", "support_edge_ids": ["BENCH-EDGE"], "supersedes": [],
            "applies": {"fact": first, "op": "eq", "value": True},
            "assertion": {"fact": second, "op": "eq", "value": True},
            "severity": "warning", "evidence_refs": ["synthetic:benchmark"],
            "remediation": {"phase": "manual_review", "summary": "Synthetic benchmark only."},
        })
    edge = {
        "id": "BENCH-EDGE", "source_version": "1.16.0", "target_version": "1.16.1",
        "scope": "static_upgrade_plan", "deployment_profile": "compose", "compose_version": "2.33",
        "required_facts": ["dify.declared_version"], "rule_ids": [rule["id"] for rule in rules],
    }
    return snapshot, Catalog((edge,), tuple(rules), f"synthetic-{profile}", "synthetic")


def _compose_snapshot() -> DeploymentSnapshot:
    with tempfile.TemporaryDirectory(prefix="dify-preflight-p07-") as directory:
        root = Path(directory)
        services = "\n".join(f"  service-{index:03d}:\n    image: busybox:1.36" for index in range(60))
        compose = root / "compose.yaml"
        compose.write_text(f"services:\n  api:\n    image: langgenius/dify-api:1.16.0\n  web:\n    image: langgenius/dify-web:1.16.0\n{services}\n", encoding="utf-8")
        return collect_snapshot(CaptureRequest(project_dir=root, compose_files=(compose,)))


def _percentile(values: list[float], proportion: float) -> float:
    return values[math.ceil(len(values) * proportion) - 1]


def _environment() -> dict[str, object]:
    return {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "cpu_count": __import__("os").cpu_count(),
        "rss_unit": "MiB; Linux ru_maxrss KiB converted by /1024",
    }


if __name__ == "__main__":
    raise SystemExit(main())
