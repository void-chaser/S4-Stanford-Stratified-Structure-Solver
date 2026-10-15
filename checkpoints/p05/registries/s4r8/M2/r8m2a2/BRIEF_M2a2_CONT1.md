# P05-S4 R8 M2a2 续1（仍为 r8m2a2，不是 M2b）：修正搜索表与索引推导 → 完成设计 v3、预注册、完整性检查、收尾

> 先读 AGENTS.md、checkpoints/p05/STATE.md、checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a2.md（原任务书全部条款继续有效，本续轮只补充与更正）。
> 第一步：用 write 工具把本续轮任务书原文保存为 `checkpoints/p05/registries/s4r8/M2/r8m2a2/BRIEF_M2a2_CONT1.md`（该路径已在 end 门禁允许列表内；不得改 gate_allow_* 文件）。
> 不运行任何 S4 驱动、运行器、gdb。不做 M2b。不宣布任何阶段完成。工作量不是停止理由；停止条件仍只限原任务书 §1.5（含 ⑧）。
> 你之前派出的后台子代理（层序 / FFT 网格 / 阶段 e）：如已返回，其结论只作交叉核对材料，写入 `$EV/SUBAGENT_CROSSCHECK_R8_M2a2.txt`；如未返回，不再等待。所有表一律由本轮脚本从文件中读取并计算生成，脚本中不得出现写死的结论字符串、行号或数量。

## 0. 续轮开工核对（只读；不重跑 start 门禁，不覆盖 GATE_R8_M2a2_start.txt）
新建 `resume_check_r8m2a2_R3.py`（经 safe_run 运行）→ `$EV/RESUME_CHECK_R8_M2a2_R3.tsv`，逐项核对：
- HEAD=6a4f0031afeda0a3105c9983d5a65a2d847f1488；HEAD:S4=6cff923a…；判定器 sha=d2d04145…
- RULINGS.tsv 前 92855 字节、ERRATA_8.txt 前 67104 字节与 HEAD 版本逐字节相同；U236–U247 各恰好 1 行；E8-91–E8-95 各恰好 1 条
- `git status --short` 每一行都能匹配 gate_allow_r8m2a2_end.txt；`git diff --name-only` 只含 STATE/RULINGS/ERRATA（STATE 此时应未改）
- `S4/` 工作区无改动；`registries/s4r8/M2/r8m2a/` 原 20 个文件 sha 不变
任一不符：停下报告（这属于"真实基线异常"）。

## 1. 执行纪律补充（在原 §1 基础上）
- 标准首段逐字：`REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"`
- `safe_run.sh p05-s4r8/m2a2 --` 后面**只能接本轮脚本文件**（`python3 -I -B testing/d003/stage_s4/<名>_r8m2a2*.py` 或 `sh testing/d003/stage_s4/<名>_r8m2a2*.sh`）。不得接 `python3 -c`、`mv`、`mkdir`、`sh -c`、`true`，也不得直接接可执行文件。需要移动、建目录、运行 harness，一律写进脚本。
- 内联命令不得含 `>` 字符（含 `2>&1`）。读文件用 read，搜索用 grep 工具。
- 每个新脚本运行前，用 grep 工具按原任务书 §1.3 的正则查禁止项，必须 0 行。

## 2. 违规与偏离披露（写入报告表二；同时生成 `$EV/DEVIATIONS_R8_M2a2.tsv`，由脚本解析 safe_run.log 生成，不手抄）
逐条列出 safe_run.log 中 safe_run 后面接的不是本轮脚本文件的记录（时间、命令前 120 字符、是否落盘、仓库内目标）。已知至少有：
- `python3 -I -B -c print('ok')`（07:07:17Z）
- `python3 -I -B -c import sys,os…`（20:35:29Z）
- `mv …inject_r8m2a2_dual_R3.cpp …`（20:35:33Z、20:36:20Z、20:37:00Z）
- `mkdir -p …/build/harness`（20:37:16Z）
- `mv …/build/harness …`（20:39:07Z）、`mv …DUAL_HARNESS…`（20:41:14Z）、`mv …tmp/posctrl …`（20:45:47Z）
- 直接运行 `build/harness_try2/dual_harness…`、`build/harness_try3/dual_harness…`（20:39:22Z–20:40:06Z，共 5 次）

另须写明：dual_harness 只链接桩（`dual_stubs_r8m2a2.cpp`）、不链接 S4。用 nm 脚本证明它没有 S4 符号，结果写入 `HARNESS_NM_R8_M2a2.tsv`。这类运行不在原任务书授权范围内，按偏离披露，由用户裁决是否接受。越界写入（表一）如无，写"无"。

## 3. 装置清单（`apparatus_manifest_r8m2a2.py` → `$EV/APPARATUS_MANIFEST_R8_M2a2.tsv`）
- 对 `testing/d003/stage_s4/` 下全部 `*r8m2a2*` 文件逐行列出：路径、sha256、角色（ACTIVE_SOURCE / ACTIVE_SCRIPT / SUPERSEDED / DRAFT / INCLUDE）、被哪个 BUILD 行使用（用 BUILD_R8_M2a2_R3.tsv、BUILD_R4 与 BUILD_OBJECTS 中的源 sha 匹配，不按名字匹配）、取代它的文件。
- 断言：每个预注册要用的驱动都恰好对应一个 ACTIVE 源文件组合。
- 汇总构建结果生成 `$EV/BUILD_FINAL_R8_M2a2.tsv`：对磁盘上每个最终产物**重算** sha256，并与各 BUILD 表记录比对；不一致标 STALE，STALE 的产物不得进入预注册。原任务书 §4.4 的 BUILD 计数以此表为准。

## 4. 阶段 e 搜索表重做（M2-02；`stage_e_search_r8m2a2_R2.py` → `$EV/STAGE_E_SEARCH_R8_M2a2_R2.tsv`）
原 `STAGE_E_SEARCH_R8_M2a2.tsv` 保留不改，在报告中标为 SUPERSEDED（原因：写死字符串、汇总行、行号错误）。

**A 部分：已登记请求，逐行展开，共 227 行**
- 脚本逐行读取 `registries/s4r6d/U2_STAGE_R6d.tsv`（202 个数据行）与 `SEAM_SITE_STAGE_R6d.tsv`（25 个数据行）。每个数据行输出一行：candidate_id（原 point_id）、来源表与行号、stage（取原表 stage 列）、位置（取原表 basis 或 file:line 列）、stage_e 判定、in_scope_d003、依据。
- 断言 A 部分行数 = 227；按 stage 计数必须等于原表（U2：a2/b197/c1/d2；SEAM：a2/b20/c1/d2），stage e 计数 = 0。
- 阶段定义引用 `registries/s4r6d/ERRATA_6d.txt:48-70`（E6d-3）。

**B 部分：ComputeLayerModes 之外的候选（[源码]，由脚本扫描 `$EV/tree_F3/S4/` 得到行号）**
- 用脚本在 `S4.cpp` 中定位 `Simulation_ComputeLayerModes` 的函数体范围（起始约 2259 行，用花括号配对求结束行）。
- 扫描 `S4.cpp`、`rcwa.cpp`、`fmm/*.cpp` 中所有 `fft_plan_dft_2d`、`fft_plan_exec`、`fft_alloc_complex`、`S4_malloc`、`Simulation_AddFieldToCache` 的调用行。对每一行记录：所在函数（脚本向上找函数头）、是否在 CLM 函数体内、是否经 CLM 调用链到达（fmm_* 内的调用都由 CLM 调用：stage a–d）。
- 规划者读源码得到的已知点（供核对，以脚本输出为准）：
  - GetFieldOnGrid `rcwa.cpp:2155`；分配与计划 `rcwa.cpp:2204-2210`；执行 `rcwa.cpp:2245`；
  - 调用者为 `S4.cpp:3533`（`Simulation_GetFieldPlane`，3471）与 `S4.cpp:4354`；
  - `S4_Simulation_GetPowerFlux` `S4.cpp:2488`；`Simulation_InitSolution` `S4.cpp:1664`；`Simulation_AddFieldToCache` `S4.cpp:4014`（由 PolBasis 在 CLM 内调用 → stage c，不是 e）。
- 范围判定的依据：
  - E6-4（`registries/s4r6/ERRATA_6.txt:49-53`，U5b）：GetFieldOnGrid 在 D003 范围外；
  - MEMORY 中的 D003 判据：位于"模式或缓存是否被安装"的验收路径，或位于 FMM/FFT 失败传播链上；
  - 非 FMM 的 S4_malloc 属于 OUT_OF_SCOPE_D003，去向 S5。
- 若 B 部分全部在范围外，M2-02 = `NOT_FOUND_IN_SCOPE`。脚本最后一行写 `# SUMMARY: A_ROWS=… B_ROWS=… STAGE_E_IN_SCOPE=…`，数字全部由脚本计算。

## 5. 类别 C 搜索表重做（M2-08；`catc_search_r8m2a2_R2.py` → `$EV/CATC_SEARCH_R8_M2a2_R2.tsv`）
原 `CATC_SEARCH_R8_M2a2.tsv` 保留不改，标为 SUPERSEDED。

以下推导链由规划者读源码得到（[源码]，未实测）。执行者须逐条用 read 复核行号，写进表头注释；任何一条与源码不符，就在表中标 `PLANNER_FACT_MISMATCH` 并按源码重推：
1. 构建未定义 `HAVE_LIBFFTW3`，`fft_plan_exec` 走 `kiss_fftnd_checked`（`fmm/fft_iface.cpp:122-131`）。用脚本检查 `build_r8/build-F3-*.log` 与 BUILD_R3 编译命令中的 `-D` 选项，确认没有 `HAVE_LIBFFTW3` 和 `KISS_FFT_USE_ALLOCA`；若定义了 alloca，执行期就没有 malloc（`kiss_fft/_kiss_fft_guts.h:154-163`）。
2. 执行期窗口里只有两处可能分配：
   - `kiss_fft.c:216` 的 `kf_bfly_generic` scratch：只在 radix 不属于 {2,3,4,5} 时走到（`kiss_fft.c:273-277,307-311`）；
   - `kiss_fft.c:392` 的 tmpbuf：只在 fin==fout 时分配。
   `kiss_fftnd` 的 tmpbuf 在计划阶段已分配（`tools/kiss_fftnd.c:44-66`），而 nd 执行时各维的 fin 与 fout 不同（`kiss_fftnd.c:165-200`）。
3. 网格每一维的长度为 `fft_next_fast_size(maxG×resolution)`：resolution=8（`S4.cpp:343`），`fft_next_fast_size` 保证结果只含因子 2、3、5（`fft_iface.cpp:35-46`）。只有当该维所有 G 分量都为 0（allzero）时，长度才取 1（`fmm_FFT.cpp:54-67`；kottke、PolBasis VL/Jones/NV 中对应的段落）。按 `kf_factor`（`kiss_fft.c:320-341`），长度为 1 时 radix=1，走 generic 分支并分配 scratch；只含 2/3/5 因子的长度不会走 generic。**结论：执行期有分配，当且仅当某一维网格长度为 1。**
4. 方形晶格（driver_d003 `Lr={1,0,0,1}`，`testing/d003/src/driver_d003.cpp:72`）用 circular 截断（`S4.cpp:346`、`gsel.c` 的 Gsel_circular 与 G_select），遇到同长度的 G 向量会去掉整个壳层。由此推出：请求 NG 1–4 → 实际 n_G=1；NG 5–8 → 实际 n_G=5；NG 9 → 9。实际 n_G=5 时两维都有非零分量，不存在长度为 1 的维。
5. 1D 晶格（只有 closed1d 使用，`driver_d003.cpp:75`）：实际 n_G = 1+2·⌊(NG−1)/2⌋（`S4.cpp:369-375`），y 维长度为 1。但 closed1d 的 FMM（`fmm_closed.cpp`）里没有 fft 调用（脚本用 grep 计数证明），FFT 只出现在 GetFieldOnGrid 中，属于 E6-4 范围外。

**表的格式**
- 每行为 (mode, NG_requested)，共 9 模式 × NG 2–8 = 63 行。列：
  - lattice、n_G_actual、ngrid_x、ngrid_y（三者由脚本按上述规则计算）；
  - fmm_uses_fft（按模式 grep 对应 fmm_*.cpp 的 `fft_plan_exec` 计数）；
  - exec_alloc_in_fmm（YES/NO）、exec_alloc_outside_fmm（GetFieldOnGrid）；
  - NB_ge_2、依据（file:line 列表）、verdict（FOUND / NOT_FOUND）。
- 如可行，用已有 M0/M1 日志中记录的 n_G 或网格 trace 交叉核对 n_G_actual（只读日志，不运行）。找不到日志就标 `[源码]`。
- 网格之外另起一节 `# CANDIDATES_OUTSIDE_U242_GRID`，列出"1D 晶格 + FFT 类 FMM 模式（fft/kottke/jones/nv/vl），实际 NB≥3"这一候选配置，标 `NEEDS_NEW_DRIVER_SCOPE_EXPANSION`。本轮不出点，列入"需要用户裁决"。
- 若网格内没有 FOUND，M2-08 = `NOT_FOUND`。SUMMARY 行的数字由脚本计算。
- M2-07 的预注册增加 `n_G_actual` 列，取自本表的推导规则（NG=1 也算）。期望值的来源规则不变（U243）。

## 6. 索引推导重做（`index_derivation_r8m2a2_R2.py` → `$EV/INDEX_DERIVATION_R8_M2a2_R2.tsv`）
原表保留，标为 SUPERSEDED。逐点更正：
- **poly 行（M2-01-11…21）**：依据改为 `stage_s3r4c2/driver_s3r4c2_poly.cpp`（快照与 call1/2/3 的行号由脚本定位）和 `stage_s3r4c3/inject_s3r4c3_poly.cpp:9,56`（window 计数在整个进程内累计，不按调用重置）。
  - 对 `win:64`，须给出"第 64 次 window malloc 发生在 call1 内"的证据：引用 M1 已有的命中记录（ADD22 第 13、15、17、19、21 行对应的 M1 结果或日志行号）。给不出就标 `UNRESOLVED_INDEX`。
- **init 行**：依据 `stage_s3r4/inject_s3r4_init.cpp`（win 在窗口内计数，init 在窗口外计数），以及 `driver_r6b_state.cpp:25`（k_fail=1、k_preretry=2、k_retry=3，适用于 inj_call=1）。
- **M2-05**：fft 模式下每个图案层在 FMM 翻译单元内有 2 次 S4_malloc（`fmm/fmm_FFT.cpp:75` work、`:83` discval；与 `registries/s4r3/CALLSEQ.tsv` 中 once/fft/F 的 6144 B、16 B 两行一致）。均匀层不进 FMM（`S4.cpp` CLM 中 `nshapes==0` 分支）。由此：
  - P0：NTH=1，目标层 0；P2：NTH=1，目标层 2；PP1：NTH=1，目标层 1；
  - **PP2：NTH=3**，目标层 2（原表写 2，会失败在第 1 层的 discval，错误）。
- **M2-04(b)（layers-dual PP1）**：call1 在第 1 层失败（NTH=1）。call2 重算第 1 层（#2、#3 成功），再到第 2 层的 #4，所以 **NTH2=4**，失败在第 2 层。call3 只算第 2 层（#5、#6）后恢复。原表写 NTH2=2，会第二次失败在第 1 层，与 U244(b) 不符，必须更正。
- **M2-04(a)**：NTH=1、NTH2=2 在同一层（第 1 层），保留。
- 每个推导都写依据（文件:行号），全部标 INFLUENCED。另加一列 `m2b_hit_check`：M2b 运行时用来核对实际失败层的 HIT 日志特征。

## 7. M2-10 gdb 脚本更正
新建 `m210_b_r8m2a2_R2.gdb`（原文件保留，标为 SUPERSEDED）。
- 断点由 `m210_bp_r8m2a2.py` 扫描 `$EV/tree_B/S4/S4.cpp` 中 ComputeLayerModes 函数体内全部 `return 20;` 生成。规划者已知的有 2362、2416、2432，以脚本输出为准。另外，B 的 FMM 返回检查若存在，也设断点；不存在就写明"B 无此检查 [源码]"。
- 驱动与 argv 不得自拟，取自 D016 / vl NG=1 的登记行（`registries/s4r7/RESULTS_R7_M1_CTRL_REJUDGE_POSTHOC.tsv` 中 vl NG=1 的行，及其指向的 R7 M1 注册表中的 driver 与 argv）。要用的 B dbg 驱动必须是同一驱动源文件链接 B dbg 库的结果；`r6bstate-B-dbg` 与登记驱动不同族时，在 build 脚本中补建同族 B dbg 驱动，并写入 BUILD_FINAL。
- 不运行 gdb。

## 8. 继续原任务书剩余步骤（全部按原条款）
1. §4.2 设计表 v3：`design_r8m2a2.py` → `M2_DESIGN_R8_M2a2.tsv/.md`。M2-02 引用 `STAGE_E_SEARCH_R8_M2a2_R2.tsv`，M2-08 引用 `CATC_SEARCH_R8_M2a2_R2.tsv`。§4.9 的完整性检查改为读取 `_R2` 搜索表（行数 > 0，且 SUMMARY 与类别一致）。
2. §4.6 预注册：`prereg_r8m2a2.py`。只用 BUILD_FINAL 中非 STALE 的产物，只用 `INDEX_DERIVATION_R8_M2a2_R2.tsv`。断言条款与原文相同（item×tree 计数之和 = 总行数；每项点数 = 设计表点数；M2-01 至少 9 个对照组）。写完后不得修改。
3. §4.7：阳性对照已有 `_R2` 通过的结果；若判定脚本在本续轮被修改，就以 `_R3` 重跑全部情形。
4. §4.8：报告核对标记在原列表基础上加 `M2A2_STAGE_E_A_ROWS=`、`M2A2_STAGE_E_B_ROWS=`、`M2A2_CATC_ROWS=`、`M2A2_DEVIATIONS=`、`M2A2_SUPERSEDED_FILES=`，全部由脚本重算。
5. §4.9 完整性检查：任一项 FAIL 就按停止条件 ⑧ 停下（不提交）。
6. §7 收尾，顺序固定：
   - registries 复制范围在原清单基础上增加 `BRIEF_M2a2_CONT1.md`（已在该目录）、RESUME_CHECK_R3、DEVIATIONS、HARNESS_NM、APPARATUS_MANIFEST、BUILD_FINAL、两份 `_R2` 搜索表、INDEX_DERIVATION_R2、DUAL_HARNESS，以及被取代的原搜索表与原索引表（原名复制，不改名）。
   - STATE ≤ 8192 字节；end 门禁 FAILS=0 才提交；提交后运行 postcommit。
   - 提交信息仍用原任务书 §7.6 的模板，在 `posctrl A-E;` 后插入 `stage-e/catC tables regenerated (R2), index derivation R2, deviations disclosed;`。

## 9. 报告中"需要用户裁决"一节只列以下内容（各附支撑表路径）
- M2-02 NOT_FOUND_IN_SCOPE 的去向；
- M2-08 NOT_FOUND，以及网格外候选（1D 晶格 + FFT 类模式）是否扩大范围；
- 本轮全部偏离（DEVIATIONS 表，含 dual_harness 运行）是否接受；
- 任何 UNRESOLVED_INDEX、BUILD_FAILED、NEEDS_S4_CHANGE、STALE 产物。

## 10. 最终回复（简短中文）
按原任务书 §8 列出，另加：被取代文件的数量、两份 `_R2` 搜索表的 SUMMARY 行原文、DEVIATIONS 条数、索引更正前后对照（PP2、M2-04(b)）。
不得出现"签收""已修好""已验证"等字样。
