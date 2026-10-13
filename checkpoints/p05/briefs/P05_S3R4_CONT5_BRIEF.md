# P05-S3 R4 续5(S3R4 的续轮,不是新阶段):收尾。只做记录、只读核对与提交,不编译、不运行 S4 驱动

你是 P05-S3 的收尾执行者。本轮记为 S3R4 续5,不得出现 P05-S6。不得宣布任何阶段完成或签收;报告与 STATE 不写签收建议(U83)。
**本轮不修改 S4/ 下任何文件,不编译、不链接、不运行任何 S4 驱动或 gdb。**自检不是修复后验证;修复后验证由 P05-S4 R8 在 F3 上完成。

先读(按顺序):AGENTS.md、checkpoints/p05/STATE.md、checkpoints/p05/P05_S3R4_CLOSEOUT_CONT4.md、
checkpoints/p05/briefs/P05_S3R4_CONT4_BRIEF.md、checkpoints/p05/P05_S3R4_CLOSEOUT_CONT3.md、
checkpoints/p05/ERRATA_S3R4.txt(ES3R4-15…24)、checkpoints/p05/registries/s3r4c3/(只读)、
testing/d003/stage_s4r7/run_m2b_all_r7.py(只读,重点 :103–150、:280–300)。

- 证据目录:checkpoints/p05/evidence/p05-s3r4c5/(新目录)。p05-s3r4/、p05-s3r4c2/、p05-s3r4c3/、p05-s4r7/ 只读引用,不往里写。
  (续4 没有创建 p05-s3r4c4/,本轮也不创建。)
- 新脚本目录:testing/d003/stage_s3r4c5/(文件名带 c5)。小型结果表:checkpoints/p05/registries/s3r4c5/。
- 报告:checkpoints/p05/P05_S3R4_CLOSEOUT_CONT5.md。勘误在 ERRATA_S3R4.txt 末尾追加,从 ES3R4-25 起编号,不改已有条目。
第一步:用 write 把本任务书原文存为 checkpoints/p05/briefs/P05_S3R4_CONT5_BRIEF.md。

## 0. 门禁与写入方式

### 0.1 开工门禁(任一不符就停下报告)
- HEAD = bee9420;`git rev-parse HEAD:S4` = 6cff923a02baf19e01966b2339755cbf3a5deeef(F3)。
- judge_d003.py sha256 = d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb(用内联 `sha256sum testing/d003/judge_d003.py` 只读取数,再由 gate_c5.sh 写入门禁文件)。
- `git status --short` 只允许以下 5 行(本任务书存档是第 6 行,属于预期):
  `?? checkpoints/p05/P05_S3R4_CLOSEOUT_CONT3.md`、`?? checkpoints/p05/P05_S3R4_CLOSEOUT_CONT4.md`、
  `?? checkpoints/p05/briefs/P05_S3R4_CONT4_BRIEF.md`、`?? checkpoints/p05/registries/s3r4c3/`、`?? testing/d003/stage_s3r4c3/`。
- /tmp 顶层只读快照:内联 `ls -A /tmp | wc -l` 与 `ls -A /tmp | sha256sum` 取数,作为参数传给 gate_c5.sh,
  写入 $EV/GATE_CONT5.txt(开工)与 $EV/GATE_CONT5_END.txt(收尾)。

### 0.2 写入方式(按 U116)
- 仓库内的文本文件(报告、ERRATA、RULINGS、STATE、tsv、脚本)只用 write 或 edit 工具写。
- **内联 bash 只用于只读命令**(git status/log/rev-parse/show --stat、ls、ls -d、test -e、sha256sum、wc、head、tail、grep、diff 不带输出文件),
  以及 `sh testing/d003/safe_run.sh p05-s3r4c5 -- sh testing/d003/stage_s3r4c5/<名字>_c5.sh [参数]`。
  内联命令尽量不写 `>`;只读命令中的 `2>&1`、`>&2` 没有写入目标,不算写入,如出现只记入表二,不停。
- 所有写入(sha256 清单、diff 输出、复制、门禁、git add/commit)都先用 write 写成 testing/d003/stage_s3r4c5/<名字>_c5.sh,再经 safe_run 运行。
  git commit 写进脚本(参照 testing/d003/stage_s3r4c3/commit_rec_c3.sh)。
- shell 脚本第一段必须**逐字**是:
  `REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"`
- 脚本与命令文本中一律不得出现:`/dev/null`(含 DEVNULL、devnull)、`&` 后台启动、heredoc、`sed -i`、`python3 -c`、`cat >`、`tee`,
  以及任何以 / 开头又不在 $REPO 下的写入目标(包括 /tmp 与任何占位路径)。
- **运行前检查**(每个脚本、每次修改后):用 grep 工具在 testing/d003/stage_s3r4c5/ 中搜索正则
  `/dev/null|DEVNULL|devnull|<<-?\s*['"]?[A-Za-z_]|sed -i|python3 -c|cat >|tee |(^|[^V])/tmp`,结果必须 0 行才可运行;
  结论(脚本名、UTC、命中 0)经 prerun_log_c5.sh 写入 $EV/PRERUN_CHECKS_C5.txt。未运行的草稿被查出并改正,不算违规。
- 写入目标只能在 $EV/、testing/d003/stage_s3r4c5/、checkpoints/p05/ 下。不改 testing/d003/ 下已提交的文件,不改 stage_s3r4c3/。
- 不做拒绝性测试或沙箱探测。长输出带 head/tail。禁止写 .git 或改工作区的 git 命令。

### 0.3 停止条件(按 U116,只认真实写入)
停止当且仅当执行了以下之一:① 写入目标在仓库外(含 /tmp);② 写入没经 safe_run(写入指有目标文件的 `>`/`>>`、tee、cp、mv、mkdir、touch、
git archive、sed -i、会生成文件的程序);③ 运行了运行前检查未通过的脚本。另外:门禁不符;需要修改 S4/、已提交的历史装置或 stage_s3r4c3/。
其他文本瑕疵(只读命令含 `2>&1` 等)记入表二,继续执行。

## 1. 用户裁决(先追加到 RULINGS.tsv,status `生效`,来源写本任务书 §1;再在 ERRATA 中 ES3R4-25 之前写裁决块)
- U111–U115:原文见 checkpoints/p05/briefs/P05_S3R4_CONT4_BRIEF.md §1,照录。
- U116:续4 的停止依任务书是正确的,两条只读 `2>&1` 命令接受为已披露(未落盘,无仓库外写入);它们不构成真实写入,
  停止的根因是续4 §0.2 规则过严(规划者疏漏)。续5 起停止条件按本任务书 §0.3。续4 的只读核对结论(ES3R4-25、26(a)–(d)、27)有效。
- U117:续4 未提交的 P05_S3R4_CLOSEOUT_CONT4.md 与 briefs/P05_S3R4_CONT4_BRIEF.md **原样提交,不修改**。
- U118:CTRL_SEAM fmmret 驱动问题登记为 ES3R4-29。R7 M2b run5–run7 的 `CTRL-SEAM-fmmret-F`、`CTRL-SEAM-fmmret-F2` 记为
  "驱动选取与登记不符:实际为 seamF-<tree>([源码],run_m2b_all_r7.py:124–131;本轮离线解析见 §3)"。原结果表、原报告不改。
  这两行不作为 fmmret plain 库的控制证据;R7 中 fmmret 库的干净对照以 M3 G6 的 SC01–SC10(r6bseam-fmmret-F/F2,dbg)为准。
  G2a 中 request 以 `fmmret:` 开头的注入行走 fmmret 驱动,不受影响。
- U119:REGISTRY_S3R4C3_D.tsv 不改。R8 第 0 步中 `CTRL-SEAM-fmmret-F` 按登记意图使用 fmmret-F 的 plain seam 驱动;期望 CONTROL_OK 仍为 INFLUENCED,
  依据改为 R4 CONTROL_R4 与 R7 M3 SC03-fmmret-F-fft(source 列的 run7 引用由 ES3R4-29 更正)。R8 的运行器必须按登记表的 driver 列选驱动,
  并在运行前断言"登记 driver 名 = 实际驱动名",不一致就拒绝运行。
- U120:续4 缺的交付物由续5 以只读计算补齐,写入 p05-s3r4c5/(不写回 p05-s3r4c3/)。U98–U115 继续有效(U98 按 U113 修改)。

## 2. 记录提交(先做,一个提交)
- RULINGS.tsv 追加 U111–U120。
- ERRATA 追加 U111–U120 裁决块,以及以下条目(每条先用 read/grep 核对文件:行号,再写进去):
  · ES3R4-25:续4 任务书 §3.2(续3 任务书原文)的 n=12 → 36 = 4×3×3(S4/pattern/pattern.c:418;U112)。
  · ES3R4-26:更正 D_STATUS_C3.txt 与续3 报告 §3.3 的 D 说明(原文件不改),逐条写 (a)–(d),内容按续4 任务书 §2 与续4 报告 §2.1。
    结论句:以上供 R8 第 0 步使用;续3 没有运行 D,这些更正不影响任何已有结果。
  · ES3R4-27:B_MAP_C3.tsv 的 polygon_breakpoint_hits 列实为窗口 malloc 次数(无 -g),只能读作"窗口 malloc 次数(替代)",不是断点证据。
  · ES3R4-28:续3 报告 §10 "本报告未提交"由 U114 处理;续3 报告 §3.3 关于 D 的原因由 ES3R4-26 更正(原文不改)。
  · ES3R4-29:CTRL_SEAM fmmret 驱动选取与登记不符(U118)。写明:登记表(registries/s4r7/REGISTRY_S4_PRE_R7_M2_CTRL_SEAM.tsv 第 7、8 行)
    driver 列;run_m2b_all_r7.py:112–116、:124–131、:147、:288 的行为;该文件自 359bf65 起未改(用 `git log --oneline -- <文件>` 核对);
    结果表不记录驱动路径;影响范围按 U118;D 点 source 列的更正按 U119。§3 的离线解析结果在最终提交时补一句引用(edit 追加,不改前文)。
  · ES3R4-30:续4 停止记录(U116;两条只读 `2>&1`,未落盘;续4 未建任何目录)。
- 提交脚本 commit_rec_c5.sh:先把 `git status --short` 写进 $EV/status_before_rec_c5.txt;git add 只列出:
  RULINGS.tsv、ERRATA_S3R4.txt、briefs/P05_S3R4_CONT4_BRIEF.md、briefs/P05_S3R4_CONT5_BRIEF.md、P05_S3R4_CLOSEOUT_CONT3.md、
  P05_S3R4_CLOSEOUT_CONT4.md、registries/s3r4c3/、testing/d003/stage_s3r4c3/。不用 `git add -A` 或 `git add .`。
  提交信息(先 write 到 $EV/COMMIT_MSG_CONT5_REC.txt):
  `P05-S3R4 CONT5 rulings U111-U120, errata ES3R4-25..30; CONT3/CONT4 reports, registries s3r4c3 and stage_s3r4c3 committed unchanged (apply_seam_f3_c3.sh DO NOT RUN). awaiting user review`

## 3. 只读补齐与离线核实(输出到 $EV = p05-s3r4c5)
### 3.1 续3 交付物(脚本 supp_c5.sh;每个输出已存在就拒绝;diff 的 rc=1 表示有差异,不是失败,rc 写在文件末尾)
- DIFF_INJECT_C3.txt:`diff -u testing/d003/stage_s3r4/inject_s3r4_init.cpp testing/d003/stage_s3r4c3/inject_s3r4c3_poly.cpp`
- DIFF_LINK_C3.txt:`diff -u testing/d003/stage_s3r4/link_init_s3r4.sh testing/d003/stage_s3r4c3/link_poly_inj_c3.sh`
- PREREG_D_RECORD_C3.txt:evidence/p05-s3r4c3/REGISTRY_S3R4C3_D.tsv 的 sha256(应为 a251a3b8…a9d5)、行数、`stat -c %y`
  (注明"文件修改时间,不是登记记录;续3 未写登记记录")。
- BINARIES_C3.tsv(name、path、sha256、compare):与续3 任务书 §0.1 的已知值比对写 SAME/DIFFERENT:
  F2 plain 库 evidence/p05-s3r4/build/F2-plain/build/libS4.a = c63d180a…c185;F3 plain 库 build_f3/plain/build/libS4.a = abbc01c7…5de;
  init-F2 驱动 = 29bb377c…1158;init-F3 驱动 = ff66cfc1…0b68(完整值见续3 任务书 §0.1)。
  F3 dbg 库(build_f3/dbg/build/libS4.a)、polyinj-F2、polyinj-F3 驱动(p05-s3r4c3/drivers/)写 FIRST_RECORD。
- SHA256SUMS_P05-S3R4C3.txt:p05-s3r4c3/ 下全部非二进制证据文件的标准格式清单(哈希 两个空格 相对 p05-s3r4c3 的路径)。
  排除 safe_run.log、tmp/、f3_export/、drivers/*/driver,排除项列在 SHA256SUMS_P05-S3R4C3_EXCLUDED.txt。
  随后在脚本中 cd 到 p05-s3r4c3 运行 `sha256sum -c`,结果写进 $EV/SHA256SUMS_P05-S3R4C3_CHECK.txt。
- 用 read 检查两个 diff:DIFF_INJECT 应只有窗口符号、跨调用累计、计数查询函数、打印格式的差异;DIFF_LINK 应只有标准首段、wrap 符号、
  输入输出路径的差异。摘要写入报告 §3;有其他差异如实列出,不改任何文件。

### 3.2 CTRL_SEAM 驱动的离线解析(新增;不运行任何驱动)
- 先用 read 查看 run_m2b_all_r7.py、run_m2_r7.py、expected_env_independent_r7.py、compare_trees_r7.py、matrix_r2.py、judge_d003.py
  的模块顶层代码(import 时会执行的部分),确认 import 时不写文件、不启动进程。若任一模块顶层有写入或启动进程,
  本节标"不可行(依据:文件:行)",只保留 ES3R4-29 的 [源码] 结论。
- 若可行:写 testing/d003/stage_s3r4c5/resolve_ctrl_seam_c5.py,用 `python3 -I -B` 运行(不生成 __pycache__)。脚本只把 stage_s4r7 加入 sys.path,
  import run_m2b_all_r7,调用其 ctrl_seam_points(EV_R7)、load_seam_drivers(EV_R7)、driver_for("CTRL_SEAM", request, tree, rec={}, seam)
  (EV_R7 = checkpoints/p05/evidence/p05-s4r7),对 4 行输出 point_id、登记 driver 列、解析出的驱动名、驱动路径、记录的 sha256、AGREE/DISAGREE。
  不调用 run、check_driver 之外的任何函数,不运行驱动。只输出到 stdout,由 resolve_ctrl_seam_c5.sh 写入 $EV/CTRL_SEAM_DRIVER_RESOLUTION_C5.tsv。
- 同时用 grep 工具在 evidence/p05-s4r7/safe_run.log 中查 run7 调用 run_m2b_all_r7.py 的记录行(只读),把行号与 UTC 写进报告。
- 期望(写在运行前的 $EV/EXPECT_RESOLUTION_C5.txt,经脚本写入,并记录 sha256):seamF 两行 AGREE;fmmret 两行 DISAGREE(解析为 seamF-F、seamF-F2)。
  结果不符时如实记录,不改期望,列入报告"待用户裁决"。

## 4. 收尾
- STATE.md(用 edit,保持一页以内):
  · 当前轮次:"P05-S3 子轮次 S3R4 续5(收尾):A 36/36 MATCH、B 44/44 MATCH(F3 REPORTED_FAILURE rc1=20);D 按 U113 转入 R8 第 0 步;
    ES3R4-29:R7 CTRL_SEAM fmmret 两行实为 seamF 驱动(U118);下一步 P05-S4 R8 在 F3 上"。开工基线 HEAD 写 bee9420。
  · S3R4 关键数字行补:A 36/36、对照 6/6;B 44/44、对照 12/12;Mfirst(fft NG1 = 1,其余 = 64);窗口 malloc n = 36。
  · 开放问题表:"S3R4 自检 A 注入运行、B、D"改为"D 冒烟 8 点 → R8 第 0 步(U113;更正见 ES3R4-26;驱动规则 U119)";
    "806、415、RP-S3R4-1"改为"注入自检通过(F3,A/B);修复后验证 → R8";"−1…−9"改为"[源码] 说明已写(registries/s3r4c3/U100_SOURCE_NOTE.md)";
    新增一行"R7 M2b CTRL_SEAM fmmret 两行驱动与登记不符(ES3R4-29)· 记录更正 · R8 补 fmmret plain 干净对照"。不新增重复行。
  · 证据位置补 p05-s3r4c3、p05-s3r4c5 与对应 registries 目录。
- 小型表复制到 registries/s3r4c5/(copy_registries_c5.sh):GATE_CONT5*.txt、PRERUN_CHECKS_C5.txt、DIFF_*_C3.txt、PREREG_D_RECORD_C3.txt、
  BINARIES_C3.tsv、SHA256SUMS_P05-S3R4C3*.txt、EXPECT_RESOLUTION_C5.txt、CTRL_SEAM_DRIVER_RESOLUTION_C5.tsv、status_before_rec_c5.txt。
  写 SHA256SUMS.txt(标准格式),在该目录内 `sha256sum -c`,结果写进 $EV。
- $EV/SHA256SUMS.txt 覆盖 p05-s3r4c5 全部非二进制文件;safe_run.log 不进清单,说明文件写"清单后追加,不参与校验"。
- 报告 P05_S3R4_CLOSEOUT_CONT5.md:门禁;记录提交哈希;U111–U120;ES3R4-25…30 要点;§3.1 补齐结果与 diff 摘要;BINARIES 比对;
  §3.2 解析结果(或不可行依据);STATE 变更摘要;违规两张表(没有写"无");待用户裁决(没有写"无")。
  每项只写"完成""未完成(原因)""不可行(依据)"之一。结尾只写"本轮已完成 S3R4 续5 范围,等待用户审核"或"本轮未完成 S3R4 续5 范围,等待用户审核",
  提交后真实的 `git log -3 --oneline` 与 `git status --short` 写进 $EV/FINAL_GIT_C5.txt,报告引用该文件,并在对话中贴出。
- 最终提交(commit_final_c5.sh):STATE.md、ERRATA(ES3R4-29 的补充引用)、P05_S3R4_CLOSEOUT_CONT5.md、registries/s3r4c5/、testing/d003/stage_s3r4c5/。提交信息:
  `P05-S3R4 CONT5 closeout: CONT3 deliverables completed read-only, CTRL_SEAM fmmret driver mismatch recorded (ES3R4-29) and resolved offline, D moved to R8 step 0 (U113, U119), STATE updated. awaiting user review`
  提交后 `git status --short` 应为空;不为空在对话中说明。

## 5. 不停但要记录的情形
- BINARIES 出现 DIFFERENT、SHA256SUMS_P05-S3R4C3 校验不全 OK、§3.2 结果与期望不符:如实记录,列入"待用户裁决"。
- "未完成"与"不可行"必须区分。
