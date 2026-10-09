# 本次公共链成功终态的有限验收更正

- 报告目录：`/srv/nvme/projects/S4-Stanford-Stratified-Structure-Solver/codex-review/P04-CLAUDE-RECOVERY-DIAGNOSTIC-CLOSEOUT-20261009T071842Z-d5f1a3/native-acceptance-20261009T075603Z/`（UTC 07:56:03Z 建立）
- 被验对象：`package/object-RUN`，唯一一次公共链 `b8cc2dc8608a4a889f2dd9d65fa97129`（launch 07:40:59Z，结束 07:42:29Z，89.787 s，`COMPLETED_PHASES`，rc 0，外层 `scientific_verdict=NOT_ASSESSED`）。
- 原始 `native-execution-20261009T073912Z/EXECUTION_REPORT.md`、`RESULT_INDEX.json` 原样保留，本文件引用而不修改它们。
- 本轮边界：没有启动 solver、驱动、原 verifier 或新的 native 命令；没有 apply 补丁；没有 Git 写入（只读 `git status`/`git ls-files`）；没有修改 `DEFECTS.md`、OBJ/RUN/OUTER/source/staging/engineering 或首次冻结账本。
- 本轮新写脚本与结果（均为离线纯解析/数学，只写本目录）：
  - `reconcile_regression.py` → `RECONCILIATION_137.json`
  - `d002_independent_check.py` → `D002_INDEPENDENT_CHECK.json`
  - `production_adoption_compare.py` → `PRODUCTION_ADOPTION_COMPARE.json`
- 配套采纳计划：`PRODUCTION_ADOPTION_PLAN.md`。

**出口：`ISOLATED_NATIVE_INTEGRATION_ACCEPTED_WITH_DECLARED_LIMITS`**（隔离集成验收；生产未采纳，未生产关闭 D001/D002/P04）。

---

## 1. 对账更正：137 项全部执行，3 项是注册的阳性控制

独立核对 `REGRESSION_COST_TABLE.json` 的 137 个 ID 与 14 个 `PHASE_*.json` 的 executed / scientific_pass / contract_probe_recorded / registered_expected_failure（结果见 `RECONCILIATION_137.json`）：

| 项 | 结果 |
|---|---|
| 成本表 ID | 137（唯一 137） |
| executed | 137；缺失 0；额外 0 |
| scientific_pass | 132 |
| contract_probe_recorded | 2：`B-ORD-A-10r`（退出 -11）、`B-ASAN-A-10r`（退出 1，ASan heap-buffer-overflow，位于 `ztrevc_`，`Eigensystems.cpp:2936`） |
| registered_expected_failure | 3：`B-POS-pos_asan`、`B-POS-pos_asan_ubsan`、`B-POS-pos_ubsan` |
| 类别交叉 | 无（pass∩observed、pass∩expected_failure、observed∩expected_failure 均为空） |
| 未分类 | 0 |
| 等式 | 137 = 132 + 2 + 3，成立 |

三项阳性控制的真实证据（stderr 中直接检索注册签名，并与 `pos_*.verify.json` 的 `SIGNATURE_MATCHED` 对照）：

| ID | 退出 | 注册签名 | stderr 含签名 | 判定 |
|---|---|---|---|---|
| B-POS-pos_asan | 1 | `AddressSanitizer: heap-buffer-overflow` | 是 | SIGNATURE_MATCHED |
| B-POS-pos_asan_ubsan | 1 | `AddressSanitizer: heap-buffer-overflow` | 是 | SIGNATURE_MATCHED |
| B-POS-pos_ubsan | 0 | `runtime error: signed integer overflow` | 是 | SIGNATURE_MATCHED |

结论：原 `EXECUTION_REPORT.md` 第 3–4 节“3 项没有状态/未对账”是报告遗漏，不是软件缺陷。这 3 项在 `registered_expected_failure` 中，并且已执行、签名匹配。UBSan 正例退出 0 但输出了注册的 runtime error，按冻结判据（签名匹配）判定通过；本轮不要求所有阳性控制非零，也没有把控制项计入 scientific_pass。

### 334 个调用的非零退出（14 个）

`logs/*.exit` 共 334 个文件，非零 14 个，逐项对照 `REGRESSION_COMMANDS.json` 的注册规则：

| 类别 | 个数 | ID | 注册依据 | 判定 |
|---|---|---|---|---|
| 契约观察 | 2 | B-ORD-A-10r（-11）、B-ASAN-A-10r（1） | expectation = `contract_probe` | CONTRACT_PROBE_RECORDED，不计为通过或失败 |
| ASan 阳性控制 | 2 | B-POS-pos_asan、B-POS-pos_asan_ubsan（均 1） | expectation = `positive_control`，verifier 要求 `SIGNATURE_MATCHED` | 见上表 |
| partial-analysis | 10 | D1–D10:partial-analysis（均 1） | 注册 `expect: {"exit": 1}` | 符合注册（见下） |

`partial-analysis` 的退出 1 的事实：
- 每个 `Dk_partial-analysis.stdout` 都有本波自身的 `Dk PASS ok`（k=1…10）。
- 聚合行为 `PASS k/11`，并且列出的 `FAIL EXIT: exit file missing` 对应的是**尚未生成退出文件的其他波**（例如 D1 的 partial 报告了 D2–D11 缺退出文件）。这是部分分析在完整链完成前执行的结果，不是单个 wave 失败。
- 完整的 `D11:partial-analysis` 为 `PASS 11/11`，退出 0。
- 注册的 `expect` 要求 partial 退出 1，所以 10 个 partial 都符合注册。
- 注意：attempt 的 `expectation` 字段写的是通用值 `must_succeed`，但注册表中 `D*:partial-analysis` 的 `expect` 是 `{"exit": 1}`；以注册表为准，不是缺陷。

本次原始 EXECUTION_REPORT 第 3 节的“partial 的故意非零未逐条核对”现已核对完毕。

---

## 2. 真实 FINAL 与主套件

### 2.1 INTEGRATION_FINAL（内层真实判定）

`evidence/INTEGRATION_FINAL.json`：
- `verdict = INTEGRATION_PASS`；`counts = {checked 25, pass 25, fail 0, not_run 0}`。
- `mock_evidence_nodes = []`；`problems = []`；`failures = []`；`main_items_not_executed_pass = []`。
- 17 个主项全部为 `EXECUTED_PASS`（D1–D11、D-ENTRY 五项、D12-N9-X1E16）。
- `nested_registered_tests = 261`。
- 外层 `NOT_ASSESSED` 只表示外层运行器不做科学判定；整链的科学判定由 INTEGRATION_FINAL 逐项给出，不能把外层标签当成“整链未判断”。

`FINAL_JUDGEMENT.json` 中的 `native_started: false` 以及 `not_run`（C-getwaves 11、C-mapping 1、D-entries 5）是**静态模板字段**，与本次 attempt 及 INTEGRATION_FINAL 的逐项消费相矛盾。以 INTEGRATION_FINAL 的逐项状态为准，不据此新增 native 缺口。其 `rows` 的分类为 48 项 `SCIENTIFIC_PASS` + 2 项 `CONTRACT_PROBE_RECORDED`，`verdict=ALL_REGISTERED_SIGNATURES_MATCHED`，与离线复算一致。

### 2.2 D-entry 与主套件（原始日志与解析摘要）

| 子项 | ran | executed | skip | fail/unexpected | 结果 |
|---|---|---|---|---|---|
| s4test（`D-ENTRY-S4TEST-DISCOVER`） | 257 | 256 | 1 | 0 / 0 | 日志 `OK (skipped=1)`，verdict SIGNATURE_MATCHED |
| Python smoke | 4 | 4 | 0 | 0 | 4 项 OK |
| Lua harness | 3 条记录 | 3 | 0 | 0 | 3/3 checks OK，SIGNATURE_MATCHED |
| Lua negative | 2 脚本 | 2 | 0 | 0 | `lua_regression_negative`、`lua_api_negative` 均 OK |
| test_structures | 模块导入 smoke | — | — | 0 | 声明 8 个符号全部存在，exit 0；这不是 unittest |

唯一 skip：`test_interpolator.InterpolatorTests.test_oom_memory_error`，理由为 `Code Review Only: C-level allocation failure paths in Interpolator_New are verified by code review…`。它在 `optional_skips` 中，理由与代码中的 `unittest.skip` 字面一致，属于既定允许范围（插值器已知 skip）；没有新增测试。

注册的 261 = 257（s4test）+ 4（Python），**不是** 261 项都无 skip。Lua 与 test_structures 不计入这 261。

### 2.3 cc 预算

- 最终统一账本 `evidence/cc_budget.json`：caps compile 48 / link 14 / ar 2；granted compile **41** / link **14** / ar **1**；refused 0 / 0 / 0。
- 拆分（按 token owner）：build 阶段 `build:*` 为 compile 39 / link 12 / ar 1；pyext（`cc:…:pyext:0000/0001`）为 compile 1 / link 1；嵌套 C API（`cc:…:capi:0000`）为 compile 1 / link 1。
- `BUILD_PHASE` 快照 40 / 13 / 1 = 39+pyext 1 / 12+pyext 1 / 1，即快照包含 pyext 但不含嵌套 C API。最终的 +1 compile / +1 link 就是嵌套 C API。
- 873 / 105 为注册的 DUT / ANALYSIS 预留与消耗口径，不是科学通过数，也不是进程数上界；descendant 进程数保持 UNKNOWN。
- python 使用 1，cap 2。少用 1 不是缺失项，没有扩大或凑满配额的必要。

---

## 3. 有限独立原始证据复核

### 3.1 D001：引用已有独立 Airy 结果，并核对其输入

- 已有结果（`codex-review/P04-CODEX-NATIVE-RESULT-REVIEW-20261009/VERIFICATION_SUMMARY.json`，`audit.py` 独立公式计算）：P02-12 max 1.11e-16，LUA-12 max 1.11e-16，EXT-16 max 1.665e-16，STAGE2 max 1.665e-16；全部 106 份 flux，最大误差 **1.6653345369377348e-16**，低于固定阈值 1e-10。
- **本轮没有重算 Airy，也没有创建新参考框架**，只引用上述结果。本轮复核的是这些结果的输入与身份：

| 核对项 | 结果 |
|---|---|
| 四份 manifest 的 raw 行数 | P02-12 12、LUA-12 12、EXT-16 16、STAGE2 66，合计 106 |
| raw 文件 SHA 与 manifest `raw_sha256` | 106/106 一致；`exit` 全部为 0；`case_key` 与 raw 内一致 |
| cases 来源 SHA | `d001_first_matrix.json`（P02/LUA）、`d001_extension_16.json`、`d001_stage2_plan.json` 与 manifest 的 `cases_file_sha256` 全部一致 |
| extension 身份 | `candidate/S4.cpython-314-x86_64-linux-gnu.so` 的 SHA = `c03782c4…5ae`，与 manifest `identity_sha256` 和 raw 内 `extension_sha256` 一致；`EXTENSION_IDENTITY.json` 的 SHA `ee42ffe6…174` 与 freeze 账本一致，`verify` 结果为 FROZEN 且未重写 |
| Lua 宿主身份 | `candidate/build/S4` 的 SHA = `59420cca…596`，与 `LUA_HOST_IDENTITY.json` 与 manifest 一致 |
| manifest 的 `identity` 字段 | 是 identity 文件路径；`identity_sha256` 是被加载的二进制 SHA。这是字段含义，不是不一致 |
| frequency / polarization / angle 来源 | 取自 **raw 中的 case 对象**，不取 model_settings |

model_settings 的核对结果（这是本次检查的关键点）：
- `model_settings.FREQUENCY` 是默认值 0.427。它与 case 的 frequency 不一致的情况：EXT-16 有 9 份，STAGE2 有 48 份（如 STAGE2 的 0.173、0.733 case）。因此 audit 使用 case 的 frequency 是正确的，使用 model_settings 会造成错误参考。
- 角度：P02-12 与 LUA-12 的 case 没有 `incidence_angle_deg` 键，按 0 处理，与 `INCIDENCE_ANGLES=[0,0]` 一致。另有 30° 的 case（EXT-16 1 份，STAGE2 6 份），其 case 字段为 30.0，而 model_settings 仍写着 [0,0]；audit 取的是 case 的 30.0，这是正确的。
- 偏振：取自 case 的 `polarization`，既有 s 也有 p。

**未完成的部分**：候选 run 没有重新做 P02 baseline 反例复现（按要求不替代 baseline 证据，见 PROJECT_ROADMAP.md P02）。

### 3.2 D002：48 个非 probe 记录的独立离线复算（已完成）

脚本 `d002_independent_check.py` 只读：RUN 的 spec、matrix（`cases/d002_matrices/matrix_*.txt`）、raw `out.txt`、attempt 记录、`d002_shim/cases/matrices.json` 中的**冻结解析参考值**，以及 `case_table.TH` 中的阈值（复制，不 import）：eig_rel_tol 1e-10、residual_tol 1e-10、vector_norm_tol 1e-12。它不加载 S4，也不运行任何驱动。

**身份与消费链（48/48 通过）**：
- 二进制 SHA = `BUILDS.json` 的 `binary_sha256` = attempt `meta.json` 的 `binary_sha256` = 实际文件 SHA。
- spec SHA 与 `pin.spec_sha256` 一致；matrix 文件 SHA 与 `pin.matrix_sha256` 一致；raw `out.txt` SHA 与 `output_sha256` 一致；attempt 记录 SHA 与 `attempt.sha256` 一致。
- judge 消费的 `meta.json`：argv[0]、argv[-1]（out 路径）、exit、binary SHA 都与 runner 记录一致。其 argv[1] 指向 attempt 目录内的 spec 副本，该副本的 SHA 与 pin 一致（runner 记录的是 `cases/d002_specs/` 路径，这是两个等价副本，不是冲突）。
- `results/JUDGEMENT.json` 中 50 条 run：48 条 `VALID`，2 条 `CONTRACT_PROBE_RECORDED`，与 FINAL 的分类一致。
- `matrix_*.txt` 与 `matrices.json` 的数值一致（已逐元素比较）。

**分类与判据（48 个非 probe 记录）**：

| 类别（FINAL group） | 记录数 | 判据 | 独立结果 |
|---|---|---|---|
| ASAN，numeric | 17 | info=0；特征值误差；右/左残差；归一化偏差；padding 未改动；query 时 work0=2n | 全部通过 |
| ASAN，helper | 2（H-01、H-08） | 标记矩阵 permutation 与 LAPACK zgebak（job P）参考一致；padding 未改写 | 全部通过 |
| ORDER，numeric | 17 | 同 ASAN numeric | 全部通过 |
| ORDER，helper | 2（H-01、H-08） | 同 ASAN helper | 全部通过 |
| KNOWN_FAIL，numeric | 4（A-34、A-35、A-38、A-41，均 ord） | 同 numeric（n=76 与 n=40） | 全部通过 |
| SEAM | 6（C-01…C-06） | candidate info = 强制值（mode≠0 时为 seam_info，否则 0）；C-03 的 seam_onlyvalues_real_info=0 | 全部通过 |

各项数值（独立计算值，eig 为最优配对的 max，阈值见上）：
- 特征值误差：最大 **6.64e-15**（阈值 1e-10）。
- 右残差：最大 **1.67e-15**；左残差：最大 **8.17e-16**。
- 向量范数偏差：最大 **7.77e-16**（阈值 1e-12）。
- 与 judge 记录值的差：最大 **7.9e-31**，两套计算完全一致。
- 48 条 stderr 全部为空、退出码全部为 0，没有 ASan/UBSan 报告，也没有 N1 文本。

**需要如实披露的覆盖边界**：
1. **helper 的置换是恒等的**：H-01 与 H-08 的 `ilo=1, ihi=2, scale=[1,1,3]`，第 3 行 `k=3=i`，因此 LAPACK zgebak 的结果是恒等置换。它们验证的是“恒等置换不被破坏”，**不验证非恒等置换**。
2. 本次注册的 helper 只有 H-01 与 H-08。H-02…H-07、H-09…H-11 不在本次注册表中（`REGRESSION_COMMANDS.json` 中没有对应条目）。非恒等置换的 API case（如 A-15/16/17/18/19/23/24）也不在本次注册的 48 条之中。因此不能写成“非恒等上下置换已通过原生复验”。
3. A-34/A-35/A-38 属于 `N2`（zlaqr0_，n>75）。judge 将它们标为“受 N2 混杂”，只判内存和访问，但本次独立复算显示它们的数值误差远低于阈值。N2 本身不因此关闭，仍是已披露边界。
4. 2 个 A-10r 观察项：
   - `B-ORD-A-10r`：退出 -11（SIGSEGV），stderr 为空，raw 非空（sha `5c8a9119…`），与 FINAL 的 `output_sha256` 一致。
   - `B-ASAN-A-10r`：退出 1，ASan heap-buffer-overflow 位于 `ztrevc_`（`Eigensystems.cpp:2936`），raw 为空（sha `e3b0c442…`）。
   - 两者都是注册的契约边界探针（rwork 短于文档要求的 2n），只记录，不判为缺陷，也不计为通过。
5. 注册的 seam 构建使用了**另一份源码树** `seam/candidate/S4/RNP/Eigensystems.cpp`，其与 candidate 的唯一差异是把 `zhseqr_` 重命名为 `d002_inner_zhseqr_`，包装与注入位于测试 driver `tools/d002_driver.cpp`（`-DD002_TEST_SEAM`）中。这属于测试装置，不是生产代码修改。
6. ord/asan 构建编译的 `candidate/S4/RNP/Eigensystems.cpp` SHA = `71817d22…353`，与补丁的 `after_sha256` 完全一致。

**D002 没有被生产关闭**：以上是隔离候选在注册用例上的离线复算；KNOWN_FAIL 是签名匹配，不代表所有相关缺陷已在生产关闭。

### 3.3 无法离线复算的具体输入缺失

无。D001 与 D002 所需的输入全部在本地，已逐项核对。

---

## 4. SHIM 首次身份

| 位置 | SHA256 | 字节 | 时间 |
|---|---|---|---|
| producer `B-D002-MAKE-SHIM` 的 `outputs_after[SHIM.json]` | `e265d84f…a605` | 41445 | attempt 记录 |
| PRODUCT_FREEZE 中 SHIM 的首次冻结记录 | `e265d84f…a605` | 41445 | `frozen_utc=2026-10-09T07:41:57Z`，owner `B-D002-MAKE-SHIM` |
| verifier 的 `SHIM_VERIFY.input` | `e265d84f…a605` | 41445 | — |
| 当前 `d002_shim/SHIM.json` | `e265d84f…a605` | 41445 | — |

- `SHIM_VERIFY.json`：`verdict=SHIM_VERIFY_OK`，`input_unchanged=true`，`mode=verify-only`，`meta_records=50`，`problems=[]`。
- verifier 的 `outputs_after` 只有 `SHIM_VERIFY.json`，没有写入 SHIM。
- **PRODUCT_FREEZE 的 402 条记录**：全部存在；SHA 与字节逐条与当前文件一致（0 不符，0 缺失）。该账本的记录中**没有 `mode` 字段**，因此无法做历史 mode 比对，这一点如实保留，不冒称已认证。
- `freeze_products`（`scripts/p04_runner.py:436`）是 **first-write-wins**：已冻结路径若出现不同 SHA 会被拒绝为 `refreeze_rejected`，记录不被覆盖；`last_update_utc` 只是账本最后一次追加写入的时间（07:42:29Z），不是每个产品的首次身份时间。402 条的 `frozen_utc` 范围为 07:41:02Z–07:42:29Z。
- 结论：SHIM 首次身份在 producer 输出、首次冻结、verifier 输入与当前文件四处一致，**不需要**重建或再冻结旧记录。本结论只覆盖本次记录的终态，不排除断电、并发或期间临时写入（不在本轮范围）。

---

## 5. 生产采纳差异（只读，详见 `PRODUCTION_ADOPTION_PLAN.md`）

- 补丁 `package/engineering/PRODUCTION_ENGINEERING.patch` SHA = `1adef26caf8765eb9392091a26548cfce3318e4b9f82f6c1442cba07b621076e`，与 `LANDING_MANIFEST.json` 一致。base = `963ccf1`。
- 102 项变更：产品源码/文档 13 项；测试与工具 89 项（`testing/phase1-d001` 2、`testing/phase1-d002` 80、`testing/s4test` 7）。
- 三方比较（`PRODUCTION_ADOPTION_COMPARE.json`）：
  - 生产仓库中 **102/102 仍是 base 版本**（modify 的 before_sha 一致；add 的路径不存在）。
  - `package/source` 中 102/102 为 after 版本。
  - `object-RUN/candidate` 中 102/102 为 after 版本。
- 因此：**不是只有前面列出的 4 个文件有差异，全部 13 个产品文件都与生产不同**。生产中没有任何一项已采纳。
- 生产仓库中的 `testing/phase1-d001/`（18 个文件）、`testing/phase1-d002/`（24 个文件，其下为 `P03-20261003…` 子目录）、`testing/phase1-prep/`、`testing/s4test/ISSUE_REGISTRY.md` 是未跟踪的已有内容，与补丁路径不同。补丁的 add 路径在生产中均不存在，因此没有同路径冲突；但采纳时这些未跟踪目录需要单独处理，不能被覆盖或误删。

---

## 6. 对既有报告的更正清单

| 原报告表述 | 更正 |
|---|---|
| EXECUTION_REPORT 第 3–4 节：“3 项未对账 / 无状态” | 是注册阳性控制（`registered_expected_failure`），已执行且签名匹配；137 = 132+2+3 |
| EXECUTION_REPORT：“partial 的故意非零未逐条核对” | 已核对：10 个 `Dk_partial` 的 expect=1，原因是全 11 波聚合在部分运行时缺退出文件；D11 为 11/11、退出 0 |
| EXECUTION_REPORT：“外层 NOT_ASSESSED” | 外层不做科学判定；内层 INTEGRATION_FINAL 为 INTEGRATION_PASS 25/25 |
| EXECUTION_REPORT：“PRODUCT_FREEZE 的 07:42:29Z 可能覆盖 SHIM” | `last_update_utc` 是账本最后一次追加；SHIM 首次记录为 07:41:57Z，与四处身份一致 |
| VERIFICATION_SUMMARY：D002 `independent_numeric_recomputation: NOT_PERFORMED` | 本轮已完成 48 个非 probe 记录的独立数值复算，结果见 `D002_INDEPENDENT_CHECK.json` |
| FINAL_JUDGEMENT：`native_started=false`、`not_run` 含 C-getwaves/D-entries | 静态模板字段，与 INTEGRATION_FINAL 的逐项 EXECUTED_PASS 相矛盾；以 INTEGRATION_FINAL 为准 |
| EXECUTION_REPORT 的 python 1 vs cap 2 | 已用 1 个、预算 2 个；少用不是缺失 |

---

## 7. 是否有需要修 solver 代码的具体缺陷

**对本次隔离集成证据：没有发现具体失败。** 逐项复算全部通过，没有触发 `ACCEPTANCE_BLOCKED_BY_NAMED_EVIDENCE` 的条件。

在采纳候选源码前需要处理的、在源码层面确认的问题（这些不是本次运行的失败，已写入采纳计划，本轮未改动）：

1. `S4/seam.h` 是 TEST-ONLY 的头文件，但补丁把它作为**新文件放进生产 `S4/` 目录**；`rcwa.cpp` 通过 `#ifdef S4_TEST_EIGEN_INFO` 引用它。采纳前应移出 `S4/`，或仅保留在测试装置中。
2. GetWaves 公共接口的改动（约 230 行守卫实现、`GetRayleighWaveRows`、错误码 19、doc 变更）在 `ISSUE_REGISTRY.md` 的 D001–D015 中**没有对应条目**。它是公共 API 的行为改变，需要先登记并单独决定是否采纳，不能静默捆绑进 P04。
3. `S4/main_python.c` 的 `errstr[19]` 使用通用 `def` 文本，而 Lua 对 19 有专门文本。**但 Python 绑定目前没有暴露 GetWaves（生产与候选中 `GetWaves` 引用为 0），错误码 19 在 Python 端不可达**。这是表项一致性的小问题，采纳时顺手修正即可，不构成用户可见缺陷。
4. `HAVE_LAPACK` 实数分支（`SolveLayerEigensystem_real` 的 info 传播与早退）在默认 Linux 构建中未定义该宏（只在 `Makefile.Msys2`、`Makefile.old` 中定义），因此该分支仍是 `NATIVE_UNVERIFIED`，与路线图一致。
5. `S4_SolveInParallel` 的改动只删除了未用变量，**仍是静默 no-op**；D012 没有因此关闭。
6. `S4Sim_ConvertUnits` 在生产中只有定义，没有方法表引用，删除它是死代码清理；它不关闭 D008。

---

## 8. 出口与声明的边界

**出口：`ISOLATED_NATIVE_INTEGRATION_ACCEPTED_WITH_DECLARED_LIMITS`**

仍然保留并披露的边界（未扩大为新的无限任务）：
- HAVE_LAPACK 实数分支：NATIVE_UNVERIFIED（默认构建未进入）。
- descendant 进程数：UNKNOWN；873/105 是注册口径，不是进程上界。
- helper 的非恒等置换与非恒等置换的 API case：未在本次注册运行中（见 3.2）。
- N2（zlaqr0_，n>75）：仍为已披露的有限边界；N1 在本次 48 条中未出现。
- T4、89 资产、830/828 披露、`verified_by_script=false` 来源声明：保持。
- D001 只覆盖注册的空气/ε=4/厚 0.25 的有限膜矩阵及其 P02–STAGE2 场景，不是全参数域证明。
- P02 baseline 未在本轮复现。

本轮**没有**关闭 P04、D001、D002；**没有**启动 P05；**没有**生产采纳。下一步是生产采纳的分批准备，见 `PRODUCTION_ADOPTION_PLAN.md`。
