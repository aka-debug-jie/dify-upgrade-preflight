import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_worker_queue_runner_uses_production_evaluator_and_keeps_heldout_oracle_separate(tmp_path: Path) -> None:
    output = tmp_path / "worker-run"
    completed = subprocess.run(
        [sys.executable, "scripts/run_p05_worker_queue_fixtures.py", "--output-dir", str(output)],
        cwd=ROOT,
        env={**__import__("os").environ, "PYTHONPATH": "src"},
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((output / "RUN_MANIFEST.json").read_text(encoding="utf-8"))
    heldout = json.loads((output / "HELDOUT_RESULTS.json").read_text(encoding="utf-8"))
    assert manifest["evaluator"] == "dify_preflight.engine.evaluate.evaluate"
    assert manifest["development_count"] == 8
    assert manifest["heldout_count"] == 3
    assert manifest["false_safe_count"] == 0
    assert manifest["extra_blocker_count"] == 0
    assert manifest["wrong_unknown_count"] == 0
    assert manifest["wrong_not_applicable_count"] == 0
    assert manifest["wrong_unsupported_count"] == 0
    assert all(item["passed"] for item in heldout["results"])
