# P01｜最小可运行闭环与核心契约 — 可直接交给 Codex

你现在只负责 Dify Upgrade Preflight 的 P01 阶段。

目标：先让一个合成快照经过纯规则判定输出正确 JSON 和退出码，再建立可安装的小包。

前置：P00；默认业务范围仍以根目录契约为准。


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
- `docs/DATA_CONTRACTS.md`
- `docs/CLI_CONTRACT.md`
- `specs/README.md`
- `examples/README.md`
- `docs/DEVELOPMENT_PROTOCOL.md`

## 输入/输出接口

实现 TruthValue、Fact、Rule、Report 及 evaluate_expression/evaluate 的 synthetic 子集；demo 是唯一演示入口，不能接受 synthetic 为真实生产结论。

## 预期写入的文件或目录

- `pyproject.toml`
- `src/dify_preflight/domain.py`
- `src/dify_preflight/engine/expressions.py`
- `src/dify_preflight/engine/verdict.py`
- `src/dify_preflight/cli.py`
- `tests/unit/test_truth_table.py`
- `tests/contract/test_verdict.py`
- `tests/contract/test_demo.py`
- `scripts/validate_governance.py`

`<run_id>` 必须替换为实际唯一运行标识；这些是执行产物路径，不是已存在的证据。

## 顺序任务

### P01.T1｜把数据与判定规格转为失败测试

行动：按 schema 定义最小类型，锁定 examples 和全部 verdict-cases；测试在功能未实现时应失败。

验收：known false != unknown；32种 verdict 组合和目标退出码精确一致。

### P01.T2｜实现单条合成路径

行动：实现规则 applies/assertion、纯 evaluator、小型 argparse demo；true/false/unknown 三个输入都走完整输出。

验收：原始样例输出 BLOCKED；改变条件为 true 不再失败；未知给 INCOMPLETE；三个结果都 synthetic。

### P01.T3｜打包并保护契约

行动：只安装 P00 批准依赖，定义 .[dev]，建立本地验证命令与 governance 校验器；创建新的虚拟环境验证导入。

验收：--help/demo 可运行；拒绝被改的受保护文件；没有空框架冒充完成；记录首个未达标也真实的性能 baseline。

## 本阶段验收命令

以下为实现完成后的目标验证命令。缺少脚本/测试时先完成本阶段对应交付，不能伪造命令执行。

```bash
python -m pytest tests/unit/test_truth_table.py tests/contract/test_verdict.py tests/contract/test_demo.py -q
python -m dify_preflight demo --case blocked --format json  # 预期 exit 2
python scripts/validate_governance.py
```

## 硬闸门

- 一个可安装的端到端 synthetic 演示成立。
- 纯 evaluator 无网络/子进程；schema/退出码与冻结数据一致。
- 类型/包装/初始快测试通过；无真实 Dify 支持声明。

## 本阶段不做

不做 Docker 采集、网络下载、真实规则批准、完整插件架构和 Web UI。

## 最后交付

按 templates/HANDOFF.md 写本阶段记录；使用真实证据。给出是否达到 ready_for_review、哪些事项仍需我审阅。不要将本阶段自设为 done，不继续下阶段。
