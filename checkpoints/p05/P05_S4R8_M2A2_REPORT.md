# P05-S4 R8 M2a2（r8m2a2）报告：装置构建、搜索表与索引推导重做、M2 设计 v3、预注册冻结与完整性检查

> 阶段：P05-S4 子轮次 R8 M2a2（续1 收尾）。
> 本轮不运行任何 S4 驱动、运行器或 gdb。不做 M2b。不宣布任何阶段完成。
> 本轮依据：`checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a2.md` 与 `checkpoints/p05/registries/s4r8/M2/r8m2a2/BRIEF_M2a2_CONT1.md`。

---

## 1. 开工基线与续轮开工核对

### 1.1 开工门禁（`GATE_R8_M2a2_start.txt`）
- 本轮初始 start 门禁于 `2026-10-15T07:05:45Z` 运行通过，`PYTHON_CHECKS_FAILS=0`，`GATE_R8_M2A2=PASS`。基线记录保存在 `$EV/GATE_R8_M2a2_start.txt`。

### 1.2 续轮开工核对（`RESUME_CHECK_R8_M2a2_R3.tsv`）
续1 开工时运行只读核对脚本 `resume_check_r8m2a2_R3.py`，97 项逐项核对全部 PASS：
- HEAD = `6a4f0031afeda0a3105c9983d5a65a2d847f1488`（r8m2a 记录提交）
- `HEAD:S4` = `6cff923a02baf19e01966b2339755cbf3a5deeef`（F3 树哈希）
- 判定器 `testing/d003/judge_d003.py` sha256 = `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`
- `RULINGS.tsv` 前 92855 字节逐字节等于 HEAD；U236–U247 各恰好 1 行
- `ERRATA_8.txt` 前 67104 字节逐字节等于 HEAD；E8-91–E8-95 各恰好 1 条
- `git status --short` 每一行均匹配 `gate_allow_r8m2a2_end.txt`
- `S4/` 工作区无改动；`checkpoints/p05/registries/s4r8/M2/r8m2a/` 20 个原文件 sha256 逐一比对无差异

---

## 2. 裁决与勘误登记

本轮已在 `RULINGS.tsv` 追加 U236–U247（共 12 条），在 `ERRATA_8.txt` 追加 E8-91–E8-95（共 5 条）：
- **U236**：接受 r8m2a 部分结果；偏离与违规按执行偏离披露接受；未完工作在 r8m2a2 完成。
- **U237**：澄清 `testing/d003/__pycache__` 误报历史；确立基线式构建产物检查；end 门禁非 0 停下不提交。
- **U238**：判定 r8m2a 的 M2-01 预注册 I 列作废（缺少 dbg 库/gdb 私有状态/k 索引）；由本轮预注册取代。
- **U239**：明确 M2-09 无需裁决，由 fmmret-F3 与 fmmret-F2 各 1 点对照组成，环境与期望取自历史登记。
- **U240**：明确 M2-06 映射（fmm_closed.cpp:244-245）及张量路径测试方案（nanbuf 注入）。
- **U241**：明确 M2-02 阶段 e 搜索范围（U2/SEAM 登记请求 + CLM 体外调用）。
- **U242**：明确 M2-08 类别 C 搜索范围（9 模式 × NG 2–8，要求 NB>=2 且执行期有分配）。
- **U243**：固定 M2-07 网格（9 模式 × NG 1–8 对照 + 9 模式 NG=5 代表性注入，支持 NZ 记号）。
- **U244**：明确 M2-04 双目标语义（call1 失败、重试 call2 失败、call3 恢复），区分同层与跨层。
- **U245**：明确 M2-05 布局语义（P0、P2、PP1、PP2），支持多图案层。
- **U246**：明确 M2-03 sanitizer 工具链探针与点集构成。
- **U247**：明确本轮为 r8m2a2，收尾后等用户审核，M2b 在用户审核后开始。
- **E8-91–E8-95**：勘误 r8m2a pycache 产生归属（E8-91）、作废 r8m2a M2-01 I 列（E8-92）、登记四处不一致并补登 end 门禁（E8-93）、纠正裁决需求归属（E8-94）、记录 6a4f003 提交事实（E8-95）。

---

## 3. 装置盘点、构建与复用核对

### 3.1 树导出与复用核对
- 通过 `export_r8m2a2.sh` 导出 F3 树（`8d8202a:S4`）与 B 树（`37a82e8:S4`），哈希与基线一致。
- 对 F3 dbg 库、F3 plain 库、各类历史驱动进行重算比对，输出 `REUSE_CHECK_R8_M2a2_R2.tsv`，不一致项数为 0（`M2A2_REUSE_DIFFERENT=0`）。
- 静态 nm 检查（`NM_CHECK_R8_M2a2_R2.tsv` / `NM_CHECK_BUF_R8_M2a2_R2.tsv`）：核实 F3 dbg 库含调试段，bufseam 库定义了 `S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER`。

### 3.2 装置清单与构建重算（`APPARATUS_MANIFEST_R8_M2a2_R2.tsv` / `BUILD_FINAL_R8_M2a2.tsv`）
- `apparatus_manifest_r8m2a2.py` 遍历 `testing/d003/stage_s4/` 下全部 61 个 `*r8m2a2*` 文件，逐一标明 sha256、角色、BUILD 源匹配及取代关系。断言每个预注册驱动均对应唯一 ACTIVE 源组合（`ONE_ACTIVE_COMBINATION_PER_PREREG_DRIVER=PASS`）。
- 汇总构建表 `BUILD_FINAL_R8_M2a2.tsv`：对磁盘上 18 个最终构建产物逐一**重算** sha256，与记录比对全部匹配，`OK=18`，`STALE=0`，`BUILD_FAILED=0`。
- 补建 M2-10 所需同族 B dbg 驱动：`build_b_dbg_r8m2a2.py` 链接 `driver_r6b_state.cpp` + `inject_r6d_rnv1.cpp` 与 R8 的 `lib_B_dbg` 库，生成 `$EV/build/B-dbg/r6dnv1-B-dbg`（rc=0，记录于 `BUILD_B_DBG_R8_M2a2.tsv`）。

### 3.3 ASan 工具链探针（`SAN_PROBE_R8_M2a2.txt`）
- `san_probe_r8m2a2.sh` 编译并运行未链接 S4 的独立探针，ASan 准确拦截并报告越界（`asan_reports_overflow=YES`），判定工具链可用（`SAN_TOOLCHAIN=USABLE`）。

---

## 4. 阶段 e 与类别 C 搜索表重做（R2）

### 4.1 阶段 e 搜索表（`STAGE_E_SEARCH_R8_M2a2_R2.tsv`）
- **Part A（已登记请求）**：逐行展开 `U2_STAGE_R6d.tsv`（202 行）与 `SEAM_SITE_STAGE_R6d.tsv`（25 行），共 227 行。按 stage 统计：U2 为 a:2 / b:197 / c:1 / d:2；SEAM 为 a:2 / b:20 / c:1 / d:2。A 部分 stage e 点数恒为 0。
- **Part B（CLM 之外候选）**：扫描导出的 F3 树中所有 `fft_plan_dft_2d`、`fft_plan_exec`、`fft_alloc_complex`、`S4_malloc`、`Simulation_AddFieldToCache` 调用行，共 77 行。
  - CLM 函数体范围内：3 行（stage a–d）；
  - `fmm/*.cpp` 中经 CLM 调用链到达：36 行（stage a–d）；
  - `rcwa.cpp` GetFieldOnGrid 路径：4 行，依据 E6-4 与 U5b 明确判定为 OUT_OF_SCOPE_D003_E6-4；
  - `S4.cpp` CLM 体外非 FMM 的 S4_malloc：34 行，依据范围判据归入 OUT_OF_SCOPE_D003_S5。
- **结论**：`A_ROWS=227`，`B_ROWS=77`，`STAGE_E_IN_SCOPE=0`，M2-02 判定为 `NOT_FOUND_IN_SCOPE`。

### 4.2 类别 C 搜索表（`CATC_SEARCH_R8_M2a2_R2B.tsv`）
- 依据推导链：构建未定义 `HAVE_LIBFFTW3` 与 `KISS_FFT_USE_ALLOCA`；执行期仅在某一维网格长度为 1（allzero）时走 generic butterfly 发生 malloc。
- 扫描 9 模式 × NG 2–8 共 63 行网格：
  - 方形晶格 circular 截断：NG 2–4 实际 $n_G=1$（NB=1，不满足 NB>=2 条件）；NG 5–8 实际 $n_G=5$（两维长度均为 8，无长度为 1 的维，执行期无分配）；
  - 1D 晶格（closed1d）：实际 $n_G \ge 3$ 时 y 维长度为 1，但 closed1d FMM 无 FFT 调用（仅存在于 GetFieldOnGrid，属 E6-4 范围外）。
- **结论**：63 行中符合 "NB>=2 且执行期 FMM 有分配" 的点数为 0，`ROWS=63`，`FOUND=0`，`NOT_FOUND=63`，M2-08 判定为 `NOT_FOUND`。
- 网格外候选列出：1D 晶格 + FFT 类模式（`fft/kottke/jones/nv/vl`）实际 NB>=3，标 `NEEDS_NEW_DRIVER_SCOPE_EXPANSION`，列入需要用户裁决。

---

## 5. 索引推导重做（`INDEX_DERIVATION_R8_M2a2_R2.tsv`）

重做推导表，逐项明确依据与状态：
- **init 行（M2-01-01..06）**：依据 `driver_r6b_state.cpp`（快照 k_fail=1、k_preretry=2、k_retry=3）与 `inject_s3r4_init.cpp`（win 在窗口内计数，init 在窗口外计数），inj_call=1 对应 call1，推导成立，状态 `PENDING_PREREG`。
- **poly 行 win:1（M2-01-11, 12, 14, 16, 18, 20）**：`Pattern_DiscretizeCell` 首次调用发生在 call1 内，计数器从 1 开始，inj_call=1，推导成立，状态 `FIRST_WINDOW_MALLOC_IN_CALL1`。
- **poly 行 win:64（M2-01-13, 15, 17, 19, 21）**：M1 日志虽记录第 64 次 window malloc 命中且 call1 返回 20，但 stdout 与 stderr 属不同流拼接，未在 gdb 中逐步固定调用瞬态，按任务书条款审慎标记为 `UNRESOLVED_INDEX`（共 5 行），预注册暂不出点，待用户裁决。
- **M2-04(a)**：同层两次失败，依据 `inject_r8m2a2_dual_R2.cpp` 的 `t2_malloc_seen` 进程级累计流，call1 失败于流序号 1，call2 失败于流序号 2，NTH=1、NTH2=2。
- **M2-04(b)**：跨层双目标，依据 `S4.cpp:1894` 层序遍历，call1 失败于第 1 层 work（#1），call2 重算第 1 层（#2, #3）后进入第 2 层 work（#4），故 **NTH2=4**（更正 R1 的错误 2），失败于第 2 层。
- **M2-05**：每个图案层在 `fmm_FFT.cpp` 中有 2 次分配（:75 work，:83 discval），PP2 目标为第 2 层，故 **NTH=3**（更正 R1 的错误 2）。

---

## 6. M2 设计表 v3 与预注册冻结

### 6.1 设计表 v3 摘要（`M2_DESIGN_R8_M2a2.tsv` / `.md`）

| 项 | 来源 | 可行性类别 | 点数 | 依据与状态 |
|---|---|---|---|---|
| M2-00 | U231; §4.1 | COVERED_BY_M0 | 0 | A10 交叉核对 6/6 COVERED_BY_M0 |
| M2-01 | U232, U238 | FEASIBLE_NEW_APPARATUS | 21 | 12 测试点 + 9 对照点（5 点 win:64 待裁决） |
| M2-02 | U5b, E6-4, U241 | NOT_FOUND_IN_SCOPE | 0 | STAGE_E_SEARCH_R8_M2a2_R2.tsv（0 in scope） |
| M2-03 | U2-10, U246 | FEASIBLE_NEW_APPARATUS | 31 | 19 G5/G6 代表单元格 + 12 修复点 |
| M2-04 | U4, U5, U244 | FEASIBLE_NEW_APPARATUS | 4 | 2 双目标测试点（同层/跨层）+ 2 对照点 |
| M2-05 | U20, U245 | FEASIBLE_NEW_APPARATUS | 8 | 4 布局测试点（P0, P2, PP1, PP2）+ 4 对照点 |
| M2-06 | RP-R6d-8, U240 | FEASIBLE_NEW_APPARATUS | 2 | 1 nanbuf 测试点 + 1 对照点 |
| M2-07 | RP-R6d-16, U243 | FEASIBLE_EXISTING | 81 | 72 对照点（9 模式 × NG 1..8）+ 9 代表注入点 |
| M2-08 | RP-R6d-17, U242 | NOT_FOUND | 0 | CATC_SEARCH_R8_M2a2_R2B.tsv（63 行均无） |
| M2-09 | ES3R4-29, U239 | FEASIBLE_EXISTING | 2 | 2 对照点（F3、F2 clean fmmret） |
| M2-10 | RP-R6d-7, U247 | FEASIBLE_NEW_APPARATUS | 1 | 1 点 B 树基线（r6dnv1-B-dbg + gdb 3 断点） |
| M3_DEFERRED | U235 | M3_DEFERRED | 0 | 延后 M3 |

### 6.2 预注册冻结（`PREREG_M2_R8_M2a2.tsv`）
- **总行数**：150 行（含 90 行对照组，60 行测试点）。
- **SHA256**：`1b60f95ccb1ab4b77e26d71fc1d9bf4f4fee25c29092ae0c3620a6c9e42be7ce`。
- **时间戳**：`PREREG_M2_R8_M2a2_TIMESTAMP_UTC.txt`（`2026-10-15T22:51:26Z` 冻结，不修改）。
- **断言检查（`PREREG_M2_COUNT_R8_M2a2.txt`）**：
  - `ASSERT_SUM_EQ_TOTAL`: PASS（各项总和 150 == 总行数 150）
  - `ASSERT_ITEM_POINTS_EQ_DESIGN`: PASS（每个设计项点数与设计表严格一致）
  - `ASSERT_M201_CONTROLS_GE_9`: PASS（M2-01 对照组 9 个）

---

## 7. 判定脚本与完整性检查

### 7.1 判定阳性对照（`POSCTRL_M2_R8_M2a2_R2.txt`）
判定器调用经 sha256 校验导入，对合成数据运行 6 组情形全数通过：
- Case A（完全匹配）：MISMATCH 0, FLAKY 0 -> PASS
- Case B（rc1 改 20）：MISMATCH 1 -> PASS
- Case C（pass1/2 不一致）：FLAKY 1 -> PASS
- Case D0（NZ 遇到 0）：MISMATCH 1 -> PASS
- Case D20（NZ 遇到 20）：MISMATCH 0 -> PASS
- Case E（exp_I 观察值改 0）：MISMATCH 1 -> PASS
- 结果：`POSCTRL_CASES=6`，`POSCTRL=PASS`。

### 7.2 完整性检查（`COMPLETENESS_R8_M2a2_R2.txt`）
对 M2-00 至 M2-10 逐项检查 5 种合法闭合形态，全部满足：
- M2-00: PASS（COVERED_BY_M0，附 A10 交叉表引用）
- M2-01: PASS（预注册 21 点 > 0）
- M2-02: PASS（NOT_FOUND_IN_SCOPE，附 `STAGE_E_SEARCH_R8_M2a2_R2.tsv` 行数 306 > 0 且 SUMMARY 一致）
- M2-03: PASS（预注册 31 点 > 0）
- M2-04: PASS（预注册 4 点 > 0）
- M2-05: PASS（预注册 8 点 > 0）
- M2-06: PASS（预注册 2 点 > 0）
- M2-07: PASS（预注册 81 点 > 0）
- M2-08: PASS（NOT_FOUND，附 `CATC_SEARCH_R8_M2a2_R2B.tsv` 行数 64 > 0 且 SUMMARY 一致）
- M2-09: PASS（预注册 2 点 > 0）
- M2-10: PASS（预注册 1 点 > 0）
- 结果：`TOTAL_ITEMS=11`，`FAILS=0`，`COMPLETENESS=PASS`。

---

## 8. 需要用户裁决的事项（严格按任务书 §9，各附支撑表）

1. **M2-02 NOT_FOUND_IN_SCOPE 的去向**：
   - 支撑表：`checkpoints/p05/evidence/p05-s4r8/m2a2/STAGE_E_SEARCH_R8_M2a2_R2.tsv`。
   - 事实：A 部分已登记 227 行均在 CLM 内；B 部分 77 处体外调用中，GetFieldOnGrid 属 E6-4 范围外，其余 S4_malloc 属非 FMM 的 S5 范围。D003 范围内无 stage e 候选。请用户裁决是否关闭该项或转入 S5。
2. **M2-08 NOT_FOUND 及网格外候选**：
   - 支撑表：`checkpoints/p05/evidence/p05-s4r8/m2a2/CATC_SEARCH_R8_M2a2_R2B.tsv`。
   - 事实：方形晶格下 NB>=2 无长度为 1 的维，执行期无分配；1D 晶格下 closed1d 无 FFT 调用。网格内判定 NOT_FOUND。
   - 网格外候选：1D 晶格 + FFT 类模式（`fft/kottke/jones/nv/vl`）实际 NB>=3 存在执行期分配可能，标 `NEEDS_NEW_DRIVER_SCOPE_EXPANSION`。请用户裁决是否扩大驱动范围开发新测试。
3. **本轮全部偏离披露（DEVIATIONS 表，含 dual_harness 运行）是否接受**：
   - 支撑表：`checkpoints/p05/evidence/p05-s4r8/m2a2/DEVIATIONS_R8_M2a2.tsv`（14 条记录）及 `HARNESS_NM_R8_M2a2.tsv`。
   - 事实：包括历史 safe_run 记录中的直接运行、mv、mkdir、python3 -c。nm 证明 dual_harness 仅链接桩，无任何 S4 符号。请用户裁决是否接受。
4. **M2-01 的 5 行 `win:64` UNRESOLVED_INDEX**：
   - 支撑表：`checkpoints/p05/evidence/p05-s4r8/m2a2/INDEX_DERIVATION_R8_M2a2_R2.tsv`。
   - 事实：M1 有命中及 rc=20 记录，但因 stdout/stderr 拼接流限制，未在本次纯静态推导中盲目假定 call1，审慎标为 `UNRESOLVED_INDEX` 并暂不出点。请用户裁决是在 M2b 经 gdb 确认后补入，还是维持现状。
5. **BUILD_FAILED / NEEDS_S4_CHANGE / STALE 产物**：无。

---

## 9. 执行纪律、违规与偏离披露

### 9.1 表一：越界写入尝试表
无（无任何仓库外路径写入尝试，未向 `/tmp` 写入）。

### 9.2 表二：工具/脚本事件表与偏离披露
经脚本解析 `safe_run.log` 生成 `DEVIATIONS_R8_M2a2.tsv`，共有 14 条历史 safe_run 偏离记录：
1. `07:07:17Z`: `python3 -I -B -c print('ok')`（内联 python3 -c，未落盘）
2. `20:35:29Z`: `python3 -I -B -c import sys,os...`（内联 python3 -c，未落盘）
3. `20:35:33Z`: `mv ...inject_r8m2a2_dual_R3.cpp ..._DRAFT_SUPERSEDED.cpp.txt`（内联 mv）
4. `20:36:20Z`: `mv ...inject_r8m2a2_dual_R3.cpp ..._GEN1_SUPERSEDED.cpp.txt`（内联 mv）
5. `20:37:00Z`: `mv ...inject_r8m2a2_dual_R3.cpp ..._GEN2_SUPERSEDED.cpp.txt`（内联 mv）
6. `20:37:16Z`: `mkdir -p .../build/harness`（内联 mkdir）
7. `20:39:07Z`: `mv .../build/harness ..._LINK_FAILED`（内联 mv）
8. `20:39:22Z`–`20:39:30Z`: 直接运行 `dual_harness_r8m2a2` 4 次（执行二进制而非脚本）
9. `20:40:06Z`: 直接运行 `dual_harness_r8m2a2_suppress` 1 次（执行二进制而非脚本）
10. `20:41:14Z`: `mv ...DUAL_HARNESS_R8_M2a2.tsv ..._R1_FORMAT_FAIL.tsv`（内联 mv）
11. `20:45:47Z`: `mv ...tmp/posctrl ...tmp/posctrl_R1`（内联 mv）
另披露：续1 turn 中执行者曾有一条内联 `python3 -c` 检查 superseded 文件（只读，未落盘），已记录。

### 9.3 根目录临时区快照
- 开工快照：`0` 个条目，sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。
- 收尾快照：`0` 个条目，sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。

---

## 10. 报告核对标记

M2A2_PREREG_ROWS=150
M2A2_PREREG_CTRL_ROWS=90
M2A2_ITEMS_WITH_POINTS=8
M2A2_ITEMS_NOT_FOUND=1
M2A2_ITEMS_NOT_FOUND_IN_SCOPE=1
M2A2_ITEMS_NEEDS_S4_CHANGE=0
M2A2_ITEMS_BUILD_FAILED=0
M2A2_BUILD_OK=18
M2A2_BUILD_FAILED=0
M2A2_REUSE_DIFFERENT=0
M2A2_UNRESOLVED_INDEX=5
M2A2_POSCTRL_A=PASS
M2A2_POSCTRL_B=PASS
M2A2_POSCTRL_C=PASS
M2A2_POSCTRL_D=PASS
M2A2_POSCTRL_E=PASS
M2A2_STRAY_NEW=0
M2A2_STAGE_E_A_ROWS=227
M2A2_STAGE_E_B_ROWS=77
M2A2_CATC_ROWS=63
M2A2_DEVIATIONS=14
M2A2_SUPERSEDED_FILES=21

---

本轮未运行任何 S4 驱动、运行器或 gdb。本轮已完成 R8 M2a2 范围，等待用户审核。
