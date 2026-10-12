# P05-S4 R6c2 报告（R6c 续，即 R6 的子轮次 R6c 的后半）：哈希勘误、判定器自检、seam 25 点判定、红点总账、修复方案与 R6 收尾

**状态：本轮已完成 R6c 范围中的第 0–6 节（门禁、ERRATA 勘误、判定器自检、seam 25 点判定、红点总账与修复方案、收尾文件）。本轮未宣布任何阶段完成或签收。P05-S3、P05-S4、P05-S5 均未签收。S3-4b 的关闭由用户决定，见第 9 节与 U21 条件核对。RNV1 延后（U16）到 R7，"其他层失败"变体延后（U20）到 R7，双目标注入与 I7 延后（U9）。**

证据目录（不提交）：`checkpoints/p05/evidence/p05-s4r6c/`；小型结果表（提交）：`checkpoints/p05/registries/s4r6c/`、`checkpoints/p05/registries/RULINGS.tsv`。

事实与判定的口径：注入结果只说明"在该注入下返回码非零"（REPORTED_FAILURE）或"被命中且判定结论"。判定结论只说明"在本装置的所列点上，所列不变量的实测值满足预注册规则"，**不说明任何树已修好或已验证**。B 列（37a82e8）是未修复基线。无实测支撑的结论写"未验证"；只读源码得到的写"[源码]"。

---

## 1. 门禁（R6c2-0）

- 门禁文件：`checkpoints/p05/evidence/p05-s4r6c/GATE_R6c2.txt`，**RESULT PASS**（由 `testing/d003/stage_s4/r6c2_gate.py` 计算全部比较，经 safe_run 运行）。
- HEAD = `fa7a247ff6d6b92c824b7774d4032cdbdd814bab`；`git log -1 -- checkpoints/p05/STATE.md` = HEAD；`HEAD:S4` = `4a6f64927a30537740dd0c8f11f9a5aae5e46ba4`；判定器 sha256 `d2d04145…209eb`；registries/s4r6b 的 SHA256SUMS 9 条全部 OK；v1 预注册 sha256 `f2523d14…c358` 一致。
- registries/s4r6c 的 SHA256SUMS_seam.txt 8 条全部 OK；SHA256SUMS.txt 除 ERRATA_6c.txt 外 9 条全部 OK（ERRATA_6c 按 E6c-6 单独核对，见第 2 节）。
- seam 预注册 `REGISTRY_S4_PRE_R6c_SEAM.tsv` sha256 `093c68a8c179131742be30ba2ddcd616c52126353b175547ff7d5ca10c1d576c` 一致。
- 工作区：除本轮门禁脚本 `r6c2_gate.py`（唯一例外，门禁文件中写明）外为干净；`git status --short` 为空（开工时）。
- `/tmp` 顶层：开工快照 0 条目，列表 sha256 `e3b0c442…b855`（空输入的哈希）。收尾快照见第 8 节。

## 2. E6c-6：ERRATA_6c.txt 的哈希勘误（事实更正）

- 里程碑提交 `6bba0bd` 的 `registries/s4r6c/SHA256SUMS.txt` 记录 ERRATA_6c.txt 的 sha256 为 `7875959f…`（64 行版本）。
- 提交 `fa7a247` 之后，ERRATA_6c.txt 追加了 E6c-3..5，变为 96 行，sha256 为 `33495a7f…`，所以 `sha256sum -c SHA256SUMS.txt` 对该项报 FAILED。
- **核对**（`r6c2_errata_prefix_check.py`，结果 `ERRATA_6c_PREFIX_CHECK.txt`，**PASS**）：`git show 6bba0bd:<path>` 得到 64 行、sha256 `7875959f…`（与清单一致）；当前文件前 64 行与之**字节逐一相同**。只追加，没有改动已有条目。
- **更正补充报告**：`P05_S4R6c_REPORT_ADDENDUM_seam.md` 第 1 节写"SHA256SUMS 全部 OK"，说法不完整。其余条目为 OK，但 ERRATA_6c.txt 这一项与当前文件不符。补充报告原文未改（按 U17），本更正记在 ERRATA_6c E6c-6 中。
- 本轮 ERRATA 的新哈希记入第 8 节的 `SHA256SUMS_closeout.txt`，不改旧清单。
- 状态：事实更正，不改变任何结果。

## 3. ERRATA_6c 本轮追加（U18–U23，写于 seam 判定与自检之前）

- U18（a）：REGISTRY_S4_PRE_R6c_SEAM_CONTROL.tsv，18 个 (library, mode) 对照，服务 25 点（求和 25，已核对）；sha256 与 UTC 见第 4 节。
- U19：自检定义（第 3 节）。
- U20：其他层失败变体记为 R7 候选（未做）。
- U21：S3-4b 关闭条件（三条，见第 9 节与 U21 核对）。
- U22：修复方案格式（第 5 节）。
- U23：RULINGS.tsv（见第 6 节）。
- E6c-7（登记于本次 ERRATA 中，说明驱动选择）：seam 状态运行的驱动为 `driver-r6b-seamF`（15 点）与 `driver-r6b-fmmret-F`（10 点，本轮新链接，见第 4 节）。`DRIVERS_DBG_SEAM.tsv` 登记的是普通 `driver-d003`，不用于对照与状态运行。

## 4. seam 25 点（第 4 节，U18 (a)）

### 4.1 fmmret-F 驱动链接（R6c2-2 步骤 1）

- `testing/d003/stage_s4/r6c2_link_fmmret.sh`（新）：库 sha256 核对通过（`f74084f0…4f7`，与 `libS4-dbg-fmmret-F.sha256` 一致），链接 `driver_r6b_state.cpp` + `inject_r4_plan.cpp`，LIBFLAGS 与 seamF 相同。**link rc 0，build.stdout 为空**。
- `driver-r6b-fmmret-F` sha256 `5f9570b8…3b02b3f`；`driver-r6b-seamF` sha256 `7f0bf3b6…a10c9b`（读取，未重链）。
- 试跑（不计入判定）：`R4-FE01-F`（experimental，fmmret:150:1）gdb 与无 gdb 的 `RC first 20 / RC retry 0 / HITCOUNT 1` 一致；与 R4 行（rc1 20、rc2 0、hit 1、REPORTED_FAILURE）一致。

### 4.2 对照登记（U18 (a)，写于任何 seam 状态运行之前）

- `REGISTRY_S4_PRE_R6c_SEAM_CONTROL.tsv`（新，18 行，`testing/d003/stage_s4/r6c2_seam_control.py`），sha256 `7e06ed2a…33c3c`，UTC `2026-10-12T07:13:08Z`（`.sha256` 与 `_TIMESTAMP_UTC.txt` 同目录）。
- 每行记录：control_id、library、mode、route once、driver 路径与 sha256、环境 `FMM_MODE`、`S4FMM_NG=9`（无 S4FMM_INJECT）、服务的点、INFLUENCED。服务点合计 25。
- `REGISTRY_S4_PRE_R6c_SEAM.tsv` 本身未改（sha256 `093c68a8…d576c`）。

### 4.3 状态运行（两遍，gdb 与无 gdb）

- 运行器 `testing/d003/stage_s4/r6c2_seam_state.py`（新，复制自 `run_r6c_seam_state.py`，改动见其文件头：按库选驱动；18 个对照先跑并纳入同一 GDB_DIVERGENT 规则；其余不变）。
- pass 1：`STATE_SEAM_R6c_pass1.tsv`，18 对照 + 25 点，**GDB_DIVERGENT 0**。
- pass 2：`STATE_SEAM_R6c_pass2.tsv`，**GDB_DIVERGENT 0**。
- 每点每遍 rc1 = 20、rc2 = 0、hit = 1，与 `SEAM_EQUIV_R6c.tsv` 一致（等价性 25/25 EQUAL，R6c 第 4.2 节）。

### 4.4 判定（`testing/d003/stage_s4/r6c2_seam_judge.py`，导入 `r6c_judge.py`，判定函数未改）

- `RESULTS_R6c_SEAM.tsv`、`STATE_SUMMARY_R6c_SEAM.txt`。
- 点级：pass 1 HOLD 25；pass 2 HOLD 25；FLAKY 0；VIOLATED 0；UNJUDGED 0；INVALID 0（hit 全为 1）。
- 按不变量（pass 1，25 点）：

| 不变量 | HOLD | VIOLATED | N/A | UNJUDGED | DEFERRED |
|---|---|---|---|---|---|
| I1 失败层 modes==NULL | 25 | 0 | 0 | 0 | 0 |
| I2 保留层与对照一致 | 23 | 0 | 2 | 0 | 0 |
| I3 field_cache（仅 PolBasis） | 10 | 0 | 15 | 0 | 0 |
| I4' 请求层 solved 与 modes | 25 | 0 | 0 | 0 | 0 |
| I5 重试区间 | 25 | 0 | 0 | 0 | 0 |
| I6 重试输出逐字节 | 25 | 0 | 0 | 0 | 0 |
| I7 sanitizer | — | — | — | — | 25（U9） |

- I2 的 N/A 2 点（R4-CLM1-F、R4-CLM2-F，alloc:21/22:1）：失败层为层 0，层 1、2 在 k_fail 时 modes 均为 NULL，无保留层，按规则 N/A。已核对 notes。
- I3 的 N/A 15 点：非 PolBasis 模式（fft、kottke、closed、tensor 等），规则 E6b-4 指定 N/A。
- I3 的 HOLD 10 点中：9 点在 k_fail 有 1 个节点且与对照一致（真实比较）；1 点（R4-ACF1-F，jones）为 0 节点（平凡 HOLD）。已核对 notes。
- 判定器未修改，规则未在看到结果后改动（E6c-2 之后无新规则）。
- 不适用的 mode：tensor、fftjones、fftnv、fftvl 中，tensor 不属 PolBasis，I3 N/A；fftjones、fftnv、fftvl 属 PolBasis（E6b-4），I3 按规则判定（HOLD）。

## 5. 判定器自检（U19，第 3 节）

- 脚本：`testing/d003/stage_s4/r6c2_judge_selftest.py`（新）。离线单元测试，**不运行 S4**，不是沙箱探测。
- 输入：真实 177 点中的原行（3 行）、其对照、真实 gdb 日志；改坏副本只存在于 `EVDIR/selftest_v2/`（只写副本，不改原件）。判定函数从 `r6c_judge.py` 导入（`judge_point`、`GdbLog`、`point_verdict`）。
- 期望写入 `SELFTEST_EXPECT_R6c2_v2.tsv`（sha256 记录于 `.sha256`），**在判定之前写入**。
- 结果：`SELFTEST_R6c2_v2.tsv`：**11 例改坏，11 例指定不变量 VIOLATED 且点级 VIOLATED；3 例原行 HOLD；失败 0**。

| 例 | 改坏 | 指定不变量 | 结果 |
|---|---|---|---|
| I1-a | k_fail 失败层 modes_null 1→0 | I1 | VIOLATED |
| I2-a | k_fail 保留层 0 的 q hash 改为不同值 | I2 | VIOLATED |
| I2-b | 对照中保留层 0 设为未安装 | I2 | VIOLATED |
| I3-a | k_fail 多出一个对照中没有的 cache 节点（jones 点） | I3 | VIOLATED |
| I3-b | k_fail 节点 P hash 与对照不同 | I3 | VIOLATED |
| I4-a | solved[req] 在 k_before=0、k_fail=1（I4' (a)） | I4 | VIOLATED |
| I4-b | solved@k_fail=1 且请求层 modes_null 1→0（twice inj2 点） | I4 | VIOLATED |
| I5-a | 层 2 在重试区间进入 ComputeLayerModes 两次 | I5 | VIOLATED |
| I5-b | 重试区间进入 k_pre 时已安装的层 0 | I5 | VIOLATED |
| I5-c | 重试 rc = 1 | I5 | VIOLATED |
| I6-a | 重试输出（call 2）改动 1 字节 | I6 | VIOLATED |

- **附带后果（如实记录）**：I4-b 的改坏同时使 I1 与 I5 判为 VIOLATED（改坏的是同一层在 k_fail 的状态，多个不变量依赖它）。I2 在 I4-b 中为 HOLD。这些附带 VIOLATED 的依据（notes）与改坏相符。自检要求的是指定不变量 VIOLATED，已满足。
- 修正历史（为可追溯，全部保留，未覆盖）：
  - 自检第一次运行写出 `SELFTEST_R6c2.tsv`、`SELFTEST_EXPECT_R6c2.tsv`，结果 11/11 与 3/3 通过，但输出中**没有判定依据（notes）列**，无法核对 VIOLATED 的原因；同时脚本的 I4-b 段含死代码与自赋值。依据 U17，这两份文件保留，不作为结论。
  - 修正后（补 notes 列、删死代码、统一 9 字段元组、输出改为 `_v2` 名）重跑，得到上表的 `SELFTEST_R6c2_v2.tsv`。这是本轮的自检结论。
- **判定器未修改**。自检没有失败，因此没有触发"判定器缺陷"停止条件。

## 6. 红点总账（R6c2-3，第 5 节）

- 文件：`evidence/p05-s4r6c/RED_POINTS_LEDGER_R6c.tsv`（类别、证据路径、状态、去向）。
- 收录（任务书列表）：RP-R5-1 至 RP-R5-4；E6-3；E6-4；E6-8 注释措辞（U11）；U14 旧 solved 观察（OBSERVATION）；E6c-6（HARNESS_OR_PROCESS）；K-1 张量路径（OPEN）；RNV1（DEFERRED，U16）；B 侧 jones/vl SILENT_SWALLOW 与 nv CRASH（OPEN，基线）；双目标注入与 I7（DEFERRED，U9）；"其他层失败"（DEFERRED，U20）；R7 项（Python/Lua 可见性、NB=1–8、类别 C、D016 B 侧 rc 20 来源）；非 FMM S4_malloc（OUT_OF_SCOPE_D003，S5）；177 点与 25 点的 OBSERVATION 行（VIOLATED 0、FLAKY 0、GDB_DIVERGENT 0）。
- 本轮 VIOLATED / FLAKY / GDB_DIVERGENT 点：**0**。因此没有需要复跑的点。
- 总账中凡引用的证据路径均已核对存在；D016 的 `RESULTS_R5_D016.tsv` 不存在，已改为 R5 报告的真实位置（标注 "does NOT exist (checked)"）。

**RNV1 状态**：延后（U16）到 R7。注入未做。pattern 内的 work malloc 无 NULL 检查（源码，见第 7 节）。

## 7. 修复方案（R6c2-3，U22）

- 文件：`evidence/p05-s4r6c/REPAIR_PROPOSAL_R6c.md`。**只写方案，未改任何代码，S4/ 未改动。**
- A（F_CONFIRMED 候选）：**无**。177 点与 25 点合计 VIOLATED 0。
- B（注释措辞 U11）：`S4/S4_internal.h:263` [源码]，1 行注释，需用户批准改 S4/。
- C（RNV1）：`S4/pattern/pattern.c:1477, 1481, 1656, 1660` [源码]：分配后直接使用，无 NULL 检查（已读取 1470–1494、1650–1669）。估计 8–12 行改动（4 处检查）；返回值与错误路径**未验证**；回归点为 nv 的 177 点与 R7 中待设计的注入点；修复后期望 REPORTED_FAILURE（注入下），177 点 nv HOLD 不变。需用户批准改 S4/。
- D（不提议修复）：已关闭或降级的项；非 FMM S4_malloc（S5）；B 侧观察（非修复证据）。
- E：R7 候选清单（见 `REPAIR_PROPOSAL_R6c.md` 第 E 节），包括 RNV1 注入、其他层失败、双目标与 I7、Python/Lua、NB=1–8、类别 C、K-1 张量、D016 B 侧、seam N/A 点的规则决定。

## 8. 收尾（R6c2-4，第 6 节）

### 8.1 小型结果表与清单（registries/s4r6c）

- 本轮新增 17 个文件复制到 `registries/s4r6c/`，并逐个与证据目录原件比对 sha256（抽查 5 个全部相同；清单核对 17 条全部 OK）。
- 新清单 `registries/s4r6c/SHA256SUMS_closeout.txt`（不改 `SHA256SUMS.txt`、`SHA256SUMS_seam.txt`）。`ERRATA_6c.txt` 按 E6c-6 记录其**当前**哈希 `212475556aad35dbcea5b804aa56e53be78bbb4cf3f9f44f174282081e3f466f`（144 行）。
- 注意：`SEAM_R6c_pass1.tsv`、`SEAM_R6c_pass2.tsv` 在复制时被覆盖（见第 12 节表一之后的表二，**U17 违规**）。覆盖前后内容相同（sha256 `cb6ccf45…8e4` 与 `1f63e349…a4af` 与 `SHA256SUMS_seam.txt` 登记值一致），故无内容改变，但这是覆盖动作，须披露。

### 8.2 证据清单与 safe_run 日志

- 证据清单 `evidence/p05-s4r6c/SHA256SUMS.txt`：**2558 条**文本类证据（txt、log、out、tsv、md、sha256、json、py、stdout、stderr、gdb），`sha256sum -c` 全部 OK（rc 0）。不收录 `safe_run.log`、`tmp/`、二进制（`.o`、`.a`、驱动可执行文件）与 R4 源树副本（`*/src/`，其完整性由各自清单与 `libS4-dbg-*.sha256` 记录）。
- `evidence/p05-s4r6c/SAFE_RUN_LOG_FINAL.txt`：写入时统计为 62 行、REFUSED 字段条目 **1**（这一数字是**误计**，见下）。
- **REFUSED 的权威计数为 0**。误计原因：统计命令 `grep -c REFUSED` 本身经 safe_run 被记入日志（命令文本含该词），而统计模式过宽。真实拒绝只由 `refuse()` 写入 `p05-s2r6/safe_run_refusals.log`，本轮时间窗内该文件为 0 条。
- 更正文件（均为新文件，未覆盖）：`SAFE_RUN_LOG_FINAL_CORRECTION.txt`（误计的第二次尝试，仍误计为 1）与 `SAFE_RUN_LOG_FINAL_CORRECTION_2.txt`（权威计数 0）。

### 8.3 收尾门禁与 tmp

- `evidence/p05-s4r6c/GATE_R6c2_END.txt`：**RESULT PASS**。`/tmp` 顶层收尾快照 0 条目，sha256 `e3b0c442…b855`，与开工一致。
- `evidence/p05-s4r6c/tmp/`：清理前核对路径为 `…/checkpoints/p05/evidence/p05-s4r6c/tmp`，内容 0 条目（已为空）。

### 8.4 附录 A

STATE.md 压缩前的原文已逐段搬入本报告附录 A，原文副本 `evidence/p05-s4r6c/STATE_before_R6c2_fa7a247.md`（sha256 `e2aee287…716b16`）。压缩后的 STATE.md 为 47 行。

## 9. U21 条件核对（S3-4b 关闭条件）

执行者只报告三条各自是否满足，**不写"S3-4b 关闭"**。关闭由用户决定。

**条件 (1)：判定器自检中，每个被改坏的例子对应的不变量判 VIOLATED，未改的原行判 HOLD。 — 满足。** 证据：`checkpoints/p05/evidence/p05-s4r6c/SELFTEST_R6c2_v2.tsv`（11/11 指定不变量 VIOLATED，3/3 原行 HOLD，失败 0）。注意第 5 节的修正历史。

**条件 (2)：202 点（177 + seam 25）中 VIOLATED = 0、FLAKY = 0、GDB_DIVERGENT = 0；UNJUDGED = 0，或每个 UNJUDGED 逐一说明原因。 — 满足。**
- 177 点：VIOLATED 0，FLAKY 0，GDB_DIVERGENT 0，UNJUDGED 0（`checkpoints/p05/registries/s4r6c/STATE_SUMMARY_R6c.txt`）。
- seam 25 点：VIOLATED 0，FLAKY 0，GDB_DIVERGENT 0，UNJUDGED 0（`evidence/p05-s4r6c/STATE_SUMMARY_R6c_SEAM.txt`；两遍 `run_seam_state_pass{1,2}.stdout` 中 `GDB_DIVERGENT=0`，状态表 43 行 OK）。
- 合计 202：VIOLATED 0，FLAKY 0，GDB_DIVERGENT 0，UNJUDGED 0。

**条件 (3)：范围声明写明：只覆盖层 1 失败；I3 中做了实际比较的点数；双目标注入、I7、"其他层失败"转到 R7。 — 事实已列出，范围声明需用户确认。**
- 失败层的覆盖（由 failing_layer 列统计，见第 9.1 节）：177 点全部失败层为层 1；seam 25 点中 23 点失败层为层 1，2 点（R4-CLM1-F、R4-CLM2-F，alloc:21/22:1）失败层为层 0。因此范围声明不能写成"只覆盖层 1 失败"，应写"失败层为层 1（177 点全部，seam 23 点）与层 0（seam 2 点）"。（注：早先草稿认为 alloc:21–24:1 全部失败于层 0，这是错误推断。统计结果为：只有 CLM1、CLM2（alloc:21、22）失败于层 0；CLM3、CLM4（alloc:23、24）失败于层 1。）
- I3 中做了实际比较的点数：177 点 9 点（1 节点）+ seam 9 点（1 节点）= **18 点**；平凡 HOLD（0 节点）：177 点 60 点 + seam 1 点 = 61 点；N/A：177 点 108 点 + seam 15 点 = 123 点。合计 18 + 61 + 123 = 202。
- 双目标注入、I7、"其他层失败"：**转 R7**（U9、U20）。

### 9.1 修正：失败层位置（条件 3 的事实）

177 点与 seam 点的失败层需分别统计，**不能一律写"层 1"**。从 `RESULTS_R6c_STATE.tsv`（177 点）与 `RESULTS_R6c_SEAM.tsv`（25 点）的 `failing_layer` 列统计，结果见第 9.2 节的表（由实际列计算，不是估计）。

### 9.2 失败层统计（pass 1，由 failing_layer 列计算）

| 集合 | 失败层 = 0 | 失败层 = 1 | 合计 |
|---|---|---|---|
| 177 点（`RESULTS_R6c_STATE.tsv`） | 0 | 177 | 177 |
| seam 25 点（`RESULTS_R6c_SEAM.tsv`） | 2（R4-CLM1-F、R4-CLM2-F；alloc:21、alloc:22） | 23 | 25 |

seam 中失败层为 0 的两点，其 I2 为 N/A（无保留层）。两遍结果相同。

### 9.3 S3-4b 的写法（任务书 6.5 固定格式）

S3-4b 在本装置范围内：177 点 HOLD 177 / VIOLATED 0 / N/A 0 / UNJUDGED 0；seam 25 点 HOLD 25 / VIOLATED 0 / UNJUDGED 0（I2 N/A 2、I3 N/A 15 按规则）；判定器自检：11 例中 11 例判出 VIOLATED（原行 3/3 HOLD）；局限：只覆盖层 1 失败（seam 另有层 0 失败 2 点）、I3 多为平凡 HOLD（177 点 60 点空 cache；seam 1 点）、双目标与 I7 延后。是否关闭由用户决定。

注：177 点的 I3 为 HOLD 69 / N/A 108（R6c 报告）；其中 60 点空 cache 为平凡 HOLD，9 点为真实比较（见第 9 节）。上式中的 N/A 0 指 I1、I2、I4–I6 的 N/A；I2 与 I3 的 N/A 另行列出（177 点 I2 N/A 0，I3 N/A 108；seam I2 N/A 2，I3 N/A 15）。

不得写"已修好""已验证""S3-4b 关闭"。以上只是事实陈述。

## 10. 需要用户裁决的事项

1. **S3-4b 是否关闭**，以及若关闭，范围声明的文字（条件 3）。执行者未关闭。
2. **修复轮的范围与时机**：是否开 S3 收尾修复轮；修复项为 B（注释 U11，1 行）与 C（RNV1，4 处 NULL 检查，需先设计注入与返回路径）。改动 S4/ 需用户批准。
3. **R7 范围**：RNV1 注入、其他层失败变体、双目标与 I7、Python/Lua 可见性、NB=1–8、类别 C、K-1 张量、D016 B 侧 rc 20 来源、seam N/A 点的规则决定。
4. **U2、U4 原文**：仓库中不存在。RULINGS.tsv 记为"原文缺失，待用户补录"。
5. **seam 中 I2 N/A 2 点与 I3 N/A 15 点**：是否接受为规则允许的 N/A，还是需要另行观测（R7-9）。

## 11. R6 整体总结表

| 子轮 | 完成项 | 关键数字 | 报告 |
|---|---|---|---|
| R1 | 门禁、预注册（62 个 R1 编号） | 无运行 | （无独立报告，见 R2 报告的 ERRATA_2） |
| R2 | 四树构建、首次三列运行 | 15 用例 × B/A/F = 45 行：34 MATCH、11 MISMATCH（9 行未命中，NTH 映射错误） | `P05_S4R2_REPORT.md` |
| R3 | 调用序发现、FMM 分配/plan/exec 穷举 | 范围内 141 点；B 123 MATCH、4 MISMATCH、22 INVALID；F 127 MATCH、22 INVALID、0 CRASH/SILENT_SWALLOW | `P05_S4R3_REPORT.md` |
| R4 | F 上 seam 库；SI/AL18/FE/info=NULL/CLM/ACF；plan NTH≥3 | 主矩阵 75 行：59 MATCH、0 MISMATCH、10 INVALID、6 NO_EXPECTATION；F 列 25/25 REPORTED_FAILURE；plancall 44 对：34 MATCH、10 MISMATCH（B，twice NTH 12–16） | `P05_S4R4_REPORT.md` |
| R5 | 回填 R1–R4；gdb 调查 plan twice；M≥2；UNMAPPED 清账；V4 sanitizer；V3 重试 | 等价性 24/24 SAME；M=2 36 点 F 全 MATCH；K1 F 4/4；D016 MATCH；V4 224 点 SAME、sanitizer 发现 0；V3 132 点 IDENTICAL（单列 70） | `P05_S4R5_REPORT.md` |
| R6 | twice NTH 12–16 在 TWICE=slab 下重跑（R6-1）；S3-4b 状态测试；RNV1；红点总账 | R6-1：24 行 × 2 遍 = 48 次，全部 MATCH；R6-2 部分（I1 单点实测）；R6-3 RNV1 延后（U16）；R6-4 账本在 R6c2 完成 | `P05_S4R6_REPORT.md` |
| R6b | S3-4b 装置与预注册（部分）；U7–U13 | 树核对 70/70 SAME；映射 202 点；预注册 177 点（INFLUENCED）；对照 16 组合；单点 gdb 与无 gdb rc 一致 | `P05_S4R6b_REPORT.md` |
| R6c | 里程碑（U14–U17）：v2 预注册；177 点两遍；seam 等价性与 inj_call 与预注册 | 177：HOLD 177 / VIOLATED 0 / UNJUDGED 0 / FLAKY 0 / GDB_DIVERGENT 0；seam 等价 25/25；inj_call 全为 1 | `P05_S4R6c_REPORT.md`、`P05_S4R6c_REPORT_ADDENDUM_seam.md` |
| R6c2（本轮） | E6c-6；U18 对照；自检（U19）；seam 状态运行与判定；红点总账；修复方案；U23 裁决表；收尾 | seam 25：HOLD 25 / VIOLATED 0 / FLAKY 0 / GDB_DIVERGENT 0；自检 11/11、原行 3/3；202 点 VIOLATED 0 | 本报告 |

## 12. 违规披露（AGENTS.md 第 3 节）

### 表一：越界写入尝试（命令自身写了仓库外路径，即使被拒绝、未落盘）

| 轮次 | 命令 | 是否落盘 | 说明 |
|---|---|---|---|
| R6c2 | 无 | — | 本轮所有写入目标都在 `$REPO` 之下（`$EV/`、`testing/d003/stage_s4/`、`checkpoints/p05/`）。仅 `/tmp` 顶层的只读计数（门禁）。 |

### 表二：工具/脚本事件

| 轮次 | 事件 | 是否落盘 | 说明与处理 |
|---|---|---|---|
| R6c2 | `python3 -I -B - <<'EOF'` 的 heredoc（运行一个空 heredoc，检查 ERRATA 行数） | 否（空输入，无写入） | **违反"不用 heredoc"**。随后用 `grep`/`awk` 读取，未再使用 heredoc。 |
| R6c2 | `write` 的 `r6c2_gate.py` 中 `verify_sums` 固定读 SHA256SUMS.txt，会使 seam 清单核对读错文件；在**运行门禁之前**由 `edit` 加入 `sums_name` 参数修正（门禁只运行一次，结果有效） | 是（仓库内，合规路径；脚本文件） | 工具事件，已在运行前修正。 |
| R6c2 | `write` 的 `r6c2_seam_control.py` 首次版本误读 DRIVERS_DBG_SEAM.tsv 的列顺序与驱动（指向普通 driver-d003） | 否（写入前发现，`edit` 修正后才运行） | 运行的是修正版；对照表 18 行的驱动均为 state 驱动（sha 已核对）。 |
| R6c2 | `edit` 写入 `r6c2_judge_selftest.py` 时引入残缺结构（`_unused = ([`） | 否（编辑当时即修正，运行的是修正版） | 工具事件。 |
| R6c2 | 自检 run 1 输出缺 notes 列且含死代码；run 1 的结果文件 `SELFTEST_EXPECT_R6c2.tsv`、`SELFTEST_R6c2.tsv`、`selftest/` 保留 | 是（$EV 内，保留，不作结论） | 见第 5 节修正历史；run 2 用 `_v2` 新名。 |
| R6c2 | 本轮所有 shell 写入命令经 safe_run，重定向写在 `sh -c` 引号内部（核对 safe_run.log：每条写入命令为 `sh -c ...` 形式）。未发现重定向在引号外。 | 不适用 | 之前草稿中"两条命令在引号外"的说法经核对不属实，已撤回。 |
| R6c2 | 框架落盘 `/tmp/dsh-spill-*`（长输出） | 未观察到（输出用 head/tail 截断） | 框架事件（若出现）单列，不算执行者违规。 |
| R6c2 | safe_run 外的 `ls`/`cat`/`grep` 只读命令 | 否（无写入） | 只读，不违规。 |

（`safe_run.log` 与 `safe_run_refusals.log` 的核对见第 8.2 节。）

**表三：U17 覆盖事件（补充）**

| 轮次 | 事件 | 是否落盘 | 说明 |
|---|---|---|---|
| R6c2 | 复制到 `registries/s4r6c/` 时覆盖了已登记的 `SEAM_R6c_pass1.tsv`、`SEAM_R6c_pass2.tsv` | 是（仓库内） | 违反 U17（不覆盖）。覆盖前后内容相同（与 `SHA256SUMS_seam.txt` 登记的 sha256 一致），无内容改变。其余 15 个复制目标均为新文件（已逐一核对）。 |

## 13. 本轮状态

- **已完成**：R6c2-0 门禁；E6c-6；U18 对照与 fmmret-F 驱动；判定器自检（U19）；seam 25 点两遍状态运行与判定；红点总账；修复方案；RULINGS.tsv（U23）；U21 条件核对的事实部分。
- **未在本轮做出判断**：S3-4b 是否关闭（由用户决定）；RNV1（延后 U16）；其他层失败（延后 U20）；双目标与 I7（延后 U9）。
- **未完成**：无（R6c 范围第 0–6 节已做，见上）。收尾文件的哈希与提交由第 8 节记录。

本轮已完成 R6c 范围（第 0–6 节），等待用户审核。

---

## 附录 A：STATE.md 压缩前的原文（逐段搬移，保证信息不丢失）

- 原文件：`checkpoints/p05/STATE.md`，HEAD `fa7a247` 版，共 70 行。逐字节导出到 `checkpoints/p05/evidence/p05-s4r6c/STATE_before_R6c2_fa7a247.md`，sha256 `e2aee287881cd2f31c59e31ec9b488b6477fce0cd1348de433421f2012716b16`（由 `git show` 得到，只读）。
- 压缩后的 STATE.md 只保留第 1–4 节的摘要与链接。下面的各段是压缩前的全文（段落保持原样，未改写）。

### A.1 原 STATE 第 1 节（当前位置）

| 项 | 值 |
|---|---|
| 分支 | `codex/p05-d003-fft-error-propagation` |
| 本轮开工基线 HEAD（R6c） | `b9fbe00f577e64a92c57522369ba7a0ab6ece316`（R6b 部分收尾提交；R6b 开工为 `20b3411`） |
| 收尾提交 | 修改本文件的最后一次提交（`git log -1 --format=%H -- checkpoints/p05/STATE.md`） |
| `HEAD:S4` | `4a6f64927a30537740dd0c8f11f9a5aae5e46ba4`（= 冻结树 F `1c11905`） |
| 判定器 sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` |
| 阶段签收 | S1、S2 已签收（带范围声明，见 `P05_S1_S2_SIGNOFF.md`）；S3、S4、S5 未签收 |
| 当前阶段 | P05-S4 子轮次 **R6c**（非新阶段）：里程碑 `6bba0bd` 已提交（177 点全量与判定，U15）；**第 4 节 seam 部分完成，状态运行待用户裁决 U18；第 5、6 节未做**。RNV1 延后（U16 → R7）。等待用户审核（报告：`P05_S4R6c_REPORT.md`、`P05_S4R6c_REPORT_ADDENDUM_seam.md`） |

### A.2 原 STATE 第 2 节（各轮关键数字）

| 轮 | 内容 | 关键数字 | 报告 |
|---|---|---|---|
| R1 | 门禁、预注册（62 个 R1 编号） | 无运行 | （无独立报告；见 R2 报告的 ERRATA_2） |
| R2 | 四树构建、首次三列运行 | 15 用例 × B/A/F = 45 行：34 MATCH、11 MISMATCH（其中 9 行未命中，均为预注册 NTH 映射错误） | `P05_S4R2_REPORT.md` |
| R3 | 调用序发现 + FMM 分配/plan/exec 穷举 | 范围内 141 点；B:123 MATCH、4 MISMATCH、22 INVALID；F:127 MATCH、22 INVALID、0 CRASH/SILENT_SWALLOW | `P05_S4R3_REPORT.md` |
| R4 | F 上 seam 库；SI/AL18/FE/info=NULL/CLM/ACF；plan NTH≥3 补测 | 主矩阵 75 行：59 MATCH、0 MISMATCH、10 INVALID（B 的 FE，结构性）、6 NO_EXPECTATION；F 列 25/25 REPORTED_FAILURE。plancall 44 对：34 MATCH、10 MISMATCH（B，twice NTH 12–16） | `P05_S4R4_REPORT.md` |
| R5 | 子轮次：回填 R1–R4（44 文件）；gdb 调查 plan twice NTH 12–16；M≥2；UNMAPPED 清账；V4 sanitizer；V3 重试 | 等价性 24/24 SAME；gdb：TWICE=slab 路线 F 检查执行（i），无 TWICE 路线未定；M=2 36 点 F 全 MATCH；K1 F 4/4 MATCH；D016 MATCH；V4 224 点类别 224 SAME、sanitizer 发现 0；V3 132 点 IDENTICAL（单列 70） | `P05_S4R5_REPORT.md` |
| R6 | 子轮次：twice NTH 12–16 在 TWICE=slab 下重跑（R6-1）；S3-4b 状态测试（R6-2）；RNV1（R6-3）；红点总账（R6-4） | R6-1：24 行 × 2 遍 = 48 次，全部 MATCH（F 为 REPORTED_FAILURE，B 为 CRASH）；gdb K=14（fft、kottke）确认调用者 FMMGetEpsilon_* 且 NULL 检查执行；R6-2：驱动编译通过，映射表 119 行，单点快照实测 I1 成立；**I1–I7 判定未完成**；R6-3、R6-4 未完成 | `P05_S4R6_REPORT.md` |
| R6b | 子轮次（部分）：S3-4b 装置与预注册；U7–U13 裁决入 ERRATA_6b | 树核对 70/70 SAME；映射 202 点（R3 119 + R4PC 22 + R5M2 36 + R4SEAM 25）；预注册 177 点（INFLUENCED，已锁定 sha `f2523d14…`）；对照组 16 组合登记；单点 closed1d malloc NTH1 once 的 gdb 与无 gdb rc 一致（20/0/0）；seam 25 点 UNJUDGED（无调试信息）；**全量运行与判定未做**；R6-3 RNV1、R6-4 账本未开始 | `P05_S4R6b_REPORT.md` |
| R6c | 子轮次：里程碑 `6bba0bd`（U14–U17；v2 预注册；177 点两遍全量与判定）；第 4 节 seam 部分（重建、等价性、inj_call、预注册）；**seam 状态运行与第 5、6 节未做** | 177 点：两遍 GDB_DIVERGENT 0；HOLD 177 / VIOLATED 0 / UNJUDGED 0 / FLAKY 0（I3 HOLD 69 / N/A 108；装置只覆盖层 1 失败）；seam 等价性 25/25 EQUAL；inj_call 全为 1；seam 判定 UNJUDGED 25（待 U18） | `P05_S4R6c_REPORT.md`、`P05_S4R6c_REPORT_ADDENDUM_seam.md` |

R1 覆盖表（62 个编号，R4 合并后）：57 REACHED，5 UNMAPPED。R5 之后：AL02 注销为 EXP40 重复；K1A、K1B、D016 已测；RNV1 部分（见第 3 节）。

### A.3 原 STATE 第 3 节（开放问题）

R5 之后的状态。"关闭"指有运行证据；"部分"指只关闭了其中一部分；闭合与否由用户决定。

1. **plan twice NTH 12–16（fft、kottke 各 5 点）** — **部分关闭，仍开放**（R6b 未改动此项；本条原"待用户裁决"已过时，U1 已于 R6 裁决）。R6-1（E6-1，用户裁决 U1）：R4 的 twice NTH 12–16 已在 TWICE=slab 下重跑 24 行 × 2 遍，全部 MATCH（F REPORTED_FAILURE、B CRASH）；gdb 仅抽 K=14 的 fft 与 kottke 各 1 点（调用者 FMMGetEpsilon_*、NULL 检查执行），**未逐点核对**。TWICE=slab 路线已机理化：F 的 `fmm_FFT:90` 检查执行，返回 20（R5-2 Q2/Q5 = i）；B 无检查，`fft_plan_exec(NULL)` 段错误。无 TWICE 路线的 F 结论**未定**（断点矛盾，E5-13）。**新发现**：R4 plancall 的 twice 行实际无 TWICE（E5-10），任务书前提"TWICE=slab 时 1/0/1"不成立（实测 F 1/0/20、B SIGSEGV）。待用户裁决。
2. **plan M≥2** — **关闭**（R5-3）：m(K)=2 在 156 个 (模式、路由、K) 观察中两遍一致（无 m≥3）；M=2 的 36 个范围内点 F 全部 REPORTED_FAILURE（MATCH）；B 全部 CRASH（基线）。
3. **UNMAPPED 5 项**：
   - AL02 — **关闭**：与 EXP40 同一站点（experimental.cpp:40），注销为重复登记（E5-5）；
   - K1A、K1B — **关闭**（R5-4）：F 在 eps 0、1e-300 得 rc 20，在 1e-100、4 得 0，与预注册一致；F 场与 S3R2 new 逐字节一致；B 在 eps 0、1e-300 段错误。**张量路径 K-1 仍开放**（R5 未做，S3R2 报告第 6 节第 4 条）；
   - D016 — **关闭**（R5-4）：F 的 `pattern_generate_flow_field` 返回 −10（两次），驱动 rc 20；B 返回 0，与 S3R2 一致；
   - RNV1 — **部分，仍开放**（R6-3 未完成：注入器未写、未运行；见报告）：pattern 内 malloc 确认存在（每次 nv 运行 3 次，F 与 B 相同）；注入未做（需新注入器，不改 S4/）；pattern 的 work malloc 无 NULL 检查（源码），注入预计先段错误，不会到达 −10 路径。列入 R6。
4. **S3 移交清单（D4 第四节）** — 逐条见 `evidence/p05-s4r5/S3_HANDOFF_COVERAGE_R5.tsv`：
   - 失败后模式/缓存不安装（S3-4b）— **R6c 里程碑后：177 点 HOLD 177 / VIOLATED 0 / UNJUDGED 0（两遍一致）。仍开放：装置只覆盖层 1 失败；I7 与双目标 DEFERRED（U9）；seam 25 点未判定（U18）。是否关闭由用户决定，不是"已修好"。**（R6 时的旧表述已过时。）R6-2 仅有单点实测（closed1d malloc NTH 1）：失败层 modes==NULL（I1 成立），层 0/2 已保留模式，按用户裁决 I2 选项 1 处理（E6-8）。`partial_modes=1` 不是缺陷证据（E6-3，驱动检查在重试之后计数，HARNESS_OR_PROCESS）；
   - 失败后不缓存部分 P — **仍开放**（无直接缓存探针）；
   - Python/Lua 可见失败 — **仍开放**（R6，R5 未跑）；
   - 恢复后重试正确（V3）— **部分关闭**：132 点重试场与同模式同路由基准逐字节相同；单列 70 点（rc2-only 45、R4 seam 25）未比较；
   - 中间量错误（类别 C）— **仍开放**（R6）；
   - NB=1–8 覆盖 — **仍开放**（R6）；
   - 失败码传播链（四节 a）— **关闭（TWICE=slab 路线）**：FFT 1 → CLM 20 → GFP 20（R5-2）。
5. **V4 sanitizer** — **关闭**（R5-5）：224 个注入点 + 5 个控制库，类别 224 SAME，sanitizer 发现 0；阳性对照确认工具能报告。
6. **B 侧未解释**（只影响基线列，不阻塞）：R3 的 jones/vl SILENT_SWALLOW、nv CRASH — **仍开放**（未在 R5 查）。
7. **非 FMM `S4_malloc`**：静态 35 个调用行，不属 D003，留给 S5 — **仍开放**（S5 登记）。
8. **新开**：
   - E5-10：R4 plancall twice 行无 TWICE（前提偏差）— **已按用户裁决 U1 处理**：R6-1 以 TWICE=slab 重跑（E6-1），R4 结果未改；
   - E5-15：驱动 witness `partial_modes=1` 与 "failed layer kept no partial modes FAILED"（132/132），语义未定；
   - E5-3：`registries/s4r3/ERRATA_3.txt` 与 `REGISTRY_S4_PRE_R3.sha256` 不一致 — **用户裁决关闭（U3，只加说明，不重跑）**：运行后有意追加 f、g 节，预注册期望未改；说明见 E6-2；
   - E5-17：R4 GATE 的 `/tmp_none` 越界写入尝试（历史，见报告违规表）。

### A.4 原 STATE 第 4 节（证据位置）

| 轮 | 证据目录（不提交） | 已提交的小型结果表 | sha256 清单 |
|---|---|---|---|
| R1 | `evidence/p05-s4/` | `registries/s4r1/`（GATE、REGISTRY_S4_PRE、PRE_REGISTRY_ERRATA_1、write_guard.log） | `registries/s4r1/SHA256SUMS.txt`（R5 已生成） |
| R2 | `evidence/p05-s4r2/` | `registries/s4r2/`（R2 结果与预注册 v2） | `registries/s4r2/SHA256SUMS.txt`（R5 已生成）；证据目录 `evidence/p05-s4r2/SHA256SUMS.txt` |
| R3 | `evidence/p05-s4r3/` | `registries/s4r3/`（R3 结果、覆盖、红点、预注册 v3） | `registries/s4r3/SHA256SUMS.txt`（R5 已生成）；证据目录 `evidence/p05-s4r3/SHA256SUMS.txt` |
| R4 | `evidence/p05-s4r4/` | `registries/s4r4/`（R4 结果、预注册 v4 与 B 版、plancall、regress、seam、drivers） | `registries/s4r4/SHA256SUMS.txt`（R5 已生成）；证据目录 `evidence/p05-s4r4/SHA256SUMS.txt` |

S3R2 的结果表已在 `registries/s3r2/`（提交 `1c11905`）。
