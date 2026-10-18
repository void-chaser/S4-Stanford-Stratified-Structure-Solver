# P05-S5 R1 报告（s5r1）：S5 输入只读盘点、分类分流、登记表补丁草案

> 轮次：P05-S5 R1。只读盘点 + 文档写入；未运行 S4 的任何程序（无 make、make test、E2E、d003 矩阵、构建、gdb）。
> 本轮不宣布 P05-S5 或 P05 阶段完成；签收只由用户在对话中给出。

## 1 门禁

- start 门禁：COUNTS	pass=23	fail=0	skip=0	total=23，FAILS=0（GATE_S5R1_start.txt；CHECK_CRASHED=0）。HEAD=59e742d5…f263；HEAD:S4=589e15eb…46cf（F4）；判定器 sha256=d2d04145…09eb；工作区干净。
- 起始文件字节数与 sha256 由脚本断言：RULINGS.tsv 146978 B（d33990ca2312eefc，最大 U363）、ERRATA_9.txt 65771 B（5a07fc22fd796f92，最后 E9-77）、STATE.md 5318 B（dc4c1083bc69284b）、P05_S3_S4_SIGNOFF.md 2077 B（7b5b412a9fa363ad）、P05_S1_S2_SIGNOFF.md 1636 B（b6174b499884a593）、S5_HANDOFF_R9M3D.tsv 1401 B（7adf17662bc47b94）、ISSUE_REGISTRY.md 20720 B（ad17b768c79a3f63）、PROJECT_ROADMAP.md 20905 B（2c8cbe18d479584a）。
- registries/s4r9/M3e/SHA256SUMS.txt 4/4 OK；m3e 证据 SHA256SUMS.txt 23/23 OK；仓库根 registries/ 不存在；/tmp 顶层 0 条目（sha256 e3b0c442…b855）。
- 开工前证据目录与 brief 均不存在（test -e 断言，EV_ABSENT_BEFORE_START / BRIEF_ABSENT_BEFORE_SAVE）。
- end 门禁：见附录 B（冻结期正式单次运行；输出写 $EV/gate/，不纳入清单）。正式运行 39 项中 38 PASS、1 FAIL（EVIDENCE_SUMS_COVERS_ALL：检查器只排除顶层 gate/，未排除 shakedown/gate/；按冻结期规则不修脚本、不重跑，照实记录）。

## 2 勘误 E9-78 / E9-79

- E9-78：M3e end 门禁的两项 POST_I 调用计数 FAIL 是检查器缺陷（gate_check_r9m3e.py 第 244 行把 mkc() 返回元组当可调用对象传入 safe()，TypeError: tuple object is not callable）；根因是试跑期未实跑 end 门禁 POST_I 块。只读复算：提交 (i) 后 chain 6 次（safe_run.log 第 59–64 行）、gate end 1 次（第 65 行）；GATE_R9M3E_end.txt 第 14 行 CALL_LINES_M3E_CHAIN_R9M3E_- 为空。只登记，不重跑 M3e。复算文件 ERRATA_RECHECK_S5R1.txt。
- E9-79：M3e 表一 3 次越界写入尝试（safe_run.log 第 1、2、3 行，均未落盘）的成因是 safe_run 接 bash -c 时外层先展开变量；修正方式见任务书第 2 节第 1 条。只登记，不重跑 M3e。

## 3 输入盘点计数

- A 组：7 行（S5-M3D-01..07，S5-M3D-06 来源按 E9-76 记 U5）
- B 组：9 行（S1/S2 签收范围第 (3) 条四项 + S1 报告 11.2 的五个哈希来源）
- C 组：3 行（D016、R-P05-01、fmm_kottke 除数数值安全；U99/U100 并入 S5-M3D-03）
- D 组：6 行（ISSUE_REGISTRY 的 D003 行与全部含 P05 的行、PROJECT_ROADMAP 的 P05 行）
- 去重前 29 行；合并记录 3 条（消除 4 行）；去重后 25 行（S5_INPUTS_S5R1.tsv；合并关系见 S5_INPUTS_DEDUP_S5R1.txt）。

## 4 分类计数

- REGISTRY_ONLY=5
- NEEDS_TEST=3
- NEEDS_FIX_NEW_DEFECT=1
- RECORD_ONLY_OPEN=6
- NEEDS_USER_RULING=10
- needs_user_ruling=YES 共 12 行；blocks_P06_D004=YES 共 2 行。

## 5 验收映射

- AC-1（每个受影响的 prepare/execute 点有正负对照）：MET
- AC-2（失败后模式/缓存不安装）：MET
- AC-3（Python/Lua 可见失败，恢复重试正确）：NEEDS_USER_RULING
- AC-4（M3a/M3b 的 make test 与 E2E 能否作为 S5 前端与回归证据）：NEEDS_USER_RULING；利弊见 P05_ACCEPTANCE_MAP_S5R1.tsv 与计划草案 Q1。
- 明细见 P05_ACCEPTANCE_MAP_S5R1.tsv；GAP 行 0。

## 6 草案摘要

- P05_S5_REGISTRY_PATCH_DRAFT.md：对 ISSUE_REGISTRY.md 与 PROJECT_ROADMAP.md 的逐条 unified diff 草案（只写不应用），覆盖 D003 状态与关闭范围（引用 P05_S3_S4_SIGNOFF.md 第 2 节原文，不改写）、D016 核对结果（已实施 3e77aa9、Python 文本未实测）、非 FMM S4_malloc 另立登记项（建议 D017）、ES3R4-5/528/1164 与 U99/U100 登记（R-P05-02/R-P05-03）、P05 行状态文字。
- P05_S5_PLAN_DRAFT.md：S5R2 与收口计划草案；NEEDS_TEST 项预注册思路（期望值运行前写入并记录 sha256）、Python/Lua 驱动与预计运行量（约 28 点两遍，若 Q1 需独立复跑追加约 50 次）、Q1..Q8 需用户裁决问题（每条附推荐与理由）。

## 7 事件两张表

### 7.1 表一：越界写入尝试

| # | 命令/脚本 | 目标 | 是否落盘 |
|---|---|---|---|
| 1 | 首次写 s5r1_startgate.py（目标目录当时不存在） | testing/d003/stage_s5r1/s5r1_startgate.py（仓库内） | 否（FileNotFoundError，未生成文件） |

无仓库外写入尝试；/tmp 顶层开工 0 条目、收尾快照见附录 B 记录。

### 7.2 表二：工具与脚本事件

| # | 事件 | 影响 |
|---|---|---|
| 1 | 首次脚本写入因 stage_s5r1 目录不存在而失败（safe_run.log 一条失败命令） | 无文件生成；随后先 mkdir 再写入 |
| 2 | 框架未产生 /tmp/dsh-spill-* 落盘 | 无 |
| 3 | 正式 end 门禁 1 FAIL（EVIDENCE_SUMS_COVERS_ALL）为检查器只排除顶层 gate/、未排除 shakedown/gate/；按冻结期规则未修脚本、未重跑，照实写入附录 B | 不影响其它 38 项；证据清单 34 项全 OK（见附录 B 与 SHA256SUMS） |
| 4 | 报告 git status 行在门禁后更新为提交 (ii) 前快照 | 不改变已校验的数字、派生文字与附录内容 |
| 5 | 门禁后修正两份草案中的禁用字样（否定句曾含阶段完成 / P05-S5 签收的字面），改为不含该字样的表述 | 不改变草案结构与证据引用；报告数字不受影响 |

其余：无裸跑写入、无 heredoc 残留、无仓库内路径拼错（除事件 1）。

## 8 需用户裁决

- AC-3/AC-4：M3a/M3b 的 make test 与 E2E 结果能否作为 S5 前端与回归证据（推荐见 Q1）。
- Q1..Q8：见 P05_S5_PLAN_DRAFT.md 第 5 节（F10/F8 历史输入、反事实通量与 allzero 意图、11.2 五哈希来源、D017 编号、R-P05-02/03 登记）。
- 本轮不自行认定上述任一项。

## 9 交付物

复制到 checkpoints/p05/registries/s5r1/ 的小表（7 项 + 清单本身）：

1. GATE_S5R1_start.txt
2. S5_INPUTS_S5R1.tsv
3. S5_INPUTS_DEDUP_S5R1.txt
4. S5_TRIAGE_S5R1.tsv
5. P05_ACCEPTANCE_MAP_S5R1.tsv
6. REPORT_CHECK_S5R1.txt
7. FROZEN_SCRIPTS_S5R1.tsv
8. SHA256SUMS.txt

## 附录 A（试跑 end 门禁摘要）

- 试跑输出：$EV/shakedown/gate/GATE_S5R1_end.txt（模拟 commit-i；不纳入 SHA256SUMS）。
- COUNTS	pass=39	fail=0	skip=0	total=39
- FAILS=0
- PASS	CHECK_CRASHED_ZERO	expected=0	actual=0
- PASS	POST_I_CALL_COUNT_GATE_S5R1_END	expected=1	actual=1
- PASS	POST_I_CALL_COUNT_S5R1_CHAIN_-	expected=6	actual=6
- PASS	POST_I_CALL_COUNT_S5R1_PREP_ALL	expected=1	actual=1

## 附录 B（正式 end 门禁原文摘要）

```
COUNTS	pass=38	fail=1	skip=0	total=39
FAILS=1
PASS	CHECK_CRASHED_ZERO	expected=0	actual=0
PASS	POST_I_CALL_COUNT_GATE_S5R1_END	expected=1	actual=1
PASS	POST_I_CALL_COUNT_S5R1_CHAIN_-	expected=6	actual=6
PASS	POST_I_CALL_COUNT_S5R1_PREP_ALL	expected=1	actual=1
# FAIL detail lines:
FAIL	EVIDENCE_SUMS_COVERS_ALL	expected=manifest covers every non-gate file	actual=['shakedown/gate/ALL_STATUS_S5R1_end.txt', 'shakedown/gate/GATE_S5R1_end.txt']
```

本轮完成 P05-S5 R1 范围，等待用户审核。

git log -1: 60896371f5d9312930f9a5df30c6b2c424d2da60 P05-S5 R1 (i): brief, errata E9-78/E9-79, STATE, registry patch and plan drafts, frozen s5r1 scripts; awaiting user review
git status --short（提交 (ii) 前快照）: ?? checkpoints/p05/P05_S5R1_REPORT.md; ?? checkpoints/p05/registries/s5r1/
