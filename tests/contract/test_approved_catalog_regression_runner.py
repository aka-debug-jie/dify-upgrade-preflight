import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_approved_catalog_regression_runner_loads_owner_catalog(tmp_path: Path) -> None:
    output = tmp_path / "approved-regression"
    completed = subprocess.run(
        [sys.executable, "scripts/run_p05_approved_catalog_regression.py", "--output-dir", str(output)],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": "src"},
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((output / "RUN_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["catalog_trust"] == "owner_approved_local"
    assert manifest["development_count"] == 30
    assert manifest["heldout_count"] == 9
    assert manifest["false_safe"] == 0
    assert manifest["extra_blocker"] == 0
    assert manifest["heldout_mismatch"] == 0
    assert manifest["wrong_unknown"] == 0
    assert manifest["wrong_unsupported"] == 0
