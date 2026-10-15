# P05-S4 R8 M1c3（r8m1c3）报告：裁决与勘误登记 + M1c F3 运行、比较、逐行判定 + M1 总表

> 依据任务书 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c3.md`。不宣布任何阶段完成。
> 开工基线 HEAD `3661416ee071993e5c7fa7e3bf9f6488b48d8db5`（r8m1c2 收尾提交）。

## 0. 结论摘要

- **F3 运行**：6 次运行器/判定器调用全部返回 rc=0；36 条驱动 sha256 记录全部等于预注册值。
- **F3 与冻结期望**：`DIFFS=0 GDB_DIVERGENT=0`（比较脚本末行）。
- **F2↔F3**：`DIFFS=0 GDB_DIVERGENT=0`。
- **逐行判定**：F3 236 行全部 MATCH（G5 177、G6 25、G6c 18、CTRL_AUX 16）；MISMATCH 0、FLAKY 0、NOT_RUN 0。判定规则在运行后修正三次（见 §4.3），修正的依据与历史版本如实列出。
- **阳性对照**：`POSCTRL=PASS`（比较阳性对照 DIFFS=1，未改副本 DIFFS=0；判定阳性对照对被改行给出 MISMATCH=1）。
- **M1 总表**：M1b 830 行与 M1c 472 行合计 MATCH 1252、NOT_REACHED_AS_EXPECTED 44、NOT_RUN 0、MISMATCH 0、FLAKY 0；U212 单列 SILENT_SWALLOW 6 行、CRASH 14 行。
- **806、415、RP-S3R4-1**：M1 中均为 `NOT_COVERED_IN_M1 → M2`（见 §7）。

本轮未完成 M2 任何补测。阶段与里程碑的收口由用户裁决，本报告不作收口表述。

## 1. 开工门禁

- 基线核对全部通过：HEAD `3661416`；`HEAD:S4` = `6cff923…`（F3）；判定器 sha256 `d2d04145…`；冻结表 `58ce1241…`（472 行）；EFFECTIVE M1b `e248b671…`（830 行）；RULINGS 84298 字节 `9e9f4c74…`；ERRATA_8 63754 字节 `fcbfe6b8…`；`postcommit_r8m1c2.py` `0f2fbad7…`。
- `git status --short` 开工时仅 `?? testing/d003/stage_s4/postcommit_r8m1c2.py`。
- 根目录临时区开工快照：0 条目，sha256 `e3b0c442…`（空串哈希），见 §10。
- **门禁脚本**：`gate_r8m1c3.sh`（由 `gate_r8m1c2.sh` 复制修改）与 `gate_check_r8m1c3.py`、允许列表两份、`diff_gate_r8m1c3.sh`。
  - 第一次 start 门禁 `GATE_R8_M1c3_START.txt` **FAILS=1**：允许列表漏列 `diff_gate_r8m1c3.sh`（执行遗漏，已修正列表与行数核对值）。该文件保留为失败记录。
  - 修正后以 `_R2` 名重跑 start：**`GATE_R8_M1c3_START_R2.txt` FAILS=0**。
  - `GATE_DIFF_R8_M1c3.txt`：四对门禁文件的 diff（已生成）。
- 门禁的 start 检查覆盖：HEAD 与 S4 树；判定器；M1c 预注册 sha256；冻结表 sha256；EFFECTIVE M1b sha256；postcommit_r8m1c2 sha256；r8m1b3 SUMS 10 项 OK；r8m1c2 SUMS 19 项 OK；s4r8 SUMS 非 ERRATA 24 项 OK；RULINGS/ERRATA 基线与开工长度；历史运行器与判定器哈希。

## 2. U218–U222、E8-81、E8-82 登记

脚本：`append_rulings_r8m1c3.sh` → `build_rulings_r8m1c3.py`；`append_errata_r8m1c3.sh` → `build_errata_r8m1c3.py`；追加由 `append_registry_r8m1c3.py` 完成，做前缀校验。

- **RULINGS.tsv**：前缀校验通过（84298 → 86035 字节，追加 1737 字节，5 行 U218–U222，status 生效）。
- **ERRATA_8.txt**：前缀校验通过（63754 → 64662 字节，追加 908 字节，E8-81 与 E8-82）。
- 两份文件仅追加，原条目未改。

登记内容见 RULINGS 与 ERRATA 原文（U218–U222；E8-81 更正 E8-79(e) 的脚本与表名；E8-82 记录 NO_OUTDIR 小写名问题）。

## 3. 预检

脚本 `preflight_m1c_r8m1c3.py`，输出 `PREFLIGHT_M1C_R8_M1c3.txt`，结果 **PREFLIGHT_OK**（FAILS=0）：

- 三个 F3 驱动可执行，sha256 与预注册 `driver_sha256` 相同（r6bstate-F3-dbg `8b269be6…`、r6bseam-seamF-F3 `4c882f73…`、r6bseam-fmmret-F3 `e6ee5b6a…`）；
- 历史预注册 G5、G6、G6c、CONTROL 的 sha256 与记录一致；
- 运行器与判定器 sha256 与门禁记录一致；`r6c_state.gdb`、`r6c_state_gdb.py` 存在；
- 冻结表 472 行，F3 行 236，sha256 与 r8m1c2 RECORD 一致；
- R8 F2 提交副本 8 个文件与 `SHA256SUMS.txt` 一致（只读）；
- `m1c_F2`、`m1c_F3` 不存在（实际名，U219）；
- gdb 版本首行：`GNU gdb (Ubuntu 17.1-2ubuntu1) 17.1`。

## 4. F3 运行、比较与判定

### 4.1 运行

脚本 `run_m1c_r8m1c3.sh F3`（由 r8m1c2 版本复制修改：EV 为 m1c3；只接受 F3；去掉 `M1C_ALLOW_F3` 闸门）。
串行调用：G5 pass1 → G5 pass2 → r6c_judge → seam pass1 → seam pass2 → r6c2_seam_judge。
全部 rc=0。输出目录 `m1c_F3/`（STATE_R6c_pass{1,2}、STATE_SEAM_R6c_pass{1,2}、RESULTS_R6c_STATE、RESULTS_R6c_SEAM、两份 SUMMARY）。

驱动记录 `DRIVER_RUN_RECORD_R8_M1c3.tsv`：36 条数据行，每条 sha256 等于预注册值。
运行器 diff `RUNNER_DIFF_R8_M1c3.txt`（r8m1c2 与 r8m1c3 的运行器与记录脚本）已生成。

### 4.2 比较（§6.1）

脚本 `compare_m1c_f3_r8m1c3.py m1c_F3 REG COMPARE_M1C_F3_R8_M1c3`。

- **F3 vs 冻结**：`COMPARE_M1C_F3_VS_FROZEN_R8_M1c3.tsv`，末行 `DIFFS=0 GDB_DIVERGENT=0`。比较项：rc1/rc2/rc3/hit（gdb 与 nogdb 两侧）、env_as_run（去掉 `S4FMM_DUMP*`）、point_verdict、I1–I6（`-` 跳过）。G5 的 I 项被逐项比较（已抽查）。
- **F2↔F3**：`F2_F3_DIFF_M1C_R8_M1c3.tsv`，末行 `DIFFS=0 GDB_DIVERGENT=0`。
- R8 F2 提交副本 `COMPARE_M1C_F2_R8_M1c2.tsv` 末行为 `DIFFS=0 GDB_DIVERGENT=0`（已核对）。

### 4.3 逐行判定（§6.2）与运行后规则修正

脚本 `verdict_m1c_r8m1c3.py`。**本轮判定经过三次运行，属运行后规则修正，须如实披露：**

| 版本 | 输出 | 结果 | 原因与处置 |
|---|---|---|---|
| v1 | `VERDICT_M1C_R8_M1c3.tsv`（保留） | CTRL_AUX F3、G6c F3 共 34 行 NOT_RUN | 判定脚本要求控制行在 RESULTS 中有记录，但控制行在冻结表中 `exp_point_verdict`/I 项为 `-`，不做 I1–I6 判定。**判定规则错误**（不是运行器未跑到）。 |
| v2 | `VERDICT_M1C_R8_M1c3_R2.tsv`（保留） | 同上 34 行 MISMATCH | 控制行的 point_verdict 比较未跳过 `-` 期望，产生假差异。**实现遗漏**。 |
| v3 | `VERDICT_M1C_R8_M1c3_R3.tsv`、`VERDICT_M1C_R8_M1c3_AGG_R3.tsv`（正式） | 全部 MATCH | 控制行只判事实与 env；point_verdict 与 I 项按冻结表 `-` 跳过（与 §6.2 一致）。 |

三次修正的依据均为冻结表自身的 `-` 标记与任务书 §6.2，**不是**为消除 MISMATCH 而改期望；冻结表未改（sha256 仍为 `58ce1241…`）。G5 与 G6 的 point 行在 v1–v3 中判定规则未变，G5/G6 的 I 项确实被比较（已抽查 `COMPARE_M1C_F3_VS_FROZEN_R8_M1c3.tsv` 中 G5 行的 P1_I1–P1_I6）。

最终判定（v3）按组×树（`VERDICT_M1C_R8_M1c3_AGG_R3.tsv`）：

| 组 | 树 | MATCH | MISMATCH | FLAKY | NOT_RUN |
|---|---|---|---|---|---|
| G5 | F3 | 177 | 0 | 0 | 0 |
| G6 | F3 | 25 | 0 | 0 | 0 |
| G6c | F3 | 18 | 0 | 0 | 0 |
| CTRL_AUX | F3 | 16 | 0 | 0 | 0 |
| **F3 合计** | | **236** | **0** | **0** | **0** |

F2 侧 236 行按 r8m1c2 比较（DIFFS=0）填入，均 MATCH（来源 `COMPARE_M1C_F2_R8_M1c2.tsv`）。合计 472 行。

### 4.4 核对标记行（供 check_report_counts_r8m1c3.py 使用，与证据表逐项比对）

S6_FROZEN_DIFFS=0
S6_FROZEN_GDB_DIVERGENT=0
S6_F2_F3_DIFFS=0
S6_F2_F3_GDB_DIVERGENT=0
S6_F3_G5_MATCH=177
S6_F3_G5_MISMATCH=0
S6_F3_G5_FLAKY=0
S6_F3_G5_NOT_RUN=0
S6_F3_G6_MATCH=25
S6_F3_G6_MISMATCH=0
S6_F3_G6_FLAKY=0
S6_F3_G6_NOT_RUN=0
S6_F3_G6c_MATCH=18
S6_F3_G6c_MISMATCH=0
S6_F3_G6c_FLAKY=0
S6_F3_G6c_NOT_RUN=0
S6_F3_CTRL_AUX_MATCH=16
S6_F3_CTRL_AUX_MISMATCH=0
S6_F3_CTRL_AUX_FLAKY=0
S6_F3_CTRL_AUX_NOT_RUN=0
S6_F3_TOTAL_MATCH=236
S6_F3_TOTAL_MISMATCH=0
S6_F3_TOTAL_FLAKY=0
S6_F3_TOTAL_NOT_RUN=0

## 5. 阳性对照（§6.3，U220 口径）

脚本 `posctrl_m1c_r8m1c3.py`，输出 `POSCTRL_M1C_R8_M1c3.txt`，结果 **POSCTRL=PASS**：

- **比较阳性对照**：副本 A 改动 `M-once-closed1d-malloc-1` 的 `gdb_rc2` → **DIFFS=1**，被改点出现在 DIFF 中（`A_CHANGED_POINT_IN_DIFF=True`）；副本 B 未改 → **DIFFS=0**。
- **判定阳性对照**：冻结表副本中 F3 点 `M-once-closed1d-malloc-1-F3` 的 `exp_rc1` 由 20 改为 7 → 判定 **MISMATCH=1**，且就是被改行。

**口径说明**：本脚本的比较只比较 pass1 的事实元组，未做正式比较脚本的两遍一致性项（TWO_PASS），因此计数为 1 而不是 U220 所述的 2。这是阳性对照脚本的实现口径，结论（改动被检出、未改为 0）不受影响，如实披露。

## 6. M1 总表（§7）

脚本 `summarize_m1_r8m1c3.py`；输出 `M1_SUMMARY_R8_M1c3_R2.tsv`（见 §4.4 说明的版本历史）。

- M1b：830 行，按 `effective_class_p1` 计数（见表内 M1b 行）。
- M1c：472 行（`VERDICT_M1C_R8_M1c3_R3.tsv`）。
- **合计（M1b+M1c）**：MATCH **1252**；NOT_REACHED_AS_EXPECTED **44**；NOT_RUN **0**；MISMATCH **0**；FLAKY **0**。
- **U212 单列**：SILENT_SWALLOW **6** 行（ADD22-A-7/8/9，属 U100，已转 S5）；CRASH **14** 行（ADD22 的 F2 行，修复前的基线，不是修复证据）。

M1b 有效表的 MATCH 1252 − M1c 的 472 行之中：M1b 的 830 行与 M1c 的 472 行分列于 `TOTAL_M1B`、`TOTAL_M1C` 行。

### 6.1 版本历史（如实披露）

- 第一次运行 `M1_SUMMARY_R8_M1c3.tsv`：读取 M1c 时断言失败（473 行，含计数行 `ROWS=472`），修正读取后重跑成功，但覆盖规则过宽（见 §7）。该过宽版本输出 `M1_SUMMARY_R8_M1c3.tsv`、`FIX_COVERAGE_M1_R8_M1c3.tsv` **保留，不删除，已作废**。
- 正式版本为 `_R2` 后缀。

### 6.2 `FIX_COVERAGE`

见 §7。

### 6.3 核对标记行（供 check_report_counts_r8m1c3.py 使用）

S7_TOTAL_MATCH=1252
S7_TOTAL_NOT_REACHED_AS_EXPECTED=44
S7_TOTAL_NOT_RUN=0
S7_TOTAL_MISMATCH=0
S7_TOTAL_FLAKY=0

## 7. 806、415、RP-S3R4-1 的 M1 覆盖

脚本 `summarize_m1_r8m1c3.py`，输出 `FIX_COVERAGE_M1_R8_M1c3_R2.tsv`：

| 项 | 状态 | M1b 行 | M1c 行 | 映射文件命中 |
|---|---|---|---|---|
| 806 | NOT_COVERED_IN_M1 → M2 | 0 | 0 | 15（ADDITIONS_MAPPING_22 系列） |
| 415 | NOT_COVERED_IN_M1 → M2 | 0 | 0 | 55（ADDITIONS_MAPPING_22 系列） |
| RP-S3R4-1 | NOT_COVERED_IN_M1 → M2 | 0 | 0 | 0 |

规则：只有 M1b/M1c 行的 point_id 本身含该编号才算覆盖。806、415 在 ADDITIONS 映射中有命中（`A-806`、`A-415`），但 M1b/M1c 的 id（`ADD22-A-<n>-F<tree>`、`M-*`、`R4-*`、`SC*`、`C-*`）不含该编号，本轮未能可靠建立映射→M1 行的对应，因此**不作覆盖声明**，转 M2。这是保守结论。

## 8. 措辞与局限

- F2 结果是回归基线，不是修复证据。F3 MATCH 只表示"在该注入下，F3 的事实与不变量等于冻结期望"。
- HOLD 只表示"在该注入（失败层为层 1，G6 有 2 点为层 0）下，各适用不变量成立"。REPORTED_FAILURE 只表示"该注入下返回码非零"。
- **局限（归 M2）**：I7、双目标注入、其他层失败变体、阶段 e、K-1、NB=1–8、类别 C、fmmret 干净对照、RP-R6d-7 仍为 DEFERRED 或未覆盖。806、415、RP-S3R4-1 的 M1 覆盖未闭合。
- F3 MATCH 的判定规则经三次运行后修正（§4.3），它不是无争议的结论，报告如实列出全部版本。

## 9. 检查

### 9.1 运行前检查（§1.3）

每个新脚本运行前执行禁止项正则检查（结果均为 0 行）。逐条列出：

| 脚本 | UTC（检查时刻） | 命中行数 |
|---|---|---|
| gate_r8m1c3.sh | 2026-10-15T05:08:38Z | 0 |
| gate_check_r8m1c3.py | 2026-10-15T05:08:38Z | 0 |
| gate_allow / diff_gate_r8m1c3.sh | 2026-10-15T05:08:38Z | 0 |
| gate_r8m1c3.sh（编辑后复查） | 2026-10-15T05:08:53Z | 0 |
| build_rulings_r8m1c3.py | 2026-10-15T05:09:49Z | 0 |
| build_errata_r8m1c3.py | 2026-10-15T05:09:49Z | 0 |
| append_registry_r8m1c3.py | 2026-10-15T05:09:49Z | 0 |
| append_rulings_r8m1c3.sh | 2026-10-15T05:09:49Z | 0 |
| append_errata_r8m1c3.sh | 2026-10-15T05:09:49Z | 0 |
| preflight_m1c_r8m1c3.py / record_drivers_r8m1c3.py / run_m1c_r8m1c3.sh | 2026-10-15T05:10:29Z | 0 |
| diff_runner_r8m1c3.sh（写入后复查，compare 修改后） | 2026-10-15T05:13:25Z | 0 |
| compare_m1c_f3_r8m1c3.py（修改后） | 2026-10-15T05:13:25Z | 0 |
| verdict_m1c_r8m1c3.py（v1/v2/v3 三次修改，每次复查） | 2026-10-15T05:14:05Z / 05:14:39Z / 05:14:56Z | 0 |
| posctrl_m1c_r8m1c3.py | 2026-10-15T05:15:27Z | 0 |
| summarize_m1_r8m1c3.py（v1、覆盖规则修改后 v2 复查） | 2026-10-15T05:15:54Z / 05:16:08Z / 05:16:36Z | 0 |
| postcommit_r8m1c3.py（修改后） | 2026-10-15T05:17:03Z | 0 |
| copy_registries_r8m1c3.py（修改后） | 2026-10-15T05:17:32Z | 0 |
| check_report_counts_r8m1c3.py（重写后） | 2026-10-15T05:18:01Z | 0 |

注：`check_report_counts_r8m1c3.py` 首版因同义反复与死代码，**未运行**，经重写后才做检查与运行。

### 9.2 内联命令自查（§1.4）

白名单内的内联命令（UTC 与原文）：

- `git rev-parse HEAD`、`git rev-parse HEAD:S4`、`git status --short`、`git branch --show-current`（只读，未写 .git）；
- `sha256sum <仓库内文件>`（基线核对）；
- `date -u +%FT%TZ`（每个检查前）；
- 根目录临时区快照：`date; ls -A /tmp | wc -l; ls -A /tmp | sha256sum; date`（开工与收尾各一次；输出见 §10）；
- `sh testing/d003/safe_run.sh p05-s4r8/m1c3 -- <本轮脚本>`（全部写入与运行）；
- `git log -1`（收尾，见 §11）。

**白名单外（偏离）**：

- `grep -c "	F3	" checkpoints/p05/registries/s4r8/M1c/r8m1c2/PREREG_M1C_FACTS_R8_M1c2.tsv`：内联 `grep -c`，用于统计 F3 行数，**不在白名单内**。结果 236，与预检一致。按 U221 精神，它是只读计数，但仍属偏离，须披露。
- 其余只读核对使用 read/grep/glob 工具，未内联 `ls`/`wc`/`head`/`tail`/`cut`/`awk`/`sed`/`git show`/`git diff`（本轮的 `git show` 仅在脚本内，由门禁执行）。

### 9.3 违规表一：越界写入尝试

无。所有写入经 `safe_run.sh` 或经 safe_run 运行的本轮脚本完成，写入目标均在仓库内（`$EV/`、`testing/d003/`、`checkpoints/p05/`）。

### 9.4 违规表二：工具/脚本事件

| 轮次/时刻 | 事件 | 是否落盘 | 处置 |
|---|---|---|---|
| start 门禁首次运行（05:08:41Z） | 允许列表漏列 `diff_gate_r8m1c3.sh`，FAILS=1 | 是（`GATE_R8_M1c3_START.txt`） | 修正列表，`_R2` 重跑，FAILS=0；失败文件保留 |
| 内联命令 | `grep -c` 白名单外（§9.2） | 否（输出仅显示） | 披露 |
| verdict v1（05:14） | 控制行判定规则错误，34 行 NOT_RUN | 是（`VERDICT_M1C_R8_M1c3.tsv`） | 修正规则，`_R2` 重跑；保留 |
| verdict v2（05:14） | point_verdict 未跳过 `-`，34 行 MISMATCH | 是（`VERDICT_M1C_R8_M1c3_R2.tsv`） | 修正规则，`_R3` 正式版；保留 |
| summary（05:15） | M1c 断言失败（473 行，计数行） | 否（断言在写文件前） | 修正读取，重跑 |
| summary（05:16） | 覆盖规则过宽（map 命中即判覆盖） | 是（`M1_SUMMARY_R8_M1c3.tsv` 与 `FIX_COVERAGE_M1_R8_M1c3.tsv`） | 作废；改保守规则后 `_R2` 正式版；保留 |
| posctrl 口径 | 阳性对照 A 计数为 1（未做两遍 TWO_PASS 项） | 是 | 按 §5 披露，不改结论 |
| 框架事件 | 工具结果落盘到根目录临时区（`/tmp/dsh-spill-*`，glob 与 grep 大结果） | 是（框架落盘） | 框架事件，单列，不算执行者违规 |
| check_report_counts | 首版同义反复 | 否（未运行） | 重写后运行 |
| postcommit 脚本 | 首版含 `/tmp` 字面量 | 否（未运行） | 改为变量路径后检查通过 |

### 9.5 根目录临时区快照

- 开工：`date` 04:00:41 PM AEDT；`ls -A /tmp | wc -l` = **0**；`ls -A /tmp | sha256sum` = `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`（空串）。
- 收尾：见 §10。

## 10. 收尾

- **根目录临时区收尾快照**：`date; ls -A /tmp | wc -l; ls -A /tmp | sha256sum; date`，结果见 §10 收尾输出。
- **快照口径**：`postcommit_r8m1c3.py` 的 `TMP_SHA256` 对条目名列表计算，与内联 `ls -A | sha256sum` 口径不同；空目录两者都为 `e3b0c442…`，可比。

（收尾输出在最终回复与 `POSTCOMMIT_R8_M1c3.txt` 中记录。）

## 11. 提交与 git 状态

- 提交与 `git log -1`、`git status --short` 在提交后记录于 `POSTCOMMIT_R8_M1c3.txt`（由 `postcommit_r8m1c3.py` 生成）。
- 报告 §1–§9 中的 UTC、计数与文件名均与证据表核对（见 `REPORT_COUNT_CHECK_R8_M1c3.txt`）。

本轮未完成 M2 范围，已完成 R8 M1c3 范围（U218–U222、E8-81/82 登记；F3 运行与判定；阳性对照；M1 总表），等待用户审核。
