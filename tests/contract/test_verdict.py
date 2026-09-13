import json
from pathlib import Path

from dify_preflight.domain import DecisionInput
from dify_preflight.engine.verdict import exit_code_for, verdict_for


def test_all_frozen_verdict_combinations() -> None:
    cases = json.loads(Path("specs/fixtures/verdict-cases.json").read_text())["cases"]
    assert len(cases) == 32
    for case in cases:
        decision = DecisionInput(
            fatal_error=case["fatal_error"],
            supported=case["supported"],
            failed_blocker=case["failed_blocker"],
            required_unknown=case["required_unknown"],
            has_warning=case["has_warning"],
        )
        verdict = verdict_for(decision)
        assert verdict.value == case["expected_verdict"]
        assert exit_code_for(verdict, case["has_warning"]) == case["expected_exit_code"]
