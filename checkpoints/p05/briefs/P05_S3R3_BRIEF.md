# P05-S3 R3(S3 的子轮次):RNV1 修复(方案 R3)+ 注释措辞 + 冻结 F2

你是 P05-S3 的修复执行者。本轮是 P05-S3 的子轮次 S3R3,不是新阶段;不得出现 P05-S6。
不得宣布任何阶段完成或签收。本轮的自检不是"修复后验证";修复后验证是 P05-S4 R7 在 F2 上做。
先读 AGENTS.md、checkpoints/p05/STATE.md,然后读:
checkpoints/p05/P05_S4R6d_REPORT.md、registries/s4r6d/REPAIR_PROPOSAL_R6d.md、registries/s4r6d/RNV1_SOURCE_R6d.md、
registries/s4r6d/RED_POINTS_LEDGER_R6d.tsv、registries/RULINGS.tsv。
证据目录:checkpoints/p05/evidence/p05-s3r3/;小型结果表:checkpoints/p05/registries/s3r3/;
报告:checkpoints/p05/P05_S3R3_CLOSEOUT.md;勘误:ERRATA_S3R3.txt(编号 ES3R3-1 起)。
本任务书原文由你用 write 工具存为 checkpoints/p05/briefs/P05_S3R3_BRIEF.md(第一步就做,原样保存,不改写),一并提交。

## 0. 硬规则(本轮要改 S4/,规则比 S4 轮更严)
- 每条含写入的命令开头先执行:
  REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
  整条命令经 `sh testing/d003/safe_run.sh p05-s3r3 -- sh -c '<命令,含全部重定向>' sh ...` 运行。
- 禁止 heredoc、`sed -i`、`python -c` 或 python 脚本直接改文件、`cat >`、`tee`。
  修改 S4/ 源码、ERRATA、报告、脚本,一律只用 edit/write 工具。
  上一轮(R6d)这几种写法都出现过,本轮再出现一次就停下,在报告中说明。
- 不得出现 /dev/null;写入目标只能是 $EV/、$REPO/testing/d003/、$REPO/checkpoints/p05/,以及按 U32 批准的两个 S4/ 文件。
- python 一律 `python3 -I -B`;长输出带 head/tail;不做沙箱探测;judge_d003.py 只导入。
- 不覆盖任何证据或结果文件(U17)。

## 1. 用户裁决(写在 ERRATA_S3R3.txt 开头,并追加到 RULINGS.tsv)
- U29:S3-4b 由用户带范围声明关闭。声明全文见本节末尾,原样写入 checkpoints/p05/P05_S3_4b_CLOSURE.md(新文件)。
  这只关闭 S3-4b 这一项,不代表 P05-S3 或 P05-S4 签收。
- U30:RNV1 采用方案 R3(R1、R2 都不采用),内容见第 3 节。
- U31:S4/S4_internal.h:263 的注释改为
  "// 20 - the layer eigensystem failed; the failed layer has no modes; layers computed before it may keep their modes"
- U32:本轮只允许修改 S4/pattern/pattern.c 与 S4/S4_internal.h 第 263 行。S4/ 下其他任何文件、
  testing/d003/ 下的历史装置都不得修改。
- U33:F2 = 本轮最后一个修改 S4/ 的提交。收尾时在 AGENTS.md 第 6 节表格追加一行 F2(只追加这一行,AGENTS.md 其他内容不改),
  并把开工门禁的树哈希改为 F2(用户批准修改 AGENTS.md 的这两处)。
- E-S3R3-A(规划者更正 R6d 的修复方案,记录在本轮 ERRATA):
  (a) REPAIR_PROPOSAL_R6d.md 漏了 pattern.c:1251(cg 内的 work)。R6d 实测窗口内的第 3 次 malloc 就在这里(RNV1_SOURCE_R6d.md 第 4 节),
      所以 M=3 的 24 行 CRASH 不在 1477/1481。cg 与 sparse_linsolve_d 都返回 void,方案 R1、R2 都覆盖不到它。
  (b) REPAIR_PROPOSAL_R6d.md:60 的"layer 0/2 installed"与 E6b-1 矛盾,应为"只有层 0"。
  (c) tri 分支(1656、1660,以及 2056 的求解)从未实测。
  R6d 的文件本身不改。
S3-4b 范围声明全文:
"S3-4b 在冻结树 F 上带范围声明关闭:202 个注入点(FMM 分配/plan/exec 177 点 + seam 25 点)在失败那一刻判定 I1–I6,
 HOLD 202 / VIOLATED 0 / FLAKY 0,两遍一致;判定器自检 11/11 判出 VIOLATED。失败阶段覆盖 a 2、b 197、c 1、d 2、e 0;
 失败层只有层 0 与层 1;缓存命中路线 1 点。不覆盖:阶段 e、I7 sanitizer、双目标注入、其他层失败变体,转到 F2 上的 R8。
 此关闭不代表 P05-S3 或 P05-S4 签收。"

## 2. S3R3-0 门禁
写入 $EV/GATE_S3R3.txt(新脚本 testing/d003/stage_s3r3/s3r3_gate.py)。逐项核对:
- HEAD = cadf258(写完整哈希);
- `HEAD:S4` = 4a6f64927a30537740dd0c8f11f9a5aae5e46ba4(F);
- judge_d003.py 的 sha256 = d2d04145…209eb;
- registries/s4r6d 的 SHA256SUMS.txt 全部 OK;
- 工作区干净(只允许 briefs/P05_S3R3_BRIEF.md 与本轮 gate 脚本未跟踪);
- /tmp 顶层快照。
任一不符就停下。

## 3. S3R3-1 修复(只读完相关源码后才动手)
1. 修改前只读确认,写入 $EV/PRE_FIX_SOURCE_S3R3.md:
   - pattern.c 中 cg、sparse_linsolve_d(两个分支,含 HAVE_LIBCHOLMOD)、_rect、_tri、pattern_generate_flow_field 的全部行号与调用关系;
   - 本仓库的构建是否定义 HAVE_LIBCHOLMOD(查构建脚本与编译命令行;以实际编译命令为准);
   - −11 在 S4/ 中没有被用作 pattern 的返回码(grep 结果原样附上);
   - 三个调用者(fmm_PolBasisNV.cpp、Jones、VL)对非零返回的处理行号(规划者读到的是 NV:144、Jones:187、VL:146;请自行核对);
   - pattern.h 中 pattern_generate_flow_field 的返回值注释,若需同步更新,只允许改 pattern.c 内的注释;pattern.h 不在 U32 批准范围内,
     如果必须改 pattern.h,就停下请求批准。
2. 方案 R3(只改 pattern.c 内的 static 函数与其调用者):
   - cg:返回 int。pattern.c:1251 分配失败时返回非零,不使用 NULL 指针;成功路径的行为、迭代、释放都不变。
   - sparse_linsolve_d:返回 int,把 cg 的状态传出;CHOLMOD 分支如果编译进来,对它的失败返回(若有)也传出;没有就返回 0,并注释说明。
   - _rect 与 _tri:work、iwork 分配后立即检查;任何一个失败,就释放已分配的那一个,返回 -1.0;
     sparse_linsolve_d 返回非零时,释放 work、iwork,返回 -1.0。
   - pattern_generate_flow_field:在已有的 D016 检查之前加 `if(max_field < 0){ return -11; }`,
     并加一行注释说明 -11 = 内部分配失败(以及 -10 与 -9 的现有含义不变)。
   - 正常路径的数值与运算顺序不得改变。
   - 提交拆分:pattern.c 的修复一个提交;S4_internal.h:263 的注释一个提交。
     两个提交的 diff 都要附在报告中(`git show --stat` 与 `git diff` 的行数)。
3. 编译检查:用 R5 dbg 的构建方式在 $EV/build/ 下构建 F2 的库(-O0 -g),以及一份与 R4 相同优化级别的普通构建。
   编译告警数与 F 构建的告警数比较,新增告警逐条列出。

## 4. S3R3-2 修复轮自检(不是 S4 验证;预注册在运行前写入,状态 INFLUENCED)
预注册 $EV/REGISTRY_S3R3_SELFCHECK.tsv(sha256 与 UTC 时间戳)。期望:
- (A) RNV1 72 个 F 点(复用 run_r6d_rnv1.py 与 inject_r6d_rnv1.cpp,改链接 F2 的库;运行器若需修改,复制成 s3r3 新文件):
  期望 REPORTED_FAILURE(rc 非零,无信号),驱动 rc 为 20;两遍。
  另外用 gdb 抽 M=1、M=3 各 1 点,确认返回码链为 −11 → PolBasis 返回 → ComputeLayerModes 20。
- (B) 无注入输出一致:nv、vl、fftnv、fftvl × NG 1、5、9,F 与 F2 的场输出逐字节比较(用 S4FMM_DUMP 或 driver_r6b_state 的 DUMP_DIR)。
  期望全部 IDENTICAL;vl NG=1 原本就走 −10(D016),期望 F 与 F2 都保持 −10,rc 20。
- (C) tri 分支:新驱动 testing/d003/stage_s3r3/driver_s3r3_tri.cpp(由 driver_r6b_state.cpp 复制,只把晶格改成非正交,例如 Lr = {1,0,0.5,0.866})。
  先在 F 上无注入运行,用 gdb 确认进入了 _tri,并记录窗口内的 malloc 次数与位置;
  再在 F 与 F2 上对窗口内每一次 malloc 注入,两遍。期望 F 为 CRASH、F2 为 REPORTED_FAILURE。
  无注入时 F 与 F2 的输出逐字节一致。
  如果 F 上无注入就无法正常运行(例如 rc 非零),如实记录并停下这一项,不要换几何体去凑结果。
- (D) 不重跑 R3–R6 全部矩阵,那是 R7 的范围。只跑 RS-177 中 nv/vl 的 M-* 点各 1 点作冒烟检查,期望 rc 与 R6c 相同。
结果写入 $EV/RESULTS_S3R3_SELFCHECK_pass{1,2}.tsv;判定用 judge_d003.classify。
任何 MISMATCH 先记录,两遍跑完后停下;不得改期望,也不得为了通过而改修复。

## 5. S3R3-3 冻结 F2 与收尾
1. F2 = 第 3 节最后一个修改 S4/ 的提交。记录:
   提交哈希、`git rev-parse <F2>:S4`、F→F2 的 `git diff --stat -- S4/`(只允许出现 pattern.c 与 S4_internal.h)。
2. AGENTS.md(U33):第 6 节表格追加一行
   "F2 | <提交> | <S4/ 树哈希> | P05-S3R3 修复后的冻结被测树(RNV1 方案 R3 + 注释 U31)";
   第 6 节开工门禁中的"F 的树哈希"改为 F2。只改这两处,用 edit 工具。
3. 更新 RULINGS.tsv(追加 U29–U33)、STATE.md(50 行以内;当前阶段写"P05-S3 R3 完成修复,等待用户审核;下一步 P05-S4 R7 在 F2 上回归")。
4. 新建 registries/s4r6d 之后的修复对照文件 $EV/RED_POINTS_STATUS_S3R3.tsv:
   每个红点修复前在 F 上的类别、修复后自检在 F2 上的结果、R7 需要回归的 point_id。
   RNV1 只写"自检通过/未通过",不得写"已修好""已验证"。
5. 小型结果表复制到 registries/s3r3/,写 SHA256SUMS.txt 并逐个比对;证据目录写 SHA256SUMS.txt(不收录 safe_run.log)和 SAFE_RUN_LOG_FINAL.txt;收尾门禁写 GATE_S3R3_END.txt。
6. 报告 P05_S3R3_CLOSEOUT.md 须包含:门禁;修改前的源码确认;两个 S4/ 提交的 diff 摘要;编译告警对比;自检 A–D 的结果;F2 的哈希;
   R7 回归矩阵清单(R3、R4、R5 M2、R6-1、R6c 177、R6c seam 25、R6d RNV1 72、S3R3 tri 点,各写来源文件);
   需要用户裁决的事项(至少包括:P05-S3 是否签收;R7 开工);违规两张表。
   结尾写"本轮已完成/未完成 S3R3 范围,等待用户审核",附 git log -3 与 git status --short。
7. 提交范围:S4/pattern/pattern.c、S4/S4_internal.h(各自单独提交),checkpoints/p05/,testing/d003/stage_s3r3/,AGENTS.md(U33 的两处)。
   提交信息末尾写 awaiting user review。

## 6. 停止条件
- 门禁不符;
- 修改需要 U32 范围以外的文件(包括 pattern.h);
- 编译失败或出现新告警而无法解释;
- 自检 (B) 出现任何 NOT IDENTICAL(正常路径被改变);
- 自检 (A) 或 (C) 出现 MISMATCH(两遍跑完后停);
- 发现 −11 已被占用。
出现以上任一情况,写报告并等用户裁决。"未完成"与"不可行"必须区分。
