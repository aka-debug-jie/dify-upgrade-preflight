# 数据与接口契约

首版 schema 版本为 `1.0`。`specs/schemas/` 给出可机器验证的形状；本文定义 JSON Schema 无法覆盖的语义。P00/P01 可通过变更申请修订，不得静默漂移。

## 1. 基本类型

`TruthValue`：TRUE / FALSE / UNKNOWN。
`Fact.status`：known / unknown / conflicted。
`Fact.origin`：declared / observed / attested / derived / synthetic。
`Finding.result`：passed / failed / unknown / not_applicable。
`Finding.severity`：blocker / warning / info。
`Report.verdict`：NO_KNOWN_BLOCKERS / BLOCKED / INCOMPLETE / UNSUPPORTED / ERROR。

known 事实必须有非空 value；unknown/conflicted 的 value 为 null，并附 reason。known=false 与 unknown 不同。值限定为标量，避免把任意配置对象带进报告。

## 2. DeploymentSnapshot

必须字段：schema_version、kind、synthetic、snapshot_id、capture、facts、public_config、private_relations、gaps。

capture 包含 mode、collector_version、compose_version（可空）、captured_at。mode 为 synthetic / compose_declared / live_opt_in。

facts 用标准路径作为键，例如：
- `dify.declared_version`：来自 API/Web 镜像或显式说明；相互冲突时 conflicted。
- `dify.observed_version`：v0.1 通常 unknown，不能复制 declared 值。
- `vector.kind`、`vector.ownership`（bundled/external/unknown）、`vector.declared_version`。
- `vector.persisted_data`：配置有挂载只证明挂载声明，不能直接设 true；必须有认可的观察或 attestation。
- `history.earliest_version`、`migration.legacy_model_types`：不从当前版本推断。

`public_config` 是经过允许字段表筛选的扁平映射：例如 `services.api.image_tag`、`services.api.depends_on.db_postgres`。不包含整个 env/command、private registry 凭据或主机路径。

`private_relations` 只允许布尔或 null，例如 `env.SECRET_KEY.matches_insecure_default`。不得存真实值和其可猜测哈希。

`build_fact_view(snapshot)` 在内存中把这些关系映射为 `private.<key>` 的 derived Fact：布尔为known、null为unknown，source_ref指向关系键。snapshot.facts禁止自带private.前缀，避免覆盖。表达式仍只读取统一Mapping[str, Fact]，不直接访问原始秘密。

`gaps` 是采集缺口，包含 id、reason、affects、required_for_scope。与本次 scope 无关的缺口仅列入未检查项，不让每一次离线分析都永久失败。

## 3. CaptureRequest / UpgradeRequest

CaptureRequest：project_dir、按顺序的 compose_files、显式 env_files、profiles、显式准许的插值变量名、固定键布尔 attestations、catalog_path、输出路径（可空）。attestations 只接受审核过的历史/归属/完成状态键；缺失就是 UNKNOWN，不能传递值、来源文本或任意事实名。都由 CLI 参数提供；不自动扫描 home、其它仓库和全局 Docker context。

UpgradeRequest：source_version、target_version、scope=`static_upgrade_plan`、optional proposed_snapshot。source/target 必须明确且与关键声明事实一致；不能使用 latest/nightly/main 作为已支持 release。

有用户目标配置 D 时，规则可验证目标计划中的真实冲突。D 的 facts 以 proposed.* 命名空间独立进入规则；不能覆盖 B 的部署事实或历史 attestation。没有 D 时，依赖 D 的规则为 UNKNOWN，只描述目标官方基线与本地修改之间的分歧。

## 4. ConfigChange

字段：path、kind、comparability、base/local/target/proposed 的允许公开值或遮罩、reason。
kind：unchanged / upstream_only / local_only / same_change / divergent_change / unknown_comparison。
comparability：public / relation_only / unknown。

不允许用遮罩字符串“相等”判断秘密相等。私密数据只能用采集时产生的关系事实。无法比较时 unknown_comparison，而不是 unchanged。

## 5. Rule

字段及完整结构见 rule schema。规则应用于批准的 support_edge_ids；只用受限表达式读取 facts。
规则分成 applies 和 assertion：先判断是否适用，再判断要求是否满足。facts 缺失是 UNKNOWN。

每条规则有 evidence_refs、review_ref、supersedes、remediation.phase、remediation.executable=false。
真实规则 status=approved 仍不足以信任：loader 还必须核对批准清单中的内容哈希与对应 sources 的固定证据。

## 6. Report

必有：schema_version、synthetic、scope、source_version、target_version、verdict、findings、changes、coverage、provenance、decision_digest。

coverage：support_edge_id、required_rule_count、evaluated_rule_count、unknown_required_rules、excluded_checks。不得把覆盖比例渲染成安全概率。

provenance：catalog_digest、snapshot_digest、proposed_snapshot_digest（可空）、tool_version。时间、耗时和 captured_at 不参与 decision_digest。provenance还包含catalog_trust；untrusted的自定义目录不能产生NO_KNOWN_BLOCKERS，而是INCOMPLETE。synthetic只允许在demo/test路径。finding 的 fact_evidence 保留事实 origin/source_ref，不携带事实原值。

decision_digest 对规范化后的 source/target/scope/有序 findings/changes/coverage/catalog_digest/snapshot_decision_digest 求 SHA-256；将 canonicalization_version 写入 provenance。按键排序、固定 Unicode/数值序列化策略，P01 用 golden 样例锁定。

## 7. 结果聚合优先级

1. 无法安全解析输入、目录损坏或内部异常：ERROR，不伪造业务结论。
2. 明确无相应支持边或部署方式不支持：UNSUPPORTED。可附非放行性质信息。
3. 已支持范围内存在 failed blocker：BLOCKED；同时保留未知检查。
4. 无 blocker，但存在必需事实/规则 UNKNOWN、覆盖缺口或catalog来源未获信任：INCOMPLETE。
5. 必需范围全部完成：NO_KNOWN_BLOCKERS；可以仍有非阻断 warning 和范围外未检查项。

发现应用范围本身不支持时，不允许靠“规则没匹配到”走到第 5 项。

## 8. 规范序列化补充

JSON解析拒绝重复键、NaN/Infinity和非法UTF-8。canonicalization_version=1使用UTF-8、ensure_ascii=false、键排序、无额外空格、拒绝非有限数。snapshot_digest基于去除snapshot_id和capture后的脱敏snapshot；capture保留供审计但不计入判定数据摘要。decision_digest对Report除decision_digest自身外的固定字段进行同样序列化并求SHA-256；当前Report不携带时延/日志。承诺相同工具版本、相同规范化输入和catalog得相同摘要，不承诺不同引擎版本摘要相同。
