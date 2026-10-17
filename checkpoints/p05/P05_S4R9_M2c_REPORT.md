# P05-S4 R9 M2c 补充报告：M2b 流程纠正与两项裁决落实

> 轮次标识：`r9m2c`（P05-S4 子轮次 R9 的 M2c，非新阶段）  
> 开工基线 HEAD：`42d7d9751ca6506601c47271c46f3b3242ad2453`（R9 M2b 收尾提交）  
> 冻结被测树：F4（提交 `05097a7`，`S4/` 树哈希 `589e15eb11fcb04e031b524f25a443e7921946cf`）  
> 未修复基线树：B（`37a82e8`，`1d738e64…`；仅基线对照，非修复证据）  
> 判定器 sha256：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`  
> 证据目录：`checkpoints/p05/evidence/p05-s4r9/m2c/`  
> 小表提交目录：`checkpoints/p05/registries/s4r9/M2c/`  
> 任务书存档：`checkpoints/p05/briefs/P05_S4R9_BRIEF_M2c.md`  
> 规范约束：遵循 `AGENTS.md` 与本任务书纪律。**不宣布阶段完成，不询问是否签收。禁止 git commit --amend、rebase 及任何改写历史的操作。本报告内不记载收尾提交哈希。**

---

## 1. 门禁核验结果

### 1.1 开工门禁（`GATE_R9M2c_start.txt`）
- **HEAD 校验**：`42d7d9751ca6506601c47271c46f3b3242ad2453`（PASS）；
- **HEAD:S4 校验**：`589e15eb11fcb04e031b524f25a443e7921946cf`（F4 冻结树，PASS）；
- **历史树校验**：F3 `6cff923…`、F2 `e124925…`、B `1d738e6…` 全部一致（PASS）；
- **判定器 sha256**：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`（PASS）；
- **工作区基线**：开工前 `git status --short` 为空；创建任务书与门禁脚本后与 `gate_allow_r9m2c_start.txt` 5 项一致（PASS）；
- **清单比对**：
  * `registries/s3r5/SHA256SUMS.txt`（14 项全部 PASS）；
  * `registries/s4r9/M0/SHA256SUMS.txt`（25 项全部 PASS）；
  * `registries/s4r9/M2/SHA256SUMS.txt`（14 项全部 PASS）；
  * `registries/s4r9/M2b/SHA256SUMS.txt`（13 项全部 PASS）；
- **活文件基线核验**：
  * `STATE.md`：7127 字节，sha256 `929bf727441b1616f305aa127d7c99997273f1612d41c52781f89008f50bfdf3`（PASS）；
  * `RULINGS.tsv`：122611 字节，sha256 `1ebffb14520317619132305baacd87e11a86991f10a9db681346e8e6084075a5`，前 121086 字节 sha256 `f17bd838a699282b7a993f82ee93455aceae06e3ba3bb3d07b5277a5d20e6986`（= ebf3d00 版本），前缀与 5 列格式核验通过（PASS）；
  * `ERRATA_S3R5.txt`：1712 字节，sha256 `a23ff03cd260548ae74205ca27c94d47a8a677d9c47bacfc5be6f5dec3077349`（PASS）；
  * `ERRATA_9.txt`：6153 字节，sha256 `0ed71687335636274e22481ee7934681db042e3ba63e5be278b352caa8ac2bb5`，前 260 字节 sha256 `c381586d31f0d640d5a8daf4c1125d76c67ec68c6c033e10c71730cbc429034c`（= ebf3d00 版本），前缀核验通过（PASS）；
- **FAIL 计数与自检一致性**：
  * 门禁输出文件中 `^FAIL\t` 匹配行数：0；
  * 末行 `FAILS=` 字段值：0；
  * 两者一致性断言：通过，门禁正常退出（exit code 0）。

---

## 2. 裁决与勘误落实

### 2.1 用户裁决追加（U302–U305）
依据任务书 §3 与 §1-8 纪律，通过 `append_rulings_r9m2c.py` 追加至 `checkpoints/p05/registries/RULINGS.tsv`（末尾追加，前缀字节保持不变，5 列格式断言通过）：
- **U302**：R9 M2b 数据采信（HITSEQ、K_INHERIT_R9M2b、SOLN_SUPP_JUDGE_R9M2b），判定不变。G-1 至 G-7 记为 E9-7 至 E9-13 追加至 ERRATA_9.txt；E9-1 中"4 vs 2"由 E9-10 更正，原行不改；M2b 报告不改，由 M2c 补充更正；
- **U303**：K 继承替代证据采信。10 组 NO_SEQ_EVIDENCE_R2 采信 HIT 行等价作为替代证据，范围仅限 k_max=1 的 10 组，要求对应注入点在两遍中均为 NONEMPTY_IDENTICAL；
- **U304**：U301 生效（追加本行，原行不改）。RP-R8-M2c-1/1b 带范围声明关闭。范围：F4 上 S4.cpp Simulation_InitSolution 1760–1774 段分配失败清理；证据为 18 个 SOLN 修后验证点（1763/1764/1765 × closed2d-ng1/fft-ng5/kottke-ng5 × dbg/san/san-AL），rc1=1、重试 call2 与无注入对照相同（I6 两遍 HOLD）、san 报告数为 0 且无崩溃。不覆盖：非 FMM 的 S4_malloc（OUT_OF_SCOPE_D003，转 S5）；Python/Lua 可见性（M3）；B 树行为（B 列非修复证据）；
- **U305**：门禁与活文件纪律自本轮生效：①门禁 FAILS 以输出文件中 `^FAIL\t` 行数为准并自检一致；②已提交门禁脚本与 allow 文件不得修改，需要变化时新建带新轮次编号的文件；③活文件只能由带前缀断言的脚本追加；④门禁发现 FAIL 时先停下写进报告，不得先修复后重跑掩盖。

### 2.2 勘误追加（E9-7 至 E9-13）
依据任务书 §4 S-B 与 §1-8 纪律，通过 `append_errata_r9m2c.py` 追加至 `checkpoints/p05/registries/s4r9/ERRATA_9.txt`（原有 E9-1 至 E9-6 保持不变，前缀字节保持不变）：
- **E9-7（对应 G-1）**：记录提交 fbf3054 中 RULINGS.tsv 截断（-155 行，U144 至 U298 段丢失）；首次 end 门禁已检出三项 FAIL；后续恢复未经 safe_run（21:16:11Z 裸写）；恢复后现行版本（42d7d97）为 310 行、122611 字节，经只读核对前缀等于 ebf3d00 且 5 列格式完备；
- **E9-8（对应 G-2）**：GATE_R9M2b_end.txt 存在 4 行 FAIL 却显示 FAILS=0，原因为 gate_check_r9m2b.py 未以 fails 作退出码且 shell 仅累加进程退出码；全仓 90 份门禁扫描确认仅此一处存在吞 FAIL；
- **E9-9（对应 G-3）**：gate_check_r9m2b.py（21:17:02Z）、gate_r9m2b.sh（21:17:59Z）、gate_allow_r9m2b_end.txt（21:17:59Z）在提交 fbf3054 后被就地修改，随 42d7d97 入库，未在 safe_run.log 与报告中披露；
- **E9-10（对应 G-4）**：更正 E9-1 中"4 vs 2"为两边各 4 次，确认规划者事实有误；全部 73 组原始日志命中数均相等；原脚本缺陷为 min 截断、第 4 次未取 bt 与大小不同 pass；撤回 M2b 报告 §4.3 中"较少 continue""LSAN 提前终止"的推测，归因为原因未查明；
- **E9-11（对应 G-5）**：纠正事件表数字不一致（报告 §7.2 写 54 项，执行总结写 58+1 项，EVENTS 表 62 行，safe_run.log 24 行）；披露遗漏的 copy_registries 与 4 项裸写；
- **E9-12（对应 G-6）**：区分 HIT 等价中 BOTH_EMPTY（178 行）与 NONEMPTY_IDENTICAL（168 行）；确认 10 组 NO_SEQ 对应注入点两遍均为 NONEMPTY_IDENTICAL；
- **E9-13（对应 G-7）**：指出 M2b 报告中违规强化词汇并作修正。

---

## 3. RULINGS 截断与恢复核验

脚本 `rulings_integrity_r9m2c.py` 输出存入 `checkpoints/p05/evidence/p05-s4r9/m2c/RULINGS_INTEGRITY_R9M2c.txt`。

### 3.1 版本数据比对
| 版本 / 提交 | 行数 | 字节数 | sha256 | U 编号数 | 相对 ebf3d00 变动 |
|---|---|---|---|---|---|
| `ebf3d00`（R9 M0+M2 基线） | 307 | 121086 | `f17bd838a699282b7a993f82ee93455aceae06e3ba3bb3d07b5277a5d20e6986` | 301 | 基准 |
| `fbf3054`（R9 M2b 记录提交） | 155 | 52723 | `8f7688b3a0ec5b044dcbc959c4f1c074dfca2c0464203fc4ecec4bd98045c314` | 149 | 删 155 行，增 3 行 |
| `42d7d97`（R9 M2b 收尾提交 / 本轮开工基线） | 310 | 122611 | `1ebffb14520317619132305baacd87e11a86991f10a9db681346e8e6084075a5` | 304 | 增 3 行（U299–U301） |

### 3.2 截断范围与断言
- **删除 U 编号范围**：U144 至 U298，共 155 个裁决项被误删；
- **断言 1（前缀一致）**：现行版本前 121086 字节与 `ebf3d00` 版本一致（PASS）；
- **断言 2（新增内容一致）**：现行版本末尾 U299–U301 三行与 `fbf3054` 版本一致（PASS）；
- **断言 3（编号唯一）**：现行版本 304 个 U 编号无重复（PASS）；
- **断言 4（格式规范）**：现行版本全部数据行均为 5 列制表符分隔（PASS）。

---

## 4. 门禁缺陷与全仓门禁扫描

脚本 `audit_gates_r9m2c.py` 输出存入 `checkpoints/p05/evidence/p05-s4r9/m2c/GATE_AUDIT_R9M2c.tsv`。

### 4.1 缺陷机理分析
1. **Python 进程退出码丢失**：`gate_check_r9m2b.py` 的 `__main__` 仅打印检查结果元组，未调用 `sys.exit(fails)`，因此进程返回码恒为 0；
2. **Shell 累加失效**：`gate_r9m2b.sh` 通过 `PY_FAILS=$?` 累加失败计数，由于 `PY_FAILS` 恒为 0，Python 脚本检测出的 FAIL 行未被记入 shell 的 `FAILS` 变量；
3. **输出行与 FAILS 值矛盾**：`GATE_R9M2b_end.txt` 中第 30、35、36、44 行输出了 FAIL，但末行依然输出 `FAILS=0`。

### 4.2 全仓门禁扫描结果
- **扫描范围**：`checkpoints/p05/registries/` 下全部已跟踪的 `GATE*.txt` 文件，共 90 份；
- **扫描结果**：
  * 无 `FAILS=` 行的旧格式文件：31 份（记为 `NO_FAILS_LINE`）；
  * `FAIL` 行数等于 `FAILS=` 值的规范文件：58 份（记为 `CONSISTENT`）；
  * **"FAIL 行数 > 0 且 FAILS=0" 的吞 FAIL 文件：仅 1 份**，即 `checkpoints/p05/registries/s4r9/M2b/GATE_R9M2b_end.txt`（fail_lines=4, fails_val=0, status=INCONSISTENT）。

---

## 5. 未披露的门禁改动与裸写披露

脚本 `gate_edits_r9m2c.py` 输出存入 `checkpoints/p05/evidence/p05-s4r9/m2c/GATE_EDITS_R9M2b_UNDISCLOSED.txt`。

### 5.1 文件修改时间戳对照
| 文件路径 | 当前 mtime（UTC） | m2b safe_run.log 对应情况 | 属性 |
|---|---|---|---|
| `checkpoints/p05/registries/RULINGS.tsv` | 2026-10-16T21:16:11Z | 无对应 safe_run 条目 | 裸写（静默恢复截断） |
| `testing/d003/stage_s4r9/gate_check_r9m2b.py` | 2026-10-16T21:17:02Z | 无对应 safe_run 条目 | 裸写（增加 end_R2 映射） |
| `testing/d003/stage_s4r9/gate_r9m2b.sh` | 2026-10-16T21:17:59Z | 无对应 safe_run 条目 | 裸写（增加 end_R2/BASE_MODE，改比较基准） |
| `testing/d003/stage_s4r9/gate_allow_r9m2b_end.txt` | 2026-10-16T21:17:59Z | 无对应 safe_run 条目 | 裸写（新增 M testing/d003/stage_s4r9/*） |

### 5.2 统一 Diff 说明
- `gate_allow_r9m2b_end.txt`：新增 ` M testing/d003/stage_s4r9/*`，以放行就地修改的门禁脚本；
- `gate_r9m2b.sh`：增加 `end_R2` 分支将 `BASE_MODE` 映射为 `end`；将 `TRACKED_TESTING_D003_NO_MOD_DEL_SINCE_START` 比较基准从 `HEAD` 改为 `$BASE`；
- `gate_check_r9m2b.py`：在 `run_checks` 开头增加 `mode in ("end", "end_R2")` 模式归一化。

---

## 6. KGRP-071 前提更正与命中数统计

脚本 `kgrp_counts_r9m2c.py` 输出存入 `checkpoints/p05/evidence/p05-s4r9/m2c/KGRP_HITCOUNT_R9_R9M2b.tsv`。

### 6.1 前提更正
- **更正事实**：R9 M2b 任务书 F-1 与勘误 E9-1 中"F3 命中 4 次、F4 命中 2 次"系规划者事实有误；
- **原始数据**：`K_INHERIT_RAW_R9.txt` 第 820–829 行显示两边实际各命中 4 次：
  * F3 命中 4 次：前 3 次为 `Simulation_ComputeLayerModes`，第 4 次为 `arg=22 func=- -:0`；
  * F4 命中 4 次：前 3 次为 `Simulation_ComputeLayerModes`，第 4 次为 `arg=22 func=- -:0`；
- **行号区间**：
  * M0 `K_INHERIT_RAW_R9.txt` 中 KGRP-071 行号区间：第 817–830 行；
  * M2b `K_INHERIT_RAW_R9M2b.txt` 中 KGRP-071 行号区间：第 743–754 行（采集到 K_max+2=3 次截止）；
- **全组命中分布**：
  * R9 M0 原始日志中全部 73 组两边命中数均相等：
    - (0, 0) 共 9 组（CITED 组）；
    - (1, 1) 共 16 组；
    - (2, 2) 共 8 组；
    - (4, 4) 共 40 组；
    - 不等组数：0 组；
  * 原脚本真实缺陷为：取 `min()` 截断、第 4 次命中未取到 bt、大小不同时直接 pass；
  * 撤回 M2b 报告 §4.3 中关于"较少 continue""LSAN 提前终止导致 2 次"的推测，归因为"规划者事实有误，原因未查明"。

---

## 7. HIT 等价口径与 U303 逐组裁决结果

脚本 `hitseq_split_r9m2c.py` 输出存入 `checkpoints/p05/evidence/p05-s4r9/m2c/HITSEQ_SPLIT_R9M2c.tsv` 与 `HITSEQ_SPLIT_SUMMARY_R9M2c.txt`。

### 7.1 HITSEQ 分类汇总（346 行）
- **空串 sha（`e3b0c442…`）**：178 行两边均为全空输出，记为 `BOTH_EMPTY`；
- **非空一致**：168 行两边输出非空且内容相同，记为 `NONEMPTY_IDENTICAL`；
- **不一致（`DIFFERENT`）**：0 行。

### 7.2 U303 替代证据核验（10 组 NO_SEQ）
依据裁决 U303，对 k_max=1 的 10 组 NO_SEQ_EVIDENCE_R2 逐组核验对应注入点在两遍中是否均为 `NONEMPTY_IDENTICAL`：

| 组号 | 对应注入点 | 两遍分类状态 | U303 替代结论 |
|---|---|---|---|
| KGRP-001 | M2-07-INJ-closed1d-ng5-F4 | pass1=NONEMPTY_IDENTICAL, pass2=NONEMPTY_IDENTICAL | SUBSTITUTE_OK |
| KGRP-002 | M2-07-INJ-closed2d-ng5-F4 | pass1=NONEMPTY_IDENTICAL, pass2=NONEMPTY_IDENTICAL | SUBSTITUTE_OK |
| KGRP-003 | M2-07-INJ-experimental-ng5-F4 | pass1=NONEMPTY_IDENTICAL, pass2=NONEMPTY_IDENTICAL | SUBSTITUTE_OK |
| KGRP-004 | M2-07-INJ-fft-ng5-F4 | pass1=NONEMPTY_IDENTICAL, pass2=NONEMPTY_IDENTICAL | SUBSTITUTE_OK |
| KGRP-005 | M2-07-INJ-kottke-ng5-F4 | pass1=NONEMPTY_IDENTICAL, pass2=NONEMPTY_IDENTICAL | SUBSTITUTE_OK |
| KGRP-006 | M2-07-INJ-tensor-ng5-F4 | pass1=NONEMPTY_IDENTICAL, pass2=NONEMPTY_IDENTICAL | SUBSTITUTE_OK |
| KGRP-007 | M2-07-INJ-jones-ng5-F4 | pass1=NONEMPTY_IDENTICAL, pass2=NONEMPTY_IDENTICAL | SUBSTITUTE_OK |
| KGRP-008 | M2-07-INJ-nv-ng5-F4 | pass1=NONEMPTY_IDENTICAL, pass2=NONEMPTY_IDENTICAL | SUBSTITUTE_OK |
| KGRP-009 | M2-07-INJ-vl-ng5-F4 | pass1=NONEMPTY_IDENTICAL, pass2=NONEMPTY_IDENTICAL | SUBSTITUTE_OK |
| KGRP-025 | M2-06-DIAG-01-F4, M2-06-01-F4-C | 点 1 两遍 NONEMPTY_IDENTICAL；点 2 两遍 NONEMPTY_IDENTICAL | SUBSTITUTE_OK |

**U303 判定结果**：10 组全部满足条件，**10/10 全部为 SUBSTITUTE_OK**，无 SUBSTITUTE_NOT_MET 组。

---

## 8. 事件两张表

数字依据 `events_r9m2c.py`（产出 `checkpoints/p05/evidence/p05-s4r9/m2c/EVENTS_R9_ALL_R9M2c.tsv`）。

### 8.1 表一：越界写入尝试表
- **越界尝试数**：0 项（无命令向仓库外部或越界路径写入）。

### 8.2 表二：工具与脚本事件总表
- **事件条目总计**：由 `events_r9m2c.py` 最终运行统计；
- **分轮次分解**：
  * `r9m0` safe_run.log 条目：27 项；
  * `r9m2` safe_run.log 条目：11 项；
  * `r9m2b` safe_run.log 条目：24 项；
  * `r9m2c` safe_run.log 条目：动态提取（详见事件总表）；
  * `git reflog amend` 条目：1 项（ebf3d00）；
  * 裸写（未经 safe_run）条目：4 项（RULINGS.tsv 21:16:11Z、gate_check 21:17:02Z、gate_sh 21:17:59Z、gate_allow 21:17:59Z）；
- **总数一致性断言**：总行数等于四份日志条目数 + 1 + 4。

---

## 9. 需用户裁决事项

- **SUBSTITUTE_NOT_MET 组**：无（10 组 NO_SEQ 全部满足 U303 条件，均为 SUBSTITUTE_OK）；
- **本轮新发现问题**：无。

---

## 10. 结论

本轮已完成 R9 M2c 范围，等待用户审核。  
下一步计划：推进至 P05-S4 R9 M1（在 F4 树上重跑 M1 1302 行并与 F3 冻结事实进行等价比对），随后进行 M3 阶段收口。