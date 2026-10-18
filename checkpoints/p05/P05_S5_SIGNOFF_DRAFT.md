# P05-S5 范围声明草稿（未签收）

> 状态：**未签收**。本文件是 P05-S5 范围声明草稿，由 P05-S5 R3 执行者按 U377 编写；签收只由用户在对话中给出。
> 本轮不宣布 P05-S5 或 P05 完成。

## 1 被测树

- 被测冻结树 F4：提交 05097a7，S4/ 树 589e15eb11fcb04e031b524f25a443e7921946cf；S5R3 的所有运行都在 F4 上。
- 未修改 S4/、testing/d003/judge_d003.py（sha256 d2d04145e056…）与历史装置。

## 2 S5 收口测试范围（S5R3 在 F4 上重跑）

- make test：B 树（37a82e8）与 F4 各两遍，判据 NO_NEW_FAILURE，单元数与日志 Ran N 对账；结果 NO_NEW_FAILURE，unit_count=265。
- E2E 42 点（25 注入 + 17 无注入对照，M3b 点族原样）：E2E_OK=25、CONTROL_OK=17、FLAKY/INVALID/HIT_OFF_TARGET/API_SILENT/RETRY_DIFF/RETRY_FAIL 均为 0。
- D016 点族（Python/Lua 公共 API，VL NB=1–4 失败与同对象重试、对照、恢复）：MATCH=33 MISMATCH=0 FLAKY=0（判定行 34：33 MATCH + 1 RECORD）。
- 阳性对照：D016 5/5、E2E 19/19、make test 4/4；独立重判 DIFFS=0。

## 3 转出项清单

- U366–U370 转出/登记项：F10 历史因果（S5-B-01）、F8 历史目录未验证（S5-B-02）、S1 报告 11.2 五哈希来源无法判定（S5-B-05..09）、反事实通量与 allzero 设计意图（R-P05-01）、U99/U100（R-P05-02/R-P05-03）。
- D017：非 FMM S4_malloc 分配失败未逐点检查（59 处出现 / CALL 52 / OUT 38 / OUT CALL 31），保持 OPEN，不在 P05 修，不阻塞 P06（U369）。
- R-P05-01 / R-P05-02 / R-P05-03：保持 OPEN，转出 P05，不阻塞 P06（U366、U370）。

## 4 已知限制

- D016 的 NV -10 路径触发不了：NV 只作为对照点（NB=1 成功），-10 路径维持 [源码] 结论，未实测。
- Lua REPL 前端只覆盖 cf/fft/kt/vl 四族（exp 无 REPL 点，因为 REPL 脚本只用真实方法名且 exp 路径由批量前端覆盖）。
- ES5-6 历史缺陷：S5R2 的 D016 比较器把预注册标签 ABSENT 与计数 0 直比导致 2 个 MISMATCH；S5R3 用比较器 v2 与 expected_count=0 重跑，S5R2 判定表保留为历史。
- 范围限 F4 与被测点族；不外推到其它树/布局/材料范围。

## 5 声明

- **未签收**；等待用户审核。

