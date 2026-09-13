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
