# Compose 采集与三方配置差异

## 1. 不重新发明 Compose

Docker 官方的 `config` 负责归一化，插值和多文件合并有明确语义，不能用 PyYAML 加 dict.update 代替。资料入口为 S02/S03/S04。

P02 先做 capability probe：记录 Compose 版本，验证需要的 config JSON 输出选项；不假设所有用户 CLI 有相同功能。缺失时给可执行的安装/导出说明，核心 check(snapshot) 仍可运行。

## 2. 两条边界清楚的输入路径

**离线 check**：只吃本工具 schema 的脱敏 snapshot 与本地 catalog，无任何外部命令。

**显式 snapshot**：接受 project-dir、按序 -f、显式 env-file/profiles，预审后调用已验证 Compose `config --format json`。输出经过字段白名单收缩；原始标准输出只存在于内存。

不提供“解析失败就用简易 YAML 当真”的静默后备。可以导出部分诊断，但必须 marked incomplete，不能形成完整快照。

## 3. 插值上下文

区分：shell interpolation 环境、项目 .env、CLI --env-file、service.env_file、service.environment。这几种来源不能简单混合。

默认不继承调用者完整 shell 环境。用户要复现部署时的 shell 覆盖，须逐个允许变量名；值不放在 argv 和日志中。检查结束明确说明采用的插值上下文不是对原始部署命令的自动回溯。

缺失变量与空字符串不同，`${X-default}` 与 `${X:-default}` 也必须由原生解析器正确处理。未设置、空、默认、显式覆盖分别有测试。

## 4. 安全预审

列举本次被读取的配置/env 路径；限制在项目根目录或用户显式批准的文件集合；路径必须 canonicalize 并检查 symlink。拒绝设备/FIFO/循环引用、远程引用、越界 env_file 和不受支持的 include/extends。

v0.1 对 include/extends 采取不支持策略；遇到时停止采集并说明，并非宣称 Docker 不支持。
对原生 YAML anchor、合法 merge key 进行限额支持；Docker 特殊 merge tag 只有在已验证 CLI/fixture 中才纳入矩阵。

不遍历 `volumes/`、模型文件和业务数据库目录。Sandbox 单个配置文件若被某条审核规则明确需要，必须有单独允许路径与只读测试，否则规则相关状态 unknown。

## 5. 三方差异定义

A=source release 的官方配置，B=用户当前配置，C=target release 的官方配置，D=可选的用户目标计划。

| A/B/C 比较 | 结论 |
|---|---|
| A=B=C | unchanged |
| A=B 且 C 不同 | upstream_only |
| A=C 且 B 不同 | local_only |
| B=C 且 A 不同 | same_change |
| 三者互异 | divergent_change，需要人工合并 |
| 缺少基线、字段不可比较或证据不足 | unknown_comparison |

字段缺失使用独立 MISSING 哨兵，不与空、null、false、0 等混同。

排序无关字段才能排序；列表顺序有语义的 command/entrypoint 不做集合化。ports、volumes、secrets、configs 等具有专门唯一键，先采用 Compose 归一化后按经验证的字段键处理。未知类型不瞎归一。

## 6. 配置变化不是事实冲突

本地设置和官方默认不同通常是正常定制。三方分歧本身最多 warning/manual review。
只有明确的规则能建立失败，例如用户给出的目标 D 仍引用一个在 D 中不存在的必需服务，且该关系在已支持部署模式下确实不允许。

镜像改名、环境变量新键、服务名变化不自动映射为重命名；需官方证据。DB_HOST 的自定义值可能指外部数据库，不能机械替换为官方 service 名。

## 7. 基线与字段安全

catalog 包含固定源码 commit 下、使用固定解析器生成的**公开基线视图**。在相同且显式记录的非秘密插值环境中比较 A/C。

B 只输出允许公开的字段。服务存在、镜像 tag、受限拓扑布尔值和非秘密 cache 开关可进入白名单；整个网络图、环境映射和 token 不能进入。秘密默认匹配或双变量一致性只能由采集器用固定审核过的检测定义在内存计算为布尔值，但不保存秘密；未实现的关系不能靠两个 REDACTED 视图比较。

三方 diff 不执行合并，也不写生成的 `.env` 或 Compose。所有修改建议均是描述，不是可直接执行的生产脚本。
