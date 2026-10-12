# P05-S4 R7 续 6 报告:M2b 在 G1 处停止(MISMATCH 94 点 × 2 遍),等待裁决

**状态:M2b 运行于 G1 停止(U67/U68 停止规则)。G2a 未运行。ENV_DRIFT 不完整(缺 G2a)。M2 里程碑未完成。未宣布任何阶段完成或签收。P05-S3、P05-S4 未签收。S4/ 未修改。本轮未完成 R7 范围(M2b 停于 G1,G2a 未运行),等待用户审核。**

## 1. 已完成

| 项 | 结果 | 提交 |
|---|---|---|
| 续 6 任务书、ADD1 原文存档 | 完成 | `29bc792` |
| U64–U68、E7-29..31 | 追加完成 | `29bc792` |
| 脚本修改:CTRL_SEAM、G2c-control 标记、verdict_of(U68)、pass/tree 逐点比较、dry-run 四项检查 | 完成 | `29bc792` |
| dry-run `DRYRUN_R7_M2b_run5b.txt` | 通过,unparseable 0 | `29bc792`(复制到 registries) |
| 前缀核对 `PREFIX_CHECK_R7_run5.txt` | `all_ok=YES` | `29bc792` |
| 准备提交 | `29bc792` | — |
| M2b 运行(run5) | 在 G1 停止 | 未提交 |
| CTRL_SEAM 与 G2c | 全部 MATCH | 未提交 |
| ENV_DRIFT(M2b) | 未完成(缺 G2a) | — |

## 2. 运行结果(只读自 `REGRESS_R7_M2b.tsv`、`M2B_SUMMARY_R7.txt`)

| 组 | 遍 | 行数 | MATCH | NOT_REACHED_AS_EXPECTED | MISMATCH | FLAKY | F≠F2 | 状态 |
|---|---|---|---|---|---|---|---|---|
| CTRL_SEAM | 1 | 4 | 4 | 0 | 0 | 0 | 0 | OK |
| CTRL_SEAM | 2 | 4 | 4 | 0 | 0 | 0 | 0 | OK |
| G2c | 1 | 60 | 60 | 0 | 0 | 0 | 0 | OK |
| G2c | 2 | 60 | 60 | 0 | 0 | 0 | 0 | OK |
| G1 | 1 | 298 | 204 | 0 | 94 | 0 | 0 | STOP |
| G1 | 2 | 298 | 204 | 0 | 94 | 0 | 0 | STOP |
| G2a | — | — | — | — | — | — | — | NOT_RUN |

G2c-control:NOT_RUN_REGISTRY_ERROR(U65a),6 行,不计入 MISMATCH。

## 3. 异常:NOT_REACHED_AS_EXPECTED 为 0

U68 规定 G1 的 INVALID_NOT_REACHED 点在"judge 为 INVALID、hit=0、rc 非空"时记为 NOT_REACHED_AS_EXPECTED。结果为 **0**。

原因(只读核对汇总行):这些点的 **hit=1**(注入被到达),judge 给出 REPORTED_FAILURE 或 SILENT_SWALLOW,与历史 F 的"未到达"(hit=0)相反。也就是说 G1 中 22 个 INVALID_NOT_REACHED 点在 R7 上**全部被到达**(汇总中可见 `M-once-fft-plan-3-F`、`M-twice-fft-plan-3-F` 等,hit=1)。这不是 U68 的情形,U68 只覆盖 hit=0。

按 U68 的 U58 条款,hit=1 的点要分类:先看同一构建的 F;只有 F2 为 1 是 REGRESSION;F 也为 1 是 ENV_DRIFT。本段的汇总显示 **F 与 F2 的 verdict、class、hit 对称**(每个点两树同时出现在 MISMATCH 中,FLAKY 0,F≠F2 0)。因此按 U58 的分类应为 **ENV_DRIFT(F 与 F2 同步偏离)而非 REGRESSION**,但这需要 ENV_DRIFT 检查的完整结果来确认(见第 5 节),当前未完成。

## 4. 94 个 MISMATCH 的分组(按 expected 与 observed)

从汇总可见的主要模式(每遍各 94 行,两遍相同):

| 模式 | 期望 | 实际 | 性质 |
|---|---|---|---|
| `…-plan-3/4/5-F` 与 `…-F2`(once 与 twice 路线,fft、kottke) | INVALID_NOT_REACHED | REPORTED_FAILURE(rc1=20,hit=1) | 注入被到达,历史为未到达 |
| `M-twice-*-malloc-2/3/4/5-F`、`*-exec-12..16-F`、`*-plan-12..16-F` | REPORTED_FAILURE 或 INVALID_NOT_REACHED | SILENT_SWALLOW(rc1=0, rc2=0, rc=1,inj_call=2) | 与历史(rc1=0 或 rc2 未记录)的分类方式不一致 |

第二类涉及 inj_call=2(twice 路线),判定读取 rc2。历史 R3 的 rc2 列为 `-`(未记录),因此无法直接比较第二次调用的返回值。这是**判定路径差异**,不是已确认的回归,需要裁决。

## 5. 未完成与需要裁决的事项

1. **G2a 未运行**(U67:停止后不进入后续组)。G2a 的 seam 驱动已链接并校验(U61、U64),但按停止规则不运行。
2. **ENV_DRIFT 不完整**:检查脚本要求 G2a 结果文件存在,拒绝运行(退出码 1)。G2c、G1 的 ENV_DRIFT 可单独计算,但未运行,因为脚本是整体运行。
3. **G1 的 94 MISMATCH 需要 U58 分类并裁决**:
   - 22 个 INVALID_NOT_REACHED 点在 R7 上被到达(hit=1),不是 U68 的 NOT_REACHED_AS_EXPECTED;
   - 另有 twice 路线的 SILENT_SWALLOW 类,与历史分类方式有关。
   按 U58,F 与 F2 对称出现,若 ENV_DRIFT 检查确认 F 的历史类别也不同,则归为 ENV_DRIFT(不是 REGRESSION);否则需要进一步判断。
4. **不改期望**:任务书要求 MISMATCH 时停下、写报告、不改期望。本段遵守。
5. **是否在裁决后继续运行 G2a**:待用户决定。

## 6. 违规披露(任务书第 0 节)

### 表一:越界写入尝试
本段无。

### 表二:工具/脚本事件
| 事件 | 是否落盘 |
|---|---|
| ENV_DRIFT 脚本在 G2a 缺失时正确拒绝(退出码 1)——这是预期的停止,不是违规 | 否 |
| 本段前半的 `git rev-parse` 等命令在命令替换中使用,只读 | 否 |

## 7. 本段不做的事

- 未改 v2、ADD、预注册、判定器、期望;
- 未运行 G2a;
- 未提交 M2b 结果(RESULTS_R7_*_run5.tsv、REGRESS_R7_M2b.tsv 留在 $EV,未复制到 registries);
- 未写 M2 最终报告(P05_S4R7_REPORT_M2_FINAL.md),因为里程碑未完成。

本轮未完成 R7 范围(M2b 停于 G1,G2a 未运行,M2 里程碑未完成),等待用户审核。
