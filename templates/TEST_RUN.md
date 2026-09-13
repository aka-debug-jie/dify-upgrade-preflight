# 测试/性能记录格式

保存内容：run_id、phase、实际命令参数（不含秘密）、开始/结束、exit_code、环境、tool/catalog/input 的安全摘要、suite、通过/失败/跳过数、跳过原因、原始性能样本、p50/p95/max、RSS 单位和换算、warnings、artifact paths。

记录真实测试数量，不能把 dry-run、计划输出、模型自述计为执行。失败日志必须脱敏且保留。没有环境时写 not_run 与原因，不编造输出。
