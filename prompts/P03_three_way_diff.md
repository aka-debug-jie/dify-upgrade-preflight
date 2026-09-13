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
