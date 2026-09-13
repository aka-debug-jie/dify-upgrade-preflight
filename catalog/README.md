# Catalog 初始状态

当前只有候选线索和空支持矩阵，没有 production rule，没有已批准支持边。

candidates.yaml 不是 rule DSL，不能被 evaluator 加载。它用于 P00 选题/核验。

P04/P05 将建立 candidates/ 与 approved/。approved 的 bundle 必须包含固定来源、规则、精确边、批准对象 digest 和索引；一个文件自称 approved 并不够。

本地哈希是完整性校验，不是自动身份认证。产品需要信任安装包内的已批准 manifest，或显式配置的 owner 审核来源；未知自定义 catalog 只能给出非放行分析，不能 NO_KNOWN_BLOCKERS。
