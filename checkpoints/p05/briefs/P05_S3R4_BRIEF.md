# P05-S3 R4(S3 的子轮次 S3R4,不是新阶段):U38 红点修复 + 冻结 F3

你是 P05-S3 的修复执行者。本轮是 P05-S3 的子轮次 S3R4,不得出现 P05-S6。不得宣布任何阶段完成或签收,
报告和 STATE 中都不写签收建议(U83)。本轮的自检不是修复后验证;修复后验证由 P05-S4 R8 在 F3 上完成。
先读 AGENTS.md、checkpoints/p05/STATE.md、checkpoints/p05/P05_S4R7_REPORT_FINAL.md、
checkpoints/p05/registries/s4r7/PATTERN_MALLOC_CLASS_R7.tsv、checkpoints/p05/P05_S3R3_CLOSEOUT.md(本轮做法以它为模板)。
证据目录:checkpoints/p05/evidence/p05-s3r4/;小型结果表:checkpoints/p05/registries/s3r4/;
报告:checkpoints/p05/P05_S3R4_CLOSEOUT.md;勘误:checkpoints/p05/ERRATA_S3R4.txt(编号 ES3R4-1 起)。
第一步:用 write 把本任务书原文存为 checkpoints/p05/briefs/P05_S3R4_BRIEF.md。

## 0. 操作规则(本轮要改 S4/,所以更严格)
- 写入:仓库文件只用 edit 或 write;其他写入一律经 `sh testing/d003/safe_run.sh p05-s3r4 -- sh -c '<命令,包括全部重定向>' sh ...`。
  写入目标只能在 $EV/、testing/d003/stage_s3r4/、checkpoints/p05/ 下,以及 U91 批准修改的三个 S4/ 文件。
- 禁止:`&` 后台启动、heredoc、`sed -i`、`python3 -c`、`cat >`、`tee`、`/dev/null`;任何以 / 开头、又不在 $REPO 下的路径都不得出现,包括占位路径。
- 只读命令白名单同续 5 第 0 节 B。
- 写入规则违反一次就停下。

## 1. 用户裁决(写在 ERRATA_S3R4.txt 开头,并追加到 RULINGS.tsv)
- U89:R7 完成(cc49c6b)。M3 经规划者独立 diff 核对(R6c 对 F 基线 354/0,对 F2 354/0,seam 50/0)。
  E7-8 的 18 行对照按 U52 的 POSTHOC 结论关闭;原 MISMATCH 行保留。R7 中披露的违规接受为已披露。
- U90:U38 分类裁决:
  · 806(pattern_get_containment_tree 的 area):IN_D003,本轮修复;
  · 415(shape_get_intersection_area_quad 的 POLYGON tri):IN_D003,本轮修复(连同上游返回值的传播);
  · 528(shape_get_intersection_area):OUT_OF_SCOPE_D003(没有调用者,死代码),交 P05-S5 登记;
  · 1164(fprint_double):OUT_OF_SCOPE_D003(唯一调用点已被注释),交 P05-S5 登记;
  · 新增 RP-S3R4-1:S4.cpp:1729 `L->pattern.parent = malloc(...)` 没有检查 NULL。分配失败时
    pattern_get_containment_tree 返回 −3,InitSolution 把 −3 当错误上报,所以不会崩溃,但错误码的含义不对。本轮一并修复。
- U91:本轮只允许修改 S4/pattern/pattern.c、S4/fmm/fmm_FFT.cpp、S4/fmm/fmm_kottke.cpp、S4/S4.cpp(只改 1729 附近)。
  S4/ 下其他任何文件、pattern.h 与历史装置都不得修改;如果确实需要改,停下申请。
- U92:顺序是 S3R4(修复并冻结 F3)→ P05-S4 R8(在 F3 上:F2→F3 回归 + 补充测试 + 阶段收口的 make test 与 E2E)。
  原 STATE 中 "转 R8(F2 上)" 的项目一律改为 "R8(F3 上)"。

## 2. 修复前源码确认($EV/PRE_FIX_SOURCE_S3R4.md)
- 806:pattern_get_containment_tree(pattern.c:782)中 area 的分配与使用,函数现有返回码(0、−1、−2、−3、i+1、nshapes+i+1),
  以及新返回码与这些现有返回码不冲突的依据;调用点 S4.cpp:1730–1734 对非零返回的处理。
- 415:shape_get_intersection_area_quad(pattern.c:301)的 POLYGON 分支;返回 double,所以需要一个失败标记(例如负值,
  面积正常时不会是负数,要写出 [源码] 依据);pattern_discretize_cell(pattern.c:1044)现有返回码(−1…−9,0)以及新返回码的选择;
  调用点 fmm_FFT.cpp:98、fmm_kottke.cpp:102 目前丢弃返回值,写出各自函数里已经分配、需要在失败路径上释放的资源与现有错误返回方式。
- 1729:S4.cpp:1726–1734 的上下文;InitSolution 的错误码约定(S4_internal.h 中 "1 - allocation error")。
- 每一条都要写出 文件:行号。

## 3. 修复(提交拆分:806 与 1729 一个提交;415 链路一个提交)
- 806:area 为 NULL 时返回一个新的、不与现有返回码冲突的值(在注释中写明含义),不碰 parent 的内容;正常路径不变。
- 1729:parent 为 NULL 时返回 1(分配失败),并保持 L->pattern.parent 为 NULL(不留下悬挂指针);正常路径不变。
- 415:tri 为 NULL 时返回失败标记;pattern_discretize_cell 在 1115 处检测到失败标记,就返回一个新的错误码;
  fmm_FFT.cpp:98 与 fmm_kottke.cpp:102 检查返回值,非零时释放本函数已分配的资源,并按该函数现有方式返回非零。
  正常路径的数值与运算顺序都不得改变。
- 编译检查:F2 与 F3 各做 dbg(-O0 -g)和 plain(R4 方式)构建,告警逐条比较(去掉行号),新增告警逐条说明。

## 4. 自检(不是 S4 验证;运行前预注册,状态 INFLUENCED)
预注册 $EV/REGISTRY_S3R4_SELFCHECK.tsv(记录 sha256 与 UTC 时间)。
- (A) 806 与 1729:新驱动 testing/d003/stage_s3r4/driver_s3r4_init.cpp(由 driver_r6b_state.cpp 复制,只在需要处改动),
  新注入器 inject_s3r4_init.cpp(--wrap=malloc,只在 Pattern_GetContainmentTree 窗口内,或 S4.cpp:1729 那一次 malloc 时返回 NULL;
  窗口的开关方式与 inject_r6d_rnv1.cpp 相同)。先在 F2 上不注入,用 gdb 记录窗口内的 malloc 次数与位置,写映射表。
  然后在 F2 与 F3 上逐点注入,两遍。期望:F2 上 806 点为 CRASH(或写明的其他类别,依据映射),1729 点为 REPORTED_FAILURE 且报告码为 −3;
  F3 上两类都是 REPORTED_FAILURE,1729 点的报告码为 1。
- (B) 415:新驱动使用多边形形状(例如 S4_Layer_SetRegionVertices,或 S4 已有的 polygon 接口;以 S4.h 中实际存在的为准),
  fft 模式与 kottke 模式。先在 F2 上不注入,确认确实进入 POLYGON 分支(gdb 函数断点),并记录 tri 的 malloc 次数;
  然后对第 1 次与最后 1 次 tri malloc 注入,两遍。期望:F2 上为 SILENT_SWALLOW 或 CRASH(依据映射写明);F3 上为 REPORTED_FAILURE。
  如果 F2 上不注入就无法正常运行,如实记录并停下这一项,不得换几何体凑结果。
- (C) 无注入输出一致:R7 4.3 的全部模式(用 closed2d,不是 closed)× NG 1/5/9,加上 (B) 的多边形驱动,
  F2 与 F3 的 dump 逐字节比较,期望全部相同。出现任何不同就停下(正常路径被改变了)。
- (D) 冒烟:M2 run7 中每组抽 2 点,在 F3 上跑一遍,期望与 run7 相同(这只是冒烟,不是回归)。
判定用 judge_d003.classify(只导入)。出现 MISMATCH:两遍跑完后停下;不改期望,也不为了通过而改修复。

## 5. 冻结 F3 与收尾
- F3 = 本轮最后一个修改 S4/ 的提交;记录提交哈希、S4 树哈希,以及 F2→F3 的 `git diff --stat -- S4/`(只允许出现 U91 的四个文件)。
- AGENTS.md:第 6 节表格追加 F3 一行;开工门禁里的树哈希改为 F3(用户批准这两处修改,其他内容不改)。
- 红点状态表 $EV/RED_POINTS_STATUS_S3R4.tsv:806、415、RP-S3R4-1 只写 "自检通过/未通过",不写 "已修好" 或 "已验证";
  528、1164 写 OUT_OF_SCOPE_D003 → S5。
- STATE.md:当前轮次写 "P05-S3 R4 完成修复与自检,冻结 F3;下一步 P05-S4 R8 在 F3 上";
  把开放问题中 "R8(F2 上)" 改为 "R8(F3 上)"(U92)。
- 小型表复制到 registries/s3r4/,写标准格式的 SHA256SUMS.txt 并校验。
- 报告 P05_S3R4_CLOSEOUT.md:门禁;修复前的源码确认;各提交的 diff 摘要;告警对比;自检 A–D 的结果;F3 的哈希;
  R8 回归清单(R7 的 M1、M2、M3 全部在 F3 上重跑,加上 S3R4 新增的点);待用户裁决的事项(只写技术问题,不写签收);违规两张表。
  结尾写 "本轮已完成/未完成 S3R4 范围,等待用户审核",附 git log -3 与 git status --short。
- 提交信息末尾写 awaiting user review。

## 6. 停止条件
门禁不符;需要修改 U91 范围以外的文件;编译失败或出现无法解释的新告警;(C) 中出现任何不同;
(A) 或 (B) 出现 MISMATCH(两遍跑完后停);新返回码与现有返回码冲突;写入规则被违反。
"未完成" 与 "不可行" 必须区分。
