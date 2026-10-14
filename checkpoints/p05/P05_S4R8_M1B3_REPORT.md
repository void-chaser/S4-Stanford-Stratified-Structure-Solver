# P05-S4 R8 M1b3 报告（r8m1b3）：M1b 补充预注册与 342 行补跑

> 本轮属于 P05-S4 子轮次 R8。证据目录 `checkpoints/p05/evidence/p05-s4r8/m1b3/`（不提交）。小型结果表与清单 `checkpoints/p05/registries/s4r8/M1b/r8m1b3/`（`SHA256SUMS.txt`）。
> 本报告不宣布任何阶段完成。P05-S4 未签收，本轮结论仅为子轮次事实记录。

## 0. 用户裁决（RULINGS.tsv，U205–U208）

| 编号 | 内容要点 |
|---|---|
| U205 | 采纳 M1b2 方案 A：补充预注册覆盖 ENV_AUDIT 中 audit_verdict ≠ ENV_AGREE 的 342 行（G1 282 + G2c 60），沿用 U203 约束，结果单独成表，不覆盖 M1b1。 |
| U206 | M1b1 的 50 行 SILENT_SWALLOW（F2 25 + F3 25，R7 inj_call=2 的 twice 点）判为缺 S4FMM_NTH 的环境假象，不进红点台账。 |
| U207 | 补跑的 inj_call 只取 R7 ADD_v3；real 只按 `real_of`；env 等于 `expected_env_from_history` 返回值，逐键比较；三项不从期望 rc 反推；每次调用的实际 FMM_*/S4FMM_* 写入 `env_as_run`。 |
| U208 | M1c 环境以 R7 调用日志 `env_as_run` 为准，本轮补交核对表；440/440 一致则 M1c 在 r8m1c1 单独执行，本轮不跑 M1c。 |

## 1. 开工

- HEAD = `a26b43dd2a77c62b9aec2e937bc7adad14996ef3`；`HEAD:S4` = `6cff923a02baf19e01966b2339755cbf3a5deeef`（F3）；判定器 sha256 = `d2d04145…209eb`；开工 `git status --short` 为空。
- 新增 `testing/d003/stage_s4/gate_r8m1b3.sh`、`gate_check_r8m1b3.py`、`gate_allow_r8m1b3_start.txt`，参照 `gate_r8m1b2.sh` 新写，未改它。start 门禁 `GATE_R8_M1b3_START.txt` FAILS=0。
- r8m1b1 与 r8m1b2 的 SHA256SUMS 均经 `sha256sum -c` 全部 OK（9 与 6 个文件），文件列表先排序比较。
- 开工根目录临时区：0 条目，sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。

## 2. 追加记录

- `RULINGS.tsv` 追加 U205–U208（5 列，前缀逐字节不变）。
- `ERRATA_8.txt` 追加 E8-78（(a)–(e)，与任务书 §3 一致；(c) 补充了核对表编号）。

## 3. M1c 调用日志核对（只读，未跑驱动）

- 脚本 `testing/d003/stage_s4/check_m1c_envlog_r8m1b3.py` → `ENV_LOGCHECK_M1C_R8_M1b3.tsv`。
- 对 `REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv` 的 440 行，与 R7 `M3_F2_STATE_R6c_pass1/2`、`M3_F2_STATE_SEAM_R6c_pass1/2` 中同一基础 id 的 `env_as_run` 比较（只比 FMM_*/S4FMM_*，排除 S4FMM_DUMP*）。
- 结果：**440/440 AGREE**，无 DIFF、无 NO_LOG、无 LOG_INCONSISTENT。与规划者开工前预期一致。
- M1c 本轮不执行，留待 r8m1c1（U208）。

## 4. 补充预注册（运行前冻结）

- 脚本 `make_prereg_supp_r8m1b3.py` → `PREREG_SUPP_R8_M1b3.tsv`，sha256 `712a5547d1257d456b295281e7df00642a49d8f9c4ed97210502127a50985738`，342 行，20 列。
- 选取：ENV_AUDIT 中 audit_verdict ≠ ENV_AGREE，恰为 342 行（G1 F2 141、G1 F3 141、G2c F2 30、G2c F3 30）。
- 来源：driver 与 driver_sha256 取自 M1a6 预注册（G1 `d003-F2/F3-plain`，G2c `d003plan-F2/F3-plain`）并与 DRIVERS 清单核对；env 取自 `expected_env_from_history`，与 ENV_AUDIT `hist_call_env` 逐键一致；inj_call 取自 ADD_v3；real 取自 `run_m2_r7.real_of`（导入）；expected_* 取自 R7 `RESULTS_R7_<G1|G2c>_pass1_run7.tsv` 的 F2 行，pass2 逐字段一致（否则停止）；comparison_contract 沿用 M1a6；status = INFLUENCED；expect_source 为 R7 文件与物理行号。
- 分布核对：G1 每棵树 REPORTED_FAILURE 119、预期未命中 22；inj_call=2 为 35（25 REPORTED_FAILURE + 10 未命中）；G2c 每棵树 REPORTED_FAILURE 30。与预登记一致。
- 字段名说明：任务书写"INVALID 22"，R7 字段值为 `INVALID_NOT_REACHED`（verdict 列为 `INVALID`）。数字 22 不变，只修正了比较时的字段值拼写（见 §8 工具事件表）。
- 预注册 `status` 为 INFLUENCED；未读取任何 M1b1 观察结果文件（脚本运行前用 grep 确认）。

## 5. 预检与补跑

- 脚本 `run_supp_r8m1b3.py`，导入 `judge_d003`（sha256 未变，未修改）。
- 预检（先于任何驱动运行）：预注册 sha256 与冻结值一致；判定器 sha 一致；342 行全部 driver 名存在于 DRIVERS 清单、驱动文件 sha 与清单一致；每行 env 与 `expected_env_from_history` 逐键一致；real 与 `real_of` 一致。`PREFLIGHT_OK rows=342 drivers=4`。
- 运行：两遍严格串行，**684 次物理调用**（脚本断言 = 684），清除继承的 FMM_* 与 S4FMM_* 后按行设置。驱动 GRID `pattern both 4 3`，超时 120 s（与 M1b1 运行器一致）。
- 判类：`judge_d003.classify(run_rc, rc1, rc2, hit, control=False, real=real, inj_call=inj_call)`。
- 比较：`evaluate_verdict` 在新脚本中重写，分支与 `plan_and_run_m1b_r8m1b1.py:75-115` 逐行对应（NOT_REACHED_AS_EXPECTED 对应原 87–90 行，REPORTED_FAILURE/CRASH/SILENT_SWALLOW 对应 102–111 行，回退对应 113–115 行）。
- 驱动执行证据：342 行两遍的 stdout 均含 `S4FMM DRIVER` 行（0 缺失）；每行的 `S4FMM HITCOUNT` 打印存在（342/342）。hit 数值：298 行 hit=1，44 行 hit=0。
- 结果表 `RESULTS_SUPP_R8_M1b3.tsv`：env_as_run、inj_call、real、两遍事实与类别、verdict、pass_consistent 齐全。独立复核：结果表的 (group, point_id, tree, env, inj_call, real) 与预注册 342 行逐行一致。

## 6. 汇总

### 6.1 VERDICT_SUPP_R8_M1b3（342 行）

| 组 | 树 | 行 | MATCH | NOT_REACHED_AS_EXPECTED | MISMATCH | FLAKY | CRASH | 非对照 SILENT_SWALLOW |
|---|---|---|---|---|---|---|---|---|
| G1 | F2 | 141 | 119 | 22 | 0 | 0 | 0 | 0 |
| G1 | F3 | 141 | 119 | 22 | 0 | 0 | 0 | 0 |
| G2c | F2 | 30 | 30 | 0 | 0 | 0 | 0 | 0 |
| G2c | F3 | 30 | 30 | 0 | 0 | 0 | 0 | 0 |

- 两遍一致（pass_consistent = YES）342/342；FLAKY 0。
- 补跑中 MISMATCH、CRASH、非对照 SILENT_SWALLOW 均为 0。上表全部是事实计数，不表示修复效果（AGENTS.md §5）。

### 6.2 CROSSWALK_M1B1_SUPP_R8_M1b3（342 行，M1b1 类别 → 补跑类别）

| M1b1 类别（p1） | 补跑类别（p1） | 行数 | 说明 |
|---|---|---|---|
| REPORTED_FAILURE | REPORTED_FAILURE | 248 | 类别一致 |
| REPORTED_FAILURE | INVALID | 44 | M1b1 期望 REPORTED_FAILURE 与实测不符；补跑按 INVALID_NOT_REACHED 判为未命中（MATCH） |
| **SILENT_SWALLOW** | **REPORTED_FAILURE** | **50** | U206 所述原 50 行：正确环境（含 NTH 与 TWICE=slab）下为 REPORTED_FAILURE |

- 原 50 行 SILENT_SWALLOW 在正确环境下：全部为 `S4FMM_TWICE=slab`、inj_call=2 的 twice 点，补跑 rc1 为 20、hit=1，类别 REPORTED_FAILURE，verdict MATCH。与 U206 结论一致。
- 注意：44 行的 M1b1 "期望 INVALID、实测 REPORTED_FAILURE" 方向与 E8-78(a) 所述一致；补跑把这 44 行变为未命中（INVALID）。

### 6.3 EFFECTIVE_M1B_R8_M1b3（830 行）

| 来源 | 行数 | 说明 |
|---|---|---|
| M1b1 ENV_AGREE | 482 | 采用 M1b1 结果 |
| SUPP_R8_M1b3 | 342 | 采用补跑结果 |
| M1b1 NOT_RUN（G2c_control） | 6 | 保持 NOT_RUN |
| **合计** | **830** | |

- 任务书写"488 行 ENV_AGREE 用 M1b1"。按 830 行的分类，ENV_AGREE 源行为 482，其余 6 行是 G2c_control 的 NOT_RUN，二者合计 488。两种口径相加都是 830；本报告采用"482 + 6 NOT_RUN"的分拆，数字差异记入 §8 表二。
- 有效判定汇总（830 行）：MATCH 780，NOT_REACHED_AS_EXPECTED 44，MISMATCH 0，FLAKY 0，NOT_RUN 6。

## 7. 运行的范围外核对

- 本轮**未运行 M1c**（U208）。M1c 环境核对 440/440 AGREE，可进入 r8m1c1 的审核。
- 本轮未修改 `S4/`、`AGENTS.md`、`judge_d003.py`，未修改 testing/d003 下任何已提交脚本。新增脚本均带 r8m1b3 命名（`make_prereg_supp_r8m1b3.py`、`check_m1c_envlog_r8m1b3.py`、`run_supp_r8m1b3.py`、`summarize_r8m1b3.py`、`gate_*r8m1b3*`、`append_*r8m1b3.sh`、`copy_registries_r8m1b3.sh`、`sums_r8m1b3.sh`）。

## 8. 违规与事件披露

### 表一：越界写入尝试（命令自身写了仓库外路径）

| 轮次 | 命令 | 是否落盘 | 说明 |
|---|---|---|---|
| r8m1b3 | 在 M1b 结果汇总的探查中，写 `awk ... > $OLDPWD/../../../evidence/p05-s4r8/m1b3/tmp/m1c_base_ids.txt`（解析后为仓库外路径） | **否**（shell 报 "No such file or directory"，未创建任何文件） | 路径拼接错误，非有意。已改用只读命令，之后不再使用此写法。 |

### 表二：工具/脚本事件

| 轮次 | 事件 | 是否落盘 | 处置 |
|---|---|---|---|
| r8m1b3 | 探查命令 `cd ../s4r7` 路径错误，`No such file` | 否（只读） | 改用绝对路径 |
| r8m1b3 | 运行 `make_prereg_supp_r8m1b3.py` 第一次：分布检查因字段值 `INVALID` 与实际 `INVALID_NOT_REACHED` 不符而停止（stop 在写表前） | 否（预注册未写出） | 字段值拼写修正为 R7 原值，数字 22 不变；记录于本表 |
| r8m1b3 | 预注册 `m1b1_verdict` 列被混入（取自 ENV_AUDIT，带有 M1b1 观察结果） | 是（第一版预注册含该列） | 运行前删除该列，删除首版 TSV 与 RECORD（均为本轮生成、未用于运行），重新生成；新 sha 712a5547 为冻结值 |
| r8m1b3 | 汇总脚本第一版以 (point_id, tree) 为键，因 G1 与 G2c 共享 point_id 而键不唯一，触发 key count mismatch 停止（无文件写出） | 否 | 键改为 (group, point_id, tree)，三元组已核对 342 唯一 |
| r8m1b3 | 核对临时键表 `tmp/m1b1_verdict_keyed.tsv`、`pre_keys.tmp`、`res_keys.tmp` 在证据 tmp 下生成 | 是（证据 tmp 内） | 核对后用 safe_run 删除，不纳入清单 |
| r8m1b3 | 预检脚本 `run_supp_r8m1b3.py` 增加 `--preflight-only` 开关 | 是（脚本内） | 仅用于先行预检，不改变判定逻辑 |
| 框架 | 无 `/tmp/dsh-spill-*` 框架落盘事件记录 | — | — |

- 表一条目是一条裸跑的内联命令（未经 safe_run），含仓库外重定向目标，被 shell 报错、未落盘。这违反了任务书 §2 的"内联命令不得含 > 字符"与"经 safe_run 运行"两条规定，按执行认定为违规，已列入表一。
- 其余含写入的命令均经 `safe_run.sh` 运行；内联命令中除表一条目外未使用 `>`，未使用 `2>/dev/null`。
- 说明：本轮若干只读核对命令以 `awk ... -F'\t'` 等形式内联运行，不含写入，不属于违规。

### 根目录临时区快照

| 时点 | 时间 | 条目数 | sha256 |
|---|---|---|---|
| 开工（start 门禁） | 2026-10-15 00:32 AEDT | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 收尾 | 2026-10-15 00:41 AEDT | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

## 9. 开放问题

1. **M1c 审核**：440/440 AGREE，本轮未执行。是否进入 r8m1c1，待用户审核（U208）。
2. **字段值拼写**：任务书 §5 "INVALID 22" 与 R7 字段值 `INVALID_NOT_REACHED` 的差异仅为拼写，已在本报告与预注册记录中说明；如用户要求，可在下轮以 ERRATA 方式补正任务书口径。
3. **ENV 口径**：任务书"488 行 ENV_AGREE"与本轮分拆 482 + 6 NOT_RUN 的差异，两者合计 830 一致；待用户确认采用哪种口径。
4. **44 行 M1b1 MISMATCH（期望不符）**：补跑后与 INVALID_NOT_REACHED 一致（未命中）。M1b1 报告把其归为 "REPORTED_FAILURE 与期望不符" 的原因是环境缺 NTH，与 U206 的环境假象同源，但本轮未对其 44 行单独裁决，留待用户确认。
5. **S4 R8 余项**：M1b 完成、M1c 待执行；R8 其余开放项（见 STATE）不变。

## 结论边界

- 本轮完成的范围：U205–U208 登记；M1c 日志核对 440/440 AGREE；342 行补充预注册与补跑（684 次物理调用）；830 行有效汇总。
- 本轮未完成：M1c 执行（U208 规定下轮执行）；P05-S4 整体未完成，未签收。
- 所有 REPORTED_FAILURE 结论仅表示"在该注入下返回码非零"（AGENTS.md §5），不据此判断修复是否生效。
- 本轮未完成/已完成 R8 M1b3 范围，等待用户审核。

## 附：提交状态

- 提交前 `git log -1`：`a26b43d`（r8m1b2 记录提交）。本轮记录提交的哈希见本轮最终回复（`git log -1`）。
- 提交前 `git status --short -uall` 共 27 条，全部在 end 允许列表内（STATE.md、RULINGS.tsv、ERRATA_8.txt 为修改；报告、`registries/s4r8/M1b/r8m1b3/` 与 `testing/d003/stage_s4/*r8m1b3*` 为新增）。
- 门禁：`GATE_R8_M1b3_START.txt` FAILS=0；`GATE_R8_M1b3_END.txt` FAILS=0（registries 副本已核对 sha256）。

本轮未完成/已完成 R8 M1b3 范围，等待用户审核。
