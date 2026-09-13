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
