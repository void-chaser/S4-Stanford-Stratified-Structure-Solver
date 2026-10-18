# P05-S5 R3 报告（s5r3）：S5 收口——勘误 ES5-6..8、D016 比较器 v2、make test 四遍与全量 E2E 42 点在 F4 上重跑、就绪审计、签收范围声明草稿

> 轮次：P05-S5 R3。本轮不宣布 P05-S5 或 P05 完成或签收；签收只由用户在对话中给出。
> 修复前证据不得称为修复后验证；本轮在 F4 上的重跑结果称为"S5 收口在 F4 上的回归与前端验证"，范围仅限本轮预注册点。

## 1 门禁

- start 门禁：2026-10-18T09:58:28Z，HEAD=29dfd1c04e18d351…，HEAD:S4=589e15eb11fcb04e…（F4），判定器 sha256=?…（GATE_S5R3_start.txt；FAILS=0；CHECK_CRASHED=0）。
- 起始文件由脚本断言：RULINGS.tsv 148522 B（最大 U371）、registries/s5r2 小表清单 11 项全 OK、p05-s5r2 证据清单 79 项全 OK、D016_VERDICT_S5R2 SUMMARY=MATCH=31 MISMATCH=2 FLAKY=0、PREREG_E2E_R9M3B 42 行且 sha 与记录一致、/tmp 顶层 0 项。
- start 门禁版本演进照实登记：v1 因门禁脚本自身未跟踪而 GIT_STATUS_EMPTY FAIL，v2 因 gate/ 目录 EV_ABSENT FAIL；v3 FAILS=0，v1 保留在 $EV/gate/GATE_S5R3_start.txt_v1。end 门禁正式一次，输出在 $EV/gate/；原文摘要见 P05_S5R3_GATE_APPENDIX.md。

## 2 裁决入账（U372–U377，纯追加）

- RULINGS.tsv 追加 U372–U377 共 6 行，前缀逐字节断言；最大编号 ?。
- 原文逐字见 registries/RULINGS.tsv 与本轮任务书 §1。

## 3 勘误 ES5-6..ES5-8

- ERRATA_S5.txt 纯追加 ES5-6/7/8（前缀 sha 断言）：5110 → 8228 B；最后条目 ES5-8。
- ES5-6：S5R2 D016 比较器缺陷（d016_run_s5r2.py:218-219 把预注册标签 ABSENT 与观测计数 0 直比，导致 PY_STDERR_INFO2/LUA_STDERR_INFO2 判 MISMATCH）；行为事实是 28 个行为点两遍全 MATCH、两个 stderr 计数均为 0；S5R2 试跑门禁把该检查写成 deferred 就判 PASS（shakedown/gate/GATE_S5R2_end.txt:83），所以冻结前未发现。处置：S5R2 判定表与门禁 FAIL 保留为历史；S5R3 用比较器 v2 与新预注册重跑（不是改期望）。
- ES5-7：S5R2 报告 §7 未说明 MISMATCH 原因、未指向 D016_VERDICT_S5R2_ERRATA.txt；§8 表二缺"冻结期比较器缺陷"；ISSUE_REGISTRY 第 48 行与 ROADMAP 第 145 行缺少原因。处置：S5R2 报告不改；按 U376 替换这两行原文（见 §8）。
- ES5-8：D016_VERDICT_S5R2_ERRATA.txt 与 D016_BUILD_S5R2.tsv 未复制进 registries/s5r2/；本轮复制到 registries/s5r3/s5r2_supplement/，sha256 与 p05-s5r2/SHA256SUMS.txt 记录一致：D016_VERDICT_S5R2_ERRATA.txt=OK; D016_BUILD_S5R2.tsv=OK

## 4 D016（比较器 v2、阳性对照、两遍）

- 新预注册 PREREG_D016_S5R3.tsv：数据行 36，状态 INFLUENCED，sha=2f59f40fded874c2…（写入早于首条正式 D016 运行行，由 end 门禁断言）。比较器按预注册列名读取；stderr 类行显式 expected_count=0，规则为"预注册 ABSENT ⇔ 计数 == 0"，不再有标签与数字直比的路径。
- 构建：trees/F4 = 05097a7 全仓导出 + make test shakedown 构建；PYEXT_SHA256=e29fa0a8cf5bfe4f…、LUA_FRONTEND_SHA256=20d43f997f2a1b5b…（D016_BUILD_S5R3.tsv）。
- 正式两遍：判定行 35（33 MATCH + ROOT_CAUSE_RC RECORD）；SUMMARY MATCH=33 MISMATCH=0 FLAKY=0。
- 阳性对照（5 例落盘篡改副本，同一 compare_passes 代码路径）：PASS 5/5。
- 事实摘要：Python 抛 RuntimeError（含 GetPowerFlux），Lua REPL 打印 GetPoyntingFlux 同一文本；两前端 stderr 均无 "Layer eigensystem returned info = 2"；恢复对象与另起进程参考值 rel_err=0。结论措辞：在 F4 上、在该输入下经公共 API 可见失败且恢复正确（不写已修好）。

## 5 E2E（构建、校准对照、两遍、重判）

- 装置按 U373 复制：build/calib/run/judge/frontend 共 7 个脚本 STRICT 复制（calib、run、Python、Lua 批量、Lua REPL 文件逐行 diff 残差为 0；build 仅参考数据换 M3b 值、judge 仅加 shakedown 块，均列为 DECLARED）；make test runner/judge 为 ADAPTED 复制（要求的分段续跑与 4 例阳性对照）。详见 COPY_DIFF_S5R3.txt。
- 构建（E2E_BUILD_S5R3.tsv）：PYEXT=e29fa0a8cf5bfe4f…（与 M3b 对照 DIFFERENT_OUTSIDE_BUILD_ID：树路径 s5r3 比 m3b 长 1 字节使嵌入路径整体移位，未判等价）；LUA_FRONTEND=20d43f997f2a1b5b…（与 M3b 对照 IDENTICAL）；4/4 __wrap 符号定义、0 个未解析原始 FFT 符号。
- 校准（注入无关，gdb）：EVENT 882 行、TARGET 27 行；与 CALIB_E2E_R9M3B.tsv 逐点比较 DIFFS=?（CALIB_DIFF_S5R3.tsv），命中序号与 size 全部一致，未调整 nth。
- 预注册 PREREG_E2E_S5R3.tsv：42 行 = 25 注入点（py 10、lua_batch 11、lua_repl 4）+ 17 无注入对照，行原样来自 M3b，状态 INFLUENCED，sha=2332927e01687e35…。
- 正式两遍（42 点）：CONTROL_OK=17, E2E_OK=25。
- 阳性对照（19 例落盘篡改记录，覆盖 3 前端与 9 类别）：PASS 19/19。
- 独立重判 rejudge_s5r3.py（新实现，不 import 判定脚本；预注册+逐点 JSON 合并）：E2E_DIFFS=?、D016_DIFFS=?、DIFFS=?。

## 6 make test（四遍、判定、对账）

- B 树 37a82e8、F4 树 05097a7（trees/B、trees/F4 由 git archive 导出，不注入）；四段 B:1、F4:1、B:2、F4:2 各一次调用，可续跑。
- 判定：verdict=NO_NEW_FAILURE，unit_count=265；B_failing=none，F4_failing=none，flaky=none，suite_diff=none。
- 与 Ran N 对账 8 段（每树每遍 2 段）：B_p1/test_python_binding units=4 ran=4 OK, B_p1/s4test_unittest units=257 ran=257 OK, F4_p1/test_python_binding units=4 ran=4 OK, F4_p1/s4test_unittest units=257 ran=257 OK, B_p2/test_python_binding units=4 ran=4 OK, B_p2/s4test_unittest units=257 ran=257 OK, F4_p2/test_python_binding units=4 ran=4 OK, F4_p2/s4test_unittest units=257 ran=257 OK。
- 阳性对照（4 例落盘篡改日志：NEW_FAILURE/FLAKY/SUITE_DIFF/RECONCILE_FAIL）：PASS 4/4。

## 7 就绪审计（READINESS_S5R3.tsv，逐条对照"无可做"七条）

- 红点：S4 签收时 26 个唯一 id，逐行见 READINESS_S5R3.tsv（RED_POINT 行）；全部引用已提交的 M3d 台账与修后回归证据。
- OPEN_ITEMS：MET（rows=25 dispositions=OPEN_TRANSFERRED_OUT,RECORD_ONLY_OPEN,REGISTERED_D017,REGISTERED_R-P05-02,REGISTRY_SYNC,TEST_S5R2,TEST_S5R3）。
- PENDING_RUNS：GAP（missing=['REJUDGE_S5R3.tsv'] markers=none）。
- CONSISTENCY：GAP（state_missing=['33', '265', 'NO_NEW_FAILURE']）。
- MAKETEST：MET（verdict=NO_NEW_FAILURE reconcile=8/8 OK）。
- PREREG_MATRIX：MET（d016={'MATCH': '33', 'MISMATCH': '0', 'FLAKY': '0'} e2e_bad=none）。
- E2E_CHAINS：MET（d016_match=33 e2e_ok_by_frontend={'lua_batch': 11, 'lua_repl': 4, 'py': 10}）。
- 汇总：6 个 SUMMARY 项，MET=4，GAP=2；RED_POINT 明细 26 行，MET=26。
- 验收映射：P05_ACCEPTANCE_MAP_S5R3.tsv AC-1..AC-4 全部 MET（AC-4 由 U364 回答，AC-3 按 S5R3 E2E/D016 结果给出最终映射）。

## 8 登记表 diff 摘要

- testing/s4test/ISSUE_REGISTRY.md：24151 → 24402 B；sha256 54e204b57d8c2d81… → a2d113b50554c163…；只改动脚本列出的行（ASSERT_ONLY_LISTED_LINES_CHANGED=PASS）。
- PROJECT_ROADMAP.md：22128 → 22211 B；sha256 8ff6d491e2efd21d… → 5a22f21ea6788f93…；只改动脚本列出的行（ASSERT_ONLY_LISTED_LINES_CHANGED=PASS）。
- 改动行：ISSUE_REGISTRY.md 第 48 行（D016）与第 29 行（D003 记录）、PROJECT_ROADMAP.md 第 51 行（P05）与第 145 行（D016 条目）；unified diff 见 REGISTRY_APPLY_DIFF_S5R3.txt。

## 9 签收草稿摘要

- P05_S5_SIGNOFF_DRAFT.md：S5 范围声明草稿，标明"未签收"，含被测树 F4、S5 收口测试范围（make test、E2E 42 点、D016 点族）、转出项清单（U366–U370、D017、R-P05-01/02/03）、已知限制（NV -10 仅 [源码]、Lua REPL 只覆盖 cf/fft/kt/vl、ES5-6 历史缺陷）；未写签收文件。

## 10 事件两张表

### 10.1 表一：越界写入尝试

| 轮次 | 命令 | 目标 | 是否落盘 |
|---|---|---|---|
| s5r3 | run_code 程序内 fs.writeFile('/tmp_prereg_body_unused', ...)（一条临时代码行，非证据写入） | /tmp（仓库外） | 否：沙箱拒绝 EROFS/denied，未落盘；已在本表登记 |

### 10.2 表二：工具与脚本事件

| # | 事件 | 处理/影响 |
|---|---|---|
| 1 | s5r3_startgate.py v1 的 GIT_STATUS_EMPTY FAIL：门禁脚本自身是未跟踪新文件 | 改为允许本轮新脚本前缀后 v2 通过；v1 保存为 $EV/gate/GATE_S5R3_start.txt_v1 |
| 2 | start gate v2 的 EV_ABSENT_BEFORE_START 把 gate/ 视为先前证据 | 排除 gate/ 后 v3 通过（FAILS=0, CHECK_CRASHED=0） |
| 3 | s5r3_prep.py v1 的 errata 块分组下标写错，ES5-6/7/8 被切错（两次追加均带前缀断言） | 用 p05-s5r2 证据副本（sha c6d2acb7…）重建后追加正确块；S5R2 清单中 ERRATA_S5.txt 旧 sha 记为预期变化（ES5-8 附带说明） |
| 4 | d016_run_s5r3.py shakedown 首跑 KeyError（py_ref 观测键与进程键冲突） | 改名 py_run_* 后 shakedown 得到 MATCH=33 MISMATCH=0 FLAKY=0 |
| 5 | D016 阳性对照案 A 只篡改 pass1，得到 FLAKY 而非预期的 MISMATCH | 改为两遍同时篡改（计数各 1）后 5/5 PASS |
| 6 | make test 阳性对照案 B 的 flip 未命中（状态词在单元下一行） | 改用与案 A 相同的跨行翻转函数后 4/4 PASS |
| 7 | build_e2e_s5r3.py 的参考数据由 M3a 改为 M3b 表（任务书 §5 要求与 E2E_BUILD_R9M3B.tsv 对照） | 在 COPY_DIFF_S5R3.txt 中列为 DECLARED 数据行，未改装置逻辑 |
| 8 | D016 预注册 artifact 行 id（LIBS4A_SHA256）与 D016_BUILD_S5R3.tsv 的列名（LIB_S4_A_SHA256）不同 | 比较器与独立重判都按 id→列名映射读取；期望语义不变 |
| 9 | 框架事件：本会话无 /tmp/dsh-spill-* 落盘记录 | 无 |

## 11 交付物

复制到 checkpoints/p05/registries/s5r3/ 的小表与 s5r2 补充件共 26 项，加 SHA256SUMS.txt 共 27 项（与 SHA256SUMS 的 26 条记录一致）：
1. GATE_S5R3_start.txt
2. PREREG_D016_S5R3.tsv
3. PREREG_D016_S5R3.tsv.sha256.txt
4. PREREG_MAKETEST_S5R3.tsv
5. PREREG_E2E_S5R3.tsv
6. PREREG_E2E_S5R3.tsv.sha256.txt
7. D016_VERDICT_S5R3.tsv
8. D016_BUILD_S5R3.tsv
9. E2E_VERDICT_S5R3.tsv
10. E2E_BUILD_S5R3.tsv
11. CALIB_DIFF_S5R3.tsv
12. MAKETEST_UNITS_S5R3.tsv
13. MAKETEST_VERDICT_S5R3.tsv
14. POSCTRL_D016_S5R3.txt
15. POSCTRL_E2E_S5R3.txt
16. POSCTRL_MAKETEST_S5R3.txt
17. REJUDGE_S5R3.tsv
18. READINESS_S5R3.tsv
19. P05_ACCEPTANCE_MAP_S5R3.tsv
20. REGISTRY_APPLY_DIFF_S5R3.txt
21. REPORT_CHECK_S5R3.txt
22. FROZEN_SCRIPTS_S5R3.tsv
23. COPY_DIFF_S5R3.txt
24. ERRATA_S5.txt
25. s5r2_supplement/D016_VERDICT_S5R2_ERRATA.txt
26. s5r2_supplement/D016_BUILD_S5R2.tsv
27. SHA256SUMS.txt

- 另：end 门禁摘要 GATE_S5R3_end.txt 由 s5r3_appendix.py 在 end 门禁之后追加到 registries/s5r3/（不在上面的编号清单内），因此目录最终为 28 项。

## 附录 A（试跑门禁摘要）

- 试跑输出：$EV/shakedown/gate/GATE_S5R3_end.txt（模拟 commit-i，含 POST_I 块；不纳入 SHA256SUMS）。
- COUNTS	pass=38	fail=40	total=78
- FAILS=40
- FAIL	FROZEN_POST_I_CALL_COUNTS_MATCH	expected=1	actual=0
- 试跑期 end 门禁的 FAIL 项均为试跑期必然（正式结果/提交 (i) 尚不存在），逐项见试跑门禁原文；本轮以 CHECK_CRASHED=0 为通过条件。

## 附录 B（正式 end 门禁原文摘要）

见 P05_S5R3_GATE_APPENDIX.md（由 s5r3_appendix.py 从正式门禁输出按列名解析生成；报告正文不内嵌门禁结果）。

本轮已完成 P05-S5 R3 范围，等待用户审核。

git log -1: 44ddcd1495b6f6a3cee7de6afd68571c8c2252d3 P05-S5 R3 (i): rulings U372..U377, errata ES5-6..ES5-8, D016 comparator-v2 prereg, make-test and E2E harness copies, frozen s5r3 scripts, s5r2 supplement; awaiting user review
git status --short: M PROJECT_ROADMAP.md;  M testing/s4test/ISSUE_REGISTRY.md

### 附录 C（end 门禁之后追加；只追加，不改正文）

end 门禁正式运行一次（输出 $EV/gate/GATE_S5R3_end.txt，冻结期不修脚本、不重跑），78 项断言：PASS=70、FAIL=8、CHECK_CRASHED=0。逐项处置如下（按 §1–§6 冻结期规则照实记录）：

| # | 断言 | 事实 | 分类 |
|---|---|---|---|
| 1 | RULINGS_LINES_5_FIELDS | actual=0：检查器把含 tab 的注释头行（如 Columns/Status 说明行）也按 5 列统计 | 检查器缺陷（RULINGS 正文 5 列由 end 门禁的 RULINGS_MAX_U_377 与 start 前缀断言共同保证） |
| 2 | FROZEN_POST_I_CALL_COUNTS_MATCH | rejudge_s5r3.py mode=formal exp=1 act=0；实际调用 1 次（safe_run.log 有行），但调用命令无 formal 参数，门禁按 mode 子串计数得 0 | 检查器/FROZEN 模式标注缺陷（调用计数其余 33 行全部一致） |
| 3 | MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST | actual=M PROJECT_ROADMAP.md：git status 输出被整体 strip() 后首行丢失前导空格，路径切片错位 | 检查器缺陷（允许清单本身包含 PROJECT_ROADMAP.md） |
| 4 | D016_VERDICT_ROWS_34 | actual=35：检查器未排除表头行 | 检查器缺陷（判定器自身输出 rows=34） |
| 5 | CALIB_DIFF_ZERO | actual=DIFFS=0=：SUMMARY 行的 diff 列不是 SAME 被计入 | 检查器缺陷（CALIB_DIFF_S5R3.tsv 的 TARGET/EVENT 全部 SAME，DIFFS=0） |
| 6 | REJUDGE_DIFFS_ZERO | actual=MISSING：rejudge_s5r3.py 正式调用崩溃（read_tsv 把 SUMMARY 行读入后 KeyError 'verdict'），未产出 REJUDGE_S5R3.tsv。冻结期规则：不修、不重跑、照实记录 | **真实失败（未完成项）** |
| 7 | READINESS_GAP_ZERO | actual=2：PENDING_RUNS（缺 REJUDGE_S5R3.tsv）与 CONSISTENCY（就绪审计在最终 STATE 生成之前运行，STATE 中还没有 33/265/NO_NEW_FAILURE） | 真实 GAP（前者由 #6 引起；后者是审计顺序设计缺陷，GAP 原因已写进 READINESS_S5R3.tsv 的 note 列） |
| 8 | REGISTRIES_SUMS_ALL_OK | actual=9/OK（清单 9 条）：chain copy 在缺失 REJUDGE_S5R3.tsv 时 HARD_STOP，只复制到 POSCTRL 三件；门禁后 s5r3_appendix.py 追加 end 门禁摘要，清单变为 10 条 | 由 #6 级联（未复制的小表见下方交付物说明） |

冻结期事件补录（与对话摘要一致，补 §10.2 表二）：

| # | 事件 | 处理/影响 |
|---|---|---|
| 10 | 正式期 rejudge_s5r3.py 崩溃：KeyError 'verdict'（D016_VERDICT 的 SUMMARY 行被 read_tsv 当作数据行） | 冻结期不修不重跑；无 REJUDGE_S5R3.tsv；end 门禁 #6/#7/#8 因此 FAIL |
| 11 | chain copy 因缺 REJUDGE_S5R3.tsv 触发 HARD_STOP | 未复制 REJUDGE/READINESS/ACCEPTANCE_MAP/REGISTRY_APPLY_DIFF/REPORT_CHECK/COPY_DIFF/ERRATA_S5 共 7 件到 registries/s5r3/；不重跑 |
| 12 | chain signoff 把草稿写到 $EV/ 而非 checkpoints/p05/（输出路径缺陷） | 门禁后以 cp 复制为 checkpoints/p05/P05_S5_SIGNOFF_DRAFT.md，两处 sha256 相同（c08bac3f05fe1c2e…）；未改脚本 |
| 13 | 正式期 /tmp 顶层快照：end 门禁时 count=0、sha=01ba4719…（与 start 相同）；无 /tmp/dsh-spill-* | 无 |

已完成的正式结果（end 门禁 PASS 项，原文）：D016 两遍 SUMMARY MATCH=33 MISMATCH=0 FLAKY=0（34 判定行）；E2E 42 点 CONTROL_OK=17、E2E_OK=25，FLAKY/INVALID/HIT_OFF_TARGET/API_SILENT/RETRY_*/MISSING_RUN 均为 0；make test NO_NEW_FAILURE、unit_count=265、4 遍 × 2 段全部与 Ran N 对账 OK；阳性对照 D016 5/5、E2E 19/19、make test 4/4；校准与 M3b 对照 DIFFS=0；COPY_DIFF strict_unexpected=0；EVIDENCE SHA256SUMS 382 项全部 OK 且覆盖完整；EVENTS 行集合与重算一致；REPORT_CHECK FAILS=0；STATE 2946 B。

未完成项（不得写成已完成）：①独立重判未产出（#6）；②就绪审计 GAP=2（#7）；③registries/s5r3 小表清单只有 10 条（应为 26 条，缺 16 条中 7 件为本次 HARD_STOP 未复制、其余在清单重建时未纳入）；④end 门禁 8 条 FAIL（其中 5 条为检查器缺陷，1 条真实脚本崩溃，2 条为级联/顺序缺陷）。

git log -1（记录提交 (i)）：44ddcd1495b6f6a3cee7de6afd68571c8c2252d3 P05-S5 R3 (i): rulings U372..U377, errata ES5-6..ES5-8, D016 comparator-v2 prereg, make-test and E2E harness copies, frozen s5r3 scripts, s5r2 supplement; awaiting user review

**本轮未完成 P05-S5 R3 范围，等待用户审核。**

> 说明：正文的收尾句由冻结收尾链在收口前生成（当时按计划写"已完成"）；end 门禁之后的事实（独立重判崩溃、就绪审计 GAP=2、registry 清单不完整）表明本轮未完成，**以本附录 C 的最终状态声明为准：未完成。**
