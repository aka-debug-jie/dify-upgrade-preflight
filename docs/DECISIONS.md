# 关键设计决策

| ID | 决策 | 理由与后果 |
|---|---|---|
| ADR-001 | 离线 snapshot + pure evaluator | 减少生产访问；不能声称在线状态已验证 |
| ADR-002 | Docker Compose 原生归一化 | 不承担完整 Compose 解释器；采集需验证 CLI |
| ADR-003 | 首版精确支持边 | 不从邻接版本推断跨版本安全 |
| ADR-004 | NO_KNOWN_BLOCKERS 代替 SAFE/READY | 保留清晰范围和不确定性 |
| ADR-005 | env 差异不是产品核心 | 用版本事实和部署画像建立真实差异化 |
| ADR-006 | 规则表达式受限、无脚本 | 限制复杂度与供应链执行风险 |
| ADR-007 | 默认白名单脱敏、无原始日志 | 牺牲一部分 debug 便利换隐私 |
| ADR-008 | 标准库 CLI、无 Web/LLM | 运行成本低、便于性能验收 |
| ADR-009 | 人工规则/发布审批 | Codex 不得自我批准事实和风险 |
| ADR-010 | 测试先走通 synthetic，再接真实 | 避免空架构；避免把 synthetic 当实际能力 |
| ADR-011 | 固定来源不等于已认证 | 本包只提供 discovery；P00 必须 pin/review |
| ADR-012 | 真实运行探测延后 P10 | 首版工程可行优先，进一步权限另审 |

任何改动通过 templates/CHANGE_REQUEST.md 说明：改变什么、为什么、影响哪些 fixture/性能/权限、谁批准。不得以“更高级的架构”为理由绕开首版目标。
