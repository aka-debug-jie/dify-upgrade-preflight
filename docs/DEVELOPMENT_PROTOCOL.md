# Codex 开发与人工审批协议

## 1. 权限区分

项目任务、工具权限和公开发布是三种独立授权。发给 Codex 一个阶段提示词，只授权该阶段内的本地工作。

“Codex Sol”在本包中仅表示你使用的编码执行器，不假设固定的 API model ID、上下文大小、自动联网或多代理能力。

使用仓库级 AGENTS.md，保持简短；不自动修改 ~/.codex 的全局配置或 approval/sandbox 设置。官方说明入口 S08/S09。

## 2. 单一进度源

roadmap.yaml 定义 phase/tasks/dependencies/status/artifacts/approval_ref。初始 P00 ready，其余 blocked 或 deferred。

合法状态：ready / in_progress / ready_for_review / done / blocked_external / blocked_review / deferred。

`ready_for_review` 不是 `done`。执行者可填真实测试证据，不能给自己造 approval。owner 明确批准后，Codex 可以记录该消息的引用和批准对象 digest，并据此完成状态迁移。

模板、汇总提示词和聊天总结不能覆盖 roadmap。修改阶段依赖或验收项需要 change request。

## 3. 固定循环

1. 读当前任务及依赖，检查已有文件和 Git 状态；不覆盖用户改动。
2. 记录本轮范围、允许写入路径、预期验收，设 in_progress。
3. 建立 baseline；新增或补足 failing test。
4. 实现最小切片；跑与风险相称的测试；失败则定位根因，不改预期掩盖。
5. 写 artifacts 与 handoff，更新 roadmap 的允许字段。
6. 所有本阶段门禁满足后设 ready_for_review，停止并请求阶段评审；不要自动跳到下一阶段。

没有必要为普通命名和局部实现反复问用户。只有权限/事实/契约无法解决时才停住受影响项。可完成的同阶段工作继续，不伪造外部验证。

## 4. 任务大小与代码管理

一次只做可独立评审的切片；避免把 parser、规则、发布混在一个未检查的大 patch。
新目录中也不自动 git init/commit，除非当前用户明确授权。已有仓库先记录 status；禁止 reset/clean。需要分工时使用用户认可的隔离目录/worktree，不能两个执行者同时写同一接口文件。

## 5. 三种角色

Evidence：只提候选事实和来源，不批准自己。
Implementer：按固定规格实现和测试。
Reviewer：先读规格与证据，主动找反例，再看实现。

单个 Codex 会话可顺序扮演角色，但不得声称独立模型审查；多代理结论也不能通过投票替代证据。关键规则仍由你审核。

## 6. 契约锁

`governance/acceptance-lock.json` 固定契约、schema、阶段提示词与 roadmap 的不可变字段摘要。状态/证据可以变；验收和依赖不能自己变。

未经批准修改受保护内容时，记录差异并停在 blocked_review。SHA 校验只验证一致性，不是身份认证；人工批准仍以真实消息及精确对象为依据。

## 7. 错误类别

blocked_external：网络/依赖/独立实验环境/真实样本缺失。
blocked_review：规则争议、范围变化、发布权限或契约冲突。

两者都必须写明已完成内容、缺口、证明方式和下一步；不得因一个缺口扩展另一个平台来“继续推进”。
