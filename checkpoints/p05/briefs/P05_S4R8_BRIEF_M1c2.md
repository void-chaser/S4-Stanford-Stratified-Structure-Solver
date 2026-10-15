# P05-S4 R8 M1c2（r8m1c2）任务书：裁决与勘误登记 + M1c 事实期望冻结 + F2 基线运行与比较

> 本轮是 P05-S4 的子轮次 R8 M1c2。不宣布任何阶段完成。先读 AGENTS.md 与 checkpoints/p05/STATE.md。
> 本轮范围只到 F2 基线比较与阳性对照，**不跑 F3**（F3 在 m1c3）。
> 工作量不是停止理由。只有 §1.5 列出的情况可以停止；任何停下都必须先跑 end 门禁，再做记录提交（U158）。
> 第一步：用 **write 工具**把本任务书原文保存为 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c2.md`。

## 0. 开工基线（任一不符就停）
- HEAD = `f913b57a487f4ae64ff6f9d1d48136e99ae65e77`（r8m1c1 停止记录提交）
- `git rev-parse HEAD:S4` = `6cff923a02baf19e01966b2339755cbf3a5deeef`（F3）
- 判定器 `testing/d003/judge_d003.py` sha256 = `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`
- `checkpoints/p05/registries/s4r8/M1a/REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv` sha256 = `e1e555ee4ca20421b6e5681e18be6cd1b873fc7cff06d246c01fad65d8d3a562`
- 开工时 `git status --short` 只允许：`?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c2.md`，以及本轮新建的 `?? testing/d003/stage_s4/*r8m1c2*`
- 证据目录 `EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c2`；safe_run 的目录参数为 `p05-s4r8/m1c2`
- `testing/d003/stage_s4/*r8m1c1*` 已提交，冻结，不修改，也不再运行。

## 1. 执行纪律（r8m1c1 因违反此节停止，务必逐条遵守）
### 1.1 写文件只有两条途径，此外一律禁止
**途径 A：write/edit 工具**，只能用于以下文件：
- 本任务书副本；
- 本轮新建的脚本与允许列表（`testing/d003/stage_s4/*r8m1c2*`）；
- 本轮报告 `checkpoints/p05/P05_S4R8_M1C2_REPORT.md`；
- `checkpoints/p05/STATE.md`。

**途径 B：经 `sh testing/d003/safe_run.sh p05-s4r8/m1c2 -- <本轮脚本及参数>` 运行的脚本。** 下列写入只能走途径 B：
- 所有证据产物；
- `RULINGS.tsv` 与 `ERRATA_8.txt` 的追加（追加脚本做前缀校验）；
- registries 复制；
- 提交。

**以下做法一律禁止：**
- 在 bash 中直接写任何文件。heredoc、`cat >`、`echo >`、`printf >`、`tee`、`cp`、`mkdir` 全部算在内，目标在仓库内也一样。r8m1c1 就是因此停止的。
- `safe_run.sh -- sh -c "<内联写入>"` 这种形式。safe_run 后面只能接本轮的脚本文件。

脚本的其他要求：
- shell 脚本首行逐字为：
  `REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"`
- Python 一律用 `python3 -I -B`。临时路径写成 `os.path.join(EV, "tmp", ...)`。
- 不删除、不移动、不覆盖任何文件（U17）。产物作废时用 `_R2` 后缀新建，并在报告中标明。
- 源码、数据、ERRATA、报告正文中不写 `/tmp` 字面量，一律写“根目录临时区”。只有 §1.2 的快照命令例外。

### 1.2 内联命令白名单（不得含任何 `>` 字符，包括 `2>&1`）
- `git rev-parse HEAD`、`git rev-parse HEAD:S4`、`git status --short`、`git log -1 --format=%H%n%s`
- `sha256sum <仓库内文件>`
- `date -u +%FT%TZ`
- 根目录临时区快照，逐字为：`date; ls -A /tmp | wc -l; ls -A /tmp | sha256sum; date`
- `sh testing/d003/safe_run.sh p05-s4r8/m1c2 -- <本轮脚本及参数>`
- 看文件用 read 工具，搜索用 grep 工具。

### 1.3 运行前检查（每个新脚本运行前都要做，包括门禁脚本）
顺序固定为：用 write 写好脚本 → 跑 `date -u +%FT%TZ` → 用 grep 工具按下面的正则查该脚本 → 结果为 0 行才可运行。查出问题后改正、重新查，不算违规。报告中逐条列出：脚本名、UTC、行数。
```
(^|[^A-Za-z0-9_}])/tmp|/dev/null|<<-?\s*['"]?[A-Za-z_]+|sed\s+-i|python3\s+-c|cat\s+>|\btee\b|\brm\s|\bmv\s|[^&>]&\s*($|;)|git\s+(fsck|gc|prune|stash|checkout|switch|reset|clean)
```
跳过此检查就运行脚本属于执行遗漏，须披露，但不是停止理由。运行了检查**未通过**的脚本，按停止条件 ③ 处理。

### 1.4 内联命令自查
报告“内联命令自查”一节逐条列出本轮执行过的全部内联命令（UTC 与原文）。

### 1.5 停止条件（仅限以下各项）
① 写入目标在仓库外；② 写入没走 §1.1 的两条途径；③ 运行了检查未通过的脚本；④ 门禁不符；⑤ 需要改 `S4/` 或已提交的历史装置；⑥ §4 冻结自检失败；⑦ §5 预检失败；⑧ 运行器报 GDB_DIVERGENT；⑨ §6 中 R8 F2 与 R7 F2 有任一差异。
- “缺少合格的 start 门禁”不是停止理由。
- 停止后仍要做 §8 收尾。

## 2. 门禁（第一步做：先跑 start，再做任何追加或运行）
- 用 read 读 `testing/d003/stage_s4/gate_r8m1c1.sh`、`gate_check_r8m1c1.py`、`gate_allow_r8m1c1_start.txt`、`gate_allow_r8m1c1_end.txt`，再用 **write 工具**新建对应的 `*_r8m1c2*` 四个文件。只改以下几处：
  - 基线 HEAD 改为 `f913b57a487f4ae64ff6f9d1d48136e99ae65e77`；
  - 证据目录与参数改为 `p05-s4r8/m1c2`；
  - 输出名形式改为 `GATE_R8_M1c2_<X>.txt`；
  - 自引用的脚本名与允许列表名改为 m1c2；
  - 允许列表内容按下文。
- 新建 `diff_gate_r8m1c2.sh`：把四对文件的 `diff -u` 写入 `$EV/GATE_DIFF_R8_M1c2.txt`（diff 返回 1 属正常）。经 §1.3 检查后经 safe_run 运行。
- start 允许列表：`?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c2.md` 与 `?? testing/d003/stage_s4/*r8m1c2*`。
- start 模式核对：
  - 沿用 r8m1c1 的全部检查项：M1c 预注册 sha256；`registries/s4r8/M1b/r8m1b3/SHA256SUMS.txt` 10 项；`registries/s4r8/SHA256SUMS.txt` 中 ERRATA_8 做前缀校验（13990 字节，`72dc6aed…`），其余项 `-c`；六个历史运行器、判定器与 gdb 文件自 `d58bafd` 起未改动；根目录临时区快照。
  - 另加：`ERRATA_8.txt` 为 62127 字节、sha256 `ee7c5e2d…dfdba`（与 r8m1c1 门禁记录一致）；`RULINGS.tsv` 为 79849 字节、sha256 `d7262cf7…6bdc7`。这两个值作为本轮追加时的前缀基准。
- end 模式：开工快照值和两个前缀基准都从 start 门禁文件读取；不检查 HEAD^。status 只允许以下各项：
  - ` M`：`checkpoints/p05/STATE.md`、`checkpoints/p05/registries/RULINGS.tsv`、`checkpoints/p05/registries/s4r8/ERRATA_8.txt`
  - `??`：`checkpoints/p05/P05_S4R8_M1C2_REPORT.md`、`checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c2.md`、`checkpoints/p05/registries/s4r8/M1c/r8m1c2/*`、`testing/d003/stage_s4/*r8m1c2*`
- end 模式另外核对：`RULINGS.tsv` 与 `ERRATA_8.txt` 的开工部分作为前缀逐字节不变。
- 两份门禁的 FAILS 都必须为 0。

## 3. 裁决与勘误登记（start 门禁通过后做）
### 3.1 RULINGS.tsv 追加（脚本 `append_rulings_r8m1c2.sh`，5 列，status“生效”，来源“P05-S4 R8 M1c2 任务书 §3”，前缀校验）
- **U209–U214**：逐字取自 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c1.md` §3.1。追加脚本从该文件读出原文并核对，不得改写；来源列写“P05-S4 R8 M1c1 任务书 §3（于 r8m1c2 登记）”。
- **U215**：接受 r8m1c1（`f913b57`）停在开工门禁。三次 bash heredoc 写入（两份允许列表、`gate_check_r8m1c1.py`、报告）未经 safe_run，按执行偏离接受，不追认为合规；文件内容经规划者事后核查无禁止项，保留原样。r8m1c1 的门禁文件和 `*r8m1c1*` 脚本冻结、不再运行。M1c 在 r8m1c2 重新开始。
- **U216**：写入途径澄清（自本轮起适用）。新建脚本、允许列表、报告、STATE.md、任务书副本可以用 write/edit 工具；证据产物、RULINGS/ERRATA 追加、registries 复制、提交只能经 safe_run 运行的本轮脚本。bash 中直接写文件（含 heredoc）和 `safe_run -- sh -c "<内联写入>"` 一律禁止。§1.3 检查适用于包括门禁在内的每个新脚本，须在运行前做。
- **U217**：M1c 分两轮。r8m1c2 做 U209–U214 登记、事实期望冻结、预检、F2 基线运行、F2 比较、阳性对照；F3 运行与比较、逐行判定、M1 总表放到 r8m1c3。U214“F2 0 差异才跑 F3”保持不变。

### 3.2 ERRATA_8.txt 追加（脚本 `append_errata_r8m1c2.sh`，只追加，前缀校验）
- **E8-79**：(a)–(e) 逐项照 `P05_S4R8_BRIEF_M1c1.md` §3.2。其中 (e) 的分布数字由 `count_r7_f2_facts_r8m1c2.py` 从 R7 已提交的表中重新计算，再填入。脚本输出 `$EV/R7_F2_FACT_DIST_R8_M1c2.tsv`；与任务书数字不一致时以表为准，并写明差异。
- **E8-80**：r8m1c1 报告的三处瑕疵，原报告不改：
  - §1 写“两次违规”，表二实列三次；
  - 表二第 2 行说 `gate_check_r8m1c1.py` 由 heredoc 写入，第 4 行说由 write 工具生成，二者矛盾，以 safe_run.log 无对应记录、报告自述 heredoc 为准；
  - 报告缺提交后的 `git log -1` 与 `git status --short`；r8m1c2 开工时核实 HEAD = `f913b57`、status 为空，以此补记。

## 4. M1c 事实期望冻结（运行前；脚本 `make_prereg_m1c_facts_r8m1c2.py`）
- 输出 `$EV/PREREG_M1C_FACTS_R8_M1c2.tsv` 与 `PREREG_M1C_FACTS_RECORD_R8_M1c2.txt`（记录 sha256、行数、来源文件及其 sha256、UTC）。
- 行集合：
  - M1c 预注册的 440 行，分组照原样：G5 177×2、G6 25×2、G6c 18×2；
  - CTRL_AUX 16×2 行，control_id 取自 `registries/s4r6b/REGISTRY_S4_PRE_R6b_CONTROL.tsv`。
  - 合计 472 行，F2、F3 两棵树都冻结。
- 列：`row_kind, group, point_id_r8, base_id, tree, driver_name, driver_sha256, env_expected, exp_rc1, exp_rc2, exp_rc3, exp_hit, exp_point_verdict, exp_I1..exp_I6, fact_source, verdict_source, status`。
  - G6、G6c 的 `exp_rc3` 写 `-`；
  - 控制点的 `exp_point_verdict` 与 `exp_I*` 写 `-`；
  - `env_expected` 取 R7 的 `env_as_run`，去掉 `S4FMM_DUMP*`；
  - `status` 写 INFLUENCED。
- 事实来源：`registries/s4r7/M3_F2_STATE_R6c_pass1/2.tsv`、`M3_F2_STATE_SEAM_R6c_pass1/2.tsv`。不变量来源：`M3_F2_RESULTS_R6c_STATE.tsv`、`M3_F2_RESULTS_R6c_SEAM.tsv`。两遍一致才采用。
- 自检（任一失败按 ⑥ 处理）：
  - gdb_* 与 nogdb_* 事实逐列相等；
  - pass1 与 pass2 相等；
  - 440 行的 env 与 M1c 预注册逐键相等（与 `ENV_LOGCHECK_M1C_R8_M1b3.tsv` 的 440/440 AGREE 一致）；
  - driver_sha256 与 M1c 预注册相同；
  - 不变量两遍相同，point_verdict 全为 HOLD。
- 本脚本不读任何 R8 M1c 运行产物。

## 5. 预检（脚本 `preflight_m1c_r8m1c2.py`，先于任何驱动运行）
- 输出 `$EV/PREFLIGHT_M1C_R8_M1c2.txt`，以 `PREFLIGHT_OK` 结尾才可继续。
- 核对 F2、F3 共六个驱动可执行，sha256 与 M1c 预注册相同：
  - F2：`evidence/p05-s4r7/drivers_r7/{r6bstate-F2-dbg,r6bseam-seamF-F2,r6bseam-fmmret-F2}/driver`
  - F3：`evidence/p05-s4r8/drivers_r8m1/{r6bstate-F3-dbg,r6bseam-seamF-F3,r6bseam-fmmret-F3}/driver`
- 四份历史预注册的 sha256 等于 `registries/s4r7/REGISTRY_S4_PRE_R7_M3.tsv` 表头记录的值。
- 运行器与判定器的 sha256 与 start 门禁一致。
- 冻结表的 sha256 与 RECORD 一致。
- `gdb --version` 首行写入输出。
- `$EV/m1c_f2/` 与 `$EV/m1c_f3/` 都不存在。

## 6. F2 基线运行与比较
- 脚本 `run_m1c_r8m1c2.sh <F2|F3>`。本轮只用 F2 调用；参数设计成可用于 F3，供 r8m1c3 复用，本轮不跑 F3。
  - 按 R7 m3r1 的命令形式（`evidence/p05-s4r7/safe_run.log` 第 430–434 行）串行调用：G5 pass1 → G5 pass2 → `r6c_judge.py` → seam pass1 → seam pass2 → `r6c2_seam_judge.py`。
  - 输出目录 `$EV/m1c_f2/`，stdout 写入 `*.stdout`。
  - 每次运行器调用前后，把三个驱动的 sha256 追加到 `$EV/DRIVER_RUN_RECORD_R8_M1c2.tsv`。
  - 不用 `&`；超时自然等待，不重复启动。
- 脚本 `compare_m1c_f2_r8m1c2.py <R8目录> <输出名>`：逐点比较 R8 F2 与 R7 F2。
  - 比较项：facts、env_as_run、不变量、point_verdict、两遍一致性；CTRL_AUX 与 G6c 控制点比较原始事实。
  - 另外统计 GDB_DIVERGENT 行。
  - 输出 `$EV/COMPARE_M1C_F2_R8_M1c2.tsv`，末行为 `DIFFS=<n> GDB_DIVERGENT=<m>`。
  - n≠0 时按 ⑨ 处理：记录差异，直接收尾。
- 阳性对照（脚本 `posctrl_m1c_r8m1c2.py`）：在 `$EV/tmp/posctrl/` 中用 shutil 复制 R8 F2 结果两份。一份改动一个 `gdb_rc2`，比较脚本必须检出 DIFFS=1；另一份不改，结果必须为 DIFFS=0。结果写入 `$EV/POSCTRL_M1C_R8_M1c2.txt`。

## 7. 措辞
- F2 结果是 F3 的回归基线，不是修复证据。
- HOLD 只表示“在该注入（失败层为层 1，G6 有 2 点为层 0）下，各适用不变量成立”。
- I7、双目标注入、其他层失败变体、阶段 e、K-1 仍为 DEFERRED 或未覆盖，归 M2。报告须写出这一局限。

## 8. 收尾（完成或停止都要做）
1. 脚本 `copy_registries_r8m1c2.sh`：把小表复制到 `checkpoints/p05/registries/s4r8/M1c/r8m1c2/`，写 `SHA256SUMS.txt`，逐个比对 sha256 与原件一致。
   - 要复制：冻结表与 RECORD、R7_F2_FACT_DIST、PREFLIGHT、DRIVER_RUN_RECORD、COMPARE_F2、POSCTRL、GATE_DIFF、两份门禁文件。
   - F2 的 `STATE_R6c_pass{1,2}.tsv`、`STATE_SEAM_R6c_pass{1,2}.tsv`、`RESULTS_R6c_STATE.tsv`、`RESULTS_R6c_SEAM.tsv`、两个 SUMMARY，复制时加 `M1C_F2_` 前缀。
   - gdb 日志与 dump 不复制。
2. 脚本 `sums_ev_r8m1c2.sh`：在 `$EV/` 写 `SHA256SUMS.txt`，覆盖全部非二进制证据。
3. 用 edit 工具更新 STATE.md，必须 ≤ 8192 字节（现为 8190）。
   - 关键数字表中，“S4R8 M1b 首轮”“M1b2”“M1b3”三行合并为“S4R8 M1b（r8m1b1–b3）”；新增一行，写 r8m1c1 与 r8m1c2。
   - 开放问题表中，“M1b env 审计与补充补跑”与“50 行 SILENT_SWALLOW 假象”合并为“M1b 已数据闭合（U212）”；“M1c 环境”一行改为“F2 基线结果；F3 待 r8m1c3”。
   - 删除第 58 行“此行已被上两行取代”的占位行，历史已在 STATE_HISTORY 中。
   - 更新开工基线、当前轮次、证据位置。
   - 用 `sha256sum` 之外的方式确认字节数时，写成脚本经 safe_run 运行。
4. 用 write 工具写报告 `checkpoints/p05/P05_S4R8_M1C2_REPORT.md`，须包含：
   - 开工门禁；U209–U217；E8-79、E8-80；
   - 冻结自检；预检；F2 比较（DIFFS、GDB_DIVERGENT）；阳性对照；
   - “运行前检查”与“内联命令自查”两节；
   - 违规表一、表二；根目录临时区开工与收尾快照；
   - 结尾写“本轮未完成/已完成 R8 M1c2 范围，等待用户审核”。
   - 提交后的 `git log -1` 与 `git status --short` 不写进报告，见第 6 步。
5. 跑 end 门禁（FAILS=0），再用 `commit_r8m1c2.sh` 经 safe_run 提交。提交前在脚本内核对 status。提交信息：
   `P05-S4 R8 M1c2 (r8m1c2): U209-U217, E8-79/E8-80, M1c facts prereg, M1c F2 baseline vs R7 (DIFFS=<n>), posctrl; F3 deferred to r8m1c3; awaiting user review`
   如果在停止条件处停下，提交信息改为说明停在哪一步，同样以 `awaiting user review` 结尾。
6. 提交后，用脚本 `postcommit_r8m1c2.sh` 经 safe_run，把 `git log -1` 与 `git status --short` 写入 `$EV/POSTCOMMIT_R8_M1c2.txt`（证据不提交），并在最终回复中原文给出。

## 9. 最终回复（简短中文）
列出以下各项：
- U209–U217、E8-79、E8-80 是否已登记；
- 冻结表的 sha256 与行数（应为 472）；
- R7 F2 事实分布的重算结果；
- F2 比较的 DIFFS 与 GDB_DIVERGENT；
- 阳性对照结果；
- 违规表；
- 提交后的 `git log -1` 与 `git status --short`；
- 需要用户裁决的事项。

不得出现“签收”“已修好”等字样。
