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
