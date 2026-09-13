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
