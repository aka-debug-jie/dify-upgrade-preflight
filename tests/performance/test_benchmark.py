import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_medium_benchmark_writes_raw_samples_and_summary(tmp_path: Path) -> None:
    output = tmp_path / "medium.json"
    completed = subprocess.run(
        [sys.executable, "scripts/benchmark.py", "--profile", "medium", "--warmup", "0", "--runs", "1", "--output", str(output)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    value = json.loads(output.read_text())
    assert value["profile"] == "medium"
    assert len(value["samples"]) == 1
    assert value["summary"]["p95_seconds"] >= 0
    assert value["workload"]["service_count"] == 60
    assert value["workload"]["fact_count"] == 2000
    assert value["workload"]["rule_count"] == 250
