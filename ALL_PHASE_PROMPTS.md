# 全阶段 Codex 引导提示词｜浏览版

由 prompts/P00…P11 汇总。真正执行只发送对应阶段文件；不要把本文件一次全部粘贴。任务状态以 roadmap.yaml 为准。

# P00｜事实、支持边与开发环境核验 — 可直接交给 Codex

你现在只负责 Dify Upgrade Preflight 的 P00 阶段。

目标：不写业务代码，确认两类以上机器可检测的真实痛点，提出两条可固定的候选升级边及最小环境方案。

前置：初始阶段，无前置业务实现；默认业务范围仍以根目录契约为准。


执行纪律：
1. 只做本阶段；先确认前置阶段 done 和实际批准记录。初始 P00 以首次启动提示词授权进入。
2. 阅读固定入口及本阶段文件。验证契约锁、现有工作树与已有失败，保留用户改动。
3. 先写本任务失败测试/事实裁决，再实现最小行为。任何判断缺证据必须明确标记，不靠合理猜测。
4. 不修改验收条件/基线哈希，不扩大支持，不增加未批准核心依赖，不改变默认权限。
5. 运行当前已存在且适用的命令；没有环境标 blocked_external，未批准动作标 blocked_review。不能把预期输出当实际执行。
6. 输出脱敏证据、实际命令/返回码/耗时、文件清单、未通过项和下一步。更新 roadmap 允许字段，完成后停在 ready_for_review。
7. 不commit/push/tag/release，不修改生产文件/数据库/volumes。实验动作另需授权。不要自动开始下一阶段。


## 本阶段补充阅读

- `sources/SOURCES.md`
- `sources/registry.yaml`
- `catalog/candidates.yaml`
- `docs/DEPENDENCIES_AND_ENVIRONMENT.md`
- `docs/SUPPORT_MATRIX.md`

## 输入/输出接口

输入是候选线索和当前开发目录；输出是固定来源记录、待批准依赖/支持提案；approved_edges 仍为空。

## 预期写入的文件或目录

- `artifacts/P00/<run_id>/DISCOVERY.md`
- `artifacts/P00/<run_id>/ENVIRONMENT.md`
- `artifacts/P00/<run_id>/SUPPORT_PROPOSAL.md`
- `sources/pinned.yaml`
- `governance/dependencies.yaml`

`<run_id>` 必须替换为实际唯一运行标识；这些是执行产物路径，不是已存在的证据。

## 顺序任务

### P00.T1｜核查工作区与权限

行动：检查已有目录、Git 状态、Python/Compose 可用性与是否有独立实验环境；不连接 daemon、不安装系统软件。

验收：ENVIRONMENT 明确已有/缺失/未验证；没有任何生产读写和全局设置变更。

### P00.T2｜固定候选事实

行动：从官方 release、固定源码和组件指南提取至少两类根因；记录完整 SHA/内容 digest、反例和来源冲突；失败可作为 blocked_external 保留。

验收：每项事实能从固定来源重查；fetch 失败不出现假 SHA，不用 bot 回复当裁决。

### P00.T3｜作出范围提案

行动：选择最多两条首版 exact edge、必要 facts、六类候选根因、依赖选择；核查名称/再分发但不注册或发布。

验收：支持提案说明可测/不可测；与普通 env sync 的区别成立；若不足则给 NO-GO/PIVOT 而非造代码。

## 本阶段验收命令

以下为实现完成后的目标验证命令。缺少脚本/测试时先完成本阶段对应交付，不能伪造命令执行。

```bash
python --version
git status --short  # 仅当前目录已是 Git 仓库时
docker compose version  # 仅已安装且只检查 CLI 版本时
```

## 硬闸门

- 实际已获得的来源和未获得的来源分开；关键来源无法固定则不能完成本阶段。
- 候选路径/事实足以支持一个小闭环，且依赖/名称/许可风险被记录。
- 你审核范围提案后才解锁 P01；没有批准不得先写业务实现。

## 本阶段不做

不生成生产规则、不猜兼容版本、不创建 src 业务代码、不自动 Git init/commit、不运行 Dify。

## 最后交付

按 templates/HANDOFF.md 写本阶段记录；使用真实证据。给出是否达到 ready_for_review、哪些事项仍需我审阅。不要将本阶段自设为 done，不继续下阶段。

---

# P01｜最小可运行闭环与核心契约 — 可直接交给 Codex

你现在只负责 Dify Upgrade Preflight 的 P01 阶段。

目标：先让一个合成快照经过纯规则判定输出正确 JSON 和退出码，再建立可安装的小包。

前置：P00；默认业务范围仍以根目录契约为准。


执行纪律：
1. 只做本阶段；先确认前置阶段 done 和实际批准记录。初始 P00 以首次启动提示词授权进入。
2. 阅读固定入口及本阶段文件。验证契约锁、现有工作树与已有失败，保留用户改动。
3. 先写本任务失败测试/事实裁决，再实现最小行为。任何判断缺证据必须明确标记，不靠合理猜测。
4. 不修改验收条件/基线哈希，不扩大支持，不增加未批准核心依赖，不改变默认权限。
5. 运行当前已存在且适用的命令；没有环境标 blocked_external，未批准动作标 blocked_review。不能把预期输出当实际执行。
6. 输出脱敏证据、实际命令/返回码/耗时、文件清单、未通过项和下一步。更新 roadmap 允许字段，完成后停在 ready_for_review。
7. 不commit/push/tag/release，不修改生产文件/数据库/volumes。实验动作另需授权。不要自动开始下一阶段。


## 本阶段补充阅读

- `docs/ARCHITECTURE.md`
- `docs/DATA_CONTRACTS.md`
- `docs/CLI_CONTRACT.md`
- `specs/README.md`
- `examples/README.md`
- `docs/DEVELOPMENT_PROTOCOL.md`

## 输入/输出接口

实现 TruthValue、Fact、Rule、Report 及 evaluate_expression/evaluate 的 synthetic 子集；demo 是唯一演示入口，不能接受 synthetic 为真实生产结论。

## 预期写入的文件或目录

- `pyproject.toml`
- `src/dify_preflight/domain.py`
- `src/dify_preflight/engine/expressions.py`
- `src/dify_preflight/engine/verdict.py`
- `src/dify_preflight/cli.py`
- `tests/unit/test_truth_table.py`
- `tests/contract/test_verdict.py`
- `tests/contract/test_demo.py`
- `scripts/validate_governance.py`

`<run_id>` 必须替换为实际唯一运行标识；这些是执行产物路径，不是已存在的证据。

## 顺序任务

### P01.T1｜把数据与判定规格转为失败测试

行动：按 schema 定义最小类型，锁定 examples 和全部 verdict-cases；测试在功能未实现时应失败。

验收：known false != unknown；32种 verdict 组合和目标退出码精确一致。

### P01.T2｜实现单条合成路径

行动：实现规则 applies/assertion、纯 evaluator、小型 argparse demo；true/false/unknown 三个输入都走完整输出。

验收：原始样例输出 BLOCKED；改变条件为 true 不再失败；未知给 INCOMPLETE；三个结果都 synthetic。

### P01.T3｜打包并保护契约

行动：只安装 P00 批准依赖，定义 .[dev]，建立本地验证命令与 governance 校验器；创建新的虚拟环境验证导入。

验收：--help/demo 可运行；拒绝被改的受保护文件；没有空框架冒充完成；记录首个未达标也真实的性能 baseline。

## 本阶段验收命令

以下为实现完成后的目标验证命令。缺少脚本/测试时先完成本阶段对应交付，不能伪造命令执行。

```bash
python -m pytest tests/unit/test_truth_table.py tests/contract/test_verdict.py tests/contract/test_demo.py -q
python -m dify_preflight demo --case blocked --format json  # 预期 exit 2
python scripts/validate_governance.py
```

## 硬闸门

- 一个可安装的端到端 synthetic 演示成立。
- 纯 evaluator 无网络/子进程；schema/退出码与冻结数据一致。
- 类型/包装/初始快测试通过；无真实 Dify 支持声明。

## 本阶段不做

不做 Docker 采集、网络下载、真实规则批准、完整插件架构和 Web UI。

## 最后交付

按 templates/HANDOFF.md 写本阶段记录；使用真实证据。给出是否达到 ready_for_review、哪些事项仍需我审阅。不要将本阶段自设为 done，不继续下阶段。

---

# P02｜受限配置采集与脱敏快照 — 可直接交给 Codex

你现在只负责 Dify Upgrade Preflight 的 P02 阶段。

目标：把明确指定的 Compose 配置安全转换成声明态快照，而不访问生产服务。

前置：P01；默认业务范围仍以根目录契约为准。


执行纪律：
1. 只做本阶段；先确认前置阶段 done 和实际批准记录。初始 P00 以首次启动提示词授权进入。
2. 阅读固定入口及本阶段文件。验证契约锁、现有工作树与已有失败，保留用户改动。
3. 先写本任务失败测试/事实裁决，再实现最小行为。任何判断缺证据必须明确标记，不靠合理猜测。
4. 不修改验收条件/基线哈希，不扩大支持，不增加未批准核心依赖，不改变默认权限。
5. 运行当前已存在且适用的命令；没有环境标 blocked_external，未批准动作标 blocked_review。不能把预期输出当实际执行。
6. 输出脱敏证据、实际命令/返回码/耗时、文件清单、未通过项和下一步。更新 roadmap 允许字段，完成后停在 ready_for_review。
7. 不commit/push/tag/release，不修改生产文件/数据库/volumes。实验动作另需授权。不要自动开始下一阶段。


## 本阶段补充阅读

- `docs/COMPOSE_AND_DIFF.md`
- `docs/DATA_CONTRACTS.md`
- `docs/DEPENDENCIES_AND_ENVIRONMENT.md`
- `specs/fixtures/cases.yaml`

## 输入/输出接口

实现 collect_snapshot(CaptureRequest) -> DeploymentSnapshot；原始配置只在内存；输出仅允许字段、private_relations 和 gaps。

## 预期写入的文件或目录

- `src/dify_preflight/collect/safe_io.py`
- `src/dify_preflight/collect/compose.py`
- `src/dify_preflight/collect/redaction.py`
- `tests/security/test_capture_boundary.py`
- `tests/integration/test_compose_oracle.py`
- `tests/contract/test_snapshot.py`

`<run_id>` 必须替换为实际唯一运行标识；这些是执行产物路径，不是已存在的证据。

## 顺序任务

### P02.T1｜建立输入边界测试

行动：先测试越界 symlink、include、FIFO、重复键、未知变量秘密、output覆盖；允许路径清单外不得读取。

验收：S01–S09 相关安全场景得到预期拒绝/脱敏，不能执行 command 或连接网络。

### P02.T2｜接原生 Compose

行动：在独立合成 fixture 上记录固定 CLI 功能；实现版本检查和受限 config JSON调用；不继承完整 shell env。

验收：C01–C05 插值/merge/profile 与 oracle 一致；没有 daemon 仍完成 config；无解析器报 ERROR。

### P02.T3｜归一化为声明态

行动：提取版本/拓扑/类型化公开配置，区分 declared/observed；加入秘密关系检测接口而不保存值。

验收：API/Web版本冲突不猜；历史未知保留；所有格式和异常无 canary；输入 hash 前后不变。

## 本阶段验收命令

以下为实现完成后的目标验证命令。缺少脚本/测试时先完成本阶段对应交付，不能伪造命令执行。

```bash
python -m pytest tests/security/test_capture_boundary.py tests/contract/test_snapshot.py -q
python -m pytest tests/integration/test_compose_oracle.py -q
```

## 硬闸门

- 合成原始 Compose 能形成 schema 合法快照，安全拒绝也可解释。
- 冻结版本上的 Compose 行为有真实执行；缺环境不计通过。
- raw stdout/stderr 不落盘，私密值不进入报告或日志。

## 本阶段不做

不使用 Docker SDK/socket/inspect，不读取业务 volumes，不启动服务，不重写 Compose 语义。

## 最后交付

按 templates/HANDOFF.md 写本阶段记录；使用真实证据。给出是否达到 ready_for_review、哪些事项仍需我审阅。不要将本阶段自设为 done，不继续下阶段。

---

# P03｜官方基线与三方差异分析 — 可直接交给 Codex

你现在只负责 Dify Upgrade Preflight 的 P03 阶段。

目标：正确区分上游变化、本地定制和分歧，避免把自定义配置误判成升级错误。

前置：P02；默认业务范围仍以根目录契约为准。


执行纪律：
1. 只做本阶段；先确认前置阶段 done 和实际批准记录。初始 P00 以首次启动提示词授权进入。
2. 阅读固定入口及本阶段文件。验证契约锁、现有工作树与已有失败，保留用户改动。
3. 先写本任务失败测试/事实裁决，再实现最小行为。任何判断缺证据必须明确标记，不靠合理猜测。
4. 不修改验收条件/基线哈希，不扩大支持，不增加未批准核心依赖，不改变默认权限。
5. 运行当前已存在且适用的命令；没有环境标 blocked_external，未批准动作标 blocked_review。不能把预期输出当实际执行。
6. 输出脱敏证据、实际命令/返回码/耗时、文件清单、未通过项和下一步。更新 roadmap 允许字段，完成后停在 ready_for_review。
7. 不commit/push/tag/release，不修改生产文件/数据库/volumes。实验动作另需授权。不要自动开始下一阶段。


## 本阶段补充阅读

- `docs/COMPOSE_AND_DIFF.md`
- `docs/ARCHITECTURE.md`
- `docs/DATA_CONTRACTS.md`
- `sources/pinned.yaml`

## 输入/输出接口

compare_three_way(PublicConfig A,B,C, optional D) -> list[ConfigChange]；只比较批准字段，MISSING 与 null 区分。

## 预期写入的文件或目录

- `src/dify_preflight/diff/three_way.py`
- `tests/unit/test_three_way.py`
- `tests/contract/test_private_comparison.py`
- `artifacts/P03/<run_id>/BASELINE_PROVENANCE.md`

`<run_id>` 必须替换为实际唯一运行标识；这些是执行产物路径，不是已存在的证据。

## 顺序任务

### P03.T1｜锁定差异真值与边界

行动：先写 D01–D07 的具体输入/预期，包含列表顺序、port/volume唯一键和私密遮罩。

验收：六类差异和 unknown 比较全部符合契约；不能用 REDACTED=REDACTED 证明相等。

### P03.T2｜生成固定公开基线

行动：从 P00固定 source/target 的允许文件，以固定 Compose 和显式非秘密上下文生成公开视图；保存来源记录。

验收：同样输入基线重复生成一致；不将 raw 第三方目录全部打包；缺资料则 blocked_external。

### P03.T3｜实现可解释差异

行动：实现字段索引和三方/可选目标 D 分析，输出每项来源和推断界限。

验收：本地正常定制不自动 blocker；没有 D 时不声称最终目标配置已验证。

## 本阶段验收命令

以下为实现完成后的目标验证命令。缺少脚本/测试时先完成本阶段对应交付，不能伪造命令执行。

```bash
python -m pytest tests/unit/test_three_way.py tests/contract/test_private_comparison.py -q
```

## 硬闸门

- 公开字段差异准确且可追溯；处理新增/删除/类型差别。
- 真实基线已固定，不能用 main 作为版本事实。
- 不执行自动合并或写回源文件。

## 本阶段不做

不生成升级 shell、不自动改 DB_HOST、不推断服务重命名、不以 diff 数作为安全评分。

## 最后交付

按 templates/HANDOFF.md 写本阶段记录；使用真实证据。给出是否达到 ready_for_review、哪些事项仍需我审阅。不要将本阶段自设为 done，不继续下阶段。

---

# P04｜规则目录、证据信任与完整性判定 — 可直接交给 Codex

你现在只负责 Dify Upgrade Preflight 的 P04 阶段。

目标：让规则目录和支持边成为有验证边界的数据，而不是加载任意 YAML 后自称安全。

前置：P03；默认业务范围仍以根目录契约为准。


执行纪律：
1. 只做本阶段；先确认前置阶段 done 和实际批准记录。初始 P00 以首次启动提示词授权进入。
2. 阅读固定入口及本阶段文件。验证契约锁、现有工作树与已有失败，保留用户改动。
3. 先写本任务失败测试/事实裁决，再实现最小行为。任何判断缺证据必须明确标记，不靠合理猜测。
4. 不修改验收条件/基线哈希，不扩大支持，不增加未批准核心依赖，不改变默认权限。
5. 运行当前已存在且适用的命令；没有环境标 blocked_external，未批准动作标 blocked_review。不能把预期输出当实际执行。
6. 输出脱敏证据、实际命令/返回码/耗时、文件清单、未通过项和下一步。更新 roadmap 允许字段，完成后停在 ready_for_review。
7. 不commit/push/tag/release，不修改生产文件/数据库/volumes。实验动作另需授权。不要自动开始下一阶段。


## 本阶段补充阅读

- `docs/RULES_AND_EVIDENCE.md`
- `docs/DATA_CONTRACTS.md`
- `docs/SUPPORT_MATRIX.md`
- `catalog/README.md`
- `governance/README.md`

## 输入/输出接口

load_catalog(path, policy)->Catalog，evaluate(snapshot, request, catalog)->Report；未经信任的 catalog 不得给 NO_KNOWN_BLOCKERS。

## 预期写入的文件或目录

- `src/dify_preflight/catalog/load.py`
- `src/dify_preflight/catalog/validate.py`
- `src/dify_preflight/engine/evaluate.py`
- `tests/contract/test_catalog_trust.py`
- `tests/unit/test_rule_lifecycle.py`
- `scripts/validate_catalog.py`

`<run_id>` 必须替换为实际唯一运行标识；这些是执行产物路径，不是已存在的证据。

## 顺序任务

### P04.T1｜先拒绝坏目录

行动：测试错哈希、无审批、重复ID、未知schema、脚本键、深度超限、空ALL和来源缺失。

验收：不读取目录外文件、不执行任何规则内容；结构损坏统一 ERROR。

### P04.T2｜完成三值与生命周期

行动：实现限定操作符、applies/assertion、显式 exact-edge、supersedes 作用域和 source/target一致性。

验收：正反未知及版本边界测试全过；A→B+B→C不推导A→C；旧边不被新规则误退休。

### P04.T3｜聚合 coverage 与 verdict

行动：按契约处理无支持边、关键缺口、blocked+unknown、范围外未检查；固定decision_digest。

验收：V01–V06和32组合通过；不会因为没有规则匹配就放行；时间变化不影响判定摘要。

## 本阶段验收命令

以下为实现完成后的目标验证命令。缺少脚本/测试时先完成本阶段对应交付，不能伪造命令执行。

```bash
python -m pytest tests/contract/test_catalog_trust.py tests/unit/test_rule_lifecycle.py tests/contract/test_verdict.py -q
python scripts/validate_catalog.py --catalog catalog/support-matrix.yaml  # 允许空规划矩阵，不宣称支持
```

## 硬闸门

- 固定schema、来源、审批、支持边和目录信任一起被验证。
- 引擎仍是纯函数；不为无法判断的状态补默认安全值。
- 规则文件不能携带可执行恢复动作。

## 本阶段不做

不开发通用DSL、插件执行器、规则在线商店或自动批准器。

## 最后交付

按 templates/HANDOFF.md 写本阶段记录；使用真实证据。给出是否达到 ready_for_review、哪些事项仍需我审阅。不要将本阶段自设为 done，不继续下阶段。

---

# P05｜真实升级案例与首批规则 — 可直接交给 Codex

你现在只负责 Dify Upgrade Preflight 的 P05 阶段。

目标：用真实固定证据验证产品价值，形成首批经过人工批准的规则与精确支持边。

前置：P04；默认业务范围仍以根目录契约为准。


执行纪律：
1. 只做本阶段；先确认前置阶段 done 和实际批准记录。初始 P00 以首次启动提示词授权进入。
2. 阅读固定入口及本阶段文件。验证契约锁、现有工作树与已有失败，保留用户改动。
3. 先写本任务失败测试/事实裁决，再实现最小行为。任何判断缺证据必须明确标记，不靠合理猜测。
4. 不修改验收条件/基线哈希，不扩大支持，不增加未批准核心依赖，不改变默认权限。
5. 运行当前已存在且适用的命令；没有环境标 blocked_external，未批准动作标 blocked_review。不能把预期输出当实际执行。
6. 输出脱敏证据、实际命令/返回码/耗时、文件清单、未通过项和下一步。更新 roadmap 允许字段，完成后停在 ready_for_review。
7. 不commit/push/tag/release，不修改生产文件/数据库/volumes。实验动作另需授权。不要自动开始下一阶段。


## 本阶段补充阅读

- `catalog/candidates.yaml`
- `sources/pinned.yaml`
- `docs/RULES_AND_EVIDENCE.md`
- `docs/TEST_STRATEGY.md`
- `templates/RULE_REVIEW.md`

## 输入/输出接口

把已固定、已裁决的事实映射成真实 Rule/SupportEdge；不能将 examples synthetic rule 改名冒充真实规则。

## 预期写入的文件或目录

- `catalog/candidates/`
- `catalog/approved/`
- `catalog/support-matrix.yaml`
- `tests/fixtures/adjudicated/`
- `tests/fixtures/heldout/`
- `tests/contract/test_real_rules.py`
- `artifacts/P05/<run_id>/RULE_REVIEW_SET.md`

`<run_id>` 必须替换为实际唯一运行标识；这些是执行产物路径，不是已存在的证据。

## 顺序任务

### P05.T1｜逐项裁决根因

行动：为候选规则写审核卡，区分before/during/after和已知/未知历史，建立不适用画像。

验收：至少6个独立根因家族，不凑版本变体；关键事实有固定官方来源，冲突明确保留。

### P05.T2｜先写真实与holdout预期

行动：由来源和人工裁决定义正例/反例/未知/边界；另外留 heldout，不从实现生成答案。

验收：至少30个边界/反例/未知；没有“新部署也要迁移”等误报；审查者能重查每个expected。

### P05.T3｜实现并申请规则晋升

行动：逐条实现 candidate，跑全套并做关键变异；准备两条支持边审批，未经owner批准不放approved。

验收：测试集 false-safe=0；多余blocker=0；每条approved有实际审批digest；批准前保持零或已有真实支持。

## 本阶段验收命令

以下为实现完成后的目标验证命令。缺少脚本/测试时先完成本阶段对应交付，不能伪造命令执行。

```bash
python -m pytest tests/contract/test_real_rules.py -q
python scripts/validate_catalog.py --catalog catalog/approved
python scripts/validate_governance.py
```

## 硬闸门

- 不能达到有效检测目标就申请缩范围或停止，不堆泛化warning。
- 两条批准边和真实规则须有owner审阅，阶段必须停在规则审核门。
- 当前版本与历史迁移、bundled与external、新部署与持久数据被区分。

## 本阶段不做

不通过自动执行升级验证规则、不读取真实数据库、不复制聊天中的版本条件。

## 最后交付

按 templates/HANDOFF.md 写本阶段记录；使用真实证据。给出是否达到 ready_for_review、哪些事项仍需我审阅。不要将本阶段自设为 done，不继续下阶段。

---

# P06｜CLI 产品化与可安装分发 — 可直接交给 Codex

你现在只负责 Dify Upgrade Preflight 的 P06 阶段。

目标：让新用户能按清晰输入得到稳定且脱敏的报告，而非只能运行开发样例。

前置：P05；默认业务范围仍以根目录契约为准。


执行纪律：
1. 只做本阶段；先确认前置阶段 done 和实际批准记录。初始 P00 以首次启动提示词授权进入。
2. 阅读固定入口及本阶段文件。验证契约锁、现有工作树与已有失败，保留用户改动。
3. 先写本任务失败测试/事实裁决，再实现最小行为。任何判断缺证据必须明确标记，不靠合理猜测。
4. 不修改验收条件/基线哈希，不扩大支持，不增加未批准核心依赖，不改变默认权限。
5. 运行当前已存在且适用的命令；没有环境标 blocked_external，未批准动作标 blocked_review。不能把预期输出当实际执行。
6. 输出脱敏证据、实际命令/返回码/耗时、文件清单、未通过项和下一步。更新 roadmap 允许字段，完成后停在 ready_for_review。
7. 不commit/push/tag/release，不修改生产文件/数据库/volumes。实验动作另需授权。不要自动开始下一阶段。


## 本阶段补充阅读

- `docs/CLI_CONTRACT.md`
- `docs/DATA_CONTRACTS.md`
- `docs/DEPENDENCIES_AND_ENVIRONMENT.md`
- `docs/RELEASE_AND_MAINTENANCE.md`

## 输入/输出接口

完成 snapshot/check/demo 与三种格式、0/1/2/3/4/5/64/130退出码；raw用户输入不能进入traceback。

## 预期写入的文件或目录

- `src/dify_preflight/report/json.py`
- `src/dify_preflight/report/text.py`
- `src/dify_preflight/report/markdown.py`
- `tests/contract/test_cli.py`
- `tests/integration/test_wheel_install.py`
- `docs/USER_GUIDE.md`

`<run_id>` 必须替换为实际唯一运行标识；这些是执行产物路径，不是已存在的证据。

## 顺序任务

### P06.T1｜固定黑盒协议

行动：编写参数错误、各种verdict、输出冲突、JSON stdout干净、NO_COLOR、中断的黑盒测试。

验收：参数错exit64；BLOCKED exit2；格式切换不改业务结果；没有隐藏skip-required。

### P06.T2｜完善报告与安装

行动：展示关键风险、官方证据、declared/observed区别、人工步骤和excluded；构建wheel/sdist并隔离安装。

验收：新环境能运行帮助/demo/check；包内不含未批准规则、raw配置、日志和大来源包。

### P06.T3｜写真实用户路径

行动：写最短示例和限制，解释准备脱敏快照、指定版本、处理INCOMPLETE和UNSUPPORTED。

验收：文档命令逐条以存在的合成/审核数据执行；不写未发布pip命令为已上线。

## 本阶段验收命令

以下为实现完成后的目标验证命令。缺少脚本/测试时先完成本阶段对应交付，不能伪造命令执行。

```bash
python -m pytest tests/contract/test_cli.py tests/integration/test_wheel_install.py -q
python -m build
```

## 硬闸门

- 干净环境安装成功；CLI与schema/退出码一致。
- 报告能让维护者指出下一项人工行动，不靠大段模糊建议。
- 仅本地构建，尚未发布或push。

## 本阶段不做

不做GUI、GitHub App、市场推广自动化、自动升级计划执行。

## 最后交付

按 templates/HANDOFF.md 写本阶段记录；使用真实证据。给出是否达到 ready_for_review、哪些事项仍需我审阅。不要将本阶段自设为 done，不继续下阶段。

---

# P07｜安全、边界和性能硬化 — 可直接交给 Codex

你现在只负责 Dify Upgrade Preflight 的 P07 阶段。

目标：用敌意输入、独立反例与原始基准数据检验首版是否达到工程验收。

前置：P06；默认业务范围仍以根目录契约为准。


执行纪律：
1. 只做本阶段；先确认前置阶段 done 和实际批准记录。初始 P00 以首次启动提示词授权进入。
2. 阅读固定入口及本阶段文件。验证契约锁、现有工作树与已有失败，保留用户改动。
3. 先写本任务失败测试/事实裁决，再实现最小行为。任何判断缺证据必须明确标记，不靠合理猜测。
4. 不修改验收条件/基线哈希，不扩大支持，不增加未批准核心依赖，不改变默认权限。
5. 运行当前已存在且适用的命令；没有环境标 blocked_external，未批准动作标 blocked_review。不能把预期输出当实际执行。
6. 输出脱敏证据、实际命令/返回码/耗时、文件清单、未通过项和下一步。更新 roadmap 允许字段，完成后停在 ready_for_review。
7. 不commit/push/tag/release，不修改生产文件/数据库/volumes。实验动作另需授权。不要自动开始下一阶段。


## 本阶段补充阅读

- `ACCEPTANCE_CONTRACT.md`
- `docs/TEST_STRATEGY.md`
- `docs/PERFORMANCE_PLAN.md`
- `SAFETY_CONTRACT.md`

## 输入/输出接口

不更改公开行为以美化指标；性能优化前后Report语义/digest必须一致。

## 预期写入的文件或目录

- `tests/security/test_secret_outputs.py`
- `tests/security/test_hostile_inputs.py`
- `tests/performance/`
- `scripts/benchmark.py`
- `artifacts/P07/<run_id>/QUALITY_REPORT.md`

`<run_id>` 必须替换为实际唯一运行标识；这些是执行产物路径，不是已存在的证据。

## 顺序任务

### P07.T1｜安全负控与变异

行动：运行所有输出的secret canary、路径/进程/网络禁止测试，并手动或工具变异关键版本/UNKNOWN/approval条件。

验收：关键变异被杀死；输入未改；无 secret 泄露；无非授权I/O。

### P07.T2｜真实性能基准

行动：固定medium/stress和参考环境，5预热+30正式样本，分别记录纯check和Compose采集。

验收：原始数据完整；满足p95/RSS/超时阈值或明确未通过，不以平均值替代。

### P07.T3｜基于profile优化

行动：定位重复parse/扫描/进程，做最小优化并回归；审查错误路径/输出限额。

验收：所有正确性/隐私保持；无新增核心依赖；快测试在预算内或有审批后的拆分方案。

## 本阶段验收命令

以下为实现完成后的目标验证命令。缺少脚本/测试时先完成本阶段对应交付，不能伪造命令执行。

```bash
python -m pytest tests/unit tests/contract tests/security -q
python scripts/benchmark.py --profile medium --warmup 5 --runs 30
python scripts/benchmark.py --profile stress --warmup 5 --runs 30
python scripts/validate_governance.py
```

## 硬闸门

- 关键已裁决数据false-safe=0、额外blocker=0；全部secret canary为0泄露。
- 验收中的性能指标有实际证据并达标；未测不得通过。
- 性能改动没有减少required checks或放宽输入保护。

## 本阶段不做

不改验收阈值、不增加后台服务/缓存数据库/GPU，不用玩具负载掩盖问题。

## 最后交付

按 templates/HANDOFF.md 写本阶段记录；使用真实证据。给出是否达到 ready_for_review、哪些事项仍需我审阅。不要将本阶段自设为 done，不继续下阶段。

---

# P08｜独立环境重演与 beta 验收 — 可直接交给 Codex

你现在只负责 Dify Upgrade Preflight 的 P08 阶段。

目标：在明确授权的独立实验环境中，用合成数据验证实际采集和至少一条真实升级案例。

前置：P07；默认业务范围仍以根目录契约为准。


执行纪律：
1. 只做本阶段；先确认前置阶段 done 和实际批准记录。初始 P00 以首次启动提示词授权进入。
2. 阅读固定入口及本阶段文件。验证契约锁、现有工作树与已有失败，保留用户改动。
3. 先写本任务失败测试/事实裁决，再实现最小行为。任何判断缺证据必须明确标记，不靠合理猜测。
4. 不修改验收条件/基线哈希，不扩大支持，不增加未批准核心依赖，不改变默认权限。
5. 运行当前已存在且适用的命令；没有环境标 blocked_external，未批准动作标 blocked_review。不能把预期输出当实际执行。
6. 输出脱敏证据、实际命令/返回码/耗时、文件清单、未通过项和下一步。更新 roadmap 允许字段，完成后停在 ready_for_review。
7. 不commit/push/tag/release，不修改生产文件/数据库/volumes。实验动作另需授权。不要自动开始下一阶段。


## 本阶段补充阅读

- `SAFETY_CONTRACT.md`
- `docs/RELEASE_AND_MAINTENANCE.md`
- `docs/SUPPORT_MATRIX.md`
- `templates/TEST_RUN.md`

## 输入/输出接口

本阶段实验不是产品自动升级功能。先提交命令/镜像/资源计划，用户批准后才在独立VM/daemon执行。

## 预期写入的文件或目录

- `artifacts/P08/<run_id>/LAB_PLAN.md`
- `artifacts/P08/<run_id>/REHEARSAL.md`
- `tests/integration/test_lab_regression.py`
- `artifacts/P08/<run_id>/BETA_READINESS.md`

`<run_id>` 必须替换为实际唯一运行标识；这些是执行产物路径，不是已存在的证据。

## 顺序任务

### P08.T1｜准备可审查实验

行动：列明独立资源、合成数据、固定镜像/版本、命令副作用和回收方法；验证不是生产context。

验收：未批准前不启动服务；无环境记blocked_external；无需读取真实凭据。

### P08.T2｜验证三种画像与重演

行动：覆盖bundled持久数据、fresh、external/不适用等至少三画像；独立跑已批准检查和一条真正升级重演。

验收：报告与实际观察对应；不把启动成功等同向量检索/迁移成功；相应不变量有具体验证。

### P08.T3｜beta质量裁决

行动：核对误报/未知比例、安装/性能/隐私和未支持项；形成只限矩阵的beta声明。

验收：不满足就保持blocked；真实升级测试与synthetic明确分开；不自动发布。

## 本阶段验收命令

以下为实现完成后的目标验证命令。缺少脚本/测试时先完成本阶段对应交付，不能伪造命令执行。

```bash
python -m pytest tests/integration/test_lab_regression.py -q  # 仅独立实验授权且环境已准备后
python scripts/validate_catalog.py --catalog catalog/approved
```

## 硬闸门

- 独立实验许可与真实执行证据存在。
- 至少一个已批准升级边重演、三个不同部署画像，结果与报告可核对。
- beta说明不超过已测范围；有错误放行立即冻结。

## 本阶段不做

不在当前生产Docker context试验、不调用down -v/prune、不读业务数据、不自动发包。

## 最后交付

按 templates/HANDOFF.md 写本阶段记录；使用真实证据。给出是否达到 ready_for_review、哪些事项仍需我审阅。不要将本阶段自设为 done，不继续下阶段。

---

# P09｜发布审批、真实反馈与稳定版判断 — 可直接交给 Codex

你现在只负责 Dify Upgrade Preflight 的 P09 阶段。

目标：交付可审阅的发布产物，并在明确授权后发布和用真实使用反馈决定稳定化。

前置：P08；默认业务范围仍以根目录契约为准。


执行纪律：
1. 只做本阶段；先确认前置阶段 done 和实际批准记录。初始 P00 以首次启动提示词授权进入。
2. 阅读固定入口及本阶段文件。验证契约锁、现有工作树与已有失败，保留用户改动。
3. 先写本任务失败测试/事实裁决，再实现最小行为。任何判断缺证据必须明确标记，不靠合理猜测。
4. 不修改验收条件/基线哈希，不扩大支持，不增加未批准核心依赖，不改变默认权限。
5. 运行当前已存在且适用的命令；没有环境标 blocked_external，未批准动作标 blocked_review。不能把预期输出当实际执行。
6. 输出脱敏证据、实际命令/返回码/耗时、文件清单、未通过项和下一步。更新 roadmap 允许字段，完成后停在 ready_for_review。
7. 不commit/push/tag/release，不修改生产文件/数据库/volumes。实验动作另需授权。不要自动开始下一阶段。


## 本阶段补充阅读

- `docs/RELEASE_AND_MAINTENANCE.md`
- `docs/CLI_CONTRACT.md`
- `docs/DEVELOPMENT_PROTOCOL.md`
- `prompts/RELEASE_AUTHORIZATION.md`

## 输入/输出接口

发布行为须绑定代码/包/catalog digest与目标渠道；稳定性只基于真实反馈，不自动提升版本标签。

## 预期写入的文件或目录

- `README.md`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `artifacts/P09/<run_id>/RELEASE_CANDIDATE.md`
- `artifacts/P09/<run_id>/PILOT_FEEDBACK.md`
- `artifacts/P09/<run_id>/STABLE_DECISION.md`

`<run_id>` 必须替换为实际唯一运行标识；这些是执行产物路径，不是已存在的证据。

## 顺序任务

### P09.T1｜准备发布而非自动上传

行动：构建校验包、许可归属、支持矩阵、真实demo、隐私/已知局限；输出精确待发布digest和命令计划。

验收：无秘密/未批准规则；发行说明不承诺安全；没有凭据也能完成本地候选。

### P09.T2｜授权后执行指定发布

行动：仅在owner明确授权对应渠道/内容时才commit/push/tag/upload；否则停ready_for_review。

验收：实际发布结果可核对；禁止把计划或本地build当已上线。

### P09.T3｜收集复用证据

行动：获得至少3画像、2独立维护者的脱敏使用反馈，记录有效发现/误报/unknown/复用；写继续、收缩或停止结论。

验收：没有足够反馈保持beta；不使用星标数或下载噪声替代实际价值。

## 本阶段验收命令

以下为实现完成后的目标验证命令。缺少脚本/测试时先完成本阶段对应交付，不能伪造命令执行。

```bash
python -m build
python -m pytest tests/integration/test_wheel_install.py -q
python scripts/validate_catalog.py --catalog catalog/approved
```

## 硬闸门

- 实际发布需要独立授权；未授权可交付候选，但本阶段不得伪完成。
- 两位独立维护者和三个画像的证据达到目标，否则稳定版门未通过。
- 发生false-safe/泄密按事件流程处理，不继续营销。

## 本阶段不做

不默认遥测、不索取真实.env、不伪造用户推荐/采用数量、不自动发社区广告。

## 最后交付

按 templates/HANDOFF.md 写本阶段记录；使用真实证据。给出是否达到 ready_for_review、哪些事项仍需我审阅。不要将本阶段自设为 done，不继续下阶段。

---

# P10｜可选运行事实探测（后续版本） — 可直接交给 Codex

你现在只负责 Dify Upgrade Preflight 的 P10 阶段。

目标：仅在首版被复用后，补充声明态与实际容器版本的差异；不开启数据库业务访问。

前置：P09；默认业务范围仍以根目录契约为准。


执行纪律：
1. 只做本阶段；先确认前置阶段 done 和实际批准记录。初始 P00 以首次启动提示词授权进入。
2. 阅读固定入口及本阶段文件。验证契约锁、现有工作树与已有失败，保留用户改动。
3. 先写本任务失败测试/事实裁决，再实现最小行为。任何判断缺证据必须明确标记，不靠合理猜测。
4. 不修改验收条件/基线哈希，不扩大支持，不增加未批准核心依赖，不改变默认权限。
5. 运行当前已存在且适用的命令；没有环境标 blocked_external，未批准动作标 blocked_review。不能把预期输出当实际执行。
6. 输出脱敏证据、实际命令/返回码/耗时、文件清单、未通过项和下一步。更新 roadmap 允许字段，完成后停在 ready_for_review。
7. 不commit/push/tag/release，不修改生产文件/数据库/volumes。实验动作另需授权。不要自动开始下一阶段。


## 本阶段补充阅读

- `docs/ARCHITECTURE.md`
- `SAFETY_CONTRACT.md`
- `docs/DATA_CONTRACTS.md`
- `templates/CHANGE_REQUEST.md`

## 输入/输出接口

先提交live_opt_in CaptureRequest扩展设计；observed事实保留来源与采集时间，不覆盖declared。

## 预期写入的文件或目录

- `artifacts/P10/<run_id>/RUNTIME_DESIGN.md`
- `src/dify_preflight/collect/runtime.py`
- `tests/security/test_runtime_permissions.py`
- `tests/integration/test_runtime_observation.py`

`<run_id>` 必须替换为实际唯一运行标识；这些是执行产物路径，不是已存在的证据。

## 顺序任务

### P10.T1｜验证需求并申请权限扩展

行动：从真实反馈证明运行差异是主要缺口；设计只读API允许集、对象范围、输出脱敏和默认关闭。

验收：没有用户价值或权限审批就保持deferred；socket ro挂载不当成权限控制。

### P10.T2｜实现受限容器元数据读取

行动：限定显式项目/容器和只读操作；比较tag/digest与声明，不exec、不生命周期控制。

验收：权限失败变unknown；实际image与配置不同能检测；无任意container遍历和秘密Env导出。

### P10.T3｜回归默认离线行为

行动：验证未启用时不存在任何Docker调用；新能力需要独立矩阵和安装测试。

验收：v0.1行为/性能不倒退；新增字段schema版本和兼容性有审批。

## 本阶段验收命令

以下为实现完成后的目标验证命令。缺少脚本/测试时先完成本阶段对应交付，不能伪造命令执行。

```bash
python -m pytest tests/security/test_runtime_permissions.py tests/integration/test_runtime_observation.py -q
```

## 硬闸门

- 需求和权限扩展先批准，才能写新I/O。
- 观察值可证明来自指定对象，错误时不回退为声明值冒充观测。
- 数据库探测仍需另一个设计/审批，不顺便加进去。

## 本阶段不做

不加入自动升级、数据库连接、SSH自动发现、Kubernetes、多平台框架。

## 最后交付

按 templates/HANDOFF.md 写本阶段记录；使用真实证据。给出是否达到 ready_for_review、哪些事项仍需我审阅。不要将本阶段自设为 done，不继续下阶段。

---

# P11｜规则维护机制与上游协作 — 可直接交给 Codex

你现在只负责 Dify Upgrade Preflight 的 P11 阶段。

目标：建立可重复的新版本审查流程，保持旧支持边可靠，而不是无限扩展范围。

前置：P09；默认业务范围仍以根目录契约为准。


执行纪律：
1. 只做本阶段；先确认前置阶段 done 和实际批准记录。初始 P00 以首次启动提示词授权进入。
2. 阅读固定入口及本阶段文件。验证契约锁、现有工作树与已有失败，保留用户改动。
3. 先写本任务失败测试/事实裁决，再实现最小行为。任何判断缺证据必须明确标记，不靠合理猜测。
4. 不修改验收条件/基线哈希，不扩大支持，不增加未批准核心依赖，不改变默认权限。
5. 运行当前已存在且适用的命令；没有环境标 blocked_external，未批准动作标 blocked_review。不能把预期输出当实际执行。
6. 输出脱敏证据、实际命令/返回码/耗时、文件清单、未通过项和下一步。更新 roadmap 允许字段，完成后停在 ready_for_review。
7. 不commit/push/tag/release，不修改生产文件/数据库/volumes。实验动作另需授权。不要自动开始下一阶段。


## 本阶段补充阅读

- `docs/RELEASE_AND_MAINTENANCE.md`
- `docs/RULES_AND_EVIDENCE.md`
- `prompts/NEXT_RELEASE_RULES.md`
- `prompts/INCIDENT_FALSE_SAFE.md`

## 输入/输出接口

新release只能产生candidate；代码版本与catalog版本独立；撤回规则和新批准均保留来源。

## 预期写入的文件或目录

- `scripts/build_catalog.py`
- `artifacts/P11/<run_id>/NEW_RELEASE_REVIEW.md`
- `artifacts/P11/<run_id>/MAINTENANCE_BUDGET.md`
- `tests/contract/test_catalog_update_regression.py`

`<run_id>` 必须替换为实际唯一运行标识；这些是执行产物路径，不是已存在的证据。

## 顺序任务

### P11.T1｜建立手动更新闭环

行动：输入显式release，固定内容、列出diff/潜在supersession，生成候选审查材料，不运行第三方内容。

验收：新候选不自动进入approved；已批准旧边不因目录更新失效。

### P11.T2｜做一次维护演练

行动：模拟新手工步骤被自动化、来源变更、旧规则撤回与false-safe修复；回归旧fixtures。

验收：所有变更有审批digest；未经批准的规则不能影响产品放行。

### P11.T3｜评估可持续性

行动：记录一次更新的人工作业、检测价值和风险；准备上游issue/PR草稿，仅授权后发送。

验收：维护成本超过收益时冻结支持范围；自动定时任务/发PR不默认启用。

## 本阶段验收命令

以下为实现完成后的目标验证命令。缺少脚本/测试时先完成本阶段对应交付，不能伪造命令执行。

```bash
python -m pytest tests/contract/test_catalog_update_regression.py -q
python scripts/validate_catalog.py --catalog catalog/approved
```

## 硬闸门

- 完成一次真实或清楚标注的维护演练，不声称维护工作永久完成。
- 新规则审查与旧路径回归机制存在。
- 公开贡献/自动化仍需单独授权。

## 本阶段不做

不为了star立即扩展n8n/Open WebUI、不自动批准规则、不擅自开启后台任务。

## 最后交付

按 templates/HANDOFF.md 写本阶段记录；使用真实证据。给出是否达到 ready_for_review、哪些事项仍需我审阅。不要将本阶段自设为 done，不继续下阶段。
