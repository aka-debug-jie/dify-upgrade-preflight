import subprocess
import sys
import tarfile
import venv
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_wheel_and_sdist_install_in_a_fresh_virtualenv(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    built = subprocess.run(
        [sys.executable, "-m", "build", "--outdir", str(dist)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert built.returncode == 0, built.stderr
    wheel = next(dist.glob("*.whl"))
    sdist = next(dist.glob("*.tar.gz"))
    _assert_public_package_contents(wheel, sdist)

    environment = tmp_path / "installed"
    venv.EnvBuilder(with_pip=True).create(environment)
    pip = environment / "bin" / "pip"
    executable = environment / "bin" / "dify-preflight"
    installed = subprocess.run([str(pip), "install", str(wheel)], capture_output=True, text=True, check=False)
    assert installed.returncode == 0, installed.stderr
    help_result = subprocess.run([str(executable), "--help"], capture_output=True, text=True, check=False)
    demo_result = subprocess.run([str(executable), "demo", "--case", "blocked", "--format", "json"], capture_output=True, text=True, check=False)
    check_result = subprocess.run(
        [
            str(executable), "check", "--snapshot", str(ROOT / "examples/approved_edge_a/current.json"),
            "--proposed-snapshot", str(ROOT / "examples/approved_edge_a/proposed-blocked.json"),
            "--from", "1.16.0", "--to", "1.16.1", "--catalog", str(ROOT / "catalog"), "--format", "json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert help_result.returncode == 0
    assert "snapshot" in help_result.stdout and "check" in help_result.stdout
    assert demo_result.returncode == 2
    assert check_result.returncode == 2


def _assert_public_package_contents(wheel: Path, sdist: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        wheel_names = archive.namelist()
    with tarfile.open(sdist) as archive:
        sdist_names = archive.getnames()
    forbidden = ("artifacts/", ".venv/", ".cache/", "catalog/candidates/", "sources/pinned.yaml", ".env", "LOCAL_ENVIRONMENT.md")
    for names in (wheel_names, sdist_names):
        assert not any(any(item.endswith(marker) or f"/{marker}" in item for marker in forbidden) for item in names)
