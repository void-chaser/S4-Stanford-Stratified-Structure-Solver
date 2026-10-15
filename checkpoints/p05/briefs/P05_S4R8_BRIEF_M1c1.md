# P05-S4 R8 M1c1（r8m1c1）任务书：M1b 裁决登记 + M1c 事实期望冻结 + M1c 执行（F2 基线 → F3）

> 本轮是 P05-S4 的子轮次 R8 M1c1。不宣布任何阶段完成。先读 AGENTS.md 与 checkpoints/p05/STATE.md。
> 工作量不是停止理由。只有 §1.4 列出的情况可以停止；任何停下都必须先跑 end 门禁，再做记录提交（U158）。
> 第一步：把本任务书原文用 write 工具保存为 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c1.md`。

## 0. 开工基线（任一不符就停）
- HEAD = `9d8333364d57977bbeb00e1ce522924b2399fd51`（r8m1b3 报告修正提交，父提交 dcf6ee7）
- `git rev-parse HEAD:S4` = `6cff923a02baf19e01966b2339755cbf3a5deeef`（F3）
- 判定器 `testing/d003/judge_d003.py` 的 sha256 = `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`
- `checkpoints/p05/registries/s4r8/M1a/REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv` 的 sha256 = `e1e555ee4ca20421b6e5681e18be6cd1b873fc7cff06d246c01fad65d8d3a562`
- `git status --short`：开工时只允许出现本任务书文件（`?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c1.md`），以及本轮新建的 `testing/d003/stage_s4/*r8m1c1*`
- 本轮证据目录：`EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c1`；safe_run 的目录参数为 `p05-s4r8/m1c1`

## 1. 执行纪律
### 1.1 写入
- 所有写入都写成脚本，经 `sh testing/d003/safe_run.sh p05-s4r8/m1c1 -- <命令>` 运行。shell 脚本首行逐字为：
  `REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"`
- Python 一律用 `python3 -I -B`。Python 里的临时路径写成 `os.path.join(EV, "tmp", ...)`，源码里不得出现字面量 `/tmp`。
- 本轮不删除、不移动、不覆盖任何文件（U17）。产物作废时，原文件留在原处，新产物用 `_R2` 后缀命名，报告中标明哪份作废。
- 数据文件、ERRATA、报告正文里不写 `/tmp` 字面量，一律写"根目录临时区"。

### 1.2 内联命令白名单（只允许以下形式，不得含任何 `>` 字符，包括 `2>&1`）
- `git rev-parse HEAD`、`git rev-parse HEAD:S4`、`git status --short`、`git log -1 --format=%H%n%s`
- `sha256sum <仓库内文件>`
- 根目录临时区快照，逐字为：`date; ls -A /tmp | wc -l; ls -A /tmp | sha256sum; date`
- `sh testing/d003/safe_run.sh p05-s4r8/m1c1 -- <本轮脚本及参数>`
- 看文件用 read 工具，搜索用 grep 工具；带输出的核对一律写成脚本，经 safe_run 运行。

### 1.3 运行前检查
每个新脚本运行前，用 grep 工具按下面的正则查一遍，结果必须为 0 行才能运行（查的是未运行的草稿，查出后改正不算违规），并在报告的"运行前检查"一节逐条列出（脚本名、UTC、行数）：
```
(^|[^A-Za-z0-9_}])/tmp|/dev/null|<<-?\s*['"]?[A-Za-z_]+|sed\s+-i|python3\s+-c|cat\s+>|\btee\b|\brm\s|\bmv\s|[^&>]&\s*($|;)|git\s+(fsck|gc|prune|stash|checkout|switch|reset|clean)
```

### 1.4 停止条件（仅限以下各项）
① 写入目标在仓库外；② 写入没经 safe_run；③ 运行了检查未通过的脚本；④ 门禁不符；⑤ 需要改 `S4/` 或已提交的历史装置；⑥ §4 的冻结自检失败（R7 两遍不一致，或 env 不一致）；⑦ §5 的预检失败；⑧ 运行器报 GDB_DIVERGENT；⑨ §6 中 F2 基线与 R7 F2 有任一差异（这时不跑 F3）。
"缺少合格的 start 门禁文件"不是停止理由：没跑 start 门禁属于执行遗漏，须如实披露。

## 2. 门禁（第一步做，先跑 start，再做任何追加或运行）
- 新建 `testing/d003/stage_s4/gate_r8m1c1.sh`、`gate_check_r8m1c1.py`、`gate_allow_r8m1c1_start.txt`、`gate_allow_r8m1c1_end.txt`，复制自 `gate_r8m1b3.sh` 与 `gate_check_r8m1b3.py`。
  只改：基线 HEAD 改为 `9d8333364d57977bbeb00e1ce522924b2399fd51`；证据目录与参数改为 `p05-s4r8/m1c1`；输出名形式改为 `GATE_R8_M1c1_<X>.txt`；允许列表文件名改掉。原件不改。每份复制品与原件的 `diff -u` 写入 `$EV/GATE_DIFF_R8_M1c1.txt`。
- start 模式另外核对：
  - M1c 预注册的 sha256（§0）；
  - `registries/s4r8/M1b/r8m1b3/SHA256SUMS.txt` 逐项 `-c` OK（10 项）；
  - `registries/s4r8/SHA256SUMS.txt` 中活文件 ERRATA_8.txt 按前缀校验（MEMORY 教训 U121），其余项 `-c` OK；
  - 四个历史运行器与判定器的 sha256，与 HEAD 版本相同，且自 `d58bafd` 起没有改动：`testing/d003/stage_s4/{run_r6c_state.py,r6c2_seam_state.py,r6c_judge.py,r6c2_seam_judge.py,r6c_state.gdb,r6c_state_gdb.py}`；
  - 根目录临时区快照。
- end 模式：从 start 门禁文件读取开工时的快照值，不用位置参数传；不检查 HEAD^；status 只允许 end 列表里的项：
  - ` M`：`checkpoints/p05/STATE.md`、`registries/RULINGS.tsv`、`registries/s4r8/ERRATA_8.txt`
  - `??`：`checkpoints/p05/P05_S4R8_M1C1_REPORT.md`、`checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c1.md`、`checkpoints/p05/registries/s4r8/M1c/r8m1c1/*`、`testing/d003/stage_s4/*r8m1c1*`
- 两份门禁的 FAILS 都必须为 0。

## 3. 裁决与勘误登记（start 门禁通过之后做）
### 3.1 RULINGS.tsv 追加（5 列，status 写"生效"，来源写"P05-S4 R8 M1c1 任务书 §3"，前缀逐字节不变）
- **U209**：接受 r8m1b3（dcf6ee7、9d83333）的结果与全部披露。表一中那条越界重定向（被拒绝、未落盘）按执行偏离接受，不追认为合规。第一版补充预注册在运行前被删除，按运行前更正接受；今后作废的预注册或结果文件一律保留原文件，不得删除。
- **U210**：M1b1 中 44 行"期望 NOT_REACHED、实测 REPORTED_FAILURE"，与 U206 的 50 行同一根因：缺 `S4FMM_NTH`，驱动默认 nth=1，注入在第 1 次调用命中。判为环境假象，不进红点台账，不作为任何产品结论的依据。在正确环境下的结果以补跑（NOT_REACHED_AS_EXPECTED 44）为准。
- **U211**：口径。按审计口径，ENV_AGREE 488 行（含 G2c_control 6 行）；按有效来源口径，M1b1 执行 482 行加 NOT_RUN 6 行。两种都有效，报告须写明用的是哪一种。`INVALID_NOT_REACHED` 的字段值拼写接受，数字 22 不变。
- **U212**：M1b 的数据层面闭合：有效表 830 行 = MATCH 780 + NOT_REACHED_AS_EXPECTED 44 + NOT_RUN 6，MISMATCH 0，FLAKY 0。有效表中另有 6 行非对照 SILENT_SWALLOW（ADD22-A-7/8/9，F2/F3 各 3 行，U96 的设计边界，属 U100，已转 S5）和 14 行 CRASH（ADD22 的 F2 行，修复前的基线，不是修复证据），都是 MATCH，总结中必须写出。这不是 M1、R8 或 P05-S4 的签收。
- **U213**：M1c 预注册中 G5、G6 行的 `expected_rc1/expected_rc2/expected_run_rc/expected_hit` 是生成器写死的常数（`make_prereg_r8m1a6.py:683,690,727,734`），与 R7 F2 的事实不符，不作期望使用。M1c 的事实期望改取 R7 已提交的 `registries/s4r7/M3_F2_STATE_R6c_pass1/2.tsv` 和 `M3_F2_STATE_SEAM_R6c_pass1/2.tsv`（两遍一致才采用）。不变量期望取 `M3_F2_RESULTS_R6c_STATE.tsv` 与 `M3_F2_RESULTS_R6c_SEAM.tsv`（两遍一致才采用）。以上在任何 M1c 运行之前写入补充预注册，状态 INFLUENCED。原预注册不改。
- **U214**：M1c 的运行方法与 R7 M3 相同：用已提交、未修改的 `run_r6c_state.py`、`r6c2_seam_state.py`、`r6c_judge.py`、`r6c2_seam_judge.py`，输入是与 R7 相同的历史预注册（G5：`registries/s4r6c/REGISTRY_S4_PRE_R6b_STATE_v2.tsv` 与 `registries/s4r6b/REGISTRY_S4_PRE_R6b_CONTROL.tsv`；G6/G6c：`registries/s4r6c/REGISTRY_S4_PRE_R6c_SEAM.tsv` 与 `REGISTRY_S4_PRE_R6c_SEAM_CONTROL.tsv`），只换驱动路径。先跑 F2，与 R7 F2 逐点比较，0 差异才跑 F3（同 U81、U139(a)）。运行器输出的 `tree` 列是历史标签 `F`，不代表实际的树；实际的树以每次调用前后记录的驱动 sha256 为准。G5 运行器附带的 16 个控制点不在 440 行内，作为辅助对照 CTRL_AUX 单列比较。

### 3.2 ERRATA_8.txt 追加 E8-79（只追加，经前缀校验）
- (a) U210 的内容；
- (b) U211 的口径说明；
- (c) r8m1b3 报告 §6 的"非对照 SILENT_SWALLOW 0"只适用于补跑的 342 行；830 行有效表的完整构成见 U212；
- (d) 第一版补充预注册在运行前被删除（`safe_run.log` 13:37:30Z 的 `rm -f`），首版的 sha256 没有保留；按 U209 处理；
- (e) U213 的内容。须逐项写出 R7 F2 的实际事实分布：G5 有 132 点 rc1=20/rc2=0/hit=1、45 点 rc1=0/rc2=20/hit=1；G6 有 25 点 rc1=20/rc2=0/hit=1；控制点 G5 16 个、G6c 18 个，均为 rc1=0/rc2=0/hit=0。以上数字由脚本从表中重新计算并核对，不得照抄本任务书。

## 4. M1c 事实期望冻结（运行前）
- 新建 `make_prereg_m1c_facts_r8m1c1.py`，输出 `$EV/PREREG_M1C_FACTS_R8_M1c1.tsv` 和 `PREREG_M1C_FACTS_RECORD_R8_M1c1.txt`（记录 sha256、行数、来源文件及其 sha256、UTC）。
- 行集合：
  - M1c 预注册的 440 行，分组照原样：G5 177×2、G6 25×2、G6c 18×2；
  - 另加 CTRL_AUX 16×2 行，取自 `REGISTRY_S4_PRE_R6b_CONTROL.tsv` 的 control_id。
- 列：`row_kind, group, point_id_r8, base_id, tree, driver_name, driver_sha256, env_expected, exp_rc1, exp_rc2, exp_rc3, exp_hit, exp_point_verdict, exp_I1..exp_I6, fact_source, verdict_source, status`。
  - G6、G6c 没有 rc3，`exp_rc3` 写 `-`；控制点的 `exp_point_verdict` 和 `exp_I*` 写 `-`；
  - `env_expected` 取 R7 的 `env_as_run`，去掉 `S4FMM_DUMP*`；
  - `status` 写 INFLUENCED。
- 自检（任一失败按停止条件 ⑥ 处理）：
  - R7 两遍的 gdb_* 事实与 nogdb_* 事实逐列相等，pass1 与 pass2 相等；
  - 440 行的 `env_expected` 与 M1c 预注册的 `env` 逐键相等（与 `ENV_LOGCHECK_M1C_R8_M1b3.tsv` 的 440/440 AGREE 一致）；
  - `driver_sha256` 与 M1c 预注册相同；
  - 不变量两遍相同，且 point_verdict 全为 HOLD。
- 本脚本不得读取任何 R8 M1c 的运行产物（此时也还不存在）。

## 5. 预检脚本 `preflight_m1c_r8m1c1.py`（先于任何驱动运行）
输出 `$EV/PREFLIGHT_M1C_R8_M1c1.txt`，以 `PREFLIGHT_OK` 结尾才可继续。逐项核对：
- 六个驱动可执行，sha256 与 M1c 预注册相同：
  - F2：`evidence/p05-s4r7/drivers_r7/r6bstate-F2-dbg/driver`、`r6bseam-seamF-F2/driver`、`r6bseam-fmmret-F2/driver`
  - F3：`evidence/p05-s4r8/drivers_r8m1/r6bstate-F3-dbg/driver`、`r6bseam-seamF-F3/driver`、`r6bseam-fmmret-F3/driver`
- 四份历史预注册的 sha256 等于 `registries/s4r7/REGISTRY_S4_PRE_R7_M3.tsv` 表头记录的值；
- 运行器和判定器的 sha256 与 start 门禁一致；
- 补充预注册的 sha256 与冻结记录一致；
- `gdb --version` 的首行写入；
- 输出目录 `$EV/m1c_f2/` 和 `$EV/m1c_f3/` 不存在。

## 6. 运行（两棵树都按"G5 pass1 → G5 pass2 → seam pass1 → seam pass2 → 两个判定器"的顺序严格串行）
- 新建 `run_m1c_r8m1c1.sh <F2|F3>`。它按 R7 的 m3r1 命令形式（见 `evidence/p05-s4r7/safe_run.log` 第 430–434 行）调用四次运行器和两个判定器，标准输出写到 `$EV/m1c_<tree>/*.stdout`，并在每次运行器调用前后把三个驱动的 sha256 追加到 `$EV/DRIVER_RUN_RECORD_R8_M1c1.tsv`。不用 `&`。超时自然等待，不重复启动。
- 先跑 F2，再跑 `compare_m1c_r8m1c1.py F2`。逐点比较 R8 F2 与 R7 F2：facts、env_as_run、不变量、point_verdict、两遍一致性，CTRL_AUX 与 G6c 控制点比较原始事实。另外数 GDB_DIVERGENT 行。
  输出 `COMPARE_M1C_F2_R8_M1c1.tsv`。有任何差异，按停止条件 ⑨ 处理：不跑 F3，直接收尾。
- F2 为 0 差异时，跑 F3，再跑 `compare_m1c_r8m1c1.py F3`。逐点与 §4 的冻结期望比较，同时与 R8 F2 比较。
  输出 `COMPARE_M1C_F3_R8_M1c1.tsv` 和 `F2_F3_DIFF_M1C_R8_M1c1.tsv`。F3 的差异只记为 MISMATCH，不停止。
- 逐行判定（440 行加 CTRL_AUX 32 行）：
  - 两遍都满足"事实相等、env 相等、point_verdict 与各适用不变量相等"，记 MATCH；
  - 两遍不一致，记 FLAKY；
  - 其他情况记 MISMATCH；
  - 因 GDB_DIVERGENT 而没跑到的行记 NOT_RUN。
- 汇总：`VERDICT_M1C_R8_M1c1.tsv` 与 `VERDICT_M1C_R8_M1c1_AGG.tsv`，按组×树统计 MATCH、MISMATCH、FLAKY、NOT_RUN、GDB_DIVERGENT。
- 阳性对照（同 R7 §3.4）：在 `$EV/tmp/` 的副本上改动一个 `gdb_rc2`，比较脚本必须检出；未改动的副本差异为 0。结果写入 `POSCTRL_M1C_R8_M1c1.txt`。

## 7. M1 总表
新建 `summarize_m1_r8m1c1.py`，输出 `M1_SUMMARY_R8_M1c1.tsv`：
- M1b：830 行，取 `EFFECTIVE_M1B_R8_M1b3.tsv` 的 effective_class 与 verdict，按组×树×类别计数，并单列 U212 中的 6 行 SILENT_SWALLOW 和 14 行 CRASH；
- M1c：440 行，加 CTRL_AUX；
- 合计：MATCH、NRAE、NOT_RUN、MISMATCH、FLAKY。
数字由脚本从表中重新计算，报告里的数字用脚本核对（同 R7 的 `check_report_counts`）。

## 8. 措辞规则
- HOLD 只表示"在该注入（失败层为层 1，G6 有 2 点为层 0）下，各适用不变量成立"，不写"已修好""已验证"。REPORTED_FAILURE 只表示"该注入下返回码非零"。
- I7、双目标注入、其他层失败变体、阶段 e、K-1 仍为 DEFERRED 或未覆盖，归 M2。报告必须写出这一局限。
- F2 上的结果是 F3 的回归基线，不是修复证据。

## 9. 收尾（无论是完成还是停止，都要做）
1. 把小表复制到 `checkpoints/p05/registries/s4r8/M1c/r8m1c1/`，写 `SHA256SUMS.txt`，逐个比对 sha256 与原件一致。要复制的小表：补充预注册与 RECORD、PREFLIGHT、DRIVER_RUN_RECORD、两份 COMPARE、F2_F3_DIFF、VERDICT 与 AGG、POSCTRL、M1_SUMMARY、GATE_DIFF、两份门禁文件，以及两棵树各自的 `STATE_R6c_pass{1,2}.tsv`、`STATE_SEAM_R6c_pass{1,2}.tsv`、`RESULTS_R6c_STATE.tsv`、`RESULTS_R6c_SEAM.tsv`、两个 SUMMARY（改名时加 `M1C_F2_`、`M1C_F3_` 前缀）。gdb 日志和 dump 不复制。
2. 在 `$EV/` 写 `SHA256SUMS.txt`，覆盖全部非二进制证据。
3. 更新 STATE.md，必须保持在 8192 字节以内：
   - 关键数字表中，"S4R8 M1b 首轮""M1b2""M1b3"三行合并为一行"S4R8 M1b（r8m1b1–b3）"，新增一行 r8m1c1；
   - 开放问题表中，"M1b env 审计与补充补跑""50 行 SILENT_SWALLOW 假象"两行合并为"M1b 已数据闭合（U212）"，"M1c 环境"一行改为本轮结果；
   - 更新开工基线、当前轮次、证据位置。
4. 报告写在 `checkpoints/p05/P05_S4R8_M1C1_REPORT.md`，须包含：
   - 开工门禁；裁决 U209–U214；E8-79；
   - 冻结自检、预检、F2 比较、F3 比较、阳性对照、M1 总表；
   - "运行前检查"一节、"内联命令自查"一节（逐条列出 UTC 与原文）；
   - 违规表一、表二，以及根目录临时区的开工与收尾快照。
   报告结尾写"本轮未完成/已完成 R8 M1c1 范围，等待用户审核"，附提交后的 `git log -1` 与 `git status --short`。
5. 跑 end 门禁（FAILS=0）后，用脚本提交。提交信息为：
   `P05-S4 R8 M1c1 (r8m1c1): U209-U214, E8-79, M1c facts prereg, M1c F2 baseline + F3 run, M1 summary; awaiting user review`
   如果在停止条件处停下，把信息改为说明停在哪一步，同样以 `awaiting user review` 结尾。

## 10. 最终回复给用户
用简短中文列出：裁决与勘误是否已登记；冻结表的 sha256；F2 比较的差异数；F3 的 MATCH、MISMATCH、FLAKY 计数；GDB_DIVERGENT 数；M1 总表合计；违规表；需要用户裁决的事项。不得出现"签收""已修好"等字样。
