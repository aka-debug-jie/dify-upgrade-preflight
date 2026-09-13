import json
from importlib.resources import files
import subprocess
import sys
from pathlib import Path


def run_demo(case: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "dify_preflight", "demo", "--case", case, "--format", "json"],
        check=False,
        capture_output=True,
        text=True,
    )


def test_blocked_demo_matches_frozen_example() -> None:
    result = run_demo("blocked")
    assert result.returncode == 2
    assert result.stderr == ""
    assert json.loads(result.stdout) == json.loads(Path("examples/synthetic_report.json").read_text())


def test_packaged_synthetic_inputs_match_the_frozen_examples() -> None:
    for name in ("synthetic_snapshot.json", "synthetic_rule.yaml", "synthetic_report.json"):
        packaged = (files("dify_preflight") / "data" / name).read_bytes()
        assert packaged == (Path("examples") / name).read_bytes()


def test_demo_exercises_pass_unknown_and_not_applicable() -> None:
    expected = {"resolved": (0, "NO_KNOWN_BLOCKERS"), "unknown": (3, "INCOMPLETE"), "external": (0, "NO_KNOWN_BLOCKERS")}
    for case, (code, verdict) in expected.items():
        result = run_demo(case)
        report = json.loads(result.stdout)
        assert result.returncode == code
        assert report["synthetic"] is True
        assert report["verdict"] == verdict


def test_help_and_invalid_arguments_use_contract_exit_codes() -> None:
    help_result = subprocess.run([sys.executable, "-m", "dify_preflight", "--help"], check=False, capture_output=True, text=True)
    invalid_result = subprocess.run([sys.executable, "-m", "dify_preflight", "demo", "--case", "nope"], check=False, capture_output=True, text=True)
    assert help_result.returncode == 0
    assert invalid_result.returncode == 64
