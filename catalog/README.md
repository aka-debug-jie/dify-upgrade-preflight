# Catalog 状态

当前有两条 owner 审批的 exact support edge 与六条 approved rule，范围以
`support-matrix.yaml` 为准，并由 `approval-manifest.yaml` 绑定。P05 仍待最终阶段验收。

candidates.yaml 不是 rule DSL，不能被 evaluator 加载。它用于 P00 选题/核验。

`approved/` 的 bundle 包含固定来源、规则、精确边、批准对象 digest 和索引；一个文件自称 approved 并不够。`candidates/` 仍用于未获批准的研究材料。

本地哈希是完整性校验，不是自动身份认证。产品需要信任安装包内的已批准 manifest，或显式配置的 owner 审核来源；未知自定义 catalog 只能给出非放行分析，不能 NO_KNOWN_BLOCKERS。
