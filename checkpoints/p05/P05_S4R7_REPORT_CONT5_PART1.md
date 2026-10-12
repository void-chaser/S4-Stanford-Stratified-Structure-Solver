# P05-S4 R7 续 5 第一部分报告(子轮次 R7,不是新阶段)

**状态:未完成。M2b 未运行;M2 里程碑未开始;准备提交未完成。未宣布任何阶段完成或签收。P05-S3、P05-S4 未签收,未写签收文件。S4/ 未修改。本轮未完成 R7 范围(准备未完成,M2b 未运行),等待用户审核。**

## 1. 本段已完成

| 项 | 方式 | 结果 |
|---|---|---|
| 任务书原文存档 | write | `checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT5.md`(已提交) |
| 续 4 收尾提交 | git add/commit(只提交 checkpoints/p05/) | `2044778`,内容:续 4 停止报告 ×2、CONT4 任务书、ERRATA_7(E7-23..26)、RULINGS(U54–U58) |
| ERRATA_7 追加 E7-27、E7-28 与修正注记 | edit | 未提交(见第 4 节) |
| RULINGS 追加 U59–U63 | edit | 未提交 |
| seam 驱动链接 | `safe_run.sh p05-s4r7 -- sh link_seam_drivers_r7.sh p05-s4r7` | 4 个驱动链接成功,退出码 0(见第 2 节) |
| 编排脚本 dry-run | `safe_run.sh … run_m2b_all_r7.py dry-run … DRYRUN_R7_M2b_run5.txt` | 通过,unparseable 0(见第 3 节) |
| 驱动与库 sha256 核对 | dry-run 内部,读取 12 项 | 全部一致 |

## 2. seam 驱动(U61)

| 驱动 | 树 | 库 sha256 | 驱动 sha256 | 与 R4 比较 |
|---|---|---|---|---|
| seamF-F | F | `8066a098…` | `e5c8c4c0…` | **SAME**(R4 seamF `e5c8c4c0…`) |
| seamF-F2 | F2 | `3ed4a6b9…` | `79a3d3e7…` | 无 R4 对照(R4 无 F2 seam 驱动) |
| fmmret-F | F | `fda3d99a…` | `43d2d6a5…` | **SAME**(R4 fmmret-F `43d2d6a5…`) |
| fmmret-F2 | F2 | `b513f840…` | `a4061e4c…` | 无 R4 对照 |

库 sha256 与 `BUILD_SEAM_PLAIN_R7_RESULT.tsv` 的记录一致。`seamF-F` 与 `fmmret-F` 的驱动与 R4 字节级相同,说明 seam 驱动的链接方式与 R4 一致。注:`check_drivers_vs_r4_r7.py` 中的库哈希比较只能记为 NOT_IN_REGISTRY(R4 库哈希不在已提交的 registry 中),这一点如实保留。

## 3. dry-run(`DRYRUN_R7_M2b_run5.txt`)

| 组 | 行数 | 可解析 | 任务书期望 |
|---|---|---|---|
| G2c-control | 6 | 6 | 6 ✓ |
| G2c | 60 | 60 | 60 ✓ |
| G1 | 298 | 298 | 298 ✓ |
| G2a | 50 | 50 | 50 ✓ |

无法解析 0;驱动与库 sha256 共核对 12 项,全部一致(DRIVERS_R7 中的 plain d003/d003plan 驱动,加上四个 seam 驱动及其库)。

**dry-run 之前的失败(记录,不隐藏):** 第一次 dry-run 因 DRIVERS_R7_SEAM.tsv 不存在而报 FileNotFoundError(退出码 1)。原因:link 步骤尚未运行。正确的顺序是先 link、再 dry-run。这不是数据错误。

## 4. 未完成的事项(为什么不能提交准备)

| 项 | 状态 | 原因 |
|---|---|---|
| `run` 模式的汇总 | **不完整** | `summarize` 中的 F/F2 基本 id 规则是我自己写的,没有与已审核的 `compare_trees_r7.base_id` 核对;v2 的 point_id 带树后缀(`M-…-F`/`M-…-F2`),剥离规则必须与之完全一致。在核对之前不能用于运行。 |
| ENV_DRIFT 检查(新文件 check_env_drift_m2b_r7.py) | **未写** | 未做。 |
| pass 比较、tree 比较(v2 配对) | **未以独立脚本形式写** | 只在 summarize 中做了不完整版本。 |
| check_prefix_r7.py 运行、PREFIX_CHECK_R7_run5.txt | **未运行** | 需要参照文件;参照用 `record_prefix_refs_r7.py` 生成。未运行。 |
| check_report_counts_r7.py | **未写** | 报告未写。 |
| STATE.md 同步(U56) | **未做** | 未做。 |
| 准备提交 | **未提交** | 上述未完成。 |
| M2b 运行 | **未运行** | 按任务书第 3 节,准备提交之后才能运行;本段未提交准备,因此未运行。 |

## 5. 违规披露(任务书第 0 节)

### 表一:越界写入尝试(命令自身写了仓库外路径)

本段无。

### 表二:工具/脚本事件

| 轮次 | 命令 | 事件 | 是否落盘 |
|---|---|---|---|
| 续 5 | `edit` 修改 `run_m2b_all_r7.py`、`check_prefix_r7.py` 等脚本的多个版本 | 脚本多次重写;首版(含占位函数,未通过)被完整覆盖。这是仓库内的脚本编辑,按 A 项使用 write/edit,合规。 | 是(仓库内) |
| 续 5 | `sh testing/d003/safe_run.sh … run_m2b_all_r7.py dry-run … DRYRUN_R7_M2b_run5.txt` | **路径拼错**:向脚本传了不带 `$EV` 前缀的相对文件名,输出落在仓库根 `DRYRUN_R7_M2b_run5.txt`。 | 是(仓库根;已用 safe_run 移入 `$EV`,仓库根已清空) |
| 续 5 | `sh testing/d003/safe_run.sh … sh -c 'test ! -e … && mv …'` | 移动仓库根的文件到 `$EV`,经 safe_run,合规。 | 是(合规路径) |
| 续 5 | `ls -d DRYRUN_R7_M2b_run5.txt checkpoints/...`、`ls -d …` | 只读,白名单内。 | 否 |
| 续 5 | `grep` 读取 v2 全表(`\tG1\t`,输出 250 行) | 读取量过大(超过必要范围);只读,工具内。 | 否 |
| 续 5 | `git show <commit>:<path> \| wc -c`(只读,白名单) | 合规。 | 否 |
| 续 5 | `read` 读取 REGISTRY_S4_PRE_R7_M2.tsv 的 offset 9 行 | 错误的偏移,只读。 | 否 |

说明:本段没有任何越界写入(表一为空)。表二的路径拼错事件已如实记录;它落在仓库内,并已移入正确位置。

## 6. 需要用户决定的事项

1. **是否继续本段的剩余工作**(汇总修正、ENV_DRIFT、pass/tree 比较、准备提交、M2b 运行、M2 里程碑)。剩余工作量大,且我已有多次路径与流程错误。建议下一段由用户明确授权"只在脚本中做计算,不在 shell 中做任何核对"。
2. **G2a 的 seam 驱动是否按 U61 认可**。驱动已链接,与 R4 的 seamF-F、fmmret-F 字节级一致;seamF-F2、fmmret-F2 为新驱动,没有 R4 对照。
3. **库哈希的 R4 对照**:`check_drivers_vs_r4_r7.py` 只能记为 NOT_IN_REGISTRY;若需要严格的库逐字节比较,需要补充 R4 库哈希 registry(`seam/LIBS_R4.tsv` 在证据目录中,未提交)。
4. P05-S3 签收(U62)与 M3(U63):在 M2 里程碑之后由用户决定。

## 7. 本段产出

- 已提交:`2044778`(续 4 收尾,checkpoints/p05/ 下的停止报告、CONT4 与 CONT5 任务书、ERRATA_7、RULINGS)。注:CONT5 任务书已在该提交中,ERRATA_7 与 RULINGS 中的 E7-27、E7-28、U59–U63 是**在该提交之后追加的**,尚未提交。
- 未提交:本报告;ERRATA_7 与 RULINGS 的 E7-27/28、U59–U63;编排脚本 `run_m2b_all_r7.py`、`check_prefix_r7.py`、`record_prefix_refs_r7.py`、`check_drivers_vs_r4_r7.py`、`link_seam_drivers_r7.sh`(均在 testing/d003/stage_s4r7/,未提交)。
- 证据(`$EV`,不提交):DRIVERS_R7_SEAM.tsv、drivers_r7/seam-*、DRYRUN_R7_M2b_run5.txt、safe_run.log。

本轮未完成 R7 范围(准备未完成;M2b 未运行;M2 里程碑未开始),等待用户审核。
