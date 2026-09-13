# 测试策略：阻止虚假放行，而不是堆测试数量

## 1. 四类测试材料必须分开

| 材料 | 来源 | 能证明什么 |
|---|---|---|
| synthetic | 人为设计 | 引擎和协议按约定工作 |
| adjudicated | 固定官方来源、人工裁决 | 已知规则和边界正确 |
| heldout | 人工另选、实现时不据此调规则 | 有限的泛化和噪声检查 |
| rehearsal | 独立实验环境真实采集/升级 | 限定环境中行为与规则一致 |

不得把 synthetic 运行成功写成 Dify 升级通过；不得让实现者修改预期值来匹配错误实现。

## 2. 最低覆盖

- 三值逻辑全真值表；缺失、不适用、false、null 的不同处理。
- verdict 优先级，包括 BLOCKED 与 UNKNOWN 并存、无支持边、catalog 损坏。
- 版本比较：1.9/1.10、前导 v、相等、边界前后、pre-release、latest、自定义 tag。
- 三方 diff 六类 + MISSING/null/空/false/0 + 列表顺序和唯一键。
- Compose：锚点、环境插值、显式 env-file、shell 覆盖、profile、override 顺序、无 daemon、缺原生解析器。
- 采集安全：越界 symlink、远程 include、恶意标签、别名膨胀、重复键、超大文件、FIFO、恶意 stderr、shell 字符串。
- 隐私：TOKEN/PASSWORD/未知变量/URL query/DSN/PEM/命令中秘密等 canary，覆盖每个输出路径。
- 目录信任：摘要错、未批准规则、无审批、审批内容改变、重复规则 ID、未知 schema、无支持边。
- CLI：安装包与源码行为一致；stdout JSON 纯净；所有格式退出码一致；用户中断和输出路径冲突。

机器可读场景入口：`specs/fixtures/cases.yaml` 和 `specs/fixtures/verdict-cases.json`。

## 3. 测试先于实现

每个任务的测试先失败；记录是预期功能失败，而不是环境缺失导致的偶然失败；实现最小行为；再跑本任务和受影响契约。

P01 起关键引擎用固定输入/期望 JSON，不从实现函数生成 golden。更新 golden 需要说明语义变更和批准记录。

## 4. 变异与负控

故意将版本 `<` 改 `<=`、将 UNKNOWN 当 FALSE、交换 verdict 优先级、忽略 rule approval、以 redacted 字符串比较秘密。关键变异必须被已有测试发现。

反例包括：新部署没有旧持久数据；外部数据库不受 bundled image 更新影响；迁移已经按证据完成；本地自定义符合目标而非冲突；历史来源不可知。

## 5. 真实规则的裁决卡

每个根因：固定来源 → 受影响状态 → 不受影响状态 → 未知状态 → 升级动作所处阶段 → 预期报告 → 实验或代码印证 → 人工批准。

只依赖用户 issue 的猜测不能直接升级成 blocker。自动 bot 回复不视为裁决依据。

## 6. 性能、安装、环境

性能方法见 PERFORMANCE_PLAN；快套件不联网、不依赖 daemon。Compose oracle 和重演另设 suite，不以 skip 偷换支持声明。

新虚拟环境安装 wheel 后测试 demo/check；包中规则、schema、最小样例必须包含，开发日志和未批准规则必须排除。

## 7. 结果和错误保全

每次执行创建独立 artifacts/<phase>/<run_id>，包含脱敏 command、exit_code、test count、duration、机器信息及变更摘要。失败证据不能被下一次成功覆盖。

至少提供一份 heldout 结果；样本数很少时直接列出每例结果，不给伪精确线上成功率。
