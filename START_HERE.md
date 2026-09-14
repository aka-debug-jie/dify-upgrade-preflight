# Dify Upgrade Preflight｜项目启动与 Codex 执行入口

规划包版本：0.1.0 · 编制日期：2026-09-13

**本仓库同时包含开发契约、设计、测试规格和早期实现。当前 catalog 有两条 owner 审批的 exact support edge 和六条规则；P05 仍待最终阶段验收，性能实测、独立真实升级重演和真实维护者反馈尚未完成。**

## 我们要交付什么

一个面向自托管 Dify 的只读升级分析 CLI。它把用户提供的部署配置、固定版本的官方基线、经过审核的升级规则结合起来，回答：

> 从声明版本 A 到目标 B，在本次检查范围内有哪些已知阻碍、配置分歧、必须补充的证据和人工步骤？

第一版优先保证工程可行、判定准确、可测试、低运行成本；不追求全版本支持、自动升级或复杂界面。

## 最短使用流程

1. 将压缩包解压到一个**新的开发目录**。不要解压进现有生产 Dify 目录，不覆盖已有 `AGENTS.md`。
2. 在 Codex 中打开这个开发目录，把根目录 `CODEX_START_PROMPT.md` 全文作为第一条任务。
3. 先读取 `roadmap.yaml`。当前 P00–P04 已完成；P05 为 `ready_for_review`，approved catalog 已建立并等待 owner stage acceptance，不能直接开始后续阶段。
4. 你审阅后明确批准当前阶段。下一轮发送对应的 `prompts/Pxx_*.md`。每次只推进一个阶段，阶段完成后停在 `ready_for_review`。
5. 换会话使用 `prompts/RESUME.md`。存在错误、安全事件或来源冲突时使用专用提示词，不重写整个项目。

`ALL_PHASE_PROMPTS.md` 方便人类浏览，但**不要一次性全部粘贴给 Codex**。它由分阶段提示词汇总，不是另一个任务状态源。

## 开工时读哪些文件

固定入口只有：`AGENTS.md` → `PROJECT_CHARTER.md` → `SAFETY_CONTRACT.md` → `ACCEPTANCE_CONTRACT.md` → `roadmap.yaml` → 当前阶段提示词。其余文件按当前阶段点名读取，不要求每轮通读全部文档。

## 资料导航

| 目的 | 文件 |
|---|---|
| 目标、取舍、范围 | `PROJECT_CHARTER.md` |
| 不可突破的安全权限 | `SAFETY_CONTRACT.md` |
| 质量、性能和完成定义 | `ACCEPTANCE_CONTRACT.md` |
| 架构、接口、数据 | `docs/ARCHITECTURE.md`、`docs/DATA_CONTRACTS.md` |
| Compose 语义与三方差异 | `docs/COMPOSE_AND_DIFF.md` |
| 规则来源与版本生命周期 | `docs/RULES_AND_EVIDENCE.md` |
| 测试及性能执行方法 | `docs/TEST_STRATEGY.md`、`docs/PERFORMANCE_PLAN.md` |
| 全阶段实施计划 | `docs/IMPLEMENTATION_PLAN.md` |
| 唯一任务状态 | `roadmap.yaml` |
| 来源线索及未核验事项 | `sources/SOURCES.md`、`sources/registry.yaml` |
| 所有文件 | `FILE_INDEX.md` |

## 当前有意保留的边界

- 支持范围仅限 `catalog/support-matrix.yaml` 中的两条 exact edge；P05 完成验收、独立真实升级重演和真实维护者反馈均尚未完成。
- `examples/` 全部是人为构造的演示数据，不是 Dify 兼容性事实。
- 上一轮聊天中的版本数字、阈值、自动迁移推断，不自动成为产品规则。
- 第一版检查 `static_upgrade_plan`，不证明数据库备份可恢复、不证明在线服务状态、不承诺升级成功。
- `dify-preflight demo` 是可运行的 synthetic CLI；它不是真实部署检查或兼容性结论。后续产品接口仍受阶段门槛约束。
- 本地实现和测试不等于授权 commit、push、创建远程仓库、发版或上传包。外部发布单独审批。

## 你需要参与的四类决策

阶段验收；真实升级规则批准；支持范围/验收标准变更；实验环境和外部发布权限。
其余普通实现选择由 Codex 在契约内完成，不为变量命名、文件拆分等反复请求确认。
