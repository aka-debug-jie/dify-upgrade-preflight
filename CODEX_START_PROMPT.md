你现在是 Dify Upgrade Preflight 的主要实现者。我负责产品范围、真实升级规则、风险判断与发布审批。

这次先只执行 P00，不开始业务代码实现。

请先完整读取：
1. AGENTS.md
2. PROJECT_CHARTER.md
3. SAFETY_CONTRACT.md
4. ACCEPTANCE_CONTRACT.md
5. roadmap.yaml
6. prompts/P00_discovery.md
再按 P00 引用读取来源、环境和支持矩阵文件。

优先级：不改生产/不泄密/不虚假放行 > 工程可行 > 实测性能 > 扩大覆盖 > 界面。

不要把先前聊天中的版本号、Weaviate路径、迁移是否自动执行等示例直接写入规则。先取得固定官方来源、源码commit、内容hash和可验证反例。本包 sources 只是线索，当前批准支持矩阵为空。

本轮要求：
- 核查当前开发目录、已有用户改动、可用Python/Compose和独立测试条件；不接触生产，不改全局环境。
- 验证至少两类超过普通env diff的真实可检测问题，提出最多两条首版source→target精确支持边。
- 记录来源冲突、不可获取资料、不可观察状态；没有证据写blocked_external，不造hash或测试结果。
- 给出最小依赖方案、候选根因、测试画像和P01可行性结论。
- 将真实输出写入P00独立artifact目录，更新roadmap的状态/证据字段。

本轮禁止：业务src代码、生产规则批准、自动升级、数据库连接、Docker生命周期命令、读取真实.env、commit/push/tag/发布，以及修改验收标准和契约锁。

完成后停在ready_for_review，向我报告：已验证事实、未验证事项、建议支持边、依赖与环境缺口、GO/NO-GO理由、P01的最小下一步。不要继续P01，也不要声称整个项目已搭建完成。
