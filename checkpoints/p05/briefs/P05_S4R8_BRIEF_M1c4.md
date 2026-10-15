# P05-S4 R8 M1c4（r8m1c4）任务书：r8m1c3 审核修正（总表 NOT_RUN、修复覆盖映射、registries 名称对照、阳性对照改用正式比较脚本、独立重比）

> 本轮是 P05-S4 的子轮次 R8 M1c4。不宣布任何阶段完成。先读 AGENTS.md 与 checkpoints/p05/STATE.md。
> 本轮不运行任何驱动、运行器或 gdb。只读已提交的 registries 和 r8m1c3 证据目录，生成修正表。不做 M2 的任何工作。
> 工作量不是停止理由。只有 §1.5 列出的情况可以停止；任何停下都必须先跑 end 门禁，再做记录提交（U158）。
> 第一步：用 **write 工具**把本任务书原文保存为 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c4.md`。

## 0. 开工基线（任一不符就停）
- HEAD = `fc3e8ca1100184e2ae0f3604869265067b4d3035`（r8m1c3 收尾提交）
- `git rev-parse HEAD:S4` = `6cff923a02baf19e01966b2339755cbf3a5deeef`（F3）
- 判定器 `testing/d003/judge_d003.py` sha256 = `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`
- `RULINGS.tsv` 86035 字节，sha256 `82d89c5e7fba0b7f1e8b746c1e2460cf3370efa588964406541214b16fd077c1`
- `ERRATA_8.txt` 64662 字节，sha256 `c8d5a1c11617729f8649528f01ad5194098fc52a8614342661d17a981c346b6f`
- `STATE.md` 8047 字节，sha256 `1d18a12323bdaf05c11a212f3023ff4db430c118b5990f0da6166a8187dbc6ed`
- 冻结表 `registries/s4r8/M1c/r8m1c2/PREREG_M1C_FACTS_R8_M1c2.tsv` sha256 = `58ce124161c0cdb0bd10f10acac351ab7ffa460bb11152abaa6e8004b036f924`
- `registries/s4r8/M1b/r8m1b3/EFFECTIVE_M1B_R8_M1b3.tsv` sha256 = `e248b671fac5d83be2081ca3212a91c3ec2668cc43aa6158578a5573c6cd1ef0`
- `registries/s4r8/M1c/r8m1c3/SHA256SUMS.txt`（25 项）与 `SHA256SUMS_END.txt`（2 项）全部 `-c` OK
- 开工时 `git status --short` 只允许出现：`?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c4.md` 和本轮新建的 `?? testing/d003/stage_s4/*r8m1c4*`
- `EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c4`；safe_run 的目录参数为 `p05-s4r8/m1c4`
- `testing/d003/stage_s4/*r8m1c1*`、`*r8m1c2*`、`*r8m1c3*` 全部冻结，不修改、不运行。r8m1c3 的证据目录 `evidence/p05-s4r8/m1c3/` 只读。

## 1. 执行纪律（与 r8m1c3 相同，逐条遵守）
### 1.1 写文件只有两条途径
**途径 A：write/edit 工具**，只能用于：本任务书副本；本轮新建的脚本与允许列表（`testing/d003/stage_s4/*r8m1c4*`）；本轮报告 `checkpoints/p05/P05_S4R8_M1C4_REPORT.md`；`checkpoints/p05/STATE.md`。
**途径 B：经 `sh testing/d003/safe_run.sh p05-s4r8/m1c4 -- <本轮脚本及参数>` 运行的脚本。** 证据产物、RULINGS/ERRATA 追加（前缀校验）、registries 复制、提交、提交后记录，只能走途径 B。
**一律禁止：** 在 bash 中直接写任何文件（heredoc、`cat >`、`echo >`、`printf >`、`tee`、`cp`、`mkdir`，目标在仓库内也一样）；`safe_run.sh -- sh -c "<内联>"`。safe_run 后面只能接本轮的脚本文件。

脚本的其他要求：
- shell 脚本首行逐字为：
  `REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c4; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"`
- Python 一律用 `python3 -I -B`；临时路径写成 `os.path.join(EV, "tmp", ...)`。
- 不删除、不移动、不覆盖任何文件（U17）。产物作废时用 `_R2` 后缀新建，并在报告中标明。
- **复制到 registries 时保留原文件名，不得改名、不得去掉 `_R2`/`_R3` 后缀**（见 U226）。
- 源码、数据、ERRATA、报告正文中不写 `/tmp` 字面量，一律写"根目录临时区"。只有 §1.2 的快照命令例外。
- 追加 RULINGS/ERRATA 时，要追加的文本放在本轮新建的 builder `.py` 中（用 write 工具），shell 追加脚本只调用 builder，不得含 heredoc。

### 1.2 内联命令白名单（不得含任何 `>` 字符，包括 `2>&1`）
- `git rev-parse HEAD`、`git rev-parse HEAD:S4`、`git status --short`、`git log -1 --format=%H%n%s`
- `sha256sum <仓库内文件>`、`ls -d <仓库内路径>`、`test -e <仓库内路径>`
- `date -u +%FT%TZ`
- 根目录临时区快照，逐字为：`date; ls -A /tmp | wc -l; ls -A /tmp | sha256sum; date`
- `sh testing/d003/safe_run.sh p05-s4r8/m1c4 -- <本轮脚本及参数>`
- 看文件用 read 工具（offset/limit），搜索用 grep 工具，找文件用 glob 工具。`grep -c`、`ls`、`wc`、`head`、`tail`、`cut`、`awk`、`sed`、`git show`、`git diff` 一律不得内联使用。需要统计时，写成本轮脚本，经 safe_run 输出到 `$EV/`，再用 read 读取。

### 1.3 运行前检查（每个新脚本运行前都要做，包括门禁脚本）
顺序固定为：用 write 写好脚本 → 跑 `date -u +%FT%TZ` → 用 grep 工具按下面的正则查该脚本 → 结果为 0 行才可运行。查出问题后改正、重新查，不算违规。报告中逐条列出：脚本名、UTC、命中行数。

### 1.4 内联命令自查
报告"内联命令自查"一节逐条列出本轮执行过的全部内联命令（UTC 与原文）；白名单外的命令单列为偏离。

### 1.5 停止条件（仅限以下各项）
① 写入目标在仓库外；② 写入没走 §1.1 的两条途径；③ 运行了检查未通过的脚本；④ 门禁不符；⑤ 需要改 `S4/` 或已提交的历史装置；⑥ §4.1 独立重比出现非 0 差异（如实记录，不改期望，跳到 §8 收尾）；⑦ §4.4 阳性对照失败。
- 停止后仍要做 §8 收尾。"缺少合格的 start 门禁"不是停止理由；没先跑 start 门禁属于执行遗漏。

## 2. 门禁（第一步做：先跑 start，再做任何追加或生成）
- 用 read 读 `testing/d003/stage_s4/gate_r8m1c3.sh`、`gate_check_r8m1c3.py`、`gate_allow_r8m1c3_start.txt`、`gate_allow_r8m1c3_end.txt`、`diff_gate_r8m1c3.sh`，再用 **write 工具**新建对应的 `*_r8m1c4*` 五个文件。只改以下几处：
  - 基线 HEAD 改为 `fc3e8ca1100184e2ae0f3604869265067b4d3035`；
  - 证据目录与参数改为 `p05-s4r8/m1c4`；输出名形式改为 `GATE_R8_M1c4_<X>.txt`；派生子输出名同样由门禁输出名派生；
  - 自引用的脚本名与允许列表名改为 m1c4；
  - RULINGS/ERRATA 前缀基准改为 §0 的字节数与 sha256；
  - 允许列表内容按下文。
- `diff_gate_r8m1c4.sh` 把五对文件的 `diff -u` 写入 `$EV/GATE_DIFF_R8_M1c4.txt`（diff 返回 1 属正常）。
- **start 允许列表（先写全，再跑；r8m1c3 首次 FAILS=1 正是漏列了 diff 脚本）**：`?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c4.md`、`?? testing/d003/stage_s4/*r8m1c4*`（通配，覆盖本轮全部新脚本与允许列表）。
- start 模式核对：沿用 r8m1c3 的全部检查项。另外：r8m1c3 两份清单（25 + 2 项）`-c` OK；冻结表与 EFFECTIVE M1b 的 sha256（§0）；`STATE.md` sha256（§0）；`postcommit_r8m1c3.py` 已被跟踪且 sha256 = `c665f3215ab562e552dfb051a4cd21d4793761b9c642c3bb7676c7e99805b73a`。
- end 模式：开工快照值与前缀基准都从 start 门禁文件读取；不检查 HEAD^。status 只允许：
  - ` M`：`checkpoints/p05/STATE.md`、`checkpoints/p05/registries/RULINGS.tsv`、`checkpoints/p05/registries/s4r8/ERRATA_8.txt`
  - `??`：`checkpoints/p05/P05_S4R8_M1C4_REPORT.md`、`checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c4.md`、`checkpoints/p05/registries/s4r8/M1c/r8m1c4/*`、`testing/d003/stage_s4/*r8m1c4*`
- end 模式另外核对：RULINGS 与 ERRATA 的开工部分作为前缀逐字节不变；`registries/s4r8/M1c/r8m1c3/` 下的所有文件 sha256 不变（逐个与其两份清单对比）。
- 两份门禁的 FAILS 都必须为 0。

## 3. 裁决与勘误登记（start 门禁通过后做）
### 3.1 RULINGS.tsv 追加（`append_rulings_r8m1c4.sh` 调用 `build_rulings_r8m1c4.py`；5 列；status"生效"；来源"P05-S4 R8 M1c4 任务书 §3"；前缀校验）
- **U223**：接受 r8m1c3（`fc3e8ca`）的 F3 运行数据：6 次调用 rc=0，36 条驱动记录等于预注册值，F3 与冻结表 DIFFS=0，F2↔F3 DIFFS=0，GDB_DIVERGENT=0。判定脚本 v1/v2 的错误只出在 34 个控制行上（冻结表中这些行的 point_verdict 与 I 项为 `-`），G5/G6 的 202 行在三个版本中规则未变，冻结表未改，因此按实现错误接受，不算"看到结果后改期望"。F3 236 行 MATCH 的采信，以本轮 §4.1 独立重比为 0 差异为条件。这不是 M1、R8 或 P05-S4 的签收。
- **U224**：r8m1c3 的 M1 总表少计 6 行：M1b 中 G2c_control 的 6 行（F2/F3 各 3 行，NOT_RUN_REGISTRY_ERROR，effective_verdict = NOT_RUN_AS_EXPECTED，依据 U65/U139/U212）没有计入合计。正确合计为 1302 行 = MATCH 1252 + NOT_REACHED_AS_EXPECTED 44 + NOT_RUN_AS_EXPECTED 6 + MISMATCH 0 + FLAKY 0。总表必须断言"各类之和 = 830 + 472"。
- **U225**：修复覆盖的映射规则。`ADD22-<A|B>-<n>-<tree>` 中的 n 等于 `registries/s4r8/M1a/ADDITIONS_MAPPING_22_R8_M1a6.tsv` 的 `row`；对应关系以两表的 env 逐键相等为准（mode、NG、INJECT）。按此规则：806 = A-1/2/3，RP-S3R4-1（1729）= A-4/5/6，415 = B-11…21；对照为 A-10、B-22；U96 为 A-7/8/9（属 U100，转 S5）。这三项在 M1 中**按"该注入下的返回码与类别"口径已覆盖**（F3 行均为 MATCH），不转 M2。F2 侧（806、415 为 CRASH；1729 为 REPORTED_FAILURE rc1=-3）是修复前的基线，不是修复证据。这些注入点的 I1–I6 在 M1 中未测，作为局限写明，不进 M2，除非用户另行裁决。r8m1c3 的 `FIX_COVERAGE_M1_R8_M1c3_R2.tsv` 作废（保留原文件）。
- **U226**：r8m1c3 复制到 registries 时去掉了后缀：registries 中的 `VERDICT_M1C_R8_M1c3.tsv`、`VERDICT_M1C_R8_M1c3_AGG.tsv`、`M1_SUMMARY_R8_M1c3.tsv`、`FIX_COVERAGE_M1_R8_M1c3.tsv` 分别是证据中 `_R3`、`_AGG_R3`、`_R2`、`_R2` 的内容，与证据中的同名文件不同。已提交的文件不改名（U17），由本轮的名称对照表说明。自本轮起，复制一律保留原名。
- **U227**：r8m1c3 比较阳性对照没有调用正式比较脚本（它另写了一套只比 pass1 的逻辑）；正式比较脚本 `compare_m1c_f3_r8m1c3.py` 的第三个参数 OUT_PREFIX 收进来后没有使用，输出名写死。本轮新建 `compare_m1c_f3_r8m1c4.py`：与 r8m1c3 版本相比，只改 EV、输入目录参数和输出名（用 OUT_PREFIX 生成），比较逻辑逐字不变（以 diff 为证）。阳性对照必须调用它。
- **U228**：对 r8m1c3 报告"需要你裁决"三项的答复：(1) F3 MATCH 按 U223 有条件采信；(2) 806/415/RP-S3R4-1 按 U225 处理，不转 M2；(3) 阳性对照按 U227 重做，计数如实记录，口径仍为 U220。r8m1c3 的内联 `grep -c` 按执行偏离接受，不追认为合规。

### 3.2 ERRATA_8.txt 追加（`append_errata_r8m1c4.sh` 调用 `build_errata_r8m1c4.py`；只追加；前缀校验）
- **E8-83**：r8m1c3 报告 §0、§6、§6.3，STATE 关键数字表，以及 `M1_SUMMARY_R8_M1c3_R2.tsv` 中"NOT_RUN 0"有误，应为 NOT_RUN_AS_EXPECTED 6（G2c_control，U224）。`REPORT_COUNT_CHECK_R8_M1c3.txt` 的 ALL_MATCH 只说明报告与总表一致，不说明总表正确。原条目不改。
- **E8-84**：r8m1c3 报告 §7 与 `FIX_COVERAGE_M1_R8_M1c3_R2.tsv` 的结论"806、415、RP-S3R4-1 NOT_COVERED_IN_M1 → M2"有误；正确结论见 U225 和本轮 `FIX_COVERAGE_M1_R8_M1c4.tsv`。
- **E8-85**：r8m1c3 报告 §6.1 说第一版 `M1_SUMMARY_R8_M1c3.tsv` 覆盖规则过宽而作废。实际上它与 `_R2` 的 sha256 相同（`5b7cee33…`），只有 FIX_COVERAGE 两版内容不同。
- **E8-86**：r8m1c3 registries 的文件名与证据不一致，以及 STATE 中引用的 `VERDICT_M1C_R8_M1c3_AGG_R3.tsv`、`M1_SUMMARY_R8_M1c3_R2.tsv` 在 registries 中不存在：见 U226 与本轮 `REGISTRY_NAME_MAP_R8_M1c3.tsv`。
- **E8-87**：r8m1c3 比较阳性对照的实现与正式比较脚本不同，且正式脚本的 OUT_PREFIX 参数未被使用：见 U227。

## 4. 修正工作（只读输入，全部输出到 `$EV/`）
### 4.1 独立重比（`recheck_f3_r8m1c4.py`）
- 输入**只**用已提交的文件：冻结表 F3 行（236）；`registries/s4r8/M1c/r8m1c3/M1C_F3_STATE_R6c_pass{1,2}.tsv`、`M1C_F3_STATE_SEAM_R6c_pass{1,2}.tsv`、`M1C_F3_RESULTS_R6c_STATE.tsv`、`M1C_F3_RESULTS_R6c_SEAM.tsv`。不 import、不调用 r8m1c3 的任何脚本，从头独立实现。
- 规则：按 `base_id` 与 pass 连接。对每一遍：`exp_rc1/rc2/rc3/hit` 中不为 `-` 的项，分别与 `gdb_*` 和 `nogdb_*` 比较；env_as_run 与 env_expected 去掉 `S4FMM_DUMP*` 后，把键值对排序比较；`exp_point_verdict` 不为 `-` 时，与 RESULTS 中同 point_id、同 pass 的 `point_verdict` 比较，并对 I1–I6 中期望不为 `-` 的项逐项比较。
- 输出 `RECHECK_F3_R8_M1c4.tsv`：先按项目列出检查次数，再列出全部差异，末行 `CHECKS=<n> DIFFS=<m>`。同时按组×row_kind 统计行数（应为 G5 point 177、G6 point 25、G6c control 18、CTRL_AUX control_aux 16）。
- 规划者用同样的规则只读预算过：rc1、rc2、hit 各 944 次，rc3 708 次，point_verdict 404 次，I 项 2424 次，差异 0。确切数字如实记录，不作期望。DIFFS 非 0 → 停止条件 ⑥。

### 4.2 M1 总表修正（`summarize_m1_r8m1c4.py`，输出 `M1_SUMMARY_R8_M1c4.tsv`）
- M1b：830 行，取 `EFFECTIVE_M1B_R8_M1b3.tsv`，按组×树×effective_class_p1 计数，再按 effective_verdict 计数（MATCH、NOT_REACHED_AS_EXPECTED、NOT_RUN_AS_EXPECTED、MISMATCH、FLAKY，其余值一律单列为 OTHER）。
- M1c：472 行，取 `registries/s4r8/M1c/r8m1c3/VERDICT_M1C_R8_M1c3.tsv`（即证据中的 `_R3`，见 U226），读取时跳过 `#` 行与 `ROWS=` 行。
- 合计行：MATCH、NOT_REACHED_AS_EXPECTED、NOT_RUN_AS_EXPECTED、MISMATCH、FLAKY、OTHER。**断言**：M1b 各类之和 = 830，M1c 各类之和 = 472，合计 = 1302；断言失败就不写文件、输出 FAIL。
- U212 单列：SILENT_SWALLOW 6 行（ADD22-A-7/8/9）、CRASH 14 行（ADD22 的 F2 行），逐行列出 point_id。

### 4.3 修复覆盖（`fix_coverage_r8m1c4.py`，输出 `FIX_COVERAGE_M1_R8_M1c4.tsv`）
- 输入：`registries/s4r8/M1a/ADDITIONS_MAPPING_22_R8_M1a6.tsv`（22 行）、`registries/s4r8/M1a/REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv` 的 ADDITIONS_22 行、`EFFECTIVE_M1B_R8_M1b3.tsv`、`registries/s4r8/M1b/r8m1b1/RESULTS_M1B_R8_M1b1.tsv` 的 ADDITIONS_22 行。
- 连接：把 ADD22 的 n 与映射表的 row 连接，并核对 env（预注册的 env 中的 FMM_MODE、S4FMM_NG、S4FMM_INJECT，与映射表的 point_or_combo、injection 一致；对照行 10、22 按 `none` 对应无注入）。任一行不一致，就把该行标为 MAP_ENV_MISMATCH，不计覆盖。
- 每个 ADD22 行输出：n、item、point_id（F2、F3 各一行）、env、F3/F2 的 effective_verdict、effective_class_p1、p1_rc1、映射核对结果。
- 汇总：每项（806、1729/RP-S3R4-1、415、U96、control）列出 F3 行数、MATCH 行数、类别分布与 F2 基线类别分布。状态写 `COVERED_IN_M1_RC_CLASS`（全部 F3 行 MATCH 且映射核对通过），否则写 `NOT_COVERED_IN_M1`。另加一列 `invariants_I1_I6 = NOT_MEASURED_IN_M1`。
- 规划者只读预查：806、1729 的 F3 行 rc1=1，415 的 F3 行 rc1=20，均为 MATCH；806、415 的 F2 行是 CRASH，1729 的 F2 行是 rc1=-3。数字如实记录。

### 4.4 比较脚本修正与阳性对照
- `compare_m1c_f3_r8m1c4.py`：用 read 读 r8m1c3 版本，再用 write 新建。只改：EV 为 m1c4；`argv[1]` 改为"相对仓库根的 F3 结果目录"（正式复现时用 `checkpoints/p05/evidence/p05-s4r8/m1c3/m1c_F3`，只读）；输出名改为 `$EV/<OUT_PREFIX>_VS_FROZEN.tsv` 与 `$EV/<OUT_PREFIX>_F2_F3_DIFF.tsv`。比较逻辑逐字不变。`diff_compare_r8m1c4.sh` 把两版的 `diff -u` 写入 `$EV/COMPARE_DIFF_R8_M1c4.txt`，报告中逐行说明每处变化。
- **正式复现**：`compare_m1c_f3_r8m1c4.py checkpoints/p05/evidence/p05-s4r8/m1c3/m1c_F3 REG CMP_REAL_R8_M1c4`。再用 `cmp_outputs_r8m1c4.py` 把两份输出与 registries 中 r8m1c3 的 `COMPARE_M1C_F3_VS_FROZEN_R8_M1c3.tsv`、`F2_F3_DIFF_M1C_R8_M1c3.tsv` 逐行比较（首行注释可以不同，其余行必须相同），结果写入 `CMP_OUTPUTS_R8_M1c4.txt`。
- **阳性对照**（`posctrl_m1c_r8m1c4.py`，用 shutil 把 m1c3 的 `m1c_F3/` 下 4 个 STATE 文件与 2 个 RESULTS 文件复制到 `$EV/tmp/posctrl_A/`、`$EV/tmp/posctrl_B/`；dump 与 state 子目录不复制，若比较脚本需要它们，就报告并停在 ⑦）：
  - 副本 A：把一个 G5 point 行的 `gdb_rc2` 在 **pass1 与 pass2 两个文件中**都改为不同的值，再用 subprocess 调用 `compare_m1c_f3_r8m1c4.py tmp/posctrl_A 的仓库相对路径 REG POSCTRL_A_R8_M1c4`。通过条件：两份输出的 DIFFS>0，且被改的 point_id 出现在 DIFF 行中。
  - 副本 A2：只改 pass1 的 `gdb_rc2`（检验两遍一致性那一项），通过条件同上。
  - 副本 B：不改，通过条件是 DIFFS=0。
  - 判定阳性对照沿用 r8m1c3 做法（复制冻结表、改一行 `exp_rc1`，调用 `verdict_m1c_r8m1c3.py <副本>`，它只写 tmp）。这是唯一允许运行的 r8m1c3 脚本，因为它在覆盖模式下不写 `$EV` 正式输出。运行前须用 read 确认这一点，并在报告中引用相应行号。
  - 全部计数如实记录（U220），输出 `POSCTRL_M1C_R8_M1c4.txt`，以 `POSCTRL=PASS/FAIL` 结尾。

### 4.5 registries 名称对照（`name_map_r8m1c4.py`，输出 `REGISTRY_NAME_MAP_R8_M1c3.tsv`）
- 列：registries 中 r8m1c3 的文件名、sha256、证据 m1c3 中 sha256 相同的文件名（可能有多个；没有就写 NONE）、证据中同名文件的 sha256（不存在就写 NONE）、二者是否相同。覆盖 r8m1c3 registries 中的全部 27 个文件。
- 另列证据 m1c3 中所有带 `_R2`/`_R3` 后缀的文件，以及它们在 registries 中有没有副本。

## 5. 措辞
- F3 MATCH 只表示"在该注入下，F3 的事实与不变量等于冻结期望"。`COVERED_IN_M1_RC_CLASS` 只表示"该注入下 F3 的返回码与类别等于预注册期望"。REPORTED_FAILURE 只表示"该注入下返回码非零"。
- F2 结果是回归基线，不是修复证据。不写"已修好""已验证"。
- 局限：806/415/1729 注入点的 I1–I6 未测；I7、双目标注入、其他层失败变体、阶段 e、K-1、NB=1–8、类别 C、fmmret 干净对照、RP-R6d-7、CTRL_SEAM fmmret 完整补测仍归 M2。

## 6. 报告数字核对（`check_report_counts_r8m1c4.py`）
- 报告中写核对标记行（`C4_RECHECK_DIFFS=`、`C4_TOTAL_MATCH=`、`C4_TOTAL_NOT_REACHED_AS_EXPECTED=`、`C4_TOTAL_NOT_RUN_AS_EXPECTED=`、`C4_TOTAL_MISMATCH=`、`C4_TOTAL_FLAKY=`、`C4_TOTAL_ROWS=`、`C4_COV_806_F3_MATCH=`、`C4_COV_1729_F3_MATCH=`、`C4_COV_415_F3_MATCH=`、`C4_POSCTRL_A_DIFFS=`、`C4_POSCTRL_A2_DIFFS=`、`C4_POSCTRL_B_DIFFS=`、`C4_CMP_REAL_SAME=`）。
- 脚本**从证据表重新计算**每一项（不得从报告取值后再写回），逐项比较，输出 `REPORT_COUNT_CHECK_R8_M1c4.txt`（`ALL_MATCH` 或列出不一致项）。另外独立断言 C4_TOTAL_ROWS = 1302。

## 7. （留空，本轮不做 M2）

## 8. 收尾（完成或停止都要做）
1. 先写好 `postcommit_r8m1c4.py`（输出 `$EV/POSTCOMMIT_R8_M1c4.txt`，U17 拒绝覆盖），在提交前通过 §1.3 检查，随本轮提交，提交后只运行（U222）。
2. `copy_registries_r8m1c4.py`：复制到 `checkpoints/p05/registries/s4r8/M1c/r8m1c4/`，**保留原名**，写 `SHA256SUMS.txt`，逐个比对 sha256 与原件一致（先确认全部输入存在再建目录）。复制：start 门禁文件、GATE_DIFF、RECHECK、M1_SUMMARY、FIX_COVERAGE、COMPARE_DIFF、CMP_REAL 两份输出、CMP_OUTPUTS、三组 POSCTRL 比较输出与 POSCTRL 文件、REGISTRY_NAME_MAP、REPORT_COUNT_CHECK（含 `_R2`，如有）。end 门禁文件在 end 门禁后单独追加复制，写入 `SHA256SUMS_END.txt`。
3. `sums_ev_r8m1c4.py`：在 `$EV/` 写 `SHA256SUMS.txt`，覆盖全部非二进制证据。
4. 用 edit 工具更新 STATE.md，必须 ≤ 8192 字节（现为 8047，字节数用本轮脚本经 safe_run 确认）。必要时压缩措辞，删减的内容只能删去已在报告中有的细节：
   - 本轮开工基线改为 `fc3e8ca`；当前轮次改为 r8m1c4；
   - "S4R8 M1 总表"一行改为：1302 行 = MATCH 1252 + NOT_REACHED_AS_EXPECTED 44 + NOT_RUN_AS_EXPECTED 6；MISMATCH 0、FLAKY 0；U212 单列 SILENT 6、CRASH 14；来源 `registries/s4r8/M1c/r8m1c4/M1_SUMMARY_R8_M1c4.tsv`；
   - 开放问题中"806、415、RP-S3R4-1"一行改为：M1 已覆盖（返回码与类别口径，U225）；I1–I6 未测；
   - "M1c 结果"一行改为：F3 236 MATCH（U223，以独立重比为条件），独立重比 DIFFS=<m>；
   - 证据位置只保留最近三轮（m1c4、m1c3、m1c2），文件名一律用 registries 中实际存在的名字。
5. 用 write 工具写报告 `checkpoints/p05/P05_S4R8_M1C4_REPORT.md`，须包含：开工门禁；U223–U228；E8-83–E8-87；§4.1–§4.5 的结果；"运行前检查"与"内联命令自查"两节；违规表一、表二；根目录临时区开工与收尾快照；局限（§5）。结尾写"本轮未完成/已完成 R8 M1c4 范围，等待用户审核"。写完后运行 `check_report_counts_r8m1c4.py`，不是 ALL_MATCH 就用 edit 修正报告后重跑（输出用 `_R2` 后缀），两次结果都保留。
6. 跑 end 门禁（FAILS=0），再用 `commit_r8m1c4.sh` 经 safe_run 提交（脚本内先核对 status）。提交信息：
   `P05-S4 R8 M1c4 (r8m1c4): U223-U228, E8-83..E8-87, M1c3 review fixes: independent F3 recheck (DIFFS=<m>), M1 totals 1302 (NOT_RUN_AS_EXPECTED 6), fix coverage 806/1729/415 via ADD22 row map, posctrl via formal compare, registry name map; awaiting user review`
   如果在停止条件处停下，提交信息改为说明停在哪一步，同样以 `awaiting user review` 结尾。
7. 提交后经 safe_run 运行 `postcommit_r8m1c4.py`，并在最终回复中原文给出它的输出。此后不再新建任何文件；`git status --short` 应为空。

## 9. 最终回复（简短中文）
列出：U223–U228、E8-83–E8-87 是否已登记；独立重比的 CHECKS 与 DIFFS；修正后的 M1 合计（M1b、M1c 分列，单列 SILENT 6 行、CRASH 14 行）；806/1729/415 的覆盖表（F3 MATCH 数、F2 基线类别）；正式复现与 r8m1c3 输出是否相同；阳性对照 A/A2/B 的确切计数；名称对照的要点；违规表；提交后的 `git log -1` 与 `git status --short`；需要用户裁决的事项。
不得出现"签收""已修好""已验证"等字样（否定用法也避免）。
