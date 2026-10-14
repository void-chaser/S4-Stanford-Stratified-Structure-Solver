# P05-S4 R8 M1a 续3a 暂停交接（未收尾）

> 本轮是 P05-S4 R8 M1a 续3a 的子轮次，不是新阶段；不宣布任何阶段完成或签收；不写签收建议。
> **状态：用户主动暂停（额度不足）。这不是技术停止。尚未执行正式收尾门禁（end），也未执行记录提交。**
> 任务书：`checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3a.md`（已按 §0 原文存档）。

## 1. 暂停时的基线（2026-10-14T05:39:26Z，只读）

| 项 | 值 |
|---|---|
| 分支 | `codex/p05-d003-fft-error-propagation` |
| HEAD | `331c022c3d9944cff8e7e63e16c24d33253ce847`（与任务书基线一致） |
| `HEAD:S4` | `6cff923a02baf19e01966b2339755cbf3a5deeef`（F3，一致） |
| 判定器 sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`（一致） |
| 后台作业 | 无（`job_list` 为空） |
| 工作区 | 见 §5（本轮未跟踪/已修改文件，未提交） |

未修改 `S4/`；未修改任何已提交的 `testing/d003` 文件（`git diff --name-only HEAD -- testing/d003` 为空，start 门禁已核对）。

## 2. 已完成步骤与门禁结果

| 步骤 | 结果 | 证据 |
|---|---|---|
| §0 开工核对（HEAD、HEAD:S4、判定器、status） | 通过 | 本节 §1 |
| §0 任务书原文存档 | 完成 | `checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3a.md` |
| 开工 /tmp 快照（TC=0，TS=e3b0c442…b855） | 完成 | 门禁参数 |
| 新增 `gate9_r8m1a4.sh`、`recheck_s4r7_r8m1a4.py` | 完成；预运行 grep 0 命中，已 `prerun_log` 记录 | `PRERUN_CHECKS_R8_M1a.txt` |
| **start 门禁** `GATE_R8_M1a4_START.txt` | **FAILS=0**（34 行，全部 PASS） | `checkpoints/p05/evidence/p05-s4r8/GATE_R8_M1a4_START.txt` |
| **U176–U182 裁决追加**（start 门禁通过后） | **FAILS=0**，RULINGS 7 行新增（NF=5，前 66509 字节前缀不变） | `APPEND_R8_M1a4.txt`；`registries/RULINGS.tsv` 已追加 |
| **E8-56 至 E8-60 勘误追加** | **FAILS=0**，ERRATA_8 前 37669 字节前缀不变 | `APPEND_R8_M1a4.txt`；`registries/s4r8/ERRATA_8.txt` 已追加 |
| U177 有效分类表 `USED_IN_M1_CORRECTION_R8_M1a4.tsv` | 完成（BP_LINE 4→2；NO 1→3；REGISTRY_ONLY 26 不变；映射本身未重跑） | `evidence/p05-s4r8/USED_IN_M1_CORRECTION_R8_M1a4.tsv` |
| `counted_families_r8m1a4.py` 干跑与 `_R2` 输出 | 完成：13 源表、12 计数族、1128 覆盖行（1046 MAPPED、82 N/A）、24 单元 | 见 §3 |
| 期望 `EXPECT_CALLSEQ_R8_M1a4_R2.txt` | 已写入并记录（见 §4）；**尚未运行任何 gdb/驱动** | 见 §4 |

## 3. 已产生的文件

**已提交前的工作区改动（未提交，供恢复）：**

- 修改：`checkpoints/p05/registries/RULINGS.tsv`（追加 U176–U182）；`checkpoints/p05/registries/s4r8/ERRATA_8.txt`（追加 E8-56–E8-60）。
- 新增（brief、脚本）：`checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3a.md`；`testing/d003/stage_s4r8/gate9_r8m1a4.sh`；`testing/d003/stage_s4r8/recheck_s4r7_r8m1a4.py`；`testing/d003/stage_s4r8/append_r8m1a4.sh`；`testing/d003/stage_s4r8/append_rulings_r8m1a4.tsv`；`testing/d003/stage_s4r8/append_errata_r8m1a4.txt`；`testing/d003/stage_s4r8/counted_families_r8m1a4.py`。
- 本交接文档：`checkpoints/p05/P05_S4R8_HANDOVER_M1a_CONT3a_PAUSE.md`。

**证据目录 `checkpoints/p05/evidence/p05-s4r8/`（不提交）：**

- `GATE_R8_M1a4_START.txt`（start 门禁，FAILS=0）；`S4R7_RECHECK_GATE_R8_M1A4_START.tsv`。
- `APPEND_R8_M1a4.txt`（追加记录，FAILS=0）。
- `USED_IN_M1_CORRECTION_R8_M1a4.tsv`（U177）。
- 生成器输出（**`_R2` 为有效版本**）：`SOURCE_HASHES_R8_M1a4_R2.tsv`、`COUNTED_FAMILIES_R8_M1a4_R2.tsv`、`CALLSEQ_UNITS_R8_M1a4_R2.tsv`、`CALLSEQ_POINT_COVERAGE_R8_M1a4_R2.tsv`、`EXPECT_CALLSEQ_R8_M1a4_R2.txt`。

**首次生成器输出（已被 `_R2` 取代，保留不删）：** `SOURCE_HASHES_R8_M1a4.tsv`、`COUNTED_FAMILIES_R8_M1a4.tsv`、`CALLSEQ_UNITS_R8_M1a4.tsv`、`CALLSEQ_POINT_COVERAGE_R8_M1a4.tsv`、`EXPECT_CALLSEQ_R8_M1a4.txt`。其中 `EXPECT_CALLSEQ_R8_M1a4.txt` 由错误的单元集合（S3R4 增补项被错误并入 `d003`/F3 的 U0025）生成，**不得作为期望使用**。

## 4. 期望与运行状态

- **未运行**任何 gdb、驱动、构建、注入或批量核对。
- 期望文件 `EXPECT_CALLSEQ_R8_M1a4_R2.txt` 已写入并记录 sha256 与 UTC（生成时间 UTC 约 05:37–05:38Z；精确值以文件为准）。它只包含规则（完整覆盖、无追踪错误、序列相等或唯一允许改名、无意外 NOT_REACHED）及覆盖计数，**不是**覆盖证明。
- 运行后不得修改该期望。若恢复后需改期望，必须新建 ERRATA，不得改原文件。

## 5. 已知未完成之处（必须在恢复前处理）

1. **驱动身份未完成（U179 核心）。** `counted_families_r8m1a4.py` 中 `driver_identity()` 仍为返回 `None` 的草稿。因此：
   - `CALLSEQ_UNITS_R8_M1a4_R2.tsv` 的单元键只含 (驱动族, tree, NG, twice, route)，**未包含实际驱动路径与 driver_sha256**，不满足单元去重键要求（brief §4：驱动身份、mode、NG、完整环境、argv）。
   - 尤其 state 族（U0021–U0024）：M3 的 G5/G6 实际使用 `r6bstate-*-dbg` 与 `r6bseam-*` 等 dbg 驱动，而命名不能作为身份依据（U179）。恢复后必须按各登记表行反查实际驱动路径与哈希。
   - 因此 `_R2` 单元表**不能直接用于运行**，需先补全驱动身份并以 `_R3` 重生成。
2. **单元 mode 未展开。** 单元表中 `mode` 列未写出（brief §4 要求），需在 `_R3` 中补齐。
3. **完整 seam 覆盖未完成。** G2a/G6 的每个 site/ID（alloc:21–25、fmmret:150–159、kottke_alloc:31、linearsolve、linearsolve_null2 各 ID）需逐一出现在覆盖表中（U181、E8-59）。当前覆盖表只标注族，未逐 ID 展开。
4. **CALLSEQ 运行器、比较器、有效性、K/M 检查、新增项映射（§5–§7）均未生成。**
5. 报告 `P05_S4R8_REPORT_M1a_CONT3a.md`、`STATE.md` 更新、`SHA256SUMS_M1a4.txt`、`commit_rec_r8m1a4.sh`、end 门禁 `GATE_R8_M1a4_END` 均未完成。

## 6. 恢复后的第一步

1. 只读核对 HEAD、HEAD:S4、判定器、status，并与 §1 对照；若任一不符则停下报告。
2. 完成 `driver_identity()`：逐条从 `DRIVERS_R7.tsv`、`DRIVERS_R7_SEAM.tsv`、`DRIVERS_R7_M3.tsv`、`DRIVERS_R8_M1a.tsv`、`DRIVERS_R8_M1a_F2_REUSED.tsv` 按登记行反查实际驱动路径与 driver_sha256，核对文件存在且哈希一致；不以文件名判断构建身份（U179）。
3. 以 `_R3` 后缀重生成五个表（不覆盖 `_R2`、不覆盖首次输出）；单元键补入驱动路径、driver_sha256、mode；seam 逐 ID 展开。
4. 重写期望为 `EXPECT_CALLSEQ_R8_M1a4_R3.txt`（新文件），记录 sha256 与 UTC，**之后才允许运行**。该期望应取代 `_R2` 期望，并在报告中说明原因。
5. 再按 brief §5 起草 gdb 追踪器与 runner，经 safe_run 运行前做 grep（0 命中）与 prerun_log 记录。

## 7. 必须保留的证据（恢复时不得删除或覆盖）

- `checkpoints/p05/evidence/p05-s4r8/GATE_R8_M1a4_START.txt`、`S4R7_RECHECK_GATE_R8_M1A4_START.tsv`、`APPEND_R8_M1a4.txt`。
- `USED_IN_M1_CORRECTION_R8_M1a4.tsv`。
- `_R2` 与首次生成器的全部输出（首次输出已标注为不得作期望使用）。
- `PRERUN_CHECKS_R8_M1a.txt` 中本轮新增记录（counted_families、gate9、recheck、append 等脚本的 grep 命中数）。
- 证据目录 `safe_run.log` 中本轮的全部记录。

## 8. 收尾状态声明

**用户主动暂停（额度不足）。本轮未完成 R8 M1a 续3a 范围，尚未执行正式收尾门禁（end）及记录提交。** 工作区改动未提交，保留供恢复。不得将本轮标为完成，不得写“下一步续3b”，不得写签收建议。

本轮未完成 R8 M1a 续3a 范围，等待用户审核。
