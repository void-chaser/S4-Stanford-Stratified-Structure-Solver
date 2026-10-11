# P05-S1R 收尾报告：S1 对账与 VL NB=1（O-1）归属

> **状态：未完成，等待用户审核。**
> 本报告是 P05-S1 的补充子任务（对账），不是新阶段。P05 固定五阶段 S1–S5，未引入 S6。
> 本报告不宣布 P05-S1、S2、S3、S4 任一阶段完成，不代替用户签收 S2，不作 O-1 的终裁。
> 结论称"装置观察"，不称"验证"。历史报告与文件名未改写；更正只写在 `P05_S1R_*` 新文件中。

## 1. 定位与阶段定义依据

- **定位**：对 S1 的结论逐条对账（Q1），并给出 VL NB=1（O-1）归属的建议（Q2），并确认违规表第 1 行（Q3）。
- **阶段定义依据**：用户提示词（P05-S1 基线与复现：枚举调用点、在 Master 上复现静默吞错、核实 VL NB1，交付报告和原始日志，不改源码）。仓库内无原始计划文档，未搜索原文。

## 2. 授权与边界

- `S4/` 相对 `64eb0b5` 改动：**0**（每次检查均如此，结束时仍为 0）。
- 未修改 `judge_d003.py`（sha256 `d2d04145e0561638`，开始与结束一致）。
- 未修改任何已提交报告原文。S1 原文 `S1_BASELINE_AND_ENUMERATION.md` 未改。
- 写入范围：`checkpoints/p05/`（新文件与追加段）、`testing/d003/stage_s1r/`（新脚本）、证据目录 `checkpoints/p05/evidence/p05-s1r/`（git 排除，不提交）。
- 未动 master、origin，未 amend、rebase、push、合并。

## 3. 起点哈希与基线核对

| 项 | 开始 | 结束 |
|---|---|---|
| HEAD | `56cccf1` | `56cccf1`（本轮未提交前） |
| 分支 | `codex/p05-d003-fft-error-propagation` | 同 |
| 工作区 | 干净 | 仅本轮新增文件（见 §8） |
| `S4/` vs `64eb0b5` | 0 | 0 |
| `/tmp` 顶层 | 0 项，sha256 `e3b0c442…` | 0 项，sha256 `e3b0c442…` |
| 抽样 strace 中 `/tmp` 引用 | 0 | 0 |
| B（`37a82e8`）的 `S4/` 与 `5b72793` | 逐字节相同（70 blob，diff 空） | — |

## 4. 提交表

| 提交 | 内容 | 说明 |
|---|---|---|
| 待提交 | `testing/d003/stage_s1r/`：gdb 脚本（`nb_probe.gdb`、`layer_probe.gdb`）与公共 API 探针（`public_nb.py`） | 单独一个提交，信息含 "awaiting user review" |
| 待提交 | 文档：`P05_S1R_RECONCILIATION.md`、`P05_S1R_O1_ATTRIBUTION.md`、`P05_S1R_O1_ISSUE_DRAFT.md`、`P05_S1R_CLOSEOUT.md`；`S1_evidence_digest.txt` 追加段；`registries/s1r/`；`MANIFEST.tsv` 追加 | 一个提交，信息含 "awaiting user review" |

（提交尚未执行；见 §10 收尾检查。）

## 5. Q1 对账摘要

完整对账表见 `checkpoints/p05/P05_S1R_RECONCILIATION.md`。本节只给摘要。

- **条目**：§1 中 66 项（计数规则与范围见该文件 §5）。状态分布：**仍成立 12，已更正 8，已取代 31，悬而未决 11，超出 S1 范围 4**。
- **计数更正**：S1 的 47 点应为 **44**（exec FMM 侧 10 而非 12；FMMGetEpsilon 10 而非 11；plan 5、S4_malloc 17、solve_info 2 成立）。
- **重要更正**：
  1. VL NB=1 的打印点为 `rcwa.cpp:883`；`:666` 在默认库中不存在（`HAVE_LAPACK` 未定义）。
  2. S1 §7.4 "均匀层也失败" 是探针伪影：`GetPowerFlux(层名)` 对整个堆栈求值。纯均匀堆栈三树均成功。
  3. S1 §3 的"驱动不可达"标注在 S1 原文中**不存在**，它出现在 S2R3 T1 的 `prior_status` 列中（前提核对，见对账文件 §1.3）。
- **已取代的重要项**：驱动编译失败（已修）；T4/T5 未运行（已在 S2 完成）；注入器不能覆盖 LinearSolve（现有 A/B/B2/B2buf 族）；exec 与 FMMGetEpsilon 的丢弃返回值（A、H 已消费/捕获）；S4_malloc 检查（A 16/17，H 17/17）。
- **半覆盖（§3.1）**：机理由源码证实（B：FFT 结果丢弃、PolBasis 无条件覆盖；H：FFT 结果捕获、PolBasis 受保护而跳过）。**内容未检查**：登记表 0 行记录矩阵值，故只有失败类别证据。
- **F10**：部分确认，因果仍未确定（历史负载的 NB 与频率在日志中无 DRIVER 行）。**悬而未决**。
- **F8**：spec 禁止访问历史候选目录，**仍未验证**。

### 5.1 悬而未决项（摘要，完整清单见对账文件 §4）

F10 因果；F8；§3.1 半覆盖的矩阵内容；§9.6 kottke 除数安全性；§9.7 `shape_get_normal` 下标界限；§11.2 的 19 个证据 sha256 未逐个复核；VL NB=1 反事实通量正确性；`allzero` 分支的设计意图。

### 5.2 "传递中的失真"（只写事实与来源，不改写旧文件）

完整清单见对账文件 §3。要点：(a) "S1 标记驱动不可达"的说法来自 S2R3 T1 的 prior 列，不是 S1 原文；(b) S2R 第 410 行把 O-1 的归属写成"需在 S4 中明确"，与 S3 的"不并入 D003"决定不一致；(c) "S1 的 47 点"在 S1 原文与 S2R 中仍被引用，而 S3 对账已纠正为 44；(d) "S1 §7.4 均匀层也失败"被沿用，本轮证明是探针伪影；(e) kottke:78 的红点说法由 S2R6 收尾传递，已由勘误 `56cccf1` 更正；(f) G3 引用 S2 原报告 §4.3，该节是"建议"，闭合依据实际在 S2R4/S2R5（引用错误，实质有据）；(g) `--wrap=malloc` 对 S4_malloc "无效"的 F9 判断只对注入成立，对计数不成立。

## 6. Q2 VL NB=1（O-1）归属摘要

完整归属见 `checkpoints/p05/P05_S1R_O1_ATTRIBUTION.md`。

- **建议类别：B（独立缺陷）**，**建议，不是裁决**；终裁属于用户。
- **一句话**：O-1 不是 D003 的"静默错误数值"（失败是显式报告的），但其根因步骤（流场归一化对零场无检查）是静默的，且把合法输入误报为特征值失败。应作为独立缺陷单独登记。
- **与 S3 的关系**：S3"不并入 D003"维持；本轮修订为"独立缺陷"（部分修订）。
- **对 S2R 第 410 行的更正**：写在归属文件 §3 中。
- **失败触发条件（n_G）**：NB 1–4 → n_G=1 → 失败（info=2）；NB 5–8 → n_G=5 → 成功；NB 9 → n_G=9 → 成功。三树一致（[实测]）。
- **机理（[实测]）**：图案层流场的 `allzero` 分支把网格设为 1×1；圆穿越该单元的 4 条边贡献 `+1,+1,−1,−1`，抵消；`b=0`，`x=0`，`max_field=0`；`1./0` 得 NaN，`pattern_generate_flow_field` 无检查返回 0；NaN 进入特征值求解，得 `info=2`，返回 20。
- **用户可见表现**：`RuntimeError`，文本 `GetPowerFlux: The layer eigensystem could not be solved; no solution was returned`（三树逐字相同）；驱动 `RC first 20`。
- **证据强弱**：最强：机理的 gdb 闭环与单一改动的反事实（diff 已核对，仅一处）。最弱：反事实通量无独立参考（三种基的 NB=1 透射通量 0.9714 / 0.9744 / 0.9589 不足以判定），以及 `allzero` 设计意图未知。
- **对 S3 收尾与 P05-S4 的建议**：不把 O-1 当作 D003 的静默错误模式修复；建议不作为 D003 控制失败排除，记为已知限制，并单独登记（草稿 D016，见 `P05_S1R_O1_ISSUE_DRAFT.md`，**未写入登记表**）。登记表修改属于 P05-S5。

## 7. Q3 违规表第 1 行的定稿

S2R3 首轮披露的 `git show … > /tmp/__never_write`。

**定稿表述**：当前未发现落盘痕迹；无法证明历史时刻未落盘。

- **检索的文件**（[实测] `grep`）：`P05_S2R3_HARNESS_GAPS.md`、`P05_S2R4_CLOSEOUT.md`、`P05_S2R5_CLOSEOUT.md`、`P05_S2R6_CLOSEOUT.md`、`P05_S2R_HARNESS_SUPPLEMENT.md`、`S1_evidence_digest.txt`、`S2_SCOPE_AND_GAPS.md` 中与 `__never_write` 相关的条目。
- **只读检查**（本轮）：`ls -A /tmp | wc -l` = 0，sha256 `e3b0c442…`（开始与结束一致）；`test -e /tmp/__never_write` 结果为不存在（以 `test -e` 执行，未写入）。
- **限制**：`/tmp` 在每次工具调用之间可能被清空（S1 §10.2 的记录），因此当前为空**不能证明**历史时刻 `/tmp/__never_write` 未曾存在。该问题的证据只能是历史时刻的日志，而本轮未找到。

## 8. 偏离与违规（单一表）

| # | 轮次 | 完整命令（或其要点） | 是否落盘 | 如何核实 |
|---|---|---|---|---|
| 1 | S2R3 | `git show … > /tmp/__never_write` | 无法证明历史时刻未落盘；当前 `/tmp` 为空，`test -e` 显示不存在 | Q3，§7；同一事件，无更早记录可对照 |
| 2 | S2R4 | `find … > /tmp_no_write_check_placeholder` | 否 | `ls -la`（S2R4 记录） |
| 3 | S2R5 | `git show … > /tmp_dummy_not_written` | 否 | `ls -d`（S2R5 记录） |
| 4 | S2R6 R6-1 | 目录参数写错，输出到仓库内 `evidence/r6-test/` | 是（仓库内） | 路径校验后删除（S2R6 记录） |
| 5 | S2R6 R6-1 | `ln -s /nonexistent_dir_r6_neg2`：链接在 `$EV` 内，目标为根下占位路径 | 链接落盘，目标未创建 | `test -e` 前后均不存在（S2R6 记录） |
| 6 | S2R6 R6-2 | `run_all.sh --out /tmp/x`（`/tmp` 字面量作参数） | 否（先拒绝，退出码 2） | 退出码（S2R6 记录） |
| 7 | **S1R Q2** | `safe_run.sh p05-s1r/src -- sh -c '… > "$EV/src/…"'`：第一次调用，`$EV/src` 被重复拼接（`src/src`），目标目录不存在 | 否（文件系统拒绝：`Directory nonexistent`；`src/src` 检查为否） | stderr 原文；`test -e "$EV/src/src"` 为 no |
| 8 | **S1R Q2** | 多次 `cat >> PROGRESS_CHECKPOINT.txt <<'EOF' … EOF` 之后，同一命令内残留 `EOF` 行被 bash 当作命令执行 | 否（错误输出到 stderr，`command not found`）；进度文件中 `^EOF` 行数为 0 | bash stderr（`line 15/16: EOF: command not found`）；`grep -c '^EOF$'` 为 0 |

**说明（口径）**：
- 第 7、8 行是本轮自身的违规，已如实列出。第 7 行的目标路径在仓库内，但拼接错误使其指向非预期目录；文件系统拒绝了写入。该行仍是一次违规，因为它是一次错误的写入尝试。
- 第 1 行与历史事件相关：同一事件是否为历史记录中的同一次，**无法确定**（以任务规则允许的标注）。
- **记录范围的限制**：命令历史本身不在仓库中，只有命令的输出与进度记录被保存。因此本表是**已能核实**的违规清单，**不是对全部命令的穷尽审计**。在本轮记录中未发现 `/tmp` 或仓库外的写入目标（见 §3 的开始与结束快照，以及对所有已保存输出的 `/tmp` 字面量检索，结果为无）。

## 9. 仍未闭合缺口

1. **F10 因果**：需要历史负载的 NB 与频率（历史日志无 DRIVER 行）。
2. **F8**：历史候选目录的六文件 SHA256，spec 禁止访问，需用户授权。
3. **§3.1 半覆盖的矩阵内容**：只有失败类别证据；需要在 PolBasis 失败前后直接读取 `Epsilon2`/`Epsilon_inv` 的 gdb 探针。
4. **§9.6 与 §9.7**：kottke 除数与 `shape_get_normal` 下标的安全性未评估。
5. **§11.2 的 19 个证据 sha256**：本轮未逐个复核。
6. **O-1 反事实通量正确性**：无独立参考（见归属文件 §8）。
7. **`allzero` 分支设计意图**：源码无注释，需原作者或用户确认。
8. **S1 的注入器文件**（`inject.cpp`，sha `13b2cbf5…`）不在仓库中；S1 §4 的历史注入器细节无法对照原文核对。
9. **驱动对 `constructed_cache_entries` 的检查**：驱动自报未检查（`N/A`）。这是未覆盖的观察维度，不是错误闭合。

## 10. 对 S2 签收判断的输入

**会影响 S2 可信度的发现**（对账中发现，用户裁决时需知道）：

1. **G3 引用错误**：S2 收敛表中"两步分支已闭合"的依据标为"S2 原报告 §4.3"，该节是建议而非界定。闭合的实质内容在 S2R4 与 S2R5，可信。**结论未错，引用需更正。**
2. **G1、G2 的范围**：闭合仅限范围内的 FMM 调用点（S2R5 §6.1），范围外按决策排除。表述准确，但应知道"已闭合"是范围内的闭合。
3. **§3.1 半覆盖**：机理与失败类别有证据，**矩阵内容未检查**。若 S2 的某结论以"半覆盖已被阻止"为依据，则其证据仅为控制流与失败类别。
4. **驱动缓存计数**：驱动自报未检查（见 §9 第 9 条）；S2 未把它列为已闭合，不构成错误闭合。
5. **kottke 红点**：已由勘误 `56cccf1` 更正。本轮复核，仅历史报告第 201 行保留原句（勘误已指出），无未更正的当前断言。

**停止条件检查**：未发现"S2 某个已闭合结论在源码上实际不成立"的情形（停止条件未触发）。第 1 条是引用错误，不是结论错误。

## 11. 对 S3 收尾与 P05-S4 的输入

- **S3 收尾**：`fmm_kottke:78` 不是红点（勘误 `56cccf1`）。B 列（恒等模型）不是修复证据。NB1 双字段与本轮一致。S3 第 170 行"NB=1–4 的 n_G 未确定"已由本轮测得为 1。
- **P05-S4**：(a) O-1 阈值以 n_G 表述（NB 1–4 → 1；NB 5–8 → 5；NB 9 → 9）；(b) O-1 不作为 D003 控制失败排除，建议记为已知限制并单独登记，由用户决定；(c) §3.1 半覆盖需要内容级探针才能称为"已证实"；(d) S4_malloc 的注入覆盖在 arm 窗口之外，**计数**覆盖已测，**注入**覆盖不成立，不能作为 FMM 分配点的注入证据。
- **修复位置（仅建议）**：`fmm_PolBasisVL.cpp` 的 `allzero` 分支与 `pattern.c` 流场归一化的零场检查，二者都在 `S4/` 中，属于 S4 阶段并需用户授权。

## 12. 路径清单

- 本报告：`checkpoints/p05/P05_S1R_CLOSEOUT.md`
- 对账：`checkpoints/p05/P05_S1R_RECONCILIATION.md`
- 归属：`checkpoints/p05/P05_S1R_O1_ATTRIBUTION.md`
- 登记草稿（未写入登记表）：`checkpoints/p05/P05_S1R_O1_ISSUE_DRAFT.md`
- 摘要追加段：`checkpoints/p05/S1_evidence_digest.txt`（原 603 行字节不变，新增段至第 629 行）
- 复现包：`checkpoints/p05/registries/s1r/`（9 个文本文件，sha256 已核对）
- MANIFEST 追加：`checkpoints/p05/registries/MANIFEST.tsv`（原 90 行字节不变，新增 10 行）
- 探针脚本：`testing/d003/stage_s1r/nb_probe.gdb`、`testing/d003/stage_s1r/layer_probe.gdb`、`testing/d003/stage_s1r/public_nb.py`
- 证据目录（git 排除，不提交）：`checkpoints/p05/evidence/p05-s1r/`，含 `PROGRESS_CHECKPOINT.txt`、`dbg-B`/`dbg-B0`/`dbg-B3`/`dbg-A`/`dbg-H`/`cf` 等调试构建、`public/`、`gdb/`、`grep/`、`src/`、`tmp_top_{start,end}.*`、`strace_{start,end}.txt`

---

**状态：未完成，等待用户审核。**
