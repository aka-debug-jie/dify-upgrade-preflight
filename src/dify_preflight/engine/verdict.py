from dify_preflight.domain import DecisionInput, Verdict


def verdict_for(decision: DecisionInput) -> Verdict:
    if decision.fatal_error:
        return Verdict.ERROR
    if not decision.supported:
        return Verdict.UNSUPPORTED
    if decision.failed_blocker:
        return Verdict.BLOCKED
    if decision.required_unknown:
        return Verdict.INCOMPLETE
    return Verdict.NO_KNOWN_BLOCKERS


def exit_code_for(verdict: Verdict, has_warning: bool = False) -> int:
    if verdict is Verdict.NO_KNOWN_BLOCKERS:
        return 1 if has_warning else 0
    return {Verdict.BLOCKED: 2, Verdict.INCOMPLETE: 3, Verdict.UNSUPPORTED: 4, Verdict.ERROR: 5}[verdict]
