# P05-S5 范围声明草稿 v2（未签收）

> 状态：**未签收**。本文件是 P05-S5 范围声明草稿 v2，由 P05-S5 R4 执行者按 U383 编写；签收只由用户在对话中给出。
> 本轮不宣布任何阶段完成或签收。v1（P05_S5_SIGNOFF_DRAFT.md）保留为历史，本文件不改写它。

## 1 被测树

- 被测冻结树 F4：提交 05097a7，S4/ 树 589e15eb11fcb04e031b524f25a443e7921946cf；S5R3/S5R4 的所有运行都基于 F4，S5R4 不重跑正式矩阵（U385）。
- 未修改 S4/、testing/d003/judge_d003.py（sha256 d2d04145e056…）与历史装置。

## 2 S5 收口测试范围

- make test：B 树（37a82e8）与 F4 各两遍（S5R3 在 F4 上重跑），判据 NO_NEW_FAILURE，单元数与日志 Ran N 对账 8/8；结果 NO_NEW_FAILURE，unit_count=265；S5R4 不重跑（U385）。
- E2E 42 点（25 注入 + 17 无注入对照，M3b 点族原样）：E2E_OK=25、CONTROL_OK=17、FLAKY/INVALID/HIT_OFF_TARGET/API_SILENT/RETRY_DIFF/RETRY_FAIL 均为 0。
- D016 点族（Python/Lua 公共 API，VL NB=1–4 失败与同对象重试、对照、恢复）：MATCH=33 MISMATCH=0 FLAKY=0（判定行 34：33 MATCH + 1 RECORD）。
- 阳性对照：D016 5/5、E2E 19/19、make test 4/4；独立重判自检 6/6、阳性对照 4/4。
- **独立重判 v2（S5R4 实测）**：REJUDGE_S5R4.tsv 的 SUMMARY 为 E2E_ROWS=42 E2E_DIFFS=0、D016_RECORDED_ROWS=34 D016_REJUDGED_ROWS=33 D016_NOT_JUDGED=1 D016_DIFFS=0、DIFFS=0；行覆盖=E2E 42 点全部 SAME、D016 33 个行为点全部 SAME、ROOT_CAUSE_RC 记 NOT_JUDGED_SOURCE_RECORD（[源码] RECORD，不在预注册中）。

## 3 S5R4 修正项（相对 S5R3）

- 独立重判：S5R3 rejudge 崩溃（ES5-9）已由 rejudge_s5r4.py 重写并正式产出（U379）。
- 门禁 5 项检查器缺陷（ES5-10）：RULINGS 注释行、FROZEN mode 标注、git status strip、D016 表头行、CALIB SUMMARY 行；S5R4 gate_check_s5r4.py 修正并逐项配落盘变异阳性对照（U378）。
- 就绪审计：改为在最终 STATE 之后运行并记录 STATE 字节/sha，GAP=0（U382）。
- registry 补齐：registries/s5r4/s5r3_completion/ 补齐 S5R3 应交付的 7 项，S5R3 覆盖 26/26（U380）。
- 试跑门禁：staging 完整演练达到 FAILS=0/CHECK_CRASHED=0（U381）。

## 4 转出项清单

- U366–U370 转出/登记项：F10 历史因果（S5-B-01）、F8 历史目录未验证（S5-B-02）、S1 报告 11.2 五哈希来源无法判定（S5-B-05..09）、反事实通量与 allzero 设计意图（R-P05-01）、U99/U100（R-P05-02/R-P05-03）。
- D017：非 FMM S4_malloc 分配失败未逐点检查（59 处出现 / CALL 52 / OUT 38 / OUT CALL 31），保持 OPEN，不在 P05 修，不阻塞 P06（U369）。
- R-P05-01 / R-P05-02 / R-P05-03：保持 OPEN，转出 P05，不阻塞 P06（U366、U370）。

## 5 已知限制

- D016 的 NV -10 路径触发不了：NV 只作为对照点（NB=1 成功），-10 路径维持 [源码] 结论，未实测。
- Lua REPL 前端只覆盖 cf/fft/kt/vl 四族（exp 无 REPL 点，因为 REPL 脚本只用真实方法名且 exp 路径由批量前端覆盖）。
- S5R2 比较器历史缺陷 ES5-6：S5R2 的 D016 比较器把预注册标签 ABSENT 与计数 0 直比导致 2 个 MISMATCH；S5R3 用比较器 v2 与 expected_count=0 重跑，S5R2 判定表保留为历史。
- S5R3 build 的 PYEXT sha 与 M3b 对照为 DIFFERENT_OUTSIDE_BUILD_ID：树路径 s5r3 比 m3b 长 1 字节使嵌入路径整体移位，未判等价（Lua 前端 sha IDENTICAL）。
- 范围限 F4 与被测点族；不外推到其它树/布局/材料范围；S5R4 不重跑正式矩阵（U385）。

## 6 声明

- **未签收**；等待用户审核。S5R3 遗留项已在 S5R4 消解，readiness GAP=0。

