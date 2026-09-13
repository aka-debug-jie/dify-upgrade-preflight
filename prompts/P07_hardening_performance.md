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
