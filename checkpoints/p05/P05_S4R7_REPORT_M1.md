# P05-S4 R7 报告 里程碑 M1(RNV1 回归,R7 的续段)

**状态:本轮未完成 R7 范围(M1 已完成,M2、M3 未开始)。本段未宣布任何阶段完成或签收。P05-S3、P05-S4 未签收。S4/ 未修改。**

M1 的判定结果:F2 上 RNV1 相关点 90/90 MATCH(两遍一致,无 FLAKY)。另有 18 个无注入对照行被判 MISMATCH,原因是预注册生成器的列错位(E7-8),对照的实测 rc 与预注册字符串逐项相等(18/18)。这 18 行按规则不改、如实报告,等待用户裁决。

规则依据:`AGENTS.md`;R7 原任务书 `checkpoints/p05/briefs/P05_S4R7_BRIEF.md`;续任务书 `checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT1.md`;勘误 `checkpoints/p05/registries/s4r7/ERRATA_7.txt`(E7-1..E7-11)。

---

## 1. 门禁与前置(第一段已完成,此处复述)

- 门禁复核 `GATE_R7_CONT1.txt`:PASS。HEAD `8e13729`;F2 树 `e124925f…`;判定器 `d2d04145…`;`/tmp` 为空。
- 第一段提交 `8a71b3f`(part 1)。

## 2. 行号清点(续任务书第 3 节第 1 条)

`checkpoints/p05/evidence/p05-s4r7/LINEMAP_F_F2_R7.tsv`(grep -n 于 `git show` 的结果)。F→F2 只改 `pattern.c` 与 `S4_internal.h`(`git diff --stat`),`S4.cpp` 与 `fmm/*.cpp` 行号不变。

| 位置 | F | F2 |
|---|---|---|
| cg 的 malloc(work) | 1251 | 1253 |
| rect 的 malloc(work) | 1477 | 1489 |
| rect 的 malloc(iwork) | 1481 | 1499 |
| tri 的 malloc(work) | 1656 | 1679 |
| tri 的 malloc(iwork) | 1660 | 1689 |

脚本引用的行号只在注释中(`r5_rnv1_malloc_count.gdb`、`s3r3_branch_gdb.gdb`);断点用函数名。因此无需改脚本,`RUNNER_DIFF_R7` 中无行为行改动。

## 3. 驱动与映射

- tri dbg 驱动(F、F2)链接成功,记录于 `DRIVERS_R7_cont1.tsv`(不改 `DRIVERS_R7.tsv`)。
- jones/fftjones 窗口映射 `RNV1_JONES_MAP_R7.tsv`:F dbg 上无注入运行全部 6 个点(rc 0),gdb 实测窗口内 malloc 为 1477、1481、1251(M=1,2,3),窗口外 806 不计。
- tri vl/jones NG9 窗口映射(`gdb_map_F_tri_{vl,jones}_ng9_run2.log`):1656、1660、1251(M=1,2,3)。
- **字节数未测**(gdb 断点只打印调用者),映射表明确不声称字节数。

## 4. M1 预注册(运行前写入,INFLUENCED)

`REGISTRY_S4_PRE_R7_M1.tsv`,生成器 `testing/d003/stage_s4r7/make_prereg_m1_r7.py`。sha256 `db52957355afadf6…`(完整值见 `REGISTRY_S4_PRE_R7_M1.sha256`),UTC `2026-10-12T11:05:20Z`。共 108 行:

| 组 | 行数 | 说明 |
|---|---|---|
| G7 | 36 | RNV1 nv/vl/fftnv/fftvl × NG1/5/9 × M1–3,F 类别从 R6d 源行读取(CRASH),F2 期望 REPORTED_FAILURE |
| G8 | 6 | tri nv NG9 M1–3,F CRASH,F2 REPORTED_FAILURE(复制自 S3R3 C2) |
| 4.2 | 48 | jones/fftjones × NG1/5/9 × M1–3(F 与 F2 各 18)及 tri vl/jones NG9 × M1–3(F 与 F2 各 6);F 期望 CRASH,F2 期望 REPORTED_FAILURE;标注"无历史 F 实测" |
| 对照 | 18 | F2 无注入,期望 rc 值读自 `RESULTS_R7_NOINJECT_run1.tsv`(见 E7-8) |

## 5. 运行与两遍结果(run2 标签)

脚本 `testing/d003/stage_s4r7/run_m1_r7.py`;判定 `judge_d003.classify`(导入,未改);每点一次运行,无 gdb。

`RESULTS_R7_M1_pass1_run2.tsv` 与 `RESULTS_R7_M1_pass2_run2.tsv`:

| 两遍 | MATCH | MISMATCH | 说明 |
|---|---|---|---|
| pass1 | 90 | 18 | 18 = 对照行(E7-8) |
| pass2 | 90 | 18 | 与 pass1 逐点相同(0 处差异) |

- F2 注入点 63 个:`RC first` 全为 20,window k=1 返回 −11(逐点读取 `win1_rc`)。
- F 注入点 27 个:全部 signal 11(CRASH),窗口未返回。
- FLAKY:0。

### 5.1 REGRESS 汇总(`REGRESS_R7_M1.tsv`,逐点见文件)

| 组 | 树 | verdict | 计数 |
|---|---|---|---|
| G7 | F2 | IMPROVED_AS_EXPECTED(F CRASH → F2 REPORTED_FAILURE,规则 4(a)) | 36 |
| 4.2 | F | MATCH(CRASH) | 24 |
| 4.2 | F2 | MATCH(REPORTED_FAILURE;无 F 实测,不标 IMPROVED,见 E7-9) | 24 |
| G8 | F | MATCH | 3 |
| G8 | F2 | MATCH | 3 |
| 对照 | F2 | MISMATCH(列错位,rc 实测相等,见 E7-8) | 18 |
| — | — | REGRESSION | 0 |
| — | — | FLAKY | 0 |

## 6. gdb 链(续任务书第 5 节;实测到哪一层)

`GDB_CHAIN_SUMMARY_R7.tsv`。F2 dbg,NG9。

| 模式 | M | pattern_generate_flow_field 返回 | FMMGetEpsilon_PolBasisJones 返回 | ComputeLayerModes rc | win k=1 |
|---|---|---|---|---|---|
| jones | 1 | −11(gdb finish) | **未读到** | 20(RC first) | −11 |
| jones | 3 | −11(gdb finish) | **未读到** | 20(RC first) | −11 |
| fftjones | 1 | −11(gdb finish) | **未读到** | 20(RC first) | −11 |

**说明(E7-10):** `finish` 会在第一个返回点停止程序。因此 finish 运行只能读到 `pattern_generate_flow_field` 的返回值;`FMMGetEpsilon_PolBasisJones` 的返回值**未读到**,不是 "−11"、不是 "0",也没有用源码补。入口运行(continue-only)确认了调用顺序:`FMMGetEpsilon_PolBasisJones` → `pattern_generate_flow_field` → 注入 → `ComputeLayerModes`。`ComputeLayerModes` 的 rc 来自驱动的 `RC first 20`,不是 gdb 读取。

早先两次 jones 尝试使用 finish 版本,程序在 `Simulation_ComputeLayerModes` 处停止、未达注入(rc 0),日志保留,不计入结果。两次尝试所用脚本为 `testing/d003/stage_s4r7/gdb_chain_jones_r7.gdb`(同时含 finish),已被 `gdb_chain_jones_entry_r7.gdb`(仅入口)与 `gdb_chain_jones_finish_r7.gdb`(仅返回值)取代;原脚本保留在仓库中,未被用于任何计入结果的运行。

## 7. 离线表(U36)

`VL_NG1_SPLIT_R7.tsv`,只读汇总 M1 G7 的 nogdb.out(vl、fftvl NG1,M1–3,两遍共 12 行)。

- 全部 12 行:window k=1 = −11,k=2 = −10,k=3 = −10,RC first = 20(与期望一致,`matches_expectation` = YES)。
- 注意:`mallocs_seen` 统计的是两次调用的窗口 malloc 总数(7、8、9),不是单个窗口。

## 8. RP-R6d-1 状态

**F2 回归 REPORTED_FAILURE:两遍均为 MATCH 的 F2 注入点共 63 个(G7 36 个 RNV1 窗口点,4.2 的 24 个 F2 点,以及 G8 的 3 个 tri 点中的 F2 行)。** 注意:这 63 个数字与 M1 总 MATCH 90 不同,90 还包括 F 侧的 CRASH 行(24 + 3)。"F2 回归 REPORTED_FAILURE 63/63 两遍"是正确的表述;不得写 "90/90 REPORTED_FAILURE"。不是"已修好",不是"已验证"。这些是 F2 回归的 REPORTED_FAILURE 结果,不构成 S4 修复后的验证结论。

## 9. 需要用户裁决的事项

1. **E7-8 的 18 个对照行**:是否按生成器列错位接受为"非结果错误"(建议),或要求重新判定。注册表按规则未改。
2. **M2 是否开工**(G1–G4:R3 141 点、R4 矩阵与 seam、R5 M=2 36 点、R6-1 TWICE 12–16)。
3. **P05-S3 是否签收**(U35:待 R7 里程碑结果交用户后决定)。
4. **U38 的分类**(pattern.c 的其余 malloc)仍在 M3,未做。
5. **FMMGetEpsilon_PolBasisJones 返回值未读到**:若需要逐层返回值,需要新的 gdb 方法(不用 finish),用户是否接受此为 M1 的已知限制。

## 10. 未完成与未做

- M2(G1–G4)与 M3(G5、G6、U38 分类、R7 收尾报告):**未开始**。
- 第 5 节的"逐层读取 PolBasis 返回值":**未读到**(见第 6 节)。
- seam 状态类 G5/G6:**未开始**。

以上为"未完成",不是"不可行"。

---

## 11. 违规披露(AGENTS.md 第 3 节)

### 表一:越界写入尝试

无。所有写入目标在 `$REPO` 下。`/tmp` 顶层保持 0 条目。

### 表二:工具/脚本事件

| 轮次 | 命令/工具 | 事件 | 是否落盘 |
|---|---|---|---|
| M1 | 预注册生成器输出的控制行列错位(`first_expected_class` 与 `expected_win1_rc`) | 生成器缺陷(E7-8);注册表已哈希,未改 | 是(合规路径) |
| M1 | gdb 第一次 jones 链尝试使用 finish 版本 | 程序在第一个 `ComputeLayerModes` 的 finish 处停止,未达注入(rc 0);日志保留 | 是(合规路径) |
| M1 | 第一段对 registries 的 SHA256SUMS 错放证据目录 | 已在第一段修正并核对 | 是(合规路径,已修正) |
| M1 | 生成 `GDB_CHAIN_SUMMARY_R7.tsv` 时的表头标签错误 | 已用 `edit` 修正为 jones/fftjones | 是(合规路径,已修正) |
| M1 | 生成 `RNV1_JONES_MAP_R7.tsv` 时,字节列写成"同 NG1",但未测字节 | 已用 `edit` 删除未测字节声明,改为"未测" | 是(合规路径,已修正) |
| M1 | `VL_NG1_SPLIT_R7.tsv` 与 `REGRESS_R7_M1.tsv` 的 python 一行命令 | 经 safe_run 写入 $EV;一次 awk 计算出错(误判为 rc1_DIFF),改用 Python 复核,结果以 Python 为准 | 是(合规路径) |
| M1 | 多处 `edit` 工具报 "file has not been read" | 读取后重试成功 | 不适用 |

说明:M1 中所有写入命令均经 `safe_run.sh p05-s4r7`。表二列出的事件均在仓库内、路径合规,如实列出。没有裸跑写入。

---

## 12. 结尾

本轮未完成 R7 范围(M1 已完成,M2、M3 未开始),等待用户审核。P05-S3、P05-S4 未签收。M1 提交之后停下,不进入 M2。

提交信息:`P05-S4 R7 milestone M1 ... awaiting user review`。
