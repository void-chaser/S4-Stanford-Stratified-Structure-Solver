# P05-S5 R2 报告（s5r2）：裁决入账、S5R1 勘误、D017 清单、登记表落实、D016 公共 API 实测

> 轮次：P05-S5 R2。本轮不宣布 P05-S5 或 P05 阶段完成；签收只由用户在对话中给出。
> 被测树为 F4（05097a7，S4/ 树 589e15eb11fcb04e031b524f25a443e7921946cf）。D016 结论只写：在 F4 上、在该输入下经公共 API 可见失败且恢复正确。

## 1 门禁

- start 门禁：2026-10-18T09:27:21Z，9f537f7c312b2ab7c64d5c0ea82da34e637da5d4（GATE_S5R2_start.txt；CHECK_CRASHED=0）。HEAD=9f537f7c…da5d4；HEAD:S4=589e15eb…46cf（F4）；判定器 sha256=d2d04145…09eb；工作区干净。
- 起始文件字节数与 sha256 由脚本断言：RULINGS.tsv 146978 B（d33990ca2312eefc，最大 U363）、ERRATA_9.txt 67981 B（95b23f21b2e48a1c，最后 E9-79）、STATE.md 3075 B（bdd9668c162832cc）、两份 S5R1 草案 9358/5351 B、S5R1 输入/分类表 7348/6455 B、ISSUE_REGISTRY.md 20720 B（ad17b768c79a3f63）、PROJECT_ROADMAP.md 20905 B（2c8cbe18d479584a）。
- S5R1 小表 SHA256SUMS 7 项 OK；p05-s5r1 证据 SHA256SUMS 34 项 OK（由脚本数出）；仓库根 registries/ 不存在；/tmp 顶层快照 count=0。
- end 门禁：正式运行一次（输出写 $EV/gate/，不纳入清单）；原文摘要见 P05_S5R2_GATE_APPENDIX.md。

## 2 裁决入账（U364–U371，纯追加）

- RULINGS.tsv 追加 U364–U371 共 8 行，原有内容逐字节不变（前缀校验）；最大编号 U371。
- U364：M3a/M3b 的 make test 与 E2E 作为 F4 上历史证据可被 S5 引用；S5R3 在 F4 上重跑一次 make test 与全量 E2E（M3b 42 点加 D016 点）；修复前证据不得称为修复后验证。
- U365：D016 在 S5R2 用 Python 与 Lua 公共 API 实测（VL，n_G=1）；NV 的 -10 路径触发不了，维持 [源码] 结论。
- U366：F10 历史因果、R-P05-01 的反事实通量与 allzero 设计意图保持 OPEN，转出 P05，写入 S5 范围声明，不阻塞。
- U367：F8 历史目录不授权访问，保持未验证。
- U368：S1 报告 11.2 的 5 个哈希来源认定为无法判定，不改写 11.2 与 EVIDENCE.sha256。
- U369：非 FMM S4_malloc 登记为 D017；登记前先只读逐点列出清单。
- U370：ES3R4-5/528/1164 与 U99 登记为 R-P05-02，U100 登记为 R-P05-03；一律写 F4 行号，旧树行号放括号内。
- U371：批准把补丁 v2 应用到 testing/s4test/ISSUE_REGISTRY.md 与 PROJECT_ROADMAP.md；不改 AGENTS.md。
- 原文逐字见 registries/RULINGS.tsv 与 briefs/P05_S5R2_BRIEF.md 第 1 节。

## 3 勘误 ES5-1 至 ES5-5

- ES5-1：S5-B-05/06/07/08 的 locator 由全文第一次出现（359/58/374/389）更正为 S1 报告 11.2 表第 478/479/480/481 行，current_status_text 改为表中哈希原文；S5-B-09（485 行）无误。更正后的 5 行见 ERRATA_S5.txt 与 P05_S5_OPEN_ITEMS.tsv。
- ES5-2：pattern.c:798（B/A）在 F4 为 815；F4 上 shape_get_intersection_area 第 474 行（旧树 528）、fprint_double 第 1178 行（旧树 1164）；B/A/F4 三棵树并列行号由脚本读出，U99 原文不改。
- ES5-3：S5R1 正式门禁后对报告与两份草案做了手工修改并 amend (ii)（reflog：f46ac87 → 9f537f7），未重跑 report_check；本轮只读复核 S5R1 最终版报告，RECHECK_FAILS 见 S5R1_REPORT_RECHECK_S5R2.txt；6089637..9f537f7 两份草案逐行差异同文件第 B 节。
- ES5-4：S5R1 EVIDENCE_SUMS_COVERS_ALL FAIL 是检查器未排除 shakedown/gate/ 的缺陷；复算排除 gate/、shakedown/gate/、tmp/ 后清单覆盖全部文件（S5R1_REPORT_RECHECK_S5R2.txt 第 D 节）；S5R2 检查器把排除列表写入门禁输出。
- ES5-5：非 FMM S4_malloc 的 35–43 说法改为本轮逐点清单：总出现 59、CALL 52、IN 21、OUT 38（OUT CALL 31）。

## 4 D017 清单计数

- 只读来源：git show 05097a7 的 S4/ 全部 .c/.cpp/.h/.hpp（全部标 [源码]，本轮未运行）。
- 总出现数 59；CALL 52；IN 21；OUT 38；OUT 中 CALL 31（即 D017 登记范围），非分配点（注释/定义/声明）7。
- 明细见 D017_S4MALLOC_INVENTORY_S5R2.tsv；ISSUE_REGISTRY.md 新增 D017 行（U369）。

## 5 开放项总表计数

- S5R1 去重后的 25 行逐行落位，见 P05_S5_OPEN_ITEMS.tsv。
- final_disposition 计数：OPEN_TRANSFERRED_OUT=12；RECORD_ONLY_OPEN=6；REGISTERED_D017=1；REGISTERED_R-P05-02=1；REGISTRY_SYNC=2；TEST_S5R2=1；TEST_S5R3=2。
- 6 行 RECORD_ONLY_OPEN（S5-M3D-01/02/05/06/07、S5-C-03）均有 registry_location（ISSUE_REGISTRY.md 的对应行）。

## 6 登记表应用 diff 摘要

- testing/s4test/ISSUE_REGISTRY.md：替换行 41,85,107,113,117；插入 10 行；应用后 sha256=54e204b57d8c2d81。
- PROJECT_ROADMAP.md：替换行 51,145,146；插入 3 行；应用后 sha256=8ff6d491e2efd21d。
- apply_patch_s5r2.py 断言：只改动了 PATCHSPEC 列出的行（ASSERT_ONLY_LISTED_LINES_CHANGED=PASS）；应用前后 sha256 与 unified diff 见 REGISTRY_APPLY_DIFF_S5R2.txt。

## 7 D016 结果（正式两遍）

- 点族：VL NB=1/2/3/4 失败点与同对象重试；VL NB=5/9、Jones NB=1、NV NB=1 对照；同进程新对象 VL NB=9 恢复并与另起进程参考值比较。
- 期望值已预注册（PREREG_D016_S5R2.tsv，状态 INFLUENCED，sha256 已记录），正式运行前写入。
- 正式两遍：MATCH=31、MISMATCH=2、FLAKY=0（判定行数 34）；明细见 D016_VERDICT_S5R2.tsv。
- 事实摘要：Python 抛 RuntimeError（GetPowerFlux: The layer eigensystem could not be solved; no solution was returned）；Lua REPL 打印 GetPoyntingFlux 同一文本（句末带点）；stderr 不出现 Layer eigensystem returned info = 2；恢复对象与另起进程参考值逐元素相对误差 ≤1e-12。
- 结论措辞：在 F4 上、在该输入下经公共 API 可见失败且恢复正确（不写已修好）。

## 8 事件两张表

### 8.1 表一：越界写入尝试

| # | 命令/脚本 | 目标 | 是否落盘 |
|---|---|---|---|
| - | 无 | - | - |

无仓库外写入尝试；/tmp 顶层开工 0 条目，收尾快照见附录 A/门禁记录。

### 8.2 表二：工具与脚本事件

| # | 事件 | 影响 |
|---|---|---|
| 1 | 脚本写入阶段出现 3 次 shell 引号导致的 python -c 失败（NameError / FileNotFoundError，均经 safe_run、无文件生成） | 无产物；随后改用 exec+base64 参数修复 |
| 2 | 早期一次只读检查把 git show 输出重定向到 /dev/null | 非仓库写入，不落盘 |
| 3 | 框架未产生 /tmp/dsh-spill-* 落盘 | 无 |

## 9 下一轮（S5R3）建议

- 在 F4 上重跑一次 make test 与全量 E2E（M3b 42 点加 D016 点），作为 S5 收口的修复后验证（U364）；修复前证据不得称为修复后验证。
- 就绪审计：F4 树/判定器/证据清单/STATE/registries/报告一致；AC-3/AC-4 最终映射。
- 不宣布阶段完成；签收只由用户在对话中给出。

## 10 交付物

复制到 checkpoints/p05/registries/s5r2/ 的小表（11 项 + 清单本身，共 12 项，与 SHA256SUMS 项数一致）：

1. GATE_S5R2_start.txt
2. ERRATA_S5.txt
3. D017_S4MALLOC_INVENTORY_S5R2.tsv
4. PREREG_D016_S5R2.tsv
5. PREREG_D016_S5R2.tsv.sha256.txt
6. D016_VERDICT_S5R2.tsv
7. D016_TRACE_S5R2.md
8. REGISTRY_APPLY_DIFF_S5R2.txt
9. S5R1_REPORT_RECHECK_S5R2.txt
10. REPORT_CHECK_S5R2.txt
11. FROZEN_SCRIPTS_S5R2.tsv
12. SHA256SUMS.txt

## 附录 A（试跑门禁摘要）

- 试跑输出：$EV/shakedown/gate/GATE_S5R2_end.txt（模拟 commit-i；不纳入 SHA256SUMS）。
- COUNTS	pass=46	fail=0	skip=0	total=46
- FAILS=0
- PASS	CHECK_CRASHED_ZERO	expected=0	actual=0
- PASS	POST_I_CALL_COUNT_GATE_S5R2_END	expected=1	actual=1
- PASS	POST_I_CALL_COUNT_S5R2_CHAIN_-	expected=6	actual=6

## 附录 B（正式 end 门禁原文摘要）

见 P05_S5R2_GATE_APPENDIX.md（由 s5r2_appendix.py 从正式门禁输出生成；报告正文不内嵌门禁结果）。

本轮已完成 P05-S5 R2 范围，等待用户审核。

git log -1: 8e76a2a9f375604d185e718df1949ce2c8678b73 P05-S5 R2 (i): rulings U364-U371, errata ES5-1..5, D017 inventory prereg, registry patch v2 applied, open items, STATE, frozen s5r2 scripts; awaiting user review
git status --short: (clean)
