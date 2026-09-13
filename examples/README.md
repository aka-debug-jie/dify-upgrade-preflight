# 合成演示

所有版本、前置条件和来源都是人为定义的协议测试，不对应真实 Dify 升级。

synthetic_snapshot.json：已知失败前置条件；synthetic_rule.yaml：如何表达 applies/assertion；synthetic_report.json：预期 BLOCKED 的输出形状。

可以把 demo.condition_resolved 改成 true 测 passed，改 unknown+null 测 INCOMPLETE，把 vector.ownership 改 external 测不适用。必须保留 synthetic=true。

示例哈希由本包真实 JSON 内容计算，但只说明示例自身的一致性，不是官方来源 hash 或人工批准。
