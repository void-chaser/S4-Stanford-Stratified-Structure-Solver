# P05-S4 R8 M1a 续3b1补正报告（r8m1a6）：完成正式预注册、STATE压缩与记录纠偏

> 本轮属于 P05-S4 R8 M1a 续3b1 的补正轮，不是新阶段，不进入续3b2，不宣布 M1a 或 P05-S4 完成，不提出阶段签收。
> 任务书原文存档：`checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3b1_FIX.md`。证据目录 `checkpoints/p05/evidence/p05-s4r8/m1a6/`（不提交）；小表与清单 `checkpoints/p05/registries/s4r8/M1a/`（提交）。

## 0. 结论先行

- **本轮已完成 R8 M1a 续3b1 补正范围，等待用户审核。**
- **完成项**：
  1. 补正续3b1 的记录与输入来源问题：追加裁决 U198–U201 与勘误 E8-70–E8-74；完成 U201 输入快照 `ADDITIONS_MAPPING_22_R8_M1a6.tsv`（sha256 `b7d1f86d…`，2581 字节，19/3 状态核对通过）；建立历史门禁快照 `HIST_GATE_R8_M1a5_END_R8_M1a6.txt` 与提交记录 `HIST_COMMIT_F1CBEFE_POST_R8_M1a6.txt`。
  2. 完成 M1b 与 M1c 两份正式预注册生成：`REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv`（830 行，sha256 `66696e831b18a98c1bad30903a45a39e525b6b1c0f9563b01b0f135f343829e2`）与 `REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv`（440 行，sha256 `e1e555ee4ca20421b6e5681e18be6cd1b873fc7cff06d246c01fad65d8d3a562`）；写出后立即冻结记录于 `PREREG_RECORD_R8_M1a6.txt`。
  3. 独立重算与表内容核对通过：`verify_prereg_r8m1a6.py` 91 项检查全部 PASS，FAILS=0（`VERIFY_PREREG_R8_M1a6.txt`）。
  4. STATE 压缩达成：`checkpoints/p05/STATE.md` 最终 UTF-8 字节数为 **7825 字节**（<= 8192 字节目标达成）；历史全文已归档至 `STATE_PRE_R8_M1a6.md`；生成逐项对照表 `STATE_ITEM_CROSSWALK_R8_M1a6.tsv`（23 项开放问题逐项对应，FAIL=0）。
  5. 门禁与提交：开工 start 门禁 FAILS=0；收尾 end 门禁 FAILS=0。无任何驱动运行、无失败注入、无 dry-run、未修改 S4/、未修改历史装置。

## 1. 门禁

| 门禁 | 结果 | 关键事实 |
|---|---|---|
| 开工 start 门禁 `GATE_R8_M1a6_START.txt` | **FAILS=0** | 基线 HEAD `f1cbefe84001c5957532133377f77d1d003e48c6`，HEAD^ `abf3e420f5ba3600e079ecf213612bc1fc2a0aad`；HEAD:S4、F3、F2 树及判定器 sha256 一致；允许列表 4 项，sha256 冻结；RULINGS 75328 字节、ERRATA_8 56089 字节前缀与 HEAD blob 完全一致；根目录临时区 0 条。 |
| 允许列表 | 冻结 | `gate_allow_r8m1a6_start.txt`（sha256 `c0c5793b…`）；`gate_allow_r8m1a6_end.txt`（sha256 `b9a4aacb…`）。开工前冻结，执行中未修改。 |
| 收尾 end 门禁 `GATE_R8_M1a6_END.txt` | **FAILS=0** | HEAD、树、判定器、允许列表 sha256 未变；RULINGS 与 ERRATA_8 旧前缀一致未截断；STATE 字节数 7825 <= 8192；预注册两表、冻结记录、独立核对与跨表对照全部有效；工作区与命名合规；根目录临时区快照与开工一致。 |

## 2. 裁决 U198–U201（已追加到 `checkpoints/p05/registries/RULINGS.tsv`，状态"生效"）

- **U198**：针对 M1 的 `fftvl-ng1` 与 `vl-ng1` 两项无注入对照，以 `RESULTS_R7_M1_CTRL_REJUDGE_POSTHOC.tsv` 两遍一致的事实为基准（`rc_first=20, rc_retry=20, run_rc=0, hit=0`）：F2 及对应 F3 预注册此事实与 `BASELINE_RC_EQUAL` 比较标签，判定器 class 记录为 `INVALID`，设 `expected_label=BASELINE_RC_EQUAL` / `comparison_contract=BASELINE_RC_EQUAL`。其余 16 项 M1 对照按 `CONTROL_OK` 生成。18 项对照均通过两遍一致性验证。
- **U199**：明确生成器补完属于续3b1 补正范围，不转入续3b2；实现未完成、缺少代码不构成技术停止条件，禁止硬编码 STOP-EXP-2 代替实现。
- **U200**：STATE 维持 <= 8192 字节要求；原文归档与开放项逐项对照，保留开放项标识、状态、去向与链接。
- **U201**：补齐旧 22 行新增映射表的提交版快照 `ADDITIONS_MAPPING_22_R8_M1a6.tsv`，生成器只读该快照，明确标注为本轮新增、随本轮提交。

## 3. 勘误 E8-70–E8-74（已追加到 `checkpoints/p05/registries/s4r8/ERRATA_8.txt`）

- **E8-70**：旧 STOP-EXP-2 实际为生成器实现未完成，不构成新增技术限制。
- **E8-71**：旧报告关于“U192 许可仍待裁决”表述纠偏（许可已生效，成果审核与签收是另一回事）。
- **E8-72**：纠偏提交 f1cbefe 声称预注册与 STATE 压缩完成的不实信息。
- **E8-73**：纠偏旧生成器直接读取证据路径及缺少 registries 快照问题，建立 U201 快照。
- **E8-74**：澄清旧报告关于 end 门禁与提交状态叙述的前后不一致事实。

## 4. STATE 压缩与开放项逐项对照

- **原文归档**：开工前完整 HEAD `STATE.md`（15619 字节，sha256 `b99e2559c69dda86beea5196a47e638f2edbe97e7fe7bedecbe225ca3732e85e`）已原样归档至 `checkpoints/p05/registries/s4r8/M1a/STATE_PRE_R8_M1a6.md`。
- **压缩后规模**：`checkpoints/p05/STATE.md` 压缩后为 **7825 字节**（UTF-8 字符/字节数均 <= 8192 字节）。
- **结构四部分**：
  1. 当前位置：开工基线 HEAD（`f1cbefe`）、收尾查询命令、F3 树、判定器 sha256、签收状态、当前轮次状态。
  2. 关键数字表：每轮一行关键数字与报告链接。
  3. 开放问题表：保留全部 23 项条目，标识、状态、去向及详情链接完整。
  4. 证据位置：只列最近三轮（r8m1a6、r8m1a5、r8m1a4audit3），其余指向各轮报告。
- **逐项对照**：`STATE_ITEM_CROSSWALK_R8_M1a6.tsv` 完成 23 项逐项核对，FAIL=0。

## 5. 正式预注册（`make_prereg_r8m1a6.py`）

生成器直接从已提交 registries 及本轮 U201 快照读取输入（38 项输入已在 `PREREG_INPUTS_R8_M1a6.tsv` 记录路径与 sha256）：

### 5.1 各组点数与行数（`PREREG_COUNTS_R8_M1a6.tsv`）

| 表 | 组 | 原始点数 | F2 行数 | F3 行数 | 控制/不运行行数 | 重复/缺失 | 状态 |
|---|---|---|---|---|---|---|---|
| M1b | G7 | 36 | 36 | 36 | 0 | 0 | OK |
| M1b | G8 | 3 | 3 | 3 | 0 | 0 | OK |
| M1b | 4.2 | 24 | 24 | 24 | 0 | 0 | OK |
| M1b | M1_CTRL | 18 | 18 | 18 | 36 | 0 | OK |
| M1b | G2b | 22 | 22 | 22 | 0 | 0 | OK |
| M1b | G3 | 36 | 36 | 36 | 0 | 0 | OK |
| M1b | G4 | 12 | 12 | 12 | 0 | 0 | OK |
| M1b | CTRL_SEAM | 2 | 2 | 2 | 4 | 0 | OK |
| M1b | G2c | 30 | 30 | 30 | 0 | 0 | OK |
| M1b | G2c_control | 3 | 3 | 3 | 6 | 0 | OK |
| M1b | G1 | 149 | 149 | 149 | 60 | 0 | OK |
| M1b | G2a | 25 | 25 | 25 | 0 | 0 | OK |
| M1b | ADDITIONS_22 | 22 | 22 | 22 | 4 | 0 | OK |
| M1b | POLY_33 | 33 | 33 | 33 | 66 | 0 | OK |
| M1c | G5 | 177 | 177 | 177 | 0 | 0 | OK |
| M1c | G6 | 25 | 25 | 25 | 0 | 0 | OK |
| M1c | G6c | 18 | 18 | 18 | 36 | 0 | OK |

- **总行数**：M1b 为 830 行（F2 415 行、F3 415 行）；M1c 为 440 行（F2 220 行、F3 220 行）。
- **K 来源**：58 个 PLANCALL 点经两遍 STATE 与请求文本核对，58/58 全部一致，记 `K_FROM_REQUEST_AGREED`（`K_SOURCE_PLANCALL58_R8_M1a6.tsv`）；其余 119 点保留 `K_FROM_HISTORY_AGREED`。
- **callseq_status**：完全按照 U196 规则逐行映射，无任何无法解析项。
- **停止项**：`PREREG_STOP_R8_M1a6.tsv` 仅含表头，无任何停止项。
- **冻结记录**：`PREREG_RECORD_R8_M1a6.txt`（2026-10-14T11:33:03Z）记录 M1b sha256 `66696e83…`、M1c sha256 `e1e555ee…`。

## 6. 独立核对（`verify_prereg_r8m1a6.py`）

独立核对脚本直接从原始源表进行重新计算与比对，91 项检查结果全部为 PASS，FAILS=0：
- M1b 行数 830、M1c 行数 440 严格符合；
- 键 `(group, point_id, tree)` 唯一性核对通过；
- F2 与 F3 对应行各项期望、环境、驱动一致性通过；
- 全部行驱动名称及 sha256 与驱动表完全匹配；
- 两个 `BASELINE_RC_EQUAL` 对照点的四项事实（rc_first=20, rc_retry=20, run_rc=0, hit=0, class=INVALID, contract=BASELINE_RC_EQUAL）与 POSTHOC 表逐字一致；
- G5 (177)、G6 (25)、G6c (18) 完整性及不变量核对通过；
- 22 行新增与 33 多边形组合完整性通过。

## 7. 违规与事件披露

### 表一：越界写入尝试（命令自身写了仓库外路径）

无。

### 表二：工具/脚本事件与违规

无。（开发过程中的中间脚本调试均在 safe_run 下受限执行，无越界落盘，无未运行违规。）

根目录临时区快照：开工 0 条，收尾 0 条，sha256 `e3b0c442…`，一致。

## 8. 内联命令自查

内联命令严格遵循只读白名单：
1. `git rev-parse HEAD; git rev-parse HEAD^; ...; git status --short`（只读）
2. `/tmp` 快照命令（开工、收尾各一次只读执行）
3. `sha256sum ...; wc -c ...`（只读）
所有文件写入、脚本调用均通过 `sh testing/d003/safe_run.sh p05-s4r8/m1a6 -- sh ...` 运行，严格遵守规范。

## 9. 剩余停止项与待用户审核

无技术停止项。两份正式预注册已冻结，STATE 已压缩。
本轮不进入续3b2，不执行任何驱动，等待用户审核。
