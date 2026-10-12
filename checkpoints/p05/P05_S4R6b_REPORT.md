# P05-S4 R6b 报告（R6 的子轮次）：S3-4b 装置、预注册与对照组登记；全量运行与判定**未完成**

**状态：本轮未完成全量。R6b 范围中已完成门禁、树核对、ERRATA_6b、202 点映射、177 点预注册（已锁定）、16 个对照组登记；两遍全量 gdb 运行、判定器、VIOLATED 复跑、红点总账、修复方案、RNV1 均未完成或未开始。S3-4b 未判定（无 HOLD、无 VIOLATED 计数，这两个 0 不是通过）。P05-S3、P05-S4 未签收，本报告不宣布任何阶段完成。**

注入结果只说明"在该注入下返回码非零"（REPORTED_FAILURE）、"被命中且类别与期望相同"（MATCH）或"未被触达"（INVALID）。不说明任何树已修好或已验证。B 列（37a82e8）是未修复基线。凡无实测支撑的结论均写为"未验证"；只读源码得到的写"[源码]"。

证据目录：`checkpoints/p05/evidence/p05-s4r6b/`（不提交）；小型结果表：`checkpoints/p05/registries/s4r6b/`（提交）。

---

## 0. 门禁（R6b-0）

- 开工门禁 `evidence/p05-s4r6b/GATE_R6b.txt`：**PASS**。分支、HEAD（20b3411）、STATE 最后修改提交、`HEAD:S4`（4a6f649）、判定器 sha256（d2d04145…）、`/tmp` 顶层（0 条目，列表 sha256 为空输入的哈希）全部一致。
- 工作区 `git status --short --untracked-files=all`：开工时为空。门禁脚本 `r6b_gate.py` 自身是本轮第一个未跟踪文件；第一次运行因此判 FAIL，随后把门禁改为"除本轮 gate 脚本外不得有其他未跟踪条目"并重跑（PASS）。这是我修改门禁的事实，已记录在第 6 节工具事件表。
- 收尾门禁 `evidence/p05-s4r6b/GATE_R6b_END.txt`：**PASS**（HEAD、S4 树、判定器未变；未跟踪条目仅为本轮 r6b 新文件）。
- 构建来源核对（`r6b_tree_verify.py`，`git hash-object` 不带 -w）：`TREE_VERIFY_R6b.tsv`，**70 相同 / 0 不同 / 0 缺失 / 0 多余**。R6 驱动链接的 `p05-s4r5/dbg/trees/F/S4` 与 `1c11905` 的 `S4/` 逐文件一致。

## 1. ERRATA_6b（只追加，未改旧文件）

`checkpoints/p05/registries/s4r6b/ERRATA_6b.txt`（也在证据目录）。内容：

- **U7–U12** 用户裁决（写入 ERRATA_6b 开头）。
- **E6b-1（E6-9，对 E6-8 前提的更正）**：E6-8 写"层 0 与层 2 已安装"，实测错误。单点 `M-once-closed1d-malloc-1__F`：失败时只有层 0 已安装；层 1（Slab）、层 2 的 `modes_null` 均为 1。裁决 U8（选项 1）及 a/b/c 条件不变。
- **E6b-2**：E6-6 写"inject_r6.cpp"，实际链接的是 `inject_r4_plan.cpp`（R6 safe_run.log 第 15 条）；驱动注释"S0–S3"实际为 k=0..4 共 5 个快照。
- **E6b-3**：registries/s4r6 实为 9 个条目（8 数据文件 + SHA256SUMS.txt），R6 报告写的"11"错误；R6 报告第 7 节"SHA256SUMS 未完成"不实（两个 SHA256SUMS 均存在）；STATE 第 3 节"待用户裁决"已过时。
- **E6b-4**：field_cache 只在 `fmm_PolBasisJones.cpp`、`fmm_PolBasisVL.cpp`、`fmm_PolBasisNV.cpp` 中读写（grep 行号见 ERRATA_6b）。其他模式的缓存不变量记 N/A，不计为 HOLD。
- **E6b-5**：`solved[]` 语义（S4.cpp:1756/1764 分配与清零；2012 全解成功置全部层；2225 仅 error==0 置请求层；`S4_Simulation_DestroyLayerModes` 不清 solved）。I4 规则在 k_fail 固定为 `solved[req]==0`；若为 1 则判 VIOLATED 并报告用户，不得改定义。
- **E6b-6（U13，规划者在任务书第 4 节的错误）**：k_fail 等快照索引原按 route 定；实际应按 inj_call 定。twice 且 inj_call=1 的 66 点，失败在 call1，因此 k_fail=1。U13 的完整规则见 ERRATA_6b。计数核对：twice&inj_call=1 = **66**，once&inj_call=2 = 0，inj_call≥3 = 0（均在 `r6b_prereg.py` 中由脚本强制检查）。
- **E6b-7（seam 25 点 UNJUDGED）**：R4 seam 库 `readelf --debug-dump=info` 为 0 个编译单元，无调试信息；seam 行无 inj_call；按任务书 3.4 须先重建并做等价性检查。本轮未做，25 点记为 **UNJUDGED（未计 HOLD）**。

## 2. 映射与预注册

### 2.1 202 点映射（R6b-2 输入）

`registries/s4r6b/MAP_R6b_ALL.tsv`，由 `r6b_map_all.py` 生成（脚本检查总数 = 202 且来源计数 = 119/22/36/25，否则拒绝写出）：

| 来源 | 点数 | 来源文件（行号写在每行的 source_line 列） | F 上观察类别（来源表） |
|---|---|---|---|
| R3 | 119 | `registries/s4r6/MAP_R6_R3.tsv` | REPORTED_FAILURE |
| R4PC | 22 | `registries/s4r4/RESULTS_R4_PLANCALL_pass1.tsv`（F 行） | REPORTED_FAILURE |
| R5M2 | 36 | `registries/s4r5/RESULTS_R5_PLANM_pass1.tsv`（F 行） | REPORTED_FAILURE |
| R4SEAM | 25 | `registries/s4r4/RESULTS_R4.tsv`（F 行） | REPORTED_FAILURE |
| **合计** | **202** | | |

按 (route, inj_call)，可判定的 177 点（不含 R4SEAM）计数：once/1 = 66，twice/1 = 66，twice/2 = 45（U13 第 5 条要求的计数表）。

### 2.2 预注册（运行前锁定）

- `registries/s4r6b/REGISTRY_S4_PRE_R6b_STATE.tsv`：**177 行**，状态 INFLUENCED，期望 HOLD（全部适用不变量）。
  - sha256 `f2523d146e7e5adbf80cf99fdc35ba7b64b0e22ac5e4cc1409e97203cba0c358`；UTC `2026-10-12T06:17:33Z`（`REGISTRY_S4_PRE_R6b_STATE.sha256`、`_TIMESTAMP_UTC.txt`；`sha256sum -c` OK）。
  - 快照索引按 U13：inj_call=1 → k_fail 1、k_preretry 2、k_retry 3、retry_call 2；inj_call=2 → k_fail 3、k_preretry 3、k_retry 4、retry_call 3。
  - 不变量 I1–I6 见预注册头部；**I7 DEFERRED（U9）**。
- `registries/s4r6b/REGISTRY_S4_PRE_R6b_CONTROL.tsv`：**16 个对照组**（mode × route × twice），覆盖全部 177 点。无注入，同 stack（pattern both 4 3）、NG 9、TWICE 显式设置。
- **与任务书的偏差**：预注册只覆盖 177 点，不是任务书第 4 节要求的 202 点。25 个 seam 点按 E6b-7 作为 UNJUDGED，留待重建与等价性检查后另行预注册。
- 期望 HOLD 依据：S3/S3R/S3R2 修复意图、R6 单点（I1 在失败瞬间成立）、E6-8/U8 裁决。状态 INFLUENCED，不是 BLIND。

### 2.3 装置验证（不是判定）

- 驱动 `testing/d003/stage_s4/driver_r6b_state.cpp`（R6 驱动复制后修改）：快照 k=0..4 含义写在文件头；`S4FMM_DUMP_DIR` 输出 call1/2/3（U13）；`S4FMM_DUMP` 保持 R6 行为。编译于 R5 dbg 树（`-O0 -g`，零告警）。
- gdb 采集 `r6b_state.gdb` + `r6b_state_gdb.py`（只读；`r6_probe(k)` 断点读 q 哈希、solved、field_cache 节点；`Simulation_ComputeLayerModes` 入口/返回计数）。
- **试跑结果（单点，不是判定）**：
  - `closed1d` 无注入：gdb 与无 gdb 的 rc 均为 0/0/0。
  - `closed1d` `s4malloc` NTH 1 once（R6 单点同条件）：gdb 与无 gdb 均为 `RC first 20`、`RC retry 0`、HITCOUNT 1，与 R6 单点一致。gdb 进一步读出：k=1 时 layer 0 已装模式、layer 1/2 未装、solved 全 0；重试区间内 Above（idx 0）未再进入 ComputeLayerModes（I5 方向上成立，**这只是 1 点**）。
- 这些试跑未用于判定。它们的日志在 `evidence/p05-s4r6b/state/trial/`。

## 3. 本轮未完成的部分（不是"不可行"，是未做）

| 未完成项 | 状态 | 说明 |
|---|---|---|
| 177 点两遍全量 gdb 运行（`run_r6b_state.py`） | **未写、未运行** | 运行器未写；无 STATE_R6b_pass{1,2}.tsv |
| gdb 与无 gdb rc 的全量核对 | 未做 | 仅单点核对 |
| 判定器 `r6b_state_judge.py` | **未写** | 无 RESULTS_R6b_STATE.tsv、无 STATE_SUMMARY_R6b.txt |
| 对照组实际运行 | 未运行 | 仅登记 |
| I5 计数、I6 逐字节比较 | 未做 | 依赖上面三项 |
| VIOLATED 复跑与 backtrace | 无（无 VIOLATED 可复跑） | 判定未做 |
| seam 25 点重建与等价性 | **未做**（UNJUDGED） | 见 E6b-7 |
| I7 sanitizer | DEFERRED（U9） | 按用户裁决 |
| 双目标注入 | DEFERRED（U9） | 按用户裁决 |
| 红点总账 `RED_POINTS_LEDGER_R6b.tsv` | **未做**（U10 要求本轮做） | 见第 5 节 |
| 修复方案 `REPAIR_PROPOSAL_R6b.md` | **未做** | 同上 |
| R6-3 RNV1 注入（可选，U10） | **未开始**（按 U10 在 2–6 节完成后才可开始） | 延后 |

**如实说明未完成的原因**：我在本轮的执行顺序是先做门禁、树核对、ERRATA、映射、预注册与对照组登记。这些都需要多次修正（列号误读、gdb 指针解引用、门禁自检误判、dump 文件名由 U13 改写、k_fail 定义冲突经用户裁决）。全量运行与判定排在它们之后，时间不够完成。这是**未完成**，不是**不可行**：单点运行约数毫秒，批量运行在工程上可行。

## 4. 对 S3-4b 状态的声明

- S3-4b（失败后模式/缓存不安装）：**未判定**。
- 没有 HOLD 计数，也没有 VIOLATED 计数。0 与 0 都是"未判定"。
- 单点试跑（1 点）显示 I1 在该点成立，这不构成关闭。
- 按任务书第 5 节，只有 202 点全部判定后才可写"S3-4b 在本装置范围内：HOLD x / VIOLATED y / N/A z"。本轮未达到此条件。是否关闭由用户决定。

## 5. 红点总账与修复方案（本轮未产出）

红点总账 `RED_POINTS_LEDGER_R6b.tsv` 与修复方案 `REPAIR_PROPOSAL_R6b.md` **本轮未产出**，不得视为已完成。已确认、可供用户参考的待定项（分类待 R6b-4 正式做）：

- RP-R5-1 — 已由 R6-1 处理（E6-1）。
- RP-R5-2 — 无 TWICE 路线的 F 结论（E6-4：OUT_OF_SCOPE_D003）。
- RP-R5-3 — `partial_modes=1`（E6-3：HARNESS_OR_PROCESS，驱动检查在重试之后计数）。
- RP-R5-4 — ERRATA_3 哈希（U3 已关闭，E6-2）。
- 注释措辞 S4_internal.h:263（HARNESS_OR_PROCESS，U11；修改留到 S3 收尾轮）。
- K-1 张量路径、RNV1（OPEN）；B 侧 jones/vl SILENT_SWALLOW 与 nv CRASH（OPEN，只影响基线列）。

## 6. 违规披露

### 表一：越界写入尝试（命令自身写了仓库外路径，即使被拒绝、未落盘）

| 轮次 | 命令 | 是否落盘 | 说明 |
|---|---|---|---|
| R6b | 无 | — | 本轮未发现命令自身写仓库外路径的情况。 |

### 表二：工具/脚本事件

| 轮次 | 事件 | 是否落盘 | 说明与处理 |
|---|---|---|---|
| R6b | 门禁 `r6b_gate.py` 首次运行 FAIL（自身未跟踪） | 是（写入 GATE_R6b.txt；随后被 PASS 结果覆盖，首次 FAIL 原文件未保留） | 门禁逻辑误把本轮 gate 脚本计入"工作区不干净"。已改为仅允许该文件，重跑 PASS。 |
| R6b | 收尾门禁 FAIL（`git status` 含本轮 r6b 新文件） | 是（GATE_R6b_END.txt 首次） | 收尾检查误用开工规则。已改为收尾专用规则（仅允许 testing/d003/stage_s4/ 下的 r6b 文件与 checkpoints/p05/ 的修改），重跑 PASS。 |
| R6b | 裸跑 `cp driver_r6_state.cpp … tmp/driver_r6_state.copy.cpp`（一次，目标在 $EV/tmp，路径合规） | 是（已随 tmp 清空删除） | 含写入但未经 safe_run。副本与 R6 驱动字节相同，未用于任何结论。 |
| R6b | `write`/`edit` 工具直接写入 `checkpoints/p05/evidence/p05-s4r6b/ERRATA_6b.txt` 与 `testing/d003/stage_s4/*.py`、`*.cpp`、`*.gdb` | 是（仓库内、合规路径） | 工具写入，非 safe_run。目标均在 $REPO 下。 |
| R6b | `edit` 工具一次失败（old_string 与 new_string 相同） | 否（被拒，未落盘） | 已改用正确内容重试。 |
| R6b | `r6b_gate.py` 中 `sha256` 与 `sum` 类比较由脚本完成 | — | 无手工比较；符合"比较写进脚本"规则。 |
| R6b | 映射 awk 列号误读一次（把 `$8` 当 inj_call） | 否（仅在终端输出） | 已用正确列号（$13 为 inj_call）重读；预注册未据误读生成。 |
| R6b | 预注册生成脚本含一段无用检查（已删除） | 否 | 删除死代码，不影响输出。 |
| R6b | `sha256sum -c SHA256SUMS.txt` 对 `safe_run.log` 报 FAILED | 是（日志追加所致） | safe_run.log 是追加日志，清单记录写入时的行数；之后追加是预期的。其余 20 个证据文件全部 OK。 |
| R6b | 框架落盘 `/tmp/dsh-spill-*` | 未观察到 | — |
| R6b | heredoc 残留 EOF | 无 | 本轮未使用 heredoc。 |
| R6b | 仓库内 pycache | 未产生 | 所有 python 调用使用 `-I -B`。 |

**safe_run 记录**：`evidence/p05-s4r6b/safe_run.log` 共 **24** 条记录，**REFUSED 0 条**（`grep -c REFUSED` = 0；本轮无 `safe_run_refusals.log`）。注意：表二中的裸跑与工具写入不在 safe_run.log 中。

---

## 7. 路径清单

- 报告：`checkpoints/p05/P05_S4R6b_REPORT.md`（本文件）
- 状态：`checkpoints/p05/STATE.md`
- 小型结果表（提交）：`checkpoints/p05/registries/s4r6b/`（GATE_R6b.txt、GATE_R6b_END.txt、ERRATA_6b.txt、TREE_VERIFY_R6b.tsv、MAP_R6b_ALL.tsv、REGISTRY_S4_PRE_R6b_STATE.{tsv,sha256,_TIMESTAMP_UTC.txt}、REGISTRY_S4_PRE_R6b_CONTROL.tsv、SHA256SUMS.txt）
- 证据目录（不提交）：`checkpoints/p05/evidence/p05-s4r6b/`（含 SHA256SUMS.txt）
- 新脚本（提交于 `testing/d003/stage_s4/`）：`r6b_gate.py`、`r6b_tree_verify.py`、`driver_r6b_state.cpp`、`r6b_state.gdb`、`r6b_state_gdb.py`、`r6b_map_all.py`、`r6b_prereg.py`、`r6b_control.py`

---

## 8. 本轮结论（诚实版）

- R6b 完成：门禁（开工/收尾）、树核对（70/70）、ERRATA_6b（U7–U13、E6b-1..7）、202 点映射、177 点预注册（锁定）、16 个对照组登记、驱动与 gdb 装置及单点试跑（gdb 与无 gdb rc 一致）。
- R6b 未完成：两遍全量运行、判定器、对照组运行、I5/I6 判定、VIOLATED 复跑、红点总账、修复方案。R6-3（RNV1）未开始。seam 25 点 UNJUDGED。
- **S3-4b 未判定**。没有确认的 F 红点（因为没有判定，也不能说没有）。
- P05-S3、P05-S4 未签收。

本轮未完成/已完成 R6b 范围（部分），等待用户审核。

---

## 9. git 状态

- 提交前范围：`checkpoints/p05/STATE.md`（M）、`checkpoints/p05/P05_S4R6b_REPORT.md`（新）、`checkpoints/p05/registries/s4r6b/`（新）、`testing/d003/stage_s4/r6b_*` 与 `driver_r6b_state.cpp`（新）。
- 提交信息末尾：`awaiting user review`。
- 提交后的 `git log -1` 与 `git status --short` 由提交命令输出确认（提交哈希不能写进提交前的文件，见 STATE 的"收尾提交"规则）。
