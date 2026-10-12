# P05-S3 R4 续3(S3R4 的续轮,不是新阶段):补完自检 A、B、D 与 U100 说明,并收尾

你是 P05-S3 的自检执行者。本轮记为 S3R4 续3,不得出现 P05-S6。不得宣布任何阶段完成或签收;报告与 STATE 不写签收建议(U83)。
本轮自检不是修复后验证;修复后验证由 P05-S4 R8 在 F3 上完成。**本轮不得修改 S4/ 下任何文件**;如果自检表明需要改 S4/,停下报告。

先读(按顺序):AGENTS.md、checkpoints/p05/STATE.md、checkpoints/p05/P05_S3R4_CLOSEOUT_CONT2.md、
checkpoints/p05/briefs/P05_S3R4_CONT2_BRIEF.md、checkpoints/p05/briefs/P05_S3R4_CONT1_BRIEF.md(§3–§7 是 A、B、D 的技术内容,
本任务书只写差异;冲突时以本任务书为准)、checkpoints/p05/ERRATA_S3R4.txt(ES3R4-15…21)、
checkpoints/p05/registries/s3r4c2/(REGISTRY_S3R4C2_A.tsv、A1_MAP_SUMMARY_S3R4C2.tsv)、
testing/d003/stage_s3r4/inject_s3r4_init.cpp、testing/d003/stage_s3r3/run_s3r3_selfcheck.py(事实提取与判定写法)、
testing/d003/judge_d003.py 的 classify 与 facts_from_log(只读)。

- 证据目录:checkpoints/p05/evidence/p05-s3r4c3/(新目录)。p05-s3r4/、p05-s3r4c2/ 只读引用,不往里面写任何东西。
- 新脚本目录:testing/d003/stage_s3r4c3/(文件名带 c3)。小型结果表:checkpoints/p05/registries/s3r4c3/。
- 报告:checkpoints/p05/P05_S3R4_CLOSEOUT_CONT3.md。勘误在 ERRATA_S3R4.txt 末尾追加,从 ES3R4-22 起编号,不改已有条目。
第一步:用 write 把本任务书原文存为 checkpoints/p05/briefs/P05_S3R4_CONT3_BRIEF.md。

## 0. 门禁与写入方式

### 0.1 开工门禁(任一不符就停下报告)
- HEAD = f826694;`git rev-parse HEAD:S4` = 6cff923a02baf19e01966b2339755cbf3a5deeef(F3);
  judge_d003.py sha256 = d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb。
- `git status --short` 只允许以下 3 行(本任务书的存档是第 4 行,属于预期):
  `?? testing/d003/stage_s3r4c2/link_c2.sh`、`?? testing/d003/stage_s3r4c2/link_init_c2.sh`、`?? testing/d003/stage_s3r4c2/run_a_c2.sh`。
- 只读核对以下 sha256(写入 $EV/GATE_CONT3.txt;任一不一致就停下):
  · F2 库 evidence/p05-s3r4/build/F2-plain/build/libS4.a = c63d180aff6c5b5e443faefeb6de44abce430dafbb846db434ac15da85fbc185
  · F3 库 evidence/p05-s3r4/build_f3/plain/build/libS4.a = abbc01c78f0a422f3494556bb43e212e397fbbf49d03370132ae45e2c268e5de
  · init 驱动 evidence/p05-s3r4c2/drivers/init-F2/driver = 29bb377c4eb5e1d393d2916d2ad9a05d9ecf781fc4cc709dd87332f8904d1158
  · init 驱动 evidence/p05-s3r4c2/drivers/init-F3/driver = ff66cfc1bf87b6c22d13e32dc6adf3c5e6b090fdcad745bf5248f74dd9510b68
  · REGISTRY_S3R4C2_A.tsv(evidence/p05-s3r4c2/)= 3f08fd8b86d2a5164b272cf3881729b3fbda04dca52e7b8d96dd64c586e5845d
- /tmp 顶层只读快照(条目数与列表的 sha256),开工与收尾各一次,写入 $EV/GATE_CONT3.txt 与 $EV/GATE_CONT3_END.txt。

### 0.2 写入方式(沿用 U106,并补上续1/续2 两次停止的原因)
- 仓库内的文本文件(报告、ERRATA、RULINGS、STATE、tsv、脚本、驱动与注入器源码)只用 write 或 edit 工具写。
- 其他写入(编译、链接、运行、复制、sha256 清单、门禁快照)分两步:① 用 write 把命令写成
  testing/d003/stage_s3r4c3/<名字>_c3.sh(或 _c3.py),所有重定向都写在脚本里;
  ② 运行 `sh testing/d003/safe_run.sh p05-s3r4c3 -- sh testing/d003/stage_s3r4c3/<名字>_c3.sh [参数]`。
  只有 git commit 可以写成内联(写法同续2 任务书 §0.2)。
- shell 脚本的第一段必须**逐字**是:
  `REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"`
- **复制历史脚本时(重要)**:testing/d003/ 下几乎所有历史脚本都有一行 `REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {…}`。
  复制时**必须删掉这一行,换成上面的标准首段**。写给原件的 diff 中,这一行的变化属于预期,在 diff 摘要中注明。
  历史脚本中嵌套调用 safe_run 的 `sh -c '…'` 若含 `>/dev/null` 或 `2>/dev/null`,同样改为重定向到 $EV/ 下的文件。
- 脚本与命令文本中一律不得出现:`/dev/null`(含 `>/dev/null`、Python 的 `subprocess.DEVNULL` 与 `os.devnull`)、
  `&` 后台启动、heredoc、`sed -i`、`python3 -c`、`cat >`、`tee`,以及任何以 / 开头又不在 $REPO 下的路径。
- **运行前检查(每个脚本、每次修改后都做)**:用 grep 工具在 testing/d003/stage_s3r4c3/ 中搜索
  `/dev/null|DEVNULL|devnull|<<|sed -i|python3 -c|cat >|tee |/tmp`,结果必须为 0 行才可以运行;把每次检查的结论
  (脚本名、时间、0 行)记入 $EV/PRERUN_CHECKS_C3.txt(经脚本写入)。未运行的草稿在检查中被发现并改正,不算违规;
  违规以"含禁止项的脚本或命令被执行"为准。
- 写入目标只能在 $EV/、testing/d003/stage_s3r4c3/、checkpoints/p05/ 下。不改 testing/d003/ 下已提交的任何文件。
- 不做拒绝性测试或沙箱探测。长输出带 head/tail,或用 read 的 offset/limit。
- 禁止写 .git 或改工作区的 git 命令(fsck、gc、prune、stash、checkout、switch、reset、clean)。
- **写入规则违反一次就停下**,按两张表披露。

## 1. 用户裁决(先追加到 RULINGS.tsv,再写进 ERRATA ES3R4-22 之前的裁决块)
- U107:续2 的写入违规(link_c2.sh、link_init_c2.sh 含 `2>/dev/null` 并各运行两次)接受为已披露;续2 停止是正确的。
  续2 的门禁、记录提交、U105、C 多边形(99/99 IDENTICAL)、A1 映射(K 唯一)与 A 的预注册仍然有效,不作废。
  根因之一是任务书要求"复制历史脚本只改路径",没有提示历史脚本首行含 2>/dev/null(规划者疏漏);续3 起按 §0.2 处理。
- U108:三个未跟踪脚本**原样提交存档,不修改,不再运行**:link_c2.sh、link_init_c2.sh 是 C 多边形与 init 驱动的来源记录;
  run_a_c2.sh 是从未运行的草稿。把这三个历史文件存档提交不算违反 U106(U106 约束的是本轮编写、执行的脚本与命令)。
  在 ERRATA 中写明"DO NOT RUN",并注明续3 的 A 由新脚本 run_a_c3.* 执行。
- U109:A 复用续2 已链接的 init 驱动(sha256 见 §0.1),不重新链接,使 A1 映射与 K 对应同一份二进制。
  REGISTRY_S3R4C2_A.tsv 原样作为 A 的预注册,不改不重写。
- U110:A-U96 的 `init:K0` 按映射定义(closed2d NG1 K0=6;fft、kottke NG5 K0=7),确认 ES3R4-20。
- U98–U106 继续有效。

## 2. 记录提交(先做,一个提交)
- RULINGS.tsv 追加 U107–U110(status `生效`,来源写本任务书 §1)。
- ERRATA 追加 U107–U110 裁决块,以及:
  ES3R4-22:续2 报告 §10 结尾"本轮已完成/未完成 S3R4 续2 范围"应读作"本轮未完成 S3R4 续2 范围"(原文不改)。
  ES3R4-23:evidence/p05-s3r4c2/SHA256SUMS.txt 用 sha256sum -c 校验时报"1 line is improperly formatted"。
  先只读核实是哪一行、为什么(预计是 safe_run.log 单列行),再写结论;不改原清单。
  ES3R4-24:U108 三个脚本的存档说明(DO NOT RUN;各自的 sha256)。
- 一起提交:RULINGS.tsv、ERRATA_S3R4.txt、briefs/P05_S3R4_CONT3_BRIEF.md、三个 stage_s3r4c2 脚本。
  提交信息:`P05-S3R4 CONT3 rulings U107-U110, errata ES3R4-22..24; CONT2 untracked scripts archived unchanged (DO NOT RUN). awaiting user review`

## 3. 执行顺序:(A)→(B)→(D)→ U100 说明
C 已由续2 完成,本轮不重做。

### 3.1 (A) 806 与 1729:注入运行(预注册与 K 已由续2 完成)
- 新的运行器 stage_s3r4c3/run_a_c3.py(由 run_a_c3.sh 经 safe_run 调用),以 REGISTRY_S3R4C2_A.tsv 为输入,每行跑两遍:
  `env -i PATH=… FMM_MODE=<mode> S4FMM_NG=<NG> S4FMM_INJECT=<inj_spec> S4FMM_DUMP_DIR=<点目录> <init-<tree> 驱动> pattern both 4 3`,
  stdout 与 stderr 分别写文件。事实 = 驱动返回码(信号按 128+n 换算)+ stdout 与 stderr 拼接后用
  judge_d003.facts_from_log 提取的 rc1、rc2、hit。类别 = judge_d003.classify(rc, rc1, rc2, hit, control=False, inj_call=1)(import,不修改)。
- verdict:class 与 expected_class 相同,并且 expected_rc1 为 "-" 或等于 rc1,判为 MATCH,否则 MISMATCH;两遍结果不同记 FLAKY。
  rc2 是副观察,单列 side_rc2_match,不参与 verdict。
- 另跑 6 次无注入对照(每棵树 × 每个组合,不设 S4FMM_INJECT),用 classify(control=True),期望 CONTROL_OK。
  对照的期望在运行前写入 $EV/REGISTRY_S3R4C3_A_CTRL.tsv,记录 sha256 与 UTC。
- 输出:$EV/a_c3/<tree>/<combo>/<point>/pass<N>/;结果表 $EV/RESULTS_S3R4C3_A.tsv(每遍一行:combo、mode、NG、tree、point_id、
  inj_spec、pass、rc、rc1、rc2、hit、class、reason、expected_rc1、expected_class、verdict、side_rc2_match)。已存在就拒绝覆盖。
- 合计 36 次注入 + 6 次对照。出现 MISMATCH:两遍跑完后停下 A,不改期望,也不改修复;继续 B 和 D。
- F2-dbg 的 `info line` 佐证是可选项;如果做,命令写进 .gdb 文件经脚本运行。

### 3.2 (B) 415:多边形 + Pattern_DiscretizeCell 窗口(续1 任务书 §4,以下为差异)
- 驱动:复用续2 的 testing/d003/stage_s3r4c2/driver_s3r4c2_poly.cpp(只读,不复制,不修改)。
- 注入器 stage_s3r4c3/inject_s3r4c3_poly.cpp:由 stage_s3r4/inject_s3r4_init.cpp 复制改名,窗口改为 `--wrap=Pattern_DiscretizeCell`。
  **窗口计数跨调用累计**:每次进入窗口时不清零,全进程只有一个窗口 malloc 序号;`win:M` = 全进程第 M 次窗口内 malloc 返回 NULL。
  每次窗口 malloc 都打印 k(累计序号)、n、caller、hit;另外导出一个计数查询函数,供 gdb 读取。写出与原注入器的 diff。
- 链接脚本 link_poly_inj_c3.sh:以 stage_s3r4/link_init_s3r4.sh 为模板(按 §0.2 替换 REPO 行),
  wrap 改为 `-Wl,--wrap=Pattern_DiscretizeCell`(其余 wrap 与转发保持一致);F2、F3 各链接一份到 $EV/drivers/polyinj-<tree>/,
  记录 sha256;写出与模板的 diff。
  链接后用 nm 核对 __wrap_Pattern_DiscretizeCell 与 __real_Pattern_DiscretizeCell 的符号,结果写 $EV/NM_CHECK_POLY_C3.txt。
  [已知,仅供参考]F3 库中 fmm_FFT.o、fmm_kottke.o 对 Pattern_DiscretizeCell 是 U,pattern.o 中是 T,属于跨目标文件调用。
- 前置映射(F2、F3 × fft、kottke × NG 1、5、9,不注入,每个组合一次):
  · gdb 在 pattern.c tri 的那次 malloc 所在行下断点,确认进入 POLYGON 分支(两棵树各自核对行号;[已知]F3 上是 pattern.c:418);
  · 统计窗口内 malloc 的总次数 Mtot 与每次的 n(期望 n=12,依据 3×(5−2)×sizeof(int);polygon_triangulate 与
    convex_polygon_intersection 不分配内存,写明 intersection.c 的 [源码] 依据);
  · **确定 Mfirst = 第一次公共调用(RC first)返回之前的窗口 malloc 次数**。方法:gdb 断在驱动打印 "RC first" 的那一行
    (driver_s3r4c2_poly.cpp 中对应行),读取注入器的累计计数。如果 Mfirst 不能唯一确定,停下 B,记"未完成(原因)"。
  · F2 不注入时 rc 不为 0,或者没有进入 POLYGON 分支:如实记录并停下 B,不得换几何体凑结果。
  映射表 $EV/B_MAP_C3.tsv:tree、combo、Mtot、Mfirst、n 的取值集合、POLYGON 断点命中次数。
- 预注册 $EV/REGISTRY_S3R4C3_B.tsv(INFLUENCED;映射之后、任何注入运行之前写定,记录 sha256 与 UTC):
  组合 fft、kottke × NG 1、5、9;点 = win:1 与 win:Mfirst(按每个组合的映射写入);
  期望 F2 = CRASH(依据写文件:行号:tri 为 NULL 时 polygon_triangulate 返回 −3 并被忽略,随后读 tri[...]);
  F3 = REPORTED_FAILURE,rc1 = 20,hit = 1,无信号(U94);副观察:F3 的 rc2 期望为 0。另加每棵树、每个组合一次无注入对照,期望 CONTROL_OK。
- 运行:6 组合 × 2 点 × 2 树 × 2 遍 = 48 次 + 12 次对照。判定方法同 A。结果表 $EV/RESULTS_S3R4C3_B.tsv。
  MISMATCH 的处理同 A。

### 3.3 (D) 冒烟(续2 任务书 §3.5 原样有效,以下为差异)
- 普通驱动以 stage_s4r7/link_drivers_s4r7.sh 为模板(按 §0.2 替换 REPO 行),只改库路径(F3 plain/dbg 库)和输出目录,
  写出选项 diff 的核对(除 REPO 行与路径外为 0)。F3 的 dbg 库若需要,只读引用 evidence/p05-s3r4/build_f3/dbg/,先记 sha256。
- CTRL_SEAM:R7 使用的是 build_seam_s4r7.sh(以 seam_r7/ 下由 seam 应用脚本生成的 seam 树为输入)。先读 R7 报告,
  确认 seamF 与 fmmret 树的生成方式。如果在 F3 上生成 seam 树需要已提交历史脚本以外的改动,不做这一组,
  记"未完成(原因)",其余 6 点照常运行,不得用别的点替代。如果只需要以历史 apply 脚本为模板复制,并在 F3 的 git archive 导出物上运行,可以做,
  但构建与 apply 的 `>/dev/null` 一律改为重定向到 $EV/ 下的文件。
- 期望 = run7 的类别与 rc1;先写 REGISTRY_S3R4C3_D.tsv,再运行。报告写"冒烟",不写"回归"。

### 3.4 U100 的 [源码] 说明
- 逐个列出 Pattern_DiscretizeCell 的 −1…−9:来源(文件:行号)、触发条件、经公共 API(S4_Layer_SetRegion*、Python、Lua)
  是否可达(只写 [源码],不运行)。写成 $EV/U100_SOURCE_NOTE.md,并作为 CLOSEOUT_CONT3 的一节。

## 4. 收尾
- 红点状态表 $EV/RED_POINTS_STATUS_S3R4C3.tsv:806、415、RP-S3R4-1 只写"自检通过/未通过/未完成(F3:类别、rc1)",
  不写"已修好""已验证";528、1164、ES3R4-5(a)(b)、−1…−9 写 OUT_OF_SCOPE_D003 → S5(附 U90、U99、U100)。
- R8 回归清单的新增行 $EV/R8_ADDITIONS_S3R4C3.tsv:A、B 的注入点与无注入对照(tree=F3,带预注册文件名与行号)。
- STATE.md:当前轮次改为"P05-S3 R4 续3:自检 A/B/D 结果……;下一步 P05-S4 R8 在 F3 上";S3R4 关键数字行补续3 数字;
  开放问题表中"S3R4 自检 A 注入运行、B、D"一行按实际结果更新;新增 ES3R4-5(a)(b) 与 −1…−9 两行(→ S5),若已有就不重复。
  整个文件保持一页以内。
- 小型表(各预注册及其 sha256 记录、RESULTS、B_MAP、NM 核对、选项 diff 摘要、PRERUN_CHECKS、红点表、R8 新增行、门禁)
  复制到 registries/s3r4c3/,写 SHA256SUMS.txt(标准 sha256sum 格式,每行"哈希 两个空格 文件名",不得混入其他行),
  并逐个比对与原件一致。
- $EV/SHA256SUMS.txt 覆盖全部非二进制证据文件,只用标准格式。safe_run.log 不进清单,在单独的说明文件中写明
  "清单后追加,不参与校验"。驱动、库只在 $EV/BINARIES_C3.tsv 中记录 sha256。
- CLOSEOUT_CONT3 报告包括:门禁;记录提交的哈希;A、B、D 的预注册 sha256、映射、结果表与数字(MATCH/MISMATCH/FLAKY 计数);
  U100 [源码] 说明;红点状态;R8 新增行;待用户裁决的技术问题;违规两张表(没有就写"无")。
  每一项只写"完成""未完成(原因)""不可行(依据)"三者之一,不得混用;结尾只写"本轮已完成 S3R4 续3 范围,等待用户审核"
  或"本轮未完成 S3R4 续3 范围,等待用户审核"其中一句,附提交后真实的 git log -3 --oneline 与 git status --short(不得预填)。
- 最后一个提交的信息末尾写 `awaiting user review`。提交后 git status --short 应为空;不为空就在报告中说明原因。

## 5. 停止条件
- 门禁不符;需要修改 S4/ 或已提交的历史装置;写入规则被违反一次 → 整轮停止,直接写报告。
- 以下情况只停对应一项,其余照常执行,在报告中写"未完成":A 或 B 出现 MISMATCH(两遍跑完后停);
  B 的前置核对不满足,或 Mfirst 不能唯一确定;D 的 CTRL_SEAM 无法按原方式构建或链接。
- "未完成"与"不可行"必须区分。
