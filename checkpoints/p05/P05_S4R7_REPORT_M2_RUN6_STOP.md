# P05-S4 R7 续 7 报告:run6 在 G1 停止(两类 MISMATCH),等待裁决

**状态:M2b run6 运行于 G1 停止(U67/U68 停止规则)。G2a 未运行。M2 里程碑未完成。ENV_DRIFT 与数值对照未对 run6 完整运行。未宣布任何阶段完成或签收。P05-S3、P05-S4 未签收。S4/ 未修改。本轮未完成 R7 范围(M2b run6 停于 G1,G2a 未运行),等待用户审核。**

## 1. 已完成

| 项 | 结果 | 提交 |
|---|---|---|
| 续 7 任务书原文存档 | 完成 | `381a802` 之后的工作区;未提交 |
| 停止报告与续 7 任务书提交 | 完成 | `381a802` |
| U69–U72、E7-32 | 追加完成 | `9c47d00` |
| 脚本修改:G1、G2c、G2a 环境经 matrix_r2.build_env(U71a);dry-run 环境断言;数值对照脚本;ENV_DRIFT 按组运行(U72) | 完成 | `9c47d00` |
| dry-run `DRYRUN_R7_M2b_run6.txt` | 通过,unparseable 0;nth>1 计数 G1=210、G2c=16(与任务书一致,由脚本核对) | `9c47d00`(registries) |
| run5 数值对照 `VALUES_VS_HISTORY_run5_pass1.tsv` | 179 点,VALUE_DRIFT 69(全部 G1),G2a MISSING | `9c47d00`(registries) |
| 准备提交 | `9c47d00` | — |
| run6 运行 | 在 G1 停止;见第 2 节 | 未提交 |

## 2. run6 结果(只读自 `REGRESS_R7_M2b_run6.tsv`、`M2B_SUMMARY_R7_run6.txt`)

| 组 | 遍 | 行数 | MATCH | NOT_REACHED_AS_EXPECTED | MISMATCH | FLAKY | F≠F2 | 状态 |
|---|---|---|---|---|---|---|---|---|
| CTRL_SEAM | 1、2 | 4 | 4 | 0 | 0 | 0 | 0 | OK |
| G2c | 1、2 | 60 | 60 | 0 | 0 | 0 | 0 | OK |
| G1 | 1、2 | 298 | 238 | 44 | 16 | 0 | 0 | STOP |
| G2a | — | 50 | — | — | — | — | — | NOT_RUN |

**与 run5 相比:**
- NOT_REACHED_AS_EXPECTED 从 0 变为 **44**(期望值 44,符合 U68);
- G1 MATCH 从 204 变为 **238**;
- G2c 与 CTRL_SEAM 的结果与 run5 相同(全部 MATCH / CONTROL_OK)。

G1 的 MISMATCH 为 16 行(run5 为 94 行),且**全部是 G1 自带的 CTL-* 对照行**(见第 3 节)。

## 3. 16 个 MISMATCH:G1 对照行 CTL-*(根因为 harness 构造错误)

- 16 行全部为 `CTL-<mode>-F` / `CTL-<mode>-F2`(8 个模式 × 2 树),期望 CONTROL_OK,实际 INVALID,观测 `rc=1 rc1=0 hit=0`,reason "control run not clean (rc=1 rc1=0)"。
- **根因(已核对,由 harness 构造引起):** 历史 G1 对照行(`run_r3_sweep.py:129–133`)的 request 为 `-`,不设 `S4FMM_INJECT`。我的 v2 对照行的 request 为 `none`(`REGISTRY_S4_PRE_R7_M2.tsv` 中 `CTL-closed1d-F … none`)。`matrix_r2.build_env` 只在 `request not in ("-", "")` 时设 INJECT,因此对照行得到 **`S4FMM_INJECT=none`**。驱动把它当作非法请求(`inject_d003.cpp:13` 只接受 scratch/plan/exec/s4malloc),返回 rc=1。
- **这不是驱动或判定问题,也不是期望问题。** 它是 U71(a) 环境构造对对照行的错误处理。U71(a) 当时没有覆盖 `request == "none"` 的对照行,这是我在续 7 中的遗漏。
- run5 中这 16 行可能也失败(run5 的 MISMATCH 列表只列出了前 50 条,其中为注入行;需要核对 run5 的 CTL 行,不能断定)。

## 4. 未完成与需要裁决的事项

1. **G1 对照行的 harness 修复(根因 3)需要经用户授权后,作为新的运行标签(run7)重跑。** 修复方式:对 request 为 `none` 的对照行,在 `build_row` 中把 request 置为 `-`(与 `run_r3_sweep.py:129–133` 一致),使 `build_env` 不设 INJECT。修复只影响 16 行 CTL-*,不影响注入行与 CTRL_SEAM(CTRL_SEAM 不经 `point_env`)。我没有修复、没有运行 run7,因为续 7 规定 run6 为本段运行标签,修复后的结果是否作为新标签由用户决定(U17)。
2. **run6 的 G1 注入行(238 MATCH、44 NOT_REACHED)与 G2c(60 MATCH)** 有效且与期望一致,但 M2 里程碑要求全组运行,因此需要在 run7 之后才能完整。
3. **G2a 未运行**(U67:G1 停止后不进入后续组)。
4. **ENV_DRIFT 与数值对照未对 run6 运行。** 任务书要求运行后按组检查;本段在 run6 停止后未执行(依据:G1 停止后不再继续本段的其它运行;这些检查可在 run7 后一并做)。
5. **run5 的 CTL 行是否也失败** 需要核对,以判断 harness 错误的影响范围。
6. **G1 与 G2c 的 NOT_REACHED_AS_EXPECTED 与 VALUE_DRIFT 的结论** 需要 run6 的数值对照,未运行。

## 5. 违规披露(任务书第 0 节)

### 表一:越界写入尝试
本段无。

### 表二:工具/脚本事件

| 事件 | 是否落盘 |
|---|---|
| 修改 `run_m2b_all_r7.py` 的汇总文件名为 run 标签(`REGRESS_R7_M2b_<tag>.tsv` 等),使 run6 不覆盖 run5 | 是(仓库内脚本编辑,合规) |
| 复制脚本 `copy_m2b_run6_prep_r7.py` 因 registries 中已有同名文件被 U17 拒绝;改为跳过已存在且 sha256 一致的文件 | 是(合规) |
| `copy_m2b_run6_prep_r7.py` 的 registries 目标 `DRYRUN_R7_M2b_run6.txt` 与 `VALUES_VS_HISTORY_run5_pass1.tsv` 已存在,未记录来源(无对应的复制命令记录) | 是(sha256 与证据一致,未覆盖) |
| 一次 `grep` 输出超过 250 行(只读,计数未得出) | 否 |
| 一次 grep 路径错误(`stage_s4/matrix_r2.py`;实际在 `testing/d003/matrix_r2.py`) | 否 |

## 6. 本段不做的事

- 未修复 G1 对照行(需用户授权,见第 4 节第 1 条);
- 未运行 run7;
- 未运行 G2a;
- 未写 M2 最终报告 `P05_S4R7_REPORT_M2_FINAL.md`(里程碑未完成);
- 未对 run6 运行 ENV_DRIFT 与数值对照。

本轮未完成 R7 范围(M2b run6 停于 G1,G2a 未运行,M2 里程碑未完成),等待用户审核。
