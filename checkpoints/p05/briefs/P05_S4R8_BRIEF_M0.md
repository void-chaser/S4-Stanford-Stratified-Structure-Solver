# P05-S4 R8 M0(P05-S4 的子轮次 R8,第一个里程碑):F3 构建、第 0 步 D 冒烟、F2↔F3 无注入等价

你是 P05-S4 的验证执行者。本轮记为 P05-S4 R8 的 M0,不是新阶段,不得出现 P05-S6。不得宣布任何阶段完成或签收;报告与 STATE 不写签收建议(U83)。
**不修改 S4/ 下任何文件。** 本轮只在 F3(8d8202a)的 git archive 导出物上构建和运行。报告写"冒烟""等价",不写"已修好""已验证"。

先读(按顺序):AGENTS.md、checkpoints/p05/STATE.md、checkpoints/p05/P05_S3R4_CLOSEOUT_CONT5.md、checkpoints/p05/ERRATA_S3R4.txt(ES3R4-25…30,重点 26、29)、
checkpoints/p05/registries/s3r4c3/REGISTRY_S3R4C3_D.tsv、checkpoints/p05/registries/s4r7/REGISTRY_S4_PRE_R7_M2_CTRL_SEAM.tsv、
checkpoints/p05/P05_S4R7_REPORT_FINAL.md(§构建与驱动)、testing/d003/stage_s4r7/ 下的 build_s4r7.sh、build_seam_plain_s4r7.sh、link_drivers_s4r7.sh、
link_seam_drivers_r7.sh、run_noinject_equiv_r7.sh、run_m2b_all_r7.py(:103–190)、run_m2_r7.py(:90–130)。以上全部只读。

- 证据目录:checkpoints/p05/evidence/p05-s4r8/(新)。p05-s4r7/、p05-s3r4*/ 只读引用,不往里写。
- 新脚本目录:testing/d003/stage_s4r8/(文件名带 _r8)。小型结果表:checkpoints/p05/registries/s4r8/。
- 报告:checkpoints/p05/P05_S4R8_REPORT_M0.md。勘误:checkpoints/p05/registries/s4r8/ERRATA_8.txt(从 E8-1 编号)。
- 第一步:用 write 把本任务书原文存为 checkpoints/p05/briefs/P05_S4R8_BRIEF_M0.md。

## 0. 门禁与写入方式

### 0.1 开工门禁(任一不符就停下报告)
- HEAD = 3ab56801e697910bdff9fbe6056807c2e41841b5;`git rev-parse HEAD:S4` = 6cff923a02baf19e01966b2339755cbf3a5deeef(F3);
  `git rev-parse 8d8202a:S4` 等于同一值;`git rev-parse a07b5ac:S4` = e124925f5b242486a913b813fa181664f665b048(F2)。
- `git diff --name-only a07b5ac 8d8202a -- S4/` 只列出 4 个文件:S4/S4.cpp、S4/fmm/fmm_FFT.cpp、S4/fmm/fmm_kottke.cpp、S4/pattern/pattern.c。
- judge_d003.py sha256 = d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb。
- `git status --short` 只有本任务书存档这一行。
- registries/s3r4c5/SHA256SUMS.txt、registries/s4r7/SHA256SUMS*.txt 在各自目录内 `sha256sum -c` 全部 OK(写在门禁脚本里)。
- REGISTRY_S3R4C3_D.tsv sha256 = a251a3b856f7772a09ce587918125f3b91d525cacc16db238e6787312353a9d5。
- /tmp 顶层只读快照:先用内联 `ls -A /tmp | wc -l` 与 `ls -A /tmp | sha256sum` 取数,再作为参数传给 gate_r8.sh,
  写入 $EV/GATE_R8_M0.txt(开工)与 $EV/GATE_R8_M0_END.txt(收尾)。

### 0.2 写入方式(沿用续5 §0.2,U127)
- 仓库内的文本文件(报告、ERRATA、RULINGS、STATE、tsv、脚本、py)只用 write 或 edit 工具写。
- 内联 bash 只用于只读命令(git status/log/rev-parse/show/diff --name-only、ls、ls -d、test -e、sha256sum、wc、head、tail、grep、diff 不带输出文件),
  以及 `sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/<名字>_r8.sh [参数]`。
- 所有写入(导出、构建、链接、运行、sha256 清单、复制、门禁、git add/commit)都先用 write 写成 testing/d003/stage_s4r8/<名字>_r8.sh(或 _r8.py),再经 safe_run 运行。
  Python 一律用 `python3 -I -B`。提交写在脚本里(参照 testing/d003/stage_s3r4c5/commit_rec_c5.sh)。
- shell 脚本第一段必须**逐字**是:
  `REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"`
- 脚本与命令文本中一律不得出现:`/dev/null`(含 DEVNULL、devnull)、`&` 后台启动、heredoc、`sed -i`、`python3 -c`、`cat >`、`tee`、`rm -rf`,
  以及任何以 / 开头又不在 $REPO 下的写入目标。临时文件只用 "$EV/tmp/…"(不要写成 "$X/tmp" 之类的其他前缀)。
- 历史脚本的复制品:R7 脚本第一行是 `REPO=$(git rev-parse --show-toplevel 2>/dev/null) || …`,复制品**必须**把它换成上面的标准首段;
  历史脚本里的 `> /dev/null` 一律改成重定向到 $EV/ 下带名字的日志文件;`rm -rf "$1" && mkdir -p "$1"` 改为 `test ! -e "$1" && mkdir -p "$1"`(已存在就拒绝,U17)。
  这三类改动以及树标签、提交号、库或驱动路径、输出目录、sha256 常量属于预期改动;每份复制品与原件的 `diff -u` 写入 $EV/RUNNER_DIFF_R8_M0.txt,
  出现其他改动就在 ERRATA_8 中逐条说明理由。
- **运行前检查**(每个脚本,每次修改后):用 grep 工具在 testing/d003/stage_s4r8/ 中搜索正则
  `/dev/null|DEVNULL|devnull|<<-?\s*['"]?[A-Za-z_]|sed -i|python3 -c|cat >|tee |rm -rf|(^|[^V])/tmp`,结果必须 0 行才能运行;
  结论(脚本名、UTC、命中 0)经 prerun_log_r8.sh 写入 $EV/PRERUN_CHECKS_R8_M0.txt。未运行的草稿被查出并改正,不算违规。
- 写入目标只能在 $EV/、testing/d003/stage_s4r8/、checkpoints/p05/ 下。不改 testing/d003/ 下任何已提交的文件。
- 不做拒绝性测试或沙箱探测。长输出带 head/tail。禁止 fsck/gc/prune/stash/checkout/switch/reset/clean。
- 复制或建目录的脚本必须**先确认全部输入存在**,再建目标目录(续5 的教训,U121)。
- 构建可能耗时较长,工具超时后会转为后台作业:等它结束,不要重复启动同一脚本。

### 0.3 停止条件(只认真实写入,同续5 §0.3)
停止当且仅当发生以下任一情况:① 写入目标在仓库外(含 /tmp);② 写入没经 safe_run;③ 运行了运行前检查未通过的脚本;
④ 门禁不符;⑤ 需要修改 S4/ 或已提交的历史装置。其他文本瑕疵(只读命令含 `2>&1` 等)记入表二,继续执行。
结果类停止见 §3、§4。

## 1. 用户裁决(先追加到 RULINGS.tsv,status `生效`,来源写本任务书 §1;同时写在 ERRATA_8.txt 开头)
- U121:接受续5 结果。copy_registries_c5.sh 留下的半个目录经 cleanup_reg_c5.sh(cmp 核对后 rm 一个文件 + rmdir)清理,接受为已披露(表二)。
  续5 的补齐与解析脚本在记录提交之前运行,与任务书 §2"先做"的顺序不同,结果有效;ES3R4-29 的离线解析引用随记录提交写入,内容属实。
  以上记为 ES3R4-31(追加到 ERRATA_S3R4.txt 末尾,不改已有条目)。今后复制脚本必须先确认全部输入存在再建目录。
- U122:S3R4 的执行范围到续5 为止。P05-S3 未签收;806、415、RP-S3R4-1 的修复后验证在 R8 中完成。
- U123:R8 在 F3(8d8202a,S4 树 6cff923a…)上运行,分四个里程碑,每个里程碑结束后停下,等用户审核:
  M0(本任务书)= 构建、第 0 步 D 冒烟、F2↔F3 无注入等价;
  M1 = R7 全部组在 F3 上回归,加上 S3R4 的 22 行新增点(registries/s3r4c3/R8_ADDITIONS_S3R4C3.tsv)与多边形等价;
  M2 = 补测项(阶段 e、I7、双目标注入、其他层失败变体、K-1 张量路径、NB=1–8、类别 C、fmmret plain 干净对照、RP-R6d-7);
  M3 = 阶段收口(F3 上 make test 相对基线、Python/Lua 端到端,只做一次)。
- U124:D 的驱动规则(补充 U119;REGISTRY_S3R4C3_D.tsv 没有 driver 列)。每点的"登记驱动族"如下:
  CTRL_SEAM 行取 REGISTRY_S4_PRE_R7_M2_CTRL_SEAM.tsv 中同 point_id 的 driver 列(fmmret-F → 族 fmmret;seamF-F2 → 族 seamF);
  G2a 行按 ES3R4-26(c):request 以 `fmmret:` 开头为 fmmret,否则为 seamF;G1 → d003(plain);G2c → d003plan(plain)。
  实际驱动 = 该族的 F3 plain 驱动。运行前写 $EV/DRIVER_MAP_R8_D.tsv(point_id、登记 tree、登记驱动族、实际驱动名、实际路径、驱动 sha256),
  记录其 sha256 与 UTC;运行器对每点断言"登记驱动族 = 实际驱动族,且实际树 = F3",不一致就拒绝运行。
- U125:D 的期望 = REGISTRY_S3R4C3_D.tsv 中的 expected_class 与 expected_rc1,原样使用(tree 列是 R7 的树标签,8 点全部在 F3 上运行),
  状态 INFLUENCED。CTRL-SEAM-fmmret-F 的期望依据按 U119 / ES3R4-29。跑两遍。
- U126:F2↔F3 等价对照的 F2 侧直接复用 R7 已链接的 F2 plain 驱动(p05-s4r7/drivers_r7/,只读,运行前核对 sha256 与 R7 记录一致;
  没有记录的写 FIRST_RECORD 并记入 E8),不重新链接。F3 侧驱动从本轮构建的 F3 库重新链接。
- U127:R8 的写入方式与停止条件沿用续5 §0.2、§0.3(见本任务书 §0),另加 §0.2 的复制品规则与"先确认输入再建目录"规则。

## 2. 记录提交(先做,一个提交;本节完成前不运行任何构建)
- RULINGS.tsv 追加 U121–U127;ERRATA_S3R4.txt 末尾追加 ES3R4-31(按 U121,写之前先用 grep 核对 safe_run.log 中的时间顺序,写出行号);
  新建 registries/s4r8/ERRATA_8.txt,开头写 U121–U127。
- commit_rec_r8.sh:先把 `git status --short` 写入 $EV/status_before_rec_r8.txt;git add 只列出:RULINGS.tsv、ERRATA_S3R4.txt、
  registries/s4r8/ERRATA_8.txt、briefs/P05_S4R8_BRIEF_M0.md、testing/d003/stage_s4r8/ 中已有的门禁脚本和提交脚本。不用 `git add -A` 或 `git add .`。
  提交信息(先 write 到 $EV/COMMIT_MSG_R8_M0_REC.txt):
  `P05-S4 R8 M0 records: rulings U121-U127, errata ES3R4-31 and ERRATA_8 header; brief archived. awaiting user review`

## 3. 构建与驱动(R8-0)
3.1 导出:export_r8.sh 用 `git archive 8d8202a | tar -x -C "$EV/trees/F3"` 导出(目标已存在就拒绝)。
    逐文件 sha256 写入 $EV/TREE_MANIFEST_R8.tsv,并核对 S4/ 下文件与 `git ls-tree -r 8d8202a S4` 的 blob 一一对应(另写 TREE_CHECK_R8.txt)。
3.2 F3 库:build_s4r8.sh 复制自 build_s4r7.sh(按 §0.2),只构建 F3 的 dbg(-O0 -g)与 plain(-O3 -march=native)两个模式,输出到 $EV/build_r8/F3-{dbg,plain}/。
    记录 make rc、告警数(期望 dbg 62、plain 71)、库 sha256;与 S3R4 的已知值比较(plain abbc01c7…05de,dbg 10ea03b3…;完整值从 registries/s3r4c5/BINARIES_C3.tsv 读取),
    写 SAME/DIFFERENT 到 $EV/BUILD_R8.tsv。DIFFERENT 只记录,不停止;告警数与 62/71 不同就停下。
    同时确认实际编译命令行中没有 -DHAVE_LIBCHOLMOD。
3.3 F3 seam 树(只做 plain;dbg seam 留到 M1):seam_r8.sh 以 R7 的做法为模板(p05-s4r7/safe_run.log 第 10–15 行,只读引用):
    - seamF-F3:导出 8d8202a → apply_seam_r2.py --families A,C,D → apply_seam_b2.py(**不得漏掉 B2**,见 ES3R4-26(b));
    - fmmret-F3:导出 8d8202a → apply_seam_r5_fmmret.py --tree A。
    每个 apply 的 --report 写到 $EV/seam_r8/,stdout 与 stderr 写到 $EV/seam_r8/*.log。testing/d003/stage_s3r4c3/apply_seam_f3_c3.sh 是 DO NOT RUN,不得使用或参照其步骤。
    seam 差异核对:对 F3 与 seamF-F3、fmmret-F3 分别做 `diff -ru`,再去掉 `diff -ru`、`+++`、`---` 行,并把 `@@ … @@` 行号统一替换成 `@@`
    (F3 在 S4.cpp、fmm_FFT.cpp、fmm_kottke.cpp 中有行号偏移);与 R7 的 p05-s4r7/seam_r7/seamdiff_F2_{seamF,fmmret}.diff 做同样的规范化后比较。
    写入 $EV/SEAM_DIFF_F2_vs_F3_R8.txt:每个变体只写 IDENTICAL 或 DIFFERS(附差异前 40 行)。DIFFERS 就停下报告,不构建 seam 库。
    然后 build_seam_plain_r8.sh(复制自 build_seam_plain_s4r7.sh)只构建 seamF-F3-plain 与 fmmret-F3-plain,宏与 R7 相同,记录告警数与 sha256。
3.4 驱动(link_drivers_r8.sh,复制自 link_drivers_s4r7.sh 与 link_seam_drivers_r7.sh,只改库路径、树标签与输出目录;输出 $EV/drivers_r8/):
    d003-F3-plain、d003plan-F3-plain、r6bstate-F3-plain、seam-seamF-F3、seam-fmmret-F3;tri-F3-plain 的链接命令
    从 p05-s4r7/safe_run.log 中只读查出 R7 链接 tri-F2-plain 的命令,照搬到 F3(找不到就把 tri 记为"未完成(原因)",其余照做)。
    在 $EV/DRIVERS_R8.tsv 记录 驱动名、树、模式、库 sha256、驱动 sha256、链接脚本。
    F2 侧(U126):r6bstate-F2-plain、tri-F2-plain 在 p05-s4r7/drivers_r7/ 中,核对 sha256 后写入 $EV/DRIVERS_R8_F2_REUSED.tsv(SAME / FIRST_RECORD)。

## 4. 第 0 步:D 冒烟 8 点(U113、U119、U124、U125)
- 先写 DRIVER_MAP_R8_D.tsv(按 U124),记录 sha256 与 UTC;同时写 $EV/EXPECT_R8_D.txt(8 行:point_id、期望类别、期望 rc1,逐字照抄登记表),记录 sha256。
- 运行器 run_d_r8.py(新文件):
  · 只 import 以下函数,并且只读 p05-s4r7 的登记表:run_m2b_all_r7 的 g_points、point_env、ctrl_seam_points、verdict_of;
    run_m2_r7 的 run、facts、clean_env、GRID、real_of、sha256_file;judge_d003 的 classify。
    **不调用** run_group、driver_for、dry_run、seam_driver_name,也不使用 run_m2_r7 的 DRIVERS 路径。驱动只来自 DRIVER_MAP_R8_D.tsv。
  · 环境:CTRL_SEAM 只设 FMM_MODE 与 S4FMM_NG(同 R7);G1、G2c、G2a 用 point_env(即 matrix_r2.build_env)。运行前用
    expected_env_independent_r7.expected_env_from_history 逐键核对环境,不一致就拒绝运行。
  · 判定:control 行用 classify(…, control=True, real=True, inj_call=1);其他行同 R7 M2b(real=real_of(group, point_id))。
    判定只看 rc、rc1、rc2、信号与命中数,不读驱动的 PASS/FAIL 行。
  · 两遍,输出 $EV/RESULTS_R8_D_pass{1,2}.tsv(已存在就拒绝)。列至少包括:point_id、group、登记 tree、实际 tree、驱动名、驱动 sha256、
    期望类别、类别、verdict、rc、rc1、rc2、hit、reason。另写 $EV/D_SUMMARY_R8.txt:MATCH/MISMATCH/FLAKY 计数。
- 任何 MISMATCH 或 FLAKY:两遍跑完后停下,不进入 §5,写报告等待裁决;不改期望,不重跑覆盖。

## 5. R8-1:F2↔F3 无注入等价
- run_noinject_equiv_r8.sh 复制自 run_noinject_equiv_r7.sh,把树标签 F/F2 改为 F2/F3,F2 用 U126 的复用驱动,F3 用 §3.4 的驱动。
  组合不变:closed、fft、kottke、experimental、tensor、closed1d、jones、nv、vl、fftjones、fftnv、fftvl × NG 1/5/9,加 tri 的 nv/vl/jones NG9。
- 期望(运行前写入 $EV/EXPECT_R8_NOINJECT.txt 并记录 sha256,状态 INFLUENCED):全部 IDENTICAL(call1–3 输出逐字节相同,两树 rc 相同);
  vl、fftvl NG1 两树都是 rc 20。依据:[源码] F2→F3 只改了失败路径(git diff a07b5ac 8d8202a -- S4/),正常返回值不变。
- 输出 $EV/RESULTS_R8_NOINJECT_run1.tsv。出现 NOT_IDENTICAL 或 rc 不同:如实记录,停下,等待裁决。
- 多边形等价(S3R4 C 的多边形组)不在本里程碑做,留到 M1。

## 6. 收尾(里程碑 M0)
- 小型表复制到 registries/s4r8/(copy_registries_r8.sh;先确认全部输入存在,再建目录):GATE_R8_M0*.txt、PRERUN_CHECKS_R8_M0.txt、
  TREE_CHECK_R8.txt、BUILD_R8.tsv、SEAM_DIFF_F2_vs_F3_R8.txt、DRIVERS_R8*.tsv、DRIVER_MAP_R8_D.tsv、EXPECT_R8_D.txt、RESULTS_R8_D_pass*.tsv、
  D_SUMMARY_R8.txt、EXPECT_R8_NOINJECT.txt、RESULTS_R8_NOINJECT_run1.tsv、RUNNER_DIFF_R8_M0.txt、status_before_rec_r8.txt、ERRATA_8.txt 的副本不需要(原件已在该目录)。
  写 SHA256SUMS.txt,在该目录内 `sha256sum -c`,逐个比对副本与原件一致,结果写入 $EV。
- $EV/SHA256SUMS.txt 覆盖 p05-s4r8 全部非二进制文件(排除 trees/、build_r8/、seam_r8/ 下的源码树与库、drivers_r8/*/driver、tmp/、safe_run.log,
  排除项列在 SHA256SUMS_EXCLUDED_R8_M0.txt);库与驱动只记录 sha256(在 BUILD_R8.tsv、DRIVERS_R8.tsv 中)。
- STATE.md(用 edit,保持一页以内):当前轮次改为"P05-S4 R8 M0(F3):D 冒烟 x/8 MATCH;F2↔F3 无注入等价 x/x IDENTICAL;下一步 R8 M1(待用户审核)";
  开工基线 HEAD 写 3ab5680;关键数字表新增 R8 一行;开放问题表中"D 冒烟 8 点"一行按实际结果更新;"R7 M2b CTRL_SEAM fmmret"一行写上 D 中 fmmret-F3 plain 控制点的结果
  (fmmret plain 干净对照的完整补测仍在 M2);证据位置补 p05-s4r8 与 registries/s4r8。
- 报告 P05_S4R8_REPORT_M0.md:门禁;记录提交哈希;U121–U127;构建与告警;seam 差异核对;驱动表;D 结果(逐点);等价结果(计数 + 非 IDENTICAL 清单);
  STATE 变更摘要;违规两张表(没有就写"无");待用户裁决(没有就写"无")。每项只写"完成""未完成(原因)""不可行(依据)"之一。
  结尾只写"本轮已完成 R8 M0 范围,等待用户审核"或"本轮未完成 R8 M0 范围,等待用户审核"。
- 最终提交(commit_final_r8_m0.sh):STATE.md、P05_S4R8_REPORT_M0.md、registries/s4r8/、testing/d003/stage_s4r8/。提交信息:
  `P05-S4 R8 M0 on F3: builds, seam plain, D smoke (step 0, U113/U119/U124), F2-F3 no-injection equivalence, STATE updated. awaiting user review`
  提交后把真实的 `git log -3 --oneline` 与 `git status --short` 写入 $EV/FINAL_GIT_R8_M0.txt,报告引用该文件,并在对话中贴出。status 应为空,不为空就说明原因。

## 7. 不停但要记录的情形
- 库 sha256 与 S3R4 已知值 DIFFERENT(告警数相同)、F2 驱动没有 sha 记录(FIRST_RECORD)、tri 链接命令找不到(tri 记"未完成")。
- "未完成"与"不可行"必须区分。M0 范围之外的事一律不做,即使看起来顺手。
