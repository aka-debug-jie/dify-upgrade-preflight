# P05 owner adjudication pack

This pack is for owner decisions only. Every candidate, expectation, severity and recommendation below is non-executable until an owner records a decision against an unchanged review object. `owner_decision` remains null throughout this run.

## Global blockers

- 33 pending cases have no independent adjudication or heldout split.
- P05-R02, R03 and R04 have candidate/implementation fact-semantic mismatches listed below.
- No candidate edge or source set is approved; the product catalog remains empty and untrusted.
- Transport receipts are fresh, but source correctness and rule applicability still require owner evidence review.

## P05-R01 — Agent API authentication uses the published development default

- **Exact edge:** `1.16.0 -> 1.16.1` (`P05-EDGE-A`), candidate only.
- **Fixed evidence:** `P05.S004`, `P05.S005`, `P05.S006`. P05.S004=937fb34a20b5c023c509cbb950406eadec69b24f69d728c34f8dd7537adab623 P05.S005=aba772e012fd829499a663532b22ff3521096105f01ed9222eeb02a956a9ff3b P05.S006=6c37d8de55cb54d56d09b8a18512c96040809f687eeb59f5db0a4ab119004234
- **Applies semantics:** Proposed only: exact edge P05-EDGE-A and a declared agent backend.
- **Assertion semantics:** Proposed only: `private.agent_api_token_is_published_default` is false.
- **Candidate required facts:** `agent_backend.declared`, `private.agent_api_token_is_published_default`.
- **Fact origin:** agent backend: declared; token-default relation: derived in memory only.
- **Version boundary:** P05-EDGE-A only (1.16.0 -> 1.16.1).
- **Severity / phase:** blocker (proposed); before_upgrade (proposed).
- **Known counterexamples:** Non-default token passes; unavailable relation is UNKNOWN; absent backend is not applicable.
- **Recommendation:** Retain only as a candidate after owner confirms the release evidence makes a default-token finding an upgrade blocker rather than a deployment warning.
- **Remaining uncertainty:** No owner severity decision; no approved rule; exact release applicability needs source review.
- **Candidate/implementation consistency:** No field-name mismatch found for the two listed candidate facts, but no executable rule exists.

| case_id | scenario | proposed_expected | evidence basis | reasoning | owner_decision |
| --- | --- | --- | --- | --- | --- |
| P05-R01-01 | Agent backend declared and token equals the published development default. | result=failed; verdict_effect=blocked | P05.S004, P05.S005, P05.S006 | Candidate-only scenario for P05-R01. It is derived from the proposed root condition and must be independently reviewed against P05.S004, P05.S005, P05.S006; it is not product test truth. | null |
| P05-R01-02 | Agent backend declared and token is explicitly non-default. | result=passed; verdict_effect=none | P05.S004, P05.S005, P05.S006 | Candidate-only scenario for P05-R01. It is derived from the proposed root condition and must be independently reviewed against P05.S004, P05.S005, P05.S006; it is not product test truth. | null |
| P05-R01-03 | Agent backend declared but default relation was not captured. | result=unknown; verdict_effect=incomplete | P05.S004, P05.S005, P05.S006 | Candidate-only scenario for P05-R01. It is derived from the proposed root condition and must be independently reviewed against P05.S004, P05.S005, P05.S006; it is not product test truth. | null |
| P05-R01-04 | Target deployment does not declare agent backend. | result=not_applicable; verdict_effect=none | P05.S004, P05.S005, P05.S006 | Candidate-only scenario for P05-R01. It is derived from the proposed root condition and must be independently reviewed against P05.S004, P05.S005, P05.S006; it is not product test truth. | null |
| P05-R01-05 | Same token facts presented for a different source-target edge. | result=not_evaluated; verdict_effect=unsupported_edge | P05.S004, P05.S005, P05.S006 | Candidate-only scenario for P05-R01. It is derived from the proposed root condition and must be independently reviewed against P05.S004, P05.S005, P05.S006; it is not product test truth. | null |

## P05-R02 — API and agent backend authentication tokens do not match

- **Exact edge:** `1.16.0 -> 1.16.1` (`P05-EDGE-A`), candidate only.
- **Fixed evidence:** `P05.S004`, `P05.S005`. P05.S004=937fb34a20b5c023c509cbb950406eadec69b24f69d728c34f8dd7537adab623 P05.S005=aba772e012fd829499a663532b22ff3521096105f01ed9222eeb02a956a9ff3b
- **Applies semantics:** Proposed only: exact edge P05-EDGE-A and a declared agent backend with relevant peer services.
- **Assertion semantics:** Proposed only: peer token relation matches and target-D wiring is complete.
- **Candidate required facts:** `agent_backend.declared`, `private.agent_api_tokens_same_as_peer`, `agent_auth_wiring_complete`.
- **Fact origin:** peer equality: derived in memory only; target wiring: declared target Compose fact.
- **Version boundary:** P05-EDGE-A only (1.16.0 -> 1.16.1).
- **Severity / phase:** blocker (proposed); before_upgrade (proposed).
- **Known counterexamples:** Matching non-default peers with complete target wiring pass; missing peer is UNKNOWN; absent target backend is not applicable.
- **Recommendation:** Revise before adjudication: define target-D fact namespace and rename the candidate wiring fact to the implemented dotted form.
- **Remaining uncertainty:** Candidate uses `agent_auth_wiring_complete`; implementation emits `agent_auth.wiring_complete`. The candidate does not state whether the assertion reads B or `proposed.*` D.
- **Candidate/implementation consistency:** BLOCKER: `agent_auth_wiring_complete` is not an emitted fact; current code uses `agent_auth.wiring_complete`.

| case_id | scenario | proposed_expected | evidence basis | reasoning | owner_decision |
| --- | --- | --- | --- | --- | --- |
| P05-R02-01 | API and agent backend tokens are both non-default but differ. | result=failed; verdict_effect=blocked | P05.S004, P05.S005 | Candidate-only scenario for P05-R02. It is derived from the proposed root condition and must be independently reviewed against P05.S004, P05.S005; it is not product test truth. | null |
| P05-R02-02 | API and agent backend tokens match and target wiring is complete. | result=passed; verdict_effect=none | P05.S004, P05.S005 | Candidate-only scenario for P05-R02. It is derived from the proposed root condition and must be independently reviewed against P05.S004, P05.S005; it is not product test truth. | null |
| P05-R02-03 | One peer token is unavailable after redaction. | result=unknown; verdict_effect=incomplete | P05.S004, P05.S005 | Candidate-only scenario for P05-R02. It is derived from the proposed root condition and must be independently reviewed against P05.S004, P05.S005; it is not product test truth. | null |
| P05-R02-04 | Agent backend is absent from the target deployment. | result=not_applicable; verdict_effect=none | P05.S004, P05.S005 | Candidate-only scenario for P05-R02. It is derived from the proposed root condition and must be independently reviewed against P05.S004, P05.S005; it is not product test truth. | null |
| P05-R02-05 | Tokens match but a customized API service does not wire the peer token. | result=failed; verdict_effect=blocked | P05.S004, P05.S005 | Candidate-only scenario for P05-R02. It is derived from the proposed root condition and must be independently reviewed against P05.S004, P05.S005; it is not product test truth. | null |
| P05-R02-06 | API token matches agent backend but worker token differs. | result=failed; verdict_effect=blocked | P05.S004, P05.S005 | Candidate-only scenario for P05-R02. It is derived from the proposed root condition and must be independently reviewed against P05.S004, P05.S005; it is not product test truth. | null |
| P05-R02-07 | Agent backend is declared but one required peer token is explicitly empty. | result=unknown; verdict_effect=incomplete | P05.S004, P05.S005 | Candidate-only scenario for P05-R02. It is derived from the proposed root condition and must be independently reviewed against P05.S004, P05.S005; it is not product test truth. | null |

## P05-R03 — Local agent sandbox bypasses the target proxy isolation topology

- **Exact edge:** `1.16.0 -> 1.16.1` (`P05-EDGE-A`), candidate only.
- **Fixed evidence:** `P05.S002`, `P05.S004`, `P05.S005`. P05.S002=9be7c92d6fc2bac708efd1c88b24c45f9587243a4b2d77729e3c13b2b82404bf P05.S004=937fb34a20b5c023c509cbb950406eadec69b24f69d728c34f8dd7537adab623 P05.S005=aba772e012fd829499a663532b22ff3521096105f01ed9222eeb02a956a9ff3b
- **Applies semantics:** Proposed only: exact edge P05-EDGE-A and Agent functionality present.
- **Assertion semantics:** Proposed only: target-D Sandbox/proxy topology is declared as compliant.
- **Candidate required facts:** `agent_runtime.backend`, `agent_sandbox.target_network_topology`.
- **Fact origin:** declared Compose topology; target configuration must remain in `proposed.*` namespace.
- **Version boundary:** P05-EDGE-A only (1.16.0 -> 1.16.1).
- **Severity / phase:** blocker (proposed); before_upgrade (proposed).
- **Known counterexamples:** Target topology passes; omitted Agent services are not applicable; unnormalizable networking is UNKNOWN.
- **Recommendation:** Revise before adjudication: replace the missing runtime fact and specify exact target-D topology facts and normalization limits.
- **Remaining uncertainty:** Candidate uses `agent_runtime.backend`; implementation emits `agent_backend.declared`. No approved rule defines which source/target topology constitutes a blocker.
- **Candidate/implementation consistency:** BLOCKER: `agent_runtime.backend` is not emitted by the collector or evaluator fact view.

| case_id | scenario | proposed_expected | evidence basis | reasoning | owner_decision |
| --- | --- | --- | --- | --- | --- |
| P05-R03-01 | Local sandbox remains on the default network without the dedicated proxy. | result=failed; verdict_effect=blocked | P05.S002, P05.S004, P05.S005 | Candidate-only scenario for P05-R03. It is derived from the proposed root condition and must be independently reviewed against P05.S002, P05.S004, P05.S005; it is not product test truth. | null |
| P05-R03-02 | Local sandbox uses both target internal networks and the dedicated proxy. | result=passed; verdict_effect=none | P05.S002, P05.S004, P05.S005 | Candidate-only scenario for P05-R03. It is derived from the proposed root condition and must be independently reviewed against P05.S002, P05.S004, P05.S005; it is not product test truth. | null |
| P05-R03-03 | Agent functionality is disabled and agent_backend plus local_sandbox are omitted. | result=not_applicable; verdict_effect=none | P05.S002, P05.S004, P05.S005 | Candidate-only scenario for P05-R03. It is derived from the proposed root condition and must be independently reviewed against P05.S002, P05.S004, P05.S005; it is not product test truth. | null |
| P05-R03-04 | A custom network driver prevents safe topology normalization. | result=unknown; verdict_effect=incomplete | P05.S002, P05.S004, P05.S005 | Candidate-only scenario for P05-R03. It is derived from the proposed root condition and must be independently reviewed against P05.S002, P05.S004, P05.S005; it is not product test truth. | null |
| P05-R03-05 | Networks are present but agent_ssrf_proxy service is missing. | result=failed; verdict_effect=blocked | P05.S002, P05.S004, P05.S005 | Candidate-only scenario for P05-R03. It is derived from the proposed root condition and must be independently reviewed against P05.S002, P05.S004, P05.S005; it is not product test truth. | null |

## P05-R04 — External plugin installation cannot invalidate enabled provider cache

- **Exact edge:** `1.16.0 -> 1.16.1` (`P05-EDGE-A`), candidate only.
- **Fixed evidence:** `P05.S004`, `P05.S013`, `P05.S014`. P05.S004=937fb34a20b5c023c509cbb950406eadec69b24f69d728c34f8dd7537adab623 P05.S013=ed9622c89cb3617e28bbec48b815db9628d99b4154adb8014b6781b1b559e32c P05.S014=d0671fbac3b7aa98159580a4803a4da356c41dec282268780f1c95a5d3f26479
- **Applies semantics:** Proposed only: external plugin installation, provider cache enabled, and candidate edge P05-EDGE-A.
- **Assertion semantics:** Proposed only: cache invalidation capability is true.
- **Candidate required facts:** `plugins.installation_ownership`, `plugins.provider_cache_enabled`, `plugins.cache_invalidation_available`.
- **Fact origin:** installation/invalidation: attested; provider cache: declared Compose fact.
- **Version boundary:** P05-EDGE-A only (1.16.0 -> 1.16.1).
- **Severity / phase:** warning (proposed); manual_review (proposed).
- **Known counterexamples:** Cache disabled or invalidation available passes; Dify-managed installation is not applicable; uncertainty is UNKNOWN.
- **Recommendation:** Revise before adjudication: align ownership naming and decide whether an attestation-dependent warning has sufficient v0.1 value.
- **Remaining uncertainty:** Candidate uses `plugins.installation_ownership`; implementation permits only boolean `plugins.externally_installed` attestation.
- **Candidate/implementation consistency:** BLOCKER: `plugins.installation_ownership` is not an emitted fact; `plugins.externally_installed` has different semantics.

| case_id | scenario | proposed_expected | evidence basis | reasoning | owner_decision |
| --- | --- | --- | --- | --- | --- |
| P05-R04-01 | Plugins are installed externally, provider cache is enabled, and invalidation is unavailable. | result=failed; verdict_effect=warning | P05.S004, P05.S013, P05.S014 | Candidate-only scenario for P05-R04. It is derived from the proposed root condition and must be independently reviewed against P05.S004, P05.S013, P05.S014; it is not product test truth. | null |
| P05-R04-02 | Plugins are installed externally and provider cache is disabled. | result=passed; verdict_effect=none | P05.S004, P05.S013, P05.S014 | Candidate-only scenario for P05-R04. It is derived from the proposed root condition and must be independently reviewed against P05.S004, P05.S013, P05.S014; it is not product test truth. | null |
| P05-R04-03 | Dify manages plugin installation and cache invalidation. | result=not_applicable; verdict_effect=none | P05.S004, P05.S013, P05.S014 | Candidate-only scenario for P05-R04. It is derived from the proposed root condition and must be independently reviewed against P05.S004, P05.S013, P05.S014; it is not product test truth. | null |
| P05-R04-04 | External plugin ownership is known but invalidation capability is unknown. | result=unknown; verdict_effect=incomplete | P05.S004, P05.S013, P05.S014 | Candidate-only scenario for P05-R04. It is derived from the proposed root condition and must be independently reviewed against P05.S004, P05.S013, P05.S014; it is not product test truth. | null |
| P05-R04-05 | External installer provides a verified invalidation mechanism while cache stays enabled. | result=passed; verdict_effect=none | P05.S004, P05.S013, P05.S014 | Candidate-only scenario for P05-R04. It is derived from the proposed root condition and must be independently reviewed against P05.S004, P05.S013, P05.S014; it is not product test truth. | null |

## P05-R05 — Legacy model-type migration is required but not attested complete

- **Exact edge:** `1.16.0 -> 1.16.1` (`P05-EDGE-A`), candidate only.
- **Fixed evidence:** `P05.S004`. P05.S004=937fb34a20b5c023c509cbb950406eadec69b24f69d728c34f8dd7537adab623
- **Applies semantics:** Proposed only: exact edge P05-EDGE-A and attested deployment history before 1.15.
- **Assertion semantics:** Proposed only: `migration.legacy_model_types_completed` is true.
- **Candidate required facts:** `history.upgraded_from_before_1_15`, `migration.legacy_model_types_completed`.
- **Fact origin:** both history and completion are fixed-key user attestations.
- **Version boundary:** P05-EDGE-A only; not evaluated for 1.17.1 where the candidate review says the migration is automatic.
- **Severity / phase:** warning (proposed); after_upgrade (proposed).
- **Known counterexamples:** Attested completion passes; fresh 1.15+ deployment is not applicable; missing history is UNKNOWN.
- **Recommendation:** Retain as a candidate only if the owner accepts the fixed source evidence and attestation boundary; do not infer history from current version.
- **Remaining uncertainty:** Migration status cannot be observed in v0.1; the automatic-migration version boundary still needs owner source review.
- **Candidate/implementation consistency:** No field-name mismatch found for the candidate attestation names; no executable rule exists.

| case_id | scenario | proposed_expected | evidence basis | reasoning | owner_decision |
| --- | --- | --- | --- | --- | --- |
| P05-R05-01 | Deployment history predates 1.15 and the legacy migration is attested incomplete. | result=failed; verdict_effect=warning | P05.S004 | Candidate-only scenario for P05-R05. It is derived from the proposed root condition and must be independently reviewed against P05.S004; it is not product test truth. | null |
| P05-R05-02 | Deployment history predates 1.15 and migration completion is attested. | result=passed; verdict_effect=none | P05.S004 | Candidate-only scenario for P05-R05. It is derived from the proposed root condition and must be independently reviewed against P05.S004; it is not product test truth. | null |
| P05-R05-03 | Fresh deployment began at 1.15 or later. | result=not_applicable; verdict_effect=none | P05.S004 | Candidate-only scenario for P05-R05. It is derived from the proposed root condition and must be independently reviewed against P05.S004; it is not product test truth. | null |
| P05-R05-04 | Earliest deployment version is unknown. | result=unknown; verdict_effect=incomplete | P05.S004 | Candidate-only scenario for P05-R05. It is derived from the proposed root condition and must be independently reviewed against P05.S004; it is not product test truth. | null |
| P05-R05-05 | Pre-1.15 history is attested but migration completion is unknown. | result=unknown; verdict_effect=incomplete | P05.S004 | Candidate-only scenario for P05-R05. It is derived from the proposed root condition and must be independently reviewed against P05.S004; it is not product test truth. | null |
| P05-R05-06 | Target is 1.17.1, where the manual legacy-model migration is not evaluated because the target migration is automatic. | result=not_evaluated; verdict_effect=unsupported_edge | P05.S004 | Candidate-only scenario for P05-R05. It is derived from the proposed root condition and must be independently reviewed against P05.S004; it is not product test truth. | null |

## P05-R06 — Existing bundled Weaviate data would cross minor versions in one restart

- **Exact edge:** `1.17.0 -> 1.17.1` (`P05-EDGE-B`), candidate only.
- **Fixed evidence:** `P05.S008`, `P05.S010`, `P05.S011`, `P05.S012`. P05.S008=0a40c493ec17d24d4c200e2e54f761ee34d0fa221be33bcc73930c9086fe3124 P05.S010=b7b7a9d043557e42814f4a6ea4ddd05e3b9d3ec4c871717b2167e36667524715 P05.S011=df7cbb6098261affc75cd8c90ebc9cd909155bab7411c3370786582f5593dacd P05.S012=f4cc24e1b2aa033ed1145b2333e23bf3eda3567131493eb47543cd7bcb81abdc
- **Applies semantics:** Proposed only: exact edge P05-EDGE-B, declared bundled Weaviate ownership, and attested persisted data.
- **Assertion semantics:** Proposed only: `vector.staged_upgrade_completed` is true.
- **Candidate required facts:** `vector.ownership`, `vector.persisted_data`, `vector.staged_upgrade_completed`.
- **Fact origin:** ownership: declared Compose fact; persisted data and stage completion: fixed-key user attestations.
- **Version boundary:** P05-EDGE-B only (1.17.0 -> 1.17.1); fresh or external stores are not applicable.
- **Severity / phase:** blocker (proposed); before_upgrade (proposed).
- **Known counterexamples:** Completed stages pass; fresh/external stores are not applicable; missing evidence is UNKNOWN, not failure.
- **Recommendation:** Retain as a candidate only after the official staged path and version boundary are independently adjudicated; define what attestations count as completed stages.
- **Remaining uncertainty:** Static Compose cannot prove persisted data or completed migration stages; Weaviate documentation is mutable and must remain so labelled.
- **Candidate/implementation consistency:** No field-name mismatch found for the listed candidate facts; no executable rule exists.

| case_id | scenario | proposed_expected | evidence basis | reasoning | owner_decision |
| --- | --- | --- | --- | --- | --- |
| P05-R06-01 | Bundled Weaviate has existing data and staged-upgrade completion is explicitly attested false. | result=failed; verdict_effect=blocked | P05.S008, P05.S010, P05.S011, P05.S012 | Candidate-only scenario for P05-R06. It is derived from the proposed root condition and must be independently reviewed against P05.S008, P05.S010, P05.S011, P05.S012; it is not product test truth. | null |
| P05-R06-02 | Bundled persisted Weaviate completed every approved staged upgrade. | result=passed; verdict_effect=none | P05.S008, P05.S010, P05.S011, P05.S012 | Candidate-only scenario for P05-R06. It is derived from the proposed root condition and must be independently reviewed against P05.S008, P05.S010, P05.S011, P05.S012; it is not product test truth. | null |
| P05-R06-03 | Fresh bundled Weaviate deployment has no existing volume data. | result=not_applicable; verdict_effect=none | P05.S008, P05.S010, P05.S011, P05.S012 | Candidate-only scenario for P05-R06. It is derived from the proposed root condition and must be independently reviewed against P05.S008, P05.S010, P05.S011, P05.S012; it is not product test truth. | null |
| P05-R06-04 | Vector store is external Weaviate or another external backend. | result=not_applicable; verdict_effect=none | P05.S008, P05.S010, P05.S011, P05.S012 | Candidate-only scenario for P05-R06. It is derived from the proposed root condition and must be independently reviewed against P05.S008, P05.S010, P05.S011, P05.S012; it is not product test truth. | null |
| P05-R06-05 | Bundled ownership is known but persisted-data or staged-completion evidence is unknown. | result=unknown; verdict_effect=incomplete | P05.S008, P05.S010, P05.S011, P05.S012 | Candidate-only scenario for P05-R06. It is derived from the proposed root condition and must be independently reviewed against P05.S008, P05.S010, P05.S011, P05.S012; it is not product test truth. | null |
