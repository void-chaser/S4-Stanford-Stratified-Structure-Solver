# P05-S4 R8 M1a 续1:裁决 M1a 停止项,补齐缺漏,完成 F2→F3 映射、预注册与 dry-run

你是 P05-S4 的验证执行者。本轮是 P05-S4 R8 M1a 的续1,不是新阶段,不得出现 P05-S6。不得宣布任何阶段完成或签收;报告与 STATE 不写签收建议。
不修改 S4/。不修改 testing/d003/ 下已提交的文件。M1a 已生成、尚未提交的文件(stage_s4r8/ 下 15 个 *_r8m1.* 与 gate_allow_r8m1a_*.txt、
P05_S4R8_REPORT_M1a.md、briefs/P05_S4R8_BRIEF_M1a.md)一律不改,原样随本轮记录提交入库;更正只写入新文件与 ERRATA_8。
**本轮不做任何注入运行。** 只允许 §5 的无注入映射运行(gdb,只设函数名断点),以及 §6 的 dry-run(不执行驱动)。

## 0. 开工
- 第一步:用 write 把本任务书原文存为 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT1.md`。
- 只读:AGENTS.md;STATE.md;`briefs/P05_S4R8_BRIEF_M1a.md`(下称"M1a 任务书";本任务书没有改动的条款,仍按它执行);
  `P05_S4R8_REPORT_M1a.md`;`registries/s4r8/ERRATA_8.txt`;`briefs/P05_S4R8_BRIEF_M0_RESTART2.md` §1 U132;
  `evidence/p05-s4r8/LINEMAP_F2_F3_R8_M1a.tsv`、`NEEDS_R8_M1a.tsv`、`DRIVERS_R8_M1a.tsv`、`DRIVERS_R8_M1a_F2_REUSED.tsv`;
  `registries/s4r7/LINEMAP_M3_R7.tsv`、`LINEMAP_A1_R7.tsv`、`PATTERN_MALLOC_CLASS_R7.tsv`;
  testing/d003/stage_s4/inject_r4_plan.cpp、inject_r6d_rnv1.cpp;stage_s3r4c2/a1map_c2.gdb、a1map_c2_v2.sh;stage_s3r4c3/b_map_c3.gdb;
  `evidence/p05-s4r7/gdb_malloc_lines_r7.gdb`(R7 的 malloc 调用序列模板)。
- **读完直接写脚本。** 不用内联命令预先核对门禁项或映射。
- 证据目录沿用 `checkpoints/p05/evidence/p05-s4r8/`,M0、M1a 的文件不删、不改、不覆盖。新文件名带 `_M1a2`(证据)或 `_r8m1a2`(脚本)。
  小表放 `checkpoints/p05/registries/s4r8/M1a/`。报告写 `checkpoints/p05/P05_S4R8_REPORT_M1a_CONT1.md`。ERRATA_8 从 E8-23 起追加。

## 1. 写入方式与停止条件
- 照 RESTART2 §1 U132(a)–(e) 与 M1a 任务书 §1。重申:
  · 内联 bash 只用 U132(c) 白名单,管道只接 head、tail、wc、sha256sum、LC_ALL=C sort。
    **`echo`、`cut`、`grep`、`sed`、`cat`、`2>&1`、`ls -la` 都不在白名单内**;查看文件用 read 工具,搜索用 grep 工具,其余需求一律写成脚本。
  · 每条内联命令在报告"内联命令自查"中登记 UTC 与原文:命令运行后立即把 `date -u` 的输出与原文记下来;
    `date -u +%Y-%m-%dT%H:%M:%SZ` 本身列入本轮白名单。做不到逐条记录,就不要用内联命令。
  · gdb 命令文件与数据文件用 write 工具写入 `testing/d003/stage_s4r8/`,不用 printf 经 sh -c 生成(R7 曾用这种做法,本轮不沿用)。
  · 每个脚本与数据文件运行前,用 grep 工具查禁止项正则,结果 0 行后经 prerun_log_r8m1.sh 逐个记录(记录文件仍为 `$EV/PRERUN_CHECKS_R8_M1a.txt`,只追加)。
- 停止条件:M1a 任务书 §1 的 ①–⑤、⑧,加上:
  ⑥' 映射 v2(§4)出现 U145–U147 以外的 MISSING 或 AMBIGUOUS;
  ⑦' 动态映射(§5)出现 U148 允许范围以外的 DIFFERENT;
  ⑨ 预注册计数自检有 BAD;
  ⑩ 门禁(§3)FAILS 不为 0。

## 2. 用户裁决(追加到 RULINGS.tsv,status `生效`,来源写"R8 M1a 续1 任务书 §2";先补 U137–U143,再写 U144–U151;同时追加到 ERRATA_8)
- U144:M1a 在 §6.1 停止,处理正确。根因是 M1a 任务书 §6.1 的规划缺陷:映射状态里没有"被修复改写"这一类,而且要求按文字匹配。
  这不是执行者的过错。M1a 的已完成部分全部接受(门禁、strip 等价并关闭 E8-9、需求清单、seam dbg 库、10 个驱动、编译选项差异 0、F2 复用、驱动汇总)。
- U145:pattern.c 的 415 与 528 按所在函数确定映射,不按文字匹配。
  F2:415 位于 `shape_get_intersection_area_quad`(301–456 行),528 位于 `shape_get_intersection_area`(457 行起)。
  F3:S3R4 把前一个函数改名为 `static shape_get_intersection_area_quad_st`(303–465 行),并在 466 行新增同名包装。
  因此 F2:415 → F3:418,状态 MODIFIED_BY_FIX(所在函数被修复改名,其后新增 NULL 检查);F2:528 → F3:545,状态 SHIFTED(528 不在修复范围内,U90)。
  这两个站点都是 U38 分类清单中的项,不是任何 R7 或 S3R4 脚本的断点或注入锚点("no anchor is in pattern.c",LINEMAP_M3_R7)。
  映射结果必须由脚本按函数范围算出,不得手写。
- U146:fmm_FFT.cpp:98 → F3:101、fmm_kottke.cpp:102 → F3:105,状态 MODIFIED_BY_FIX:是同一个 Pattern_DiscretizeCell 调用,修复后检查返回值是否为 −12(U94、U96)。
  这两处不是任何脚本的断点锚点。调用次数是否不变,以 §5 用函数名断点 Pattern_DiscretizeCell 测得的序列为准。
- U147:映射状态增加 MODIFIED_BY_FIX,且只允许用于 U145、U146 点名的 3 个站点。脚本须逐项核实以下三点,任一不成立就判 MISSING 并停止:
  (i) F3 的这一行落在 `git diff -U0 a07b5ac 8d8202a` 的某个 + 段内,或紧邻该段;
  (ii) F2 这一行的核心表达式(调用或 malloc 表达式,不含前导赋值)是 F3 这一行的子串;
  (iii) F3 这一行所在函数与 U145、U146 规定的函数一致。
  新增列 anchor_use,取值:GDB_LINE_BP(某个 gdb 文件以 `文件:行号` 引用这一行,写出 gdb 文件名与行号)或 CLASSIFICATION_ONLY。
  映射还须纳入 `testing/d003/stage_s4/r6_plan14_caller.gdb` 的 fmm_FFT.cpp:90 与 fmm_kottke.cpp:94。
- U148:动态映射允许且只允许一处改名等价:F2 帧名 `shape_get_intersection_area_quad` ≡ F3 帧名 `shape_get_intersection_area_quad_st`。
  序列比较给出两种状态:IDENTICAL(原样相同),或 IDENTICAL_AFTER_RENAME(只应用这一条改名后相同);按 U140,两者都算可以照搬期望。其余一律 DIFFERENT,停下。
  序列只保留帧名(#0 被计数的函数、#1 调用者),去掉地址、参数与 `文件:行号`(F2 与 F3 的行号本来就不同)。
- U149:M1a 报告的缺陷,记为 E8-23 至 E8-26。M1a 报告文件不改,更正只写在 ERRATA_8 与续1 报告中:
  (a) E8-23:M1a 报告 §2 写"已追加到 RULINGS.tsv",实际未追加(`grep -c U137` 结果为 0),与对话中的说法也矛盾。本轮补追加。
  (b) E8-24:LINEMAP_F2_F3_R8_M1a.tsv 中 FFT 与 kottke 两个站点的出处写成"r5_rnv1_malloc_count.gdb comment",是错的
      (那段注释引用的是 pattern.c 的 1477、1481、1656、1660 行)。正确出处是 `registries/s4r7/PATTERN_MALLOC_CLASS_R7.tsv` 的 415 行与 U94。
  (c) E8-25:RUNNER_DIFF_R8_M1a.txt 未生成;recheck_s4r7_r8m1.py 与两个 gate_allow 文件没有 PRERUN 记录行。本轮补做,补记行标明"补记(运行后)"。
  (d) E8-26:M1a 有 22 条内联命令超出白名单,UTC 未记录,接受为已披露的表二事件。本轮按 §1 逐条记录。
- U150:门禁更正(规划者疏漏,E8-27):
  (a) registries/s4r8/SHA256SUMS.txt 中 ERRATA_8.txt 那一行是活文件快照。核对方法:对 ERRATA_8.txt 的前 13990 字节计算 sha256,
      应等于 72dc6aedfe698022727c7871a643a354dfa245c495d5346405b42c9ba01a1551(前缀检查);其余 24 行用 `sha256sum -c` 从 stdin 校验,全部 OK。
  (b) M1a 任务书中 gate4 的 end 模式在提交前检查 HEAD^,按 §8 的顺序必然失败。改为:end 门禁在提交前运行,检查 HEAD 仍为 e2589cb;
      提交后的 HEAD^ 与提交信息由收尾脚本写入 FINAL_GIT_R8_M1a2.txt。
  (c) gate4_r8m1.sh 不改,作为 M1a 已运行的记录保留。本轮新建 gate5_r8m1a2.sh(复制 gate4 后修改),允许列表为新的数据文件 gate_allow_r8m1a2_{start,end}.txt。
- U151:r6dnv1-F3-dbg 驱动在 M1a 中未链接,本轮补链接,只用于 §5 的 RNV1 窗口映射。
  链接命令复制自 link_drivers_s4r7.sh 的 r6dnv1 dbg 段,库为 R8 的 F3 dbg 库(56f72c58…);写 link_r6dnv1_dbg_r8m1a2.sh。

## 3. 门禁 gate5_r8m1a2.sh
- 参数与输出格式同 gate4。开工输出 `GATE_R8_M1a2.txt`,收尾输出 `GATE_R8_M1a2_END.txt`。
- start 模式检查以下各项:
  · HEAD = e2589cbc2b470ae88286d582ee62699e7c0d9e4c;HEAD:S4、8d8202a:S4、a07b5ac:S4 三个树哈希;S4 diff 恰为 4 个文件(LC_ALL=C sort);
  · 判定器 sha256;REGISTRY_S3R4C3_D.tsv 的 sha256;registries/s4r8 清单按 U150(a) 核对;registries/s3r4c5 清单全部 OK;
    registries/s4r7 用 recheck_s4r7_r8m1.py 核对(输出用新文件名,fails=0);
  · M1a 未提交文件的 sha256 与下表一致(任一不符,FAILS +1):
    P05_S4R8_REPORT_M0.md 1fc08a1f5dbf1340d3500979980a4f808b141515c8e1814c23da796e7deb0a0f
    P05_S4R8_REPORT_M1a.md 2b1c2de19a39c7e44c6cea75e55963bb5995849ee1d19a77d1ad7b2248676c04
    briefs/P05_S4R8_BRIEF_M1a.md a84da018b782f52e73a533d79d2224058e48d924bf817df869a94e5656686ec3
    registries/s4r8/ERRATA_8.txt 6e134abadbc86ffe24ce4f3bb156f8c7290c107369af289094b675e4b4498f22(本轮追加之前的值;20474 字节)
    stage_s4r8/gate4_r8m1.sh ae80a3c176cb6121c486df9fb36cd795552de8913cef8fcefdebdea700d3bece
    stage_s4r8/map_f2_f3_r8m1.py 746f5eb5e68835d658e842fbefa21740587b2f1a244d32860bc24d363b57e2e4
    stage_s4r8/gate_allow_r8m1a_start.txt 7df7f53e43208d0df9838a1a8eaaa8970e5e9abeb77a81511351deb57ba77128
    stage_s4r8/gate_allow_r8m1a_end.txt c0a0621cb2deb9457fe2a4f7583bb4444917ab56d6e57fe94931ac6ffc9031dc
    (其余 11 个 *_r8m1.* 脚本:在门禁中记录当前 sha256,不做比较);
  · git status 每一行都在允许列表内。start 允许列表:
    ` M checkpoints/p05/P05_S4R8_REPORT_M0.md`、` M checkpoints/p05/registries/s4r8/ERRATA_8.txt`、
    `?? checkpoints/p05/P05_S4R8_REPORT_M1a.md`、`?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a.md`、
    `?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT1.md`、`PREFIX ?? testing/d003/stage_s4r8/`;
  · /tmp 快照。
- end 模式(提交前运行):HEAD 仍为 e2589cb;HEAD:S4 不变;ERRATA_8 的前 20474 字节 sha256 等于 6e134abadbc8…(只追加);
  RULINGS.tsv 相对 HEAD 只追加(HEAD 版本是新文件的字节前缀);status 只含 end 允许列表中的项;/tmp 快照与开工时相同。
  end 允许列表在 start 允许列表的基础上增加:` M checkpoints/p05/STATE.md`、` M checkpoints/p05/registries/RULINGS.tsv`、
  `?? checkpoints/p05/P05_S4R8_REPORT_M1a_CONT1.md`、`PREFIX ?? checkpoints/p05/registries/s4r8/M1a/`。
- FAILS 必须为 0。

## 4. 补做与映射 v2
4.1 runner_diff_r8m1a2.sh:对 M1a 与本轮全部复制品,逐个与原件做 `diff -u`,输出 `$EV/RUNNER_DIFF_R8_M1a.txt`(补做,E8-25)。
    清单为:复制品、原件、哪些改动属于 M1a 任务书 §1 允许的类别。§1 允许类别以外的改动,逐条写入 E8-28 并说明理由。
    diff 返回 1 是预期结果,不算失败。
4.2 PRERUN 补记:recheck_s4r7_r8m1.py、gate_allow_r8m1a_start.txt、gate_allow_r8m1a_end.txt 各补一行,标明"补记(运行后)",同时记录当前 grep 命中数。
4.3 map_f2_f3_r8m1a2.py(新文件;复制 map_f2_f3_r8m1.py 后修改,原件不改):
    · 站点表修正出处(U149(b));加入 r6_plan14_caller.gdb 的 fmm_FFT.cpp:90 与 fmm_kottke.cpp:94;
    · 另外由脚本扫描 testing/d003/stage_s4、stage_s4r7、stage_s3r4c2、stage_s3r4c3 下全部 *.gdb 与 *.py,
      找出 `break <文件>:<行号>`、`tbreak <文件>:<行号>`、`LineBP("<文件>:<行号>"`、`gdb.Breakpoint("<文件>:<行号>"` 四种形式,全部纳入映射,anchor_use 记为 GDB_LINE_BP;
    · 加入"所在函数"列:由脚本解析两棵树中各站点所在的顶层函数(用花括号深度为 0 的函数头,写出解析规则);
    · 状态规则:文字唯一且所在函数同名(或属于 U145 的改名)→ SAME_LINE/SHIFTED;U145、U146 的 3 个站点按 U147 核实后 → MODIFIED_BY_FIX;
      文字出现多处时,按所在函数消歧,消歧后仍不唯一 → AMBIGUOUS;找不到 → MISSING。
    · 输出 `LINEMAP_F2_F3_R8_M1a2.tsv`。期望:MISSING 0、AMBIGUOUS 0、MODIFIED_BY_FIX 恰为 3;
      415→418(MODIFIED_BY_FIX)、528→545(SHIFTED)、FFT 98→101、kottke 102→105、S4.cpp 2413→2422、fmm_PolBasisJones.cpp 192→192。
      先把期望写入 `EXPECT_LINEMAP_R8_M1a2.txt`,记录 sha256 后再运行。
    · 映射用到的 gdb 行断点如果属于 M1b/M1c 要运行的组,在报告中写明:M1b/M1c 中这些断点用 F3 行号的复制品,不改原件。

## 5. 动态映射(M1a 任务书 §6.2,按本节更正执行)
5.1 先列计数族:counted_families_r8m1a2.py 只读 registries/s4r7 中 M1b/M1c 各组的预注册与 ADD 表,以及 S3R4 的 A、B、POLY 登记表,输出 `COUNTED_FAMILIES_R8_M1a2.tsv`。
    列为:组、请求种类(S4FMM_INJECT 的取值前缀)、是否按次数计数(NTH、`:N`、窗口 M、init:N、win:M)、被计数的函数(依据注入器源码的 文件:行号)、
    涉及的 (模式, NG, 驱动族) 组合数、来源表:行。
    不按次数计数的种类写 N/A,预注册中对应行的 callseq_status 也写 N/A。
    凡是从注入器源码定不出被计数函数的种类,写 UNMAPPED。UNMAPPED 的行在 dry-run 中会判 fail,按 §1 ⑧ 停下。
5.2 gdb 命令文件(用 write 写入 stage_s4r8/,只用函数名断点):对每个被计数函数各写一个,格式参照 gdb_malloc_lines_r7.gdb(`break <函数>`、`commands`、`silent`、`bt 2`、`continue`)。
    Pattern_DiscretizeCell 计数(U146)用 b_map_c3.gdb 或 a1map_c2.gdb 的做法。
5.3 callseq_r8m1a2.py:用 F2 与 F3 的 dbg 驱动(F2:drivers_r7/*-F2-dbg 与 S3R4 的 F2 驱动;F3:drivers_r8m1/*-F3-dbg 与 U151 的 r6dnv1-F3-dbg),
    对 5.1 列出的每个组合**无注入**各跑一次。环境由 matrix_r2.build_env 与 expected_env_independent_r7 的规则推导,
    不设置 S4FMM_INJECT,也不设置 S4FMM_NTH。每次运行以 `env -i PATH="$PATH" …` 启动,gdb 原始输出写入 `$EV/callseq_r8m1a2/`。
    提取 (#0 帧名, #1 帧名) 有序序列,按 U148 规则归一。
    输出 `CALLSEQ_F2_F3_R8_M1a2.tsv`:组合、计数族、F2 序列 sha256、F3 序列 sha256、F2 长度、F3 长度、状态(IDENTICAL / IDENTICAL_AFTER_RENAME / DIFFERENT)、
    gdb rc 与驱动 rc。
    gdb rc 或驱动 rc 不为 0 时,该行记为 RUN_ERROR,并停止。
    运行前先写 `EXPECT_CALLSEQ_R8_M1a2.txt`,记录 sha256。期望写:全部为 IDENTICAL,或 IDENTICAL_AFTER_RENAME(仅限多边形组合)。
    依据:[源码] F2→F3 的非注释改动只有失败返回处与 415 所在函数的改名。
5.4 `CALLSEQ_ADDITIONS_R8_M1a2.tsv`:按 M1a 任务书 §6.2 末条,核对 init-F3 与 polyinj-F3 在 22 行新增的 K 值上的序列,与 S3R4 C2、C3 的映射记录一致。
    S3R4 的 A1 映射口径(K=7/8 对 K0=6/7)按原样引用,不重新解释。

## 6. 预注册、dry-run、M1b/M1c 运行器
- 按 M1a 任务书 §7 执行,文件名不变(REGISTRY_S4_PRE_R8_M1b.tsv、REGISTRY_S4_PRE_R8_M1c.tsv、PREREG_COUNTS_R8_M1a.tsv、PREREG_RECORD_R8_M1a.txt、
  DRYRUN_R8_M1a.txt;这些在 M1a 中都没有生成,不存在覆盖问题)。生成器写作 make_prereg_r8m1a2.py,dry-run 脚本写作 dryrun_r8m1a2.py,
  运行器写作 run_m1b_r8m1a2.py 与 run_m1c_r8m1a2.py。
- callseq_status 取自 CALLSEQ_F2_F3_R8_M1a2.tsv;不按次数计数的行写 N/A。
  dry-run 只接受 IDENTICAL、IDENTICAL_AFTER_RENAME、N/A 三种值。
- 环境推导、比较规则与期望来源照 U139 与 U142。期望只能由脚本从已提交的 registries 表生成。
  预注册写完立即记录 sha256 与 UTC;之后要改,只能新建 *_ERRATA*.txt。

## 7. 记录提交(本轮唯一一次提交,在 §3–§6 全部完成后做)
- 小表复制到 registries/s4r8/M1a/(先确认全部输入存在)。范围:M1a 任务书 §8 列出的表,加上本轮的 GATE_R8_M1a2*.txt、LINEMAP_F2_F3_R8_M1a.tsv(M1a 原件)
  与 LINEMAP_F2_F3_R8_M1a2.tsv、EXPECT_LINEMAP、COUNTED_FAMILIES、EXPECT_CALLSEQ、CALLSEQ_*_M1a2、RUNNER_DIFF、DRIVERS_R8_M1a*.tsv、NEEDS、STRIP_EQUIV_*。
  在该目录写 SHA256SUMS.txt,`sha256sum -c` 全部 OK,并逐个 cmp 副本与原件。超过 1 MB 的文件不复制,只记 sha256,并写入 E8。
- 写 `$EV/SHA256SUMS_M1a.txt`,覆盖 M1a 与本轮新增的非二进制证据。
- STATE.md 用 edit 修改,保持一页以内。当前轮次写:"P05-S4 R8 M1a(准备,含续1):strip 等价关闭 E8-9;静态映射 …(MODIFIED_BY_FIX 3);
  动态映射 … 组合,IDENTICAL x / AFTER_RENAME y;预注册 M1b x 行、M1c y 行;dry-run ok …;下一步 M1b(待用户审核)"。
  关键数字表加 R8 M1a 一行;开放问题表中 E8-9 一行改为已关闭。
- 续1 报告依次写:门禁;U137–U151;补做(4.1、4.2);映射 v2;计数族;动态映射;预注册计数;dry-run;STATE 变更;违规两张表(逐条写 UTC);
  内联命令自查(逐条原文与 UTC);待用户裁决(没有就写"无")。每项只写"完成""未完成(原因)""不可行(依据)"之一。
- 先运行 gate5 end,FAILS=0 后再运行 commit_rec_r8m1a2.sh。脚本逐个 git add 下列文件,不用 -A 或 `.`:
  RULINGS.tsv、ERRATA_8.txt、STATE.md、P05_S4R8_REPORT_M0.md、P05_S4R8_REPORT_M1a.md、P05_S4R8_REPORT_M1a_CONT1.md、两份 briefs、
  registries/s4r8/M1a/ 下的全部文件、stage_s4r8/ 下 M1a 与本轮新增的全部文件(add 前与门禁记录的 sha256 核对)。
  提交信息:`P05-S4 R8 M1a prep on F3 (incl. cont1): dbg strip equivalence closes E8-9, drivers, F2-F3 line map v2 (MODIFIED_BY_FIX per U145-U147) and call-sequence map, M1b/M1c pre-registration, dry-run; rulings U137-U151; M0 report wording (U137). awaiting user review`
- 提交后,用脚本把真实的 `git log -3 --oneline`、`git rev-parse HEAD^`、`git log -1 --format=%s`、`git status --short` 写入 `$EV/FINAL_GIT_R8_M1a2.txt`,
  并在对话中原样贴出。HEAD^ 应为 e2589cb,status 应为空。提交后不再修改任何已跟踪文件。
- 中途按 §1 停止时不提交;报告写到停止处为止,未提交文件的 sha256 写入报告,供下一轮门禁使用。

## 8. 不停但要记录的情形
- 驱动 sha256 为 DIFFERENT(库与告警相同);FIRST_RECORD;映射中 CLASSIFICATION_ONLY 站点的行号变化。
- M1a 范围以外的事一律不做,尤其不得运行任何注入。
- 结尾只写"本轮已完成 R8 M1a 范围,等待用户审核"或"本轮未完成 R8 M1a 范围,等待用户审核"。
