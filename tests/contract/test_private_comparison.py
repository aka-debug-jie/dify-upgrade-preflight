from dify_preflight.diff.three_way import compare_three_way
from dify_preflight.domain import Comparability, ConfigChangeKind


def test_d07_redacted_values_are_never_equal_evidence() -> None:
    path = "services.api.image_tag"
    change = compare_three_way({path: "REDACTED"}, {path: "REDACTED"}, {path: "REDACTED"})[0]
    assert change.kind is ConfigChangeKind.UNKNOWN_COMPARISON
    assert change.comparability is Comparability.UNKNOWN
    assert change.reason == "redacted_value_is_not_comparable"


def test_redaction_nested_in_registered_list_is_not_compared() -> None:
    path = "services.api.ports"
    change = compare_three_way({path: [{"target": 80, "published": "REDACTED"}]}, {path: [{"target": 80, "published": "REDACTED"}]}, {path: [{"target": 80, "published": "REDACTED"}]})[0]
    assert change.kind is ConfigChangeKind.UNKNOWN_COMPARISON
