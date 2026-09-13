# 真实规则审核卡

复制到当前阶段 artifact；每条规则一张。

1. 规则 ID、revision、内容 SHA-256、具体 source→target 与画像。
2. 官方来源 URL、固定 commit/内容 digest、section/path、实际查阅时间。
3. 作者自己的事实摘要；哪些是来源明确说的，哪些是推断。
4. applies 所需事实及可信来源；缺失时行为。
5. assertion、severity、before/during/after/manual_review 的理由。
6. 不适用画像、external/bundled、新部署、已经完成迁移、版本边界。
7. 正例、反例、未知例、替代旧规则例的 test ID 与真实执行结果。
8. 重演或源码印证的证据；无法确认的部分。
9. 审查意见、冲突、修复后的 diff。
10. owner 最终批准/拒绝/要求修改的真实记录及内容 digest。

缺任何必需项时保持 candidate。不要把模板中的条目改成已完成标记。
