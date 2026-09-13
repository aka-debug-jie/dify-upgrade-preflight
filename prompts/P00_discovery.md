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
