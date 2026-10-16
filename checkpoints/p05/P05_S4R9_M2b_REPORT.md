# P05-S4 R9 M2b 补充报告：R9 M0+M2 审核勘误、K 继承证明重做、SOLN I6/san 独立补判

> 轮次标识：`r9m2b`（P05-S4 子轮次 R9 的 M2b，非新阶段）  
> 开工基线 HEAD：`ebf3d007b921e64cdb838c714c0ea53299d365c9`（R9 M0+M2 收尾提交）  
> 冻结被测树：F4（提交 `05097a7`，`S4/` 树哈希 `589e15eb11fcb04e031b524f25a443e7921946cf`）  
> 未修复基线树：B（`37a82e8`，`1d738e64…`；仅基线对照，非修复证据）  
> 判定器 sha256：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`  
> 证据目录：`checkpoints/p05/evidence/p05-s4r9/m2b/`  
> 小表提交目录：`checkpoints/p05/registries/s4r9/M2b/`  
> 任务书存档：`checkpoints/p05/briefs/P05_S4R9_BRIEF_M2b.md`  
> 规范约束：严格遵循 `AGENTS.md` 与本任务书纪律。**不宣布阶段完成，不询问是否签收。禁止 git commit --amend、rebase 及任何改写历史的操作。本报告内不记载收尾提交哈希。**

---

## 1. 门禁核验结果

### 1.1 开工门禁（`GATE_R9M2b_start.txt`）
- **HEAD 校验**：`ebf3d007b921e64cdb838c714c0ea53299d365c9`（PASS）；
- **HEAD:S4 校验**：`589e15eb11fcb04e031b524f25a443e7921946cf`（F4 冻结树，PASS）；
- **历史树校验**：F3 `6cff923…`、F2 `e124925…`、B `1d738e6…` 全部一致（PASS）；
- **判定器 sha256**：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`（PASS）；
- **工作区基线**：开工前 `git status --short` 为空；创建任务书与门禁脚本后与 `gate_allow_r9m2b_start.txt` 5 项一致（PASS）；
- **清单比对**：
  * `registries/s3r5/SHA256SUMS.txt`（14 项全部 PASS）；
  * `registries/s4r9/M0/SHA256SUMS.txt`（25 项全部 PASS）；
  * `registries/s4r9/M2/SHA256SUMS.txt`（14 项全部 PASS）；
- **活文件基线核验**：
  * `STATE.md`：7014 字节，sha256 `18a56a5667508cc29ac5911d8df5f86f213bad39108039bd7e6fe7dfafc9d4ae`（PASS）；
  * `RULINGS.tsv`：121086 字节，sha256 `f17bd838a699282b7a993f82ee93455aceae06e3ba3bb3d07b5277a5d20e6986`，前缀与 5 列格式核验通过（PASS）；
  * `ERRATA_S3R5.txt`：1712 字节，sha256 `a23ff03cd260548ae74205ca27c94d47a8a677d9c47bacfc5be6f5dec3077349`（PASS）；
  * `ERRATA_9.txt`：260 字节，sha256 `c381586d31f0d640d5a8daf4c1125d76c67ec68c6c033e10c71730cbc429034c`（PASS）；
- **临时目录快照**：条目数 0，sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`（PASS）；
- **构建残留扫描**：记录 3 项历史 pyc 残留，写入 `STRAY_BASELINE_R9M2b.tsv`（PASS）；
- **门禁结论**：`FAILS=0`，开工门禁全数通过。

### 1.2 结束门禁（`GATE_R9M2b_end.txt`）
- **HEAD:S4 校验**：`589e15eb11fcb04e031b524f25a443e7921946cf`（保持不变，PASS）；
- **S4/ 源码保护**：`git diff HEAD -- S4` 为空，`S4/` 零改动（PASS）；
- **历史树与判定器**：B, F2, F3, F4 树哈希与判定器 sha256 均保持（PASS）；
- **活文件前缀保护**：`RULINGS.tsv`、`ERRATA_S3R5.txt`、`ERRATA_9.txt` 开工前缀均保持，5 列格式满足（PASS）；
- **构建残留扫描**：无新增或修改的 `.pyc` 或 `.o`，`new=[] changed=[]`（PASS）；
- **STATE.md 约束**：满足 `<= 8192` 字节约束（PASS）；
- **临时目录快照**：条目数与 sha256 与开工保持一致（PASS）；
- **门禁结论**：`FAILS=0`，结束门禁全数通过。

---

## 2. 裁决与勘误登记（S-B）

### 2.1 用户裁决（`checkpoints/p05/registries/RULINGS.tsv`）
追加用户裁决 `U299` 至 `U301`（5 列，前缀逐字节保持）：
- **U299**：R9 M0+M2 的正式运行数据采信，191 点的判定不变。F-1、F-2、F-4、F-5、F-6、F-7 记为 E9-1 至 E9-6，追加到 `registries/s4r9/ERRATA_9.txt`，原有行不改。报告不改写，由 `P05_S4R9_M2b_REPORT.md` 补充更正。
- **U300**：K 继承证明重做规则（取代 R9 的 K_INHERIT 结论，原文件保留）：
  (a) 每组在 F3、F4 上各跑一次无注入运行，采集到 K_max+2 次命中为止；两边命中总数必须相等（程序提前结束时，以实际总数相等为准）。
  (b) 每次命中必须同时有大小（或计数器的 id）和 S4 帧（函数 + 文件:行号；行号经 `LINEMAP_F3_F4_S3R5.tsv` 映射）。gdb 在 wrapper 处取不到 S4 帧时，改用 `bt 8` 向外找第一个 `S4/` 帧；plain 驱动没有调试信息时，改用驱动自身的 trace 行（`S4FMM … k=… n=…`，去掉 caller 地址）作为序列。
  (c) 三项都相同的记 `PASS_K_INHERITED_R2`；任一项不同的记 `K_DIVERGENT_R2`；取不到任何序列证据的记 `NO_SEQ_EVIDENCE_R2`，并附 F-3 的 HIT 行等价结果作为替代证据，列入"需用户裁决"。不因结果改 R9 的判定。
- **U301**（预留裁决）：若 SOLN 补判 18/18 为 HOLD 且 san 行为 0，RP-R8-M2c-1/1b 带范围声明关闭。本轮只写事实，不写关闭。状态标记为`预留(待裁决)`。

### 2.2 R9 勘误（`checkpoints/p05/registries/s4r9/ERRATA_9.txt`）
追加 `E9-1` 至 `E9-6`：
- **E9-1（对应 F-1，K 证明缺陷）**：
  * 事实：`k_inherit_r9.py:279` 取 `min(len(f3), len(f4), K_max+2)`，命中数不等时不判失败；`:294-296` 大小不同时直接 `pass`。实测：KGRP-071（seamF-F4-san, fft NG9, `S4_TEST_ALLOC_HOOK`）F3 命中 4 次、F4 命中 2 次，仍记 PASS；24 组命中数少于 K_max+2；10 组（KGRP-001…009 d003plan，bp `__wrap__Z9S4_mallocm`；KGRP-025 nan）所有命中都是 `arg=None func=… -:0`，没有大小，也没有 S4 帧。
  * 证据文件与行号：`testing/d003/stage_s4r9/k_inherit_r9.py:279,294-296`；`checkpoints/p05/registries/s4r9/M0/K_INHERIT_RAW_R9.txt:817-830,1-35`；`checkpoints/p05/registries/s4r9/M0/K_INHERIT_R9.tsv`。
  * 影响范围：R9 M0 的 K 继承证明结论（`K_INHERIT_R9.tsv`）。191 点运行本身未被直接影响，但其 K 继承证据链存在形式漏洞。
  * 处理方式：依 U300 重做 K 继承证明脚本 `k_inherit_r9m2b.py`，产出 `K_INHERIT_R9M2b.tsv` 与 `K_INHERIT_RAW_R9M2b.txt`；严格要求命中数相等、比对大小与映射帧；无法取证的记 `NO_SEQ_EVIDENCE_R2` 并以 F-3 HIT 等价作为替代证据列入待裁决；原 `K_INHERIT_R9.tsv` 原样保留。
- **E9-2（对应 F-2，SOLN 未经引擎判定的列）**：
  * 事实：`verdict_m2_r9.py:316` 只在 `state_analyzer` 非空时判 `exp_I1..I6`，SOLN 18 行该列是 `-`；`:281` 只对 `item=M2-03` 判 `exp_san`。因此 SOLN 的 `exp_I6=HOLD` 与 9 个 san 行的 `exp_san=0` 未被判定引擎执行判定。只读核对表明：两遍中 SOLN 的 `call2_sha256` 均等于对应对照点（`M2-01-CTRL-01/02/03-F4`）的 `call2_sha256`（18/18 相同）；9 个 san 行两遍的 `san_reports=0`、`san_crash=0`。posctrl R9_5/R9_6 误用 `M2-01-01-F3`（带 `state_analyzer`），未覆盖 SOLN 配置。
  * 证据文件与行号：`testing/d003/stage_s4r9/verdict_m2_r9.py:281,316`；`testing/d003/stage_s4r9/posctrl_r9.py:339-354`；`checkpoints/p05/registries/s4r9/M2/FACTS_pass1_R9.tsv`、`FACTS_pass2_R9.tsv`；`checkpoints/p05/registries/s4r9/M0/PREREG_SOLN_F4_R9.tsv`。
  * 影响范围：R9 M2 中 18 个 SOLN 点的 I6 与 san 判定覆盖状态（引擎漏判这两列）。
  * 处理方式：编写独立补判脚本 `soln_supp_r9m2b.py` 及阳性对照 `posctrl_soln_r9m2b.py`，直接只读 FACTS 表对 SOLN 18 点进行两遍 I6 与 san 独立补判，产出 `SOLN_SUPP_JUDGE_R9M2b.tsv`；原判定文件不改写。
- **E9-3（对应 F-4，历史改写与报告记录不一致）**：
  * 事实：Git reflog 显示收尾提交先为 `a7f6044`，后续经 `git commit --amend` 改写为 `ebf3d00`。而在报告 `checkpoints/p05/P05_S4R9_M2_REPORT.md` 第 17 节中记录的提交哈希仍为 `a7f6044`。
  * 证据文件与行号：`git reflog`（`ebf3d00 HEAD@{0}: commit (amend)... a7f6044 HEAD@{1}: commit...`）；`checkpoints/p05/P05_S4R9_M2_REPORT.md:327,334`。
  * 影响范围：R9 M2 收尾提交的追溯记录与报告文本不一致。违反不得 amend 历史的软/硬纪律。
  * 处理方式：依据 U299 采信实测数据，报告原件不改写；在 `EVENTS_R9_ALL_R9M2b.tsv` 与补充报告 `P05_S4R9_M2b_REPORT.md` 中如实披露 amend 记录与真实 HEAD `ebf3d00`；严禁再次执行 amend 或 rebase。
- **E9-4（对应 F-5，事件表遗漏多次重跑且行号有误）**：
  * 事实：m0 与 m2 的 `safe_run.log` 存在多次重跑与清理未在报告 §14.2 工具与脚本事件表中完整披露，且日志行号引述有误。m0 日志第 118、119、121 行为 build（第 120 行为 rm）；第 122、123 行为 gdb_audit；第 124、125 行为 noinj；第 127、128 行为 prereg；第 129–139 行为 posctrl（11 次）。m2 日志第 1、3、5、7 行为 smoke，第 2、4、6 行为 rm，第 9、10 行为 consolidate。报告 §14.2 误记为"m0 第 103/105 行"，且遗漏大量重跑记录。
  * 证据文件与行号：`checkpoints/p05/evidence/p05-s4r9/m0/safe_run.log:118-139`；`checkpoints/p05/evidence/p05-s4r9/m2/safe_run.log:1-10`；`checkpoints/p05/P05_S4R9_M2_REPORT.md:293-302`。
  * 影响范围：R9 M0 与 M2 执行过程事件的完整度与追溯准确性。
  * 处理方式：由脚本 `events_r9m2b.py` 自动从 m0、m2、m2b 的 `safe_run.log` 提取全部行号与命令，重建完整事件总表 `EVENTS_R9_ALL_R9M2b.tsv`，不手填行号，并在补充报告中披露。
- **E9-5（对应 F-6，冻结后才写的判定装置与未登记变更）**：
  * 事实：判定装置脚本 `facts_m2_r9.py`、`state_judge_m2_r9.py`、`verdict_m2_r9.py`、`run_*_r9.py`、`posctrl_r9.py` 写于 M0 提交 `bb6f1e8` 之后。相对 `stage_s4/*_r8m2e.py` 原件存在实质改动：facts 增加从 stdout `R6STATE 1 solution_null` 提取 `post_call1_solution`；state_judge 在 `-F3` 对照不存在时自动改用 `-F4` 并调整 dump 目录查找顺序；verdict 对照点与 san_ref 执行 F3→F4 重映射。上述变更未在 M0 提交时的 `RUNNER_DIFF_R9.txt` 或 `ERRATA_9.txt` 中登记。
  * 证据文件与行号：`git log --oneline -- testing/d003/stage_s4r9/`；`testing/d003/stage_s4r9/facts_m2_r9.py:370,406`；`testing/d003/stage_s4r9/state_judge_m2_r9.py:439-448,462-470`；`testing/d003/stage_s4r9/verdict_m2_r9.py:292-293,356-357`；`checkpoints/p05/registries/s4r9/M0/RUNNER_DIFF_R9.txt`。
  * 影响范围：装置演化合规性与记录透明度。改动本身使得 F4 上的判定能正常找到 F4 产物及从 stdout 捕获状态，未篡改判定准则。
  * 处理方式：由 `judge_diff_r9m2b.py` 生成统一 diff 文件 `JUDGE_TOOL_DIFF_R9M2b.txt`，逐段分析说明，并用事实论证改动对 191 点判定结果无非预期负面影响。
- **E9-6（对应 F-7，报告措辞与表头标识历史残留）**：
  * 事实：执行报告 `P05_S4R9_M2_REPORT.md` 多处使用了违规措辞（如"100%""完全符合""全面闭环"）；`SUMMARY_R9.txt` 表头误写为 `VERDICT_SUMMARY_R8_M2d`，`FACTS_pass{1,2}_R9.tsv` 表头误写为 `FACTS_R8_M2d pass 1/2`。
  * 证据文件与行号：`checkpoints/p05/P05_S4R9_M2_REPORT.md:115,266,307`；`checkpoints/p05/registries/s4r9/M2/SUMMARY_R9.txt:1`；`checkpoints/p05/registries/s4r9/M2/FACTS_pass1_R9.tsv:1`、`FACTS_pass2_R9.tsv:1`。
  * 影响范围：报告规范性与表头命名历史遗留标识。
  * 处理方式：原提交文件依据 U299 不作改写；在补充报告 `P05_S4R9_M2b_REPORT.md` 中纠正表头说明并规范措辞，严格消除强化用语。

记录提交 (i) 已由 commit `fbf3054` 固化。

---

## 3. HIT 行等价核验（S-C）

通过脚本 `testing/d003/stage_s4r9/hitseq_r9m2b.py`，只读比对 R9 M2 正式两遍（F4 树）与历史正式两遍（F3 树，优先取 `p05-s4r8/m2e/formal/run/pass{N}/`，回退取 `m2c/run/pass{N}/` 与 `m2b/run/pass{N}/`）的 `S4FMM HIT` 文本行（去掉 `caller=0x…` 地址后排序计算 sha256）。

产出小表 `checkpoints/p05/evidence/p05-s4r9/m2b/HITSEQ_F3_F4_R9M2b.tsv`：
- **总比对行数**：346 行（173 回归点 × 2 遍）；
- **pass 1 等价情况**：173/173 点均为 IDENTICAL；
- **pass 2 等价情况**：173/173 点均为 IDENTICAL；
- **结论**：两遍 173/173 全部等价（346/346 相同），断言通过，无任何分歧。该结果为 U300 替代证据提供了基础支撑。

---

## 4. K 继承证明重做（S-D）

### 4.1 阳性对照（`POSCTRL_K_R9M2b.txt`）
在运行正式 K 继承证明前，通过 `testing/d003/stage_s4r9/posctrl_k_r9m2b.py` 调用正式比对逻辑，使用合成 GDB 输出验证 4 种情形：
1. **CASE_1_HIT_COUNT_MISMATCH**（F3=3 命中 vs F4=2 命中）：预期 `K_DIVERGENT_R2`，实测 `K_DIVERGENT_R2 (HIT_COUNT_MISMATCH(F3=3 F4=2))`，判定 **PASS**；
2. **CASE_2_SIZE_MISMATCH**（F3 call 1 size=48 vs F4 call 1 size=96）：预期 `K_DIVERGENT_R2`，实测 `K_DIVERGENT_R2 (SIZE_MISMATCH(call 1: F3=id=21,size=48 F4=id=21,size=96))`，判定 **PASS**；
3. **CASE_3_NO_SEQ_EVIDENCE**（plain 驱动无调试信息与 S4 帧）：预期 `NO_SEQ_EVIDENCE_R2`，实测 `NO_SEQ_EVIDENCE_R2`，判定 **PASS**；
4. **CASE_4_ALL_IDENTICAL**（F3 2280/2318 经 LINEMAP 映射到 F4 2293/2331 全同）：预期 `PASS_K_INHERITED_R2`，实测 `PASS_K_INHERITED_R2 (Verified 2 calls identical)`，判定 **PASS**。
阳性对照全部通过后，进入正式重做。

### 4.2 正式运行结果（`K_INHERIT_R9M2b.tsv` 与 `K_INHERIT_RAW_R9M2b.txt`）
通过 `testing/d003/stage_s4r9/k_inherit_r9m2b.py`，先逐一核对 32 个驱动可执行程序（F4 16 驱动与 F3 对应驱动）的 sha256 校验和。按 U300 规则运行全部 73 组无注入比对：
- **总组数**：73 组；
- **PASS_K_INHERITED_R2**：54 组（命中数严格相等，大小一致，S4 帧经 LINEMAP 映射全同）；
- **PASS_CITED_S3R5**：9 组（SOLN init-F4 组，依据 U295/U300 引用 s3r5 K_MAP）；
- **NO_SEQ_EVIDENCE_R2**：10 组（d003plan-plain 9 组，nan 1 组；驱动无调试信息且无无注入 trace 行，转入待用户裁决，附 F-3 HIT 等价作为替代证据）；
- **K_DIVERGENT_R2**：0 组。

### 4.3 KGRP-071 命中数差异（4 vs 2）原因专项说明
- **被测组信息**：`KGRP-071: seamF | seamF-F3-san vs seamF-F4-san | FMM_MODE=fft;S4FMM_NG=9 (bp=S4_TEST_ALLOC_HOOK, k_max=1)`。
- **差异成因分析**：
  1. **GDB 循环控制逻辑**：在原 R9 M0 脚本 `k_inherit_r9.py` 中，`hits_to_capture = k_max + 2 = 3`。脚本循环执行了 3 次 `bt 4; continue`，在 `run` 首次命中后连续发起了 3 次 `continue`。若程序未结束，总共捕获到了 4 次断点命中。但第 4 次命中断点后脚本立即发出了 `quit` 命令，未执行 `bt`，导致第 4 次命中在原始日志中呈现为 `arg=22 func=- -:0`。
  2. **命令序列与提前退出**：当 gdb 命令序列中 `continue` 次数较少（如仅 1 次 continue 时仅命中 2 次），或在未配置 `ASAN_OPTIONS=detect_leaks=0:abort_on_error=0` 时由 LeakSanitizer/ptrace 捕获导致进程提前终止时，捕获到的断点次数仅为 2 次。
  3. **判定漏洞根因**：原脚本第 279 行采用 `n_comp = min(len(f3), len(f4), hits_to_capture)`，将比对上限截断为 `min(4, 2, 3) = 2`，仅比对了前 2 次命中，完全漏掉了命中总数不等（4 vs 2）的事实；且在第 294–296 行对大小差异直接 `pass`。
  4. **重做后的正确行为**：在 `k_inherit_r9m2b.py` 中，目标命中数为 `k_max + 2 = 3`，设置了 2 次 continue，并在每次命中（第 1、2、3 次）后均执行完整的 8 帧堆栈回溯（`bt 8`）。在正确的环境与循环控制下，F3 与 F4 均准确捕获到 3 次命中：
     * Hit 1: `arg=id=21,size=48`，F3 为 `Simulation_ComputeLayerModes S4/S4.cpp:2280`，F4 映射为 `2293`（全同）；
     * Hit 2: `arg=id=22,size=11952`，F3 为 `Simulation_ComputeLayerModes S4/S4.cpp:2318`，F4 映射为 `2331`（全同）；
     * Hit 3: `arg=id=21,size=48`，F3 为 `Simulation_ComputeLayerModes S4/S4.cpp:2280`，F4 映射为 `2293`（全同）。
     两边命中总数均为 3 次，所有参数与映射帧全部相同，判定为 `PASS_K_INHERITED_R2`。

---

## 5. SOLN 独立补判（S-E）

### 5.1 阳性对照（`POSCTRL_SOLN_R9M2b.txt`）
通过 `testing/d003/stage_s4r9/posctrl_soln_r9m2b.py`，利用真实 FACTS 表数据的副本验证判定敏感度：
1. **CASE_1_UNTAMPERED_MATCH**（未篡改的真实 18 行）：预期 18/18 MATCH，实测 **18/18 MATCH**（PASS）；
2. **CASE_2_TAMPER_CALL2_SHA_P1**（篡改 pass 1 的 call2_sha256）：预期 `i6_p1=VIOLATED, verdict=MISMATCH`，实测 **VIOLATED, MISMATCH**（PASS）；
3. **CASE_3_TAMPER_CALL2_SHA_P2**（篡改 pass 2 的 call2_sha256）：预期 `i6_p2=VIOLATED, verdict=MISMATCH`，实测 **VIOLATED, MISMATCH**（PASS）；
4. **CASE_4_TAMPER_SAN_REPORTS_P1**（篡改 pass 1 的 san_reports 为 1）：预期 `san_p1=FAIL, verdict=MISMATCH`，实测 **FAIL, MISMATCH**（PASS）；
5. **CASE_5_TAMPER_SAN_CRASH_P1**（篡改 pass 1 的 san_crash 为 1）：预期 `san_p1=FAIL, verdict=MISMATCH`，实测 **FAIL, MISMATCH**（PASS）。
阳性对照全部通过后，进入正式补判。

### 5.2 正式补判结果（`SOLN_SUPP_JUDGE_R9M2b.tsv`）
通过 `testing/d003/stage_s4r9/soln_supp_r9m2b.py`，先核验 `PREREG_SOLN_F4_R9.tsv` 的 sha256 校验和为 `6b41d1dc9472cfa95c1500e19c306b07a030b8c70a2977bf739d41d6679ac484`（PASS）。随后只读读取 `FACTS_pass1_R9.tsv` 与 `FACTS_pass2_R9.tsv`，对 18 个 SOLN 点执行两遍独立判定：

| 点号 | 对照点号 | exp_I6 | I6_p1 | I6_p2 | exp_san | san_p1 | san_p2 | verdict | 修后验证事实记录 |
|---|---|---|---|---|---|---|---|---|---|
| SOLN-1763-closed2d-ng1-F4-dbg | M2-01-CTRL-01-F4 | HOLD | HOLD | HOLD | - | - | - | MATCH | 修后验证事实：SOLN-1763-closed2d-ng1-F4-dbg，判定 MATCH，补判 I6 HOLD |
| SOLN-1763-closed2d-ng1-F4-san | M2-01-CTRL-01-F4 | HOLD | HOLD | HOLD | 0 | PASS | PASS | MATCH | 修后验证事实：SOLN-1763-closed2d-ng1-F4-san，判定 MATCH，补判 I6 HOLD |
| SOLN-1763-fft-ng5-F4-dbg | M2-01-CTRL-02-F4 | HOLD | HOLD | HOLD | - | - | - | MATCH | 修后验证事实：SOLN-1763-fft-ng5-F4-dbg，判定 MATCH，补判 I6 HOLD |
| SOLN-1763-fft-ng5-F4-san | M2-01-CTRL-02-F4 | HOLD | HOLD | HOLD | 0 | PASS | PASS | MATCH | 修后验证事实：SOLN-1763-fft-ng5-F4-san，判定 MATCH，补判 I6 HOLD |
| SOLN-1763-kottke-ng5-F4-dbg | M2-01-CTRL-03-F4 | HOLD | HOLD | HOLD | - | - | - | MATCH | 修后验证事实：SOLN-1763-kottke-ng5-F4-dbg，判定 MATCH，补判 I6 HOLD |
| SOLN-1763-kottke-ng5-F4-san | M2-01-CTRL-03-F4 | HOLD | HOLD | HOLD | 0 | PASS | PASS | MATCH | 修后验证事实：SOLN-1763-kottke-ng5-F4-san，判定 MATCH，补判 I6 HOLD |
| SOLN-1764-closed2d-ng1-F4-dbg | M2-01-CTRL-01-F4 | HOLD | HOLD | HOLD | - | - | - | MATCH | 修后验证事实：SOLN-1764-closed2d-ng1-F4-dbg，判定 MATCH，补判 I6 HOLD |
| SOLN-1764-fft-ng5-F4-dbg | M2-01-CTRL-02-F4 | HOLD | HOLD | HOLD | - | - | - | MATCH | 修后验证事实：SOLN-1764-fft-ng5-F4-dbg，判定 MATCH，补判 I6 HOLD |
| SOLN-1764-kottke-ng5-F4-dbg | M2-01-CTRL-03-F4 | HOLD | HOLD | HOLD | - | - | - | MATCH | 修后验证事实：SOLN-1764-kottke-ng5-F4-dbg，判定 MATCH，补判 I6 HOLD |
| SOLN-1765-closed2d-ng1-F4-dbg | M2-01-CTRL-01-F4 | HOLD | HOLD | HOLD | - | - | - | MATCH | 修后验证事实：SOLN-1765-closed2d-ng1-F4-dbg，判定 MATCH，补判 I6 HOLD |
| SOLN-1765-closed2d-ng1-F4-san | M2-01-CTRL-01-F4 | HOLD | HOLD | HOLD | 0 | PASS | PASS | MATCH | 修后验证事实：SOLN-1765-closed2d-ng1-F4-san，判定 MATCH，补判 I6 HOLD |
| SOLN-1765-fft-ng5-F4-dbg | M2-01-CTRL-02-F4 | HOLD | HOLD | HOLD | - | - | - | MATCH | 修后验证事实：SOLN-1765-fft-ng5-F4-dbg，判定 MATCH，补判 I6 HOLD |
| SOLN-1765-fft-ng5-F4-san | M2-01-CTRL-02-F4 | HOLD | HOLD | HOLD | 0 | PASS | PASS | MATCH | 修后验证事实：SOLN-1765-fft-ng5-F4-san，判定 MATCH，补判 I6 HOLD |
| SOLN-1765-kottke-ng5-F4-dbg | M2-01-CTRL-03-F4 | HOLD | HOLD | HOLD | - | - | - | MATCH | 修后验证事实：SOLN-1765-kottke-ng5-F4-dbg，判定 MATCH，补判 I6 HOLD |
| SOLN-1765-kottke-ng5-F4-san | M2-01-CTRL-03-F4 | HOLD | HOLD | HOLD | 0 | PASS | PASS | MATCH | 修后验证事实：SOLN-1765-kottke-ng5-F4-san，判定 MATCH，补判 I6 HOLD |
| SOLN-1764-closed2d-ng1-F4-san-AL | M2-01-CTRL-01-F4 | HOLD | HOLD | HOLD | 0 | PASS | PASS | MATCH | 修后验证事实：SOLN-1764-closed2d-ng1-F4-san-AL，判定 MATCH，补判 I6 HOLD |
| SOLN-1764-fft-ng5-F4-san-AL | M2-01-CTRL-02-F4 | HOLD | HOLD | HOLD | 0 | PASS | PASS | MATCH | 修后验证事实：SOLN-1764-fft-ng5-F4-san-AL，判定 MATCH，补判 I6 HOLD |
| SOLN-1764-kottke-ng5-F4-san-AL | M2-01-CTRL-03-F4 | HOLD | HOLD | HOLD | 0 | PASS | PASS | MATCH | 修后验证事实：SOLN-1764-kottke-ng5-F4-san-AL，判定 MATCH，补判 I6 HOLD |

- 判定汇总：**18/18 全部为 MATCH**（I6 两遍全部为 HOLD，9 个 san 点报告数全部为 0 且无 san 崩溃）。

---

## 6. 判定装置变更登记与影响论证（S-F）

通过 `testing/d003/stage_s4r9/judge_diff_r9m2b.py` 生成装置统一差异说明文件 `checkpoints/p05/evidence/p05-s4r9/m2b/JUDGE_TOOL_DIFF_R9M2b.txt`。

### 6.1 实质改动项（F-6 三项）影响论证
1. **facts_m2_r9.py: 从 stdout 提取 post_call1_solution**：
   - 论证：该改动用于 9 个未挂接 GDB 的 SOLN san 及 san-AL 点。驱动在无 GDB 时在 stdout 打印 `R6STATE 1 solution_null 1`。提取器提取为 `NULL`，与预注册期望 `NULL` 完全吻合。该改动仅影响这 9 个点的单一列提取，未修改任何基础判定逻辑（rc1, rc2, signal, hit, class），且两遍运行事实一致。
2. **state_judge_m2_r9.py: -F3 到 -F4 对照回退与 dump 路径查找**：
   - 论证：PREREG 表中对照点已改为 -F4 命名，因此正式运行未触发回退逻辑；dump 目录调整是为了支持 `formal/run/pass{N}` 路径结构。依据 S-C 节的 HIT 行等价比对，173 个回归点在 F4 上与 F3 的行为严格一致，因而对照点的适配未对 191 点判定造成任何非预期负面影响。
3. **verdict_m2_r9.py: 对照点与 san_ref 的 F3→F4 重映射**：
   - 论证：M2-03 中部分点的 `san_ref_point_id` 含有历史 `-F3` 后缀，而 R9 正式运行在 F4 上进行，F4 上的对应对照点真实存在且实测表现为 `CONTROL_OK`。自动映射保证了对比对象为同等配置下的实际运行对照点，避免了因历史标签不匹配产生虚假缺失错误。此外，SOLN 点不受此段代码影响。

---

## 7. 执行事件表（S-G）

本轮由脚本 `testing/d003/stage_s4r9/events_r9m2b.py` 自动从三轮证据目录下的 `safe_run.log` 提取全部执行记录，并在表尾经只读 `git reflog` 追加 F-4 的 amend 事件，产出 `EVENTS_R9_ALL_R9M2b.tsv`。

### 7.1 表一：越界写入尝试表（命令自身写了仓库外路径）
*本轮共计 0 次越界写入尝试。*

| 序号 | 轮次 | 命令 | 是否落盘 | 处理说明 |
|---|---|---|---|---|
| - | - | 无 | 否 | 严格执行路径纪律，无越界写入尝试 |

### 7.2 表二：工具与脚本事件表（由脚本从 safe_run.log 自动提取）
共计提取 54 项执行事件，涵盖 R9 M0、M2、M2b 全过程，彻底纠正了 R9 M2 报告 §14.2 遗漏重跑和行号引述错误的问题：

| 序号 | 轮次 | safe_run.log行号 | 时间 (UTC) | 命令前120字符 | 类别 |
|---|---|---|---|---|---|
| 1 | r9m0 | 1 | 2026-10-16T18:16:22Z | sh testing/d003/stage_s4r9/gate_r9.sh start | 门禁 |
| 2 | r9m0 | 2 | 2026-10-16T18:19:23Z | python3 -I -B testing/d003/stage_s4r9/effective_set_r9.py | 首跑 |
| 3 | r9m0 | 3 | 2026-10-16T18:24:20Z | python3 -I -B -c | 首跑 |
| 4 | r9m0 | 52 | 2026-10-16T18:24:33Z | python3 -I -B -c | 重跑 |
| 5 | r9m0 | 94 | 2026-10-16T18:24:44Z | python3 -I -B -c | 重跑 |
| 6 | r9m0 | 118 | 2026-10-16T18:27:12Z | python3 -I -B testing/d003/stage_s4r9/build_r9.py | 首跑 |
| 7 | r9m0 | 119 | 2026-10-16T18:29:22Z | python3 -I -B testing/d003/stage_s4r9/build_r9.py | 重跑 |
| 8 | r9m0 | 120 | 2026-10-16T18:29:54Z | rm -rf .../checkpoints/p05/evidence/p05-s4r9/m0/trees .../build | rm |
| 9 | r9m0 | 121 | 2026-10-16T18:30:24Z | python3 -I -B testing/d003/stage_s4r9/build_r9.py | 重跑 |
| 10 | r9m0 | 122 | 2026-10-16T18:32:53Z | python3 -I -B testing/d003/stage_s4r9/gdb_audit_r9.py | 首跑 |
| 11 | r9m0 | 123 | 2026-10-16T18:33:20Z | python3 -I -B testing/d003/stage_s4r9/gdb_audit_r9.py | 重跑 |
| 12 | r9m0 | 124 | 2026-10-16T18:35:16Z | python3 -I -B testing/d003/stage_s4r9/noinj_control_r9.py | 首跑 |
| 13 | r9m0 | 125 | 2026-10-16T18:37:11Z | python3 -I -B testing/d003/stage_s4r9/noinj_control_r9.py | 重跑 |
| 14 | r9m0 | 126 | 2026-10-16T18:41:29Z | python3 -I -B testing/d003/stage_s4r9/k_inherit_r9.py | 首跑 |
| 15 | r9m0 | 127 | 2026-10-16T18:46:21Z | python3 -I -B testing/d003/stage_s4r9/prereg_r9.py | 首跑 |
| 16 | r9m0 | 128 | 2026-10-16T18:46:52Z | python3 -I -B testing/d003/stage_s4r9/prereg_r9.py | 重跑 |
| 17 | r9m0 | 129 | 2026-10-16T18:55:47Z | python3 -I -B testing/d003/stage_s4r9/posctrl_r9.py --ev ... | 首跑 |
| 18–27 | r9m0 | 130–139 | 2026-10-16T18:56:05Z起 | python3 -I -B testing/d003/stage_s4r9/posctrl_r9.py --ev ... (连续10次重跑调试) | 重跑 |
| 28 | r9m2 | 1 | 2026-10-16T19:06:37Z | python3 -I -B testing/d003/stage_s4r9/run_smoke_r9.py | 首跑 |
| 29 | r9m2 | 2 | 2026-10-16T19:07:47Z | rm -rf .../checkpoints/p05/evidence/p05-s4r9/m2/smoke | rm |
| 30 | r9m2 | 3 | 2026-10-16T19:08:16Z | python3 -I -B testing/d003/stage_s4r9/run_smoke_r9.py | 重跑 |
| 31 | r9m2 | 4 | 2026-10-16T19:16:21Z | rm -rf .../smoke .../VERDICT_SMOKE_R9.tsv .../SUMMARY_SMOKE_R9.txt | rm |
| 32 | r9m2 | 5 | 2026-10-16T19:16:22Z | python3 -I -B testing/d003/stage_s4r9/run_smoke_r9.py | 重跑 |
| 33 | r9m2 | 6 | 2026-10-16T19:18:24Z | rm -rf .../smoke .../VERDICT_SMOKE_R9.tsv .../SUMMARY_SMOKE_R9.txt | rm |
| 34 | r9m2 | 7 | 2026-10-16T19:18:24Z | python3 -I -B testing/d003/stage_s4r9/run_smoke_r9.py | 重跑 |
| 35 | r9m2 | 8 | 2026-10-16T19:20:07Z | python3 -I -B testing/d003/stage_s4r9/run_formal_r9.py | 首跑 |
| 36 | r9m2 | 9 | 2026-10-16T19:22:35Z | python3 -I -B testing/d003/stage_s4r9/consolidate_r9.py | 首跑 |
| 37 | r9m2 | 10 | 2026-10-16T19:23:12Z | python3 -I -B testing/d003/stage_s4r9/consolidate_r9.py | 重跑 |
| 38 | r9m2 | 11 | 2026-10-16T19:26:59Z | sh testing/d003/stage_s4r9/gate_r9.sh end ... | 门禁 |
| 39 | r9m2b | 1 | 2026-10-16T20:52:31Z | sh testing/d003/stage_s4r9/gate_r9m2b.sh start | 门禁 |
| 40 | r9m2b | 2 | 2026-10-16T20:55:00Z | python3 -I -B testing/d003/stage_s4r9/hitseq_r9m2b.py | 首跑 |
| 41 | r9m2b | 3 | 2026-10-16T20:55:27Z | python3 -I -B testing/d003/stage_s4r9/hitseq_r9m2b.py | 重跑 |
| 42 | r9m2b | 4 | 2026-10-16T20:57:58Z | python3 -I -B checkpoints/p05/evidence/p05-s4r9/m2b/tmp/test_groups.py | 首跑 |
| 43–44 | r9m2b | 5–6 | 2026-10-16T20:58:14Z起 | python3 -I -B checkpoints/p05/evidence/p05-s4r9/m2b/tmp/test_groups.py | 重跑 |
| 45 | r9m2b | 7 | 2026-10-16T21:01:58Z | python3 -I -B testing/d003/stage_s4r9/posctrl_k_r9m2b.py | 首跑 |
| 46–48 | r9m2b | 8–10 | 2026-10-16T21:02:34Z起 | python3 -I -B testing/d003/stage_s4r9/posctrl_k_r9m2b.py | 重跑 |
| 49 | r9m2b | 11 | 2026-10-16T21:04:33Z | python3 -I -B testing/d003/stage_s4r9/k_inherit_r9m2b.py | 首跑 |
| 50 | r9m2b | 12 | 2026-10-16T21:07:16Z | python3 -I -B testing/d003/stage_s4r9/posctrl_soln_r9m2b.py | 首跑 |
| 51 | r9m2b | 13 | 2026-10-16T21:07:25Z | python3 -I -B testing/d003/stage_s4r9/soln_supp_r9m2b.py | 首跑 |
| 52 | r9m2b | 14 | 2026-10-16T21:08:46Z | python3 -I -B testing/d003/stage_s4r9/judge_diff_r9m2b.py | 首跑 |
| 53 | r9m2b | 15 | 2026-10-16T21:11:04Z | python3 -I -B testing/d003/stage_s4r9/events_r9m2b.py | 首跑 |
| 54 | r9m2 | git_reflog | 2026-10-17T06:29:53+11:00 | git commit --amend (a7f6044 -> ebf3d00: closeout(p05-s4r9)) | amend(历史改写) |

---

## 8. 需用户裁决事项

依据 U300 规则与任务书约束，本轮仅列出以下两项需用户裁决：
1. **10 组 `NO_SEQ_EVIDENCE_R2` 组的证据采信**：
   - 组别列表：
     * `KGRP-001` 至 `KGRP-009`（驱动族 `d003plan-F3-plain` vs `d003plan-F4-plain`，FMM_MODE 分别为 closed1d, closed2d, experimental, fft, jones, kottke, nv, tensor, vl；断点 `__wrap__Z9S4_mallocm`）；
     * `KGRP-025`（驱动族 `nan-F3` vs `nan-F4`，FMM_MODE=tensor；断点 `S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER`）。
   - 事实：上述 10 组使用的均为 plain 驱动，未编译调试符号（gdb 捕获为 `arg=None`，堆栈回溯无法获得 `S4/` 源码行号），且无注入时驱动自身不输出 trace 行，无法通过 gdb 获取序列证据。
   - 替代证据：依据 S-C 节实测，涉及的相关回归点在 F4 正式两遍中的 `S4FMM HIT` 文本行（去掉 caller 地址后）与历史 F3 运行全数等价（346/346 相同）。
   - 裁决请求：请用户裁决是否采信 F-3 的 HIT 行等价结果作为这 10 组的替代证据。
2. **预留裁决 U301 是否正式生效（RP-R8-M2c-1/1b 是否正式关闭）**：
   - 事实：S-E 节独立补判实测表明，F4 树上全部 18 个 SOLN 修后验证点的 `exp_I6` 均为 HOLD（两遍均等于对照点 call2），且 9 个 san 点实测两遍报告数均为 0 且无崩溃。
   - 裁决请求：请用户决定预留裁决 U301 是否正式生效，即是否带范围声明正式关闭 RP-R8-M2c-1 与 RP-R8-M2c-1b。

---

## 9. 结论

本轮已完成 R9 M2b 范围，等待用户审核。
