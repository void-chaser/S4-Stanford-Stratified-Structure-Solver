# P05-S4 R7 报告 第一段(part 1,R7 的子轮次续)

**状态:本轮未完成 R7 范围(第一段)。第一段已完成:门禁复核、run1b 结果表、RULINGS/STATE/ERRATA 更新、小型表复制与清单。里程碑 M1(RNV1 回归)与 M2、M3 未开始。本段未宣布任何阶段完成或签收。P05-S3、P05-S4 未签收。S4/ 未修改。**

规则依据:`AGENTS.md`;R7 原任务书 `checkpoints/p05/briefs/P05_S4R7_BRIEF.md`;续任务书 `checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT1.md`;勘误 `checkpoints/p05/registries/s4r7/ERRATA_7.txt`(E7-1..E7-7)。

---

## 1. 门禁复核(续任务书第 2 节第 1 条)

脚本 `testing/d003/stage_s4r7/r7_gate_cont1.py`(新文件;`r7_gate.py` 未改),输出 `checkpoints/p05/evidence/p05-s4r7/GATE_R7_CONT1.txt`,结果 PASS。

| 项 | 结果 |
|---|---|
| HEAD | `8e13729635c20dc658abc2a35e8195b26e3b9bec` |
| `HEAD:S4` | `e124925f5b242486a913b813fa181664f665b048`(F2) |
| `a07b5ac:S4` | `e124925f5b242486a913b813fa181664f665b048`(一致) |
| judge_d003.py sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`(一致) |
| `git status --short` | 只有 R7 未跟踪文件(briefs、registries/s4r7/、testing/d003/stage_s4r7/) |
| RULINGS.tsv 中 U34–U43 行数(续段之前) | 0(即 E7-7 所述的不一致) |
| `/tmp` 顶层 | 0 条目 |

---

## 2. run1b 结果表(续任务书第 2 节第 2 条)

脚本 `testing/d003/stage_s4r7/summarize_noinject_run1b_r7.py`(新文件)。只读已有输出,不重跑驱动。对 F 与 F2 的 call1–3 用 `filecmp.cmp(shallow=False)` 逐字节比较,从 stdout 解析 `RC first` / `RC retry`。结果 `checkpoints/p05/evidence/p05-s4r7/RESULTS_R7_NOINJECT_run1b.tsv`。

| 模式 | NG | 文件 | F rc1 / rc2 | F2 rc1 / rc2 | cmp |
|---|---|---|---|---|---|
| closed2d | 1 | call1–3 | 0 / 0 | 0 / 0 | IDENTICAL ×3 |
| closed2d | 5 | call1–3 | 0 / 0 | 0 / 0 | IDENTICAL ×3 |
| closed2d | 9 | call1–3 | 0 / 0 | 0 / 0 | IDENTICAL ×3 |

**9/9 IDENTICAL,rc 0/0。** 与续任务书第 2 节第 2 条的期望一致。4.3 门禁按 U40 视为通过(条件满足)。

---

## 3. 无注入等价的完整记录(run1)

`RESULTS_R7_NOINJECT_run1.tsv`:117 行比较(12 模式 × 3 NG 的方形晶格 + tri 的 nv/vl/jones),其中:

- **108 IDENTICAL**;
- **9 NOT_IDENTICAL_OR_MISSING**,全部是 `closed` 模式名输入错误(驱动对 F 与 F2 都以 rc 2 退出,`S4FMM ARGERROR invalid or missing FMM_MODE=closed`)。根因是 R7 任务书 4.3 节写错了模式名(见 U40、E7-3 追加)。这 9 行不是 F 与 F2 输出的差异,run1 文件保持原样(U17)。

---

## 4. 本段新增与修改的文件

| 文件 | 性质 |
|---|---|
| `checkpoints/p05/briefs/P05_S4R7_BRIEF.md` | R7 原任务书(第一段提交前已存盘) |
| `checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT1.md` | 续任务书(本段第一步存盘,原样) |
| `checkpoints/p05/registries/RULINGS.tsv` | 追加 U34–U43(原有行未改) |
| `checkpoints/p05/STATE.md` | 第 10 行改为 R7 开工 HEAD(E7-2);第 15 行改为 R7 当前状态;开放问题中的补测项去向改 R8(E7-1),D016 项拆为 R7 观察 |
| `checkpoints/p05/registries/s4r7/ERRATA_7.txt` | 追加 E7-3 根因说明、E7-7;原有条目未改 |
| `checkpoints/p05/registries/s4r7/` | 小型表 10 项 + ERRATA_7 的 SHA256SUMS.txt(11 项全部 OK) |
| `testing/d003/stage_s4r7/r7_gate_cont1.py` | 新增 |
| `testing/d003/stage_s4r7/summarize_noinject_run1b_r7.py` | 新增 |

证据目录 `checkpoints/p05/evidence/p05-s4r7/`(不提交)中另有 `SHA256SUMS.txt`(evidence 侧,由同一批文件生成,早于 ERRATA_7 的追加,已如实保留)与 `SHA256SUMS_registry_tmp.txt`(中间文件)。

---

## 5. ERRATA_7 事项(第一段)

- **E7-1**:STATE 中补测项去向由 R7 改为 R8(双目标注入、I7、其他层失败变体、Python/Lua、NB、类别 C);D016 B 侧 rc 20 来源保留为 R7 观察。历史报告未改。
- **E7-2**:STATE 第 10 行开工 HEAD 改为 `8e13729…`。
- **E7-3**:`closed` 模式输入错误与根因(任务书);追加根因与 run1b 门禁通过说明(U40)。
- **E7-4 至 E7-6**:见 ERRATA_7(141 与 149 的区分;seam diff 方法;库哈希)。
- **E7-7**:RULINGS.tsv 不一致(见第 1 节 U34–U43 计数 0)及修正。

---

## 6. 本段未完成的 R7 工作

- M1(RNV1 回归):G7(RNV1 36 点)、G8(tri nv NG9 M1–3)、4.2 新增点(jones/fftjones、tri vl/jones)、jones gdb 链、U36 离线表、预注册与运行。**未开始。**
- M2(G1–G4)与 M3(G5、G6、U38 分类、收尾报告)。**未开始。**
- 行号清点(LINEMAP)与 DRIVERS_R7_cont1、tri dbg 驱动:**未开始**(属于 M1 准备)。

以上为"未完成",不是"不可行"。

---

## 7. 违规披露(AGENTS.md 第 3 节)

### 表一:越界写入尝试(命令自身写了仓库外路径)

无。本段所有写入目标均在 `$REPO` 下(`checkpoints/p05/`、`testing/d003/stage_s4r7/`、`$EV`)。`/tmp` 顶层保持 0 条目。

### 表二:工具/脚本事件

| 轮次 | 命令/工具 | 事件 | 是否落盘 |
|---|---|---|---|
| R7 续 | `sha256sum ... > "$2/SHA256SUMS.txt"`(本段第 2 节第 4 条) | 路径错误:清单写到了证据目录 `p05-s4r7/`,而非注册目录 `registries/s4r7/`。该命令在 safe_run 之内,路径在仓库内,属合规路径但内容错位。已用 `cp` 把同一清单复制到注册目录并通过 `sha256sum -c` 核对(11/11 OK)。 | 是(合规路径,已修正) |
| R7 续 | 注册目录 `SHA256SUMS.txt` 首次生成后 ERRATA_7 又追加了 E7-3/E7-7 | 清单的 ERRATA_7 哈希过期;已重新生成并核对(11/11 OK)。 | 是(合规路径,已修正) |
| R7 续 | `edit` 工具:RULINGS.tsv、STATE.md、ERRATA_7.txt | 工具写入;目标在仓库内;读取后重试成功(无 FS_STALE_VERSION)。 | 不适用 |
| R7 续 | 所有写入命令(cp、sha256sum、python 脚本输出、printf) | 均经 `safe_run.sh p05-s4r7` 运行;本段未出现裸跑写入。 | 不适用 |

说明:本段无裸跑写入。表二只列出清单路径错位这一执行者事件,它在 safe_run 之内但路径错位,如实列出。

---

## 8. 本段结束状态

本轮未完成 R7 范围(第一段已完成),等待用户审核。M1 尚未开始。

需要用户裁决的事项:
1. 是否按续任务书 U42 继续做 M1(RNV1 回归)。
2. P05-S3 是否签收(U35,等待 R7 里程碑结果交用户后决定)。

提交信息:`P05-S4 R7 part 1 (partial): gate, builds, seam diff, no-injection equivalence; injection not run. awaiting user review`。
