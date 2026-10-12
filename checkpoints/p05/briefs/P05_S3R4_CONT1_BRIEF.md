# P05-S3 R4 续1(S3R4 的续轮,不是新阶段):补完自检 A、B、C(多边形)、D,修正 S3R4 记录

你是 P05-S3 的自检执行者。本轮是 S3R4 的续轮(记为 S3R4 续1),不得出现 P05-S6。不得宣布任何阶段完成或签收,
报告与 STATE 中不写签收建议(U83)。本轮的自检不是修复后验证;修复后验证由 P05-S4 R8 在 F3 上完成。
**本轮不得修改 S4/ 下任何文件。** 如果自检表明需要改 S4/,停下报告,等待新的裁决。

先读:AGENTS.md、checkpoints/p05/STATE.md、checkpoints/p05/briefs/P05_S3R4_BRIEF.md、
checkpoints/p05/P05_S3R4_CLOSEOUT.md、checkpoints/p05/ERRATA_S3R4.txt、checkpoints/p05/P05_S3R3_CLOSEOUT.md(做法模板)、
checkpoints/p05/evidence/p05-s3r4/map_F2_A1/stderr.txt、testing/d003/stage_s3r4/ 下全部脚本。
证据目录:checkpoints/p05/evidence/p05-s3r4c1/(新目录;不往 p05-s3r4/ 写任何东西);
小型结果表:checkpoints/p05/registries/s3r4c1/;报告:checkpoints/p05/P05_S3R4_CLOSEOUT_CONT1.md;
勘误:在 checkpoints/p05/ERRATA_S3R4.txt 末尾追加,从 ES3R4-10 起编号,不改已有条目。
第一步:用 write 把本任务书原文存为 checkpoints/p05/briefs/P05_S3R4_CONT1_BRIEF.md。

## 0. 门禁与操作规则
- 开工门禁:HEAD = 2fc6a55;`git rev-parse HEAD:S4` = 6cff923a02baf19e01966b2339755cbf3a5deeef(F3);
  judge_d003.py sha256 = d2d04145…209eb;`git status --short` 只允许出现 ` M checkpoints/p05/P05_S3R4_CLOSEOUT.md`。
  任一不符就停下报告。/tmp 顶层只读快照,开工和收尾各做一次,写入 $EV/GATE_CONT1.txt。
- 写入:仓库文件只用 edit 或 write;其他写入一律经
  `sh testing/d003/safe_run.sh p05-s3r4c1 -- sh -c '<命令,包括全部重定向>' sh ...`。
  **外层的 `>`、`2>&1` 也必须写在 sh -c 里面**(S3R4 表二的过失不得重复)。
  写入目标只能在 $EV/、testing/d003/stage_s3r4c1/(新目录,本轮新脚本都放这里)、checkpoints/p05/ 下。
- 禁止:`&` 后台启动、heredoc、`sed -i`、`python3 -c`、`cat >`、`tee`、`/dev/null`、2>/dev/null;
  不得出现以 / 开头又不在 $REPO 下的路径(包括占位路径);不做拒绝性测试或沙箱探测;
  不得改 testing/d003/stage_s3r4/ 下已提交的文件(需要改动时复制到 stage_s3r4c1/ 并改名,文件名带 c1)。
- 写入规则违反一次就停下(U101 重申)。只读命令同续 5 第 0 节 B 的白名单。长输出带 head/tail。

## 1. 用户裁决(写在 ERRATA_S3R4.txt 的 ES3R4-10 之前,并追加到 RULINGS.tsv)
- U98:S3R4 的自检 A、B、D,以及 C 的多边形部分,在 S3R4 续1 中完成,不并入 R8。顺序:续1 → 用户审核 → P05-S4 R8(F3 上)。
- U99:ES3R4-5(a)(b) 同意交 P05-S5 登记,不在 P05-S3/S4 修复。补充说明写进 S5 登记:798 行的内层循环
  `for(j = i+1; i < nshapes; ++i)` 会把外层 i 推到 nshapes,所以 nshapes > 1 时只有第 0 个形状做了 shape_valid 检查;
  修好它会改变正常路径(现有输入可能新报错),因此不属于 D003。
- U100:FFT/Kottke 忽略 Pattern_DiscretizeCell 的 −1…−9,同意交 P05-S5。本轮写一段 [源码] 说明,
  逐个返回码说明经公共 API 是否可达(文件:行号),只写 [源码],不运行。
- U101:S3R4 表二的"外层重定向未经 safe_run"(目标都在 $EV/ 内)接受为已披露;S3R4 当时违规后没有停下,登记为过程偏离。本轮严格按"违反一次就停"执行。
- U102:RULINGS.tsv 补登 U96、U97 两行,内容按 ERRATA ES3R4-7/8 与 CLOSEOUT §1 转述,status 写 `生效-补录(据报告转述)`;
  不改已有行。

## 2. 记录修正(先做,单独一个提交)
- 先提交 CLOSEOUT 中未提交的 §12 补充,内容不改。提交信息写明 "commit pending §12 of S3R4 closeout"。
- ERRATA 追加:
  ES3R4-10:A1_MAP_STATUS_F2.txt 写的 "WIN_OPEN count=2" 有误,stderr 实际为 3(三个层各调用一次 Pattern_GetContainmentTree;
  其中两次 malloc_in_window=0,即 nshapes=0 的层)。原文件不改。
  ES3R4-11:CLOSEOUT §5(C) 写"通过",但任务书 §4(C) 要求的"(B) 的多边形驱动"没有运行;tri 驱动是三角晶格驱动(driver_s3r3_tri),
  不是多边形形状。正确的写法是"(C) 部分完成:圆形与三角晶格 117/117 IDENTICAL;多边形部分未做"。本轮补做。
  ES3R4-12:RULINGS.tsv 缺 U96、U97,CLOSEOUT 第 5 行的"U89–U97"不实;已按 U102 补登。
  ES3R4-13:evidence/p05-s3r4/SHA256SUMS.txt 中 safe_run.log 校验 FAILED,原因是清单写完后又追加了日志(请核实后写明);
  不重写原清单,在 $EV 中写一份核对记录。
  ES3R4-14:CLOSEOUT §12 写"git status 为空",实际 §12 本身没有提交;已在本轮第一个提交补交。
- RULINGS.tsv 追加 U96、U97(补录)以及 U98–U102。

## 3. 自检 (A):806 与 1729(驱动 driver_r6b_state;注入器 stage_s3r4/inject_s3r4_init.cpp,不修改)
- 构建:F2 库沿用 evidence/p05-s3r4/build/F2-plain(只读引用,先核对 sha256 与 S3R4 记录一致),
  F3 库沿用 evidence/p05-s3r4/build_f3/plain(同样核对)。init 驱动在本轮 $EV/drivers/ 下重新链接 F2 与 F3 两份
  (复制 link_init_s3r4.sh 为 stage_s3r4c1/link_init_c1.sh,只改输出目录),记录 sha256。
- A1 映射(每棵树、每个组合都做,不假设相同):组合 = closed2d NG1、fft NG5、kottke NG5。
  方法:在 gdb batch 下运行(gdb 默认关闭 ASLR),在 `exit` 处设断点,停下后执行 `info proc mappings` 取得驱动的装载基址,
  再对 stderr 中每个不同的 caller 用 `addr2line -f -e <driver> <caller−基址>` 解析函数名。
  映射表 $EV/A1_MAP_C1.tsv:tree, combo, K, n, caller, offset, function, 所在层(按 WIN_OPEN 先后推断)。
  判定 1729 的 K:函数为 Simulation_InitSolution,n = 4 × nshapes,而且是该层 WIN_OPEN 之前最后一次窗口外 malloc。
  预计 K=7(n=4)和 K=6、8(n=0),但以映射为准。如果不能唯一确定,停下这一项。
  附加核对:另把 init 驱动链接到 F2-dbg 库,用 `info line *<地址>` 确认是 S4.cpp 中 parent 的那次 malloc 所在行(只作佐证)。
- 预注册 $EV/REGISTRY_S3R4C1_A.tsv(INFLUENCED,在任何注入运行之前写定;记录 sha256 与 UTC 时间)。每个组合三个点:
  · A-806:`win:1`(窗口内唯一一次 malloc)。期望 F2 = CRASH;F3 = REPORTED_FAILURE,rc1 = 1。
  · A-1729:`init:K`(nshapes=1 的层)。期望 F2 = REPORTED_FAILURE,rc1 = −3;F3 = REPORTED_FAILURE,rc1 = 1。
  · A-U96 边界:`init:K0`(nshapes=0 的层,n=0)。期望 F2、F3 的 rc1 = 0,判定器给出 SILENT_SWALLOW。
    这一行在预注册中标注 `BOUNDARY_U96_BY_DESIGN`:用来确认 nshapes=0 时空 parent 不算失败,不是缺陷。
  · 副观察(不参与判定,也要预注册):F3 上 A-806 与 A-1729 的 rc2(重试)期望为 0;F2 上 A-1729 的 rc2 期望为 0。
- 运行:3 组合 × 3 点 × 2 树 × 2 遍 = 36 次;外加每棵树、每个组合一次无注入对照(判定 CONTROL_OK)。
  判定只 import judge_d003.classify。出现 MISMATCH:两遍跑完后停下,不改期望,也不改修复。

## 4. 自检 (B):415(新驱动 + 新注入器)
- 驱动 testing/d003/stage_s3r4c1/driver_s3r4c1_poly.cpp:从 driver_r6b_state.cpp 复制,唯一改动是 pattern 分支用
  `S4_Layer_SetRegionVertices(S, slab, mGlass, S4_REGION_TYPE_POLYGON, 5, v, center, &angle_frac)`,
  v 为半径 0.25 的正五边形,逆时针:(0.25,0)、(0.0772542,0.2377641)、(−0.2022542,0.1469463)、
  (−0.2022542,−0.1469463)、(0.0772542,−0.2377641);center (0,0),angle_frac 0;其余逐行与原驱动相同。
  写一份逐行 diff 证明只改了这一处。closed1d 不适用(1D 只允许矩形),不运行。
- 注入器 stage_s3r4c1/inject_s3r4c1_poly.cpp:由 inject_s3r4_init.cpp 复制改名,窗口改为 `--wrap=Pattern_DiscretizeCell`。
  这次调用来自 fmm_FFT.o、fmm_kottke.o,定义在 pattern.o,是跨目标文件调用,所以 --wrap 有效;链接后用 nm 核对。
  注入方式为 `win:M`(窗口内第 M 次 malloc 返回 NULL)。
- 前置核对(F2 与 F3 各一次,不注入):
  · gdb 函数断点确认进入 POLYGON 分支(F2 断在 shape_get_intersection_area_quad,F3 断在 shape_get_intersection_area_quad_st;
    可在 pattern.c 中 tri 那次 malloc 所在行下行断点,两棵树各自核对行号);
  · 映射窗口内 malloc 的总次数 Mtot,以及每次的 n(期望 n = 12,即 3×(5−2)×sizeof(int);polygon_triangulate 与
    convex_polygon_intersection 不分配内存,用 [源码] 写明 intersection.c 的依据);
  · 如果 F2 不注入时 rc 不为 0,或者没有进入 POLYGON 分支,如实记录并停下这一项,不得换几何体凑结果。
- 预注册 $EV/REGISTRY_S3R4C1_B.tsv(INFLUENCED):组合 = fft、kottke × NG 1、5、9;点 = win:1 与 win:Mtot(各组合按映射写入)。
  期望:F2 = CRASH(tri 为 NULL 时 polygon_triangulate 返回 −3,该返回值被忽略,随后读 tri[...] 解引用 NULL;依据写文件:行号);
  F3 = REPORTED_FAILURE,rc1 = 20,无信号,hit = 1;副观察:F3 的 rc2 期望为 0。
- 运行:6 组合 × 2 点 × 2 树 × 2 遍 = 48 次,另加无注入对照。MISMATCH 的处理同 A。

## 5. 自检 (C) 补做:多边形驱动的无注入逐字节比较
- 预注册 $EV/REGISTRY_S3R4C1_C_POLY.tsv:poly 驱动(F2 与 F3 各一份;链接 R6b 的 inject_r4_plan.cpp,与 C 中的 state 驱动相同,
  链接选项与 S3R4 C 一致,并写出 diff)× 模式 closed2d、fft、kottke、experimental、tensor、jones、nv、vl、fftjones、fftnv、fftvl
  × NG 1、5、9 = 33 个组合。期望:F2 与 F3 的 call1–3 dump 全部 IDENTICAL,rc 对全部一致。
  F2 上的 rc 不要求为 0;某些模式对多边形本来就报错,要如实记录,但两棵树必须相同。
- 出现任何不同就停下(说明正常路径被改变了)。

## 6. 自检 (D):冒烟
- 从 M2 run7 的结果表(registries/s4r7/ 下对应的 run7 文件)中,每组(CTRL_SEAM、G2c、G1、G2a)按 id 排序取第一个和最后一个点,
  共 8 点。先写入 $EV/REGISTRY_S3R4C1_D.tsv(期望 = run7 的类别与 rc1),然后用与 R7 相同的源码与链接选项链接 F3 驱动
  (复制 R7 的链接脚本到 stage_s3r4c1/,只改库路径;写出选项 diff = 0 的核对),跑一遍。
  报告中写"冒烟",不写"回归"。

## 7. 收尾
- 红点状态表 $EV/RED_POINTS_STATUS_S3R4C1.tsv:806、415、RP-S3R4-1 只写"自检通过/未通过(F3:类别、rc1)",
  不写"已修好""已验证";528、1164、ES3R4-5(a)(b)、−1…−9 写 OUT_OF_SCOPE_D003 → S5(附 U90、U99、U100)。
- STATE.md:当前轮次写"P05-S3 R4 续1:自检 A/B/C/D 结果……;下一步 P05-S4 R8 在 F3 上";
  开放问题表新增 ES3R4-5(a)(b) 与 −1…−9 两行(→ S5),并把 RNV1 一行的去向改为 "R8(F3 上)"(U92)。保持一页以内。
- CLOSEOUT_CONT1 报告:门禁;记录修正;A1 映射;A、B、C 多边形部分、D 的预注册 sha256 与结果表;
  R8 回归清单的新增行(A、B 的注入点与无注入对照);U100 的 [源码] 说明;待用户裁决的技术问题;违规两张表;
  结尾写"本轮已完成/未完成 S3R4 续1 范围,等待用户审核",附 git log -3 与 git status --short(提交后的真实结果,不得预填)。
- 小型表复制到 registries/s3r4c1/,写 SHA256SUMS.txt 并逐个校验;$EV 写 SHA256SUMS.txt,写完之后不再经 safe_run 写入
  (最后的 git 提交如果必须追加 safe_run.log,就在清单中把 safe_run.log 单列为"清单后追加",不参与校验)。
- 提交信息末尾写 `awaiting user review`。

## 8. 停止条件
门禁不符;需要修改 S4/ 或已提交的历史装置;A1 映射不能唯一确定 K;B 在 F2 上不注入就不能正常运行或没有进入 POLYGON 分支;
(C) 多边形部分出现任何不同;A 或 B 出现 MISMATCH(两遍跑完后停);写入规则被违反一次。
"未完成"与"不可行"必须区分。
