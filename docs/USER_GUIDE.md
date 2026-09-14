# 用户指南

本工具只读、离线分析明确提供的脱敏快照。它不会连接 Docker daemon、数据库或网络，不会执行升级、迁移或修复。当前 catalog 只覆盖 [support matrix](../catalog/support-matrix.yaml) 中的两条 exact edge；范围外版本会给出 UNSUPPORTED。

项目处于公开 beta：P07 性能验收已完成，P08 仅在 `1.16.0 → 1.16.1` 的核心服务实验范围内完成独立重演；真实维护者反馈尚未完成。NO_KNOWN_BLOCKERS 只表示本次已列明的规则没有发现已知阻碍，不是升级安全保证。

## 安装和帮助

从源码在新的虚拟环境中安装：

~~~bash
python -m venv .venv
. .venv/bin/activate
python -m pip install .
dify-preflight --help
~~~

尚未发布到 PyPI，因此不要使用未验证的包名安装命令。

## 合成演示

~~~bash
dify-preflight demo --case blocked --format json
dify-preflight demo --case resolved --format text
dify-preflight demo --case unknown --format markdown
~~~

这些输入完全是 synthetic。blocked 的退出码为 2，unknown 为 3；它们不代表真实 Dify 兼容性结论。

## 导出声明态快照

只对你明确授权的非生产副本执行。不要把 .env、原始 Compose 或生成的快照提交、粘贴到 issue，或作为诊断日志上传。

~~~bash
dify-preflight snapshot \
  --project-dir ./dify/docker \
  -f docker-compose.yaml \
  --env-file .env \
  --catalog ./catalog \
  --output ./reports/deployment.json
~~~

可重复使用 -f、--env-file 和 --profile，并按给定顺序处理。--allow-env NAME 只会读取这个明确列名的插值变量；没有该项时不会继承业务环境。输出必须是一个不存在、位于 project directory 内、且不与输入同名的路径。工具只保存批准的公开事实和布尔 private relations，不保存环境变量值或其哈希。

## 离线检查

用户计划采用的目标 Compose D 应另行采集为 --proposed-snapshot。当前声明态快照 B 与目标 D 不会互相替代。

~~~bash
dify-preflight check \
  --snapshot ./reports/deployment.json \
  --proposed-snapshot ./reports/proposed.json \
  --from 1.16.0 --to 1.16.1 \
  --catalog ./catalog \
  --format markdown
~~~

--catalog 接受 catalog/、catalog/approved/ 或 catalog/support-matrix.yaml，但必须是本地、经 approval manifest 验证的 catalog。不会联网下载规则。检查输出始终列出官方 evidence refs、事实来源、规则阶段和未检查项；不会输出 env 值、完整命令或主机路径。

本仓库包含只用于命令复现的 synthetic approved-catalog 示例：

~~~bash
dify-preflight check \
  --snapshot examples/approved_edge_a/current.json \
  --proposed-snapshot examples/approved_edge_a/proposed-blocked.json \
  --from 1.16.0 --to 1.16.1 --catalog ./catalog --format json
~~~

此命令返回 BLOCKED 和退出码 2。将 proposed-blocked.json 换为 proposed-resolved.json 会移除该阻断项；这些仍是合成的 owner-adjudicated 测试材料。

## 处理结果和退出码

| 退出码 | 结果 | 下一项行动 |
| ---: | --- | --- |
| 0 | NO_KNOWN_BLOCKERS，没有 warning | 人工确认 excluded checks 后再决定升级。 |
| 1 | NO_KNOWN_BLOCKERS，有 warning | 在报告给出的 phase 处理 warning。 |
| 2 | BLOCKED | 不要继续该升级计划，先完成 failed blocker 对应的人工步骤。 |
| 3 | INCOMPLETE | 补充报告列出的 required facts 或目标 D。 |
| 4 | UNSUPPORTED | 不把结果外推；该 edge 不在当前 support matrix。 |
| 5 | ERROR | 修正快照或 approved catalog 的受控输入错误。 |
| 64 | 参数错误 | 使用 --help 检查必需参数。 |
| 130 | 用户中断 | 本工具没有部署写操作；可重新运行。 |

running_images、database_state 和 backup_restore_validity 在 v0.1 中明确 excluded，必须人工确认。
