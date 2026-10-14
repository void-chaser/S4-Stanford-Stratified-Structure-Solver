# P05-S4 R8 M1a 续2:裁决续1 停止项,映射 v3(修正函数解析),动态映射,记录提交

你是 P05-S4 的验证执行者。本轮是 P05-S4 R8 M1a 的续2,不是新阶段,不得出现 P05-S6。不得宣布任何阶段完成或签收;报告与 STATE 不写签收建议。
不修改 S4/。不修改 testing/d003/ 下已提交的文件。M1a、续1 已生成但尚未提交的文件一律不改,原样随本轮提交入库;更正只写新文件和 ERRATA_8(只追加)。
**本轮不做任何注入运行。** 只允许 §5 的无注入映射运行(gdb,只设函数名断点)。预注册、dry-run 和运行器移到续3(U159)。

## 0. 开工
- 第一步:用 write 把本任务书原文(含附录 A)存为 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT2.md`。
- 第二步:用 write 把附录 A(续1 停止报告原文)存为 `checkpoints/p05/P05_S4R8_REPORT_M1a_CONT1.md`,文件开头加一行:
  "本文件由续2 按 U152 补写:正文为续1 执行者在对话中的停止报告原文,未改动;续1 停止时未生成本文件(E8-31)。"
- 只读:AGENTS.md;STATE.md;`briefs/P05_S4R8_BRIEF_M1a.md`;`briefs/P05_S4R8_BRIEF_M1a_CONT1.md`(下称"续1 任务书";本任务书未改动的条款仍按它执行);
  `registries/s4r8/ERRATA_8.txt`;`evidence/p05-s4r8/LINEMAP_F2_F3_R8_M1a2.tsv`、`EXPECT_LINEMAP_R8_M1a2.txt`、`RUNNER_DIFF_R8_M1a.txt`、`PRERUN_CHECKS_R8_M1a.txt`;
  `testing/d003/stage_s4r8/map_f2_f3_r8m1a2.py`、`gate5_r8m1a2.sh`;`registries/s4r7/LINEMAP_M3_R7.tsv`;续1 任务书 §5 点名的全部文件。
- **读完直接写脚本**,不用内联命令预先核对。
- 证据目录沿用 `checkpoints/p05/evidence/p05-s4r8/`,已有文件不删、不改、不覆盖。新文件名带 `_M1a3`(证据)或 `_r8m1a3`(脚本)。
  小表放 `checkpoints/p05/registries/s4r8/M1a/`。本轮报告:`checkpoints/p05/P05_S4R8_REPORT_M1a_CONT2.md`。ERRATA_8 从 E8-31 起追加。

## 1. 写入方式、内联命令与停止条件
- 写入方式照 RESTART2 §1 U132(a)–(e)、M1a 任务书 §1、续1 任务书 §1。shell 脚本首段逐字为
  `REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"`。
  Python 一律 `python3 -I -B`。gdb 命令文件与数据文件用 write 工具写入 `testing/d003/stage_s4r8/`。
- **内联 bash(U157,取代以前的白名单)**:只允许下面 4 种,不允许其他任何形式:
  (1) `date -u +%Y-%m-%dT%H:%M:%SZ; sh testing/d003/safe_run.sh p05-s4r8 -- <命令>; date -u +%Y-%m-%dT%H:%M:%SZ`
  (2) `date -u +%Y-%m-%dT%H:%M:%SZ; git status --short; date -u +%Y-%m-%dT%H:%M:%SZ`
  (3) `date -u +%Y-%m-%dT%H:%M:%SZ; git rev-parse HEAD HEAD:S4; date -u +%Y-%m-%dT%H:%M:%SZ`
  (4) `date -u +%Y-%m-%dT%H:%M:%SZ; sha256sum <仓库内文件…>; date -u +%Y-%m-%dT%H:%M:%SZ`
  这样每条命令的 UTC 都留在输出里,报告的"内联命令自查"逐条抄写原文与前后两个 UTC。
  查看文件用 read,找文件用 glob,搜索用 grep 工具。`ls`、`echo`、`cut`、`sed`、`cat`、`2>&1`、管道都不用;其余需求写成脚本。
- 每个脚本与数据文件运行前用 grep 工具查禁止项正则,0 行后经 `prerun_log_r8m1.sh` 记录(仍写入 `$EV/PRERUN_CHECKS_R8_M1a.txt`,只追加)。
- **顺序硬规则**:§2 的 RULINGS/ERRATA 追加必须在 §3 start 门禁 FAILS=0 之后进行(E8-34)。
- 停止条件:M1a 任务书 §1 的 ①–⑤;续1 任务书 §1 的 ⑦'、⑩;再加上:
  ⑪ 映射 v3 的解析器自检(§4.2)有 BAD;
  ⑫ 映射 v3 的结果与 `EXPECT_LINEMAP_R8_M1a3.txt` 不一致,或 diff 偏移交叉核对(§4.3)有 DISAGREE;
  ⑬ 函数名断点符号核对(§4.4)有 MISSING 或 MULTIPLE。
- 停止时按 U158 处理:报告写到停止处,仍运行 end 门禁;FAILS=0 就做记录提交,提交信息开头改为 `P05-S4 R8 M1a cont2 (stopped at §x): …`。

## 2. 用户裁决(门禁通过后追加到 RULINGS.tsv,status `生效`,来源"R8 M1a 续2 任务书 §2";同时追加到 ERRATA_8)
- U152:续1 在 §4.3 按 ⑥' 停止,处理正确,没有为消除 AMBIGUOUS 自行改规则。接受续1 的已完成部分:GATE_R8_M1a2_R2(FAILS=0)、U137–U151 追加、
  RUNNER_DIFF_R8_M1a.txt、PRERUN 补记、EXPECT_LINEMAP_R8_M1a2.txt、LINEMAP_F2_F3_R8_M1a2.tsv(停止记录,不改)、F2_S4.cpp.txt。
  续1 停止时未写报告文件(E8-31),本轮按附录 A 补写。
- U153:S4.cpp:4334 的 AMBIGUOUS 有两个原因。
  (a) 规划缺陷:续1 §4.3 把 stage_s4 下全部 gdb 都纳入扫描,收进了 R5 历史脚本 r5_plan_twice*.gdb;R7、S3R4、R8 的运行器与登记表都不引用它们;
  (b) 规划缺陷加脚本缺陷:任务书没有规定解析器要处理块注释和字符串,v2 只去掉了 `//`。S4.cpp 2914 行之后的字符串含 `{`,导致 4210 等行的所在函数判错。
  处置:4334 保留在映射中,不排除;新增列 used_in_m1(见 U154(d))。映射 v3 按 U154 规则得到的结果是 F3:4343,所在函数 S4_Simulation_GetFieldPlane,状态 SHIFTED。
  这一期望受 v2 结果和规划者只读复算影响,状态写 INFLUENCED。
- U154:映射 v3 的规则(新文件 map_f2_f3_r8m1a3.py,复制 map_f2_f3_r8m1a2.py 后修改,原件不改):
  (a) 解析前先把源码"抹空":`//` 注释、`/* */` 块注释、字符串字面量、字符字面量(处理 `\` 转义)中的字符换成空格,保留换行;
      以 `#` 开头的预处理行不参与函数头识别。花括号深度只在抹空后的文本上计算。
  (b) 解析器自检:5 个文件(S4.cpp、pattern.c、fmm_FFT.cpp、fmm_kottke.cpp、fmm_PolBasisJones.cpp)在两棵树中各解析一遍,
      文件末尾深度为 0,且深度从不小于 0。另核对下列所在函数(取自 [源码]):
      F2:S4.cpp 4210、4334 → S4_Simulation_GetFieldPlane;2413 → Simulation_ComputeLayerModes;
      F3:S4.cpp 4219、4343 → S4_Simulation_GetFieldPlane;2422 → Simulation_ComputeLayerModes;
      F2 pattern.c 415 → shape_get_intersection_area_quad;528 → shape_get_intersection_area;1253 → cg;
      F3 pattern.c 418 → shape_get_intersection_area_quad_st;545 → shape_get_intersection_area;1279 → cg。
      结果写入 `PARSER_SELFCHECK_R8_M1a3.tsv`(OK/BAD)。
  (c) diff 偏移交叉核对:从 `git diff -U0 a07b5ac 8d8202a -- <文件>` 的 hunk 头计算累计偏移。对不在任何 "-" 段内的 F2 行,F3 行 = F2 行 + 累计偏移。
      每个非 MODIFIED_BY_FIX 站点都必须与按文字/函数得到的 F3 行一致(AGREE),否则记 DISAGREE。
      MODIFIED_BY_FIX 的 3 个站点不做这项核对,仍按 U147 核实。
  (d) 新增列:used_in_m1 = YES(写出引用它的 R7/S3R4/R8 运行器或登记表的 文件:行)或 NO(写"无引用",并写出所查的目录:
      stage_s4r7、stage_s3r4c2、stage_s3r4c3、stage_s4r8、registries/s4r7、registries/s3r4c2、registries/s3r4c3);
      diff_offset_check = AGREE / DISAGREE / N/A(MODIFIED_BY_FIX)。
- U155:LINEMAP_M3_R7.tsv Part A 把 S4.cpp 第 23、32 行写成 Simulation_ComputeLayerModes、Simulation_GetLayerSolution 的声明行。
  [源码] 这两行实际是 `#include "S4.h"` 与 `# include <TBLAS_ext.h>`;两个函数的声明在 218、214 行,F2 中的定义在 2250、1778 行。
  这些断点按函数名设置,不影响 R7 的结果;R7 文件不改,记为 E8-33。
  映射 v3 对 Part A 的函数名断点(r6_probe、Simulation_ComputeLayerModes、Simulation_GetLayerSolution、S4_Simulation_GetFieldPlane)
  另做符号核对:在 F2 与 F3 中各恰有一个定义(函数头所在行),写入 `FUNC_BP_SYMBOLS_R8_M1a3.tsv`(符号、文件、F2 定义行、F3 定义行、PRESENT/MISSING/MULTIPLE)。
  期望:Simulation_GetLayerSolution 1778→1787、Simulation_ComputeLayerModes 2250→2259、S4_Simulation_GetFieldPlane 4210→4219,
  r6_probe 在驱动源码 73→73(驱动源码在两棵树中相同)。
- U156:E8-28 补全(以"E8-28(补全)"为标题追加,不改原占位行)。根据 RUNNER_DIFF_R8_M1a.txt,逐对列出 M1a 任务书 §1 允许类别以外的改动并给出理由。至少包括:
  strip_equiv_r8m1.sh 删去驱动比较对(由 U141"只比较库"要求,归为"裁决要求");
  link_drivers_r8m1.sh 的 link() 改了参数结构,并新增输入存在检查与拒绝覆盖;
  gate4、gate5 新增的检查段;recheck_s4r7_r8m1a2.py 改动的接受文件名。
  只记录,不重跑;链接产物的有效性以 M1a 已记录的 sha256 与告警为准。
- U157:续1 的表二事件记为 E8-34:(a) 门禁之前先追加 RULINGS,后撤回,门禁通过后重做;
  (b) 超出白名单的内联命令未记录 UTC,与 E8-26 同类重复。接受为已披露。从本轮起按 §1 的 4 种形式执行。
- U158:停止时也做记录提交:报告写到停止处,end 门禁 FAILS=0 后提交。目的是避免未提交文件跨轮累积。
- U159:M1a 剩余工作拆分。续2 = 映射 v3 + 续1 §5 的动态映射 + 记录提交;
  续3 = 预注册、PREREG_COUNTS、dry-run、M1b/M1c 运行器(按续1 任务书 §6),以及 M1a 收尾。
  续1 §5 的文件名把 `_M1a2`/`_r8m1a2` 换成 `_M1a3`/`_r8m1a3`;U151 的链接脚本改名为 `link_r6dnv1_dbg_r8m1a3.sh`,内容要求不变。

## 3. 门禁 gate6_r8m1a3.sh(复制 gate5_r8m1a2.sh 后修改;gate5 不改)
- 允许列表放在新数据文件 `gate_allow_r8m1a3_{start,end}.txt`。输出:开工写 `GATE_R8_M1a3.txt`,收尾写 `GATE_R8_M1a3_END.txt`。
- start 模式:
  · HEAD = e2589cbc2b470ae88286d582ee62699e7c0d9e4c;三个树哈希与 S4 diff 4 个文件同 gate5;判定器 sha256;
    REGISTRY_S3R4C3_D.tsv;registries/s4r8 清单按 U150(a) 核对;s3r4c5 清单;s4r7 用 recheck_s4r7_r8m1a2.py 核对(新输出名,fails=0);
  · ERRATA_8.txt 的前 13990 字节 sha256 = 72dc6aedfe698022727c7871a643a354dfa245c495d5346405b42c9ba01a1551;
    前 20474 字节 = 6e134abadbc86ffe24ce4f3bb156f8c7290c107369af289094b675e4b4498f22;
    全文(本轮追加前,23046 字节)= 93b2aba6037d4b171e6b0c1f70d18fbbbc1d1b7e65b33bbd1ffff38e31f5a109;
  · RULINGS.tsv:HEAD 版本(48880 字节)是当前文件的字节前缀;当前全文(55304 字节)= a3030e47509a519213e46cd57b4170dbfbbb899269c1b2b3e1e3eb3eaef156df;
  · 下列未提交文件的 sha256(任一不符则 FAILS +1):
    P05_S4R8_REPORT_M0.md 1fc08a1f5dbf1340d3500979980a4f808b141515c8e1814c23da796e7deb0a0f
    P05_S4R8_REPORT_M1a.md 2b1c2de19a39c7e44c6cea75e55963bb5995849ee1d19a77d1ad7b2248676c04
    briefs/P05_S4R8_BRIEF_M1a.md a84da018b782f52e73a533d79d2224058e48d924bf817df869a94e5656686ec3
    briefs/P05_S4R8_BRIEF_M1a_CONT1.md debf29e1ff978450cb01e85120d347de05aeb469830ebe70689933628673bb76
    stage_s4r8/gate4_r8m1.sh ae80a3c176cb6121c486df9fb36cd795552de8913cef8fcefdebdea700d3bece
    stage_s4r8/map_f2_f3_r8m1.py 746f5eb5e68835d658e842fbefa21740587b2f1a244d32860bc24d363b57e2e4
    stage_s4r8/gate_allow_r8m1a_start.txt 7df7f53e43208d0df9838a1a8eaaa8970e5e9abeb77a81511351deb57ba77128
    stage_s4r8/gate_allow_r8m1a_end.txt c0a0621cb2deb9457fe2a4f7583bb4444917ab56d6e57fe94931ac6ffc9031dc
    stage_s4r8/gate5_r8m1a2.sh 4824e584291d08e76217d5636c8683c72b92ad6d68c74f7db163947ccdf14230
    stage_s4r8/gate_allow_r8m1a2_start.txt 04ce8778d414157807cbb3213f3e81d12b226bc3bff3c04d9f76f41a5a4861af
    stage_s4r8/gate_allow_r8m1a2_end.txt 7daf90aceb3b66f07cafd659608c0906e7becb98d43e35749cea11f195e31b16
    stage_s4r8/map_f2_f3_r8m1a2.py 8e4910b8b9fb848a8e88f58086551ea77c3dbd9b042d6bc992bc4bdf842582da
    stage_s4r8/recheck_s4r7_r8m1a2.py b6db2d12cadc9def3fb49c7d01dbaedc697829d1bf8b663a9ef8bf72b89e5c51
    stage_s4r8/runner_diff_r8m1a2.sh 58c6296ed77b5cd907e8ed54da6a34f91f525955669235530796fc757e02f32b
    stage_s4r8/export_f2_s4cpp_r8m1a2.sh 66ba39e9715ef9693c82e9100a8dfd6a5213c9daa75f2b036f37e2349d0e47b2
    evidence: LINEMAP_F2_F3_R8_M1a2.tsv 9888edb28a5e2006445be68433fb5f2a5fc8282e44c7bfdecd2cdc1d66ad8757
              EXPECT_LINEMAP_R8_M1a2.txt bf71ccdce7bb3e4d569119dc785d35d7103d2bffc93ed1b724f6380c1ac2e24b
              GATE_R8_M1a2.txt 4d4b51b60b1b72c5152a8fcee94373ff38cf3fc55ef1de563b2c43765aaa5454
              GATE_R8_M1a2_R2.txt 155ecbfd3c3d3e2435409253022905b58683f51327f339e7ae1caf740213339e
              RUNNER_DIFF_R8_M1a.txt 119722a7f7349acc19fbe45b5fd34bd57a587dccae184475e5e5db1f2ef79283
              F2_S4.cpp.txt e287fbc70025e2dcda66c3aa3e9b48df585a4e279c3fcd7620eb19003880ce87
    PRERUN_CHECKS_R8_M1a.txt 是只追加文件:前 1926 字节 sha256 应为 38e3f1652908aa080c20218dd1439270c5a884c5cd98abe0c082f56e6976e248。
    其余 *_r8m1.* 脚本只记录当前 sha256,不做比较。
  · start 允许列表:
    ` M checkpoints/p05/P05_S4R8_REPORT_M0.md`、` M checkpoints/p05/registries/RULINGS.tsv`、` M checkpoints/p05/registries/s4r8/ERRATA_8.txt`、
    `?? checkpoints/p05/P05_S4R8_REPORT_M1a.md`、`?? checkpoints/p05/P05_S4R8_REPORT_M1a_CONT1.md`、
    `?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a.md`、`?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT1.md`、`?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT2.md`、
    `PREFIX ?? testing/d003/stage_s4r8/`;
  · /tmp 快照。
- end 模式(提交前运行):HEAD 仍为 e2589cb;HEAD:S4 不变;ERRATA_8 前 23046 字节 = 93b2ab…(只追加);RULINGS 前 55304 字节 = a3030e…(只追加);
  status 只含 end 允许列表中的项;/tmp 快照与开工时相同。end 允许列表在 start 的基础上增加:
  ` M checkpoints/p05/STATE.md`、`?? checkpoints/p05/P05_S4R8_REPORT_M1a_CONT2.md`、`PREFIX ?? checkpoints/p05/registries/s4r8/M1a/`。
- FAILS 必须为 0。

## 4. 映射 v3
4.1 先写期望 `EXPECT_LINEMAP_R8_M1a3.txt`(第一行写 `status INFLUENCED`,出处写"续2 任务书 U153–U155;v2 停止记录;规划者只读复算"),记录 sha256 后再运行脚本。内容:
    MISSING 0;AMBIGUOUS 0;MODIFIED_BY_FIX 3;PARSER_SELFCHECK BAD 0;DIFF_OFFSET DISAGREE 0;
    v2 期望中的 6 条原样保留;另加:S4/S4.cpp 4334 F3 4343 SHIFTED(S4_Simulation_GetFieldPlane;used_in_m1 NO);
    S4/S4.cpp 4210 F3 4219 SHIFTED(S4_Simulation_GetFieldPlane);U155 的 4 个符号全部 PRESENT,定义行如 U155 所写。
4.2 map_f2_f3_r8m1a3.py:按 U154 修改。站点表、gdb 引用扫描(四种形式、四个目录)与 v2 相同;FUNCTION_RULE 写进输出文件头。
    输出 `LINEMAP_F2_F3_R8_M1a3.tsv`、`PARSER_SELFCHECK_R8_M1a3.tsv`、`FUNC_BP_SYMBOLS_R8_M1a3.tsv`。
    脚本最后把结果与 EXPECT 逐项比较,写出 `LINEMAP_CHECK_R8_M1a3.txt`(MATCH/MISMATCH 逐项列出)。任一 MISMATCH 都按 ⑫ 停止。
4.3 写一份 `LINEMAP_V2_V3_DIFF_R8_M1a3.txt`:逐站点比较 v2 与 v3 的 F3 行号、所在函数与状态;只记录,不判。
    预期只有 4210、4334 两行(以及受块注释影响的其他所在函数列)有变化。
4.4 映射中 used_in_m1=YES 的 `文件:行号` 断点,报告写明:M1b/M1c 使用 F3 行号的复制品,不改原件(续1 §4.3 末条)。

## 5. 动态映射
- 照续1 任务书 §5.1–§5.4 执行,文件名按 U159 换成 `_M1a3`/`_r8m1a3`。U151 的链接脚本是 `link_r6dnv1_dbg_r8m1a3.sh`。
- 补充要求:
  · counted_families_r8m1a3.py 必须写出所读每个源表的 sha256;UNMAPPED 大于 0 就停下(写进停止原因,不做 dry-run)。
  · gdb 与驱动运行都经 safe_run;每次运行的命令行、开始与结束 UTC、gdb rc、驱动 rc 写入 `CALLSEQ_RUNS_R8_M1a3.tsv`。
  · 运行前先写 `EXPECT_CALLSEQ_R8_M1a3.txt` 并记录 sha256,内容照续1 §5.3。
  · 出现 DIFFERENT 时:先在报告中写出 [源码] 依据,说明它是否属于 S3R4 A1 映射的同一口径差异;不重新映射,停下(⑦')。

## 6. 记录与提交(U158;未停止时在 §4–§5 完成后进行,停止时在停止处进行)
- 小表复制到 `registries/s4r8/M1a/`(先确认全部输入存在):GATE_R8_M1a*.txt(含 M1a、续1 的停止记录)、gate_allow 各文件、PRERUN_CHECKS_R8_M1a.txt、
  STRIP_EQUIV_*_R8_M1a.*、NEEDS_R8_M1a.tsv、BUILD_OPTION_DIFF_R8_M1a.txt、DRIVERS_R8_M1a*.tsv、DRIVER_R6B_SEAM_R8_M1a.tsv、DRIVERS_S3R4_R8_M1a_F3.tsv、
  LINEMAP_F2_F3_R8_M1a.tsv、LINEMAP_F2_F3_R8_M1a2.tsv、EXPECT_LINEMAP_R8_M1a2.txt、本轮全部 *_M1a3.* 小表、RUNNER_DIFF_R8_M1a.txt、S4R7_RECHECK_R8_M1A*.tsv。
  不复制 F2_S4.cpp.txt,只记 sha256。超过 1 MB 的文件只记 sha256,并写入 E8。
  在该目录写 SHA256SUMS.txt,`sha256sum -c` 全部 OK,逐个 cmp 副本与原件。
- 写 `$EV/SHA256SUMS_M1a.txt`,覆盖 M1a、续1、续2 的非二进制证据。
- STATE.md 用 edit 修改,保持一页以内。当前轮次写:
  "P05-S4 R8 M1a(准备,续2):E8-9 已关闭;静态映射 v3 …(MODIFIED_BY_FIX 3,AMBIGUOUS 0);动态映射 … 组合,IDENTICAL x / AFTER_RENAME y;下一步 M1a 续3(预注册与 dry-run,待用户审核)"。
  关键数字表加 R8 M1a 一行;开放问题表中 E8-9 一行改为已关闭。
- 本轮报告依次写:门禁;U152–U159;续1 报告补写;E8-28 补全;映射 v3(自检、交叉核对、v2/v3 差异、符号核对);计数族;动态映射;STATE 变更;
  违规两张表(逐条写 UTC);内联命令自查(逐条原文与前后 UTC);待用户裁决(没有就写"无")。每项只写"完成""未完成(原因)""不可行(依据)"之一。
- 先运行 gate6 end,FAILS=0 后运行 commit_rec_r8m1a3.sh。脚本逐个 git add 下列文件,不用 -A 或 `.`,add 前核对 sha256 与门禁记录一致:
  RULINGS.tsv、ERRATA_8.txt、STATE.md、P05_S4R8_REPORT_M0.md、P05_S4R8_REPORT_M1a.md、P05_S4R8_REPORT_M1a_CONT1.md、P05_S4R8_REPORT_M1a_CONT2.md、
  briefs/P05_S4R8_BRIEF_M1a.md、_CONT1.md、_CONT2.md、registries/s4r8/M1a/ 下全部文件、stage_s4r8/ 下全部未跟踪文件(逐个列出)。
  提交信息:`P05-S4 R8 M1a prep on F3 (cont1+cont2): dbg strip equivalence closes E8-9, drivers, F2-F3 line map v3 (parser fix, MODIFIED_BY_FIX per U145-U147) and call-sequence map; rulings U137-U159; M0 report wording (U137). awaiting user review`
  (停止时按 U158 改开头。)
- 提交后用脚本把真实的 `git log -3 --oneline`、`git rev-parse HEAD^`、`git log -1 --format=%s`、`git status --short` 写入 `$EV/FINAL_GIT_R8_M1a3.txt`,
  并在对话中原样贴出。HEAD^ 应为 e2589cb,status 应为空。提交后不再修改任何已跟踪文件。

## 7. 不停但要记录的情形
- 驱动 sha256 DIFFERENT(库与告警相同);FIRST_RECORD;CLASSIFICATION_ONLY 或 used_in_m1=NO 站点的行号变化。
- 本轮范围以外的事一律不做,尤其不得运行任何注入,不得开始预注册。
- 结尾只写"本轮已完成 R8 M1a 续2 范围,等待用户审核"或"本轮未完成 R8 M1a 续2 范围,等待用户审核"。

## 附录 A:续1 停止报告原文
【在此粘贴续1 执行者的停止报告全文】
