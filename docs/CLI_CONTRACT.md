# CLI 契约

`dify-preflight` 已实现为本地、离线、只读 CLI。它只读取调用者指定的输入和本地 owner-approved catalog；不会连接 Docker daemon、数据库或网络。当前是 beta，`NO_KNOWN_BLOCKERS` 不能作为升级安全保证。

## 1. 命令面

```bash
dify-preflight --help
dify-preflight demo --case blocked --format text
dify-preflight snapshot --project-dir ./dify/docker \
  -f docker-compose.yaml --env-file .env --catalog ./catalog \
  --output ./reports/deployment.json
dify-preflight check --snapshot ./reports/deployment.json \
  --from 1.16.0 --to 1.16.1 --catalog ./catalog --format json
dify-preflight check --snapshot ./reports/deployment.json \
  --from 1.16.0 --to 1.16.1 --catalog ./catalog \
  --proposed-snapshot ./reports/proposed.json --format markdown
```

示例版本对应当前 matrix 中的一条 approved exact edge。当前仅支持 `catalog/support-matrix.yaml` 中的两条 exact edge；范围外版本返回 `UNSUPPORTED`。路径必须由用户调整为实际存在且明确授权的目录。

`snapshot` 明确授权读取提供的路径并调用受限解析器；`check` 绝不访问 Docker、数据库和网络。
`demo` 只使用包内合成数据，始终标记 synthetic=true、DEMO，不得拿来证明真实兼容性。

## 2. 参数规范

必需 --from/--to，不隐式使用 latest；--catalog 必须明确目录或包内已批准目录，不能联网回退。
-f 顺序保留；--env-file 可多次指定且顺序保留；--profile 可多次指定。
--allow-env NAME 只允许该插值变量从进程环境传入，报告名字而不报告值；默认不继承其余业务环境变量。

--output 指定脱敏文件，不覆盖现存文件，不允许等于任何输入，不允许写入生产配置路径。无 --output 的 check 输出 stdout。
首版不提供 --fix、--upgrade、--force-safe、--ignore-blocker、--skip-required。

## 3. 输出协议

format=json 时 stdout 恰好一个合法 JSON 文档，不混进颜色、进度和日志。stderr 只输出脱敏诊断。终端格式不用颜色也完整可读，遵守 NO_COLOR。

日志、snapshot、Markdown、异常都复用同一脱敏边界。默认隐藏 traceback；debug 也不得泄露原始输入。

NO_KNOWN_BLOCKERS 的固定解释为：
“在本次列明的检查范围和规则版本内，未发现已知阻碍。未检查项仍需人工确认。”

## 4. 退出码

| code | 意义 |
|---:|---|
| 0 | NO_KNOWN_BLOCKERS 且没有 warning；或成功执行 help/snapshot |
| 1 | NO_KNOWN_BLOCKERS，但存在非阻断 warning |
| 2 | BLOCKED |
| 3 | INCOMPLETE |
| 4 | UNSUPPORTED |
| 5 | ERROR：解析/目录验证/受限采集/内部操作失败 |
| 64 | 参数错误；必须覆盖 argparse 的默认 exit=2 |
| 130 | 用户中断 |

同一规则结论在 text/json/markdown 下退出码一致。demo 使用相同业务退出码，但显式标记合成。

## 5. 不越界的错误提示

缺少 catalog：报告目录无批准数据及下一步，不自动下载。
未知版本：UNSUPPORTED，不按照版本大小推定兼容。
raw Compose 无解析器：ERROR 并提示需要经验证 Compose；已导出的合法 snapshot 仍可离线分析。
秘密相关错误：只给字段名和错误类别，不回显内容。

## 6. README 首屏示例要求

用一条真实、已裁决的故障画像及其反例演示：内置组件命中风险；外部组件不适用；关键信息缺失变为 INCOMPLETE。
展示来源定位、未检查项和机器输出，不能写“保证安全升级”。
