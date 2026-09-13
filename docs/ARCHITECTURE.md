# 架构设计：小而可验证的本地工具

## 1. 取舍

考虑过三条路线：直接扫描并连接在线服务；先做脱敏快照和纯规则分析；先造通用多平台升级框架。
选择第二条。它先把风险最高的 I/O 与可重复的判断分开，能用合成输入快速验收；在线探测和平台泛化均后置。

技术基线：Python；标准库 argparse/json/logging/pathlib/subprocess/hashlib；Pydantic、PyYAML、packaging 为候选运行依赖，P00 审核后固定。第一版不依赖 Rich、Typer、Docker SDK、ORM、网络服务或模型 API。终端报告先用可读纯文本。

## 2. 数据流

```text
开发侧：固定官方源码/说明 → 人工审核 → catalog/approved（不含可执行代码）
                                      │
用户显式指定的配置 → 受限采集 → 脱敏快照 ─┼→ 纯 evaluator → Report
                                      │                    ├→ terminal
                           source/target + support edge    ├→ JSON
                                                           └→ Markdown
```

网络获取资料是**开发侧维护流程**，不是用户 `check` 的一部分。产品不因为目标版本未知而自行联网。

## 3. 模块与接口

| 模块 | 职责 | 不能做 |
|---|---|---|
| `domain.py` | 类型模型、枚举、结果契约 | I/O、默认补未知为已知 |
| `collect/safe_io.py` | 允许路径、文件限额、只读打开 | 任意递归、读取生产业务卷 |
| `collect/compose.py` | 调用固定 Compose config、归一化 | 自行完整实现 Compose、启动容器 |
| `collect/redaction.py` | 允许字段导出、敏感关系布尔化 | 保存原始值用于 debug |
| `catalog/load.py` | 验证本地 catalog、schema、哈希和批准状态 | 下载、执行规则代码 |
| `diff/three_way.py` | 可比较字段的 A/B/C/D 差异 | 把所有差异定义为错误 |
| `engine/expressions.py` | 三值表达式 | eval、插件解释器 |
| `engine/evaluate.py` | 适用性、规则结果 | 网络、文件读写、Docker |
| `engine/verdict.py` | 支持/覆盖/风险的聚合 | 隐藏未知、提前短路漏报 |
| `report/*` | 三种格式和稳定摘要 | 泄露输入或宣称安全 |
| `cli.py` | 参数、错误映射、编排 | 内嵌大量业务规则 |

## 4. 冻结的核心函数签名（目标接口）

```python
collect_snapshot(request: CaptureRequest) -> DeploymentSnapshot
load_catalog(path: Path, policy: CatalogPolicy) -> Catalog
compare_three_way(base: PublicConfig, local: PublicConfig,
                  target: PublicConfig,
                  proposed: PublicConfig | None = None) -> list[ConfigChange]
build_fact_view(snapshot: DeploymentSnapshot) -> Mapping[str, Fact]
evaluate_expression(expr: Expression, facts: Mapping[str, Fact]) -> TruthValue
evaluate(snapshot: DeploymentSnapshot, request: UpgradeRequest,
         catalog: Catalog) -> Report
render_report(report: Report, format: ReportFormat) -> str
```

P01 先定义类型和纯 evaluator 的小闭环。P02 再实现 I/O。不得先把所有模块建成空壳并声称架构完成。

`PublicConfig` 是扁平的公开可比较字段映射；只有字段注册表批准的键和值类型能进入快照。
`Fact` 必须带来源类别，`Expression` 采用受限 AST，不是字符串代码。

## 5. 目录（未来实现目标，不代表当前已存在）

```text
src/dify_preflight/
  __init__.py, __main__.py, cli.py, domain.py
  collect/{safe_io,compose,redaction}.py
  catalog/{load,validate}.py
  diff/three_way.py
  engine/{expressions,evaluate,verdict}.py
  report/{json,text,markdown}.py
scripts/{validate_catalog,validate_governance,benchmark,build_catalog}.py
tests/{unit,contract,integration,security,performance}/
tests/fixtures/{synthetic,adjudicated,heldout}/
```

生产规则放 `catalog/approved/`，未批准规则放 `catalog/candidates/`，实验材料放忽略的 `artifacts/`。启动包的 `specs/` 是输入规格，不当成已实现测试。

## 6. 类型与复杂度

对可比较字段建索引，差异比较预期 O(K)；规则求值预期 O(R×C)，C 为规则条件数。禁止对每条规则重复加载配置、重复调用 Compose 或重新扫描全部文件。

核心 evaluator 是同步纯函数；先不引入 asyncio、任务队列、数据库和持久化缓存。P10 需要探测时再单独设计有界并发。

## 7. 版本路径不是普通最短路径

一个经过验证的 A→B 和 B→C，不自动证明 A→C。首版只允许批准的精确边；间接路径可以显示为“需分别检查的候选序列”，不得给总放行判定。

同一版本相关的多组件步骤有前置关系，不按 release 编号拼接 shell 命令。首版 remediation 是带 phase 和证据的人工检查清单，不是升级脚本。

## 8. 避免过度工程

不为未来十个平台做插件系统；不做完整规则语言；不做网络缓存服务；不为潜在百万规则优化。
新增抽象需至少两个已通过的真实场景支持。能用一个纯函数表达时，不引入管理器工厂或多层继承。
