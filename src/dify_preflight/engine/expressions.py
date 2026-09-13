import re
from collections.abc import Mapping
from typing import Any

from dify_preflight.domain import Fact, FactStatus, TruthValue


def evaluate_expression(expression: Mapping[str, Any], facts: Mapping[str, Fact]) -> TruthValue:
    if "all" in expression:
        values = [evaluate_expression(item, facts) for item in expression["all"]]
        return TruthValue.FALSE if TruthValue.FALSE in values else (TruthValue.UNKNOWN if TruthValue.UNKNOWN in values else TruthValue.TRUE)
    if "any" in expression:
        values = [evaluate_expression(item, facts) for item in expression["any"]]
        return TruthValue.TRUE if TruthValue.TRUE in values else (TruthValue.UNKNOWN if TruthValue.UNKNOWN in values else TruthValue.FALSE)
    if "not" in expression:
        value = evaluate_expression(expression["not"], facts)
        return {TruthValue.TRUE: TruthValue.FALSE, TruthValue.FALSE: TruthValue.TRUE, TruthValue.UNKNOWN: TruthValue.UNKNOWN}[value]

    fact = facts.get(expression["fact"])
    if fact is None or fact.status is not FactStatus.KNOWN:
        return TruthValue.UNKNOWN
    comparison = _compare(fact.value, expression["op"], expression["value"])
    return TruthValue.UNKNOWN if comparison is None else TruthValue.TRUE if comparison else TruthValue.FALSE


def _compare(actual: object, operator: str, expected: object) -> bool | None:
    if operator == "eq":
        return actual == expected
    if operator == "ne":
        return actual != expected
    if operator == "in":
        return actual in expected
    if operator.startswith("version_"):
        left, right = _version_key(str(actual)), _version_key(str(expected))
        if left is None or right is None:
            return None
        return {"version_lt": left < right, "version_lte": left <= right, "version_gt": left > right, "version_gte": left >= right}[operator]
    raise ValueError(f"unsupported synthetic expression operator: {operator}")


def _version_key(value: str) -> tuple[int, ...] | None:
    if not re.fullmatch(r"\d+(?:\.\d+)*(?:[-+][0-9A-Za-z.-]+)?", value):
        return None
    core = value.split("-", 1)[0].split("+", 1)[0]
    return tuple(int(part) for part in core.split("."))
