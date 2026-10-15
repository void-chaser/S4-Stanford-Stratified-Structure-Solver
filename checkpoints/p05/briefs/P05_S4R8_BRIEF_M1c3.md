# P05-S4 R8 M1c3（r8m1c3）任务书：裁决与勘误登记 + M1c F3 运行、比较、逐行判定 + M1 总表

> 本轮是 P05-S4 的子轮次 R8 M1c3。不宣布任何阶段完成。先读 AGENTS.md 与 checkpoints/p05/STATE.md。
> 范围：U218–U222、E8-81 登记；M1c F3 运行；F3 与冻结期望比较、F3 与 R8 F2 比较；逐行判定；阳性对照；M1 总表。不做 M2 任何补测。
> 工作量不是停止理由。只有 §1.5 列出的情况可以停止；任何停下都必须先跑 end 门禁，再做记录提交（U158）。
> 第一步：用 **write 工具**把本任务书原文保存为 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c3.md`。

## 0. 开工基线（任一不符就停）
- HEAD = `3661416ee071993e5c7fa7e3bf9f6488b48d8db5`（r8m1c2 收尾提交）
- `git rev-parse HEAD:S4` = `6cff923a02baf19e01966b2339755cbf3a5deeef`（F3）
- 判定器 `testing/d003/judge_d003.py` sha256 = `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`
- 冻结表 `checkpoints/p05/registries/s4r8/M1c/r8m1c2/PREREG_M1C_FACTS_R8_M1c2.tsv` sha256 = `58ce124161c0cdb0bd10f10acac351ab7ffa460bb11152abaa6e8004b036f924`（472 行）
- `checkpoints/p05/registries/s4r8/M1b/r8m1b3/EFFECTIVE_M1B_R8_M1b3.tsv` sha256 = `e248b671fac5d83be2081ca3212a91c3ec2668cc43aa6158578a5573c6cd1ef0`（830 行）
- `RULINGS.tsv` 84298 字节、sha256 `9e9f4c748544354adfd4b640147c25466de27b4a3ef6ee2752d8963c3d8361e2`
- `ERRATA_8.txt` 63754 字节、sha256 `fcbfe6b8cf3ab201c8bcd3dda86a59ecd6e3a9d4393fb81b1cd6950a2fb2be02`
- 开工时 `git status --short` 只允许出现：
  - `?? testing/d003/stage_s4/postcommit_r8m1c2.py`（r8m1c2 提交后创建，sha256 `0f2fbad75cac4ae7d39fa848a34a823fcbfed3640613728937b1490f13e14ab9`，本轮随记录提交，不修改、不运行）
  - `?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c3.md`
  - 本轮新建的 `?? testing/d003/stage_s4/*r8m1c3*`
- 证据目录 `EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c3`；safe_run 的目录参数为 `p05-s4r8/m1c3`
- `testing/d003/stage_s4/*r8m1c1*`、`*r8m1c2*` 已冻结，不修改、不运行（`postcommit_r8m1c2.py` 只提交）。r8m1c2 的运行脚本把 EV 写死为 m1c2，本轮**不得**复用，须新建 m1c3 版本。

## 1. 执行纪律（与 r8m1c2 相同，逐条遵守）
### 1.1 写文件只有两条途径
**途径 A：write/edit 工具**，只能用于：本任务书副本；本轮新建的脚本与允许列表（`testing/d003/stage_s4/*r8m1c3*`）；本轮报告 `checkpoints/p05/P05_S4R8_M1C3_REPORT.md`；`checkpoints/p05/STATE.md`。
**途径 B：经 `sh testing/d003/safe_run.sh p05-s4r8/m1c3 -- <本轮脚本及参数>` 运行的脚本。** 证据产物、RULINGS/ERRATA 追加（前缀校验）、registries 复制、提交、提交后记录，只能走途径 B。
**一律禁止：** 在 bash 中直接写任何文件（heredoc、`cat >`、`echo >`、`printf >`、`tee`、`cp`、`mkdir`，目标在仓库内也一样）；`safe_run.sh -- sh -c "<内联>"`。safe_run 后面只能接本轮的脚本文件。

脚本的其他要求：
- shell 脚本首行逐字为：
  `REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"`
- Python 一律用 `python3 -I -B`；临时路径写成 `os.path.join(EV, "tmp", ...)`。
- 不删除、不移动、不覆盖任何文件（U17）。产物作废时用 `_R2` 后缀新建，并在报告中标明。
- 源码、数据、ERRATA、报告正文中不写 `/tmp` 字面量，一律写"根目录临时区"。只有 §1.2 的快照命令例外。
- 追加 RULINGS/ERRATA 时，要追加的文本放在本轮新建的 `.txt` 或 builder `.py` 中（用 write 工具），shell 追加脚本只调用 builder，**不得含 heredoc**（r8m1c2 第一版因此被 §1.3 查出）。

### 1.2 内联命令白名单（不得含任何 `>` 字符，包括 `2>&1`）
- `git rev-parse HEAD`、`git rev-parse HEAD:S4`、`git status --short`、`git log -1 --format=%H%n%s`
- `sha256sum <仓库内文件>`、`ls -d <仓库内路径>`、`test -e <仓库内路径>`
- `date -u +%FT%TZ`
- 根目录临时区快照，逐字为：`date; ls -A /tmp | wc -l; ls -A /tmp | sha256sum; date`
- `sh testing/d003/safe_run.sh p05-s4r8/m1c3 -- <本轮脚本及参数>`
- 看文件用 read 工具（offset/limit），搜索用 grep 工具，找文件用 glob 工具。**`ls`/`wc`/`head`/`tail`/`cut`/`awk`/`sed`/`git show`/`git diff` 不得内联使用**（r8m1c2 的偏离）。需要统计或比对时，写成本轮脚本，经 safe_run 输出到 `$EV/`，再用 read 读取。

### 1.3 运行前检查（每个新脚本运行前都要做，包括门禁脚本）
顺序固定为：用 write 写好脚本 → 跑 `date -u +%FT%TZ` → 用 grep 工具按下面的正则查该脚本 → 结果为 0 行才可运行。查出问题后改正、重新查，不算违规。报告中逐条列出：脚本名、UTC、命中行数。
```
(^|[^A-Za-z0-9_}])/tmp|/dev/null|<<-?\s*['"]?[A-Za-z_]+|sed\s+-i|python3\s+-c|cat\s+>|\btee\b|\brm\s|\bmv\s|[^&>]&\s*($|;)|git\s+(fsck|gc|prune|stash|checkout|switch|reset|clean)
```
跳过此检查就运行脚本，属于执行遗漏，须披露，但不是停止理由。运行检查未通过的脚本，按停止条件 ③ 处理。

### 1.4 内联命令自查
报告"内联命令自查"一节逐条列出本轮执行过的全部内联命令（UTC 与原文）；白名单外的命令单列为偏离。

### 1.5 停止条件（仅限以下各项）
① 写入目标在仓库外；② 写入没走 §1.1 的两条途径；③ 运行了检查未通过的脚本；④ 门禁不符；⑤ 需要改 `S4/` 或已提交的历史装置；⑥ §4 预检失败；⑦ F3 运行器报 GDB_DIVERGENT（运行器自身会中断，未跑到的行记 NOT_RUN，仍要做 §6 的判定与汇总，然后收尾）；⑧ §6 阳性对照失败。
- **F3 与冻结期望之间的差异不是停止条件**，一律记 MISMATCH 并继续。
- "缺少合格的 start 门禁"不是停止理由；没有先跑 start 门禁属于执行遗漏。
- 停止后仍要做 §8 收尾。

## 2. 门禁（第一步做：先跑 start，再做任何追加或运行）
- 用 read 读 `testing/d003/stage_s4/gate_r8m1c2.sh`、`gate_check_r8m1c2.py`、`gate_allow_r8m1c2_start.txt`、`gate_allow_r8m1c2_end.txt`，再用 **write 工具**新建对应的 `*_r8m1c3*` 四个文件。只改以下几处：
  - 基线 HEAD 改为 `3661416ee071993e5c7fa7e3bf9f6488b48d8db5`；
  - 证据目录与参数改为 `p05-s4r8/m1c3`；输出名形式改为 `GATE_R8_M1c3_<X>.txt`；派生子输出名同样由门禁输出名派生；
  - 自引用的脚本名与允许列表名改为 m1c3；
  - RULINGS/ERRATA 前缀基准改为 §0 的字节数与 sha256；
  - 允许列表内容按下文。
- 新建 `diff_gate_r8m1c3.sh`：把四对文件的 `diff -u` 写入 `$EV/GATE_DIFF_R8_M1c3.txt`（diff 返回 1 属正常）。
- start 允许列表：`?? testing/d003/stage_s4/postcommit_r8m1c2.py`、`?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c3.md`、`?? testing/d003/stage_s4/*r8m1c3*`。
- start 模式核对：沿用 r8m1c2 的全部检查项，另加：
  - 冻结表 sha256（§0）；
  - `registries/s4r8/M1c/r8m1c2/SHA256SUMS.txt` 全部 19 项 `-c` OK；
  - `EFFECTIVE_M1B_R8_M1b3.tsv` sha256（§0）；
  - `postcommit_r8m1c2.py` sha256（§0）。
- end 模式：开工快照值与前缀基准都从 start 门禁文件读取；不检查 HEAD^。status 只允许：
  - ` M`：`checkpoints/p05/STATE.md`、`checkpoints/p05/registries/RULINGS.tsv`、`checkpoints/p05/registries/s4r8/ERRATA_8.txt`
  - `??`：`checkpoints/p05/P05_S4R8_M1C3_REPORT.md`、`checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c3.md`、`checkpoints/p05/registries/s4r8/M1c/r8m1c3/*`、`testing/d003/stage_s4/*r8m1c3*`、`testing/d003/stage_s4/postcommit_r8m1c2.py`
- end 模式另外核对：RULINGS 与 ERRATA 的开工部分作为前缀逐字节不变。
- 两份门禁的 FAILS 都必须为 0。

## 3. 裁决与勘误登记（start 门禁通过后做）
### 3.1 RULINGS.tsv 追加（脚本 `append_rulings_r8m1c3.sh` 调用 `build_rulings_r8m1c3.py`；5 列；status"生效"；来源"P05-S4 R8 M1c3 任务书 §3"；前缀校验）
- **U218**：接受 r8m1c2（`3661416`）的结果与全部披露：事实冻结 472 行（`58ce1241…`），F2 基线 DIFFS=0、GDB_DIVERGENT=0（1112 条比较记录），阳性对照通过。按 U214，准许在 r8m1c3 运行 F3。这不是 M1、R8 或 P05-S4 的签收。
- **U219**：r8m1c2 的输出目录 `m1c_F2`（大写；任务书写作 `m1c_f2`）按执行偏离接受，不移动（U17）。自 r8m1c3 起，目录名一律以运行脚本实际生成的 `m1c_<TREE>`（`m1c_F2`、`m1c_F3`）为准，预检须检查实际名。
- **U220**：r8m1c2 阳性对照的"DIFFS=1"是任务书的计数错误：改动一个 `gdb_rc2` 必然同时破坏 STATE_FACT 与 TWO_PASS 两项，并使 GDB_DIVERGENT=1。接受"DIFFS>0，且被改动的 point_id 出现在 DIFF 行中；未改副本 DIFFS=0"为阳性对照判定口径。自本轮起，确切计数如实记录，不作期望。
- **U221**：r8m1c2 中白名单外的只读内联命令（`ls`、`wc`、`head`、`tail`、`cut`、`awk`、`sed -n`、`git show`、`git diff`）按执行偏离接受，不追认为合规。
- **U222**：`postcommit_r8m1c2.py`（提交后创建，未跟踪）随 r8m1c3 记录提交纳入，不修改、不再运行。自本轮起，提交后记录脚本必须在提交前写好并通过 §1.3 检查，提交后只运行、不新建。

### 3.2 ERRATA_8.txt 追加（脚本 `append_errata_r8m1c3.sh` 调用 `build_errata_r8m1c3.py`；只追加；前缀校验）
- **E8-81**：更正 E8-79(e)。E8-79(e) 中写的脚本与表为 `count_r7_f2_facts_r8m1c2.py` / `R7_F2_FACT_DIST_R8_M1c2.tsv`；有效的是 `count_r7_f2_facts_r8m1c2_R2.py` / `R7_F2_FACT_DIST_R8_M1c2_R2.tsv`。旧版按整行比较两遍，因 `gdb_log_sha256` 列天然不同而报 False，属口径错误，不是数据不一致；数字 132/45/25/16/18 不变。原条目不改。
- **E8-82**：r8m1c2 预检的 `NO_OUTDIR m1c_f2` / `m1c_f3` 检查的是小写名，与运行脚本实际生成的 `m1c_F2` 不对应。运行前 `m1c_F2` 确实不存在（依据：safe_run.log 的时间顺序与运行脚本的 U17 拒绝逻辑），结果不受影响。见 U219。

## 4. 预检（脚本 `preflight_m1c_r8m1c3.py`，先于任何驱动运行）
输出 `$EV/PREFLIGHT_M1C_R8_M1c3.txt`，以 `PREFLIGHT_OK` 结尾才可继续。核对：
- F3 三个驱动可执行，sha256 与 M1c 预注册（`REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv`）及冻结表 F3 行的 `driver_sha256` 相同：`evidence/p05-s4r8/drivers_r8m1/{r6bstate-F3-dbg,r6bseam-seamF-F3,r6bseam-fmmret-F3}/driver`。
- 四份历史预注册（G5 STATE_v2、CONTROL、SEAM、SEAM_CONTROL）的 sha256 等于 `registries/s4r7/REGISTRY_S4_PRE_R7_M3.tsv` 表头记录的值。
- 运行器、判定器、`r6c_state.gdb`、`r6c_state_gdb.py` 的 sha256 与 start 门禁一致。
- 冻结表 sha256 与 r8m1c2 RECORD 一致，472 行；其中 F3 行 236 行。
- R8 F2 基线的提交副本（`registries/s4r8/M1c/r8m1c2/M1C_F2_*`，8 个文件）sha256 与该目录 `SHA256SUMS.txt` 一致。本轮的 F2 侧一律只读这些提交副本，不读 m1c2 证据目录。
- `gdb --version` 首行写入输出。
- `$EV/m1c_F3/` 不存在（**实际名，大写**）。

## 5. F3 运行（脚本 `run_m1c_r8m1c3.sh F3`、`record_drivers_r8m1c3.py`）
- 用 read 读 `run_m1c_r8m1c2.sh` 与 `record_drivers_r8m1c2.py`，再用 write 新建 m1c3 版本。只改：首行 EV 改为 m1c3；记录文件名改为 `DRIVER_RUN_RECORD_R8_M1c3.tsv`；只接受参数 `F3`（F2 拒绝）；去掉 `M1C_ALLOW_F3` 闸门。两对文件的 `diff -u` 写入 `$EV/RUNNER_DIFF_R8_M1c3.txt`（由一个本轮 diff 脚本生成）。
- 命令形式与顺序同 r8m1c2：G5 pass1 → G5 pass2 → `r6c_judge.py` → seam pass1 → seam pass2 → `r6c2_seam_judge.py`，串行、不用 `&`，超时自然等待，不重复启动。输出 `$EV/m1c_F3/`。
- 每次运行器/判定器调用前后，三个驱动的 sha256 追加到 `DRIVER_RUN_RECORD_R8_M1c3.tsv`（应为 36 条，全部等于预注册值）。
- 运行器输出的 `tree` 列是历史标签 `F`，不代表实际的树；实际的树以驱动 sha256 为准（U214）。

## 6. F3 比较、逐行判定、阳性对照
### 6.1 比较（脚本 `compare_m1c_f3_r8m1c3.py <R8_F3目录名> <F2来源目录> <输出前缀>`）
- 正式调用：`compare_m1c_f3_r8m1c3.py m1c_F3 REG COMPARE_M1C_F3_R8_M1c3`（REG 表示 `registries/s4r8/M1c/r8m1c2/M1C_F2_*`）。
- 输出两份：
  - `COMPARE_M1C_F3_VS_FROZEN_R8_M1c3.tsv`：F3 实测与冻结表 F3 行（236 行）逐行比较。比较项：facts（rc1、rc2、rc3、hit，gdb 与 nogdb 两侧；log-hash 列除外）、env_as_run 与 `env_expected` 逐键比较（去掉 `S4FMM_DUMP*`）、point_verdict、I1–I6（G6/G6c 和控制点按冻结表的 `-` 跳过）。
  - `F2_F3_DIFF_M1C_R8_M1c3.tsv`：F3 实测与 R8 F2 提交副本逐点逐项比较，列出全部差异（含 I7 列，仅供记录）。
- 两份末行均为 `DIFFS=<n> GDB_DIVERGENT=<m>`。
### 6.2 逐行判定（脚本 `verdict_m1c_r8m1c3.py`）
- 对 F3 的 236 行（G5 177、G6 25、G6c 18、CTRL_AUX 16）：
  - 两遍都满足"事实相等、env 相等、point_verdict 与各适用不变量相等"→ MATCH；
  - pass1 与 pass2 不一致 → FLAKY；
  - 运行器因 GDB_DIVERGENT 中断、未跑到 → NOT_RUN；
  - 其他 → MISMATCH，并写出差异字段。
- F2 的 236 行按 r8m1c2 的比较结果填入（均 MATCH，来源列写 `COMPARE_M1C_F2_R8_M1c2.tsv`）。
- 输出 `VERDICT_M1C_R8_M1c3.tsv`（472 行）与 `VERDICT_M1C_R8_M1c3_AGG.tsv`（按组×树统计 MATCH、MISMATCH、FLAKY、NOT_RUN、GDB_DIVERGENT）。
- MISMATCH 行同时列出：冻结期望、F3 实测、R8 F2 实测；**不得通过改期望消除 MISMATCH**；对原因只能写 [源码]/未验证。
### 6.3 阳性对照（脚本 `posctrl_m1c_r8m1c3.py`，按 U220 口径）
- 在 `$EV/tmp/posctrl/` 中用 shutil 复制 F3 结果两份：
  - 副本 A 改动一个 point 行的 `gdb_rc2` → 比较脚本须给出 DIFFS>0，且该 point_id 出现在 DIFF 行中；
  - 副本 B 不改 → DIFFS=0。
  - 两项的确切计数如实记录。
- 另做一项判定器阳性对照：把一份冻结期望副本中某一行的 `exp_rc1` 改掉，`verdict_m1c_r8m1c3.py` 对该行须给出 MISMATCH。
- 结果写入 `POSCTRL_M1C_R8_M1c3.txt`，以 `POSCTRL=PASS` 或 `POSCTRL=FAIL` 结尾；FAIL 按 ⑧ 处理。

## 7. M1 总表（脚本 `summarize_m1_r8m1c3.py`，输出 `M1_SUMMARY_R8_M1c3.tsv`）
- M1b：830 行，取 `EFFECTIVE_M1B_R8_M1b3.tsv` 的 `effective_verdict` 与 `effective_class_p1`，按组×树×类别计数；单列 U212 中的 6 行 SILENT_SWALLOW（ADD22-A-7/8/9，属 U100，已转 S5）与 14 行 CRASH（ADD22 的 F2 行，修复前的基线，不是修复证据）。
- M1c：472 行，取 `VERDICT_M1C_R8_M1c3.tsv`，按组×树计数。
- 合计：MATCH、NOT_REACHED_AS_EXPECTED、NOT_RUN、MISMATCH、FLAKY。
- 另写 `check_report_counts_r8m1c3.py`：报告写完后，从报告中抽取 §7 和 §6 的全部数字，与总表、AGG 重新核对，输出 `REPORT_COUNT_CHECK_R8_M1c3.txt`（`ALL_MATCH` 或列出不一致项）。
- 806、415、RP-S3R4-1：脚本列出 M1b/M1c 中覆盖这三项的行（按 R8 M1a 的 ADDITIONS 映射与 SITEMAP），写入 `FIX_COVERAGE_M1_R8_M1c3.tsv`。未覆盖的标 `NOT_COVERED_IN_M1 → M2`，不得声称已验证。

## 8. 措辞
- F2 结果是回归基线，不是修复证据；F3 MATCH 只表示"在该注入下，F3 的事实与不变量等于冻结期望"。
- HOLD 只表示"在该注入（失败层为层 1，G6 有 2 点为层 0）下，各适用不变量成立"。REPORTED_FAILURE 只表示"该注入下返回码非零"。
- 不写"已修好""已验证"。I7、双目标注入、其他层失败变体、阶段 e、K-1、NB=1–8、类别 C、fmmret 干净对照、RP-R6d-7 仍为 DEFERRED 或未覆盖，归 M2。报告须写明这一局限。

## 9. 收尾（完成或停止都要做）
1. **提交后记录脚本先写好**：`postcommit_r8m1c3.py`（输出 `$EV/POSTCOMMIT_R8_M1c3.txt`，U17 拒绝覆盖），在提交前写好并通过 §1.3 检查，随本轮提交（U222）。
2. `copy_registries_r8m1c3.py`：复制到 `checkpoints/p05/registries/s4r8/M1c/r8m1c3/`，写 `SHA256SUMS.txt`，逐个比对 sha256 与原件一致（先确认全部输入存在再建目录）。
   - 要复制：PREFLIGHT、RUNNER_DIFF、DRIVER_RUN_RECORD、两份 COMPARE/DIFF、VERDICT 与 AGG、POSCTRL、M1_SUMMARY、FIX_COVERAGE、REPORT_COUNT_CHECK、GATE_DIFF、start 门禁文件；
   - F3 的 `STATE_R6c_pass{1,2}.tsv`、`STATE_SEAM_R6c_pass{1,2}.tsv`、`RESULTS_R6c_STATE.tsv`、`RESULTS_R6c_SEAM.tsv`、两个 SUMMARY，复制时加 `M1C_F3_` 前缀；
   - gdb 日志与 dump 不复制；end 门禁文件在 end 门禁后单独追加复制，并更新清单（同 r8m1c2 的做法）。
3. `sums_ev_r8m1c3.py`：在 `$EV/` 写 `SHA256SUMS.txt`，覆盖全部非二进制证据。
4. 用 edit 工具更新 STATE.md，必须 ≤ 8192 字节（现为 7917；字节数用本轮脚本经 safe_run 确认）：
   - 开工基线改为 `3661416`；当前轮次改为 r8m1c3；
   - 关键数字表中，"S4R8 M1c1–M1c2"一行改为"S4R8 M1c（r8m1c1–c3）"，写 F2 DIFFS=0 与 F3 判定计数；新增一行写 M1 总表合计；
   - 开放问题中，"M1c 环境"一行改为 M1c 结果；"806、415、RP-S3R4-1"一行写 M1 覆盖情况与转 M2 的部分；
   - 证据位置只保留最近三轮。
5. 用 write 工具写报告 `checkpoints/p05/P05_S4R8_M1C3_REPORT.md`，须包含：
   - 开工门禁；U218–U222；E8-81、E8-82；
   - 预检；F3 运行；两份比较；逐行判定与 AGG；阳性对照；M1 总表；修复覆盖表；
   - "运行前检查"与"内联命令自查"两节；违规表一、表二；根目录临时区开工与收尾快照；
   - 局限（§8）；
   - 结尾写"本轮未完成/已完成 R8 M1c3 范围，等待用户审核"。
   - 写完后运行 `check_report_counts_r8m1c3.py`。结果不是 ALL_MATCH 时，用 edit 修正报告后重跑（输出用 `_R2` 后缀），两次结果都要保留。
6. 跑 end 门禁（FAILS=0），再用 `commit_r8m1c3.sh` 经 safe_run 提交（脚本内先核对 status）。提交信息：
   `P05-S4 R8 M1c3 (r8m1c3): U218-U222, E8-81/E8-82, M1c F3 run vs frozen (MATCH=<a> MISMATCH=<b> FLAKY=<c> NOT_RUN=<d>), F2-F3 diff, posctrl, M1 summary; awaiting user review`
   如果在停止条件处停下，提交信息改为说明停在哪一步，同样以 `awaiting user review` 结尾。
7. 提交后经 safe_run 运行 `postcommit_r8m1c3.py`，并在最终回复中原文给出它的输出。此后不再新建任何文件；`git status --short` 应为空。

## 10. 最终回复（简短中文）
列出：
- U218–U222、E8-81、E8-82 是否已登记；
- F3 的 MATCH、MISMATCH、FLAKY、NOT_RUN、GDB_DIVERGENT（按组）；
- F2↔F3 差异数及其概要；
- 阳性对照结果（确切计数）；
- M1 总表合计（M1b、M1c 分列，单列 6 行 SILENT 与 14 行 CRASH）；
- 806/415/RP-S3R4-1 的 M1 覆盖情况；
- 违规表；
- 提交后的 `git log -1` 与 `git status --short`；
- 需要用户裁决的事项。

不得出现"签收""已修好""已验证"等字样（否定用法也避免）。
