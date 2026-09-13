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
