# checkpoints/p04 — P04 第一阶段（D001 / D002）

| 文件 | 内容 |
|---|---|
| `REPORT.md` | 执行报告：绑定版本、源码改动与来源映射、终验结果、覆盖表、边界与未解决项 |
| `INDEPENDENT_REVIEW_HANDOFF.md` | 独立审核交接：审核对象、重点核对点、复现命令、关闭判断依据（执行者不执行关闭） |
| `CLEANUP.md` | 本地目录清理报告：前后大小、删除与归档映射、保留原因、完整性核对、当前入口、未处理阻塞 |
| `review-inputs/` | 本阶段需要的最小审核材料（REVIEW.md、ACCEPTANCE_CORRECTION.md、PRODUCTION_ADOPTION_PLAN.md、NEXT_CLAUDE_PROMPT.md、LANDING_MANIFEST.json、RECONCILIATION_137.json、两份 P03 小补丁）及 `SHA256SUMS.txt` |
| `evidence/` | 终验最小证据：D001 摘要与冻结 12 例原始记录；D002 判定 JSON、构建记录与阳性对照；错误码 20 摘要；s4test/Lua/Python 日志；`STEPS.txt`、`ARTIFACTS.sha256`；产品差异补丁；清理前快照 |

终验绑定：源码修复 `44f4a097…`，终验 tip `8b13d67b…`（见 REPORT.md 第 1 节）。

状态口径：implemented（已实现）／targeted complete（定向验证完成）／pending independent production acceptance（待独立生产验收）。本目录不含任何生产关闭结论。
