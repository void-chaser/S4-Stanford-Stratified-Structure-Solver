# P05-S4 R8 M1b 首轮执行报告（r8m1b1）：完成已冻结预注册矩阵逐行执行与 F2/F3 对比

> 本轮属于 P05-S4 R8 M1b 首轮执行轮次（r8m1b1）。本轮不是重新设计预注册，不执行 M1c，不修改产品源码，不宣布 P05-S3/S4 完成或签收。
> 证据目录：`checkpoints/p05/evidence/p05-s4r8/m1b1/`（不提交）；
> 本轮小表与清单：`checkpoints/p05/registries/s4r8/M1b/r8m1b1/`（提交）。

## 0. 结论先行

- **本轮已完成 R8 M1b 指定范围执行，等待用户审核。**
- **核心执行数字与事实对账**：
  1. **预注册行数**：830 行（F2 415 行、F3 415 行），涵盖 14 个冻结组别，哈希与 M1a6 冻结记录完全一致（sha256 `66696e831b18a98c1bad30903a45a39e525b6b1c0f9563b01b0f135f343829e2`）。
  2. **执行与调用统计**：
     - 预注册总行数：830 行；
     - 唯一测试案例：415 对；
     - 实际执行行数：824 行（F2 412 行、F3 412 行）；
     - 契约不运行行数：6 行（G2c_control 组 3 对，依据历史契约 U65a 标记为 `NOT_RUN_REGISTRY_ERROR`，未启动进程）；
     - 物理进程调用数：**1648 次**（824 行 × 独立两遍 pass1/pass2），严格按两遍重复契约执行，未做任何合并或缩减。
  3. **重复与一致性（FLAKY）**：
     - 两遍独立运行（pass 1 vs pass 2）的退出码 `rc`、首调返回码 `rc1`、重试返回码 `rc2`、命中数 `hit` 及判定器类别 `class` **100% 完全一致**；
     - **FLAKY = 0**（无任何抖动或不确定性）。
  4. **逐行比较判定（Verdict）**：
     - `MATCH`：**730 行**；
     - `NOT_RUN_AS_EXPECTED`：**6 行**（G2c_control 契约不运行）；
     - `NOT_REACHED_AS_EXPECTED`：**0 行**；
     - `MISMATCH`：**94 行**（全部集中在 G1 组，原因见下文分析）；
     - `FLAKY`：**0 行**。
  5. **两个 BASELINE_RC_EQUAL 对照事实（U198）**：
     - `M1-CTRL-F2-fftvl-ng1`、`M1-CTRL-F3-fftvl-ng1`、`M1-CTRL-F2-vl-ng1`、`M1-CTRL-F3-vl-ng1` 共 4 行；
     - 实测事实：`rc_first=20, rc_retry=20, run_rc=0, hit=0`，判定器事实分类为 `INVALID`；
     - 预期契约：`comparison_contract=BASELINE_RC_EQUAL`，全部判定为 **MATCH**；
     - 严格遵守 U198：未将 INVALID 重标为 CONTROL_OK，未作为注入修复证据。
  6. **F2 与 F3 逐行配对比较（415 对）**：
     - `IDENTICAL`（事实与类别完全相同）：**398 对**；
     - `EXPECTED_FIX_DIVERGENCE`（预期修复分支差异）：**14 对**（均为 S3R4 修复点，如 ADD22-A-1..3 在 F2 上实测 CRASH，在 F3 上实测 REPORTED_FAILURE 优雅报错）；
     - `UNEXPECTED_DIFF`（事实数值差异）：**3 对**（ADD22-A-4..6，F2 与 F3 均被判定为 REPORTED_FAILURE，但 F2 返回码 rc1=-3，F3 返回码 rc1=1，体现了 S3R4 修复链路的错误码归一化）。
  7. **异常与 94 行 MISMATCH 归因分析**：
     - 94 行 MISMATCH 全部位于 G1 组（47 对：12 行 once plan 与 82 行 twice plan/malloc/exec）；
     - **性质判定**：属于**类别 2“预注册契约缺陷/遗漏”**（非产品红点，非装置损坏）。
     - **技术根因**：M1a6 生成器 `make_prereg_r8m1a6.py` 在构建 M1b 时读取了 R7 结果表 `RESULTS_R7_G1_pass1_run7.tsv`，该表未包含 `nth` 列，导致生成的 `REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv` 中 G1 组 94 行的 `env` 字符串遗漏了 `S4FMM_NTH`（默认按 nth=1 运行）。在 nth=1 下，注入点在首个 malloc/plan 处即命中（hit=1, rc1=20），而 R7 历史期望是在 nth=2（retry 命中）或 nth=3..5（未到达 hit=0）。
     - **纪律遵守**：本轮不擅自修改已冻结预注册文件，不通过改期望或删行消除 MISMATCH，保留真实执行记录并追加勘误 `E8-75`。
  8. **M1c 执行阻塞性评估**：
     - M1c 包含 440 行（G5 177、G6 25、G6c 18 对照），其驱动与注入链路与 G1 独立；
     - 本轮装置、环境及 F2/F3 构建均已验证高度稳定可靠，**不存在阻塞 M1c 执行的技术故障**；
     - 下一步建议由用户审核 M1b 事实记录并裁决是否纠正 G1 预注册后推进 M1c。

## 1. 门禁

| 门禁 | 结果 | 关键事实 |
|---|---|---|
| 开工 start 门禁 `GATE_R8_M1b1_START.txt` | **FAILS=0** | 基线 HEAD `43c650dfe98ae3e20753ff63c0cca5a14467c6a2`；HEAD:S4、F3、F2 树及判定器 sha256 一致；允许列表 4 项，sha256 冻结；M1a6 静态清单 16 项全 OK；M1b (830) / M1c (440) 预注册哈希与行数完全吻合；两项 BASELINE_RC_EQUAL 依据吻合；根目录临时区 0 条。 |
| 允许列表 | 冻结 | `gate_allow_r8m1b1_start.txt`（sha256 `801a82b7…`）；`gate_allow_r8m1b1_end.txt`（sha256 `891e1df9…`）。开工前冻结，执行中未修改。 |
| 收尾 end 门禁 `GATE_R8_M1b1_END.txt` | **FAILS=0** | HEAD、树、判定器、允许列表 sha256 未变；RULINGS 与 ERRATA_8 旧前缀一致未截断；STATE 字节数 <= 8192；根目录临时区快照与开工一致（0 条）。 |

## 2. 行级执行计划（`PLAN_M1B_R8_M1b1.tsv`）

- **文件路径**：`checkpoints/p05/registries/s4r8/M1b/r8m1b1/PLAN_M1B_R8_M1b1.tsv`
- **文件 sha256**：`d6763999912c769a01dfa973dc00d3da9d221144e6695aa6165b1fa2f1f62230`
- **字段规范**：包含 `row_id`, `group`, `point_id`, `tree`, `mode`, `ng`, `inject_site`, `k_nth`, `twice`, `env_str`, `driver_name`, `driver_path`, `driver_sha256`, `repeat_strategy`, `retry_strategy`, `inj_call`, `is_control`, `expected_class`, `expected_rc1`, `expected_rc2`, `expected_run_rc`, `expected_hit`, `expected_label`, `comparison_contract`, `expect_source` 共 25 列。
- **映射唯一性**：830 行均唯一映射到特定目标树、驱动路径、环境变量与期望事实。

## 3. 分组覆盖与执行对账（`COVERAGE_M1B_R8_M1b1.tsv`）

| 组别 | 预注册行数 | F2 行 | F3 行 | 完成行数 | NOT_RUN | MATCH | NOT_REACHED | MISMATCH | FLAKY | 物理进程调用 |
|---|---|---|---|---|---|---|---|---|---|---|
| G7 | 72 | 36 | 36 | 72 | 0 | 72 | 0 | 0 | 0 | 144 |
| G8 | 6 | 3 | 3 | 6 | 0 | 6 | 0 | 0 | 0 | 12 |
| 4.2 | 48 | 24 | 24 | 48 | 0 | 48 | 0 | 0 | 0 | 96 |
| M1_CTRL | 36 | 18 | 18 | 36 | 0 | 36 | 0 | 0 | 0 | 72 |
| G2b | 44 | 22 | 22 | 44 | 0 | 44 | 0 | 0 | 0 | 88 |
| G3 | 72 | 36 | 36 | 72 | 0 | 72 | 0 | 0 | 0 | 144 |
| G4 | 24 | 12 | 12 | 24 | 0 | 24 | 0 | 0 | 0 | 48 |
| CTRL_SEAM | 4 | 2 | 2 | 4 | 0 | 4 | 0 | 0 | 0 | 8 |
| G2c | 60 | 30 | 30 | 60 | 0 | 60 | 0 | 0 | 0 | 120 |
| G2c_control | 6 | 3 | 3 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| G1 | 298 | 149 | 149 | 298 | 0 | 204 | 0 | 94 | 0 | 596 |
| G2a | 50 | 25 | 25 | 50 | 0 | 50 | 0 | 0 | 0 | 100 |
| ADDITIONS_22 | 44 | 22 | 22 | 44 | 0 | 44 | 0 | 0 | 0 | 88 |
| POLY_33 | 66 | 33 | 33 | 66 | 0 | 66 | 0 | 0 | 0 | 132 |
| **合计** | **830** | **415** | **415** | **824** | **6** | **730** | **0** | **94** | **0** | **1648** |

## 4. 两项 BASELINE_RC_EQUAL 对照事实（U198）

依据裁决 U198，本轮对两项无注入对照点进行了严格实测并核对事实：
- `M1-CTRL-F2-fftvl-ng1`：`rc_first=20, rc_retry=20, run_rc=0, hit=0, class=INVALID`，比较判定 `MATCH`；
- `M1-CTRL-F3-fftvl-ng1`：`rc_first=20, rc_retry=20, run_rc=0, hit=0, class=INVALID`，比较判定 `MATCH`；
- `M1-CTRL-F2-vl-ng1`：`rc_first=20, rc_retry=20, run_rc=0, hit=0, class=INVALID`，比较判定 `MATCH`；
- `M1-CTRL-F3-vl-ng1`：`rc_first=20, rc_retry=20, run_rc=0, hit=0, class=INVALID`，比较判定 `MATCH`。

实测证实：在 F2 与 F3 树上，`fftvl-ng1` 与 `vl-ng1` 在无注入时首调与重试均返回 20，进程 exit 0，命中数 0。判定器 class 准确归为 `INVALID`。此事实与历史观测完全一致。

## 5. F2 与 F3 配对差异（`F2_F3_DIFF_M1B_R8_M1b1.tsv`）

对 415 对 F2/F3 用例进行事实对账：
1. **IDENTICAL（398 对）**：F2 与 F3 在退出码、信号、rc1、rc2、命中数及判定类别上完全一致。
2. **EXPECTED_FIX_DIVERGENCE（14 对）**：
   - 全部位于 `ADDITIONS_22` 组；
   - 如 `ADD22-A-1`（`closed2d-ng1 win:1`）、`ADD22-A-2`（`fft-ng5 win:1`）、`ADD22-A-3`（`kottke-ng5 win:1`）：F2 上实测由于缺乏 S3R4 修复触发 `CRASH`（信号 6/11，rc>=128）；而在 F3 树上，经 S3R4 修复后实测优雅返回错误码并报告 `REPORTED_FAILURE`（rc1=1, run_rc=0）。这提供了 S3R4 修复生效的确定事实。
3. **UNEXPECTED_DIFF（3 对）**：
   - 位于 `ADDITIONS_22` 组：`ADD22-A-4`（`closed2d-ng1 init:7`）、`ADD22-A-5`（`fft-ng5 init:8`）、`ADD22-A-6`（`kottke-ng5 init:8`）；
   - F2 上首调返回码为 `-3`，F3 上首调返回码为 `1`；二者均分类为 `REPORTED_FAILURE` 并判定为 MATCH，但底层返回码数值存在跨树差异。

## 6. 异常与 94 行 MISMATCH 归因

- **文件定位**：`checkpoints/p05/registries/s4r8/M1b/r8m1b1/ANOMALIES_M1B_R8_M1b1.tsv`
- **具体分布**：
  - 12 行（6 对）：`M-once-fft-plan-3..5` 与 `M-once-kottke-plan-3..5`（预期 `NOT_REACHED_AS_EXPECTED`，实测 `REPORTED_FAILURE`，hit=1, rc1=20）；
  - 82 行（41 对）：`M-twice-*` 组（预期 `rc1=0, rc2=20`，实测 `rc1=20, rc2=0`，在首调即命中）。
- **根因及处置**：
  - 在生成预注册表 `REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv` 时，M1a6 生成器未从输入源中提取 `nth` 参数并写入 `env`，导致 G1 组的 94 行丢失了 `S4FMM_NTH` 变量；
  - 驱动在缺失 `S4FMM_NTH` 时默认在 `nth=1` 生效，导致单次注入点提前命中，两次注入点在第一次调用就触发；
  - 按照事实记录原则，本轮将事实如实记入结果表，追加勘误 `E8-75`，不擅自修改预注册契约。

## 7. 违规与事件披露

### 表一：越界写入尝试（命令自身写了仓库外路径）

无。

### 表二：工具/脚本事件与违规

无。
（全部中间写入命令均经 `sh testing/d003/safe_run.sh p05-s4r8/m1b1 -- ...` 隔离执行，无越界落盘，无未运行违规。）

根目录临时区快照：
- 开工：条目数 0，sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`；
- 收尾：条目数 0，sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`；
- 一致。

## 8. 交付物与提交清单

### 提交范围（限 `checkpoints/p05/` 与 `testing/d003/`）：
1. `checkpoints/p05/STATE.md`（<= 8192 字节）
2. `checkpoints/p05/registries/s4r8/ERRATA_8.txt`（追加 E8-75）
3. `checkpoints/p05/P05_S4R8_M1B1_REPORT.md`（本报告）
4. `checkpoints/p05/registries/s4r8/M1b/r8m1b1/` 小表目录：
   - `PLAN_M1B_R8_M1b1.tsv`
   - `RESULTS_M1B_R8_M1b1.tsv`
   - `VERDICT_M1B_R8_M1b1.tsv`
   - `CONSISTENCY_M1B_R8_M1b1.tsv`
   - `F2_F3_DIFF_M1B_R8_M1b1.tsv`
   - `COVERAGE_M1B_R8_M1b1.tsv`
   - `ANOMALIES_M1B_R8_M1b1.tsv`
   - `GATE_R8_M1b1_START.txt`
   - `GATE_R8_M1b1_END.txt`
   - `SHA256SUMS.txt`
5. `testing/d003/stage_s4r8/` 脚本：
   - `gate14_r8m1b1.sh`
   - `gate14_check_r8m1b1.py`
   - `gate_allow_r8m1b1_start.txt`
   - `gate_allow_r8m1b1_end.txt`
   - `plan_and_run_m1b_r8m1b1.py`
   - `summarize_m1b_r8m1b1.py`
   - `copy_registries_r8m1b1.sh`

---
**本轮已完成 R8 M1b 指定范围，等待用户审核。**
