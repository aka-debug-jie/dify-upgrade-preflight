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
