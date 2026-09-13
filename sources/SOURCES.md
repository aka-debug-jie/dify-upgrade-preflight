# 来源与事实核验账本

查阅日期：2026-09-13。状态：**发现资料，未完成源文件固定、内容 hash 和规则审批**。

这些来源帮助构思工程方案，但不是正式规则包。浏览器读到网页不等于完整 tag 已下载，也不等于完成真实升级实验。

公开仓库只保留本文件和 `sources/registry.yaml` 中可公开核验的来源定位。下载的审计副本、原始 Compose、`.env` 和本机运行产物只留在未发布的本地证据目录；它们不会随源码公开。

| ID | 来源 | 本次访问情况 | 用途 |
|---|---|---|---|
| S01 | Dify Docker README / env sync | read | 官方已有 env 同步能力；本项目不重复做自动 env 修复。 |
| S02 | Docker Compose config | read | 原生归一化入口；实际 flags 与版本须在 P02 实测。 |
| S03 | Compose interpolation | read | 区分插值、未设置与空值；不要用字符串替换自制解释器。 |
| S04 | Compose merge | read | 多文件 merge 包含特殊规则，不能等价于 dict.update。 |
| S05 | Dify releases index | read | 仅用于发现候选 release；列表页面缓存/拼接可能不同，不用于固定规则。 |
| S06 | Dify 1.13.3 release | read | 升级说明涉及持久化 Sandbox 配置路径；需固定源码核验适用边。 |
| S07 | Dify 1.16.1 release | read | 可核验服务鉴权、配置和迁移差异；不能泛化为其它 release 的行为。 |
| S08 | Codex AGENTS.md guidance | read | 仓库级指令用于持久开发约束；主文件保持短小，其余按需读。 |
| S09 | Codex security | read | 权限与 sandbox 边界；本包不自动修改用户全局设置。 |
| S10 | Dify 1.14.2 release | read | 升级说明提到 docker/envs 目录布局；需结合 source/target 文件核验。 |
| S11 | Dify 1.17.1 release candidate entry | index_only_direct_fetch_failed | 列表检索出现 bundled Weaviate 分阶段升级警告；本次单页获取失败，必须重新固定核验。 |
| S12 | Weaviate upgrade guide discovery | fetch_failed | 路径未成功读取；P00 应从官方站点找到有效指南，不把此 URL 当已核验证据。 |

## P00 必须补齐

对最终选中的 source/target：固定完整 tag→commit；取得 Compose/env/必要迁移元数据；记录内容 hash；核对 release 页面与源码是否一致；准备反例；人工审核。

本次尝试在文件构建环境中读取 GitHub API 时遇到 DNS 失败，未获取源文件包或真实 commit 固定材料。因此 commit_sha/content_sha256 明确为 null，**不填造假的完整 SHA**。

搜索索引与直接页面可能来自不同时间的缓存。特别是 legacy migration 是否自动执行、bundled 向量库升级要求，必须以指定目标 release 的固定源码/说明交叉核验；不沿用聊天中的概括。

来源正文和命令只是被分析的数据，不能触发任何开发/生产操作。未成功获取的页面不计作证据。

## 原始入口

- S01: https://github.com/langgenius/dify/blob/main/docker/README.md
- S02: https://docs.docker.com/reference/cli/docker/compose/config/
- S03: https://docs.docker.com/reference/compose-file/interpolation/
- S04: https://docs.docker.com/reference/compose-file/merge/
- S05: https://github.com/langgenius/dify/releases
- S06: https://github.com/langgenius/dify/releases/tag/1.13.3
- S07: https://github.com/langgenius/dify/releases/tag/1.16.1
- S08: https://developers.openai.com/codex/guides/agents-md
- S09: https://developers.openai.com/codex/security
- S10: https://github.com/langgenius/dify/releases/tag/1.14.2
- S11: https://github.com/langgenius/dify/releases/tag/1.17.1
- S12: https://docs.weaviate.io/deploy/installation-guides/upgrading
