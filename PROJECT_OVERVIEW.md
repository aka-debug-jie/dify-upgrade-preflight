# 项目总览与关键选择

## 目标

做“固定官方升级证据 × 实际提供的配置 × 明确source/target”的个性化预检，不做自动升级器。

## 首版只有四个核心

脱敏快照；三方配置差异；审核规则和精确支持边；可追溯报告。

## 先不做

数据库连接、Docker运行探测、自动修复、升级/回滚、Kubernetes、Web、LLM、多平台通用框架。

## 质量优先顺序

安全和正确性 → 小闭环可用 → 性能可测 → 扩大覆盖 → 界面。

中型离线分析目标 p95≤2秒、RSS≤200MiB；压力负载 p95≤8秒。均为待测目标，不是完成声明。检测准确性另以真实根因/反例/未知测试验收。

## 人机分工

Codex实现和测试，整理证据；你批准规则/范围/风险和发布。roadmap为唯一状态源；每阶段ready_for_review后停住。

## 下一步怎么做

当前实现已完成 P00–P04；P05 已建立 owner 审批的两条 exact edge 和六条 catalog rule，并为 `ready_for_review`，等待 owner stage acceptance。继续前先读取 `roadmap.yaml` 和 `prompts/RESUME.md`，只在取得新的阶段授权后推进；不能将 candidate 材料或范围外版本当作已批准能力。

## 当前状态

已有 synthetic CLI、受限 Compose 采集、三方差异和 digest-bound approved catalog。性能实测、独立真实升级重演和真实维护者反馈仍未完成，因此不能声称 production-grade 或升级安全保证。详细方案在docs/IMPLEMENTATION_PLAN.md，所有阶段提示词在prompts/。
