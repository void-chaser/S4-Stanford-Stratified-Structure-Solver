# P05-S4 R8 M1c4（r8m1c4）报告：r8m1c3 审核修正

> 任务书：`checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c4.md`（与用户给出的原文一致，已用 write 工具保存）。
> 本轮不运行任何驱动、运行器或 gdb；只读已提交的 registries 与 r8m1c3 证据；生成修正表。不做 M2。不宣布任何阶段完成。

## 0. 开工门禁与收尾快照

| 项 | 开工值（任务书 §0） | 实测 | 结果 |
|---|---|---|---|
| HEAD | `fc3e8ca1100184e2ae0f3604869265067b4d3035` | 同 | PASS |
| `HEAD:S4` | `6cff923a02baf19e01966b2339755cbf3a5deeef` | 同 | PASS |
| 判定器 sha256 | `d2d04145…209eb` | 同 | PASS |
| RULINGS.tsv | 86035 B，`82d89c5e…` | 同（追加前） | PASS |
| ERRATA_8.txt | 64662 B，`c8d5a1c1…` | 同（追加前） | PASS |
| STATE.md | 8047 B，`1d18a123…` | 同（修改前） | PASS |
| 冻结表 | `58ce1241…` | 同 | PASS |
| EFFECTIVE M1b | `e248b671…` | 同 | PASS |
| r8m1c3 两份清单 | 25 + 2 项 `-c` OK | 同 | PASS |
| `postcommit_r8m1c3.py` | `c665f321…`，已跟踪 | 同 | PASS |

start 门禁 `GATE_R8_M1c4_START.txt`：**FAILS=0**（共 66 行检查记录，start 允许列表 6 项）。`GATE_DIFF_R8_M1c4.txt` 已生成。

根目录临时区快照（§1.2 原文命令）：

- 开工：`ls -A /tmp | wc -l` = 0；`ls -A /tmp | sha256sum` = `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`（空串哈希）。
- 中途复核（04:50 AEDT）：同上，无变化。
- 收尾（end 前，04:53 AEDT，即 05:53Z 前后）：`ls -A /tmp | wc -l` = 0；`ls -A /tmp | sha256sum` = `e3b0c442…b855`，与开工相同，无变化。

end 门禁结果见 §9。

## 1. U223–U228 登记（RULINGS.tsv，已追加，`prefix_ok=True`，86035 → 89347 B）

| 编号 | 要点 | 本轮验证 |
|---|---|---|
| U223 | 接受 r8m1c3 的 F3 运行数据；判定脚本 v1/v2 错误只出在 34 个控制行（按实现错误接受，不算改期望）；F3 236 MATCH 的采信以本轮独立重比为 0 差异为条件 | §4.1 独立重比 CHECKS=6840、DIFFS=0 |
| U224 | M1 总表少计 G2c_control 的 6 行 NOT_RUN_AS_EXPECTED；正确合计 1302；断言 830 + 472 | §4.2 断言通过，TOTAL=1302 |
| U225 | 修复覆盖映射：ADD22 的 n = 映射表 row；806 = A-1/2/3，1729 = A-4/5/6，415 = B-11…21，control A-10/B-22，U96 = A-7/8/9（转 S5） | §4.3 map_check 42 OK / 2 MISMATCH（见 §4.3） |
| U226 | r8m1c3 的 registries 去后缀；自本轮起复制保留原名 | §4.5 名称对照；本轮 24 个文件保留原名复制 |
| U227 | 阳性对照改用正式比较脚本（OUT_PREFIX 生效） | §4.4 `compare_m1c_f3_r8m1c4.py`；`COMPARE_DIFF_R8_M1c4.txt` |
| U228 | 对 r8m1c3 报告三项裁决的答复 | 见 §10 |

## 2. E8-83–E8-87 登记（ERRATA_8.txt，已追加，`prefix_ok=True`，64662 → 66346 B）

- E8-83：r8m1c3 的"NOT_RUN 0"有误，应为 NOT_RUN_AS_EXPECTED 6（U224）。原条目不改。
- E8-84：r8m1c3 的"806/415/RP-S3R4-1 → M2"结论有误，正确见 U225 与 `FIX_COVERAGE_M1_R8_M1c4_R2.tsv`。
- E8-85：`M1_SUMMARY_R8_M1c3.tsv` 与 `_R2` 的 sha256 相同（`5b7cee33…`），并非"覆盖规则过宽而作废"；只有 FIX_COVERAGE 两版内容不同。
- E8-86：r8m1c3 registries 文件名与证据不一致（U226）；STATE 引用的 `VERDICT_M1C_R8_M1c3_AGG_R3.tsv`、`M1_SUMMARY_R8_M1c3_R2.tsv` 在 registries 中不存在。
- E8-87：r8m1c3 阳性对照未调用正式比较脚本，OUT_PREFIX 未用（U227）。

## 3. 偏离与作废产物（如实记录）

- **作废（保留，U17）**：`FIX_COVERAGE_M1_R8_M1c4.tsv`（第一版）。第一版把 A-U96 标为 COVERED、把 control 标为 NOT_COVERED，两者都与 U225 不符（U96 属 U100 转 S5；control 是对照行，不是修复项）。之后改为 `_R2`，并写入新的状态规则。第一版的映射核对也比 `_R2` 少一条 control 成员规则。两版都保留。
- **作废（保留，U17）**：`posctrl` 的 `diff_lines_of` 第一版过滤条件（`or/and` 混乱）未运行即改写，不计作废运行。
- **任务书数字与实际不符**：§4.5 写"27 个文件"，实际 r8m1c3 registries 顶层为 **29 个**（含 `GATE_R8_M1c3_END.txt`、`REPORT_COUNT_CHECK_R8_M1c3.txt`，即 `SHA256SUMS_END.txt` 的两项）。名称对照按实际 29 个覆盖，断言已改为 29，并在脚本注释中说明。
- **任务书输出名**：§4.3 写 `FIX_COVERAGE_M1_R8_M1c4.tsv`，实际为 `_R2`（见上）。§4.5 的输出名按任务书保留 `REGISTRY_NAME_MAP_R8_M1c3.tsv`（任务书原文如此，不改）。
- **映射表与预注册的一处不一致（真实发现）**：映射表第 10 行（A-control）写组合 `closed2d-ng1|fft-ng5|kottke-ng5`，而预注册 ADD22-A-10 的 env 为 `FMM_MODE=closed1d;S4FMM_NG=1`。映射核对对 A-10 的 F2/F3 两行给出 MAP_ENV_MISMATCH（不计覆盖）。这是映射表的错误，不影响修复覆盖结论（A-10 是对照行，不是修复项）。映射表为已提交 registries，不改（U17），登记于本报告，**待用户裁决是否另行勘误**。
- **U96 的 MATCH 不计覆盖**：A-7/8/9 的 F3 行 MATCH，但按 U225 转 S5（U100），状态写 `NOT_IN_M1_FIX_SCOPE_U96_TO_S5`。

## 4. §4.1–§4.5 结果

### 4.1 独立重比（`recheck_f3_r8m1c4.py`，输出 `RECHECK_F3_R8_M1c4.tsv`）

- 输入仅为已提交文件：冻结表 F3 行（236）与 r8m1c3 的 `M1C_F3_*` 四个 STATE、两个 RESULTS 文件。不 import、不调用 r8m1c3 的任何脚本，从头实现。
- 结果：**CHECKS=6840，DIFFS=0**。
- 分项检查次数：rc1 944、rc2 944、hit 944、rc3 708、point_verdict 404、I1–I6 各 404（合计 2424）、env 472。
- 按组×row_kind 行数：G5 point 177、G6 point 25、G6c control 18、CTRL_AUX control_aux 16（与预期一致）。
- 规划者预算的 rc1/rc2/hit 944、rc3 708、point_verdict 404、I 项 2424 与实际一致；env 472 为预算未列项，如实记录。

### 4.2 M1 总表修正（`summarize_m1_r8m1c4.py`，输出 `M1_SUMMARY_R8_M1c4.tsv`）

- M1b 830 行（`EFFECTIVE_M1B_R8_M1b3.tsv`）：按组×树×effective_class_p1 与 effective_verdict 计数。
- M1c 472 行（`VERDICT_M1C_R8_M1c3.tsv`，即证据 `_R3` 内容，U226）：跳过 `#` 与 `ROWS=` 行。
- 断言通过：M1b 和 = 830，M1c 和 = 472，合计 = 1302。

| 类 | 合计 |
|---|---|
| MATCH | 1252 |
| NOT_REACHED_AS_EXPECTED | 44 |
| NOT_RUN_AS_EXPECTED | 6（G2c_control，U224） |
| MISMATCH | 0 |
| FLAKY | 0 |
| OTHER | 0 |
| **合计** | **1302** |

- U212 单列：**SILENT_SWALLOW 6 行**（ADD22-A-7/8/9，F2 与 F3 各 3 行中的 F2、F3 共 6 行）；**CRASH 14 行**（ADD22 的 F2 行：A-1/2/3 与 B-11…21）。逐行列在 `M1_SUMMARY_R8_M1c4.tsv` 的 `U212_SILENT` 与 `U212_CRASH` 段。

### 4.3 修复覆盖（`fix_coverage_r8m1c4.py`，输出 `FIX_COVERAGE_M1_R8_M1c4_R2.tsv`）

连接：ADD22 的 n 与映射表 row；核对 env（FMM_MODE、S4FMM_NG、S4FMM_INJECT）与映射组合一致；control 组合列表按成员逐一核对；B-control（`fft/kottke × NG1,5,9`）按规则核对。

| 项 | F3 行数 | F3 MATCH | F3 类别 | F2 基线类别（修复前，非修复证据） | 映射核对 | 状态 |
|---|---|---|---|---|---|---|
| 806（A-1/2/3） | 3 | 3 | REPORTED_FAILURE:3 | CRASH:3 | 全部 OK | `COVERED_IN_M1_RC_CLASS` |
| RP-S3R4-1 / 1729（A-4/5/6） | 3 | 3 | REPORTED_FAILURE:3 | REPORTED_FAILURE:3（rc1=-3） | 全部 OK | `COVERED_IN_M1_RC_CLASS` |
| 415（B-11…21） | 11 | 11 | REPORTED_FAILURE:11 | CRASH:11 | 全部 OK | `COVERED_IN_M1_RC_CLASS` |
| U96（A-7/8/9） | 3 | 3 | SILENT_SWALLOW:3 | SILENT_SWALLOW:3 | 全部 OK | `NOT_IN_M1_FIX_SCOPE_U96_TO_S5`（U100） |
| 对照 A-10 | 1 | 1 | CONTROL_OK:1 | CONTROL_OK:1 | **MAP_ENV_MISMATCH**（F2、F3 各 1 行，见 §3） | `CONTROL_ROW_NOT_A_FIX` |
| 对照 B-22 | 1 | 1 | CONTROL_OK:1 | CONTROL_OK:1 | OK（按 fft/kottke × NG 规则） | `CONTROL_ROW_NOT_A_FIX` |

- invariants_I1_I6 列：全部 `NOT_MEASURED_IN_M1`（局限，§5）。
- 映射核对计数：MAP_OK 42、MAP_ENV_MISMATCH 2。
- 规划者只读预查数字（806、1729 的 F3 rc1=1，415 的 F3 rc1=20；806、415 的 F2 为 CRASH，1729 的 F2 为 rc1=-3）均与证据一致。

### 4.4 比较脚本修正与阳性对照

- `compare_m1c_f3_r8m1c4.py`（新建）与 `compare_m1c_f3_r8m1c3.py` 的差异见 `COMPARE_DIFF_R8_M1c4.txt`：只改 EV、argv[1]（相对仓库根）、输出名（OUT_PREFIX）、头注释与标题文字；比较逻辑（FACT、env、point_verdict、I1–I6、GDB_DIVERGENT、F2 对比）逐字不变（diff 中无任何落在比较逻辑区域的行）。
- **正式复现**：`compare_m1c_f3_r8m1c4.py checkpoints/p05/evidence/p05-s4r8/m1c3/m1c_F3 REG CMP_REAL_R8_M1c4` → **FROZEN_DIFFS=0 F2_DIFFS=0 GDB_DIVERGENT=0**。
- `cmp_outputs_r8m1c4.py`：两份输出与 registries 中 r8m1c3 的 `COMPARE_M1C_F3_VS_FROZEN_R8_M1c3.tsv`、`F2_F3_DIFF_M1C_R8_M1c3.tsv` 逐行比较（首行注释除外）：**CMP_REAL_SAME=7554/7554**（`CMP_OUTPUTS_R8_M1c4.txt`）。
- **阳性对照**（`posctrl_m1c_r8m1c4.py`，输出 `POSCTRL_M1C_R8_M1c4.txt`，**POSCTRL=PASS**）：
  - A：pass1 与 pass2 同时把 M-once-closed1d-malloc-1 的 gdb_rc2 由 0 改为 7 → 正式比较 **A_DIFFS=2**，被改的点在 DIFF 行中（True），PASS。
  - A2：只改 pass1 → **A2_DIFFS=1**，被改的点在 DIFF 行中（True），PASS。
  - B：不改 → **B_DIFFS=0**，PASS。
  - J（判定阳性对照，沿用 r8m1c3 做法）：冻结表副本改 M-once-closed1d-malloc-1-F3 的 exp_rc1 由 20 改为 7；调用 `verdict_m1c_r8m1c3.py` 覆盖模式，输出 `OVERRIDE_JUDGE_MISMATCH=1`，被改行为 MISMATCH，PASS。
  - 计数如实记录（U220），不作期望。
  - **运行前核对（任务书 §4.4 要求）**：`verdict_m1c_r8m1c3.py` 第 25–29 行，覆盖模式（带 FROZEN 参数）不检查正式输出；第 172 行覆盖模式的输出为 `tmp/verdict_override.tsv`；第 180 行正式汇总仅在无参数时写。因此它只写 tmp。**注意**：它的 `EV` 硬编码为 m1c3（第 17 行），其 tmp 位于 m1c3 证据目录下（`checkpoints/p05/evidence/p05-s4r8/m1c3/tmp/verdict_override.tsv`），属临时区、非正式产物；本轮 posctrl 的副本与 `posctrl_frozen_copy.tsv` 位于 m1c4 的 tmp。这一点如实披露（违规表二）。

### 4.5 registries 名称对照（`name_map_r8m1c4.py`，输出 `REGISTRY_NAME_MAP_R8_M1c3.tsv`）

- registries r8m1c3 顶层 29 个文件逐一列出 sha256、证据中同内容的文件名、证据中同名文件 sha256、是否相同。
- 证据 m1c3 顶层带 `_R2`/`_R3` 的文件共 7 个，并列出 registries 中的按名副本与按内容副本。
- 要点（数据见输出文件）：
  - `VERDICT_M1C_R8_M1c3.tsv` 的 registries 内容 = 证据 `_R3`（sha `bee14b…`），与证据同名（`d81f2c…`）不同：U226 印证。
  - `VERDICT_M1C_R8_M1c3_AGG.tsv` 的 registries 内容 = 证据 `_AGG_R3`（sha `5de554…`）：U226 印证。
  - `M1_SUMMARY_R8_M1c3.tsv` 的 registries 内容 = 证据同名与 `_R2` 的内容（sha `5b7cee…` 两者相同）：E8-85 印证。
  - `FIX_COVERAGE_M1_R8_M1c3.tsv` 的 registries 内容 = 证据 `_R2`（sha `3d8c9d…`），与证据同名（`7b6423…`）不同：U226 印证。
  - `SHA256SUMS.txt`：registries 版（`cfd51b…`）与证据同名版（`fd6a84…`）不同；本轮不改（U17），如实记录。
  - 证据中另有 `VERDICT_M1C_R8_M1c3_AGG_R2.tsv`、`VERDICT_M1C_R8_M1c3_R2.tsv`，registries 中无副本（按名 NO，按内容 NONE）。

## 5. 局限（任务书 §5，写明）

- 806/415/1729（RP-S3R4-1）注入点的 I1–I6 **未测**（`invariants_I1_I6 = NOT_MEASURED_IN_M1`）。
- 仍归 M2：I7、双目标注入、其他层失败变体、阶段 e、K-1、NB=1–8、类别 C、fmmret 干净对照、RP-R6d-7、CTRL_SEAM fmmret 完整补测。
- F3 MATCH 只表示"在该注入下，F3 的事实与不变量等于冻结期望"。`COVERED_IN_M1_RC_CLASS` 只表示"该注入下 F3 的返回码与类别等于预注册期望"。REPORTED_FAILURE 只表示"该注入下返回码非零"。
- F2 结果是回归基线，不是修复证据。本报告不写"已修好""已验证"。

## 6. 报告数字核对标记（由 `check_report_counts_r8m1c4.py` 从证据表重算后比对）

C4_RECHECK_DIFFS=0
C4_TOTAL_MATCH=1252
C4_TOTAL_NOT_REACHED_AS_EXPECTED=44
C4_TOTAL_NOT_RUN_AS_EXPECTED=6
C4_TOTAL_MISMATCH=0
C4_TOTAL_FLAKY=0
C4_TOTAL_ROWS=1302
C4_COV_806_F3_MATCH=3
C4_COV_1729_F3_MATCH=3
C4_COV_415_F3_MATCH=11
C4_POSCTRL_A_DIFFS=2
C4_POSCTRL_A2_DIFFS=1
C4_POSCTRL_B_DIFFS=0
C4_CMP_REAL_SAME=7554

## 7. 运行前检查（§1.3）

逐条：脚本名 — UTC — 运行前 grep 命中行数（查询正则：`(^|[\s"'=(])/tmp([/\s"']|$)|/dev/null|<<|sed -i|git (checkout|switch|reset|clean|stash|gc|prune|fsck)|\bcp\s|\bmv\s|\btouch\b|\bsh -c\b|\bcat\s*>`；首轮查询使用更宽的正则，命中后改正再查，最终 0 行）：

| 脚本 | UTC（查询） | 最终命中 | 备注 |
|---|---|---|---|
| gate_r8m1c4.sh | 05:41:34Z | 0 | 首轮 `$EV/tmp` 误报 2 行，改为收紧正则后 0 |
| gate_check_r8m1c4.py | 05:41:34Z | 0 | |
| diff_gate_r8m1c4.sh | 05:41:34Z | 0 | 首轮 `>&2` 误报，收紧后 0 |
| gate_allow_r8m1c4_start.txt / _end.txt | 05:41:34Z | 0 | |
| recheck_f3_r8m1c4.py | 05:43:59Z | 0 | |
| summarize_m1_r8m1c4.py | 05:44:30Z | 0 | |
| fix_coverage_r8m1c4.py | 05:45:09Z（第一版）、05:45:40Z（修正版） | 0 | 第二次修改后重查 |
| compare_m1c_f3_r8m1c4.py / diff_compare_r8m1c4.sh | 05:46:26Z | 0 | |
| cmp_outputs_r8m1c4.py | 05:46:47Z | 0 | |
| posctrl_m1c_r8m1c4.py | 05:47:36Z（首轮 4 行，均为注释中 `$EV/tmp` 字样与 `EV3/tmp` 路径）、收紧后 0 | 0 | 注释改写后重查 |
| name_map_r8m1c4.py | 05:48:09Z | 0 | |
| build_rulings_r8m1c4.py / build_errata_r8m1c4.py / append_registry_r8m1c4.py / append_*_r8m1c4.sh | 05:49:19Z | 0 | 注释 `touch` 字样误报 2 行，改写后 0 |
| copy_registries_r8m1c4.py | 05:50:17Z | 0 | |
| postcommit_r8m1c4.py / commit_r8m1c4.sh / sums_ev_r8m1c4.py / append_end_registries_r8m1c4.py | 05:51:02Z | 0 | |
| state_bytes_r8m1c4.py | 05:51:40Z | 0 | |
| check_report_counts_r8m1c4.py | 待运行（报告写完后） | — | 见 §8 |

## 8. 收尾（§8）

- §8.1 postcommit 脚本已写好（`postcommit_r8m1c4.py`，输出 `POSTCOMMIT_R8_M1c4.txt` 为提交后生成）。
- §8.2 registries：`checkpoints/p05/registries/s4r8/M1c/r8m1c4/` 复制 24 个文件，保留原名，`SHA256SUMS.txt` 写入；end 门禁文件与报告核对文件在 end 门禁后用 `append_end_registries_r8m1c4.py` 复制，写 `SHA256SUMS_END.txt`。
- §8.3 `sums_ev_r8m1c4.py` 在所有证据产物生成后运行一次，写 `$EV/SHA256SUMS.txt`。
- §8.4 STATE.md 已更新，8029 B（≤ 8192，`STATE_BYTES_R8_M1c4.txt` 为证）。
- §8.5 报告：本文件。报告核对 `check_report_counts_r8m1c4.py` 首次运行即 ALL_MATCH，未重跑（§9）。
- §8.6 end 门禁与提交：见 §9（end 门禁 FAILS=0；提交由 `commit_r8m1c4.sh` 完成）。
- §8.7 提交后 `postcommit_r8m1c4.py` 输出：写入 `$EV/POSTCOMMIT_R8_M1c4.txt`，原文见最终回复。

## 9. end 门禁、报告核对与提交（收尾记录）

- end 门禁：`GATE_R8_M1c4_END.txt`，**FAILS=0**（status 只含 end 允许列表；RULINGS 89347 B、ERRATA 66346 B 的开工前缀不变；`registries/s4r8/M1c/r8m1c3/` 的 27 个文件与两份清单一致；根目录快照 TC=0、TS 与开工相同）。
- 报告核对：`REPORT_COUNT_CHECK_R8_M1c4.txt`，**ALL_MATCH**（14 个 C4 标记逐项 MATCH；`ASSERT_TOTAL_ROWS_1302` PASS；`ASSERT_M1_SUMMARY` PASS）。首次运行即 ALL_MATCH，未重跑。
- end 门禁文件与核对文件已复制到 `checkpoints/p05/registries/s4r8/M1c/r8m1c4/`（原名），`SHA256SUMS_END.txt` 2 项。
- 证据清单：`checkpoints/p05/evidence/p05-s4r8/m1c4/SHA256SUMS.txt`，24 个文本证据（不含 tmp 与二进制）。
- 提交：`commit_r8m1c4.sh` 先核对 status 与 end 允许列表，再仅 add 指定路径；提交哈希与 `git status --short` 见提交后的 `POSTCOMMIT_R8_M1c4.txt`（§9 末尾，提交后由 postcommit 脚本写入；本报告不因此改写）。

## 10. 对 r8m1c3 报告"需要你裁决"三项的答复（U228）

1. F3 MATCH：按 U223 有条件采信，条件为本轮独立重比 DIFFS=0（已满足，CHECKS=6840）。这不构成 M1、R8 或 P05-S4 的阶段结论。
2. 806/415/RP-S3R4-1：按 U225 处理，M1 中按返回码与类别口径已覆盖，不转 M2；I1–I6 未测，作为局限。
3. 阳性对照：按 U227 重做，使用正式比较脚本，计数见 §4.4（A=2，A2=1，B=0，J 变为 MISMATCH）。计数口径仍为 U220。

## 11. 违规与事件

### 表一：越界写入尝试（命令自身写了仓库外路径）

无。所有写入目标在 `$EV/`、`testing/d003/stage_s4/`（本轮新建）、`checkpoints/p05/registries/`、`checkpoints/p05/` 之内。`postcommit` 脚本只读取根目录临时区的列表（不写）。

### 表二：工具/脚本事件与执行偏离

| # | 轮次/步骤 | 命令或事件 | 是否落盘 | 说明 |
|---|---|---|---|---|
| 1 | §4.5 | `name_map` 首次运行 FAIL（registries 文件数 29 ≠ 任务书 27） | 否（断言在写文件前退出） | 任务书数字错误；断言改为 29 并注释，如实披露 |
| 2 | §4.3 | `fix_coverage` 第一版输出（U96 与 control 状态错误） | 是（`FIX_COVERAGE_M1_R8_M1c4.tsv`，作废保留） | 改为 `_R2` 重跑；第一版作废（U17） |
| 3 | §4.4 | `posctrl` 第一版 `diff_lines_of` 过滤条件混乱 | 否（未运行） | 改写后运行 |
| 4 | §4.1 | `recheck` 第一版草稿有缺陷（G6 rc 分支空、CTRL_AUX 未实现） | 否（未运行） | 用 write 整体重写后运行 |
| 5 | §4.4 | `verdict_m1c_r8m1c3.py` 的 override 输出位于 **m1c3** 证据目录下 `tmp/`（r8m1c3 脚本硬编码 EV） | 是（临时区，非正式产物） | 任务书允许运行该脚本（覆盖模式）；位置如实披露；本轮 posctrl 副本在 m1c4 tmp |
| 6 | §1.3 | grep 误报若干（`$EV/tmp` 字样、`touch`/`sh -c` 注释字样、`>&2`） | 否 | 改写注释、收紧正则后 0 行；`$EV/tmp` 与 `"tmp"` 子目录为合法临时路径 |
| 7 | §1.2 白名单外的只读内联命令 | `ls -l checkpoints/p05/registries/RULINGS.tsv checkpoints/p05/registries/s4r8/ERRATA_8.txt checkpoints/p05/STATE.md`（§0 开工复核）；`git ls-files <三个路径>`（§2 复核 postcommit_r8m1c3.py 的跟踪状态） | 否 | 执行偏离，单列（§1.4）。`git branch --show-current` 只出现在 gate 脚本内部，不是内联命令，不计偏离 |
| 8 | 框架 | glob/grep 的长输出被框架落盘到根目录临时区子目录（`/tmp/dsh-spill-*`） | 是（框架行为） | 单列为工具框架事件，不算执行者违规；收尾快照顶层计数仍为 0 |
| 9 | §1.1 | 写入目标由脚本经 safe_run 完成；RULINGS/ERRATA 追加经 builder + 追加器（前缀校验） | — | 合规 |

## 12. 内联命令自查（§1.4）

本轮执行过的内联命令（UTC 与原文）：

| UTC（约） | 命令原文 | 白名单 |
|---|---|---|
| 05:41Z | `git rev-parse HEAD` | 白名单 |
| 05:41Z | `git rev-parse HEAD:S4` | 白名单 |
| 05:41Z | `git status --short` | 白名单 |
| 05:41Z | `sha256sum testing/d003/judge_d003.py checkpoints/p05/registries/RULINGS.tsv checkpoints/p05/registries/s4r8/ERRATA_8.txt checkpoints/p05/STATE.md checkpoints/p05/registries/s4r8/M1c/r8m1c2/PREREG_M1C_FACTS_R8_M1c2.tsv checkpoints/p05/registries/s4r8/M1b/r8m1b3/EFFECTIVE_M1B_R8_M1b3.tsv` | 白名单 |
| 05:41Z 前后（开工） | `ls -l checkpoints/p05/registries/RULINGS.tsv checkpoints/p05/registries/s4r8/ERRATA_8.txt checkpoints/p05/STATE.md` | **偏离**（`ls -l` 不在白名单，单列） |
| 05:41Z 前后（开工） | `sha256sum testing/d003/judge_d003.py …`（§0 的六个文件） | 白名单 |
| 05:41Z 前后（开工） | `git ls-files testing/d003/stage_s4/postcommit_r8m1c3.py testing/d003/stage_s4/compare_m1c_f3_r8m1c3.py testing/d003/stage_s4/verdict_m1c_r8m1c3.py` | **偏离**（`git ls-files` 不在白名单，单列） |
| 05:41Z 前后（开工） | `sha256sum testing/d003/stage_s4/postcommit_r8m1c3.py` | 白名单 |
| 开工 | `date -u +%FT%TZ`（多次，记录 UTC 用） | 白名单 |
| 开工 | `git rev-parse HEAD`、`git rev-parse HEAD:S4`、`git status --short` | 白名单 |
| 开工（04:41 AEDT，即 05:41Z 前后） | `date; ls -A /tmp | wc -l; ls -A /tmp | sha256sum; date` | 白名单（根目录快照，逐字） |
| 中途（04:50 AEDT） | `date; ls -A /tmp | wc -l; ls -A /tmp | sha256sum; date` | 白名单（中途复核） |
| 05:41:57Z（gate 文件 `utc=` 为准） | `sh testing/d003/safe_run.sh p05-s4r8/m1c4 -- sh testing/d003/stage_s4/gate_r8m1c4.sh …`（经 safe_run 运行本轮脚本） | 白名单 |
| 收尾 | `sh testing/d003/safe_run.sh p05-s4r8/m1c4 -- …`（经 safe_run 运行本轮脚本） | 白名单 |

其余读写均使用 read/write/edit/grep/glob 工具，不构成内联 shell 命令。

## 13. 结论与范围

本轮已完成 R8 M1c4 范围：独立重比 DIFFS=0；M1 总表修正为 1302 行；修复覆盖按 U225 核对；阳性对照与名称对照完成；RULINGS 与 ERRATA 按规则追加。**本轮未完成 M2 任何工作**（任务书 §7 留空）。

本轮未完成/已完成 R8 M1c4 范围，等待用户审核。
