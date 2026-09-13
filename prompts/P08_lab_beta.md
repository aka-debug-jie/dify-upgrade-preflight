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
