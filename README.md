# Dify Upgrade Preflight

离线、只读、证据驱动的 Dify 升级预检工具。它将用户明确提供的 Compose 配置收缩为脱敏的声明态快照，并将其与固定官方基线和经过审核的规则相比较。

> **开发中，不能用于真实升级决策。** 当前 catalog 已有 owner 审批的两条 exact support edge 和六条规则，仅限 [support matrix](catalog/support-matrix.yaml) 明确列出的范围；P05 为 `ready_for_review`，等待 owner stage acceptance。demo 和测试输入仍为 synthetic；尚未完成独立真实升级重演或真实维护者反馈，`NO_KNOWN_BLOCKERS` 不是升级安全保证。

## 当前可运行内容

需要 Python 3.11+。在新的项目虚拟环境中安装后，可运行合成闭环：

```bash
python -m pip install .
dify-preflight --help
dify-preflight demo --case blocked --format json
```

`demo` 的 `BLOCKED` 退出码为 2；这是固定协议示例，不表示任何真实 Dify 部署存在问题。产品不连接数据库、Docker daemon 或生产目录；配置采集仅接受调用者明确指定的输入，并遵守 [SAFETY_CONTRACT.md](SAFETY_CONTRACT.md)。

## 项目边界与状态

- [PROJECT_CHARTER.md](PROJECT_CHARTER.md) 说明产品范围；[ACCEPTANCE_CONTRACT.md](ACCEPTANCE_CONTRACT.md) 定义完成门槛。
- [roadmap.yaml](roadmap.yaml) 是唯一阶段状态来源。P05 正等待 owner stage acceptance；不得将 matrix 之外的版本或 `NO_KNOWN_BLOCKERS` 解读为安全保证。
- `catalog/approved/` 和 [catalog/approval-manifest.yaml](catalog/approval-manifest.yaml) 是当前 owner 审批的本地 catalog；`catalog/candidates/` 仍包含未获批准的研究材料，不能自动提升为规则。
- [sources/SOURCES.md](sources/SOURCES.md) 仅提供公开来源定位；本地审计原件、原始 Compose、`.env`、运行产物和证据副本不会发布。

## 参与方式

请先阅读 [START_HERE.md](START_HERE.md)、[AGENTS.md](AGENTS.md) 和 [CODEX_START_PROMPT.md](CODEX_START_PROMPT.md)。贡献新的规则或支持边必须附带不可变官方来源、边界案例和人工批准记录；不得提交真实配置、凭据、日志、数据库或未脱敏的错误输出。

安全问题请遵循 [SECURITY.md](SECURITY.md)；不要通过公开 issue、PR 或讨论区发送秘密、Compose 原文或环境变量。
