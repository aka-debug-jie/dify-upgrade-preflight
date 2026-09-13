# 规则、证据与生命周期

## 1. 两种来源库

`sources/registry.yaml` 是当前规划使用的公开资料线索，状态为 discovered_not_pinned；**不是可以直接发布的证据库**。

开发时建立 catalog source registry，必须记录 source_id、官方 URL、release/tag、完整 commit SHA（适用时）、retrieved_at、原始内容 SHA-256、定位 section/path、摘要、许可/再分发处理、review_status。

网页会变化、release note 可能被编辑。tag 与 main 不等同；固定 tag 后还需解析到 commit，正文另外固定内容 digest。网络不可达时标记 blocked_external，不填猜测哈希。

不在公开包复制完整第三方文档；优先保留最小必要片段/摘要和定位。需要再分发文件时先核对该文件许可证，不假定整个上游都是普通 MIT。

## 2. 事实等级

| 级别 | 用途 |
|---|---|
| official_fixed | 官方固定版本源码/说明 + 内容 digest，规则主要依据 |
| official_mutable | 官方 main/在线说明，发现线索，不能单独批准版本边 |
| user_report | issue/discussion 的实际故障线索，需重演或代码印证 |
| bot_comment | 自动回复，只是线索，不当权威升级指令 |
| model_inference | 待验证推断，不是生产规则事实 |
| synthetic | 自造测试语义，绝不转成真实产品规则 |

## 3. 三值规则语义

规则先 `applies` 后 `assertion`：

- applies=FALSE → not_applicable。
- applies=UNKNOWN → unknown；必需规则影响完整性。
- applies=TRUE，assertion=TRUE → passed。
- applies=TRUE，assertion=FALSE → failed；severity=blocker 时阻断。
- applies=TRUE，assertion=UNKNOWN → unknown。

ALL：任一 FALSE 则 FALSE，否则任一 UNKNOWN 则 UNKNOWN，否则 TRUE。
ANY：任一 TRUE 则 TRUE，否则任一 UNKNOWN 则 UNKNOWN，否则 FALSE。
NOT：TRUE/FALSE 互换，UNKNOWN 保持。

限定操作符：eq、ne、in、version_lt、version_lte、version_gt、version_gte。版本使用规范化明确 release，禁止字典序比较。无法解析版本返回 UNKNOWN，不吞掉成最小版本。

规则树深度 ≤ 8，单规则条件节点 ≤ 64，禁止空 ALL/ANY、重复 rule id、任意正则、脚本和 Python 表达式。

## 4. 严格生命周期

candidate → reviewed → approved → superseded/retired。
磁盘 schema 的 status 用 candidate/approved/retired；reviewed 是审批流程中间状态，不另外加载到生产。

approved 要求：来源固定、正反未知边界测试、根因案例、owner approval 的内容 digest 一致。文件里自写 status=approved 不够；loader 必须同时校验批准清单。

supersedes 只影响**同一个适用范围**。新规则自动执行迁移的证据不能让所有旧版本的手工步骤失效。旧规则退休也必须有反例证明不会漏报旧路径。

## 5. 每条规则的最低证据与测试

官方明确要求 → 配置/组件事实 → 适用性 → 不满足条件 → severity → 用户下一步。

最低测试：适用且失败、适用且满足、不适用、关键信息未知、版本边界前后、归属 external/bundled、已执行/未证实（适用时）、supersession。

故障类型必须区分：已知前置阻碍、正常待执行迁移、目标版本自身回归、需要人工确认、升级后验收。

## 6. 候选事实不能变成万能规则

例如“某 release 更新 bundled Weaviate”必须结合真实 component 版本、是否由此 Compose 管理、是否持久数据、目标版本及厂商升级说明。不是 `weaviate < target` 就一律阻断。

“部署当前版本较新”不证明历史 legacy 数据迁移已执行；“来自更老版本”也不一定意味着在目标版还需要手工命令。来源冲突时暂停规则晋升。

不复制聊天里示例的 image、迁移 ID、命令顺序。P00 需要从固定版本重新核验。

## 7. catalog 作为构建产物

catalog 有自身 version、schema_version、source identities、support edges、规则索引和全包 digest。生产 check 只加载本地审核版本；禁止运行时下载规则并立即信任。

候选规则的增加可以由 Codex辅助；其批准和首次纳入支持矩阵需要人工。自动维护工作流最多创建本地候选/待审查材料，不自动发布。
