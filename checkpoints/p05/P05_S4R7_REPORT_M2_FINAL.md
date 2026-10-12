# P05-S4 R7 M2 里程碑报告(M2a + M2b run7)

**状态:M2a 与 M2b run7 全部完成,无 MISMATCH、无 FLAKY、无 VALUE_DRIFT、无 ENV_DRIFT。M2 里程碑已完成(R7 范围中的 M2)。本报告不宣布任何阶段完成或签收。P05-S3、P05-S4 未签收。S4/ 未修改。本轮未完成 R7 范围(M3 未开始),等待用户审核。**

规则依据:AGENTS.md;R7 任务书;续 1–8 任务书(CONT5、CONT6、CONT6_ADD1、CONT7、CONT8、CONT8_ADD1);裁决 `checkpoints/p05/registries/RULINGS.tsv`(U1–U78);勘误 `checkpoints/p05/registries/s4r7/ERRATA_7.txt`(E7-1 至 E7-35)。

---

## 1. 结论摘要

| 项 | 结果 |
|---|---|
| M2a(G2b、G3、G4;run4) | 两遍全部 MATCH(见 `P05_S4R7_REPORT_M2.md`,本段未改) |
| M2b(run7):CTRL_SEAM、G2c、G1、G2a | 两遍全部通过;MISMATCH 0;FLAKY 0;F 与 F2 五项相等 |
| 22 个 INVALID 点(G1) | 两遍各 44 行 NOT_REACHED_AS_EXPECTED(22 点 × F、F2),hit 全为 0 |
| 数值对照(历史表,G1、G2c、G2a) | 408 点比较,VALUE_DRIFT 0 |
| ENV_DRIFT(G1、G2c、G2a) | 204 点,env_drift 0,absent 0 |
| 报告数字核对(`check_report_counts_r7.py`) | checks_failed 0 |

---

## 2. M2b run7 结果

来源:`REGRESS_R7_M2b_run7.tsv`、`M2B_SUMMARY_R7_run7.txt`(证据目录,不提交)。

| 组 | 遍 | 行数 | MATCH | NOT_REACHED_AS_EXPECTED | MISMATCH | FLAKY | F≠F2 | 状态 |
|---|---|---|---|---|---|---|---|---|
| CTRL_SEAM | 1 | 4 | 4 | 0 | 0 | 0 | 0 | OK |
| CTRL_SEAM | 2 | 4 | 4 | 0 | 0 | 0 | 0 | OK |
| G2c | 1 | 60 | 60 | 0 | 0 | 0 | 0 | OK |
| G2c | 2 | 60 | 60 | 0 | 0 | 0 | 0 | OK |
| G1 | 1 | 298 | 254 | 44 | 0 | 0 | 0 | OK |
| G1 | 2 | 298 | 254 | 44 | 0 | 0 | 0 | OK |
| G2a | 1 | 50 | 50 | 0 | 0 | 0 | 0 | OK |
| G2a | 2 | 50 | 50 | 0 | 0 | 0 | 0 | OK |

汇总:`total MISMATCH rows: 0`,`stopped after group: none`。

G1 的 254 MATCH 由 238 个注入行与 16 个对照行(CTL-*)组成。对照行 16/16 CONTROL_OK。

**G2c-control(6 行)**:按 U65(a) 记为 NOT_RUN_REGISTRY_ERROR,不计入上表,不作为 MISMATCH。其 v2 登记的 mode(addf、b2buf、fmmret)不是驱动接受的 FMM 模式。

**CTRL_SEAM(4 行)**:按 U65(b) 的新登记运行(seamF-F、seamF-F2、fmmret-F、fmmret-F2;mode fft;无注入),4/4 CONTROL_OK,两遍。

---

## 3. 22 个 INVALID 点的 hit(G1)

来源:`RESULTS_R7_G1_pass1_run7.tsv`、`RESULTS_R7_G1_pass2_run7.tsv`(只读计数)。

- 22 个点(44 行:F 与 F2,两遍各 44 行)全部 `expected = INVALID_NOT_REACHED`、`class = INVALID`、`verdict = NOT_REACHED_AS_EXPECTED`。
- 这 44 行的 **hit 全为 0**,rc 为 1,rc1 为 0。reason 为 "injection never reached (hit=0)"。
- 没有任何 INVALID_NOT_REACHED 点 hit = 1。U58 的分类条款(hit = 1)不需要触发。

与 run5、run6 对比:run5 中这些点 hit = 1(因 NTH 缺陷,注入落在第 1 次调用,见 E7-32);run6 中 hit 已为 0 但有 16 个对照错误(E7-33)。run7 中两个缺陷都已修复。

---

## 4. F 与 F2 差异

- 每组每遍,F 与 F2 在 class、rc、rc1、rc2、hit 五项上逐点比较(经 `compare_trees_r7.base_id` 配对,U66):**不相等的点 0**(M2b 汇总 F_vs_F2_unequal_points 全为 0)。
- 每组每遍 FLAKY 为 0(pass1 与 pass2 的 class、verdict、rc、rc1、rc2、hit 全部一致)。

---

## 5. 数值对照与 ENV_DRIFT

**数值对照(VALUE_DRIFT,U71b)**:`VALUES_VS_HISTORY_run7.tsv`:408 个比较点(G1、G2c、G2a,两遍),**VALUE_DRIFT 0,MISSING 0**。历史来源:G1 `RESULTS_R3.tsv`、G2c `REGRESS_R4.tsv`、G2a `RESULTS_R4.tsv`(F 行,rc、rc1、rc2、hit)。

**ENV_DRIFT(U72,按组)**:`ENV_DRIFT_R7_M2b_run7.tsv`:204 点(G1、G2c、G2a),**env_drift 0,absent 0,missing_groups none**。

**注:** run5 的数值对照(VALUE_DRIFT 69,全部 G1)与 run5 的 ENV_DRIFT(env_drift 47)是两个不同检查的结果;二者都在 run5 作废后不再引用。

---

## 6. G2a 与 R4 的比较

- G2a(seam 请求,50 行,两遍)在 run7 中**全部 MATCH**。它是 M2b 中第一次完整运行(run5、run6 都在 G1 停止)。
- G2a 的历史对照:`RESULTS_R4.tsv` 的 F 行(rc_p1、rc1_p1、rc2_p1、hit_p1)。VALUE_DRIFT 对 G2a 为 0。
- seam 驱动与 R4 的比较(`CHECK_DRIVERS_VS_R4_R7_run5.tsv`):seamF-F 与 fmmret-F 的库 sha256 与驱动 sha256 与 R4 **SAME**(`checkpoints/p05/registries/s4r4/LIBS_R4.tsv`,U64)。seamF-F2 与 fmmret-F2 无 R4 对照。

---

## 7. 修复与作废的运行(本里程碑的过程)

| 运行 | 结果 | 处理 | 依据 |
|---|---|---|---|
| run5 | G1 在 G1 停止;注入未设 NTH | HARNESS_INVALID,不计入 M2 | U69、E7-32 |
| run6 | G1 在 G1 停止;16 行对照 request "none" 经 build_env 变成 INJECT=none;G2c twice 点无 TWICE | HARNESS_INVALID(对照);G2c 路线登记错误 | U73、U74、E7-33、E7-34 |
| run7 | 四组完整运行,MISMATCH 0 | **M2 正式结果** | U76 |

run5、run6 的文件保留在证据目录(U17),不计入 M2。

**修复内容(均不改期望,不改 v2、判定器与历史装置):**
- 编排脚本 `run_m2b_all_r7.py`:G1、G2c、G2a 的环境经 `matrix_r2.build_env`(U71a);汇总文件名带 run 标签;对照以 point id 的 `CTL-` 前缀识别(U75b);G2a 的 request 只取 F 行(冲突则拒绝)。
- 登记表 `REGISTRY_S4_PRE_R7_M2_ADD_v3.tsv`(U75a、U77):G2c route 与 twice_env 由 `run_r3_sweep.route_of` 推导;G1 对照行 request、nth 设为 `-`、route 设为 `control`。与 ADD_v2 的关键列差异 0(`KEY_COLUMNS_V3_VS_V2.txt`,U78)。环境列差异 92 格(G2c route 30、G2c twice_env 30、G1 request 16、G1 route 16、G1 nth 0)。
- 独立环境断言 `expected_env_independent_r7.py`(U75b):由 point id 与历史规则推导期望环境,不读 ADD;dry-run 逐行比较,失败计入无法解析。

---

## 8. 违规披露

### 表一:越界写入尝试(命令自身写了仓库外路径)

本段无。

### 表二:工具/脚本事件

| 轮次 | 事件 | 是否落盘 |
|---|---|---|
| 续 6–8 | run5 编排脚本仍有 NTH 缺陷,经数值对照发现后作废(非违规,是 harness 缺陷) | 是(run5 文件保留,U17) |
| 续 7 | 复制脚本 `copy_m2b_run6_prep_r7.py` 的目标文件在 registries 中已存在,来源未记录;sha256 与证据一致 | 是(已在 run6 报告表二登记) |
| 续 8 | dry-run 第一次与第二次失败(`DRYRUN_R7_M2b_run7.txt` unparseable 30,`run7b` unparseable 14),保留为证据 | 是(合规路径) |
| 续 8 | 第一次 dry-run 的输出文件名与已有文件冲突,被 U17 拒绝;改用 `_final` 名称 | 否(拒绝未写入) |
| 续 8 | 多次 `grep` 输出过量(超过 250 行),未用于计数 | 否(只读) |
| 续 8 | 手工写 `REPORT_COUNTS_DRAFT_run7.txt` 的数字(由脚本核对) | 是(证据目录,合规) |
| 续 8 | 报告草稿的数字由核对脚本逐项核对,checks_failed 0 | 否 |

说明:本段没有越界写入(表一为空)。表二的事件均在仓库内或被拒绝,已如实列出。

---

## 9. 本段未做的事

- 未进入 M3(按 U63,M3 在 M2 里程碑之后另发任务书);
- 未宣布 P05-S3、P05-S4 签收(按 U62,签收由用户在对话中给出);
- 未修改 S4/、判定器、历史装置(`matrix_r2.py`、`run_r3_sweep.py`、`run_r4_regress.py`、`run_m2_r7.py` 均只导入)。

---

## 10. 需要用户裁决的事项

1. **P05-S3 是否签收**(U47、U62)。M2 里程碑已完成,签收决定由用户在对话中给出。
2. **M3 是否开工**(U63):G5、G6 状态判定、U38 分类、收尾报告。
3. **RP-R6d-1 的状态**:只依据 M1,措辞不变(见下节)。
4. **run5、run6 的作废结论**(U69、U73、U74)是否接受。

## 11. RP-R6d-1 的状态(只依据 M1,措辞不变)

RP-R6d-1(RNV1 注入)的状态只依据 M1:F2 注入点 REPORTED_FAILURE 63/63(两遍),F 注入点 CRASH 27/27(两遍)(U48、E7-13)。M2 的数据不计入 RP-R6d-1 的计数。

---

## 12. 勘误与裁决索引

- E7-23 至 E7-35(`checkpoints/p05/registries/s4r7/ERRATA_7.txt`)。
- U54 至 U78(`checkpoints/p05/registries/RULINGS.tsv`)。
- 每个数字由 `check_report_counts_r7.py` 核对(见本报告末段)。

---

本轮未完成 R7 范围(M2 已完成;M3 未开始),等待用户审核。P05-S3、P05-S4 未签收。

COUNT CTRL_SEAM_MATCH_pass1 = 4
COUNT CTRL_SEAM_MATCH_pass2 = 4
COUNT G2c_MATCH_pass1 = 60
COUNT G2c_MATCH_pass2 = 60
COUNT G1_MATCH_pass1 = 254
COUNT G1_MATCH_pass2 = 254
COUNT G1_NOT_REACHED_pass1 = 44
COUNT G1_NOT_REACHED_pass2 = 44
COUNT G1_MISMATCH_pass1 = 0
COUNT G1_MISMATCH_pass2 = 0
COUNT G2a_MATCH_pass1 = 50
COUNT G2a_MATCH_pass2 = 50
COUNT FLAKY_total = 0
COUNT MISMATCH_total = 0
COUNT VALUE_DRIFT_total = 0
COUNT ENV_DRIFT_total = 0
COUNT ENV_absent_total = 0
COUNT points_value_compared = 408
COUNT INVALID_hit_nonzero = 0

---

附:提交时的 git log -3(写报告时的 HEAD 之前三条):

```
359bf65 P05-S4 R7 cont8 prep complete: ADD v3 accepted (U77), independent env assertion, dry-run OK. awaiting user review
acd52c4 P05-S4 R7 cont8 prep (partial): ERRATA E7-33/34, rulings U73-U76, ADD v3 generator; ADD v3 diff counts differ from brief 2.1, awaiting user review; run7 not run
0432234 P05-S4 R7 run6 stop report (G1 CTL harness error) and cont8 brief. awaiting user review
```

附:写报告时的 git status --short:`?? checkpoints/p05/P05_S4R7_REPORT_M2_FINAL.md` 与 `?? testing/d003/stage_s4r7/check_report_counts_r7.py`(本报告与核对脚本,待提交)。
