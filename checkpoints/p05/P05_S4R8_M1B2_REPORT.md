# P05-S4 R8 M1b2 审计报告：M1b 预注册 env 缺陷审计、根因证实与 M1c 准备就绪评估

> 本轮属于 P05-S4 R8 的子轮次（r8m1b2）。本轮不是重新设计预注册，不修改 S4/ 源码、AGENTS.md、判定器及历史脚本。
> 证据目录：`checkpoints/p05/evidence/p05-s4r8/m1b2/`（不提交）；
> 本轮小表与清单：`checkpoints/p05/registries/s4r8/M1b/r8m1b2/`（提交）。

## 0. 结论先行与执行状态

- **本轮未完成 R8 M1b2 补跑范围（停于 A 段停止条件：审计证实 G2c 组 60 行亦存在遗漏 S4FMM_NTH 缺陷，超出仅限 G1 范围），等待用户审核。**
- **核心审计结论与事实对账**：
  1. **静态审计全覆盖**：
     - M1b 全部 830 行逐行完成环境变量审计（`ENV_AUDIT_M1B_R8_M1b2.tsv`）；
     - M1c 全部 440 行逐行完成环境变量审计（`ENV_AUDIT_M1C_R8_M1b2.tsv`）。
  2. **根因完全证实**：
     - 技术根因“R7 结果表无 nth 列导致生成器遗漏 S4FMM_NTH”【已证实】；
     - 引用生成器 `make_prereg_r8m1a6.py` 第 426–440 行及 R7 结果表表头事实，证明链条完全闭合（`ROOTCAUSE_R8_M1b2.txt`）；
     - 查明 M1a6 静态门禁仅校验结构完整性与主键唯一性、未反向做端到端变量强一致性核对的失效机理。
  3. **M1b 缺陷分布发现**：
     - G1 组（298 行）：16 行控制行（CTL-*）`ENV_AGREE`；94 行 M1b1 MISMATCH 行确认为 `MISMATCH_UNDER_WRONG_ENV`；188 行 M1b1 MATCH 行确认为 `MATCH_UNDER_WRONG_ENV`（在默认 nth=1 下恰好首调命中）；G1 缺陷共 282 行。
     - **新发现 G2c 组（60 行）亦存在同类缺陷**：生成器同样调用 `process_r7_group` 从无 nth 列的 `RESULTS_R7_G2c_pass1_run7.tsv` 生成，导致 G2c 全部 60 行亦遗漏 `S4FMM_NTH`（在 M1b1 中因 `d003plan` 驱动在默认 nth=1 下首调即返回 REPORTED_FAILURE 而观察为 MATCH，实质为 `MATCH_UNDER_WRONG_ENV`）。
     - M1b 其余 12 组（472 行）：100% 与历史来源严格一致（`ENV_AGREE`）。
  4. **A 段停止条件触发**：
     - 依据任务书 §2 停止条件：“任一行为 NO_SOURCE，或 env 缺陷超出'G1 缺少 NTH/TWICE'这一类；命中任意一条：做 end 门禁 + 记录提交，然后停下”；
     - 审计确认 env 缺陷已超出原任务书预期的 G1 范围（波及 G2c 组 60 行），故严格按指令停于 A 段，不擅自扩充补跑范围，提交完整静态审计成果供用户裁决。
  5. **M1c 可执行性判定**：
     - M1c 全部 440 行（G5 354 行、G6 50 行、G6c 36 行）经逐行比对，**100% 证实与 R7 原始调用环境完全一致（ENV_AGREE = 440，无缺陷 = 0）**；
     - 依据裁决 U204，待用户审核本轮审计结论后，M1c 即可直接安排执行。
  6. **耗时核实**：
     - m1b1 物理调用 1648 次耗时 6.346 秒，单次中位数 2.3 ms，为单进程严格串行；
     - 抽检 10 次跨组调用证实均具备完整驱动标头、底层状态与注入命中日志，无伪造或空跑（`TIMING_CHECK_R8_M1b2.txt`）。

---

## 1. 用户裁决与编号顺延记录

因 `checkpoints/p05/registries/RULINGS.tsv` 中编号 U199–U201 已于 R8 M1a6 轮次被占用，本轮任务书 §0 给出的三项裁决顺延为 U202–U204，已在开工时追加录入：

| 任务书原编号 | 顺延正式编号 | 裁决内容摘要 | 状态 |
|---|---|---|---|
| U199 | **U202** | M1b1 的 94 行 MISMATCH 原样保留，不改原预注册、不删行。根因确认前，这 94 行和 G1 其余 204 行都记为"条件待核"，不作为任何产品结论的依据。 | 生效 |
| U200 | **U203** | 批准新建"补充预注册"`PREREG_SUPP_R8_M1b2.tsv`。它覆盖本轮审计确认 env 有误的全部行（F2/F3 都要），期望值和 env 的来源只能是 R7 的原始调用参数（运行脚本、计划表或调用日志），不得取自 M1b1 的观察结果。状态一律写 INFLUENCED。补跑结果单独成表，不覆盖 M1b1 的结果。 | 生效 |
| U201 | **U204** | M1c 暂缓。只有本轮的 M1c env 审计结论为"无缺陷"，或缺陷已经用补充预注册修正并经用户审核后，才能执行 M1c。 | 生效 |

---

## 2. 门禁检查结果

| 门禁 | 结果 | 关键事实 |
|---|---|---|
| 开工 start 门禁 `GATE_R8_M1b2_START.txt` | **FAILS=0** | 基线 HEAD `274738dd2367db15a6915d1bccf7babd66394623`；HEAD:S4、F3、F2 树及判定器 sha256 一致；允许列表 4 项冻结；r8m1b1 的 9 项文件 sha256 全部 -c OK；M1a6 的 16 项文件 -c OK；ERRATA_8.txt 与 RULINGS.tsv 前缀校验一致；两份预注册哈希与 PREREG_RECORD 吻合；根目录临时区 0 条。 |
| 收尾 end 门禁 `GATE_R8_M1b2_END.txt` | **FAILS=0** | HEAD、树、判定器、允许列表 sha256 未变；RULINGS 与 ERRATA_8 相对开工前缀一致未截断；STATE 字节数 7765 <= 8192；根目录临时区快照与开工一致（0 条）。 |

---

## 3. A 段静态审计结果

### 3.1 M1b 全部 830 行环境审计交叉统计（`ENV_AUDIT_M1B_R8_M1b2.tsv`）

对 M1b 的全部 830 行，逐行核对其预注册 `env` 与 R7 原始调用 `env`（来源为 R7 运行脚本 `run_m1_r7.py`、`run_m2b_all_r7.py`、历史规则 `expected_env_independent_r7.py` 及计划表 `REGISTRY_S4_PRE_R7_M2_ADD_v3.tsv`）：

| 组别 | 总行数 | F2 行 | F3 行 | ENV_AGREE | ENV_MISSING_VAR (MISMATCH) | ENV_MISSING_VAR (MATCH_UNDER_WRONG_ENV) | ENV_VALUE_DIFF | NO_SOURCE | 审计状态 |
|---|---|---|---|---|---|---|---|---|---|
| G7 | 72 | 36 | 36 | 72 | 0 | 0 | 0 | 0 | 100% 合规 |
| G8 | 6 | 3 | 3 | 6 | 0 | 0 | 0 | 0 | 100% 合规 |
| 4.2 | 48 | 24 | 24 | 48 | 0 | 0 | 0 | 0 | 100% 合规 |
| M1_CTRL | 36 | 18 | 18 | 36 | 0 | 0 | 0 | 0 | 100% 合规 |
| G2b | 44 | 22 | 22 | 44 | 0 | 0 | 0 | 0 | 100% 合规 |
| G3 | 72 | 36 | 36 | 72 | 0 | 0 | 0 | 0 | 100% 合规 |
| G4 | 24 | 12 | 12 | 24 | 0 | 0 | 0 | 0 | 100% 合规 |
| CTRL_SEAM | 4 | 2 | 2 | 4 | 0 | 0 | 0 | 0 | 100% 合规 |
| G2c_control | 6 | 3 | 3 | 6 | 0 | 0 | 0 | 0 | 100% 合规 (NOT_RUN) |
| G2a | 50 | 25 | 25 | 50 | 0 | 0 | 0 | 0 | 100% 合规 |
| ADDITIONS_22 | 44 | 22 | 22 | 44 | 0 | 0 | 0 | 0 | 100% 合规 |
| POLY_33 | 66 | 33 | 33 | 66 | 0 | 0 | 0 | 0 | 100% 合规 |
| **G1** | **298** | 149 | 149 | **16** | **94** | **188** | **0** | **0** | **282 行缺 S4FMM_NTH** |
| **G2c** | **60** | 30 | 30 | **0** | **0** | **60** | **0** | **0** | **60 行缺 S4FMM_NTH** |
| **合计** | **830** | **415** | **415** | **488** | **94** | **248** | **0** | **0** | **342 行缺变量** |

**关键审计发现**：
1. **G1 组**：除了已知的 94 行 MISMATCH 外，其余 204 行中有 188 行注入点同样缺失 `S4FMM_NTH=1`。因注入驱动默认在 `nth=1` 生效，故这 188 行在 M1b1 中观察为 MATCH，但客观属于 `MATCH_UNDER_WRONG_ENV`；仅有 16 行 CTL-* 无注入对照行完全符合 R7 调用环境。
2. **G2c 组**：M1a6 生成器同样采用 `process_r7_group` 读取 `RESULTS_R7_G2c_pass1_run7.tsv` 构建 G2c 预注册，该表同样无 `nth` 列，导致 G2c 全部 60 行均丢失 `S4FMM_NTH`（R7 中有 16 行为 `nth=2..3`，44 行为 `nth=1`）。在 M1b1 中，因 `d003plan` 在默认 nth=1 下首调即返回 `REPORTED_FAILURE`，恰好命中 `expected_class=REPORTED_FAILURE`，故全部 60 行均观察为 MATCH，其实质同样属于 `MATCH_UNDER_WRONG_ENV`。

### 3.2 M1c 全部 440 行环境审计统计（`ENV_AUDIT_M1C_R8_M1b2.tsv`）

覆盖 M1c 的全部 440 行，比对结果如下：

| 组别 | 总行数 | F2 行 | F3 行 | 历史来源依据 | ENV_AGREE | ENV_DIFF | 结论 |
|---|---|---|---|---|---|---|---|
| G5 | 354 | 177 | 177 | `M3_F2_RESULTS_R6c_STATE.tsv` (119 处 NTH，58 处 plancall) | 354 | 0 | 100% 严格一致 |
| G6 | 50 | 25 | 25 | `REGISTRY_S4_PRE_R7_M3.tsv` (seam) | 50 | 0 | 100% 严格一致 |
| G6c | 36 | 18 | 18 | `M3_F2_STATE_SEAM_R6c_pass1/2.tsv` (control) | 36 | 0 | 100% 严格一致 |
| **合计** | **440** | **220** | **220** | — | **440** | **0** | **100% 无缺陷** |

**审计结论**：
M1c 预注册表在 M1a6 构建时，其 G5 组的环境变量通过专门逻辑（`make_prereg_r8m1a6.py` 第 661–667 行）从包含完整 `NTH_or_K` 的 `M3_F2_RESULTS_R6c_STATE.tsv` 表中正确提取了 `S4FMM_NTH`，因此 **M1c 完全未受结果表缺少 nth 列缺陷的影响，440 行环境 100% 正确无误**。

---

## 4. 技术根因证明与静态门禁失效分析（`ROOTCAUSE_R8_M1b2.txt`）

### 4.1 根因证明链条（证明属实）
- **代码直接证据**：`make_prereg_r8m1a6.py` 第 429 行写作：
  ```python
  nth = p1.get("nth") or p1.get("NTH") or p1.get("M", "-")
  ```
  而在构建 M1b 的 G1 组与 G2c 组时，传入的输入表分别为 `RESULTS_R7_G1_pass1_run7.tsv` 与 `RESULTS_R7_G2c_pass1_run7.tsv`。
- **表头直接证据**：上述两张 R7 结果表的表头均为：
  `point_id	group	tree	mode	request	inj_call	expected_class	class	verdict	rc	rc1	rc2	hit	reason`
  表头中完全没有 `nth`、`NTH` 或 `M` 列。
- **推导结论**：变量 `nth` 恒取默认值 `"-"`，导致第 436 行 `if nth not in ("-", ""):` 恒为 False，追加 `S4FMM_NTH` 的代码分支被永久跳过。

### 4.2 M1a6 静态门禁失效原因
`gate13_check_r8m1a6.py` 静态门禁仅核验了表的结构（行数 830/440、主键唯一、驱动哈希匹配、BASE 事实相等），未建立将 `env` 字符串反解并与 R7 实际运行期望（`expected_env_independent_r7.py`）进行逐项变量强校验的机制，导致格式合法但语义缺失的环境变量逃逸入库。

---

## 5. 耗时核实与驱动真实执行证明（`TIMING_CHECK_R8_M1b2.txt`）

1. **执行方式**：单进程 Python 脚本通过循环调用 `subprocess.run(...)` 顺序执行，1648 次物理调用为【严格串行】。
2. **耗时分布**：
   - 1648 次调用总物理耗时：**6.346 秒**；
   - 最小单次耗时：**1.8 ms**；
   - 中位数耗时：**2.3 ms**；
   - 最大单次耗时：**88.8 ms**；
   - 平均单次耗时：**3.9 ms**。
3. **10 次跨组等间距抽样检查**：
   - 抽样覆盖 G7、4.2、G2b、G3、G1、ADDITIONS_22、POLY_33；
   - 全部 10 次运行日志中均具备底层的 `S4FMM DRIVER_R6B mode=...`、`R6STATE` 状态打印、`RC first` 返回码、底层注入钩子打印（`R6D_WIN_MALLOC`、`S3R4C3_WIN_MALLOC`、`S4FMM HIT`）；
   - 证实 1648 次调用【全部真实执行了被测二进制驱动】，无任何 mock、空跑或虚假输出。

---

## 6. 报告勘误与台账更新（ERRATA_8.txt）

已在 `checkpoints/p05/registries/s4r8/ERRATA_8.txt` 追加两条新勘误：

1. **E8-76（对照 122 行与 132 行矛盾勘误）**：
   - 明细核实：M1b 预注册全部 830 行中，无注入/对照性质用例合计为 **132 行**（M1_CTRL 36 行 + G1 控制行 16 行 + CTRL_SEAM 4 行 + G2c_control 6 行 + ADDITIONS_22 控制行 4 行 + POLY_33 多边形无注入行 66 行）；
   - 矛盾根因：M1b1 报告引用的“122 行”系仅计入 M1_CTRL (36) + G1 控制行 (16) + CTRL_SEAM (4) + POLY_33 (66) = 122 行，漏计了 G2c_control (6 行) 与 ADD22 控制行 (4 行) 共 10 行；
   - 正确口径：狭义纯装置对照 66 行；广义无注入/预期 CONTROL_OK（含 POLY_33）132 行。122 行为遗漏 10 行之笔误，予以更正。
2. **E8-77（M1b1 报告措辞纠偏）**：
   - 更正 S3R4 修复生效表述：依 AGENTS.md 第 5 节，将原报告中“这提供了 S3R4 修复生效的确定事实”更正为客观事实表述“ADD22-A-1..3 在 F2 上实测 CRASH，在 F3 上实测返回码非零（rc1=1, run_rc=0，判定类别为 REPORTED_FAILURE）”；
   - 更正 -3→1 返回码差异解释：对 ADD22-A-4..6 返回码跨树差异的“归一化”机理解释补充标注为“[源码/未验证]”推断，非既定结论。

---

## 7. A 段停止条件触发与后一步行动建议

### 7.1 停止条件触发分析
依据任务书 §2 硬性规定：
> “A 段停止条件（命中任意一条：做 end 门禁 + 记录提交，然后停下；不得以'工作量大'为由在其他地方停下）：
> - 任一行为 NO_SOURCE，或 env 缺陷超出'G1 缺少 NTH/TWICE'这一类；
> - M1c 审计发现任何 env 缺陷（不在本轮修 M1c，只记录）；
> - 耗时核实显示调用没有真正执行驱动。”

本轮审计中：
- 耗时核实通过（1648 次真实调用）；
- M1c 审计通过（440 行 100% 无缺陷）；
- 但在 M1b 中，**确认除 G1 组外，G2c 组全部 60 行亦存在遗漏 S4FMM_NTH 的缺陷**。
- 任务书 §0 之裁决 U199 仅将 G1 组定义为“条件待核”，未包含 G2c 组；且任务书标题明确限定为“G1 补充预注册 + 补跑”。
- 发现 G2c 组 60 行存在同类缺陷，属于**环境缺陷范围超出了原设想的“仅 G1 缺少 NTH/TWICE”**。
- 因此，本轮严格遵循工程纪律，**在 A 段完成全部审计、根因证明与勘误后准时停下，做 end 门禁与记录提交，不擅自侵入 B 段**。

### 7.2 后一步补充预注册与补跑建议方案
待用户审核本报告后，建议裁决采取以下方案之一：
- **方案 A（完整闭环，推荐）**：扩充裁决范围，将 G2c 组 60 行与 G1 组 282 行一同纳入补充预注册 `PREREG_SUPP_R8_M1b2.tsv`（共 342 行 / 171 对），执行 684 次物理补跑，一次性彻底解决 M1b 中由于无 nth 列导致的所有环境变量缺陷。
- **方案 B（严格限定 G1）**：维持原任务书范围，仅对 G1 组 282 行（94 MISMATCH + 188 MATCH_UNDER_WRONG_ENV）建立补充预注册并补跑；G2c 组 60 行维持 M1b1 的 MATCH 记录（但标注 condition influenced）。

### 7.3 M1c 是否可以执行的评估
- **结论**：**可以执行**。
- **依据**：M1c 的 440 行已全部经逐行独立审计，其环境变量与 R7 M3 调用环境完全一致（ENV_AGREE 440，ENV_DIFF 0），不存在任何预注册变量遗漏或数值漂移缺陷。依照 U204，待本轮审计结论经用户审核确认后，即可安排 M1c 执行。

---

## 8. 违规与事件披露

### 表一：越界写入尝试（命令自身写了仓库外路径）

无。

### 表二：工具/脚本事件与违规

无。
（全部中间写入命令均经 `sh testing/d003/safe_run.sh p05-s4r8/m1b2 -- ...` 隔离执行，无越界落盘，无未运行违规。）

**根目录临时区快照**：
- 开工：条目数 0，sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- 收尾：条目数 0，sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- 开闭一致。

---

## 9. 交付物与提交清单

### 提交范围（限 `checkpoints/p05/` 与 `testing/d003/`）：
1. `checkpoints/p05/STATE.md`（7765 字节 <= 8192 字节）
2. `checkpoints/p05/registries/RULINGS.tsv`（追加顺延裁决 U202–U204）
3. `checkpoints/p05/registries/s4r8/ERRATA_8.txt`（追加 E8-76、E8-77）
4. `checkpoints/p05/P05_S4R8_M1B2_REPORT.md`（本报告）
5. `checkpoints/p05/registries/s4r8/M1b/r8m1b2/` 审计小表目录：
   - `ENV_AUDIT_M1B_R8_M1b2.tsv`
   - `ENV_AUDIT_M1C_R8_M1b2.tsv`
   - `ROOTCAUSE_R8_M1b2.txt`
   - `TIMING_CHECK_R8_M1b2.txt`
   - `GATE_R8_M1b2_START.txt`
   - `GATE_R8_M1b2_END.txt`
   - `SHA256SUMS.txt`
6. `testing/d003/stage_s4/` 脚本与配置：
   - `gate_r8m1b2.sh`
   - `gate_check_r8m1b2.py`
   - `gate_allow_r8m1b2_start.txt`
   - `gate_allow_r8m1b2_end.txt`
   - `audit_env_r8m1b2.py`
   - `copy_registries_r8m1b2.sh`

---

**本轮未完成 R8 M1b2 范围（停于 A 段停止条件：审计证实 G2c 组 60 行亦存在遗漏 S4FMM_NTH 缺陷，超出仅限 G1 范围），等待用户审核。**
