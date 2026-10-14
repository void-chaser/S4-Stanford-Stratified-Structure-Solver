# P05-S4 R8 M1a 续3a 报告：完整无注入调用序列映射与新增项映射复核

> 本轮属于 P05-S4 R8 M1a 续3a，不是新阶段；不宣布任何阶段完成或签收，不写签收建议。
> 任务书：`checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3a.md`（按 §0 原文存档）与恢复补充 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3a_RESUME.md`。
> 暂停交接记录：`checkpoints/p05/P05_S4R8_HANDOVER_M1a_CONT3a_PAUSE.md`。
> 本轮范围：(1) 续2c 接受记录及 E8-55 分类更正；(2) F2→F3 无注入调用序列映射；(3) S3R4 新增项 F3 映射复核；(4) 门禁、归档、报告及一次记录提交。
> 未修改 `S4/`；未修改 `testing/d003/` 下任何已提交文件；未做任何失败注入，未运行 M1b/M1c 回归，未生成正式预注册或回归运行器。

## 1. 恢复与门禁核对

### 1.1 开工基线与暂停恢复
- 开工与恢复 HEAD = `331c022c3d9944cff8e7e63e16c24d33253ce847`
- 当前被测树 `HEAD:S4` = `6cff923a02baf19e01966b2339755cbf3a5deeef`（F3，与 S3R4 候选一致）
- 前一冻结树 `a07b5ac:S4` = `e124925f5b242486a913b813fa181664f665b048`（F2）
- 判定器 sha256 = `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`
- 树差异：F2 与 F3 的 S4 差异恰为 4 个文件（S4.cpp, fmm_FFT.cpp, fmm_kottke.cpp, pattern.c）
- 历史装置检查：`git diff --name-only HEAD -- testing/d003` 为空。

### 1.2 开工门禁与恢复门禁
1. **开工门禁 `GATE_R8_M1a4_START.txt`**：
   - 运行时间：2026-10-14T05:32:39Z，运行经 safe_run。
   - 结果：**文件34行，FAILS=0**（证据：`checkpoints/p05/evidence/p05-s4r8/GATE_R8_M1a4_START.txt`）。
   - 对应 s4r7 分类复核：`S4R7_RECHECK_GATE_R8_M1A4_START.tsv`，末行 `fails=0`。
   - /tmp 开工快照：条目数 0，sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。
2. **用户主动暂停**：
   - 因额度原因用户主动暂停本轮，保存现场交接于 `checkpoints/p05/P05_S4R8_HANDOVER_M1a_CONT3a_PAUSE.md`，无后台作业。未执行 end 门禁及提交。
3. **恢复门禁 `GATE_R8_M1a4_RESUME_R2.txt`**：
   - 恢复时 /tmp 快照：2026-10-14T05:45:43Z，条目数 0，sha256 `e3b0c442...`。
   - 初次运行 `GATE_R8_M1a4_RESUME.txt` 因 tail 行数过多误抓历史 ERRATA 条目导致 FAILS=1（门禁自身提取脚本缺陷）；修正为按开工字节数偏移提取后，重跑 `GATE_R8_M1a4_RESUME_R2.txt`，结果：**FAILS=0**（38 行全部 PASS）。
   - 对应 s4r7 分类复核：`S4R7_RECHECK_GATE_R8_M1A4_RESUME_R2.tsv`，末行 `fails=0`。

## 2. 裁决记录与 E8-55 分类更正

1. **裁决追加 U176–U182**：
   - start 门禁通过后，经 `testing/d003/stage_s4r8/append_r8m1a4.sh` 追加至 `checkpoints/p05/registries/RULINGS.tsv`，FAILS=0。
   - 前 66509 字节 sha256 保持不变（`77ca58673d471b8122b7c805cbd77c4aac65923c89c800241118132b426376d5`）；新增 7 行每行恰 5 列（4 个 TAB），状态均为 `生效`。
2. **勘误追加 E8-56 至 E8-62**：
   - E8-56：E8-55 澄清（依据 U177）。排除注释行及明确“不使用”引用，两处有效分类由 BP_LINE 改为 NO。
   - E8-57：替换上一版建议（依据 U181、U182）。G2a/G6 seam hook 仍做无注入计数序列核对，控制行写 N/A。
   - E8-58：实际驱动映射口径（依据 U179）。逐一核对驱动表路径、sha256、库身份及族；不凭 dbg/plain 命名推断。
   - E8-59：完整 seam 覆盖要求（依据 U181、U182）。G2a/G6 的 site/ID 钩子逐一展开。
   - E8-60：续2c 报告记录差异澄清（sh 调用为 03:35:00Z，误用 python 为 03:35:59Z；endB 为独立清单）。
   - E8-61：首次及 _R2 单元与期望草稿失效说明。
   - E8-62：恢复身份门禁 GATE_R8_M1a4_RESUME_R2.txt 通过说明。
3. **U177 有效分类表**：
   - 产物：`checkpoints/p05/evidence/p05-s4r8/USED_IN_M1_CORRECTION_R8_M1a4.tsv`。
   - 统计对比：
     - v3c 历史统计：BP_LINE 4、REGISTRY_ONLY 26、NO 1（保留不改原件，不重跑静态映射）。
     - U177 生效统计：BP_LINE 2、REGISTRY_ONLY 26、NO 3。
     - 两处变更：`S4/fmm/fmm_FFT.cpp:90`（BP_LINE -> NO）与 `S4/fmm/fmm_kottke.cpp:94`（BP_LINE -> NO）。

## 3. 准备缺陷与其修正链（_R1 → _R2 → _R3）

在生成映射需求与单元表时，经历了严格的自审与修正链，所有历史版本全部保留不删：
1. **首次输出（_R1 草稿，25单元）**：
   - 缺陷：误将 S3R4 新增项 22 行合并成 `d003`/F3 的 U0025；未解析驱动真实路径；point_id 关联过于粗糙。
   - 处理：该草稿生成的 `EXPECT_CALLSEQ_R8_M1a4.txt` 已正式标记废弃，不得作为期望使用。
2. **二次输出（_R2 草稿，24单元）**：
   - 缺陷：排除了新增项，但 `driver_identity()` 未实现（返回 None）；单元键缺少驱动路径与哈希；mode 未展开；G2a/G6 未按 site/ID 展开；历史树 F 与运行树 F3 未做推导。
   - 处理：作为中间草稿保留，不直接作为运行依据。
3. **三次输出（_R3 正式版本，198单元/99对）**：
   - 实现完整的 `driver_family_of()` 与 `resolve_driver()`，严密反查 5 份驱动表，逐一校验磁盘文件存在与 sha256；
   - 明确分离 `source_tree`（历史登记原标签）与 `run_tree`（本轮实际运行树 F2/F3）；
   - 完整展开 mode、NG、route、twice_env、argv、规范化环境；
   - 建立 9 个驱动族在 F2 与 F3 的对称配对体系，形成严格对应的 99 对无注入比较单元；
   - 覆盖表不再按 point_id 简单串联，而是按完整语义配置精准关联到唯一单元；
   - 通过全部准备自检，输出正式 `_R3` 版本及冻结期望 `EXPECT_CALLSEQ_R8_M1a4_R3.txt`。

## 4. F2→F3 无注入动态调用序列映射（§5、§6）

### 4.1 gdb 追踪运行（§5）
- 执行脚本：`testing/d003/stage_s4r8/callseq_runner_r8m1a4.py`，调用 `callseq_r8m1a4_gdb.py`（gdb -batch -nx）。
- 干净环境：`env -i PATH="$PATH" LANG=C LC_ALL=C PYTHONDONTWRITEBYTECODE=1` + 必要环境（`FMM_MODE`, `S4FMM_NG`, `S4FMM_TWICE`），无 INJECT/NTH 污染。
- 运行顺序：严格按 pair_id 顺序，F2 先于 F3。
- 运行结果：
  - 198 个单元全部成功执行完毕。
  - 汇总表：`checkpoints/p05/evidence/p05-s4r8/CALLSEQ_RUNS_R8_M1a4_R3.tsv`。
  - 统计：`gdb_rc = 0` 198/198；`inferior_exit = 0` 198/198；`signal = -` 198/198；`trace_error = NONE` 198/198。零错误，零崩溃。

### 4.2 调用序列比较（§6）
- 比对脚本：`testing/d003/stage_s4r8/compare_callseq_r8m1a4.py`。
- 产物：`checkpoints/p05/evidence/p05-s4r8/CALLSEQ_F2_F3_R8_M1a4_R2.tsv`。
- 比较结果（99 对配对单元）：
  - **IDENTICAL: 99**
  - **IDENTICAL_AFTER_RENAME: 0**
  - **DIFFERENT: 0**（实测确为零！）
- 序列完全一致，事件类型、序号、内部 plan malloc 明细、window malloc 明细、seam per-ID 序列全部有序严格吻合。

### 4.3 序列有效性证明（§6）
- 产物：`checkpoints/p05/evidence/p05-s4r8/CALLSEQ_VALIDITY_R8_M1a4_R2.tsv`。
- 结果：99 对单元全部为 **VALID**。
- 证明内容：所有 plan 事件闭合（PLAN_START 与 PLAN_END 成对，嵌套深度平衡）；所有 window 事件闭合（WIN_OPEN 与 WIN_CLOSE 成对）；malloc 明细序号严格连续；exit code 与汇总文件一致。

### 4.4 逐点 K/M 覆盖与可达性检查（§6）
- 产物：
  - 调用上限表：`checkpoints/p05/evidence/p05-s4r8/CALLSEQ_KMAX_R8_M1a4_R2.tsv`
  - 逐点覆盖检查表：`checkpoints/p05/evidence/p05-s4r8/CALLSEQ_POINT_COVERAGE_CHECK_R8_M1a4_R2.tsv`
- 检查对象：全部 1128 个历史覆盖点（M1=108, M2=554, M3=440, CTRL_SEAM=4, ADDITIONS=22）。
- 统计结果：
  - **REACHED: 1026**（所有需要注入的测试点在无注入调用序列中均达到目标 K/M 次数）
  - **N/A (control): 80**（无注入控制行，按规则标记 N/A）
  - **ADDITIONS: 22**（S3R4 新增项，转入 §7 独立复核）
  - **UNKNOWN_REQUEST: 0**
  - **UNEXPECTED_NOT_REACHED: 0**
- 覆盖率 100%，无任何漏查或不可达点。

## 5. S3R4 新增项映射复核（§7）

- 驱动与装置核对：
  - `init-F3`：sha256 `ff66cfc1bf87b6c22d13e32dc6adf3c5e6b090fdcad745bf5248f74dd9510b68`（SAME）
  - `polyinj-F3`：sha256 `419cfb727932cc8d9417fd3a873c578f2f1f597f57e501041d9dd3b221ad30a9`（SAME）
- 执行脚本：`a1map_r8m1a4.sh`（3 组合）与 `b_map_r8m1a4.sh`（6 组合），差异记录于 `RUNNER_DIFF_R8_M1a4.txt`。
- 汇总与验证：`testing/d003/stage_s4r8/summarize_additions_r8m1a4.py`。
- 产物：
  - 9 组合复核结果表：`checkpoints/p05/evidence/p05-s4r8/CALLSEQ_ADDITIONS_R8_M1a4.tsv`
  - 22 行对应表：`checkpoints/p05/evidence/p05-s4r8/ADDITIONS_MAPPING_22_R8_M1a4.tsv`
- 结果：
  - Section A（3 组合）：
    - `closed2d-ng1`: win_open=3, win_malloc=1, outside_malloc=104, K_init=7, K0=6, caller=Simulation_InitSolution, status=UNIQUE -> **MATCH**
    - `fft-ng5`: win_open=3, win_malloc=1, outside_malloc=116, K_init=8, K0=7, caller=Simulation_InitSolution, status=UNIQUE -> **MATCH**
    - `kottke-ng5`: win_open=3, win_malloc=1, outside_malloc=116, K_init=8, K0=7, caller=Simulation_InitSolution, status=UNIQUE -> **MATCH**
  - Section B（6 组合）：
    - `fft-ng1`: Mtot=1, Mfirst=1, n_values=36, RC=0/0, hits=0, poly_bp_hits=1 -> **MATCH**
    - `fft-ng5`: Mtot=64, Mfirst=64, n_values=36, RC=0/0, hits=0, poly_bp_hits=64 -> **MATCH**
    - `fft-ng9`: Mtot=64, Mfirst=64, n_values=36, RC=0/0, hits=0, poly_bp_hits=64 -> **MATCH**
    - `kottke-ng1`: Mtot=64, Mfirst=64, n_values=36, RC=0/0, hits=0, poly_bp_hits=64 -> **MATCH**
    - `kottke-ng5`: Mtot=64, Mfirst=64, n_values=36, RC=0/0, hits=0, poly_bp_hits=64 -> **MATCH**
    - `kottke-ng9`: Mtot=64, Mfirst=64, n_values=36, RC=0/0, hits=0, poly_bp_hits=64 -> **MATCH**
  - **总计：9/9 MATCH，0 MISMATCH**。
  - 声明：9 个映射组合结果已建立与 22 行新增登记项的完整映射对应，不把 9 个无注入映射冒称 22 次注入验证。

## 6. 证据归档与清单管理（§9）

已复制到 `checkpoints/p05/registries/s4r8/M1a/` 的小表清单（共 21 个文件，逐个 cmp 通过，`SHA256SUMS_M1a4.txt` 全部校验 OK）：
1. `GATE_R8_M1a4_START.txt`
2. `S4R7_RECHECK_GATE_R8_M1A4_START.tsv`
3. `GATE_R8_M1a4_RESUME_R2.txt`
4. `S4R7_RECHECK_GATE_R8_M1A4_RESUME_R2.tsv`
5. `APPEND_R8_M1a4.txt`
6. `APPEND_ERRATA_R8_M1a4_R3.txt`
7. `USED_IN_M1_CORRECTION_R8_M1a4.tsv`
8. `SOURCE_HASHES_R8_M1a4_R3.tsv`
9. `COUNTED_FAMILIES_R8_M1a4_R3.tsv`
10. `CALLSEQ_UNITS_R8_M1a4_R3.tsv`
11. `CALLSEQ_POINT_COVERAGE_R8_M1a4_R3.tsv`
12. `EXPECT_CALLSEQ_R8_M1a4_R3.txt`
13. `EXPECT_ADDITIONS_R8_M1a4.txt`
14. `CALLSEQ_RUNS_R8_M1a4_R3.tsv`
15. `CALLSEQ_F2_F3_R8_M1a4_R2.tsv`
16. `CALLSEQ_VALIDITY_R8_M1a4_R2.tsv`
17. `CALLSEQ_KMAX_R8_M1a4_R2.tsv`
18. `CALLSEQ_POINT_COVERAGE_CHECK_R8_M1a4_R2.tsv`
19. `RUNNER_DIFF_R8_M1a4.txt`
20. `CALLSEQ_ADDITIONS_R8_M1a4.tsv`
21. `ADDITIONS_MAPPING_22_R8_M1a4.tsv`

历史清单未修改。

## 7. 违规两张表与事件披露

### 7.1 表一“越界写入尝试”
- 无。所有命令与写入目标均位于 `$EV/`、`$REPO/testing/d003/stage_s4r8/` 或 `$REPO/checkpoints/p05/` 内，无任何越界写入尝试。

### 7.2 表二“工具/脚本事件”
| # | UTC | 事件说明 | 性质 | 是否落盘 | 处理与披露 |
|---|---|---|---|---|---|
| 1 | 约 05:46Z | 恢复门禁 `gate9_resume_r8m1a4.sh` 首次运行 tail 行数过多误抓历史 ERRATA 条目导致 FAILS=1 | 门禁自身提取脚本缺陷 | 否（门禁自检失败） | 修正提取逻辑为按开工字节数偏移提取，重跑 `GATE_R8_M1a4_RESUME_R2.txt`，FAILS=0 |
| 2 | 约 05:58Z | `callseq_runner_r8m1a4.py` 在 U0033 停止，报 `SeamHookBP.__init__() got unexpected keyword argument 'internal'` | 脚本参数签名缺陷 | 否 | 给 `SeamHookBP.__init__` 添加 `**kwargs` 修复，重跑 runner 至 `callseq_r8m1a4_r3`，198 单元全通 |
| 3 | 约 06:05Z | `compare_callseq_r8m1a4.py` 首次逐点检查时，将 request="plan" 的 128 点标记为 `UNKNOWN_REQUEST` | 正则匹配遗漏字面值 "plan" | 否 | 补充 `req == "plan"` 的事实判断逻辑，重跑输出 `_R3`，0 UNKNOWN 全通 |

所有事件均属于运行前的脚本草稿调试，已记录于事故证据并在报告中完整披露，无任何违规落盘。

## 8. 未完成项与待裁决项

- **未完成项**：
  - 续3b 范围：正式预注册表生成、逐组计数、dry-run 和回归运行器编写；
  - 实际失败注入与回归执行（M1b/M1c）。
- **待裁决项**：
  - 无。E8-55 规则已由 U177 正式裁决并更正生效。

## 9. 结论

本轮已完成 R8 M1a 续3a 全部指定范围：
1. 续2c 接受记录及 E8-55 分类更正已完成，U176–U182 与 E8-56–E8-62 已记录生效；
2. F2→F3 无注入动态调用序列映射已完成，198 个单元（99 对）调用序列 100% IDENTICAL，0 DIFFERENT，1026 个注入点全部可达（REACHED），80 个控制点 N/A；
3. S3R4 新增项复核完成，9 个组合全部 MATCH（0 MISMATCH），与 22 行新增项一一映射建立；
4. 小表全部归档复制并通过校验。

本轮已完成 R8 M1a 续3a 范围，等待用户审核。
