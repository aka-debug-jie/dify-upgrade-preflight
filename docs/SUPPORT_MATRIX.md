# 支持矩阵与范围声明

机器真相：`catalog/support-matrix.yaml`。当前 `approved_edges: []`；所有候选仅供 P00 核验。

每条批准边必须精确指定：source release、target release、source/target commit、deployment profile、Compose 解析器版本、scope、所需 facts、规则集合、测试案例、审批。

首版 scope 为 static_upgrade_plan。它评估已提供的配置与升级计划，而非活体生产实例。

| 信息 | v0.1 的处理 |
|---|---|
| 配置声明的镜像版本 | 可采集；标 declared |
| 实际运行镜像 | 未观察；列入 excluded_checks |
| PostgreSQL/Redis 是否在线 | 不探测 |
| 数据库迁移实际状态 | 需要外部可信事实时 unknown，不猜 |
| 备份是否可恢复 | 不检查，列入人工前置清单 |
| 内置/外部向量库归属 | 只有配置/用户证据充分时判定 |
| 本地文件差异 | 只读分析 |
| 目标部署配置 | 未提供时只预测官方变化；不能声称已验证最终合并 |

UNKNOWN 与范围外不同：规则在本范围内必需但事实缺失 → INCOMPLETE；明确不在本范围的在线检查 → 列未检查项，不阻止一个有用的静态报告。

v0.1 不能隐式支持任意相邻版本、downgrade、nightly、自定义构建或任意 Compose 扩展。首版 exact-edge 优先于自动寻路。
