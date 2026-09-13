import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "generate_p03_baselines.py"
SPEC = importlib.util.spec_from_file_location("p03_baselines", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def result(tag: str, attempt: int, digest: str = "same") -> dict[str, object]:
    return {"tag": tag, "attempt": attempt, "result": "ok", "public_config_sha256": digest}


def complete() -> list[dict[str, object]]:
    return [result(tag, number) for tag in MODULE.CANDIDATES for number in (1, 2)]


def test_complete_baselines_require_two_matching_successes_per_tag() -> None:
    assert MODULE.repeatable_complete_baselines(complete()) is True


def test_partial_failure_cannot_be_reported_as_repeatable() -> None:
    attempts = complete()
    attempts[1] = {"tag": "1.13.1", "attempt": 2, "result": "blocked_external"}
    assert MODULE.repeatable_complete_baselines(attempts) is False


def test_mismatched_repeated_digest_cannot_be_reported_as_repeatable() -> None:
    attempts = complete()
    attempts[3] = result("1.13.2", 2, "different")
    assert MODULE.repeatable_complete_baselines(attempts) is False
