# P05-S5 范围声明草稿 v3（未签收）

> 状态：**未签收**。本文件是 P05-S5 范围声明草稿 v3，由 P05-S5 R5 执行者按 U390 编写；签收只由用户在对话中给出。
> 本轮不宣布任何阶段完成或签收。v1（P05_S5_SIGNOFF_DRAFT.md）与 v2（P05_S5_SIGNOFF_DRAFT_v2.md）保留为历史，本文件不改写它们。
> 门禁结果只写：见 P05_S5R5_REPORT.md 附录 C；若附录 C 中 FINAL_STATUS≠COMPLETE，本草稿无效。

## 1 被测树

- 被测冻结树 F4：提交 05097a7，S4/ 树 589e15eb11fcb04e031b524f25a443e7921946cf；S5R3/S5R4/S5R5 的所有运行都基于 F4，S5R5 不重跑 D016/E2E/make test 正式矩阵。
- 未修改 S4/、testing/d003/judge_d003.py（sha256 d2d04145e056…）与历史装置。

## 2 S5 收口测试范围（继承 v2，引用 S5R3/S5R4 实测）

- make test：B 树（37a82e8）与 F4 各两遍（S5R3 在 F4 上重跑），判据 NO_NEW_FAILURE，单元数与日志 Ran N 对账 8/8；结果 NO_NEW_FAILURE，unit_count=265；S5R5 不重跑。
- E2E 42 点（25 注入 + 17 无注入对照）：E2E_OK=25、CONTROL_OK=17，FLAKY/INVALID/HIT_OFF_TARGET/API_SILENT/RETRY_DIFF/RETRY_FAIL 均为 0。
- D016 点族（Python/Lua 公共 API，VL NB=1–4 失败与同对象重试、对照、恢复）：MATCH=33 MISMATCH=0 FLAKY=0（判定行 34：33 MATCH + 1 RECORD）。
- 阳性对照：D016 5/5、E2E 19/19、make test 4/4；独立重判自检 6/6、阳性对照 4/4（S5R4 实测）。
- 独立重判 v2（S5R4 实测）：REJUDGE_S5R4.tsv 的 SUMMARY 为 E2E_ROWS=42 E2E_DIFFS=0、D016_RECORDED_ROWS=34 D016_REJUDGED_ROWS=33 D016_NOT_JUDGED=1 D016_DIFFS=0、DIFFS=0；行覆盖=E2E 42 点全部 SAME、D016 33 个行为点全部 SAME、ROOT_CAUSE_RC 记 NOT_JUDGED_SOURCE_RECORD。

## 3 R5 修正项（相对 S5R4）

- ES5-15：S5R4 正式 end 门禁唯一 1 项失败为检查器字符串缺陷（"STAGING_MODE"+"TAB"+"yes" 对不上 RECORD 行的三段格式）。R5 不改、不重跑 gate_check_s5r4.py，也不重跑 S5R4 的 139 项正式断言；新脚本 s5r5_recheck_staging.py 在 R4 冻结数据上同时用修正逻辑与 R4 原逻辑重判该行：修正逻辑成立、R4 原逻辑得 not_staging（复现 R4 的失败）。重判阳性对照 4/4。
- ES5-16：S5R4 的 STATE 在门禁前写了结果，就绪审计只核对字节/sha 导致内容失真。R5 更正 STATE 并让就绪审计按 U389 扫描 STATE、本草稿与报告正文中的门禁结果字样（三类正则，命中数 0），并核对 STATE 的 S5R4 行与 S5R4 报告附录 C 的 FINAL_STATUS=INCOMPLETE 一致。
- 同类缺陷静态普查：gate_check_s5r4.py 的 139 项断言全部按机制分类（SWEEP_ROWS=139、SELF_BRANCH_ROWS=2、VACUOUS=0），每条字符串匹配/否定匹配断言在 R4 冻结数据上以正确格式重算，未发现空洞通过。
- R5 门禁设计（U388）：不出现依据"是否试跑"或"输出路径是否为自身"的分支；试跑与正式运行只差根路径参数；门禁不读取任何门禁输出文件；试跑输出由门禁之外的 s5r5_shakedown_verify.py 核验，且在提交 (i) 之前完成。

## 4 转出项清单（同 v2）

- U366–U370 转出/登记项：F10 历史因果（S5-B-01）、F8 历史目录未验证（S5-B-02）、S1 报告 11.2 五哈希来源无法判定（S5-B-05..09）、反事实通量与 allzero 设计意图（R-P05-01）、U99/U100（R-P05-02/R-P05-03）。
- D017：非 FMM S4_malloc 分配失败未逐点检查（59 处出现 / CALL 52 / OUT 38 / OUT CALL 31），保持 OPEN，不在 P05 修，不阻塞 P06（U369）。
- R-P05-01 / R-P05-02 / R-P05-03：保持 OPEN，转出 P05，不阻塞 P06（U366、U370）。

## 5 已知限制（原样继承 v2，另加 R5）

- D016 的 NV -10 路径触发不了：NV 只作为对照点（NB=1 成功），-10 路径维持 [源码] 结论，未实测。
- Lua REPL 前端只覆盖 cf/fft/kt/vl 四族（exp 无 REPL 点，因为 REPL 脚本只用真实方法名且 exp 路径由批量前端覆盖）。
- S5R2 比较器历史缺陷 ES5-6：S5R2 的 D016 比较器把预注册标签 ABSENT 与计数 0 直比导致 2 个 MISMATCH；S5R3 用比较器 v2 与 expected_count=0 重跑，S5R2 判定表保留为历史。
- S5R3 build 的 PYEXT sha 与 M3b 对照为 DIFFERENT_OUTSIDE_BUILD_ID：树路径 s5r3 比 m3b 长 1 字节使嵌入路径整体移位，未判等价（Lua 前端 sha IDENTICAL）。
- 范围限 F4 与被测点族；不外推到其它树/布局/材料范围；S5R5 不重跑正式矩阵。
- R5 不重跑 S5R4 的 139 项正式断言，沿用其 138 项原文结论（门禁文件 sha 20bb6ad0…）+ R5 的 1 项修正重判；这是 U386 批准的最小修正，不是对 R4 门禁的重新执行。

## 6 声明

- **未签收**；等待用户审核。S5R3 遗留项已在 S5R4 消解；S5R4 的唯一正式失败项已由 R5 以修正重判处置（U386）。
- 门禁结果只写：见 P05_S5R5_REPORT.md 附录 C；若附录 C 中 FINAL_STATUS≠COMPLETE，本草稿无效。
