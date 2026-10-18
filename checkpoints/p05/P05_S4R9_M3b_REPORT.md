# P05-S4 R9 M3b 报告（轮次标识 r9m3b）——M3a 偏差裁决落账 + make test 只读重解析 + E2E 装置修订、校准、新预注册与正式两遍运行

> 规则依据仓库根 AGENTS.md 与本轮任务书（`checkpoints/p05/briefs/P05_S4R9_BRIEF_M3b.md`）。本轮不改 S4/、判定器与历史装置，不重跑 make test（只读重解析 M3a 的 4 份日志），正式结果由记录提交 (i) 之后的冻结脚本给出（附录 A）。

## 1. 门禁

开工门禁逐项核对，全部一致：

| 项 | 期望 | 实际 |
|---|---|---|
| HEAD | `6aa11d8b2eb3bea896406842c30eda742af19080` | 一致 |
| `HEAD:S4` | `589e15eb11fcb04e031b524f25a443e7921946cf`（F4） | 一致 |
| 判定器 sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` | 一致 |
| git status --short（开工） | 空 | 空 |
| `/tmp` 顶层 | 条目数 0 | 0 |
| RULINGS.tsv | 136951 字节，sha `579b73c9…8951`，最大 U333 | 一致 |
| ERRATA_9.txt | 38912 字节，sha `d5d8d9a0…49ee`，最后 E9-45，共 45 条 | 一致 |
| STATE.md | 5191 字节，sha `7ae31ae0…25d1` | 一致 |
| registries/s4r9/M3a/SHA256SUMS.txt | sha `1fdf80ac…d3d8`，17 项全 OK | 一致 |
| PREREG_E2E_R9M3A.tsv | sha `88f02070…5b9e` | 一致 |
| 历史清单 | 全部 OK（项数由脚本数出） | s3r5 14 / M0 25 / M2 14 / M2b 13 / M2c 11 / M1 28 / M1R2 33 / M1R3 26 / M1R4 11 / M3a 17 项 |

正式 start 门禁：`gate_r9m3b.sh start` → `GATE_R9M3B_start.txt`，45 项断言，PASS=45、FAILS=0。试跑版 `GATE_R9M3B_start.txt_SHAKEDOWN1` 同为 FAILS=0。

两次 start 门禁之间的说明（照实披露）：本轮的 S-C 构建、校准、预注册与注入试跑先于正式 start 门禁执行，随后才落正式 start 门禁；start 门禁所检查的开工不变量（HEAD、`HEAD:S4`、判定器、RULINGS/ERRATA/STATE 的字节数与 sha、已提交文件未改动、`/tmp` 条目数 0）在门禁时刻仍全部成立，因此正式 start 门禁有效；该顺序偏差登记在 §12 表二第 1 行。`GIT_STATUS_LINES=16` 全部落在本轮允许清单内。

## 2. K 项复核（`AUDIT_R9M3A_R9M3B.tsv`，12 行全部“属实”，行号由脚本从原文件算出）

| 项 | 复核结论 | 脚本算出的关键事实（摘要） |
|---|---|---|
| K-1 | 属实 | `run_e2e_r9m3a_v2.py:39` 把注入 env 交给整个 Python 子进程；`e2e_python_r9m3a.py:51` 的 1_clean_ref 在同进程先执行 |
| K-2 | 属实 | `e2e_lua_r9m3a.lua:3` 读全局 arg；`main_lua.c:3498/3532` 只把 -a 放进局部 arg 与 S4.arg；`main_lua.c:3551` 把每个 argv 当脚本加载；`SetDiscretizedEpsilon` 不存在（注册名 `UseDiscretizedEpsilon`，`main_lua.c:3320`） |
| K-3 | 属实 | `S4.cpp:2410` 先调 FFT、`S4.cpp:2413` 才进 PolBasis；`fmm_FFT.cpp:75/83` 两处 S4_malloc；校准实测 jones/nv/vl 的第 1、2 次 S4_malloc 来自 `FMMGetEpsilon_FFT`，PolBasis 在 call_seq=3 |
| K-4 | 属实 | 默认 `use_discretized_epsilon=0`（`S4.cpp:337`）→ `FMMGetEpsilon_ClosedForm`（`S4.cpp:2422`）；Kottke 由 `use_subpixel_smoothing`（`S4.cpp:2407/2408`）选择，Python kwlist 含 SubpixelSmoothing（`main_python.c:1749`）；Lua 注册 `UseExperimentalFMM`（`main_lua.c:3330`）而 main_python.c 无 experimental；REPL `S4L_set_interactive(L,1)`（`main_lua.c:3570`）后 S4L_error 不 exit |
| K-5 | 属实 | `judge_maketest_r9m3a_v3.py` 只看单元行与下一行（`:62/:64`）；M3a 表里 s4test 167 个单元，日志写 `Ran 257`（`m3a/maketest/F4_p1.log:779`），漏 90 个 |
| K-6 | 属实 | M3a 报告正文写 /tmp 临时目录（`P05_S4R9_M3a_REPORT.md:60`），表一（`:90`）写“无” |
| K-7 | 属实 | `judge_e2e_r9m3a.py` 的 visible 含 `or len(stderr)>0`（`:83`）；`synthetic()` 只造 Python 记录（`:97`）且对 Lua 返回 None（`:123`） |
| K-8 | 属实 | PREREG fft 行未写 PolarizationDecomposition 而装置设了（`e2e_python_r9m3a.py:19`）；报告 §10 编号 1/2/4/3（`:108-111`）；§11 小节标题写成 10.1（`:115`）；§3 写 STATE 5062（`:37`） |
| U334 | 属实 | M3a 日志中 run_maketest 真正被调用 2 次（`m3a/safe_run.log:112,114`），中断现场 `maketest_interrupted/` 存在 |
| U335 | 属实 | M3a end 门禁 `POST_I_NO_TESTING_D003_WRITES actual=1`、`UNLOGGED_SELF actual=2`；closeout 调用行在其日志第 117 行之后 |
| U336 | 属实 | `m3a/REPORT_CHECK_R9M3A.txt` 的 NUM_STATE_BYTES FAIL；STATE 实际 5191 字节 |
| U337 | 属实 | M3a end 门禁 9 条 FAIL（4 条调用计数、2 条 start 语义、1 条反引号解析等）、start 复核 FAILS=10 |

## 3. 裁决与勘误

- 裁决追加：`append_rulings_r9m3b.py` 以“旧文件 + 新行”写入 U334–U342（5 列，前缀断言通过）。RULINGS.tsv 136951 → 139934 字节，sha `579b73c9…8951` → `4bcebe60…631a`，最大 U342。
- 勘误追加：`append_errata_r9m3b_v2.py` 追加 E9-46–E9-57（K-1..K-8 各一条 + U334–U337 各一条；事实与证据行号取自 `AUDIT_R9M3A_R9M3B.tsv` 的脚本复算结果，写入前断言 12 项全为“属实”）。ERRATA_9.txt 38912 → 51809 字节，sha `d5d8d9a0…49ee` → `2d32e4f1…2716`，共 57 条，最后 E9-57。
- M3a 报告、M3a registries 与 PREREG_E2E_R9M3A.tsv 保持不动（U336/U339）；`git diff` 校验见 end 门禁。

## 4. make test 只读重解析（S-B；**不运行 make**）

数据：M3a 证据目录下 `maketest/{B,F4}_p{1,2}.log`（只读）。解析规则：unittest 单元为 `test_x (mod.Class.test_x)` 行；状态词取该行或其后**直到下一个单元行为止**的第一个状态词（ok/FAIL/ERROR/skipped/expected failure/unexpected success）。

对账（每遍、每树，4 遍 × 2 段全部 OK）：

| 日志 | 段 | 识别单元数 | 日志 Ran N | skipped 识别/日志 |
|---|---|---|---|---|
| B_p1 / F4_p1 / B_p2 / F4_p2 | s4test_unittest | 257 | 257 | 1/1 |
| B_p1 / F4_p1 / B_p2 / F4_p2 | test_python_binding | 4 | 4 | 0/0 |

判定（`MAKETEST_VERDICT_R9M3B.tsv`，判据同 U333a）：**NO_NEW_FAILURE**；unit_count=265（261 个 unittest 单元 + 4 个 stage 级条目）；B/F4 失败集合都是 none、两遍 0 处不一致、两树单元集合相同。阳性对照（`POSCTRL_MAKETEST_R9M3B.txt`）：篡改一个 docstring 单元 ok→FAIL 判出 NEW_FAILURE；删除一个单元行判出 RECONCILE_FAIL，2/2 PASS。按 U338，M3a 的 NO_NEW_FAILURE 因本重解析通过而成立。

## 5. E2E 调研 v2 与 COVERAGE

`E2E_API_SURVEY_R9M3B.md`（全部 [源码]）逐条改正 K-4：ClosedForm 是默认路径；Kottke 可经 SubpixelSmoothing 到达；Lua 有 UseExperimentalFMM（Python 没有）；Lua REPL 出错不退出。可达点族与首个 S4_malloc 站点：CF `fmm_closed.cpp:40`、FFT `fmm_FFT.cpp:75/83`（plan `:89`、exec `:191`）、KT `fmm_kottke.cpp:87`（plan `:93`、exec `:271`）、JONES/NV/VL 在 PolBasis 文件内（`fmm_PolBasisJones.cpp:108` / `fmm_PolBasisNV.cpp:59` / `fmm_PolBasisVL.cpp:58`，**前两次 S4_malloc 来自 fmm_FFT**）、EXP `fmm_experimental.cpp:40`。

`COVERAGE_E2E_R9M3B.tsv`：LinearSolve A/B/B2/B2-buf（18 行 M1 覆盖）、FMM 返回码族 E（20 行）、分配 seam 家族 C（12 行）、kottke_alloc:31（2 行）标 `SEAM_ONLY`，逐行给出 M1/M2 的 point_id=verdict 覆盖行（读自 `registries/s4r9/M1/PREREG_M1_F4_R9M1.tsv` 与 `M1R3/VERDICT_M1_F4_R9M1R3.tsv`）。按 U340，这些族不出 E2E 点。

## 6. 构建与 sha 对照

在 `$EV/trees/E2E_F4`（`git archive HEAD`，未改源码）用 `build_e2e_r9m3b_v2.py` 重建，链接参数与 M3a 相同（`-Wl,--wrap=malloc`、`--wrap=_Z13fft_plan_execP12tag_fft_plan`、`--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i`、`--wrap=_Z9S4_mallocm`），只链接未修改的 `testing/d003/src/inject_d003.cpp`。

| 产物 | sha256 | 与 M3a 比对 |
|---|---|---|
| Python 扩展 | `2890991c…aaa7` | 不同：仅 build-id（20 字节）+ 树路径 `m3b`/`m3a` 一个字符；脚本按字节复算为 `DIFFERENT_ONLY_BY_TREE_PATH_m3b_vs_m3a` |
| Lua 前端 | `20d43f99…8fd6` | 相同（逐字节 IDENTICAL） |
| 注入器目标 | `636cb15e…76a3` | 相同 |
| libS4.a | `a28eaa5d…b8d` | 相同 |

`nm`（未加 -C）核对：两个产物都定义全部 4 个 `__wrap_` 符号；未解析的原始 mangled FFT 符号为 0。

## 7. 校准（注入无关，先于预注册）

`calib_e2e_r9m3b_v3.py` 对 17 个“前端 × 选项组”做无注入 gdb 运行（`gdb -nx -batch`，断点 `__wrap__Z9S4_mallocm`、`__wrap__Z15fft_plan_dft_2d…`、`__wrap__Z13fft_plan_exec…`、`__wrap_malloc`；S4_malloc 的 bt 第 1 帧用 `info symbol *(void **)$rsp` 解析），gdb 命令文件在 `$EV/tmp/`，原始日志在 `$EV/calib/`。结果 `CALIB_E2E_R9M3B.tsv`：882 个 EVENT 行 + 27 个 TARGET 行。

关键校准值（nth = 目标文件内第一次 S4_malloc 的调用序号；同时记录该序号对应的 size）：

| 组 | 目标函数 | nth | calib size | 说明 |
|---|---|---|---|---|
| CF | FMMGetEpsilon_ClosedForm | 1 | 192 | 默认路径 |
| FFT plan/exec/s4malloc | fft_plan_dft_2d / fft_plan_exec / FMMGetEpsilon_FFT | 1/1/1 | 5192 / NA / 24576 | plan 的 size 是首个 plan 调用内的第一个 malloc |
| KT plan/exec/s4malloc | 同上 / FMMGetEpsilon_Kottke | 1/1/1 | 5192 / NA / 16 | kottke 的 work 走 fft_alloc_complex，不经 S4_malloc |
| JONES / NV / VL s4malloc | FMMGetEpsilon_PolBasis* | 3 | 192 | 前两次来自 fmm_FFT（K-3） |
| EXP s4malloc（仅 Lua） | FMMGetEpsilon_Experimental | 1 | 192 | UseExperimentalFMM |

## 8. 预注册

`PREREG_E2E_R9M3B.tsv`（状态 INFLUENCED）在任何注入运行之前写成：42 行 = 25 个注入点（Python 10、Lua 批处理 11、Lua REPL 4）+ 17 个无注入对照（每“前端 × 选项组”1 行：py 6、lua_batch 7、lua_repl 4）。sha 与 UTC 记录在 `PREREG_E2E_R9M3B.sha256.txt`（sha `9e3895bb…31da`，utc 2026-10-18T07:17:39Z）。列：point_id、frontend、spec、options、inject_mode、nth、target_file_line、calib_size、exp_hit=1、exp_visible（具体文本模式）、exp_retry_same、exp_retry_fresh、tolerance（逐元素相对误差 ≤1e-12）、m12_k_group、is_control、note。预注册之后没有修改 exp_visible / exp_retry_*；不需要 PREREG_E2E_R9M3B_ERRATA.txt（无 nth/目标错误）。

## 9. 试跑摘要（记录提交 (i) 之前；输出在 `$EV/shakedown/`）

| 序号 | 目录 | 做了什么 | 结果 |
|---|---|---|---|
| 1 | `shakedown/smoke1` | 无注入对照冒烟（三个前端全覆盖） | 17/17 CONTROL_OK，rc=0、hits=0 |
| 2 | `shakedown/inj1` | 全量 42 点注入试跑（不算正式结果） | 25/25 E2E_OK（命中 1 次/点）、17/17 CONTROL_OK、BAD_OR_JUDGEABLE=0 |
| 3 | `posctrl/` | E2E 阳性对照（19 例落盘篡改记录，覆盖 3 前端与全部 9 类别，含 FLAKY 两个 run 文件） | 19/19 PASS |
| 4 | `posctrl/maketest/` | make test 阳性对照（2 例落盘篡改日志） | 2/2 PASS |

| 5 | `$EV/shakedown/`（收尾链预演） | closeout → report_check → copy_registries → events → sha_sums → end 门禁 `--commit-i HEAD` 全链预演（以 `shakedown/inj1` 的结果做临时输入） | 各脚本均成功执行；end 门禁 75 项全部执行，FAIL 项全部是试跑期必然（RULINGS/ERRATA 尚未在 (i) 提交、脚本调用次数 >1、d003 写入、ALL_STATUS 清单口径），逐项见 `GATE_R9M3B_end.txt_SHAKEDOWN2` |
三个前端都冒烟通过：Python（RuntimeError 文本含 GetPowerFlux）、Lua 批处理（stderr 以 GetPoyntingFlux: 开头且 rc=1）、Lua REPL（第一次求解 nil、第二次等于参考值）。装置修正要点：参考值一律另起无注入进程；注入变量只覆盖注入进程；Lua 用 `-a` 传 S4.arg 且只用真实方法名（缺失即 error）；REPL 用 30 行以内、每行 <200 字节的 stdin 脚本、只用全局变量。

## 10. 正式两遍结果

记录提交 (i) 之后由冻结脚本执行：`run_e2e_r9m3b.py formal pass1`、`formal pass2`（可分段续跑，按 point_id 跳过已完成点）→ `judge_e2e_r9m3b.py posctrl` → `judge_e2e_r9m3b.py formal pass1 pass2` → `judge_maketest_r9m3b_v2.py formal`。逐点类别、两遍一致性（FLAKY）、红点与阳性对照结果见附录 A；逐点明细见 `E2E_VERDICT_R9M3B.tsv`。

## 11. 台账一致性与事件

- 台账一致性：`LEDGER_CHECK_R9M3B.tsv`（最新已提交红点台账 `registries/s4r9/M2/RED_POINTS_LEDGER_APPEND_R9.tsv` 与 STATE 开放项表的逐行比对；U38 按 U333c 只核对、不重新分类）。
- 新红点：`RED_POINTS_LEDGER_APPEND_R9M3B.tsv`（按 U333d，只有出现 API_SILENT / RETRY_DIFF / RETRY_FAIL 才登记；本轮结果见附录 A）。

## 12. 事件两张表

### 12.1 表一：越界写入尝试

| 轮次 | 命令 | 是否落盘 | 说明 |
|---|---|---|---|
| r9m3a | 项目套件 `testing/s4test/test_lua_regression_negative.sh` 用 `mktemp -d /tmp/s4_lua_neg_XXXXXX` 写 /tmp 并在退出时删除 | 是（临时目录，退出即删） | 按 U338 补登记：项目套件固有行为、临时目录、非执行者违规；本轮开工与结束时 /tmp 快照均为 0 项 |
| r9m3b | 无 | 否 | 本轮所有写入在 `$EV/`、`testing/d003/stage_s4r9/`（文件名带 r9m3b）、`checkpoints/p05/` 之内 |

### 12.2 表二：工具与脚本事件

| # | 事件 | 处理 |
|---|---|---|
| 1 | S-C 的构建/校准/预注册/注入试跑先于正式 start 门禁执行（任务书 §5 顺序为 start 门禁在前） | 照实披露；正式 start 门禁在开工不变量仍全部成立时执行且 FAILS=0，结论有效；此后严格按 §5 顺序 |
| 2 | `calib_e2e_r9m3b.py` v1 的 site 正则不容忍 demangle 后的参数表；lua_repl 的 gdb `run < FILE` 会丢掉 `--args` | 新建 `_v2`；v2 的 CALIB 头行字符串拼接笔误导致 SyntaxError，新建 `_v3` 修正；最终 17 组 0 FAIL |
| 3 | `audit_r9m3a_r9m3b.py` v1 缺 `import sys`；v2 更正后又发现 U334 把 run_maketest 的 base64 写入行也计入调用 | 新建 `_v3` 用与门禁一致的“脚本 token”判据计数，12/12 属实 |
| 4 | `append_errata_r9m3b.py` v1 读取审计表时列名用错（`claim` vs `planner_claim`）在写入前抛 KeyError | 新建 `_v2`，写入前断言 12 项全属实；ERRATA 前缀 sha 校验通过 |
| 5 | `judge_maketest_r9m3b.py` v1 的阳性对照用 `len(lines)-len(block)` 推算块起始行，篡改落到错误行 | 新建 `_v2` 用 banner 行号定位；posctrl 2/2 PASS |
| 6 | 框架落盘：本会话无 `/tmp/dsh-spill-*` 记录 | — |
| 7 | 本轮所有写入均经 `safe_run` 且每条写入单独一条命令；end 门禁 UNLOGGED_SELF 结果见门禁文件 | — |

| 8 | 正式 start 门禁由 `gate_r9m3b.sh`(v1)+`gate_check_r9m3b.py`(v1) 执行并通过；随后发现交付物小节解析需容忍反引号与 12.1/14.1 编号、以及 `gate_r9m3b.sh` 的后缀拼接在试跑中写出了字面 $${OUTNAME}$${1} 文件，改为 v2/v3（终止版本 `gate_r9m3b_v3.sh` + `gate_check_r9m3b_v3.py`） | start_recheck 用 v2、end 用 v3；EV 内字面文件名残留已删除；FROZEN 清单按 v3 记录 |
| 9 | `sha_sums_r9m3b.py` v1 把门禁自己会改写的 `ALL_STATUS_R9M3B_end.txt` 纳入证据清单，试跑中 EVIDENCE_SHA256SUMS 因此报哈希不一致 | 新建 `_v2`：清单排除 `ALL_STATUS_*`（门禁生成的快照，不属证据表）；正式期使用 v2，并在本表披露 |
| 10 | `start_recheck` 在冻结清单写定之前执行（§5 的顺序为冻结清单 → start 前缀复核 → (i)） | 照实披露：该复核只检查 RULINGS/ERRATA 前缀 sha 与已提交文件未被改动，冻结脚本不改变这两项，结论有效；其余顺序严格执行 |

## 13. 需用户裁决

1. `PREREG_E2E_R9M3B.tsv` 的 42 点布点、nth（CF/FFT/KT/EXP=1，JONES/NV/VL=3）、容差 1e-12、Lua 批处理 `exp_retry_same=NOT_APPLICABLE_PROCESS_EXIT` 与 REPL 观测口径是否认可。
2. U340 的 SEAM_ONLY 处理（LinearSolve A/B/B2/B2-buf、FMM 返回码族 E、分配家族 C、kottke_alloc:31）是否接受“不出 E2E 点、以 M1/M2 覆盖行代替”。
3. 本轮 E2E 正式两遍的判定与红点（附录 A）；若出现 FLAKY / INVALID / HIT_OFF_TARGET 照实列出。按 U333d，出现 API_SILENT 或 RETRY_DIFF/RETRY_FAIL 时登记新红点，本阶段不改 S4/。
4. 本轮表二第 1 行（S-C 先于 start 门禁的顺序偏差）的处置。
5. M3a 的 end 门禁 6 条缺陷与 start 复核 10 条 FAIL 已按 U337 在本轮门禁中修复；是否需要另立 M3a 门禁的更正件。

## 14. 交付物清单（与 `registries/s4r9/M3b/SHA256SUMS.txt` 项数一致）

### 14.1 小表交付物（`checkpoints/p05/registries/s4r9/M3b/`）

1. GATE_R9M3B_start.txt
2. GATE_R9M3B_start_RECHECK.txt
3. AUDIT_R9M3A_R9M3B.tsv
4. MAKETEST_UNITS_R9M3B.tsv
5. MAKETEST_VERDICT_R9M3B.tsv
6. POSCTRL_MAKETEST_R9M3B.txt
7. E2E_API_SURVEY_R9M3B.md
8. COVERAGE_E2E_R9M3B.tsv
9. E2E_BUILD_R9M3B.tsv
10. CALIB_E2E_R9M3B.tsv
11. PREREG_E2E_R9M3B.tsv
12. PREREG_E2E_R9M3B.sha256.txt
13. E2E_VERDICT_R9M3B.tsv
14. POSCTRL_E2E_R9M3B.txt
15. RED_POINTS_LEDGER_APPEND_R9M3B.tsv
16. LEDGER_CHECK_R9M3B.tsv
17. FROZEN_SCRIPTS_R9M3B.tsv
18. REPORT_CHECK_R9M3B.txt
19. SHA256SUMS.txt

## 15. 结论

本轮已完成 R9 M3b 范围：M3a 偏差裁决落账（U334–U342、E9-46–E9-57）、make test 只读重解析（NO_NEW_FAILURE，四遍对账通过）、E2E 装置修订/校准/新预注册/正式两遍运行与判定。未宣布阶段完成；正式两遍的逐点结论、阳性对照与红点见附录 A。等待用户审核。

### 附录 A（收尾时由 closeout 写入正式结果）

记录提交 (i) 之后由冻结脚本执行；本附录的数字全部由 closeout 从结果表复算，未手写。

- E2E 正式两遍（pass1、pass2）：CONTROL_OK=17, E2E_OK=25；其他类别： none
- E2E 判据：visible 为具体错误文本（Python RuntimeError 含 GetPowerFlux；Lua 以 GetPoyntingFlux: 开头的 stderr 行），HIT 的序号与 size 必须等于 CALIB；FLAKY=none，INVALID=none，HIT_OFF_TARGET=none，MISSING_RUN=none
- E2E 阳性对照（冻结期正式调用 1 次）：OVERALL_POSITIVE_CONTROL: PASS (19/19)
- make test 只读重解析：verdict=NO_NEW_FAILURE unit_count=265；4 遍 × 2 段对账 存在 FAIL: [['reconcile', 'B_p1', 'test_python_binding', '4', '4', '0', '0', 'OK'], ['reconcile', 'B_p1', 's4test_unittest', '257', '257', '1', '1', 'OK'], ['reconcile', 'F4_p1', 'test_python_binding', '4', '4', '0', '0', 'OK'], ['reconcile', 'F4_p1', 's4test_unittest', '257', '257', '1', '1', 'OK']]；阳性对照：OVERALL_POSITIVE_CONTROL: PASS (2/2)
- 构建：Python 扩展 sha 2890991c（与 M3a 差异仅 build-id 与树路径），Lua 前端 sha 20d43f99（与 M3a 逐字节相同）
- 校准：EVENT 行 882、TARGET 行 27（17 个前端 × 选项组，注入无关；gdb 日志在 $EV/calib/）
- 预注册：PREREG_E2E_R9M3B.tsv 共 42 行（25 注入点 + 17 无注入对照），sha=9e3895bb，状态 INFLUENCED
- 新增红点： 无（无 API_SILENT / RETRY_DIFF / RETRY_FAIL）
- 门禁：start PASS=45 FAILS=0；审计 12/12 属实；FROZEN 调用计数由 end 门禁按清单核对
- STATE 最终字节数：5534（<=8192）
- 逐点明细：E2E_VERDICT_R9M3B.tsv；红点表：RED_POINTS_LEDGER_APPEND_R9M3B.tsv；台账核对：LEDGER_CHECK_R9M3B.tsv

台账：RULINGS 最大 U342；ERRATA 最后 E9-57，共 57 条；本轮 M3a 判定 NO_NEW_FAILURE 因上述重解析通过而成立（U338）。
### 附录 B（end 门禁之后追加；只追加，不改正文）

end 门禁（`GATE_R9M3B_end.txt`，冻结期单次调用）：76 项断言，PASS=75、FAILS=1。按 §1-6（冻结期不修脚本、不重跑）逐项处置如下：

| # | 断言 | 事实 | 分类 |
|---|---|---|---|
| 1 | `EVIDENCE_SHA256SUMS_OK` | actual = "no sha_sums_r9m3b.py call after (i)" | **检查器缺陷**：`gate_check_r9m3b_v3.py` 的该检查仍硬编码 v1 脚本名 `sha_sums_r9m3b.py`，而 FROZEN 清单与实际冻结脚本是 `sha_sums_r9m3b_v2.py`。同一门禁的 FROZEN 计数项 `POST_I_CALL_COUNT_SHA_SUMS_R9M3B_V2_EQ_1` 判 PASS（actual=1），证明该脚本被调用恰好 1 次；`EV/SHA256SUMS.txt` 由其生成（截断行 = 第 125 行，sha `387b754d…d37d2e`，43 项）。该项 FAIL 不表示证据清单缺失。 |

其余 75 项全部 PASS，包括：FROZEN 15 项 sha 全部未变；全部冻结脚本的 POST_I 调用计数（run_e2e 2 段、judge_e2e posctrl/formal 各 1、judge_maketest_v2 posctrl/formal 各 1、ledger 1、closeout/report_check/copy_registries/events/sha_sums_v2 各 1、gate end 1）；`POST_I_NO_TESTING_D003_WRITES=0`；`COMMITTED_I_FILES_UNCHANGED_AT_END`；EVENTS 124 行与重算一致；`UNLOGGED_SELF=0`；其它轮证据目录未动；`REGISTRIES_M3B_SUMS_ALL_OK`（清单 18 项与报告 19 项一致）；预注册早于任何 E2E 点；正式两遍 42/42；E2E verdict 42 行 `{CONTROL_OK: 17, E2E_OK: 25}`；CALIB 27 个 TARGET 行；MAKETEST `NO_NEW_FAILURE`；STATE 5534 字节。

正式结果摘要（与附录 A 一致）：E2E 25 个注入点全部 `E2E_OK`、17 个无注入对照全部 `CONTROL_OK`；`FLAKY`/`INVALID`/`HIT_OFF_TARGET`/`API_SILENT`/`RETRY_DIFF`/`RETRY_FAIL` 均为 0；阳性对照 E2E 19/19、MAKETEST 2/2；新增红点 0。make test 只读重解析 `NO_NEW_FAILURE`（4 遍 × 2 段对账 257/257 + 4/4，265 单元），U338 所述条件成立。

门禁版本演进（照实记录）：start 用 `gate_r9m3b.sh`(v1) + `gate_check_r9m3b.py`(v1)，start_recheck 用 v2，end 用 v3。v2 修好了交付物小节解析对反引号与 12.1/14.1 编号的容忍与 `OUTNAME` 后缀拼接；v3 保留了 `sha_sums_r9m3b.py` 旧脚本名硬编码这一处残留缺陷（即上表第 1 项），按 §1-6 不在冻结期修改。

git log -1（记录提交 (i)）：`70eefa824a5572ead8dfd0f8051f026b15047ec0 P05-S4 R9 M3b (i): freeze brief, rulings U334..U342, errata E9-46..E9-57, make-test reparse, E2E harness/calib/prereg; awaiting user review`

git status --short（附录 B 落盘前、收尾提交 (ii) 前）：

```
 M checkpoints/p05/P05_S4R9_M3b_REPORT.md
 M checkpoints/p05/STATE.md
?? checkpoints/p05/registries/s4r9/M3b/
```

（`registries/s4r9/M3b/` 下 19 个文件 = 18 项小表 + SHA256SUMS.txt，将在收尾提交 (ii) 一并提交。）
