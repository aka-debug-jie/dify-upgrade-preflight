from dify_preflight.domain import Fact, FactOrigin, FactStatus, TruthValue
from dify_preflight.engine.expressions import evaluate_expression


def test_known_false_is_not_unknown() -> None:
    facts = {
        "known_false": Fact(FactStatus.KNOWN, False, FactOrigin.SYNTHETIC, "test", None),
        "unknown": Fact(FactStatus.UNKNOWN, None, FactOrigin.SYNTHETIC, "test", "not supplied"),
    }

    assert evaluate_expression({"fact": "known_false", "op": "eq", "value": True}, facts) is TruthValue.FALSE
    assert evaluate_expression({"fact": "unknown", "op": "eq", "value": True}, facts) is TruthValue.UNKNOWN


def test_three_valued_boolean_operators() -> None:
    facts = {
        "true": Fact(FactStatus.KNOWN, True, FactOrigin.SYNTHETIC, "test", None),
        "false": Fact(FactStatus.KNOWN, False, FactOrigin.SYNTHETIC, "test", None),
        "unknown": Fact(FactStatus.UNKNOWN, None, FactOrigin.SYNTHETIC, "test", "not supplied"),
    }

    assert evaluate_expression({"all": [{"fact": "false", "op": "eq", "value": True}, {"fact": "unknown", "op": "eq", "value": True}]}, facts) is TruthValue.FALSE
    assert evaluate_expression({"any": [{"fact": "true", "op": "eq", "value": True}, {"fact": "unknown", "op": "eq", "value": True}]}, facts) is TruthValue.TRUE
    assert evaluate_expression({"not": {"fact": "unknown", "op": "eq", "value": True}}, facts) is TruthValue.UNKNOWN


def test_version_comparison_is_not_lexical() -> None:
    facts = {"version": Fact(FactStatus.KNOWN, "1.10", FactOrigin.SYNTHETIC, "test", None)}
    assert evaluate_expression({"fact": "version", "op": "version_gt", "value": "1.9"}, facts) is TruthValue.TRUE


def test_unparseable_version_is_unknown() -> None:
    facts = {"version": Fact(FactStatus.KNOWN, "latest", FactOrigin.SYNTHETIC, "test", None)}
    assert evaluate_expression({"fact": "version", "op": "version_gt", "value": "1.9"}, facts) is TruthValue.UNKNOWN
