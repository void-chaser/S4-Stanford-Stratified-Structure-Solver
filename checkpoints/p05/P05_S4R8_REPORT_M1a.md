# P05-S4 R8 M1a 报告(准备轮:dbg 库差异、F3 构建与驱动补齐、F2→F3 注入点映射;在 §6.1 停止)

> P05-S4 的子轮次 R8 的 M1a 里程碑,不是新阶段,不出现 P05-S6。本报告不宣布任何阶段完成或签收,不写签收建议。
> 本轮未修改 S4/,未修改 testing/d003/ 下任何已提交文件,未运行任何注入。
> 报告用"冒烟""等价""映射""链接"等措辞;REPORTED_FAILURE 只表示"在该注入下返回码非零",本轮没有任何注入运行。

## 0. 结论(事实)

- **本轮未完成 R8 M1a 范围。** 在 §6.1(F2→F3 静态映射)停止:28 个站点中 MISSING 2、AMBIGUOUS 2,按任务书 §6.1 "MISSING 就停下"与 §1 的停止规则,未进行 §6.2 动态映射、§7 预注册与 dry-run、§8 记录提交。
- 已完成并有证据的部分:门禁 start(FAILS=0);§4 dbg 库 strip 等价(24/24 EQUAL_AFTER_STRIP,E8-9 关闭);§5 需求清单、F3 seam dbg 库与驱动补齐、编译选项核对(0 差异)、F2 复用核对(17 SAME、1 FIRST_RECORD)、驱动汇总;§6.1 静态映射 28 站点的结果(SAME_LINE 5、SHIFTED 19、MISSING 2、AMBIGUOUS 2)。
- 未完成(原因):§6.1 的 4 个停止项需要用户裁决(见 §13);§6.2、§7、§8 依赖 §6.1 的结论,未开始。
- 没有执行任何注入运行。没有执行任何驱动(只链接驱动并计算库与驱动的 sha256;链接后仅检查可执行位,未运行)。
- 没有给出 M1b/M1c 的期望或预注册。

## 1. 门禁(任务书 §3)

- 门禁脚本:`testing/d003/stage_s4r8/gate4_r8m1.sh`(复制自 gate3_r8.sh 后修改:start/end 双模式;允许列表改为数据文件,U143)。
- 允许列表数据文件及其 sha256(运行前写入,随记录提交入库):
  - `testing/d003/stage_s4r8/gate_allow_r8m1a_start.txt`:sha256 `7df7f53e43208d0df9838a1a8eaaa8970e5e9abeb77a81511351deb57ba77128`;
  - `testing/d003/stage_s4r8/gate_allow_r8m1a_end.txt`:见其文件(本轮未运行 end 模式,见 §12)。
- 开工门禁结果:`checkpoints/p05/evidence/p05-s4r8/GATE_R8_M1a.txt`,**FAILS=0**(UTC 2026-10-13T08:05:28Z)。逐项:HEAD `e2589cb`、HEAD:S4 `6cff923a…`、8d8202a:S4 与 a07b5ac:S4 树哈希、S4 差异四文件(LC_ALL=C sort)、判定器 sha256、REGISTRY_S3R4C3_D.tsv sha256、registries/s4r8 的 SHA256SUMS(25/25 OK)、registries/s3r4c5 的 SHA256SUMS(14/14 OK)、registries/s4r7 清单分类(`S4R7_RECHECK_R8_M1A_START.tsv`,fails=0)、`git status` 逐行对照允许列表(无不允许行)、/tmp 快照(0 项,sha256 为空串哈希)。
- 任务书 §8 要求的 gate4 end 未运行(见 §12)。
- 运行前检查:`PRERUN_CHECKS_R8_M1a.txt` 记录每个脚本的 grep 命中数(全部为 0)。

## 2. 用户裁决 U137–U143(任务书 §2)

已追加到 `checkpoints/p05/registries/RULINGS.tsv`(生效)与 `checkpoints/p05/registries/s4r8/ERRATA_8.txt`(E8-18 起)。

- **U137**:R8 M0 由用户审核接受(e2589cb);§10/§16 的措辞修正(未提交)接受,随本轮记录提交入库(本轮未提交,见 §12)。收尾阶段的超出白名单的只读命令记入表二,记为 E8-18。
- **U138**:R8 M1 分为 M1a(准备,本轮)、M1b(plain 组注入回归)、M1c(dbg/gdb 状态组),每个结束后停下等用户审核。
- **U139**:M1b/M1c 的比较规则(a)–(e)写入裁决;期望只能由脚本从 registries/s4r7 生成(本轮未生成预注册,见 §10)。
- **U140**:按调用次数计数的注入能否照搬到 F3,取决于 §6 的映射;只有 IDENTICAL 的点才能照搬;DIFFERENT 停下等裁决。本轮 §6.1 已停止(见 §7、§13)。
- **U141**:E8-9 的查明为第 0 步,方法照 U84/U87。结果见 §4(全部成员 EQUAL_AFTER_STRIP,关闭 E8-9)。
- **U142**:22 行新增与多边形等价在 M1b 运行。本轮只完成 F3 侧驱动的链接(init-F3、polyinj-F3、poly-F3,见 §5)与 F2 侧复用核对(§6 的 F2 复用表)。
- **U143**:门禁允许列表为数据文件(见 §1)。

## 3. 内联命令白名单与复制品规则

- 本轮所有写入均经 `sh testing/d003/safe_run.sh p05-s4r8 -- …` 或 `python3 -I -B`(经 safe_run)运行。`safe_run.log` 记录每次调用(`checkpoints/p05/evidence/p05-s4r8/safe_run.log`)。
- 本轮新建的脚本与数据文件(均在 `testing/d003/stage_s4r8/`):`prerun_log_r8m1.sh`、`gate4_r8m1.sh`、`gate_allow_r8m1a_start.txt`、`gate_allow_r8m1a_end.txt`、`recheck_s4r7_r8m1.py`、`strip_equiv_r8m1.sh`、`make_needs_r8m1.py`、`build_seam_r8m1.sh`、`link_drivers_r8m1.sh`、`link_r6b_seam_r8m1.sh`、`link_s3r4_r8m1.sh`、`build_option_diff_r8m1.py`、`reuse_f2_r8m1.py`、`make_drivers_summary_r8m1.py`、`map_f2_f3_r8m1.py`。
- 复制品与原件的 diff(任务书 §1 要求写入 `RUNNER_DIFF_R8_M1a.txt`):**本轮未生成该文件。** 复制品的改动已在各脚本的头部注释中逐条写明(标准首段、删除 `rm -rf` 为存在性检查、`/dev/null` 的替换、输出目录与库路径);这一项列为未完成,见 §12。
- 运行前禁止项检查:每个脚本运行前用 grep 工具搜索 `testing/d003/stage_s4r8/`(禁止项正则 `/dev/null|DEVNULL|devnull|<<-?…|sed -i|python3 -c|cat >|tee |rm -rf|(^|[^V])/tmp`),结果 0 行后才运行;结果经 `prerun_log_r8m1.sh` 记录到 `PRERUN_CHECKS_R8_M1a.txt`。单独写入记录的脚本有:`gate4_r8m1.sh`、`strip_equiv_r8m1.sh`、`make_needs_r8m1.py`、`build_seam_r8m1.sh`、`link_drivers_r8m1.sh`、`link_r6b_seam_r8m1.sh`、`link_s3r4_r8m1.sh`、`build_option_diff_r8m1.py`、`reuse_f2_r8m1.py`、`make_drivers_summary_r8m1.py`、`map_f2_f3_r8m1.py`。
- 记录缺口(如实说明):`recheck_s4r7_r8m1.py`(由 gate4 调用)与两个 `gate_allow_r8m1a_*.txt` 数据文件没有单独的 PRERUN 记录行;它们包含在全目录 grep 的 0 行结果之内,但单独的记录行未写。这一缺口不影响结论,记为执行者的记录遗漏。
- 草稿中的字面量(注释中出现 `/dev/null`、`rm -rf`、`/tmp` 字样)在运行前改写为不含禁止项的文字,未运行即修正,不算违规(E8-22)。

## 4. §4 dbg 库差异(U141;E8-9)

- 脚本:`testing/d003/stage_s4r8/strip_equiv_r8m1.sh`(复制自 `testing/d003/stage_s4r7/check_dbg_strip_equiv_r7.sh`;只改比较对象与输出目录;删去驱动比较段)。
- 比较对象:R8 的 F3-dbg 库(`checkpoints/p05/evidence/p05-s4r8/build_r8/F3-dbg/build/libS4.a`,sha256 `56f72c58…897a`)与 S3R4 的 F3-dbg 库(`checkpoints/p05/evidence/p05-s3r4/build_f3/dbg/build/libS4.a`,sha256 `10ea03b3…65afa`,运行前核对)。
- 方法:复制两份库,对复制件运行 `objcopy --strip-debug`,`ar x` 后逐成员比较(原件未修改)。
- 结果(`checkpoints/p05/evidence/p05-s4r8/strip_cmp_r8m1/STRIP_EQUIV_R8_M1a.tsv` 与 `STRIP_EQUIV_SUMMARY_R8_M1a.txt`):成员 24,EQUAL_AFTER_STRIP 24,other 0,FAILS 0,RESULT PASS。原始字节不等(`sha_raw_equal=no`),去调试段后逐成员相等。
- 处置:按 U141/U87 措辞关闭 E8-9:**差异只来自调试段**。这不是修复验证,也不改变任何 S4/ 或历史装置。

## 5. §5 需求清单、F3 构建与驱动补齐

### 5.1 需求清单

- `checkpoints/p05/evidence/p05-s4r8/NEEDS_R8_M1a.tsv`(由 `make_needs_r8m1.py` 只读生成;38 行数据;`r7_not_recorded=0`)。
- 每行给出:组、驱动族、模式、库类型、树、R7 记录名、R7 驱动路径与 sha256、F3 驱动名、M0 是否已有、来源(文件:行号)。R7 链接命令的行号(safe_run.log)写在表头注释中(例如 tri plain 循环 121、tri dbg 循环 150、r6bseam-seamF-F 387)。
- 需求结论:M0 已有的 F3 驱动为 d003-F3-plain、d003plan-F3-plain、r6bstate-F3-plain、tri-F3-plain、seam-seamF-F3、seam-fmmret-F3。M1b/M1c 需要而 M0 没有的为:r6dnv1-F3-plain(G7、4.2)、tri-F3-dbg(G8、4.2 tri)、d003-F3-dbg/d003plan-F3-dbg/r6bstate-F3-dbg(G5 与 dbg 对照)、r6bseam-seamF-F3 与 r6bseam-fmmret-F3(G6、G6c)、init-F3、polyinj-F3、poly-F3(22 行与多边形,U142)。

注意:R7 的 M1 运行器(`run_m1_r7.py:37-38`)把 tri 点用 **dbg** 驱动,rnv1 点用 **plain** 驱动,与 M0 的 plain 清单不同;这一点在需求清单中照实列出。

### 5.2 构建与驱动

**seam dbg 库**(`testing/d003/stage_s4r8/build_seam_r8m1.sh`,复制自 build_seam_s4r7.sh;源码树为 M0 的 `seam_r8/F3-seamF` 与 `F3-fmmret`,只读):

| 库 | 告警 | make rc | sha256 | R7 对照(BUILD_SEAM_R7) |
|---|---|---|---|---|
| seamF-F3 (dbg) | 62 | 0 | `16d43d3c…add3` | seamF-F 62 |
| fmmret-F3 (dbg) | 62 | 0 | `309707ab…3f6e` | fmmret-F 62 |

告警数与 R7 相同,符合 §5.2 的期望。

**驱动链接**(均只链接,未运行):

| 驱动 | 库 | 脚本 | driver sha256(前 8 位) |
|---|---|---|---|
| r6dnv1-F3-plain | F3 plain(M0) | link_drivers_r8m1.sh | a9fccfa3 |
| d003-F3-dbg | F3 dbg(M0) | link_drivers_r8m1.sh | ef3b2ecb |
| d003plan-F3-dbg | F3 dbg(M0) | link_drivers_r8m1.sh | 07476839 |
| r6bstate-F3-dbg | F3 dbg(M0) | link_drivers_r8m1.sh | 8b269be6 |
| tri-F3-dbg | F3 dbg(M0) | link_drivers_r8m1.sh | 7cd9edfa |
| r6bseam-seamF-F3 | seamF-F3 dbg(M1a) | link_r6b_seam_r8m1.sh | 4c882f73 |
| r6bseam-fmmret-F3 | fmmret-F3 dbg(M1a) | link_r6b_seam_r8m1.sh | e6ee5b6a |
| init-F3 | F3 plain(M0) | link_s3r4_r8m1.sh | ff66cfc1 |
| polyinj-F3 | F3 plain(M0) | link_s3r4_r8m1.sh | 419cfb72 |
| poly-F3 | F3 plain(M0) | link_s3r4_r8m1.sh | c92e7d7a |

`link_drivers_r8m1.sh` 的链接命令与 R7 `link_drivers_s4r7.sh`(dbg `-O0 -g`、plain `-O1`)及 safe_run.log 第 117–126、145–155 行的 tri 链接命令一致;tri-F3-dbg 使用 `LIBFLAGS` 含 `Pattern_GenerateFlowField` 包装(与 R7 tri dbg 命令一致)。`init-F3` 与 `polyinj-F3` 的库为 R8 的 F3 plain(按任务书 §5.2 "库改为 R8 的 F3 plain 库")。

**编译选项核对**(`testing/d003/stage_s4r8/build_option_diff_r8m1.py`,输出 `checkpoints/p05/evidence/p05-s4r8/BUILD_OPTION_DIFF_R8_M1a.txt`):6 对(G5 dbg、G6 seamF/fmmret dbg、plain、seam plain 的 fmmret 与 seamF),每对 12 条 `g++` 命令行,去掉路径前缀后差异行数 **0**。

**告警与 S3R4 的 F3 库记录**:F3 plain 库 `abbc01c7…05de` 与 S3R4 记录 SAME(M0 已核对);F3 dbg 库 `56f72c58…897a` 与 S3R4 首次记录 `10ea03b3…65afa` 不同(E8-9),strip 等价已证(§4)。

### 5.3 F2 侧复用(`testing/d003/stage_s4r8/reuse_f2_r8m1.py`,输出 `DRIVERS_R8_M1a_F2_REUSED.tsv`)

- 18 行:**17 SAME、1 FIRST_RECORD、0 DIFFERENT、0 MISSING**。
- SAME 的 17 行:R7 的 F2 驱动(DRIVERS_R7 中的 F2 行、DRIVERS_R7_cont1 的 tri-F2-dbg、DRIVERS_R7_SEAM 的 seam-*-F2、DRIVER_R6B_SEAM_R7_F2 的 r6bseam-*-F2)与 S3R4 的 init-F2(BINARIES_C3 SAME 记录)、polyinj-F2、F2 库 c63d180a…(SAME)。
- FIRST_RECORD 的 1 行:**poly-F2**(`checkpoints/p05/evidence/p05-s3r4c2/drivers/poly-F2/driver`,sha256 `e9b75ca2…0ec86`):registries/s3r4c2 中没有该驱动的 sha 记录(grep 确认),记入 E8-21。
- polyinj-F2:BINARIES_C3 把它标为 FIRST_RECORD(值 237bbefc…);本轮当前值与该值相同,按记录值比较为 SAME。这一比较的来源性质(S3R4 当时标为 FIRST_RECORD)在 E8-21 中说明。
- 没有重新链接任何 F2 驱动(U126)。

### 5.4 汇总

`checkpoints/p05/evidence/p05-s4r8/DRIVERS_R8_M1a.tsv`(由 `make_drivers_summary_r8m1.py` 只读汇总,33 行):SAME 18、FIRST_RECORD 11、DIFFERENT_LIBRARY_ONLY 4。

- DIFFERENT_LIBRARY_ONLY 的 4 行是 F3 dbg 库驱动(d003-F3-dbg、d003plan-F3-dbg、r6bstate-F3-dbg、tri-F3-dbg):库 sha 与 S3R4 首次记录不同(E8-9,已由 §4 证明只差调试段);驱动本身无历史记录。
- init-F3:SAME(与 S3R4 BINARIES_C3 记录 `ff66cfc1…` 相同)。
- polyinj-F3:SAME(与 S3R4 记录值 `419cfb72…` 相同;S3R4 当时标为 FIRST_RECORD,见 E8-21)。
- poly-F3 与 seam/r6bseam 的 F3 新驱动:FIRST_RECORD(无历史记录)。

## 6. §6.1 静态映射(U140)

- 脚本:`testing/d003/stage_s4r8/map_f2_f3_r8m1.py`(只读,`git show a07b5ac:<file>` 与 `git show 8d8202a:<file>`,不写中间文件)。
- 站点来源:`LINEMAP_F_F2_R7.tsv`、`LINEMAP_M3_R7.tsv`(Part A 与 Part B)、`LINEMAP_A1_R7.tsv`、`gdb_chain_jones_line_r7.gdb`、`r5_rnv1_malloc_count.gdb` 注释、`driver_r6b_state.cpp:73`。
- 方法:取 F2 站点行的文本(去首尾空白)作为键,在 F3 同一文件中查找相同文本:唯一且行号相同为 SAME_LINE;唯一且行号不同为 SHIFTED;不存在为 MISSING;多处为 AMBIGUOUS。
- 结果(`checkpoints/p05/evidence/p05-s4r8/LINEMAP_F2_F3_R8_M1a.tsv`,28 站点,**exit 1**):

| 状态 | 数量 | 站点 |
|---|---|---|
| SAME_LINE | 5 | fmm_PolBasisJones.cpp:185、192;S4.cpp:23、32;driver_r6b_state.cpp:73 |
| SHIFTED | 19 | pattern.c 的 cg、rect、tri 的 solve 与 malloc、fn_* 定义行、1416、806、1164、1253/1499/1689(U38 的 malloc 重复项);S4.cpp:4210、2413 |
| MISSING | 2 | fmm_FFT.cpp:98、fmm_kottke.cpp:102(见下) |
| AMBIGUOUS | 2 | pattern.c:415、528(见下) |

- **MISSING(fmm_FFT.cpp:98、fmm_kottke.cpp:102)**:F3 的 S3R4 修复(U94/U96)把这两处 `Pattern_DiscretizeCell(...)` 调用改写为 `if(-12 == Pattern_DiscretizeCell(...)){ ret = 1; goto cleanup; }`(F3 第 101 与 105 行;`git diff a07b5ac 8d8202a -- S4/fmm/` 确认)。站点仍在,文字已改。这是 F3 修复改动的真实结果,不是映射错误;但按任务书 §6.1,MISSING 必须停下,脚本不把它判为 SAME 或 SHIFTED。
- **AMBIGUOUS(pattern.c:415、528)**:F2 的 415 与 528 行同文本(`int *tri = (int*)malloc(sizeof(int)*3*(s->vtab.polygon.n_vertices-2));`),在 F3 中出现在 418 与 545。F3 的 418 位于 `shape_get_intersection_area_quad_st`(303 起)之内,545 位于 `shape_get_intersection_area`(474 起)之内;F2 的 415 与 528 所属函数(LINEMAP_M3_R7 Part B)与 F3 的函数归属不能由文字匹配确定,需要人工核对。
- 停止:按任务书 §6.1 与 §1,本轮在 §6.1 停止。未做 §6.2 动态映射。

## 7. §6.2 动态映射、§7 预注册与 dry-run、§8 记录提交

- §6.2 动态映射:**未开始**(依赖 §6.1 的结论;按任务书 §6.2,期望文件 `EXPECT_CALLSEQ_R8_M1a.txt` 也未写入)。
- §7 预注册(`REGISTRY_S4_PRE_R8_M1b.tsv`、`REGISTRY_S4_PRE_R8_M1c.tsv`)、`PREREG_COUNTS`、`PREREG_RECORD`、dry-run(`DRYRUN_R8_M1a.txt`):**未开始**。
- §8 记录提交与 gate4 end:**未做**(见 §12)。

## 8. STATE 变更

- 本轮**未修改** `checkpoints/p05/STATE.md`(停止在 §6.1;§8 的 STATE 更新依赖完成的 M1a 范围)。
- 需要用户裁决后再更新 STATE(见 §13)。

## 9. 违规披露

### 表一:越界写入尝试(命令自身写了仓库外路径,即使被拒绝、未落盘)

本轮无。所有写入目标在 `$REPO` 之下(`$EV/`、`testing/d003/stage_s4r8/`)。

### 表二:工具/脚本事件

| 序号 | UTC | 事件 | 是否落盘 | 处置 |
|---|---|---|---|---|
| 1 | 未记录 | 本轮内联命令中含超出白名单的只读形式(见 §10 逐条) | 否(只读) | 记入表二,未停止(任务书 §1) |
| 2 | 未记录 | 运行前禁止项检查中,脚本注释含 `/dev/null`、`rm -rf`、`/tmp` 字样(草稿) | 否(未运行) | 运行前改写为不含禁止项的文字(按任务书 §0.2 不算违规) |
| 3 | 未记录 | 第一版 `gate4_r8m1.sh` 写入 `/tmp` 字样于注释 | 否(未运行) | 改写(同上) |
| 4 | 未记录 | 第一版 `strip_equiv_r8m1.sh` 注释含 R7 首行字面量 | 否(未运行) | 改写(同上) |
| 5 | 未记录 | 第一版 `build_seam_r8m1.sh` 注释含递归删除字面量 | 否(未运行) | 改写(同上) |
| 6 | 未记录 | 第一版 `make_needs_r8m1.py` 的 seam 记录与 G6 分组拼接错误(在运行前发现) | 否(未运行) | 按 R7 record 名重写脚本后运行 |
| 7 | 未记录 | `map_f2_f3_r8m1.py` 把 Part B 的 F 行号(1251/1481/1660)误当作 F2 行号 | 否(未运行) | 改为 F2 列行号(1253/1499/1689)后运行 |
| 8 | 未记录 | 执行者主动以后台方式启动 seam dbg 构建(作业 bash-2334;经 safe_run 运行,不是框架转入后台) | 否(构建产物在 $EV 内,经 safe_run) | 作业已完成(exit 0),输出已读取;不算违规,记为执行者的选择 |

说明:UTC 未记录的原因是会话中未逐条标注时间;不能从证据文件还原。第 2–7 条均在运行前发现或改正,未落盘,未越界。

### 本轮 `safe_run.log`

`checkpoints/p05/evidence/p05-s4r8/safe_run.log` 记录了本轮所有经 safe_run 的写入调用(由 safe_run 自动追加)。

## 10. 内联命令自查(任务书 §1)

本轮内联 bash 中含 `>`、`<`、`/dev/null`、`..`、`$(`、`|`、`2>&1`、`sed`、`grep`、`cut`、`wc`、`ls -la`、`git diff … | grep`、`git show … | wc`、`git status`、`git rev-parse`、`git log` 等形式者,均为只读命令,未写仓库外路径。下列为会话中执行过的超出白名单形式的**归纳**(不是逐字原文;逐字原文以会话记录为准;UTC 未记录,无法从证据文件还原):

1. `git rev-parse --show-toplevel; git rev-parse HEAD; git log -3 --oneline; git status --short | head -50`(白名单形式,含 `| head`)。
2. `git rev-parse HEAD:S4; git rev-parse a07b5ac:S4; git rev-parse 8d8202a:S4; ls checkpoints/p05/ | head -100; echo ---; ls checkpoints/p05/registries/s4r8/ | head -80; echo ---; ls testing/d003/stage_s4r8/ | head -100`(`echo ---` 为超出白名单的分隔输出)。
3. `wc -l checkpoints/p05/P05_S4R7_REPORT_M1.md … testing/d003/safe_run.sh …`(`wc -l` 对仓库内文件,白名单)。
4. `tail -n 12 checkpoints/p05/registries/RULINGS.tsv; echo ---; ls checkpoints/p05/evidence/; echo ---; ls checkpoints/p05/evidence/p05-s4r8/ | head -100`(`echo ---`、`tail` 白名单外的组合)。
5. `ls checkpoints/p05/evidence/p05-s4r8/build_r8 … | head -80; echo ---; ls checkpoints/p05/evidence/p05-s4r7 | head -120`(`echo`、`head`)。
6. `ls -A /tmp | wc -l`、`ls -A /tmp | sha256sum`(白名单形式)。
7. `cut -f1,2,3,4,5 checkpoints/p05/registries/s4r7/REGISTRY_S4_PRE_R7_M1.tsv | grep -v '^#' | head -n 4; echo ---; …`(`cut`、`grep -v` 超出白名单)。
8. `cut -f2 checkpoints/p05/registries/s4r7/REGISTRY_S4_PRE_R7_M2.tsv | sort | uniq -c | head -40; echo ---; …`(`cut`、`sort`、`uniq` 超出白名单;`sort` 未用 LC_ALL=C)。
9. `head -n 12 …REGISTRY_S4_PRE_R7_M2.tsv | tail -n 1; grep -c '' …`(`grep -c` 超出白名单)。
10. `ls testing/d003/matrix_r2.py … 2>&1; wc -l …`(含 `2>&1`)。
11. `cat checkpoints/p05/registries/s4r7/DRIVERS_R7_M3.tsv | cut -c1-260; …`(`cat`、`cut` 超出白名单)。
12. `ls checkpoints/p05/evidence/p05-s4r7/build_r7 …`(白名单)。
13. `ls … 2>&1`(含 `2>&1`,多处,包括核对 M0 与 R7 的 build 目录)。
14. `sed -n` 与 `cut -c1-200` 的读取(由 `cat`/`head` 配合,超出白名单)。
15. `git diff --stat a07b5ac 8d8202a -- S4/; echo ---; git diff --numstat …`(白名单形式的 `git diff`,`echo` 超出)。
16. `git diff -U0 a07b5ac 8d8202a -- S4/S4.cpp … | grep '^@@'`(管道接 `grep`,超出白名单)。
17. `git diff -U0 a07b5ac 8d8202a -- S4/pattern/pattern.c | grep '^@@'`(同上)。
18. `git show a07b5ac:S4/fmm/fmm_PolBasisJones.cpp | head -n 3; echo ---; git show 8d8202a:S4/S4.cpp | wc -l; …`(`echo`、`wc` 超出)。
19. `git diff -U3 a07b5ac 8d8202a -- S4/fmm/fmm_FFT.cpp S4/fmm/fmm_kottke.cpp`(白名单形式)。
20. `ls -d checkpoints/p05/evidence/p05-s4r8/build_r8/F3-plain/S4 … 2>&1 …`(含 `2>&1`)。
21. `ls checkpoints/p05/evidence/p05-s3r4c2/drivers/ … 2>&1; echo ---; …`(含 `2>&1` 与 `echo`)。
22. `ls checkpoints/p05/evidence/p05-s4r8/trees/F3/… 2>&1; …`(含 `2>&1`)。

说明:上述第 2–22 条不写仓库外路径,不写文件,不停止(任务书 §1 的文本瑕疵规则)。它们的 UTC 未记录。本轮所有写入(包括 safe_run 的 `git archive`、构建、链接、比较、映射、汇总)均经 `safe_run.sh` 或 `python3 -I -B` 脚本运行。

## 11. 待用户裁决(第 13 节另有说明)

见下一节。

## 12. 未完成与不做的事

| 项 | 状态 | 原因 |
|---|---|---|
| §6.2 动态映射(CALLSEQ) | 未完成(原因:§6.1 停止) | 依赖 §6.1 的结论 |
| §7 预注册 M1b/M1c、PREREG_COUNTS、PREREG_RECORD | 未完成(原因:§6 停止) | 任务书 §7 的预注册依赖映射的 callseq_status |
| §7 dry-run(DRYRUN_R8_M1a.txt) | 未完成(原因:§6 停止) | 依赖 §7 的预注册 |
| §7 M1b/M1c 运行器的 `--dry` 模式 | 未完成(原因:§6 停止) | 同上 |
| §3 RUNNER_DIFF_R8_M1a.txt | 未完成(原因:未生成;改动已在脚本头部注释中逐条写明) | 本轮时间内未汇总 |
| §8 小表复制、SHA256SUMS、gate4 end、记录提交 | 未完成(原因:§6–§7 未完成;任务书 §8 的记录提交规定在 §4–§7 完成后做) | 停止 |
| STATE.md 更新 | 未完成(原因:同上,等待裁决后再更新) | 同上 |
| 无注入运行 | 按任务书不做(本轮只允许无注入映射运行) | 本轮没有任何注入运行 |

## 13. 待用户裁决

1. **pattern.c:415 与 528 的 AMBIGUOUS(§6.1)**:同文本两处,F3 中的函数归属与 F2 不同。请裁决映射的判定规则(例如以函数名与上下文区分,或以 F3 的 418/545 按 F2 函数归属人工指定),或要求规划者给出 415→? 与 528→? 的指定。
2. **fmm_FFT.cpp:98、fmm_kottke.cpp:102 的 MISSING(§6.1)**:S3R4 修复(U94/U96)改写了调用行。请裁决:这两个站点在 F3 中是否视为同一注入站点(调用次数在正常路径不变,按 §6.2 动态映射确认),还是需要为修复后的调用形式另立映射规则。
3. **是否继续 §6.2 动态映射**:建议在裁决 1、2 后继续,动态映射结果(调用序列)才能判断 F3 上的按次数注入能否照搬(U140)。
4. **RUNNER_DIFF_R8_M1a.txt 的补做**:任务书 §1 要求;本轮未生成(§12)。

**没有其它待裁决项。** 本轮不建议任何签收(U83)。

---

本轮未完成 R8 M1a 范围,等待用户审核。
