from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Mapping, TypeAlias, TypedDict


Scalar: TypeAlias = str | int | float | bool
PublicConfig: TypeAlias = Mapping[str, object]


class _Missing:
    def __repr__(self) -> str:
        return "MISSING"


MISSING = _Missing()


class TruthValue(str, Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"


class FactStatus(str, Enum):
    KNOWN = "known"
    UNKNOWN = "unknown"
    CONFLICTED = "conflicted"


class FactOrigin(str, Enum):
    DECLARED = "declared"
    OBSERVED = "observed"
    ATTESTED = "attested"
    DERIVED = "derived"
    SYNTHETIC = "synthetic"


class Verdict(str, Enum):
    NO_KNOWN_BLOCKERS = "NO_KNOWN_BLOCKERS"
    BLOCKED = "BLOCKED"
    INCOMPLETE = "INCOMPLETE"
    UNSUPPORTED = "UNSUPPORTED"
    ERROR = "ERROR"


class FindingResult(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class FindingSeverity(str, Enum):
    BLOCKER = "blocker"
    WARNING = "warning"
    INFO = "info"


class ConfigChangeKind(str, Enum):
    UNCHANGED = "unchanged"
    UPSTREAM_ONLY = "upstream_only"
    LOCAL_ONLY = "local_only"
    SAME_CHANGE = "same_change"
    DIVERGENT_CHANGE = "divergent_change"
    UNKNOWN_COMPARISON = "unknown_comparison"


class Comparability(str, Enum):
    PUBLIC = "public"
    RELATION_ONLY = "relation_only"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Fact:
    status: FactStatus
    value: Scalar | None
    origin: FactOrigin
    source_ref: str
    reason: str | None


@dataclass(frozen=True)
class DecisionInput:
    fatal_error: bool
    supported: bool
    failed_blocker: bool
    required_unknown: bool
    has_warning: bool


@dataclass(frozen=True)
class CaptureRequest:
    project_dir: Path
    compose_files: tuple[Path, ...]
    env_files: tuple[Path, ...] = ()
    profiles: tuple[str, ...] = ()
    allowed_env: Mapping[str, str] = field(default_factory=dict)
    attestations: Mapping[str, bool] = field(default_factory=dict)
    output_path: Path | None = None


@dataclass(frozen=True)
class DeploymentSnapshot:
    schema_version: str
    kind: str
    synthetic: bool
    snapshot_id: str
    capture: dict[str, object]
    facts: Mapping[str, Fact]
    public_config: Mapping[str, Scalar | None]
    private_relations: Mapping[str, bool | None]
    gaps: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "synthetic": self.synthetic,
            "snapshot_id": self.snapshot_id,
            "capture": self.capture,
            "facts": {
                name: {
                    "status": fact.status.value,
                    "value": fact.value,
                    "origin": fact.origin.value,
                    "source_ref": fact.source_ref,
                    "reason": fact.reason,
                }
                for name, fact in self.facts.items()
            },
            "public_config": self.public_config,
            "private_relations": self.private_relations,
            "gaps": list(self.gaps),
        }


@dataclass(frozen=True)
class UpgradeRequest:
    source_version: str
    target_version: str
    scope: str = "static_upgrade_plan"
    proposed_snapshot: DeploymentSnapshot | None = None


@dataclass(frozen=True)
class ConfigChange:
    path: str
    kind: ConfigChangeKind
    comparability: Comparability
    base: object
    local: object
    target: object
    proposed: object
    reason: str


class Report(TypedDict):
    schema_version: str
    synthetic: bool
    scope: str
    source_version: str
    target_version: str
    verdict: str
    findings: list[dict[str, object]]
    changes: list[dict[str, object]]
    coverage: dict[str, object]
    provenance: dict[str, object]
    decision_digest: str
