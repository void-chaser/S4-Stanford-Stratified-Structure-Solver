# P05-S5 R4 报告（s5r4）：S5 收口补齐——独立重判 v2、S5R3 门禁 8 项消解、就绪审计 GAP=0、S5R3 registry 26/26、签收范围声明草稿 v2

> 轮次：P05-S5 R4。本轮不宣布任何阶段完成或签收；签收只由用户在对话中给出。
> 修复前证据不得称为修复后验证；S5R4 不重跑 D016/E2E/make test 正式矩阵（U385），只做独立重判与一致性收口。

## 1 门禁

- start 门禁：2026-10-18T10:58:02Z
，HEAD=e6a65ab4751c5ba5…，HEAD:S4=589e15eb11fcb04e…（F4），判定器 sha256=d2d04145e0561638…；FAILS=0、CHECK_CRASHED=0（GATE_S5R4_start.txt；36 项断言）。
- 起始常量由 start 门禁记录：RULINGS.tsv 150471
 B（最大 U377）、ERRATA_S5.txt 8228
 B（最后 ES5-8）、STATE.md 3135
 B、p05-s5r3 证据清单 382 项全 OK（sha ab40c174…）、registries/s5r3 清单 10 条全 OK、R3 end 门禁 FAILS=8/CHECK_CRASHED=0。
- 试跑 end 门禁：$EV/shakedown/gate/GATE_S5R4_end.txt，staging 证据根/checkpoints 根/POST_I 起点行完整演练，FAILS=0、CHECK_CRASHED=0、总断言 139 项（U381：不再以 CHECK_CRASHED=0 单独作为通过条件；试跑期 FAIL 逐项归因并修正后以同一脚本 sha 重跑）。
- 正式 end 门禁：只跑一次，输出 $EV/gate/GATE_S5R4_end.txt；原文摘要见附录 B（门禁后追加）。
- 已交付的正式结果（S5R3 在 F4 上重跑、S5R4 独立重判复核，U385 不重跑）：E2E_OK=25 CONTROL_OK=17；D016 MATCH=33 MISMATCH=0 FLAKY=0；make test NO_NEW_FAILURE（unit_count=265，对账 8/8）；独立重判 DIFFS=0（E2E_ROWS=42 / D016_REJUDGED_ROWS=33 / D016_NOT_JUDGED=1）。

## 2 裁决入账（U378–U385，纯追加）

- RULINGS.tsv 纯追加 U378–U385 共 8 行（每行 5 个 tab 字段），前缀逐字节断言不变；追加后 154825 B，最大编号 U385。
- 原文逐字见 registries/RULINGS.tsv 与本轮任务书 §1。

## 3 勘误 ES5-9..ES5-14

- ERRATA_S5.txt 纯追加 ES5-9..14（前缀 sha 断言）：8228 → 13848 B；最后条目 ES5-14。
- ES5-9：S5R3 rejudge_s5r3.py 崩溃（SUMMARY 行被当数据行，KeyError），未产出 REJUDGE_S5R3.tsv；处理=U379。
- ES5-10：S5R3 end 门禁 5 项检查器/冻结标注缺陷（逐项见文件）；数据 sha 不变；处理=U378。
- ES5-11：S5R3 报告笔误与占位（§4 判定行 35→34；§5 的 DIFFS 未填（占位）；§11 写 26 项而清单实为 10 条）；R3 报告不改。
- ES5-12：S5R3 chain copy HARD_STOP、signoff 写错路径、就绪审计在 STATE 之前；处理=U380 与 R4 链顺序。
- ES5-13：S5R3 草稿含未实测『独立重判 DIFFS=0』；处理=U383 v2。
- ES5-14：S5R3 任务书把试跑通过条件定为 CHECK_CRASHED=0（规划缺陷）；处理=U381。

## 4 独立重判 v2（覆盖率与阳性对照）

- 输入：p05-s5r3 的 PREREG_E2E_S5R3.tsv、E2E_VERDICT_S5R3.tsv、e2e/pass1+pass2/points/*.json、PREREG_D016_S5R3.tsv、D016_PASS1/2_S5R3.json、D016_VERDICT_S5R3.tsv、D016_BUILD_S5R3.tsv；每个输入的 sha256 在首次正式调用之前写入 PREREG_REJUDGE_S5R4.tsv（91 个输入，状态 INFLUENCED）。
- 规则：不 import 任何判定/比较器脚本；跳过 # 注释行、表头行与 SUMMARY 行，一律按列名读取；E2E 42 点=25 注入+17 对照，每遍分类，不同记 FLAKY，缺遍记 MISSING_RUN；D016 36 行预注册中 3 行 ARTIFACT 不参与行为重判，33 行行为点重判比较，ROOT_CAUSE_RC 显式记 NOT_JUDGED_SOURCE_RECORD。
- 正式结果：E2E_ROWS=42 E2E_DIFFS=0；D016_RECORDED_ROWS=34 D016_REJUDGED_ROWS=33 D016_NOT_JUDGED=1 D016_DIFFS=0；DIFFS=0。
- 行覆盖：E2E 42 点全部 SAME（含 17 对照）；D016 33 个行为点全部 SAME；ROOT_CAUSE_RC 1 行记 NA/NOT_JUDGED_SOURCE_RECORD。
- 自检 6/6（$EV/SELFTEST_REJUDGE_S5R4.txt）：verdict 文件含 SUMMARY 行不崩溃且被排除、正常 MATCH、篡改→MISMATCH、两遍不同→FLAKY、缺遍→MISSING_RUN、D016 恢复值超阈值→MISMATCH；阳性对照 4/4（$EV/POSCTRL_REJUDGE_S5R4.txt）：干净副本 DIFFS=0，3 例篡改副本（E2E 可见错误删除、D016 恢复值超阈值、记录 verdict 翻转 1 行）均 DIFFS≥1。

## 5 门禁 5 项修正与 R3 复核表

- 修正（U378，详见 ERRATA ES5-10）：
  1. RULINGS_LINES_5_FIELDS：跳过 # 行，其余每个非空行正好 5 个 tab 字段；
  2. FROZEN_POST_I_CALL_COUNTS_MATCH：FROZEN 按列名读取，mode='-' 任意调用，mode=formal 要求命令含 formal 词，实际调用数逐行等于 expected；
  3. MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST：git status --porcelain=v1 不整体 strip，按状态列+路径解析；
  4. D016_VERDICT_ROWS_34：排除 # 行、point_id 表头行与 SUMMARY 行后计数 34，并断言 MATCH=33/RECORD=1；
  5. CALIB_DIFF_ZERO：排除首列为 SUMMARY 的行，其余每行 diff==SAME，SUMMARY 的 DIFFS=0。
- 每项修正配落盘变异阳性对照（$EV/POSCTRL_GATE_S5R4.txt）：干净副本 PASS、篡改副本使该检查 FAIL；git status 一项用真实格式字符串的允许/不允许两例 + 本轮真实 status。
- R3 复核表（$EV/R3_GATE_RECHECK_S5R4.tsv，8 行 = S5R3 的 8 条 FAIL 名称；每行 r4_result=PASS 且数据 sha 不变）：

| # | S5R3 FAIL | cause_class | 消解 |
|---|---|---|---|
| 1 | RULINGS_LINES_5_FIELDS | CK_COMMENT | fixed rule (skip '#' lines, exactly 5 tab fields) on the R3-final snapshot: 381 data rows, 0 bad rows (S5R3 checker counted comment lines) |
| 2 | FROZEN_POST_I_CALL_COUNTS_MATCH | FROZEN_MODE | R3 list wrote mode=formal but the R3 command had no formal word; R4 list mode=formal and the R4 formal rejudge command contains formal: actual=1 expected=1 |
| 3 | MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST | CK_STRIP | fixed parser (status=ln[:2], path=ln[3:]) on the R4 real status: 1 lines, 0 not allowed (R3 stripped the leading status space) |
| 4 | D016_VERDICT_ROWS_34 | CK_HEADER | fixed reader (skip '#' lines, point_id header, SUMMARY rows): rows=34 MATCH=33 RECORD=1 (S5R3 checker counted the header row) |
| 5 | CALIB_DIFF_ZERO | CK_SUMMARY | fixed rule (exclude first-field=SUMMARY rows; all other rows SAME; SUMMARY DIFFS=0): non-SAME rows=0 summary=SUMMARY DIFFS=0    |
| 6 | REJUDGE_DIFFS_ZERO | REAL_CRASH | S5R4 formal independent re-judge (new script, SUMMARY rows in the verdict files handled): DIFFS=0 E2E_ROWS=42 D016_REJUDGED_ROWS=33 D016_NOT_JUDGED=1; R3 inputs read-only, sha unch |
| 7 | READINESS_GAP_ZERO | ORDER | S5R4 order fixed: final STATE -> readiness; READINESS_S5R4 GAP=0 and its META records the final STATE bytes=3424 sha=1a962c77e13f8c3f... |
| 8 | REGISTRIES_SUMS_ALL_OK | CASCADE | registries/s5r3 unchanged (10-item manifest is historical); s5r3_completion sources available: 19 verified in registries/s5r3 + 7 sources = 26/26 (R3 chain HARD_STOP cascaded the m |

## 6 就绪审计（READINESS_S5R4.tsv，逐条对照『无可做』）

- 在最终 STATE 写入之后运行（U382），READINESS_S5R4.tsv 的 # META 行记录其读取的 STATE 字节数=3424、sha256=1a962c77e13f8c3f1189b7227855bf8826f48b7af84a43badd6cc21de509807c。
- 红点 26/26 MET；OPEN_ITEMS 25 行处置不变；PENDING_RUNS 无（独立重判已产出）；CONSISTENCY（STATE/registry/报告/草稿关键数字）；MAKETEST（R3 结果，不重跑）；PREREG_MATRIX（R3 D016/E2E + S5R4 重判 DIFFS=0）；E2E_CHAINS；REGISTRY_COMPLETION 26/26；SHAKEDOWN FAILS=0。
- 汇总：GAP=0（必须为 0；否则 HARD_STOP 不进入 end 门禁）。

## 7 registry 补齐与 S5R4 registry

- registries/s5r4/s5r3_completion/：补齐 S5R3 应交付但未入清单的 7 项（REJUDGE_S5R3.tsv 内容 = 本轮 REJUDGE_S5R4.tsv，其余 6 项从证据复制：READINESS_S5R3、P05_ACCEPTANCE_MAP_S5R3、REGISTRY_APPLY_DIFF_S5R3、REPORT_CHECK_S5R3、COPY_DIFF_S5R3、ERRATA_S5_R3FINAL），并写 README.md 与 SHA256SUMS.txt。
- S5R3 覆盖对照 26/26：19 项已在 registries/s5r3/ 中（逐项 sha 与 p05-s5r3/SHA256SUMS.txt 一致）+ 7 项由 s5r3_completion 补齐；registries/s5r3/ 与其 SHA256SUMS.txt、p05-s5r3/ 一律不写（sha 不变）。
- registries/s5r4/：本轮 14 项小表 + SHA256SUMS.txt；GATE_S5R4_end.txt 在门禁之后追加并更新清单（附录 B 记录门禁时 N 项与最终 N+1 项）。

## 8 登记表 diff（U384）

- testing/s4test/ISSUE_REGISTRY.md 与 PROJECT_ROADMAP.md：只改动脚本列出的 3 行（ISSUE_REGISTRY D016 行；ROADMAP P05 行与 D016 分条），unified diff 断言通过（ASSERT_ONLY_LISTED_LINES_CHANGED=PASS）；R3→R4 链式 sha 一致（R3 after_sha == R4 before_sha）。
- 详见 $EV/REGISTRY_APPLY_DIFF_S5R4.txt；不改 AGENTS.md。

## 9 签收范围声明草稿 v2

- P05_S5_SIGNOFF_DRAFT_v2.md：标明未签收；范围=F4；make test/E2E 42 点/D016 点族引用 S5R3 结果 + S5R4 独立重判实测 DIFFS=0；转出项 U366–U370/D017/R-P05-0x；已知限制（NV -10 仅 [源码]、Lua REPL 覆盖 cf/fft/kt/vl、S5R2 比较器历史缺陷、S5R3 build 的 PYEXT sha 与 M3b 差在嵌入路径/build-id 未判等价）。
- S5R3 版本 P05_S5_SIGNOFF_DRAFT.md 保留为历史，不改写（sha 不变）。

## 10 事件两张表

### 10.1 表一：越界写入尝试

| 轮次 | 命令 | 目标 | 是否落盘 |
|---|---|---|---|
| s5r4 | 无 | 无（本轮所有写入均在仓库内 $EV/、testing/d003/、checkpoints/p05/） | 不适用 |

### 10.2 表二：工具与脚本事件

| # | 事件 | 处理/影响 |
|---|---|---|
| 1 | start 门禁 v1：RULINGS sha 常量笔误（7dde vs 7de）+ EV 预内容规则把 safe_run 自身创建的 mkdir 行视为先前输出，FAILS=2 | 修正常量与预内容规则；v2 输出保存为 $EV/gate/GATE_S5R4_start.txt_v2_fails1 |
| 2 | start 门禁 v2：EV 预内容规则把上一次 start 门禁自身的输出视为先前证据，FAILS=1 | 允许 GATE_S5R4_start.txt 自身与版本保留 cp；v3 通过 |
| 3 | start 门禁 v3：版本保留 cp 行被预内容规则判为外部命令，FAILS=1 | 允许含 GATE_S5R4_start.txt 的保留命令；v4 FAILS=0（36 项） |
| 4 | 一次裸跑 python3 -m py_compile 生成 testing/d003/stage_s5r4/__pycache__（未经 safe_run，仓库内路径） | 已删除；改为在 safe_run 内运行脚本自检；登记为工具事件（未越界仓库） |
| 5 | s5r4_rejudge_check.py 首跑：summary 解析读 stdout 而非输出 TSV，且 D016 观测键路径写错（KeyError VL_NB9_REF），selftest 2/6 | 改为解析输出 TSV 的 SUMMARY 行、按 observations.py_ref 读参考值；6/6 通过 |
| 6 | 框架事件：本会话无 /tmp/dsh-spill-* 落盘记录 | 无 |

## 11 交付物

复制到 checkpoints/p05/registries/s5r4/ 的小表共 14 项，加 SHA256SUMS.txt；门禁后追加 GATE_S5R4_end.txt 并更新清单：交付物数量=14
1. GATE_S5R4_start.txt
2. PREREG_REJUDGE_S5R4.tsv
3. PREREG_REJUDGE_S5R4.tsv.sha256.txt
4. REJUDGE_S5R4.tsv
5. R3_GATE_RECHECK_S5R4.tsv
6. READINESS_S5R4.tsv
7. P05_ACCEPTANCE_MAP_S5R4.tsv
8. POSCTRL_REJUDGE_S5R4.txt
9. POSCTRL_GATE_S5R4.txt
10. COPY_DIFF_S5R4.txt
11. REGISTRY_APPLY_DIFF_S5R4.txt
12. REPORT_CHECK_S5R4.txt
13. FROZEN_SCRIPTS_S5R4.tsv
14. REGISTRY_EXPECTED_S5R4.txt

## 附录 A（试跑门禁摘要）

- 试跑输出：$EV/shakedown/gate/GATE_S5R4_end.txt（staging 证据根/checkpoints 根/POST_I 起点行完整演练，模拟 commit-i=HEAD，不碰正式路径）；不纳入 SHA256SUMS。
- 试跑结果：COUNTS total=139、FAILS=0、CHECK_CRASHED=0。
- 试跑期 FAIL 归因（U381）：逐项记录在 $EV/shakedown/gate/GATE_S5R4_end.txt 与归档的失败版本中；检查器缺陷在提交 (i) 之前修正，并用同一脚本 sha 重跑至 FAILS=0。

## 附录 B（正式 end 门禁摘要）

- 门禁前占位：正式 end 门禁只跑一次，输出 $EV/gate/GATE_S5R4_end.txt（总断言 ≥78）；门禁后由 s5r4_appendix.py 把失败项/计数摘要追加到本附录末尾（不改本行之前的正文）。

FINAL_STATUS=PENDING_GATE

（FINAL_STATUS=PENDING_GATE）本轮 P05-S5 R4 范围证据已生成，等待 end 门禁；最终状态与收尾句由门禁后追加的附录 C 给出。


- 正式 end 门禁原文摘要（门禁后追加）：COUNTS total=139、FAILS=1、CHECK_CRASHED=0；失败项=SHAKEDOWN_USED_STAGING_ROOTS。
- 门禁脚本 sha256=829f2708601ae55678d00ec8ef46754781ffe12538fd2cd98a126313692fd2c7；门禁时 registry 小表 14 项，门禁后追加 GATE_S5R4_end.txt 并更新清单为 15 项（报告正文交付物数量按门禁时 14 项计数）。

## 附录 C（门禁后追加；只追加，不改正文）

end 门禁正式运行一次：139 项断言，FAILS=1、CHECK_CRASHED=0；失败项=SHAKEDOWN_USED_STAGING_ROOTS。
冻结期规则：不修脚本、不重跑；照实记录并停止。

FINAL_STATUS=INCOMPLETE

本轮未完成 P05-S5 R4 范围，等待用户审核。

- 失败项归因（U381 分类：检查器缺陷，不是数据缺陷）：SHAKEDOWN_USED_STAGING_ROOTS 期望在试跑门禁输出里找到 `STAGING_MODE\tyes`，但门禁记录行的格式是 `RECORD\tSTAGING_MODE\tvalue=yes`（shakedown/gate/GATE_S5R4_end.txt 第 4 行，内容确为 value=yes）；同一次门禁的 SHAKEDOWN_GATE_FAILS_ZERO 读到该输出为 FAILS=0/CHECK_CRASHED=0（PASS），试跑记录 shakedown/SHAKEDOWN_REHEARSAL.txt 也完整（STAGING_EV_ROOT/STAGING_P05_ROOT/POST_I_FROM/STAGED_STEPS）。因此是检查器字符串比较写错，被检数据（试跑门禁输出）正确。
- 为什么试跑没抓到：试跑时该检查走"自身运行中"分支（读 SHAKEDOWN_REHEARSAL.txt 返回 PASS），只有正式门禁才会走读输出文件的分支；同一脚本 sha 的试跑因此覆盖不到该分支。这是本轮试跑覆盖面的缺陷，记入下面事件表。
- 处理（按任务书 §12，冻结期硬规则）：end 门禁正式运行一次后 FAILS=1，不修脚本、不重跑、不放宽/删除检查；照实写 FINAL_STATUS=INCOMPLETE 并停止，等待用户裁决是否开一个最小修正子轮（只改该检查的字符串比较，并重跑试跑覆盖该分支）。

### 附录 C 事件表（门禁后）
| # | 事件 | 处理/影响 |
|---|---|---|
| C1 | 正式 end 门禁 FAILS=1：SHAKEDOWN_USED_STAGING_ROOTS 检查器字符串写错 | 冻结期不修不重跑；FINAL_STATUS=INCOMPLETE；数据正确（试跑输出 STAGING_MODE=value=yes、FAILS=0/CHECK_CRASHED=0） |
| C2 | 本轮 STATE.md 在门禁前写入，其中"正式 end 门禁 FAILS=0"是门禁前预投影（未实测） | 不能事后改 STATE（门禁后只允许写 registries/ 与报告附录）；以本附录 C 的 FINAL_STATUS=INCOMPLETE 为准；下一轮应把 STATE 中的门禁结果改为引用附录 |
| C3 | 门禁后把 GATE_S5R4_end.txt 复制进 registries/s5r4/ 并把该目录清单从 14 项更新为 15 项 | 只写 registries/ 与报告附录，未写 $EV（$EV 最后一次写入仍是 sha_sums） |
| C4 | 冻结期 /tmp 顶层快照：门禁时与 start 记录一致（0 项，sha 01ba4719…） | 无 |
| C5 | 框架/工具事件：一次裸跑 python3 -m py_compile（生成 __pycache__，仓库内路径）已删除；一次 --out /dev/null 的只读调试调用（无实际落盘） | 已在报告事件表与最终答复中披露 |
