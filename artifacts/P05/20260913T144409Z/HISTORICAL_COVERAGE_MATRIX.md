# Historical capability traceability

The six scenarios below are a value-validation set. They are not automatically six blocker rules, and candidate evidence never counts as an approved product detector.

| Historical scenario | Original problem | Current mechanism | Status | Actual locations | Boundary |
| --- | --- | --- | --- | --- | --- |
| UID 1001 host-permission transition | Dify container user changed and host-mounted paths may require ownership/permission adjustment. | No P02/P03/P04/P05 mechanism observes host ownership or permission bits. Source evidence exists only as historical P00 material. | `UNCOVERED` | `sources/pinned.yaml; artifacts/P00/20260913T075059Z/DISCOVERY.md` | See status description; no unlisted detection claim. |
| 1.13.3 persistent Sandbox configuration path | Older deployments may need a persistent Sandbox configuration-path change. | P00 has source material, but no current public snapshot field, diff field, candidate rule, or case encodes the path transition. | `MANUAL_ONLY` | `sources/pinned.yaml; artifacts/P00/20260913T075059Z/DISCOVERY.md; sources/SOURCES.md` | See status description; no unlisted detection claim. |
| 1.14.x environment-file layout split | Official environment-file layout changed and local deployments can retain an obsolete layout. | P02 safely validates explicit Compose env_file paths and optional-file semantics, but no version-specific P05 rule determines that a layout difference blocks an exact upgrade edge. | `GENERIC_DETECTION` | `src/dify_preflight/collect/safe_io.py; tests/integration/test_compose_oracle.py; sources/SOURCES.md` | See status description; no unlisted detection claim. |
| 1.16.x legacy model-type migration | A pre-1.15 deployment may require legacy model-type migration for the 1.16.0 -> 1.16.1 candidate edge. | P05-R05 has fixed-key attestation support and proposed cases, but all case decisions and the rule remain unapproved. | `RULE_CANDIDATE` | `catalog/candidates/P05-recovery-candidates.yaml; tests/fixtures/pending_adjudication/P05-recovery-cases.yaml; src/dify_preflight/collect/redaction.py; tests/contract/test_recovery_snapshot.py` | See status description; no unlisted detection claim. |
| 1.17.1 bundled Weaviate staged upgrade | Existing bundled Weaviate data may require a staged path before the 1.17.0 -> 1.17.1 candidate edge. | P05-R06 has declared/attested facts and proposed cases, but it is not an approved rule or edge and static collection cannot verify stage completion. | `RULE_CANDIDATE` | `catalog/candidates/P05-recovery-candidates.yaml; tests/fixtures/pending_adjudication/P05-recovery-cases.yaml; src/dify_preflight/collect/redaction.py; artifacts/P05/20260913T144409Z/SOURCE_TRANSPORT_CLOSURE.json` | See status description; no unlisted detection claim. |
| Custom Compose conflict with target configuration | A local customisation can diverge from the target official configuration and needs a non-destructive comparison. | P03 compares registered public fields across baseline/local/target; it produces configuration classifications, not a version-specific blocker rule. | `GENERIC_DETECTION` | `src/dify_preflight/diff/three_way.py; tests/unit/test_three_way.py; src/dify_preflight/engine/evaluate.py; tests/unit/test_recovery_evaluator.py` | See status description; no unlisted detection claim. |

## Count

- `RULE_CANDIDATE`: 2 (legacy migration, bundled Weaviate).
- `GENERIC_DETECTION`: 2 (environment-file handling, three-way customisation diff).
- `MANUAL_ONLY`: 1 (persistent Sandbox path).
- `UNCOVERED`: 1 (UID 1001 host permission transition).
- `EVIDENCE_INSUFFICIENT`: 0 in this matrix; it remains available when a scenario has a proposed detector but insufficient evidence. None is relabelled merely to improve the count.

The generic categories report existing mechanics only. Neither produces a version-specific blocker without a separately approved exact edge and rule.
