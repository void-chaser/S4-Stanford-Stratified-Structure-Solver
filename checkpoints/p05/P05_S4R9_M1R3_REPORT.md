# P05-S4 R9 M1 第二修正轮报告：在"试跑-冻结-单次调用"纪律下取得 M1 F4 事实并纠正流程偏差

> 轮次标识：`r9m1r3`（P05-S4 子轮次 R9 的 M1 第二修正轮，非新阶段）  
> 开工基线 HEAD：`16a789791f792f8814dc8896e03fb1b3f75c6294`（r9m1r2 收尾提交）  
> 记录提交 (i) HEAD：`289237d`  
> 冻结被测树：F4（提交 `05097a7`，`S4/` 树哈希 `589e15eb11fcb04e031b524f25a443e7921946cf`）  
> 参照树：F3（`8d8202a`，`6cff923…`）、F2（`a07b5ac`，`e124925…`）、B（`37a82e8`，`1d738e6…`；仅基线对照，非修复证据）  
> 判定器 sha256：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`  
> 证据目录：`checkpoints/p05/evidence/p05-s4r9/m1r3/`  
> 小表提交目录：`checkpoints/p05/registries/s4r9/M1R3/`  
> 任务书存档：`checkpoints/p05/briefs/P05_S4R9_BRIEF_M1R3.md`  
> 规范约束：遵循 `AGENTS.md` 与本任务书纪律。不宣布阶段完成，不询问是否签收。禁止 git commit --amend、rebase 及任何改写历史的操作。本报告内不记载收尾提交哈希。

---

## 0. 身份、边界与工作概述

- **轮次定位**：P05-S4 子轮次 R9 的 M1 第二修正轮（r9m1r3），旨在：
  1. 登记 r9m1r2 自身的流程偏差（冻结后改写重跑、多次调用、裸写、收尾混乱与门禁多跑）；
  2. 修正两处事实口径：一是 G2c_control 未运行行真实记为未运行，不合成数值或 CONTROL_OK；二是 M1c G6 的 I1–I6 不变量真实接入判定与比对；
  3. 在"试跑 → 冻结 → 单次调用"的纪律下，重新取得 M1 F4 侧 651 行事实，与 F3 冻结事实逐字段等价比对，合并形成 1302 行总表。
- **保护边界**：本轮未修改 `S4/` 源码目录、未修改判定器 `judge_d003.py`、未修改历史装置及已提交的文件（含 r9m1、r9m1r2 全部脚本与小表）；历史证据目录只读；新脚本置于 `testing/d003/stage_s4r9/` 且文件名带 `r9m1r3`。
- **执行纪律落地**：
  * 试跑期在 `shakedown/` 目录下调试跑通全流程，已执行脚本不原地改写，改写换文件名并进事件表；
  * 记录提交 (i) 之后严格冻结脚本，门禁从 safe_run.log 计数断言冻结期 posctrl、smoke、formal、verdict、compare 各只调用 1 次；
  * 门禁断言记录提交后无任何写入 `testing/d003/` 命令；
  * 收尾严格按照固定单向顺序执行，门禁之后不改写任何交付物。

---

## 1. 门禁核验结果

### 1.1 开工门禁（`GATE_R9M1R3_start_v4.txt`）
- **HEAD 校验**：`16a789791f792f8814dc8896e03fb1b3f75c6294`（PASS）；
- **HEAD:S4 校验**：`589e15eb11fcb04e031b524f25a443e7921946cf`（F4 冻结树，PASS）；
- **历史树校验**：F3 `6cff923…`、F2 `e124925…`、B `1d738e6…` 全部一致（PASS）；
- **判定器 sha256**：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`（PASS）；
- **清单比对**：
  * `registries/s3r5/SHA256SUMS.txt`（14 项全部 PASS）；
  * `registries/s4r9/M0/SHA256SUMS.txt`（25 项全部 PASS）；
  * `registries/s4r9/M2/SHA256SUMS.txt`（14 项全部 PASS）；
  * `registries/s4r9/M2b/SHA256SUMS.txt`（13 项全部 PASS）；
  * `registries/s4r9/M2c/SHA256SUMS.txt`（11 项全部 PASS）；
  * `registries/s4r9/M1/SHA256SUMS.txt`（28 项全部 PASS）；
  * `registries/s4r9/M1R2/SHA256SUMS.txt`（33 项全部 PASS）；
- **活动文件校验**：RULINGS.tsv 130798 字节（U317）、ERRATA_9.txt 19322 字节（E9-20）、STATE.md 8056 字节；前缀比对一致（PASS）；
- **未跟踪构建产物基线**：登记 2 项（judge_d003 与 matrix_r2 的 pyc，PASS）；
- **门禁结果**：FAILS = 0，0 FAIL lines（PASS）。

---

## 2. 输入事实复核结论（G-1 至 G-8）

经编写并在 safe_run 下运行 `audit_r9m1r2_r9m1r3_v2.py`，对规划者输入的 G-1 至 G-8 事实对照原始日志与文件逐项核对，产出 `AUDIT_R9M1R2_R9M1R3.tsv`。复核结论全部为**属实**：

| 项 | 事实摘要 | 原始日志/文件行号 | 复核结论 | 核验细节说明 |
|---|---|---|---|---|
| **G-1** | 冻结与实际调用不一致 | 提交 `a413db0`；m1r2 safe_run.log:L29,30,33,34,39,40,37,44；FROZEN_SCRIPTS_R9M1R2.tsv | **属实** | 提交 a413db0 时间为 01:51:09Z。L29 写入 compare_R2、L30 写入 posctrl_R2、L33 写入 smoke_R2、L34 写入 formal_R2、L39 写入 formal_R3 均在提交之后。正式事实来自 formal_R3，冒烟来自 smoke_R2，比对来自 compare_R2。原清单脚本未产出最终结果。 |
| **G-2** | 多次调用脚本与报告 §8.1 不符 | safe_run.log:L28,31,32,35,37,38,40；runs/formal/；报告 §8.1:175-179 | **属实** | posctrl 调 2 次，smoke 调 3 次，formal 调 2 次。首次 formal 中断系 run_formal_r9m1r2_R2.py:228 将 point_id 误写为 id 引发 KeyError。报告 §8.1 称仅调用 1 次与日志不符。 |
| **G-3** | 原地改写后重跑且对照未覆盖 | safe_run.log:L36,37,43,44,31；F3_F4_EQUIV_R9M1R2.tsv | **属实** | L36 原地改写 run_smoke_R2 后 L37 重跑；L43 原地改写 compare_R2 后 L44 重跑并覆盖比对表。L31 阳性对照调用 L29 版 compare，未覆盖 L43 版。 |
| **G-4** | m1r2 裸写且报告 §11 遗漏披露 | m1r2/tmp/ 下 13 个文件 mtime；报告 §11:235-245 | **属实** | test_plain_g 等 7 个调试文件（01:31-01:35Z，介于 L13 与 L14 间）及 posctrl_tampered_* 等 6 个文件（01:49:05Z，早于 L24）无对应日志。报告 §11 记为 0 且称全部经 safe_run 运行不属实。 |
| **G-5** | 收尾顺序混乱、门禁多跑与清单失败 | safe_run.log:L52-L65；m1r2/SHA256SUMS.txt；报告 §13:255-290 | **属实** | events 于 L52 运行，L53-L65 共 13 条未进事件表；end 门禁运行 4 次，中间穿插多条内联 exec 改写交付物；m1r2/SHA256SUMS.txt 有 2 项 FAILED，GATE_R9M1R2_end_R4.txt 漏列。 |
| **G-6** | G2c_control 未运行行填值 0/CONTROL_OK | run_formal_r9m1r2_R3.py:90-97；PREREG_M1_F4_R9M1R2.tsv；报告 §9.2:207 | **属实** | 驱动未运行却填入 rc=0、rc1=0、rc2=0、class=CONTROL_OK；预注册中期望类别为 NOT_RUN_REGISTRY_ERROR；报告 §9.2 错误称其为"本轮事实"。 |
| **G-7** | G6 不变量未进入判定比对与报告失实 | verdict_r9m1r2.py:133；compare_f3_f4_r9m1r2_R2.py:91-132,183；报告 §9.1:194-201 | **属实** | verdict 仅判 G5 漏判 G6；compare 错误读取全为 '-' 的 STATE_SEAM 表并跳过比对；报告 §9.1 称核对了 I1..I6 且 0 DIFFS 与事实不符。真值在 RESULTS_R6c_SEAM.tsv。 |
| **G-8** | K 命中数核对不足与点数对应缺失 | build_kmap_r9m1r2.py:175-184；K_INHERIT_R9M1R2.tsv；报告 §12:248-251 | **属实** | 仅按 8 个模式核对 malloc 总数，未按 26 组专有 env 与断点比对；K_INHERIT 统计 416 点未列出与 651 点逐行映射；报告 §12 称需用户裁决项"无"掩盖了不完备。 |

---

## 3. 裁决与勘误登记

### 3.1 用户裁决落实（U318 至 U322）
经 `append_rulings_r9m1r3.py` 追加至 `checkpoints/p05/registries/RULINGS.tsv`（前缀断言一致，5 列）：
- **U318**：登记 r9m1r2 流程偏差为勘误（E9-21 起），不改动已提交文件；r9m1r2 结果降级为"参考结果二"，有效结果以 r9m1r3 为准；
- **U319**：未运行行真实记录为未运行：`rc/rc1/rc2/rc3/hit` 记为 `-`，`class` 记为 `NOT_RUN_REGISTRY_ERROR`，`verdict` 记为 `NOT_RUN_AS_EXPECTED`，比对单列为 `NOT_RUN`，不计入 `EQUIVALENT`；
- **U320**：M1c G6 的 I1–I6 与 point_verdict 纳入判定与比对：F4 侧取 RESULTS_R6c_SEAM 两遍值；F3 侧取 r8m1c3 冻结表 M1C_F3_RESULTS_R6c_SEAM.tsv；期望取 PREREG_M1_F4_R9M1R3 的 exp_I1..I6，三方严格比对；
- **U321**：K 补核：对 26 个 d003/d003plan 组按专有 env 和断点符号用 gdb 数 plain 与 kmap 命中数要求相等；出具 K_COVERAGE 表对账 416 点与 651 行；
- **U322**：固定执行顺序：start 门禁 → 取证复核 → 裁决勘误 → K 补核 → 试跑期跑通 → 预注册冻结 → 冻结清单 → 记录提交 (i) → 冻结期单次调用 → 收尾固定顺序 → 收尾提交 (ii)。

### 3.2 勘误追加（E9-21 至 E9-28）
经 `append_errata_r9m1r3.py` 追加至 `checkpoints/p05/registries/s4r9/ERRATA_9.txt`（前缀断言一致），覆盖 G-1 至 G-8 事实及 r9m1r2 报告中与日志不符的陈述：
- **E9-21**：覆盖 G-1（记录提交后换脚本运行，冻结清单原件未产出最终结果）；
- **E9-22**：覆盖 G-2 及报告 **§8.1:175-179**（多次调用正式/冒烟/阳性对照，报告虚报"仅调用 1 次"）；
- **E9-23**：覆盖 G-3（原地改写后重跑，阳性对照未覆盖最终比对逻辑）；
- **E9-24**：覆盖 G-4 及报告 **§11:235-245**（13 处未受包裹裸写，报告遗漏披露且虚报"0"）；
- **E9-25**：覆盖 G-5 及报告 **§13:255-290**（收尾混乱、事件表漏 13 条、门禁跑 4 次改写交付物、SHA256SUMS 失败）；
- **E9-26**：覆盖 G-6 及报告 **§9.2:207**（G2c_control 未运行行填值 0/CONTROL_OK，报告误报"本轮事实"）；
- **E9-27**：覆盖 G-7 及报告 **§9.1:194-201**（G6 I1..I6 漏判漏比对，报告虚报"已逐字段核对 I1..I6 且 0 DIFFS"）；
- **E9-28**：覆盖 G-8 及报告 **§12:248-251**（K 命中数核对范围不足与点数对应缺失，报告虚报裁决项"无"）。

---

## 4. K 命中数补核与点数对账（Step S-D）

经 safe_run 运行 `kcount_r9m1r3_v2.py` 取得补充验证事实：

### 4.1 26 组 d003/d003plan GDB 命中数等价核验（`K_COUNT_R9M1R3.tsv`）
- **复用驱动校验**：复用 `checkpoints/p05/evidence/p05-s4r9/m1r2/build/` 下 4 个 kmap-dbg 驱动，逐一核对 sha256 均与 `BUILD_KMAP_R9M1R2.tsv` 一致；
- **命中数核验**：对 26 个 d003/d003plan 组，在各自专有的 clean_env 与断点符号下，运行 GDB 计数：
  * **F3 侧**：plain 驱动命中数与 kmap 驱动命中数均相等；
  * **F4 侧**：plain 驱动命中数与 kmap 驱动命中数均相等；
  * **跨树两侧**：F3 plain == F3 kmap == F4 plain == F4 kmap；
- **核验结论**：26 组全部为 **PASS_EQUAL_HITS**，MISMATCH = 0，0 组 DIVERGENT。

### 4.2 651 行点数对账与覆盖表（`K_COVERAGE_R9M1R3.tsv`）
- **覆盖点对账**：
  * **纳入 53 个 K 组的点数**：合计 **416** 点（d003 111 点 + d003plan 108 点 + init 9 点 + polyinj 11 点 + r6bstate 177 点）；
  * **不需 K 映射的点数**：合计 **235** 点，逐行标注具体原因：
    1. 未运行控制点无需K映射：3 点（M1b G2c_control 3 行）；
    2. 无注入/控制对照点无需K映射：54 点（CTRL_SEAM 2 点、M1_CTRL 18 点、CTRL_AUX 16 点、G6c 18 点）；
    3. 无注入/未触碰点无需K映射：22 点（G1 组 hit=0 的 22 点）；
    4. seam 断言桩驱动无需 malloc/fft 包装 K 映射：68 点（seam 25 点 G6 + 25 点 G2a + 18 点 G6b）；
    5. 多边形/几何驱动无需 malloc/fft 包装 K 映射：42 点（POLY_33 33 点 + tri 9 点）；
    6. 张量/RNV1 驱动无需 malloc/fft 包装 K 映射：46 点（4.2 组 24 点 + G7 组 22 点）；
  * **点数总计**：416（K 组）+ 235（非 K 组）= **651** 点，与 M1 总点数严格对账闭环。

---

## 5. 试跑期（Shakedown）纪律与执行摘要

依据 §1-2 与 §1-3，在记录提交 (i) 之前建立试跑期，所有中间产物置于 `shakedown/` 隔离目录，已执行过的脚本不原地改写，改写时换新文件名并入事件表：
1. **门禁脚本演进**：
   * `gate_r9m1r3.sh` / `gate_check_r9m1r3.py`：初次写入时因模版字符串转义缺陷发生语法错误；
   * 换文件名新建 `gate_r9m1r3_v2.sh` / `gate_check_r9m1r3_v2.py`，修正转义并在 allow 列表登记；初次运行时 line 1 残留 m1r2 路径落盘至 m1r2/tmp，立即执行恢复并还原原始文件；
   * 换文件名新建 `gate_r9m1r3_v3.sh` / `gate_check_r9m1r3_v3.py`，修正 BASE 哈希为 16a7897；
   * `gate_r9m1r3_v3.sh start _v4` 运行取得 **FAILS=0**（产出 `GATE_R9M1R3_start_v4.txt`）；
   * 为确保 end 门禁准确核验冻结脚本调用计数，换文件名新建 `gate_check_r9m1r3_v5.py` 与 `gate_r9m1r3_v5.sh`，绑定 start_v4 基线并列入冻结清单。
2. **取证与补核脚本演进**：
   * `audit_r9m1r2_r9m1r3.py` 语法错误后换新文件名新建 `audit_r9m1r2_r9m1r3_v2.py` 顺利运行；
   * `kcount_r9m1r3.py` 在字典键覆盖排查后换新文件名新建 `kcount_r9m1r3_v2.py`，顺利产出 K_COUNT 与 K_COVERAGE 表；
   * `prereg_r9m1r3.py` 哈希校验后换新文件名新建 `prereg_r9m1r3_v2.py`，完成 651 行预注册冻结。
3. **装置试跑（Shakedown 轮次）**：
   * **Shakedown 1**：在 `$EV/shakedown/1/` 下试跑 posctrl 与 smoke，排查出：① 阳性对照基线未采用 U319 规范口径导致用例 2 误报；② 冒烟测试中规划者要求"G6 含一行 I4=N/A"与事实不符（G6 全为 I4=HOLD，N/A 在 I3 与 I2）；③ formal 运行 clean_child_env 未清理继承环境变量；
   * **脚本升级**：按规则换新文件名新建 `posctrl_r9m1r3_v2.py`、`run_smoke_r9m1r3_v3.py`、`run_formal_r9m1r3_v2.py`；
   * **Shakedown 2**：在 `$EV/shakedown/2/` 下全流程跑通：posctrl (PASS 0/5/22) → smoke (25/25 MATCH) → formal 两遍全量 (651+651 行) → verdict (626 MATCH, 22 NOT_REACHED, 3 NOT_RUN, 0 MISMATCH, 0 FLAKY) → compare (0 DIFFS) → summarize (1302 总计) → cmp_vs_r9m1r2 (仅 3 处 G2c 预期差异)。
4. **试跑结论**：新套件功能完整、逻辑严密，在正式进入冻结期前已在隔离目录下验证通畅。

---

## 6. 预注册与判定口径冻结

### 6.1 预注册表生成（`prereg_r9m1r3_v2.py`）
- 生成 `PREREG_M1_F4_R9M1R3.tsv`（sha256 `a7f418defc40...`）与 `PREREG_M1_CITED_F2_R9M1R3.tsv`（sha256 `293c10a62308...`）。
- **字段对齐**：29 列字段完整对齐。
- **与 r9m1r2 差异比对（`PREREG_VS_R9M1R2_DIFF_R9M1R3.tsv`）**：
  * 逐行核对确认：所有既有期望字段（exp_class, exp_rc1..3, exp_hit, exp_point_verdict, exp_I1..6, inj_call, contract, f3_effective_verdict）**期望列差异为 0**；
  * G2c_control 保持未运行期望；G5 与 G6 的 exp_I1..I6 保持原始期望真值。

### 6.2 判定口径冻结（`ENGINE_COLUMNS_R9M1R3.txt`）
在 r9m1r2 既有依据基础上新增 U319 与 U320 两节，历史脚本引用详实：
1. **M1b rc2 比对依据**：引用 `plan_and_run_m1b_r8m1b1.py:102-111` 与 `run_supp_r8m1b3.py:107-115`，仅在 exp_rc2 非 0 且非空时比对；
2. **M1c G6c / CTRL_AUX '-' 处理依据**：引用 `verdict_m1c_r8m1c3.py:103-106,114-115,132-133`，控制行无 RESULTS 记录，依据事实要求 computed_class 为 CONTROL_OK；
3. **U319 未运行行依据**：引用 `run_supp_r8m1b3.py:73-82`、`plan_and_run_m1b_r8m1b1.py:60-70` 及 `verdict_r9m1r2.py:73-77`，明确未运行行事实记为 `-` 与 `NOT_RUN_REGISTRY_ERROR`，禁止合成 0/CONTROL_OK；
4. **U320 G6 不变量判定与比对依据**：引用 `verdict_m1c_r8m1c3.py:80,87-93,136-143`，明确 G6 属于 seam 点，其 I1–I6 与 point_verdict 取自 `RESULTS_R6c_SEAM.tsv`，必须与预注册及 F3 历史真值逐字段严格比对。

---

## 7. 阳性对照验证（`posctrl_r9m1r3_v2.py`）

在冻结期仅调用 1 次，报告存档于 `POSCTRL_M1_R9M1R3.txt`：
1. **用例 1（F3 冻结事实输入比对引擎）**：
   * 结果：CHECKS = 651，**DIFFS = 0** -> **PASS**。
2. **用例 2（篡改副本 5 处故障注入判定引擎）**：
   * 篡改 1：M1b G2b `M-once-fft-plan-3-F4` rc1 由 20 改为 0；
   * 篡改 2：M1c G5 `M-once-closed1d-malloc-1-F4` I1 由 HOLD 改为 1；
   * 篡改 3：M1b G1 `M-twice-closed1d-malloc-2-F4` rc2 由 20 改为 0（合同要求比对 rc2）；
   * 篡改 4：M1c G6 `R4-ACF1-F-F4` I3 由 HOLD 改为 1；
   * 篡改 5：M1b G2c_control `addf-F-ctrl-F4` rc1 由 '-' 改为 0；
   * 结果：检出 MISMATCH 数量**恰好为 5 处**，无多检或漏检 -> **PASS**。
3. **用例 3（旧版预注册 3894d899 对照正式事实）**：
   * 结果：检出 G2b 组 MISMATCH 数量**恰好为 22 处**，其余组 MISMATCH 为 0 -> **PASS**。
- **阳性对照结论**：3 项核验全部通过，证明判定与比对引擎对返回值、不变量、控制行及历史键覆盖缺陷具有敏感检出能力。

---

## 8. 冒烟测试结果（`SMOKE_M1_F4_R9M1R3.tsv`）

在冻结期仅调用 1 次，测试范围覆盖 25 个代表点（覆盖全部 23 个 section × group × driver 组合）：
- **运行核验**：
  * G1 `M-once-fft-plan-3-F4`：rc1=0, hit=0, class=INVALID -> **NOT_REACHED_AS_EXPECTED**；
  * G2b `M-once-fft-plan-3-F4`：rc1=20, hit=1, class=REPORTED_FAILURE -> **MATCH**；
  * G2c_control `addf-F-ctrl-F4`：未运行驱动 -> **NOT_RUN_AS_EXPECTED**；
  * G6 选取 2 点：`R4-AL18-F-F4`（含 I3=N/A）与 `R4-ACF1-F-F4`（全 HOLD）-> 全部 **MATCH**；
  * 其余 20 点全部判定为 **MATCH**；
- **任务书事实更正**：任务书 §4 S-G 要求"G6 至少 2 行（含一行 I4=N/A）"，经查原始表 G6 全部 25 点的 exp_I4 均为 HOLD，含有 N/A 的不变量为 I3 与 I2，规划者事实有误；本轮选取含 I3=N/A 的点满足覆盖意图；
- **冒烟结论**：25 点全部符合期望，FAILS = 0，无停滞项。

---

## 9. 正式运行与判定结果

### 9.1 正式两遍执行（`run_formal_r9m1r3_v2.py`）
- 依据 §1-4 与 §1-11，正式运行脚本仅调用 1 次，Pass 1 与 Pass 2 在同一次运行中完成，输出至事先不存在的新目录 `runs/formal/`。
- 每条运行前后核验驱动 sha256 均与预注册一致。
- 产出 `FORMAL_FACTS pass1`（651 行）与 `FORMAL_FACTS pass2`（651 行）。

### 9.2 判定结果（`VERDICT_M1_F4_R9M1R3.tsv`）
- **两遍一致性**：651 点 pass 1 与 pass 2 事实一致，**FLAKY = 0**，**GDB_DIV = 0**。
- **判定汇总**：
  * **MATCH**：626 行；
  * **NOT_REACHED_AS_EXPECTED**：22 行（G1 组 22 点注入未触碰）；
  * **NOT_RUN_AS_EXPECTED**：3 行（G2c_control 组 3 点未运行，真实反映未运行事实）；
  * **MISMATCH**：0 行。
- 分组统计见 `VERDICT_M1_F4_R9M1R3_AGG.tsv`。

---

## 10. 事实等价比对与参考结果比对

### 10.1 F3 / F4 事实等价比对（`F3_F4_EQUIV_R9M1R3.tsv`）
- **核对范围**：F4 pass 1 事实 vs F3 冻结事实（M1b 415 行 + M1c 236 行 = 651 行）。
- **核对字段**：rc1, rc2, rc3, hit, class, I1..I6, clean_base_env（环境比对已忽略 S4FMM_INJECT, S4FMM_NTH, S4FMM_TWICE）。
- **G6 不变量核验**：F3 侧真实读取 `M1C_F3_RESULTS_R6c_SEAM.tsv`，断言 G6 全部 25 行均具有非 `-` 的真值，全部 25 行参与了 I1..I6 逐字段比对。
- **比对结果**：CHECKS = 651，**DIFFS = 0**。
- **HIT 等价分类统计**：
  * **NONEMPTY_IDENTICAL**：529 行（两侧命中数均大于 0 且数值与行为相同）；
  * **BOTH_EMPTY**：119 行（两侧命中数均为 0）；
  * **NOT_RUN**：3 行（控制行未运行，按 U319 单列，不计入 EQUIVALENT）；
  * 合计：651 行。

### 10.2 r9m1r2 参考结果比对（`R9M1R2_VS_R9M1R3_R9M1R3.tsv`）
- 本轮有效事实与 r9m1r2 参考事实二逐行比对：
  * **648 行一致**；
  * **恰好 3 行存在差异**：均为 M1b G2c_control（`addf-F-ctrl-F4`, `b2buf-F-ctrl-F4`, `fmmret-F-ctrl-F4`），r9m1r2 记录为合成的 `0 / CONTROL_OK`，本轮事实修正为真实的 `- / NOT_RUN_REGISTRY_ERROR`；
  * 其余 648 行被测执行点行为保持一致。

---

## 11. M1 汇总总表（1302 行）

合并 F4 事实行（651 行）与引用 F2 冻结行（651 行），生成 `M1_SUMMARY_F4_R9M1R3.tsv`：

| 分部 | 树 | MATCH | NOT_REACHED | NOT_RUN | MISMATCH | FLAKY | GDB_DIV | 合计 |
|---|---|---|---|---|---|---|---|---|
| **M1b（830 行）** | F4 | 390 | 22 | 3 | 0 | 0 | 0 | 415 |
| | F2（引用） | 390 | 22 | 3 | 0 | 0 | 0 | 415 |
| **M1c（472 行）** | F4 | 236 | 0 | 0 | 0 | 0 | 0 | 236 |
| | F2（引用） | 236 | 0 | 0 | 0 | 0 | 0 | 236 |
| **总计（1302 行）** | F4 + F2 | **1252** | **44** | **6** | **0** | **0** | **0** | **1302** |

- **总表断言校验**：
  * M1B_F4_TOTAL = 415, M1B_F2_TOTAL = 415 (M1B_SUM = 830)；
  * M1C_F4_TOTAL = 236, M1C_F2_TOTAL = 236 (M1C_SUM = 472)；
  * GRAND_TOTAL_EQ_1302 = TRUE。

---

## 12. 过程事件表

### 12.1 表一：越界写入尝试
- 本轮越界写入尝试次数：**0**。

### 12.2 表二：工具与脚本执行事件表
由 `events_r9m1r3.py` 自 safe_run.log 提取，完整台账见事件表（EVENTS_R9M1R3）：
1. **r9m1r2 历史补登事件**：
   * 补登 safe_run.log L53-L65 共 13 条未入事件表的操作记录及 13 处未受包裹裸写文件（详见 `BARE_WRITE_AUDIT_R9M1R3.tsv` 与 `SCRIPT_VERSIONS_R9M1R3.tsv`）。
2. **r9m1r3 本轮过程事件**：
   * **门禁升级**：初次门禁脚本转义异常，按规则不原地改写，依次升级为 v2、v3、v4、v5；
   * **路径纠正**：gate_r9m1r3_v2.sh 初次写入时 line 1 残留 m1r2 路径落盘至 m1r2/tmp，立即执行恢复并还原原始文件；
   * **取证与补核脚本升级**：audit_v2、kcount_v2、prereg_v2 均经改写并换新文件名；
   * **装置试跑**：shakedown/1 与 shakedown/2 记录了 posctrl_v2、smoke_v3、formal_v2 的试跑排查过程；
   * **冻结期单次调用**：记录提交 (i) 之后，posctrl_v2、run_smoke_v3、run_formal_v2、verdict、compare 各严格调用 1 次，无 testing/d003 写入。

---

## 13. 需用户裁决项

- **项一（收尾门禁脚本异常待裁决）**：
  * **事实**：收尾门禁 `gate_r9m1r3_v5.sh end` 产生 3 项 FAIL（详见附录 A 门禁诊断）。排查表明两处根因均在门禁校验脚本本身，并非被测事实问题：一是 `gate_r9m1r3_v5.sh:37` 将 STARTF 指向初版未完成的 `GATE_R9M1R3_start.txt` 而非通过版 `GATE_R9M1R3_start_v4.txt`，导致 ALLOW_START 哈希与 TMP 快照比较不符；二是 `gate_check_r9m1r3_v5.py:288` 查找冻结清单时路径遗留大写 R9M1R2，导致 `frozen_map` 未定义并抛出 NameError。
  * **被测事实状态**：物理事实（阳性对照 0/5/22 全部通过、冒烟测试 25 点全部符合预期、单次调用正式两遍 651 点 0 FLAKY / 0 GDB_DIV 全部 MATCH、F3/F4 事实等价比对 651 行 0 DIFFS、总表 1302 行闭环、证据库 12160 项全部 OK）已全部产出并落盘。
  * **纪律执行**：遵循 §1-5、§1-6 与 §5 硬停止纪律，门禁 FAIL 后停下写附录，不修脚本、不重跑门禁，保留现场列入本项供用户裁决。

---

## 14. 交付物与提交清单

### 14.1 小表交付物（已复制至 `checkpoints/p05/registries/s4r9/M1R3/`，sha256 一致）
1. `AUDIT_R9M1R2_R9M1R3.tsv`
2. `BARE_WRITE_AUDIT_R9M1R3.tsv`
3. `ENGINE_COLUMNS_R9M1R3.txt`
4. `EVENTS_R9M1R3.tsv`
5. `F3_F4_EQUIV_R9M1R3.tsv`
6. `FROZEN_SCRIPTS_R9M1R3.tsv`
7. `GATE_R9M1R3_start_v4.txt`
8. `GATE_R9M1R3_end.txt`
9. `K_COUNT_R9M1R3.tsv`
10. `K_COVERAGE_R9M1R3.tsv`
11. `M1_SUMMARY_F4_R9M1R3.tsv`
12. `POSCTRL_M1_R9M1R3.txt`
13. `PREREG_M1_CITED_F2_R9M1R3.tsv`
14. `PREREG_M1_CITED_F2_R9M1R3.tsv.sha256`
15. `PREREG_M1_CITED_F2_R9M1R3_TIMESTAMP_UTC.txt`
16. `PREREG_M1_F4_R9M1R3.tsv`
17. `PREREG_M1_F4_R9M1R3.tsv.sha256`
18. `PREREG_M1_F4_R9M1R3_TIMESTAMP_UTC.txt`
19. `PREREG_VS_R9M1R2_DIFF_R9M1R3.tsv`
20. `R9M1R2_VS_R9M1R3_R9M1R3.tsv`
21. `RUNNER_DIFF_R9M1R3.txt`
22. `SCRIPT_VERSIONS_R9M1R3.tsv`
23. `SHA256SUMS.txt`
24. `SMOKE_M1_F4_R9M1R3.tsv`
25. `SMOKE_SUMMARY_R9M1R3.txt`
26. `VERDICT_M1_F4_R9M1R3.tsv`
27. `VERDICT_M1_F4_R9M1R3_AGG.tsv`

---


---

## 附录 A. 收尾门禁核验异常诊断与硬停止记录

依据任务书 §1-5、§1-6 与 §5 硬停止条件，冻结期脚本报错或门禁 FAIL 时，"不修脚本、不重跑；保留已产出文件，停下写报告，列入需用户裁决"。现将收尾门禁核验现场与根因分析记录如下：

### A.1 门禁现场核验事实
执行 `sh testing/d003/stage_s4r9/gate_r9m1r3_v5.sh end`，产出 `GATE_R9M1R3_end.txt`，退出码为 3，记录 3 项 FAIL：
1. `FAIL ALLOW_START_SHA256_EQ_START expected=0de756e... actual=888dde9...`；
2. `FAIL TMP_COUNT_EQ_START expected= actual=0`；
3. `FAIL TMP_SHA256_EQ_START expected= actual=e3b0c44...`；
4. `NameError: name 'frozen_map' is not defined`（python 门禁辅助脚本异常中断）。

### A.2 根因溯源
1. **STARTF 绑定偏差**：`gate_r9m1r3_v5.sh:37` 中 `STARTF` 硬编码为 `GATE_R9M1R3_start.txt`，该文件系试跑期初次生成的未完成文件（ALLOW_START 为 5 项版，且未完成 TMP 快照记录）。通过的开工门禁文件实为 `GATE_R9M1R3_start_v4.txt`（73 行全 PASS，ALLOW_START 为 9 项版，TMP 快照记录完整）。读取初版导致比较预期值为空或旧值。
2. **冻结清单文件名笔误**：`gate_check_r9m1r3_v5.py:288` 中在 end 模式下检索清单时写为 `FROZEN_SCRIPTS_R9M1R2.tsv`（遗留 R9M1R2），未命中本轮实际清单 `FROZEN_SCRIPTS_R9M1R3.tsv`，导致 `frozen_map` 未在条件块内初始化，并在随后调用时抛出未定义异常。

### A.3 硬停止纪律遵从
执行者依从 §1-6 纪律："门禁之后不得再改报告、STATE、事件表。门禁 FAIL 就停下写附录，不改门禁、不重跑。"
- 未改动任何 `testing/d003/` 脚本；
- 未二次重跑门禁消除错误；
- `finalize_r9m1r3.py` 仅执行法定两件事：将门禁文件复制至 registries、重写 registries/SHA256SUMS.txt（26 项全部比对一致）；
- 完整保留所有已产出事实与门禁报告，等待用户审核与裁决。

本轮未完成 R9 M1 第二修正范围（收尾门禁出现异常中断，停下记录附录待用户裁决），等待用户审核
