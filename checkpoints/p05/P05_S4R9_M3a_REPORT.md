# P05-S4 R9 M3a 报告（轮次标识 r9m3a）——M1R4 勘误收口 + make test 主套件回归 + Python/Lua E2E 装置与预注册（不运行 E2E）

> 规则依据仓库根 AGENTS.md 与本轮任务书（`checkpoints/p05/briefs/P05_S4R9_BRIEF_M3a.md`）。本轮不运行任何真实 E2E 注入点，不改 S4/、判定器与历史装置，不在仓库根目录执行 make。

## 1. 门禁

开工门禁（§0）逐项核对，全部一致：

| 项 | 值 |
|---|---|
| HEAD | `2f86aa11c7ee1bb16f663abf03ddbf04674a6912` |
| `HEAD:S4` | `589e15eb11fcb04e031b524f25a443e7921946cf`（F4） |
| 判定器 sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` |
| git status --short（开工时） | 空 |
| `/tmp` 顶层 | 0 项，sha256 `e3b0c442…b855` |
| RULINGS.tsv | 134794 字节，sha `8b3d0e31…8ae2`，最大 U327 |
| ERRATA_9.txt | 30931 字节，sha `49add16f…f5748`，最后 E9-34 |
| registries/s4r9/M1R4/SHA256SUMS.txt | sha `57d72574…e5d75`，11 项全部 OK |
| 历史清单 | s3r5 14 / M0 25 / M2 14 / M2b 13 / M2c 11 / M1 28 / M1R2 33 / M1R3 26 项，全部 OK（项数由脚本数出） |

正式 start 门禁：`gate_r9m3a_v2.sh start` → `GATE_R9M3A_start.txt`，43 项断言，FAILS=0（试跑版 `GATE_R9M3A_start_SHAKEDOWN3.txt` 同为 FAILS=0；第一版 `gate_check_r9m3a.py` 在导入期因 `REPO` 未定义崩溃，见 §9 表二）。

## 2. J-1..J-6 复核（AUDIT_R9M1R4_R9M3A_v3.tsv，行号由脚本从原文件算出）

| 项 | 复核结论 | 脚本算出的关键事实 |
|---|---|---|
| J-1 | **属实** | `recert_r9m1r4_v2.py:374` 常量 `sha256(b"tampered_fact")`、`:380-382` 用 `158-1` 与 `158` 比较（两项恒真）；case1 在 `:360` 只改内存字典；`m1r4/shakedown/posctrl` 不存在 |
| J-2 | **属实** | `recert_r9m1r4_v2.py` 的 `target_scripts` 只有 5 项；`FROZEN_SCRIPTS_R9M1R3.tsv` 按脚本计 14 项；m1r3 日志中 events 命中物理行 `158,160`（2 次）、report_check 命中 `155,156,157`（3 次），其余各 1 次 |
| J-3 | **属实** | m1r3 safe_run.log 中 `gate_r9m1r3_v4.sh start _v5` 的物理行号是 **94**（第 82 行是 heredoc 内容）；`AUDIT_R9M1R3_R9M1R4.tsv` 的 H-5 行确实写“物理82” |
| J-4 | **属实** | `786b150` 与 `2f86aa1` 两版的 `UNLOGGED_WRITES_R9M1R3.tsv` 只在第 6、7 行（RULINGS.tsv、ERRATA_9.txt）不同，mtime 03:44:43Z → 05:23:53Z；m1r4 日志第 14、15 行的 append 正是 05:23:53Z；`gate_check_r9m1r4_v3.py` 的 `check_committed_i` diff 范围不含 registries |
| J-5 | **属实** | end 门禁 3 条 FAIL，其中 `POST_I_CALL_COUNT_FINALIZE_EQ_1 expected=1 actual=0`；m1r4 日志中 `gate_r9m1r4_v3.sh end` 出现在 `29`（试跑）、`35`、`58`（正式），首个锚点=29；shakedown 两次 end 试跑均 FAIL `COMMIT_I_PRESENT`；EVENTS 54 行、最大 log_line=56，sha_sums 在 57、正式门禁在 58 |
| J-6 | **属实** | `report_check_r9m1r4.py:13` 的禁用词表包含该四个字的用语，报告正文只用否定式提到它（L3/L211/L212/L225）；STATE 8480 字节 > 8192；报告 §9 写“无”而附录 A.3 有 4 项；§10.1 列 13 项而 registries 只有 11 项；§1 称 41 项 PASS 且未提初版 start 门禁 `FAILS=1` |
| J-7（参考） | **属实** | 两遍 FORMAL_FACTS 各 651 行、键唯一、12 个事实字段 0 处不同；VERDICT 626/22/3 |

## 3. 裁决与勘误

- STATE 压缩：8480 → 5062 字节（≤ 8192，按 U332 项四执行；end 门禁断言 STATE_BYTES_LE_8192）。

- 裁决追加：`append_rulings_r9m3a.py` 以“旧文件 + 新行”方式写入 U328–U333（5 列，前缀断言通过；134794 → 136951 字节，sha `8b3d0e31…` → `579b73c9…`）。
- 本轮自身勘误：E9-45 登记本轮多条含写入命令未经过 safe_run（详见 §9.2 第 9 行与 §10 第 4 项）；ERRATA_9 现 38912 字节，最后一条 E9-45，共 45 条（原 34 条 + 本轮 11 条）。
- 勘误追加：`append_errata_r9m3a.py` 追加 E9-35–E9-44（十个条目覆盖 J-1..J-6 及其子项，每条都带脚本算出的证据行号）；随后 `fix_errata_r9m3a.py` 更正 E9-36 证据行号中的一处笔误（`…L160,L169` → `…L160`；ERRATA_9 现 38065 字节，sha `8d54e8af…`，前 30931 字节 sha 仍等于开工基线）。

## 4. 试跑期摘要（全部经 safe_run，输出在 `$EV/shakedown/`）

| 序号 | 目录 | 做了什么 | 结果 |
|---|---|---|---|
| 1 | `shakedown/1/` | F4 导出树上跑一次完整 `make -C trees/F4 test PYTHON=python3`，用于调好解析脚本 | `make_rc=0`；260 个 `... ok` 单元；该次**不计正式结果** |
| 2 | `shakedown/2/` | `judge_maketest_r9m3a_v3.py posctrl` 用合成日志做阳性对照 | NEW_FAILURE、FLAKY 两个期望都命中，OVERALL PASS |
| 3 | `shakedown/3/` | `events_r9m3a.py` 试跑 | 76 行事件（含本行之前全部物理行） |
| e2e_smoke2 | `shakedown/e2e_smoke2/` | E2E 无注入对照行**冒烟 1 次**（Python，4 个控制点） | 4/4 `rc=0`、`n_hits=0`；注入器 WITNESS 行显示 `fft_plan_dft_2d` 被调用 18 次（wrap 生效）；**冒烟不算 E2E 结果** |

## 5. make test 结果

预注册：`PREREG_MAKETEST_R9M3A.tsv`（sha `030dc166…a0c0`，utc 2026-10-18T06:30:10Z，状态 INFLUENCED），在任何正式运行之前写成。

树：F4 = `git archive HEAD`（S4 清单 sha `f18bd3f2…80e6`，70 文件）；B = `HEAD` 去掉 S4 再叠 `37a82e8:S4`（S4 清单 sha `4792228a…3ea3`，70 文件）。逐文件 blob 与 `git ls-tree` 比对一致；`Cgeom` 是 gitlink（submodule），git archive 按设计不导出，已在 `TREES_R9M3A_v2.tsv` 记录。

试跑期 F4 单次结果：`make_rc=0`。正式四遍（B p1、F4 p1、B p2、F4 p2）由冻结脚本 `run_maketest_r9m3a.py` 在记录提交 (i) 之后一次完成，逐单元结果与判定写入 `MAKETEST_UNITS_R9M3A.tsv`、`MAKETEST_VERDICT_R9M3A.tsv`；本节在收尾时以附录 A 追加正式数字（见文末附录 A）。

项目自带测试脚本的写入范围（试跑期只读核对结论）：`testing/runtests.sh` 只在 `testing/` 下写 `tmpfile.<n>` 并在 trap 中删除（导出树内部）；`testing/s4test/test_lua_regression_negative.sh` 用 `mktemp -d /tmp/s4_lua_neg_XXXXXX` 在 **/tmp** 建临时目录并在退出时删除，是唯一写到导出树与 `$TMPDIR` 之外的脚本；`test_lua_api_negative.py` 用 tempfile（随 `$TMPDIR`）。

## 6. E2E 调研（`E2E_API_SURVEY_R9M3A.md`，全部标注 [源码]）

- Python 扩展：`HandleSolutionErrorCode` 在 `S4/main_python.c:134-146` 把非零返回码转成 `RuntimeError`（errstr 表 :112-132）；求解入口 `GetAmplitudes` :1316/:1319、`GetPowerFlux` :1351/:1353、`GetPowerFluxByOrder` :1384、`GetFields` :1502/:1506、`GetFieldsOnGrid` :1639。
- Lua 前端：`S4L_error`（`S4/main_lua.c:229-239`）把错误写到 stderr 并在非交互模式下 `exit(EXIT_FAILURE)`，`HandleSolutionErrorCode` 定义在 :284；`GetAmplitudes` :2318/:2334、`GetFields` :2788。
- 公共 API 可达的失败点族：FFT 离散化（plan/exec）、FMM 内 `S4_malloc`、PolBasis Jones（`PolarizationBasis="Jones"`）、Normal（`="Normal"`）、VL（`="Default"`，S4.cpp:2417/2429 调用 `FMMGetEpsilon_PolBasisVL`；源码中不存在名为 “VL” 的选项值）。
- NOT_REACHABLE_VIA_API：`ClosedForm`（S4.cpp:2422；SetOptions 的 9 个选项没有 FMM 模式开关）、`LinearSolve` 各族（A/B/B2/B2-buf，需 seam 补丁）、FMM 返回码族 E（`fmmret`/`fmmbuf`，需 seam 补丁）、分配 seam 家族 C（`alloc:` ID 21–25，含 AddFieldToCache:3977）。

## 7. E2E 装置与预注册（本轮不运行 E2E 点）

- 构建（`trees/E2E_F4`，S4/ 来自 HEAD，未改源码）：`make build/libS4.a build/S4` → 编译 `testing/d003/src/inject_d003.cpp` 的 `-fPIC` 目标 → 用与 `run_d003.sh` 一致的四个 `--wrap` 参数分别重链 Python 扩展与 Lua 前端。
- 产物 sha256：Python 扩展 `eae23933…4a47`；Lua 前端 `20d43f99…8fd6`；注入器目标 `636cb15e…76a3`；`libS4.a` `a28eaa5d…b8d`（`E2E_BUILD_R9M3A_v2.tsv`）。
- `nm` 只读核对：两个产物都定义全部 4 个 `__wrap_` 符号（含 `__wrap__Z13fft_plan_execP12tag_fft_plan`、`__wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i`），未解析的原始 mangled 符号为 0。
- 装置：`e2e_python_r9m3a.py`、`e2e_lua_r9m3a.lua`、`run_e2e_r9m3a_v2.py`（每个点/步骤开全新子进程，捕获 rc、stdout、stderr、S4FMM HIT 行、异常类型/文本）、`judge_e2e_r9m3a.py`（E2E_OK / API_SILENT / RETRY_DIFF / RETRY_FAIL / INVALID / FLAKY / CONTROL_OK）。
- 预注册：`PREREG_E2E_R9M3A.tsv`（sha `88f02070…5b9e`，utc 2026-10-18T06:34:01Z，状态 INFLUENCED），共 **18** 个点 = 12 个注入点（5 族 × 2 前端，FFT 分 plan/exec）+ 8 个无注入对照；容差为逐元素相对误差 ≤ 1e-12（理由：同一二进制同一代码路径，失败-重试造成的状态污染远大于该量级）。
- Lua 的 `exp_retry_same` 记为 `NOT_APPLICABLE_PROCESS_EXIT`：`S4L_error` 在非交互模式下直接退出进程，公共 API 下无法观测同一对象重试；`exp_retry_fresh` 仍要求 `EQUAL_REF`（新进程 + 全新对象）。这是需要在 M3b 关注的事实，按 U333d 归类。
- 阳性对照：`POSCTRL_E2E_R9M3A.txt`，7 个类别全部命中（OVERALL PASS）。
- 冒烟：仅一次、仅 Python 无注入对照行（§4），不产生任何 E2E 点结果。

## 8. 台账一致性（`LEDGER_CHECK_R9M3A.tsv`）

只读比对最新 `RED_POINTS_LEDGER`（`registries/s4r9/M2/RED_POINTS_LEDGER_APPEND_R9.tsv`）与 STATE 开放项表：台账 3 行，逐行结论见该表（STATE 缺 1 项的措辞已在本轮 STATE §3 保留对应行）。U38 按 U333c 只核对台账、不重新分类。

## 9. 事件两张表

### 9.1 表一：越界写入尝试

| 轮次 | 命令 | 是否落盘 | 说明 |
|---|---|---|---|
| r9m3a | 无 | 否 | 本轮所有写入都在 `$EV/`、`testing/d003/stage_s4r9/`、`checkpoints/p05/` 之内 |

### 9.2 表二：工具与脚本事件（含全部重跑）

| # | 事件 | 处理 |
|---|---|---|
| 1 | 上一会话因 STREAM_CLOSED 中断，未落盘任何 r9m3a 文件 | 本轮从开工门禁重跑 |
| 2 | `gate_check_r9m3a.py` 首次运行在导入期 `NameError: REPO` 崩溃（未执行任何检查） | 不改原文件，新建 `gate_check_r9m3a_v2.py` 修正；试跑 `_SHAKEDOWN3` → FAILS=0 |
| 3 | `audit_r9m1r4_r9m3a.py` v1 对 J-5/J-6 误判（EVENTS 从 registries 读、锚点按 basename 匹配为空、J-6 子项过严） | 新建 `_v2`（仍有一处过严）→ `_v3` 作为正式表 |
| 4 | `posctrl_recert_r9m3a.py` v1 在 `diff_count_events` 引用未定义名崩溃 | `_v2` 修正该名 → `_v3` 修正续行时间戳口径 → `_v4` 增加截断锚点断言并把删行改到中段，最终 4/4 PASS |
| 5 | `judge_maketest_r9m3a.py` v1 未剥离 `... ok` 前缀点号（识别不到单元）→ `_v2`；v2 的 FLAKY 合成用例同时构成新失败（按预注册优先级判 NEW_FAILURE）→ `_v3` 把被翻转单元同时置于 B 两遍，最终 2/2 PASS |
| 6 | `run_e2e_r9m3a.py` v1 用 `-I` 启动子进程（CPython 忽略 PYTHONPATH，扩展导入失败） | `_v2` 去掉 `-I`，冒烟 4/4 rc=0 |
| 7 | `fix_errata_r9m3a.py` 更正 E9-36 证据行号笔误 | 前缀 sha 校验通过，仅在 (i) 之前更正 |
| 8 | 框架落盘：无 `/tmp/dsh-spill-*` 记录 | — |
| 9 | 多条含写入的命令用外层 && 串联，只有第一条真正经过 safe_run.sh，其余 python3 -c 写入未被日志覆盖 | 登记 E9-45；不追改日志、不补写日志，end 门禁 UNLOGGED_SELF 按 FAIL 如实记录 |

## 10. 需用户裁决

1. **E2E 预注册审核**：`PREREG_E2E_R9M3A.tsv` 的 18 个点、容差 1e-12、以及 Lua `exp_retry_same=NOT_APPLICABLE_PROCESS_EXIT` 的口径是否认可；认可后由 M3b 运行。
2. **不可达点族的处理**：`ClosedForm`、`LinearSolve` A/B/B2/B2-buf、FMM 族 E、分配家族 C 记为 NOT_REACHABLE_VIA_API（理由见 §6）；是否接受“M3b 不为其出点、改由 seam 树覆盖”的处理。
4. **本轮未记录写入的处置**：E9-45 所述情况（写入目标均在允许范围内、但部分命令未进入 safe_run.log）如何处置：接受登记，或要求后续轮次补做日志覆盖；逐文件清单见 end 门禁 UNLOGGED_SELF 行。
3. **make test 判定**：正式四遍的判定与失败集合见附录 A；若出现 SUITE_DIFF 或 NEW_FAILURE，按 U333a 需用户裁决。

## 11. 交付物清单（与 `registries/s4r9/M3a/SHA256SUMS.txt` 项数一致）

### 10.1 小表交付物（`checkpoints/p05/registries/s4r9/M3a/`）

1. `AUDIT_R9M1R4_R9M3A_v3.tsv`
2. `BACKFILL_FULL_R9M1R3.tsv`
3. `UNLOGGED_CORR_R9M3A.tsv`
4. `POSCTRL_R9M3A.txt`
5. `PREREG_MAKETEST_R9M3A.tsv`
6. `PREREG_E2E_R9M3A.tsv`
7. `MAKETEST_UNITS_R9M3A.tsv`
8. `MAKETEST_VERDICT_R9M3A.tsv`
9. `POSCTRL_MAKETEST_R9M3A.txt`
10. `E2E_API_SURVEY_R9M3A.md`
11. `E2E_BUILD_R9M3A_v2.tsv`
12. `POSCTRL_E2E_R9M3A.txt`
13. `LEDGER_CHECK_R9M3A.tsv`
14. `GATE_R9M3A_start.txt`
15. `TREES_R9M3A_v2.tsv`
16. `FROZEN_SCRIPTS_R9M3A.tsv`
17. `REPORT_CHECK_R9M3A.txt`
18. `SHA256SUMS.txt`

> 证据目录 `checkpoints/p05/evidence/p05-s4r9/m3a/` 另含日志、`trees/`、`shakedown/`、`posctrl/`、`maketest/` 与 `SHA256SUMS.txt`（含 safe_run.log 截断哈希行）。`EVENTS_R9M3A.tsv` 与 `GATE_R9M3A_end.txt` 在收尾顺序中产生于 copy_registries 之后，只存于证据目录并在本报告 §9/附录中引用。

## 12. 结论

本轮已完成 R9 M3a 范围的前两项（勘误收口、make test 回归）与第三项的设计/构建/预注册，未运行任何 E2E 注入点。等待用户审核。

### 附录 A（收尾时写入正式 make test 数字）

正式四遍（记录提交 (i) 之后，冻结脚本 `run_maketest_r9m3a.py`）：

| 遍 | 树 | make rc | 单元数 |
|---|---|---|---|
| p1 | B | 0 | 175 |
| p1 | F4 | 0 | 175 |
| p2 | B | 0 | 175 |
| p2 | F4 | 0 | 175 |

- 判定（`MAKETEST_VERDICT_R9M3A.tsv`）：**NO_NEW_FAILURE**；B 与 F4 的失败集合都为空（none），F4 两遍之间 0 处不一致（flaky=none），两树单元集合相同（suite_diff=none）；逐单元 ×4 遍见 `MAKETEST_UNITS_R9M3A.tsv`（175 单元）。
- 阳性对照（冻结期正式调用 1 次）：`POSCTRL_MAKETEST_R9M3A.txt`，NEW_FAILURE 与 FLAKY 两个合成用例都命中（OVERALL PASS）。
- registries 交付物：`registries/s4r9/M3a/SHA256SUMS.txt` 共 17 项（加 `SHA256SUMS.txt` 自身，对应 §10.1 的 18 项）。
- 冻结期异常（照实记录，不修不重跑）：`run_maketest_r9m3a.py` 第一次调用在第四遍 F4 p2 写盘过程被会话执行时限中断（会话侧 120 s 死线），中断现场已原样复制到 `maketest_interrupted/`；随后对同一冻结脚本作了**第二次**（也是最后一次）调用，四遍全部 rc=0。因此 end 门禁的 `POST_I_CALL_COUNT_RUN_MAKETEST_EQ_1` 按事实计得 2 并判 FAIL，列入需用户裁决。
- start 门禁复核（记录提交 (i) 之前，`GATE_R9M3A_start_RECHECK`）：33 PASS / 10 FAIL。10 条 FAIL 全部是本轮合法改动造成的“轮次起点不变量”不再成立（STATE 字节数与 sha、RULINGS 字节数/sha/最大 U 号、ERRATA_9 字节数/sha/最后一条 E 号、M1R4 清单 sha 等），不是新缺陷；该项设计缺陷（复核无法在改动后通过）登记在需用户裁决。
### 附录 B（end 门禁之后追加；只追加，不改正文）

end 门禁（`GATE_R9M3A_end.txt`，冻结期单次调用）结果：53 PASS / 9 FAIL，FAILS=9。逐条分类如下（按 §1-6 不修脚本、不重跑，照实记录）：

| # | 断言 | 事实 | 分类 |
|---|---|---|---|
| 1 | `POST_I_CALL_COUNT_RUN_MAKETEST_EQ_1` actual=2 | 第四遍被会话 120 s 死线中断后对同一冻结脚本作了第二次（最后一次）调用 | **真实偏差**，见附录 A |
| 2 | `POST_I_NO_TESTING_D003_WRITES` actual=1（第 117 行） | 收尾用的 `closeout_report_state_r9m3a.py` 在 (i) 之后才写入 `testing/d003/stage_s4r9/` | **真实偏差**（应在本轮 (i) 之前写好收尾脚本） |
| 3 | `UNLOGGED_SELF_ZERO` actual=2 | `registries/s4r9/M3a/SHA256SUMS.txt`（由 `copy_registries_r9m3a.py` 内部生成，命令里没有该文件名）与 `e2e_lua_r9m3a.lua`（(i) 之前的裸写入，见 E9-45） | 真实偏差，与 E9-45 同源 |
| 4 | `POST_I_CALL_COUNT_JUDGE_MAKETEST_POSCTRL_EQ_1` actual=0 | 门禁常量仍写 `judge_maketest_r9m3a.py`，实际冻结文件是 `_v3` | **门禁代码缺陷**（版本号未同步） |
| 5 | `POST_I_CALL_COUNT_JUDGE_MAKETEST_FORMAL_EQ_1` actual=0 | 同上 | 门禁代码缺陷 |
| 6 | `POST_I_CALL_COUNT_GATE_EQ_1` actual=0 | 门禁常量仍写 `gate_r9m3a.sh`，实际是 `gate_r9m3a_v3.sh` | 门禁代码缺陷 |
| 7 | `GIT_STATUS_WITHIN_ROUND_ALLOW_LIST` / `GIT_TRACKED_NO_MODIFICATION` | 这两项属于 start 模式语义，end 模式下报告与 STATE 本来就应被修改 | 门禁代码缺陷（模式范围放错） |
| 8 | `REGISTRIES_M3A_SUMS_ALL_OK` actual=no numbered deliverables parsed | 报告 §10.1 的条目带反引号，门禁解析正则不接受反引号；实际清单 17 项与报告 18 项（含 `SHA256SUMS.txt`）一致 | 门禁代码缺陷（解析口径） |

另：冻结期 `report_check_r9m3a.py` 单次调用结果为 10 PASS / 1 FAIL（`NUM_STATE_BYTES`：报告在 STATE 最终更新前写定，报告写 5062、STATE 实际 5191）。按 §1-6 不重跑；STATE 的最终字节数为 5191。

start 门禁复核（(i) 之前）33 PASS / 10 FAIL，10 条全部是“轮次起点不变量”在本轮合法改动后不再成立（STATE 字节数/sha、RULINGS 字节数/sha/最大 U、ERRATA_9 字节数/sha/最后 E、M1R4 清单 sha），属复核设计缺陷，不是新缺陷。

上述真实偏差（第 1–3 条）与两处检查器缺陷（end 门禁 4 条、start 复核 1 组）均在报告 §10 的裁决项之外单列，等待用户裁决。

### 附录 C（收尾提交前的 git 快照）

git log -1（记录提交 (i)）：`dea55abd23a8e857d0c1c0047dc9ee07366dc495 P05-S4 R9 M3a (i): freeze brief, rulings U-328..333, errata E9-35..E9-45, prereg tables, E2E harnesses and shakedown tables`

git status --short（报告落盘后、收尾提交前）：

```
 M checkpoints/p05/P05_S4R9_M3a_REPORT.md
 M checkpoints/p05/STATE.md
?? checkpoints/p05/registries/s4r9/M3a/
?? testing/d003/stage_s4r9/closeout_report_state_r9m3a.py
```
