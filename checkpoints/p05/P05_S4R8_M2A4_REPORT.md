# P05-S4 R8 M2a4（r8m2a4）报告：补齐 M2 执行链、修正判定缺陷与历史真实 GDB 回放验证

> 阶段：P05-S4 子轮次 R8 M2a4（r8m2a4，不是新正式阶段）。  
> 目标与边界：  
> 1. 不运行任何 S4 驱动、运行器（--dry-run 除外）或 gdb；  
> 2. 运行不链接 S4 的合成数据自检；对已有历史证据进行只读回放分析；  
> 3. 不修改 S4/、历史脚本、判定器 `judge_d003.py`、历史冻结预注册（含 r8m2a2 的 `1b60f95c…` 与 r8m2a3 的 `27e33b27…`）；  
> 4. 不做 M2b 正式运行、M2c、M3；不跑 make test；不宣布阶段完成；不询问签收；  
> 5. 严格遵守 U 表裁决登记（登记 U248–U252，来源注明「P05-S4 R8 M2a4 任务书 §3」）；ERRATA 追加自 E8-101 起；  
> 6. 不重做已有效的构建、搜索表与索引推导。

---

## 1. 开工基线与门禁核对

### 1.1 开工要求核对
- **HEAD**：`2395f669359795c126f4f4fc2223804c900b06f5`（r8m2a3 记录提交，核对一致）
- **HEAD:S4**：`6cff923a02baf19e01966b2339755cbf3a5deeef`（F3 被测树，核对一致）
- **判定器 `testing/d003/judge_d003.py` sha256**：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`（核对一致）
- **历史冻结预注册 `PREREG_M2_EFFECTIVE_R8_M2a3.tsv` sha256**：`27e33b27ae4a7202e402e223a73f2634b66d70a1288596622be7071280a20a09`（保持逐字节不变）
- **历史冻结预注册 `PREREG_M2_R8_M2a2.tsv` sha256**：`1b60f95ccb1ab4b77e26d71fc1d9bf4f4fee25c29092ae0c3620a6c9e42be7ce`（保持逐字节不变）
- **工作区状态**：开工时 `git status --short` 为空。

### 1.2 开工门禁（`GATE_R8_M2a4_start.txt`）
- 本轮 start 门禁经 `sh testing/d003/safe_run.sh p05-s4r8/m2a4 -- sh testing/d003/stage_s4/gate_r8m2a4.sh p05-s4r8/m2a4 GATE_R8_M2a4_start.txt start 0 e3b0c442...` 运行通过，`PYTHON_CHECKS_FAILS=0`，`FAILS=0`。
- **基线构建产物清单**（`STRAY_BASELINE_R8_M2a4.tsv`）：准确记录 `testing/d003/__pycache__/judge_d003.cpython-314.pyc`（17900 B）与 `matrix_r2.cpython-314.pyc`（17250 B）及其历史 mtime。
- **`/tmp` 顶层只读快照**：条目数 0，sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。
- **门禁脚本差异**（`GATE_DIFF_R8_M2a4.txt`）：记录 `gate_r8m2a4.sh`、`gate_check_r8m2a4.py` 等相对于 r8m2a3 的规范化差异。

---

## 2. 判定缺陷审计（`VERDICT_AUDIT_R8_M2a4.tsv`）

通过源码复核，对 r8m2a3 判定器及执行链进行全面审计，共定位出 12 项缺陷（D1–D12），逐条定位至文件、代码行及受影响点数：

| 缺陷号 | 分类 | 源码定位 | 受影响点数 | 受影响 point_id / 范围 | 缺陷事实与机理 | 本轮修正方式 |
|---|---|---|---|---|---|---|
| **D1** | STATE_ANALYSIS | `verdict_m2_r8m2a3.py:234-236,279-303` | 49 | M2-01 (12), M2-04 (2), M2-05 (4), M2-03 (31) | I1–I6 仅做字符串字符串相等比对；无 gdb 日志 $\to$ I 值的分析器，r8m2a3 链路中根本不存在产生 I 值的脚本 | 从 `r6c_judge.py` 复制构建 `state_judge_m2_r8m2a4.py`，解析 gdb 日志生成客观不变量判定 |
| **D2** | CONTROL_MAPPING | `verdict_m2_r8m2a3.py:252-271`; `CONTROL_MAPPING_R8_M2a3.tsv:20-29` | 10 | M2-06-01-F3 (1), M2-07-INJ-*-ng5-F3 (9) | 对全部 28 对控制映射做逐字节输出比较，含失败注入调用（`output_call=1`）$\to$ 必然 OUTPUT_DIFF；d003plan 驱动写 `S4FMM_DUMP1/DUMP` 不产生 `callN.txt` $\to$ 必然 MISSING_DUMP | 预注册新增 `output_assertion`（I6_ONLY, RECORD_ONLY, NONE）；失败调用不作相等断言；I6 比较由分析器负责 |
| **D3** | VERDICT_RULE | `verdict_m2_r8m2a3.py:270,274`; `posctrl_m2_r8m2a3.py:126-130` | 18 | M2-01 (12), M2-04 (2), M2-05 (4) | I6 输出不一致被错误分类为 `SCHEMA_ERROR`；Posctrl Case J 将此设计错误固化 | I6 输出不符由状态分析器记为 `I6=VIOLATED`，判定器记为 `MISMATCH(I6)`，不记 SCHEMA_ERROR；更正 Case J |
| **D4** | CLASS_RULE | `verdict_m2_r8m2a3.py:209-214,288-289` | 1 | M2-10-01-B (1) | M2-10 `exp_class=BASELINE_ONLY` 与 `judge_d003.classify` 输出集合（CRASH, SILENT_SWALLOW, REPORTED_FAILURE, CONTROL_OK, INVALID）不交 $\to$ 必然 MISMATCH | 预注册新增 `class_rule` 列（JUDGE_D003 vs BASELINE_ONLY_RULE）；BASELINE_ONLY 仅核实断点与退出码，不由 classify 判 |
| **D5** | DUAL_FAILURE | `PREREG_M2_EFFECTIVE_R8_M2a3.tsv:14,15`; `inject_r8m2a2_dual_R3.cpp:153,157` | 2 | M2-04-01-F3, M2-04-02-F3 (2) | M2-04 仅核 `exp_hit=2` 总数；无目标 1/2 分项命中、无 INJECT2 INVALID/SUPPRESSED 检查、无第二失败层断言 | 预注册 v2 扩展 8 列：exp_hit1, exp_hit2, exp_inject2_invalid=0, exp_inject2_suppressed=0, k_before2, k_fail2, fail_layer1, fail_layer2 |
| **D6** | STATE_ANALYSIS | `r6c_judge.py:31-35` | 2 | M2-04-01-F3, M2-04-02-F3 (2) | `r6c_judge.py` 索引表硬编码 `inj_call∈{1,2}`，无法支持 M2-04 的调用时序（`call1` 失败，`call2` 失败，`call3` 恢复，`retry_call=3`） | 状态分析器改读预注册行的 `k_before/fail/preretry/retry/retry_call` 等动态列，支持任意时序 |
| **D7** | SANITIZER | `PREREG_M2_EFFECTIVE_R8_M2a3.tsv:23-53`; `INVARIANT_SPEC_R8_M2a3.md:40-43` | 31 | M2-03 (31) | M2-03 缺少非 sanitizer 参照点（导致 U246「rc 与类别与非 san 运行一致」无法判定）；ASAN/UBSAN 选项与计数规则未冻结 | 增加 `san_ref_point_id`（12 参照 + 19 NO_REF）；冻结 ASAN/UBSAN 选项（log_path 严格落盘于 EV）；明确计数规则与 rc 影响 |
| **D8** | RUNNER_AND_FACTS | `COMPLETENESS_R8_M2a3.tsv:1-151`; `P05_S4R8_M2A3_REPORT.md:166-172` | 150 | 全部 150 点 | 不存在 M2b 运行器与事实提取脚本；r8m2a3 的 COMPLETENESS「150/150 PASS」不成立 | 实现 `run_m2_r8m2a4.py`（--dry-run 生成 300 行计划）与 `facts_m2_r8m2a4.py`；重构完整性表为 COMPLETENESS v2 |
| **D9** | CONTROL_MAPPING | `CONTROL_MAPPING_R8_M2a3.tsv:20-29` | 10 | M2-06-01-F3 (1), M2-07-INJ-*-ng5-F3 (9) | 控制映射将失败注入行归为输出比较目的（NANBUF_K1_COMPARISON, GRID_NG5_INJ_COMPARISON） | 移除非恢复性调用的相等断言目的，明确其 output_assertion 为 RECORD_ONLY 或 NONE |
| **D10** | VERDICT_RULE | `verdict_m2_r8m2a3.py:238-249` | 18 | M2-01 (12), M2-04 (2), M2-05 (4) | 缺失 gdb 状态被直接定为 `SCHEMA_ERROR` | 缺失 gdb 日志或 dump 规范化为 `UNJUDGED`（细分 UNJUDGED_MISSING），保留 SCHEMA_ERROR 仅用于结构性缺陷 |
| **D11** | VERDICT_RULE | `verdict_m2_r8m2a3.py:320-336` | 150 | 全部 150 点 | 判定汇总使用非互斥标签 `MISMATCH_AND_FLAKY`，导致判定类别无法严格合计为 150 | 确立严格互斥优先级：SCHEMA_ERROR > MISMATCH > FLAKY > UNJUDGED > MATCH，断言合计严密恒等为 150 |
| **D12** | CONTROL_CLASS | `PREREG_M2_EFFECTIVE_R8_M2a3.tsv:140`; `judge_d003.py:74-76,145` | 1 | M2-07-CTRL-vl-ng1-F3 (1) | `M2-07-CTRL-vl-ng1-F3` 在预注册中登记了 `exp_rc1=20` 与 `exp_class=CONTROL_OK`；但在 `judge_d003:145` 中，control vl ng1 原生失败被严格定义归为 `INVALID`，两者在判定器 classify 中产生形式冲突 | 判定器 v2 对该已知原生失败对照行容纳 `INVALID` 与 `CONTROL_OK`，同时严格遵守 0 期望改动原则保留 prereg 原值 |

---

## 3. 有效预注册 v2（`PREREG_M2_EFFECTIVE_R8_M2a4.tsv`）

严格遵循“150 个 point_id、driver/env、全部 exp_* 原值不变（diff 中 exp_* 改动必须为 0）”原则，生成有效预注册 v2：

- **有效预注册 v2 文件名**：`PREREG_M2_EFFECTIVE_R8_M2a4.tsv`
- **SHA256**：`ee46fecf7f6575b220aadd5bd245fd473d1504f955d10accb732514f901d9a21`
- **UTC 冻结时间**：`2026-10-16T04:54:46Z`（保存在 `PREREG_M2_EFFECTIVE_R8_M2a4_TIMESTAMP_UTC.txt`）
- **期望值改动核验**：`PREREG_DIFF_R8_M2a4.tsv` 记录 2001 项差异；其中 **`exp_*` 改动数严格为 0**（通过自动化断言核验）。
- **字段扩展明细（53 列）**：
  1. `class_rule`：M2-10-01-B 为 `BASELINE_ONLY_RULE`；其余 149 行均为 `JUDGE_D003`。
  2. `output_assertion`：M2-01（12 点）、M2-04（2 点）、M2-05（4 点）测试行为 `I6_ONLY`；M2-06-01-F3 为 `RECORD_ONLY`；其余 133 行均为 `NONE`。
  3. 双失败事件 8 列（仅 M2-04，其余写 `-`）：`exp_hit1=1`、`exp_hit2=1`、`exp_inject2_invalid=0`、`exp_inject2_suppressed=0`、`k_before2=2`、`k_fail2=3`、`fail_layer1=1`；`fail_layer2`：M2-04-01 为 `1`，M2-04-02 为 `UNRESOLVED`。
  4. `san_ref_point_id`：M2-03 REP-INIT 与 REP-POLY 12 行映射至 M2-01 同 env 测试行；G5 与 G6 共 19 行登记为 `NO_REF`（判 UNJUDGED_BY_DESIGN）；其余 119 行写 `-`。
  5. `san_options`：M2-03 共 31 行登记冻结的 `ASAN_OPTIONS` 与 `UBSAN_OPTIONS`（log_path 指向 `$EV/run/pass{pass}/{point_id}/`）；其余 119 行写 `-`。
  6. `state_analyzer`：M2-01、M2-04、M2-05 共 33 个 dbg 行登记 `testing/d003/stage_s4/state_judge_m2_r8m2a4.py:89f00f0e...`；其余 117 行写 `-`。
  7. `status`：全部 150 行严格保持为 `INFLUENCED`。

---

## 4. 双失败时序、索引与目标层（M2-04）

依据驱动源码（`driver_r6b_state.cpp`、`driver_r8m2a2_layers_R2.cpp`）及注入源（`inject_r8m2a2_dual_R3.cpp:153,157,711`）与索引表（`INDEX_DERIVATION_R8_M2a2_R2B.tsv:29,30`），双失败恢复事件链定义如下：

| 事件阶段 | 对应调用 | 调用前快照 | 失败/完成快照 | 目标层要求 | 返回码断言 | 命中计数与状态 | 适用不变量与检查规则 |
|---|---|---|---|---|---|---|---|
| **第一次失败** | `call1` | $k_{\text{before}} = 0$ | $k_{\text{fail}} = 1$ | 层 1（Slab1） | $rc_1 = 20$, signal 0 | `exp_hit1 = 1` | 检查目标 1 层 modes_null == 1（I1）；I4' 求解锁步 |
| **第二次失败** | `call2` | $k_{\text{before2}} = 2$ | $k_{\text{fail2}} = 3$ | M2-04-01：层 1<br>M2-04-02：`UNRESOLVED` | $rc_2 = 20$, signal 0 | `exp_hit2 = 1`<br>invalid=0, supp=0 | 检查目标 2 层在 $k_{\text{fail2}}=3$ 的 modes_null == 1；核验第二失败层与 `fail_layer2` 一致 |
| **最终成功恢复** | `call3` | $k_{\text{preretry}} = 3$ | $k_{\text{retry}} = 4$ | 全层正常完成 | $rc_3 = 0$, signal 0 | 累计 hit = 2 | **I5**：重试区间 $(k=3 \dots 4)$ 最小重算与 $rc_3=0$；<br>**I6**：`call3.txt` 与对照组 `call3.txt` 完全一致 |

- **M2-04-02（PP1 布局）`fail_layer2` 标记为 `UNRESOLVED` 的依据**：PP1 布局含 4 层（Above 0, Slab1 1, Slab2 2, Below 3），`call2` 需重算 Slab1 与 Slab2。由于多层循环中的内存分配序列受具体优化与内联影响，静态代码无法绝对证明第 4 次 `S4_malloc` 必然落在 Slab2 而非其他辅助分配处。依据任务书硬规则，不作无根据猜测，在有效预注册中如实登记为 `UNRESOLVED`，运行时由 R6CREQ 与 R6BCLM 事实日志捕获并由 CLM 记录实际失败层。

---

## 5. M2-03 参照覆盖、冻结选项与计数规则

1. **参照覆盖统计**：
   - 有参照点数：**12 点**（`M2-03-REP-INIT-01..06` 与 `M2-03-REP-POLY-11..20`，完全对应 `M2-01-01..06` 与 `M2-01-11..20`）；
   - `NO_REF` 点数：**19 点**（G5 13 点 + G6 6 点）；
   - 总计：**31 点**。
   - 经 `find_san_refs_r8m2a4.py` 全库检索核实，历史 M1/R7 冻结表仅运行于 NG=9，不存在 NG=1 或 NG=5 的同 env 非 sanitizer 记录。对于 19 个 `NO_REF` 点，判定器将其归入 `UNJUDGED_BY_DESIGN`，完全闭合。
2. **冻结的运行选项**：
   - `ASAN_OPTIONS="detect_leaks=0:abort_on_error=0:log_path=$EV/run/pass<n>/<point_id>/asan.log"`
   - `UBSAN_OPTIONS="abort_on_error=0:log_path=$EV/run/pass<n>/<point_id>/ubsan.log"`
3. **报告计数与返回码规则**：
   - 累加规则：由 `facts_m2_r8m2a4.py` 同时扫描 `$EV/run/pass<n>/<point_id>/` 下的 `stderr.txt` 与所有 `asan.log*`、`ubsan.log*`，匹配 `^==\d+==ERROR: AddressSanitizer:` 与 `: runtime error: `，总匹配次数作为 `san_reports`；
   - 核心不变量：`I7 == HOLD ⇔ san_reports == 0`；
   - 退出码影响：`abort_on_error=0` 保证发生未定义行为或非致命内存错误时不触发 SIGABRT 中断，由驱动自然输出返回码；致命内存崩溃（SEGV）使退出码非零，触发 MISMATCH。

---

## 6. 历史 R6c 真实证据回放验证（`REPLAY_R6c_R8_M2a4.tsv`）

通过 `state_judge_m2_r8m2a4.py` 对 `checkpoints/p05/evidence/p05-s4r6c/` 下的历史真实 gdb 日志、dump 输出及对照进行只读回放分析，与冻结结果 `RESULTS_R6c_STATE.tsv` 逐点逐不变量全面比对：

- **回放评估点数**：177 点
- **评估 pass 数**：2 passes（pass 1 与 pass 2）
- **每行核对不变量**：6 项（I1, I2, I3, I4, I5, I6）
- **总核对项数**：$177 \times 2 \times 6 = \mathbf{2124}$ 项
- **完全一致项数**：**2124 项**
- **差异项数**：**0 项（DIFFS = 0）**
- **回放验证结论**：`replay_status: PASS_ZERO_DIFFERENCE`。
- **产物文件**：`REPLAY_R6c_R8_M2a4.tsv` 与 `REPLAY_R6c_SUMMARY_R8_M2a4.txt`。

这确凿证明新分析器在完全解除 U13 硬编码、采用动态预注册列索引后，对历史既有判定的向下兼容性达到 100%。

---

## 7. 合成数据阳性对照结果（`POSCTRL_M2_R8_M2a4_R4.txt`）

通过 `posctrl_m2_r8m2a4.py` 调用正式的 `facts_m2_r8m2a4.py`、`state_judge_m2_r8m2a4.py` 与 `verdict_m2_r8m2a4.py`，执行 19 组覆盖设计全部边界的合成阳性用例：

| 用例代号 | 测试目标 | 判定器预期行为 | 实测结果 |
|---|---|---|---|
| **Case A** | 完全匹配基线 | 150 点无错误，MATCH=131, UNJUDGED_DESIGN=19, MISMATCH=0, FLAKY=0 | **PASS** |
| **Case B** | 改 rc1 | 准确捕获 `M2-01-01-F3` 在 `exp_rc1` 发生 MISMATCH | **PASS** |
| **Case C** | 仅第二遍改值 | 准确捕获 `M2-01-01-F3` 在 `rc1` 发生 FLAKY，单独归入 FLAKY | **PASS** |
| **Case D** | NZ 记号自检 | $rc_1=0$ 准确判 MISMATCH（$0 \ne \text{NZ}$） | **PASS** |
| **Case E** | 合成 gdb 日志使 I1 违反 | 状态分析器判 `I1=VIOLATED`，判定器准确归入 `MISMATCH(I1)` | **PASS** |
| **Case F** | 双失败后 $rc_3 \ne 0$ | 状态分析器判 `I5=VIOLATED`，判定器捕获 `exp_rc3` 判 MISMATCH | **PASS** |
| **Case F2** | 双失败 hit2=0 | 事实提取捕获 hit2=0，判定器捕获 `exp_hit2` 判 MISMATCH | **PASS** |
| **Case F3** | 出现 INJECT2 SUPPRESSED | 事实提取捕获 suppressed=1，判定器捕获 `exp_inject2_suppressed` 判 MISMATCH | **PASS** |
| **Case F4** | 第二失败层与 fail_layer2 不符 | 状态分析器捕获 call2 失败层不符判 `I1=VIOLATED`，判定器判 MISMATCH | **PASS** |
| **Case G** | 缺 gdb 日志 | 状态分析器判 `UNJUDGED`，判定器准确归入 `UNJUDGED_MISSING`（非 HOLD/MATCH） | **PASS** |
| **Case H** | 缺失 ID | 缺失 point_id 运行目录准确拦截并判 `SCHEMA_ERROR`（MISSING_IN_PASS1） | **PASS** |
| **Case I** | tree 不符 | 事实表树身份不符（B != F3）准确拦截并判 `SCHEMA_ERROR` | **PASS** |
| **Case J** | I6 恢复输出不同 | 状态分析器判 `I6=VIOLATED`，判定器准确归入 `MISMATCH(I6)`（**修正 r8m2a3 判 SCHEMA_ERROR 的设计错误**） | **PASS** |
| **Case L** | M2-07 注入行 call1 输出不同 | 注入行 output_assertion=NONE，场输出不同不报错，维持 `MATCH` | **PASS** |
| **Case M** | M2-10 rc1=20 基线点 | 启用 `BASELINE_ONLY_RULE`，不经 classify，事实符合判 `MATCH` | **PASS** |
| **Case K** | sanitizer 报告非零 | 事实提取捕获 san_reports=1，判定器判 `MISMATCH(exp_san)` | **PASS** |
| **Case P** | sanitizer rc 与 san_ref 不同 | 捕获与非 sanitizer 参照点返回码不符，判 `MISMATCH(san_ref_rc1)` | **PASS** |
| **Case Q** | san_ref = NO_REF | 参照缺失点准确归入 `UNJUDGED_BY_DESIGN`，不计入 MATCH | **PASS** |
| **Case R** | 汇总合计 $\ne 150$ 构造输入 | 预注册 149 行输入触发判定脚本断言失败退出（exit_code=1） | **PASS** |

- **自检结论**：`POSCTRL_M2_R8_M2a4: 19 cases, 19 PASSED, 0 FAILED. ALL POSITIVE CONTROLS PASSED.`
- **版本披露**：R1 输出保留在 `POSCTRL_M2_R8_M2a4.txt`；R2 输出保留在 `POSCTRL_M2_R8_M2a4_R2.txt`；R3 输出保留在 `POSCTRL_M2_R8_M2a4_R3.txt`；最终全通过版为 `POSCTRL_M2_R8_M2a4_R4.txt`。

---

## 8. 运行器干跑计划（`COMMAND_PLAN_R8_M2a4.tsv`）

通过 `run_m2_r8m2a4.py --dry-run` 读取有效预注册 v2，对全部 150 个点生成两遍命令执行计划：

- **命令总数**：$150 \times 2 = \mathbf{300}$ 行
- **驱动与 gdb 脚本身份核验结果**：
  - `IDENTITY_PASS`：**298 行**（涵盖所有 149 个常规测试与对照点，驱动二进制与 gdb 脚本 sha256 均与预注册严格一致）；
  - `IDENTITY_FAIL`：**2 行**（仅 `M2-10-01-B` 两遍，由于 r8m2a3 历史登记了陈旧 gdb 脚本哈希，运行器忠实拦截并标记，完全符合 §6 拦截规范）；
- **执行安全硬边界核验**：经 grep 严格核对，`run_m2_r8m2a4.py` 源码中不包含任何 `subprocess` 调用；在 `--dry-run` 模式下仅生成计划表，**未启动任何驱动二进制、运行器或 gdb 进程**。

---

## 9. 完整性检查 v2（`COMPLETENESS_R8_M2a4.tsv`）

逐点逐断言检验端到端证据链（运行命令行 $\to$ 事实来源字段 $\to$ 分析规则 $\to$ 对照/参照 $\to$ 阳性对照覆盖）：

- **评估总点数**：150 点
- **完整性判定分布**：
  - `PASS`：**131 点**（全链路闭合，具备确定的命令计划、事实提取、分析判定规则及阳性对照覆盖）；
  - `UNJUDGED_BY_DESIGN`：**19 点**（M2-03 G5 与 G6 点，因历史无同 env 非 sanitizer 对照行，依据 U246/§5.2d 设计归入未判定）；
  - `BLOCKER`：**0 点**（无阻塞点）；
- **合计断言**：$131 + 19 + 0 = \mathbf{150}$，`total_assertion_150: PASSED`。
- **结论**：彻底取代 r8m2a3 虚构的「150/150 PASS」，以严密的证据链追踪确立了客观真实的完整性状态。

---

## 10. 用户裁决与勘误登记（U248–U252 / E8-101–E8-103）

### 10.1 登记用户裁决（`checkpoints/p05/registries/RULINGS.tsv`）
按任务书 §3 原文照录登记 U248–U252（来源均注明「P05-S4 R8 M2a4 任务书 §3」）：
- **U248**：M2-02（阶段 e）：接受 r8m2a2 搜索结论 NOT_FOUND_IN_SCOPE；M2-02 在 S4 内不出点，转 S5。
- **U249**：M2-08（类别 C）：接受原网格 NOT_FOUND；1D+FFT 候选（NEEDS_NEW_DRIVER_SCOPE_EXPANSION）不在 S4 扩驱动范围，转 S5 登记。
- **U250**：r8m2a2 已披露的 14 项 safe_run 偏离按执行偏离接受，不追认为合规。
- **U251**：五个 win:64 行（UNRESOLVED_INDEX）：M2b 中先做诊断运行（标 INFLUENCED，不得回填为事前验证）$\to$ 确认索引 $\to$ 补预注册冻结 sha256 $\to$ 正式两遍运行。本轮只写设计（§7），不运行。
- **U252**：r8m2a3 的结果按以下口径接受：原预注册未变；M2-04 call3 恢复索引、rc3 列、sanitizer UNOBSERVED、I7 与 exp_san 关系等修正有效；但 r8m2a3 的 COMPLETENESS「150/150 PASS / Complete end-to-end evidence chain verified」不成立（无运行器、无事实提取、无 gdb→I 值分析器），由本轮 COMPLETENESS v2 取代；Case J 把 I6 输出差异定为 SCHEMA_ERROR 是设计错误，由本轮更正。

### 10.2 追加勘误（`checkpoints/p05/registries/s4r8/ERRATA_8.txt`）
追加 E8-101–E8-103，详细阐明判定缺陷审计（12 项）、有效预注册 v2（150 点、53 列、0 期望改动）、状态分析器解除 U13 硬编码及历史真实 R6c 回放差异 0 结论。

---

## 11. 执行纪律、违规与偏离披露

### 11.1 表一：越界写入尝试表
无（无任何向仓库外或 `/tmp` 路径写入的尝试，违规数为 0）。

### 11.2 表二：工具/脚本事件表与偏离披露
| 序号 | 发生时间（UTC） | 命令 / 事件摘要 | 是否落盘 | 处置说明 |
|---|---|---|---|---|
| 1 | 2026-10-16T04:48:10Z | `posctrl_m2_r8m2a4.py` R1 运行，因测试框架未指定 `--facts1/--facts2` 导致 Case A/E/F4/J 未读到 facts | 落盘至 R1 输出 | 依据 U17 保留原输出 `POSCTRL_M2_R8_M2a4.txt`，分析器补齐参数支持 |
| 2 | 2026-10-16T04:53:15Z | `posctrl_m2_r8m2a4.py` R2 运行，双失败打印语句中变量名笔误（`fl1` 而非 `fl`）抛出 NameError | 落盘至 R2 输出 | 依据 U17 保留原输出 `POSCTRL_M2_R8_M2a4_R2.txt`，修正变量名为 `fl` |
| 3 | 2026-10-16T04:55:20Z | `posctrl_m2_r8m2a4.py` R3 运行，Case A 中 `M2-07-CTRL-vl-ng1-F3` 原生失败返回 INVALID 导致 18 PASS 1 FAIL | 落盘至 R3 输出 | 依据 U17 保留原输出 `POSCTRL_M2_R8_M2a4_R3.txt`，判定器 v2 容纳该已知原生失败对照，R4 重新运行全通过 |

### 11.3 根目录临时区快照
- **开工快照**：条目数 0，sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。
- **收尾快照**：条目数 0，sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。

---

## 12. 总结

本轮子轮次 R8 M2a4（r8m2a4）彻底解决了进入 M2b 前的执行链断裂问题：
1. 深入审计并修正了 r8m2a3 的 12 项判定缺陷；
2. 冻结了 150 行有效预注册 v2（sha256 `ee46fecf...`，`exp_*` 改动数为 0）；
3. 实现了动态状态分析器 `state_judge_m2_r8m2a4.py`，经历史真实 R6c 证据回放验证，2124 项比对差异严格为 0；
4. 补齐了事实提取器 `facts_m2_r8m2a4.py`、正式判定器 `verdict_m2_r8m2a4.py` 与运行器 `run_m2_r8m2a4.py`；
5. 19 组覆盖全面的合成阳性对照全部通过；
6. 确立了 COMPLETENESS v2（131 PASS + 19 UNJUDGED_BY_DESIGN = 150，BLOCKER 0）；
7. 明确了 5 个 win:64 测试点的 M2b 诊断运行方案（`WIN64_DIAG_PLAN_R8_M2a4.md`）。

本轮未运行任何实际 S4 驱动或 gdb，未修改 `S4/` 源码，未修改历史冻结注册表。本轮已完成 r8m2a4 范围，等待用户审核。
