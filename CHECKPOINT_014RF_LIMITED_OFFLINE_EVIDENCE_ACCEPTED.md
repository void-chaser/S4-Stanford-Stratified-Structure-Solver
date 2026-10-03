# CHECKPOINT 014RF — LIMITED_OFFLINE_EVIDENCE_CHAIN_ACCEPTED

日期：2026-10-03（Australia/Sydney）。

Git parent HEAD：`64561e92f36d8b4fa39238d431426b24c7049c75`。开始分支：`feature/python314-binding`；checkpoint 分支：`checkpoint/014rf-offline-evidence-accepted-20261003`。

最新独立结论：**LIMITED_OFFLINE_EVIDENCE_CHAIN_ACCEPTED**。验收范围仅为 limited offline evidence reconstruction/signoff chain。D001/D002 production closure、native S4、scalea、I3/I4、legacy scientific certification 均未因此验收或升级。本提交是源码与证据摘要的阶段快照，不授权 native/solver 运行，不开始下一 defect，不表示 main 可合并。

最新审核摘要：[FINAL_REVIEW.md](checkpoints/014rf/FINAL_REVIEW.md)；机器结论：[VERDICT.json](checkpoints/014rf/VERDICT.json)；完整定位哈希、关键审核文件 SHA256、审核根文件清单摘要及候选 14 文件哈希：[PROVENANCE.json](checkpoints/014rf/PROVENANCE.json)。它们来自 `audit-workspace/codex-review/014R-F/CONTROL_REVIEW_EVIDENCE_FINAL_014RF/independent-20261003T101954Z-62a3318f`，而非较早的 CANDIDATE_SIGNOFF_BOUNDARY_QUALIFIED。原指定 CONTROL_REVIEW_SIGNOFF_BOUNDARY_014RF 是历史复核入口。

## 源码保留范围

19 个 tracked 修改与历史交接附录的有意集成清单一致；其中 15 个同时匹配最新审核保护映射。保留原字节，包括既有 CRLF/尾随空白；本轮不修复、不构建、不重新验证其科学正确性。纳入 38 个配套测试源码/说明/参考输入，三份小型固定回归文本基线，以及两份明确带日期的历史交接文档。历史交接的旧计划或旧 HEAD 不覆盖本文边界。

当前 tracked 修改清单：

- `Makefile.common`
- `S4/Interpolator.c`
- `S4/RNP/Eigensystems.cpp`
- `S4/S4.cpp`
- `S4/S4.h`
- `S4/fmm/fft_iface.cpp`
- `S4/fmm/fft_iface.h`
- `S4/kiss_fft/kiss_fft.c`
- `S4/kiss_fft/kiss_fft.h`
- `S4/kiss_fft/tools/kiss_fftnd.c`
- `S4/kiss_fft/tools/kiss_fftnd.h`
- `S4/main_lua.c`
- `S4/main_python.c`
- `S4/numalloc.c`
- `S4/rcwa.cpp`
- `S4/rcwa.h`
- `testing/numdiff`
- `testing/runtests.sh`
- `testing/testcases.txt`

## 冻结锚点与本地证据

- `audit-workspace/014R-F/TASK_BUDGET_REGISTRY_014RF.jsonl`：`a03d614f5f1e0c954136f4d6058ba0675e51dba23fbc7fa21fd3550d7b3d53f7`
- `audit-workspace/codex-review/013/Task013控制审核/controlled_inputs_v1/I2.json`：`59c6363999b5cde9bac57bd717fd189367b662c47f481dd748a2f70a91c679a5`

完整 audit-workspace（含大量 fixture、store、日志和历史 mutation 副本）不整体进入 Git。所有旧证据根保持本地只读；完整 Git 路径清单和本次操作日志位于 `audit-workspace/codex-review/014R-F/CHECKPOINT_014RF_LIMITED_OFFLINE_EVIDENCE_ACCEPTED/checkpoint-20261003T104650Z-534c1e3f`。远端可恢复的是提交内源码、配套测试及接受摘要/定位哈希，不是完整历史 audit 的远端重放环境。

下一阶段应从本 checkpoint 继续，沿用 014RF 已接受的有限边界；不要重新解释 014RF，也不要自动开始 D001/D002 或 native 验证。普通 push 后只在新隔离 checkout 做 Git 干净性和字节恢复检查，完成后停止。
