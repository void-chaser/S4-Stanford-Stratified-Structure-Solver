# P05-S4 R7(P05-S4 的子轮次):F2 上的修复后回归

你是 P05-S4 的验证执行者。本轮是 P05-S4 的子轮次 R7,不是新阶段;不得出现 P05-S6。
不得宣布任何阶段完成或签收。本轮不修改 S4/(任何文件)。
先读 AGENTS.md、checkpoints/p05/STATE.md,再读:
checkpoints/p05/P05_S3R3_CLOSEOUT.md、checkpoints/p05/ERRATA_S3R3.txt、checkpoints/p05/registries/RULINGS.tsv、
checkpoints/p05/registries/s3r3/(全部)、checkpoints/p05/registries/s4r6d/RNV1_SOURCE_R6d.md、
checkpoints/p05/registries/s4r6d/RED_POINTS_LEDGER_R6d.tsv,以及第 7 节(R7 回归矩阵清单)列出的各轮报告与 registries。
证据目录:checkpoints/p05/evidence/p05-s4r7/;小型结果表:checkpoints/p05/registries/s4r7/;
报告:checkpoints/p05/P05_S4R7_REPORT.md;勘误:checkpoints/p05/registries/s4r7/ERRATA_7.txt(编号 E7-1 起)。
第一步:用 write 工具把本任务书原文存为 checkpoints/p05/briefs/P05_S4R7_BRIEF.md(原样,不改写),一并提交。
注意路径:registries 一律在 checkpoints/p05/registries/ 下,仓库根没有 registries/。

## 0. 硬规则
- 每条含写入的命令开头先执行:
  REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r7; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
  整条命令经 `sh testing/d003/safe_run.sh p05-s4r7 -- sh -c '<命令,含全部重定向>' sh ...` 运行。
  "含写入"包括 printf/grep/sha256sum/sed 的重定向、gdb 的 -batch 输出,以及写到 $EV/tmp 的临时文件。S3R3 有 5 类裸跑写入,本轮不得再有。
- 禁止 heredoc、sed -i、python -c、cat >、tee。报告、ERRATA、脚本只用 edit/write 工具写。
  出现一次就停下,写进报告。裸跑重定向(即使在合规路径下)累计 3 次也停下。
- 不得出现 /dev/null;写入目标只能是 $EV/、$REPO/testing/d003/stage_s4r7/(新目录)、$REPO/checkpoints/p05/。
- python 一律用 `python3 -I -B`;长输出带 head/tail;不做沙箱探测;judge_d003.py 只导入,不修改。
- 不覆盖任何证据或结果文件(U17)。gdb 日志、stdout、结果表的文件名都带 run 标签(run1、run2…);重跑一律新建文件。
- 历史运行器(testing/d003/stage_s4/、stage_s3r3/)不改。需要改路径或哈希的,复制到 testing/d003/stage_s4r7/
  并加后缀 _r7。每份副本与原件的 diff 写入 $EV/RUNNER_DIFF_R7.txt,只允许改树标签、库/驱动路径、sha256 常量、
  输出目录这几类行;出现其他改动,在 ERRATA_7 中逐条说明理由。

## 1. 用户裁决(写在 ERRATA_7.txt 开头,并追加到 RULINGS.tsv;原有行不改)
- U34:R7 在 F2(a07b5ac,S4/ 树 e124925f5b242486a913b813fa181664f665b048)上开工。R7 只做回归;
  U25/U29 指定给 R8 的项(阶段 e、I7、双目标注入、其他层失败变体、K-1、Python/Lua、NB=1–8、类别 C)本轮不做。
- U35:P05-S3 暂不签收。待 R7 里程碑(第 4 节)结果交用户后,由用户决定是否带范围声明签收。
- U36:S3R3 自检 A 中 vl/fftvl NG1 注入后的 rc 20 不另做路径拆分。按第 5.1 节离线整理成表。
- U37:RNV1 的点补上 jones、fftjones(F 与 F2 都跑);tri 分支补上 vl、jones。
- U38:pattern.c 中尚未分类的 malloc(415、528、806、1164;以 F2 实际行号为准)只做 [源码] 分类,不测试、不修复,交用户裁决。
- U39:STATE.md 中写成"去向 R7"的补测项按 U25 改为 R8(写 E7-1,不改历史报告)。
  STATE.md 第 10 行"开工基线 HEAD(R6c2)"改为本轮的开工 HEAD。

## 2. R7-0 门禁
新脚本 testing/d003/stage_s4r7/r7_gate.py,输出 $EV/GATE_R7.txt。逐项核对:
- HEAD = 8e13729635c20dc658abc2a35e8195b26e3b9bec(写完整哈希);
- git rev-parse HEAD:S4 = e124925f5b242486a913b813fa181664f665b048(F2);
- git rev-parse a07b5ac:S4 等于同一值;1c11905:S4 = 4a6f64927a30537740dd0c8f11f9a5aae5e46ba4(F);
- `git diff --name-only 1c11905 a07b5ac -- S4/` 只列出 S4/pattern/pattern.c 与 S4/S4_internal.h;
- judge_d003.py 的 sha256 = d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb;
- checkpoints/p05/registries/s3r3/SHA256SUMS.txt 与 registries/s4r6d/SHA256SUMS.txt 全部 OK;
- 工作区干净(只允许 briefs/P05_S4R7_BRIEF.md 与本轮 gate 脚本未跟踪);
- /tmp 顶层快照(条目数与 sha256)。
任一不符就停下。

## 3. R7-1 构建(从提交导出,不从工作区复制)
1. 用 git archive 把 a07b5ac 的 S4(及构建文件)导出到 $EV/trees/F2,把 1c11905 导出到 $EV/trees/F。
   逐文件 sha256 写入 $EV/TREE_MANIFEST_R7.tsv。核对 F2 导出与 S3R3 构建所用 F2 源码(S3R3 的 build/ 目录)逐字节一致;
   不一致就写 E7-x 并停下。
2. 两棵树都做 dbg 构建(-O0 -g,R5 方式)与 plain 构建(R4 方式),同一构建路径布局。
   记录实际编译命令行(确认没有 -DHAVE_LIBCHOLMOD)、告警数(应为 62/71)、库的 sha256。
   库哈希与 S3R3 不同时只记录,只比较结果,不比较字节。
3. seam 变体:用 R4/R6c 的 seam 应用方式在 F2 上重建 seamF2 与 fmmret-F2,dbg 方式与 R6c 一致。
   验证"seamF2 − F2"与"seamF − F"的 diff 完全相同,写入 $EV/SEAM_DIFF_F_vs_F2_R7.txt。不同就停下。
4. 驱动:为每个要回归的矩阵重新链接 F2 版本(以及必要时的 F 版本),
   在 $EV/DRIVERS_R7.tsv 记录 驱动名、树、库 sha256、驱动 sha256、链接脚本。

## 4. R7-2 预注册(全部写完、记录 sha256 与 UTC 时间后才能运行任何注入;状态 INFLUENCED)
文件 $EV/REGISTRY_S4_PRE_R7.tsv。每行至少包含:point_id、来源矩阵、来源结果文件、来源 sha256、来源行的类别、
F2 期望类别、期望依据。规则:
- 默认:F2 期望 = F 上已记录的类别,机械复制。来源文件及其 sha256 写在表头;复制脚本也提交。
- 例外只允许以下几类,每行写明 [源码] 依据:
  (a) RNV1 窗口内的注入点:F 为 CRASH,F2 期望 REPORTED_FAILURE;
  (b) 新增点(第 4.2 节),期望由 [源码] 推出,标明"无 F 实测"或"F 本轮实测";
  (c) 其他任何预期 F2 ≠ F 的点。原则上不应存在;若存在,运行前写进 ERRATA_7 交代原因。
- 状态类判定(R6c 177、seam 25)的期望是 I1–I6 全部 HOLD,判定方法与 R6c/R6c2 相同。
  RNV1 新增的 PolBasis 失败点如果纳入状态判定,单独标出,不混入 177。

4.1 需回归的矩阵(来源见 P05_S3R3_CLOSEOUT.md 第 7 节;每项两遍)
| 组 | 内容 | 来源 |
|---|---|---|
| G1 | R3 范围内 141 点(rc/信号/命中) | registries/s4r3/ |
| G2 | R4 矩阵、plancall、seam 25 点(plain 构建) | registries/s4r4/ |
| G3 | R5 M=2 36 点 | registries/s4r5/ |
| G4 | R6-1 twice NTH 12–16,S4FMM_TWICE=slab | registries/s4r6/ |
| G5 | R6c 177 点状态判定(I1–I6) | registries/s4r6c/RESULTS_R6c_STATE.tsv 等 |
| G6 | R6c seam 25 点状态判定 + U18 对照 18 行 | registries/s4r6c/RESULTS_R6c_SEAM.tsv 等 |
| G7 | RNV1 36 点(nv/vl/fftnv/fftvl × NG1/5/9 × M1–3)在 F2 上 | registries/s4r6d/、registries/s3r3/ 第 A 节 |
| G8 | tri 分支 nv NG9 M1–3,F 与 F2 | registries/s3r3/ 第 C2 节 |
如果某组的历史结果不足以直接复制期望(例如 R5 V3 132 点是否纳入),在预注册前写 E7-x 说明取舍,不要猜。

4.2 新增点(U37)
- RNV1 jones、fftjones × NG1/5/9 × 窗口内每一次 malloc。先在 F 上无注入跑一次,用 gdb 记录窗口内 malloc 的次数与位置,
  写入 $EV/RNV1_JONES_MAP_R7.tsv,再写这些点的预注册。F 期望 CRASH,F2 期望 REPORTED_FAILURE(rc1 = 20)。
  如果 F 上无注入就不能正常运行,如实记录,这一项停下;不得换几何体凑结果。
- tri 分支 vl、jones NG9(用 driver_s3r3_tri.cpp 的晶格):同样先绘制窗口 malloc 映射,再预注册;F 期望 CRASH,F2 期望 REPORTED_FAILURE。
- 所有 RNV1/tri 结果行多记一列 win1_rc(第一个窗口关闭时 pattern 的返回值,从 R6D_WIN_CLOSE k=1 解析)。

4.3 无注入等价(扩展 S3R3 的 B)
模式:closed、fft、kottke、experimental、tensor、closed1d、jones、nv、vl、fftjones、fftnv、fftvl,
NG 1/5/9,外加 tri 驱动的 nv/vl/jones。F 与 F2 的输出(call1–3 dump)逐字节比较,rc 两树都记录。
期望全部 IDENTICAL。vl/fftvl NG1 两树都是 rc 20(−10 路径)。

## 5. R7-3 运行与判定
- 顺序:先跑 4.3(无注入等价);任何 NOT_IDENTICAL 立即停下(正常路径被改变),不再跑注入。
- 之后 G7、G8、4.2 → G1–G4 → G5、G6。每组两遍;判定用 judge_d003.classify(状态类用 R6c/R6c2 的判定器,只导入)。
- 每组输出 $EV/RESULTS_R7_<组>_pass{1,2}_run1.tsv,并生成对比表 $EV/REGRESS_R7.tsv:
  point_id、F 类别(历史)、F2 期望、F2 pass1、F2 pass2、verdict(MATCH / REGRESSION / FLAKY / IMPROVED_AS_EXPECTED)。
  IMPROVED_AS_EXPECTED 只用于 4(a)(b) 类点。
- 任何 MISMATCH 或 FLAKY:先记录,该组两遍跑完再停下,写报告等待裁决;不得改期望,不得重跑覆盖。
- gdb 抽样:G7 中 jones、fftjones 各抽 1 点,确认 −11 → FMMGetEpsilon_PolBasisJones 返回 → ComputeLayerModes 20。
  这次要在 gdb 中逐层读到 PolBasis 那一层的返回值;读不到就写"未读到",不要用源码补。

5.1 离线表(U36):$EV/VL_NG1_SPLIT_R7.tsv
从 S3R3 的 selfcheck 日志与 R7 G7 日志解析 vl/fftvl NG1 M1–3 两遍的 win1_rc 与后续窗口 rc、RC first。
期望(规划者已读到,INFLUENCED):win1_rc = −11,k=2、3 为 −10,RC first 20 来自第一次调用。
只汇总已有事实,不新增运行。

5.2 里程碑(仿照 U15)
G7、G8、4.2、4.3、G1–G4 判定完成后,做一次里程碑提交(小型表复制到 registries/s4r7/,写 SHA256SUMS、更新 STATE)。
提交信息写 "R7 milestone ... awaiting user review"。之后继续 G5、G6,不必等待。
如果剩余预算不够做 G5、G6,在里程碑处停下,并在报告中写"未完成",不要压缩判定。

## 6. R7-4 只读事项(不运行 S4)
- U38:$EV/PATTERN_MALLOC_CLASS_R7.tsv 列出 F2 pattern.c 中全部 malloc 的 行号、函数、调用者链([源码])、
  是否有 NULL 检查、是否在"模式/缓存安装验收路径或 FMM/FFT 失败传播链上"(按 MEMORY 范围判据),给出建议分类
  (IN_D003_CANDIDATE / OUT_OF_SCOPE_D003 / UNCLEAR)。只是建议,裁决归用户。
- 红点账本:新建 $EV/RED_POINTS_STATUS_R7.tsv,在 S3R3 状态表基础上加列 R7_result。
  RP-R6d-1 只能写"F2 回归 REPORTED_FAILURE x/y,两遍",不得写"已修好""已验证"。

## 7. 收尾
1. ERRATA_7:E7-1(STATE 中 R7/R8 去向更正,U39)及本轮全部事件。
2. 小型结果表(预注册及其 sha256 和时间戳、RESULTS、REGRESS、映射表、离线表、门禁、ERRATA)复制到 registries/s4r7/,
   写 SHA256SUMS.txt 并逐个比对;证据目录写 SHA256SUMS.txt(不收录 SHA256SUMS.txt 自身与 safe_run.log)
   和 SAFE_RUN_LOG_FINAL.txt;收尾门禁 GATE_R7_END.txt(含 /tmp 快照)。
3. STATE.md:一页以内;当前轮次写"P05-S4 R7(F2 回归)完成/未完成,等待用户审核";开放问题按 U39 改去向。
4. 报告 P05_S4R7_REPORT.md 须包含:门禁;构建与 seam diff 对比;预注册摘要;每组结果(两遍)与 REGRESS 汇总;
   无注入等价;jones 与 tri 新增点;离线 vl NG1 表;pattern malloc 分类;红点状态;需要用户裁决的事项
   (至少:P05-S3 是否签收;U38 的分类;R8 的范围与开工);违规两张表。
   结尾写"本轮已完成/未完成 R7 范围,等待用户审核",附 git log -3 与 git status --short。
5. 提交范围:checkpoints/p05/、testing/d003/stage_s4r7/。提交信息末尾写 awaiting user review。

## 8. 停止条件
- 门禁不符;F2 导出与 S3R3 源码不一致;seam diff 不同;
- 需要修改 S4/ 或历史装置;
- 4.3 出现任何 NOT_IDENTICAL;
- 任一组出现 REGRESSION/MISMATCH/FLAKY(该组两遍跑完后停);
- F 上新增点无注入不能正常运行(只停该项);
- 第 0 节规定的写法违规达到阈值。
出现以上任一情况,写报告并等待用户裁决。"未完成"与"不可行"必须区分。
