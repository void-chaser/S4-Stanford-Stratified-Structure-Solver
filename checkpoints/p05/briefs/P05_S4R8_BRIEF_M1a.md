# P05-S4 R8 M1a(P05-S4 子轮次 R8 的 M1 第一部分):准备轮——dbg 库差异查明、F3 构建与驱动补齐、F2→F3 注入点映射、预注册、dry-run

你是 P05-S4 的验证执行者。本轮是 P05-S4 R8 的 M1a,不是新阶段,不得出现 P05-S6。不得宣布任何阶段完成或签收;报告与 STATE 不写签收建议。
**不修改 S4/。不修改 testing/d003/ 下任何已提交文件**(包括 stage_s4r7/、stage_s4/、stage_s3r4*/、stage_s4r8/ 中已提交的脚本)。
**本轮不做任何注入运行。** 只允许 §5 的无注入映射运行(gdb 或计数),以及 §7 的 dry-run(只解析、不执行驱动)。

## 0. 开工
- 第一步:用 write 把本任务书原文存为 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a.md`。
- 先读(只读):AGENTS.md;STATE.md;`P05_S4R8_REPORT_M0.md`;`registries/s4r8/ERRATA_8.txt`;`briefs/P05_S4R8_BRIEF_M0_RESTART2.md`(§1 U132、§2);
  `briefs/P05_S4R8_BRIEF_M0_CLOSE.md`;`P05_S4R7_REPORT_FINAL.md`;`P05_S4R7_REPORT_M1.md`;`P05_S4R7_REPORT_M2_FINAL.md`;`registries/s4r7/ERRATA_7.txt`(E7-3、E7-8、E7-32…E7-37、E7-42、E7-44);
  `registries/s3r4c3/R8_ADDITIONS_S3R4C3.tsv`;`registries/s3r4c2/REGISTRY_S3R4C2_A.tsv`;`registries/s3r4c3/REGISTRY_S3R4C3_B.tsv`;`registries/s3r4c2/REGISTRY_S3R4C2_C_POLY.tsv`;
  testing/d003/stage_s4r7/ 与 stage_s3r4c2/、stage_s3r4c3/ 中本任务书点名的脚本。全部只读。
- **读完直接写脚本**,不要用内联命令预核对门禁项。
- 证据目录:`checkpoints/p05/evidence/p05-s4r8/`(沿用,继续追加;M0 的文件不删、不改、不覆盖)。新文件名一律带 `_M1a` 或 `_r8m1`。
  新脚本:`testing/d003/stage_s4r8/`,文件名带 `_r8m1`。小表:`checkpoints/p05/registries/s4r8/M1a/`。
  报告:`checkpoints/p05/P05_S4R8_REPORT_M1a.md`。勘误:继续追加到 `registries/s4r8/ERRATA_8.txt`(从 E8-18 起)。

## 1. 写入方式与停止条件
- 照 RESTART2 §1 U132(a)–(e) 与 §2:
  · 内联 bash 只用白名单;查看文件用 read 工具,搜索用 grep 工具;
  · 所有写入都写成脚本,经 `sh testing/d003/safe_run.sh p05-s4r8 -- …` 运行;
  · shell 脚本首段逐字为 `REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"`;
  · Python 一律用 `python3 -I -B`;
  · 脚本与命令中不得出现 `/dev/null`、heredoc、`sed -i`、`python3 -c`、`cat >`、`tee`、`rm -rf`、`&` 后台启动,也不得出现仓库外写入目标;
  · 每个脚本运行前用 grep 工具查原任务书 §0.2 的禁止项正则,结果 0 行才能运行,并经 prerun_log_r8.sh 记录(记录文件改为 `$EV/PRERUN_CHECKS_R8_M1a.txt`)。
    prerun_log_r8.sh 已提交,不改;如果它的输出文件名是写死的,就新建 `prerun_log_r8m1.sh`(复制后只改输出文件名)。
- 历史脚本的复制品:标准首段替换、`/dev/null` → `$EV/` 下的日志、`rm -rf` → `test ! -e`(U17)、树标签、库与驱动路径、输出目录、sha256 常量,属于预期改动。
  每份复制品与原件的 `diff -u` 写入 `$EV/RUNNER_DIFF_R8_M1a.txt`;出现其他改动,就在 ERRATA_8 中逐条说明理由。
- 复制或建目录的脚本必须**先确认全部输入存在**,再建目标目录。构建耗时长,超时转为后台时等它结束,不重复启动。
- 停止条件仅限:① 写入目标在仓库外;② 写入没经 safe_run;③ 运行了运行前检查未通过的脚本;④ 门禁不符;⑤ 需要改 S4/ 或已提交的历史装置;
  ⑥ §3 中 dbg 库去调试段后不相等;⑦ §5 的映射出现 DIFFERENT;⑧ §7 的 dry-run 有 fail 或 unparsed。
  只读内联命令的文本瑕疵(未写仓库外)记入表二,继续执行,但报告必须逐条列出 UTC 与原文。
- 报告必须有"内联命令自查"一节。

## 2. 用户裁决(追加到 RULINGS.tsv,status `生效`,来源写"R8 M1a 任务书 §2";接在 U136 之后;同时追加到 ERRATA_8.txt)
- U137:R8 M0 由用户审核接受(e2589cb)。提交后对 `P05_S4R8_REPORT_M0.md` §10/§16 的措辞修正(未提交)接受,随本轮记录提交入库,不单独提交。
  收尾阶段那条超出白名单的只读内联命令(`ls -la … | head -20; echo ---; git status --short`)记入表二。以上记为 E8-18。
- U138:R8 M1 分为三个子里程碑,每个结束后停下,等用户审核:
  M1a(本任务书)= 准备,不做注入运行;
  M1b = plain 组注入回归(R7 的 G7、G8、4.2、G2b、G3、G4、CTRL_SEAM、G2c、G1、G2a),加 S3R4 的 22 行新增与多边形等价;
  M1c = dbg/gdb 状态组(R7 的 G5、G6 与 18 对照)。
- U139:M1b/M1c 的比较规则(在本轮预注册):
  (a) 每组先在 F2 上跑基线(复用 R7 的 F2 驱动,U126 做法),逐点与 R7 中 F2 的结果比较,不变才继续(同 R7 的 U81);
  (b) 再在 F3 上跑。F3 的期望 = R7 中 F2 两遍一致的 class 与 rc1(INFLUENCED);
  (c) 对照行期望 CONTROL_OK;R7 M1 的 18 行对照按 U44 的 POSTHOC 重判(`RESULTS_R7_M1_CTRL_REJUDGE_POSTHOC.tsv`)取期望,不用 RESULTS 中 E7-8 的错位行;
  (d) R7 G1 中 22 个 NOT_REACHED_AS_EXPECTED 点,期望照旧为 NOT_REACHED_AS_EXPECTED;
  (e) G2c-control 6 行沿用 U65(a) 的 NOT_RUN_REGISTRY_ERROR,不运行。
  期望只能由脚本从 R7 已提交的 registries/s4r7/ 表生成,不得手写。
- U140:按调用次数计数的注入(init:N、win:M、S4FMM_NTH、RNV1 窗口 M 值等),在 F3 上能否照搬期望,取决于 §5 的 F2→F3 调用序列映射:
  只有 IDENTICAL 的点才能照搬;任何 DIFFERENT 都停下等裁决,不得自行重映射。
- U141:E8-9 的查明(U136)是本轮第 0 步。方法照 R7 U84/U87:对复制件做 `objcopy --strip-debug`,静态库逐成员比较(`ar x` 后逐 .o strip 再比);
  比较对象是 R8 的 F3-dbg 库与 S3R4 的 F3-dbg 库(`evidence/p05-s3r4/build_f3/dbg/build/libS4.a`,sha256 10ea03b37ccdb6f256bd65904763520e6570e297ba2060416f28253e1f065afa)。
  全部成员 EQUAL_AFTER_STRIP,就关闭 E8-9(措辞同 U87:差异只来自调试段);否则停下。
- U142:22 行新增与多边形等价在 M1b 运行。F3 侧驱动用 R8 的 F3 plain 库(sha256 abbc01c7…05de,与 S3R4 SAME)重新链接,并把驱动 sha256 与 S3R4 记录比较,
  结果写 SAME 或 DIFFERENT(DIFFERENT 只记录,不停止)。F2 侧复用 S3R4 的 F2 驱动,运行前核对 sha256。
  期望取自 REGISTRY_S3R4C2_A.tsv、REGISTRY_S3R4C3_A_CTRL.tsv、REGISTRY_S3R4C3_B.tsv、REGISTRY_S3R4C2_C_POLY.tsv 的原行(INFLUENCED)。
  这是 S4 的修复后验证,不再是自检;但报告仍只写"REPORTED_FAILURE(该注入下返回码非零)",不写"已修好"。
- U143:门禁的"允许修改列表"与"允许未跟踪列表"改为数据文件。门禁运行前先用 write 写入 `testing/d003/stage_s4r8/gate_allow_r8m1a_{start,end}.txt`,
  记录 sha256,并随记录提交入库;门禁脚本只读这两个文件,不在脚本里写死。

## 3. 门禁 gate4_r8m1.sh(新文件,复制 gate3_r8.sh 后修改)
- 参数:`<输出名> <start|end> <允许列表文件> <tmp_count> <tmp_sha256> [<start_tmp_count> <start_tmp_sha256>]`。
- start 模式:
  · HEAD = e2589cbc2b470ae88286d582ee62699e7c0d9e4c;
  · HEAD:S4 = 8d8202a:S4 = 6cff923a02baf19e01966b2339755cbf3a5deeef;
  · a07b5ac:S4 = e124925f5b242486a913b813fa181664f665b048;
  · S4 diff 用 `LC_ALL=C sort` 后,等于那 4 个文件;
  · 判定器 sha256、REGISTRY_S3R4C3_D.tsv 的 sha256 与之前相同;
  · `registries/s4r8/` 中 `sha256sum -c SHA256SUMS.txt` 全部 OK;
  · registries/s4r7 按 check_s4r7_manifests_r8.py 核对,fails=0(输出用新文件名);
  · `git status --short` 的每一行都要出现在允许列表里。start 允许列表恰为:
    ` M checkpoints/p05/P05_S4R8_REPORT_M0.md` 与 `?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a.md`,
    以及 `testing/d003/stage_s4r8/` 下本轮新建的未跟踪文件(按前缀匹配);
  · /tmp 快照。
- end 模式:
  · HEAD^ 为 e2589cb,且 HEAD 的提交信息等于 §8 的记录提交信息;
  · HEAD:S4 不变;
  · status 中只允许列表里的项出现。end 允许列表为:STATE.md、ERRATA_8.txt、RULINGS.tsv 为 ` M`;
    `P05_S4R8_REPORT_M1a.md`、`registries/s4r8/M1a/`、`testing/d003/stage_s4r8/` 下的新文件为 `??`;
  · /tmp 快照与开工值相同。
- 开工输出 `GATE_R8_M1a.txt`,收尾输出 `GATE_R8_M1a_END.txt`。FAILS 必须为 0。

## 4. 第 0 步:dbg 库差异(U141)
- strip_equiv_r8m1.sh:复制自 `testing/d003/stage_s4r7/check_dbg_strip_equiv_r7.sh`,只改比较对象(上述两份 F3-dbg 库)与输出目录 `$EV/strip_cmp_r8m1/`。
  输出 `STRIP_EQUIV_R8_M1a.tsv`(逐成员一行)与 `STRIP_EQUIV_SUMMARY_R8_M1a.txt`(成员总数、EQUAL_AFTER_STRIP 数、其他数)。
- 原件不改,只对复制件做 strip。不相等就停下。

## 5. F3 构建与驱动补齐(只做 M1b/M1c 需要、而 M0 没有的部分)
5.1 先写清单 `$EV/NEEDS_R8_M1a.tsv`:对 R7 每个组列出组名、所用驱动族、模式(plain/dbg)、库类型(plain/seam plain/seam dbg)、R7 驱动路径、R7 驱动 sha256、
    F3 对应驱动名、是否已在 M0 中存在(DRIVERS_R8.tsv)。来源只能是 R7 的 DRIVERS_R7*.tsv、运行器源码与 p05-s4r7/safe_run.log(只读,写出行号)。
5.2 按清单补建(都复制自 R7 脚本,只改树、库路径和输出目录):
    · F3 seam dbg 库(seamF、fmmret):复制自 build_seam_s4r7.sh;seam 源码树复用 M0 的 `$EV/seam_r8/`(只读),不重新 apply;
    · r6dnv1-F3-plain(G7、4.2 用):复制自 link_drivers_s4r7.sh 中的 r6dnv1 段;
    · tri-F3-dbg(M1 的 G8 与 tri 行用 dbg,见 run_m1_r7.py:37–38):复制自 R7 链接 tri dbg 驱动的命令(p05-s4r7/safe_run.log 中查出);
    · d003/d003plan/r6bstate 的 F3 dbg 驱动;
    · r6bseam-seamF-F3、r6bseam-fmmret-F3(G6 用):复制自 link_r6b_seam_r7.sh;
    · init-F3、polyinj-F3、poly-F3(22 行新增与多边形用,U142):分别复制自 stage_s3r4c2/link_init_c2.sh、stage_s3r4c3/link_poly_inj_c3.sh、stage_s3r4c2/link_c2.sh,
      库改为 R8 的 F3 plain 库,输出到 `$EV/drivers_r8m1/`。
    · 编译选项:对每组 g++ -c 命令行与 R7 对应组比较(复制 build_option_diff_r7.sh),去掉路径后的差异行数写入 `BUILD_OPTION_DIFF_R8_M1a.txt`,期望为 0。
    告警数:dbg 62、plain 71;seam 告警数与 R7 BUILD_SEAM*_R7.tsv 中的值相同。不同就停下。
5.3 F2 侧复用:R7 的 F2 驱动(全部组)与 S3R4 的 F2 驱动(init、polyinj、poly)只读复用。运行前核对 sha256 与 R7/S3R4 的记录一致,
    写入 `DRIVERS_R8_M1a_F2_REUSED.tsv`(SAME / FIRST_RECORD)。不重新链接。
5.4 汇总 `DRIVERS_R8_M1a.tsv`:驱动名、树、模式、库 sha256、驱动 sha256、链接脚本、与历史比较(SAME/DIFFERENT/FIRST_RECORD)。

## 6. F2→F3 注入点映射(U140;只做无注入运行)
6.1 静态映射(只读 `git show`):F2(a07b5ac)与 F3(8d8202a)中,R7 脚本与 gdb 文件引用的所有 `文件:行号` 与函数名,写入 `LINEMAP_F2_F3_R8_M1a.tsv`
    (列:引用来源脚本:行、文件、F2 行号或函数、F3 行号或函数、状态 SAME_LINE/SHIFTED/MISSING)。MISSING 就停下。
6.2 动态映射:对每个按次数计数的注入族(R7 中实际用到的 init:N、win:M、S4FMM_NTH、RNV1 窗口 M),用 dbg 驱动在 F2 与 F3 上**无注入**各运行一次,
    记录被计数调用的有序序列(调用点的函数名 + 调用者函数名 + 序号;不含地址),覆盖 R7 中每个 (模式, NG, 驱动族) 组合。
    · 方法:复制 R7 或 S3R4 已有的映射脚本(R7 的 RNV1_JONES_MAP 用的 gdb 文件、stage_s3r4c2/a1map_c2_v2.sh 与 a1map_c2.gdb),只改驱动与输出;
      没有现成脚本的注入族,写新 gdb 脚本,只用函数名断点,不用 `文件:行号` 断点。
    · 输出 `CALLSEQ_F2_F3_R8_M1a.tsv`(组合、注入族、F2 序列 sha256、F3 序列 sha256、F2 长度、F3 长度、IDENTICAL/DIFFERENT)与原始序列文件。
    · 期望:除 F3 在失败路径上新增的检查(不改变正常路径的调用次数)外,全部 IDENTICAL。依据:[源码] F2→F3 的非注释改动只在失败返回处(git diff a07b5ac 8d8202a -- S4/)。
      先把这一期望写入 `EXPECT_CALLSEQ_R8_M1a.txt` 并记录 sha256,再运行。
    · 已知事项:S3R4 的 A1 映射(K=7/8 对 K0=6/7)用的是 init 驱动和另一种计数口径,按原样引用,不在本轮重新解释。
      若本轮出现 DIFFERENT,先查是否属于同一口径差异(写 [源码] 依据),然后停下等裁决。
    · 22 行新增(A/B 行)的 init:N 与 win:M 来自 S3R4 在 F3 上的实测映射,不需要 F2→F3 映射;只需核对 R8 的 init-F3 驱动和 polyinj-F3 驱动
      在这些 K 值上的序列,与 S3R4 C2/C3 的映射记录一致(`CALLSEQ_ADDITIONS_R8_M1a.tsv`)。

## 7. 预注册与 dry-run
- make_prereg_r8m1.py(新文件)只读 registries/s4r7/ 与 registries/s3r4c2/、s3r4c3/ 的已提交表(写出源文件 sha256),生成:
  · `REGISTRY_S4_PRE_R8_M1b.tsv`:R7 的 G7、G8、4.2、G2b、G3、G4、CTRL_SEAM、G2c、G1、G2a 的每个点各两行(F2 基线行与 F3 行)。
    列至少包括:group、point_id、tree、driver、环境(由 matrix_r2.build_env 与 expected_env_independent_r7 的规则推导,不读 ADD 的环境列,同 U75b)、
    expected_class、expected_rc1、来源表:行、callseq_status(取自 §6)、status=INFLUENCED;
    另含 22 行新增(F2 与 F3 行,照原登记表)与多边形 33 组合(F2 与 F3)。
  · `REGISTRY_S4_PRE_R8_M1c.tsv`:G5(177)、G6(25)、18 对照,F2 与 F3 各一套。期望照 REGISTRY_S4_PRE_R7_M3.tsv 中 F2 的判定,不变量 I1–I6;I7 仍 DEFERRED。
  · 生成器自检:每组行数与 R7 对应结果表的点数一致,写入 `PREREG_COUNTS_R8_M1a.tsv`(组、R7 点数、预注册行数、OK/BAD)。任一 BAD 就停下。
  · 两份预注册写完立即记录 sha256 与 UTC(`PREREG_RECORD_R8_M1a.txt`)。之后只能新建 `*_ERRATA*.txt`,不改原文件。
- dry-run(dryrun_r8m1.py,复制自 R7 的 dryrun_m3_r7.py 与 run_m2b_all_r7.py 的 dry_run 模式):逐行解析预注册,核对驱动存在且 sha256 一致、环境可推导、callseq_status 为 IDENTICAL(或该行不适用),
  **不执行驱动**。输出 `DRYRUN_R8_M1a.txt`(ok、fail、unparsed)。fail 或 unparsed 大于 0 就停下。
- M1b/M1c 的运行器本轮只写、不运行(run_m1b_r8m1.py、run_m1c_r8m1.py,只 import R7 的判定与环境函数,不调用 R7 中写死 F/F2 路径的 driver_for 等函数,驱动只来自 DRIVERS_R8_M1a.tsv 与 F2_REUSED 表)。
  每个运行器提供 `--dry` 模式,由 dryrun_r8m1.py 调用;它们的运行前检查也要做。

## 8. 记录提交(本轮唯一一次提交,在 §4–§7 完成后做)
- 小表复制到 `registries/s4r8/M1a/`(先确认全部输入存在):
  GATE_R8_M1a*.txt、gate_allow 两个文件的 sha256 记录、PRERUN_CHECKS_R8_M1a.txt、STRIP_EQUIV_*_R8_M1a.*、NEEDS_R8_M1a.tsv、BUILD_OPTION_DIFF_R8_M1a.txt、
  构建表、DRIVERS_R8_M1a*.tsv、LINEMAP_F2_F3_R8_M1a.tsv、EXPECT_CALLSEQ_R8_M1a.txt、CALLSEQ_*_R8_M1a.tsv、两份预注册、PREREG_COUNTS、PREREG_RECORD、DRYRUN、RUNNER_DIFF。
  单个文件超过 1 MB 的不复制,只在清单中记录 sha256,并写入 E8。在该目录写 SHA256SUMS.txt;`sha256sum -c` 全部 OK,逐个 cmp 副本与原件。
- `$EV/SHA256SUMS_M1a.txt` 覆盖本轮新增的非二进制证据文件(不覆盖 M0 的清单)。
- STATE.md 用 edit 修改,保持一页以内:当前轮次写"P05-S4 R8 M1a(准备):dbg 库 strip 等价 …;映射 …;预注册 M1b x 行、M1c y 行;dry-run ok …;下一步 M1b(待用户审核)";
  关键数字表加 R8 M1a 一行;开放问题表中 E8-9 一行按结果更新。
- 报告 `P05_S4R8_REPORT_M1a.md`,依次写:门禁;U137–U143;dbg 库差异;需求清单;构建与驱动;F2 复用;静态映射;动态映射;预注册计数;dry-run;
  STATE 变更;违规两张表;内联命令自查;待用户裁决(没有就写"无")。每项只写"完成""未完成(原因)""不可行(依据)"之一。
- 先运行 gate4 end,FAILS=0 后再写 commit_rec_r8m1.sh。git add 逐个列出文件:RULINGS.tsv、ERRATA_8.txt、STATE.md、P05_S4R8_REPORT_M0.md、P05_S4R8_REPORT_M1a.md、
  briefs/P05_S4R8_BRIEF_M1a.md、registries/s4r8/M1a/ 下的文件、testing/d003/stage_s4r8/ 下本轮的新文件。不用 -A 或 `.`。
  提交信息:`P05-S4 R8 M1a prep on F3: dbg strip equivalence (E8-9), drivers, F2-F3 line and call-sequence maps, M1b/M1c pre-registration, dry-run; M0 report wording (U137). awaiting user review`
- **提交后不再修改任何已跟踪文件。** 如果发现报告有错,只在对话里说明,下一轮再改。
  提交后把真实的 `git log -3 --oneline` 与 `git status --short` 写入 `$EV/FINAL_GIT_R8_M1a.txt`(用脚本),并在对话中原样贴出。status 应为空。
- 结尾只写"本轮已完成 R8 M1a 范围,等待用户审核"或"本轮未完成 R8 M1a 范围,等待用户审核"。

## 9. 不停但要记录的情形
- 驱动 sha256 与历史 DIFFERENT(库相同、告警相同);F2 驱动没有 sha 记录(FIRST_RECORD);某组在 R7 中没有可复制的链接命令(写"未完成(原因)",并说明这对 M1b/M1c 的哪些行有影响)。
- M1a 范围以外的事一律不做,即使看起来顺手。尤其不得提前运行任何注入。
