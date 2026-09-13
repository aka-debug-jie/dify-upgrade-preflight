# P06｜CLI 产品化与可安装分发 — 可直接交给 Codex

你现在只负责 Dify Upgrade Preflight 的 P06 阶段。

目标：让新用户能按清晰输入得到稳定且脱敏的报告，而非只能运行开发样例。

前置：P05；默认业务范围仍以根目录契约为准。


执行纪律：
1. 只做本阶段；先确认前置阶段 done 和实际批准记录。初始 P00 以首次启动提示词授权进入。
2. 阅读固定入口及本阶段文件。验证契约锁、现有工作树与已有失败，保留用户改动。
3. 先写本任务失败测试/事实裁决，再实现最小行为。任何判断缺证据必须明确标记，不靠合理猜测。
4. 不修改验收条件/基线哈希，不扩大支持，不增加未批准核心依赖，不改变默认权限。
5. 运行当前已存在且适用的命令；没有环境标 blocked_external，未批准动作标 blocked_review。不能把预期输出当实际执行。
6. 输出脱敏证据、实际命令/返回码/耗时、文件清单、未通过项和下一步。更新 roadmap 允许字段，完成后停在 ready_for_review。
7. 不commit/push/tag/release，不修改生产文件/数据库/volumes。实验动作另需授权。不要自动开始下一阶段。


## 本阶段补充阅读

- `docs/CLI_CONTRACT.md`
- `docs/DATA_CONTRACTS.md`
- `docs/DEPENDENCIES_AND_ENVIRONMENT.md`
- `docs/RELEASE_AND_MAINTENANCE.md`

## 输入/输出接口

完成 snapshot/check/demo 与三种格式、0/1/2/3/4/5/64/130退出码；raw用户输入不能进入traceback。

## 预期写入的文件或目录

- `src/dify_preflight/report/json.py`
- `src/dify_preflight/report/text.py`
- `src/dify_preflight/report/markdown.py`
- `tests/contract/test_cli.py`
- `tests/integration/test_wheel_install.py`
- `docs/USER_GUIDE.md`

`<run_id>` 必须替换为实际唯一运行标识；这些是执行产物路径，不是已存在的证据。

## 顺序任务

### P06.T1｜固定黑盒协议

行动：编写参数错误、各种verdict、输出冲突、JSON stdout干净、NO_COLOR、中断的黑盒测试。

验收：参数错exit64；BLOCKED exit2；格式切换不改业务结果；没有隐藏skip-required。

### P06.T2｜完善报告与安装

行动：展示关键风险、官方证据、declared/observed区别、人工步骤和excluded；构建wheel/sdist并隔离安装。

验收：新环境能运行帮助/demo/check；包内不含未批准规则、raw配置、日志和大来源包。

### P06.T3｜写真实用户路径

行动：写最短示例和限制，解释准备脱敏快照、指定版本、处理INCOMPLETE和UNSUPPORTED。

验收：文档命令逐条以存在的合成/审核数据执行；不写未发布pip命令为已上线。

## 本阶段验收命令

以下为实现完成后的目标验证命令。缺少脚本/测试时先完成本阶段对应交付，不能伪造命令执行。

```bash
python -m pytest tests/contract/test_cli.py tests/integration/test_wheel_install.py -q
python -m build
```

## 硬闸门

- 干净环境安装成功；CLI与schema/退出码一致。
- 报告能让维护者指出下一项人工行动，不靠大段模糊建议。
- 仅本地构建，尚未发布或push。

## 本阶段不做

不做GUI、GitHub App、市场推广自动化、自动升级计划执行。

## 最后交付

按 templates/HANDOFF.md 写本阶段记录；使用真实证据。给出是否达到 ready_for_review、哪些事项仍需我审阅。不要将本阶段自设为 done，不继续下阶段。
