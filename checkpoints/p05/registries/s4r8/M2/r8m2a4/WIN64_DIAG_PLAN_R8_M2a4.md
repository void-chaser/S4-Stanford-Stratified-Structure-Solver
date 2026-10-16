# WIN64_DIAG_PLAN_R8_M2a4: M2-01 五个 win:64 测试点诊断运行与转入方案

> 轮次：P05-S4 R8 M2a4（r8m2a4）  
> 依据：用户裁决 U251、U232、INDEX_DERIVATION_R8_M2a2_R2B.tsv；AGENTS.md 第 5 节。  
> 约束：本轮只写设计，**严禁运行任何 S4 驱动或 gdb**；所有诊断观察在后续执行后必须明确标记为 `INFLUENCED`，严禁回填假装为事前预言。

---

## 1. 待诊断的 5 个 win:64 测试点清单

在 M1 ADD22 运行历史中，多边形窗口计数器（`S3R4C3 poly window`）按进程累计，在 `win:64` 时触发分配失败。由于历史 `run.out` 将 stdout 与 stderr 顺序拼接，无法静态断言第 64 次 malloc 发生在 `call1` 还是 `call2` 内部。为保证预注册严密性，这 5 点在 M2a 阶段作为 `UNRESOLVED_INDEX` 保留，不在本轮有效矩阵（150 点）中冒充已解析点。

| 序号 | 增补 point_id | driver | env | 目标层 | 历史观察与未决原因 |
|---|---|---|---|---|---|
| 1 | `M2-01-13-F3` | `polyinj-F3-dbg` | `FMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=win:64` | 1 | ADD22-B-13-F3：hit 行在日志末尾，RC first 为 11，RC retry 为 33；未区分各 call 内部计数 |
| 2 | `M2-01-15-F3` | `polyinj-F3-dbg` | `FMM_MODE=fft;S4FMM_NG=9;S4FMM_INJECT=win:64` | 1 | ADD22-B-15-F3：同上，第 64 次分配所在调用待确认 |
| 3 | `M2-01-17-F3` | `polyinj-F3-dbg` | `FMM_MODE=kottke;S4FMM_NG=1;S4FMM_INJECT=win:64` | 1 | ADD22-B-17-F3：同上，第 64 次分配所在调用待确认 |
| 4 | `M2-01-19-F3` | `polyinj-F3-dbg` | `FMM_MODE=kottke;S4FMM_NG=5;S4FMM_INJECT=win:64` | 1 | ADD22-B-19-F3：同上，第 64 次分配所在调用待确认 |
| 5 | `M2-01-21-F3` | `polyinj-F3-dbg` | `FMM_MODE=kottke;S4FMM_NG=9;S4FMM_INJECT=win:64` | 1 | ADD22-B-21-F3：同上，第 64 次分配所在调用待确认 |

---

## 2. 诊断用断点设置方案

诊断运行时使用专门的 gdb 诊断脚本 `win64_diag_m2.gdb`，设置以下三个关键断点捕获执行轨迹：

1. **多边形分配计数断点**：
   - 目标符号/位置：`testing/d003/stage_s3r4c3/inject_s3r4c3_poly.cpp:54`（窗口 malloc 触发判断处）。
   - 动作：打印当前累计分配序号 `n_window_malloc`，以及当前所属的驱动调用阶段（通过外部变量或帧栈深度回溯）。
2. **快照探针断点**：
   - 目标符号：`r6_probe(int k)`。
   - 动作：在每次进入 $k=0, 1, 2, 3, 4$ 时打印时间戳与快照编号，用于确立失败事件发生在哪两个快照点之间。
3. **层模式计算断点**：
   - 目标符号：`Simulation_ComputeLayerModes`（entry 与 return）。
   - 动作：记录当前被调用的层索引 `idx`、返回码 `rc`。

---

## 3. 要观察的事实与索引确认判据

### 3.1 观察事实
- 事实一：第 64 次分配发生时，程序正处于 `call1` 还是 `call2` 的调用栈中；
- 事实二：分配失败发生的目标层（是否为层 1 `Slab`）；
- 事实三：失败发生时的前后快照点编号 $k_{\text{before}}$ 与 $k_{\text{fail}}$；
- 事实四：重试调用何时发生，重试区间为哪个快照区间 $(k_{\text{preretry}} \dots k_{\text{retry}})$。

### 3.2 确认索引的严格判据
- **判定情况 A（call1 命中）**：
  若第 64 次分配在 `r6_probe(0)` 之后、`r6_probe(1)` 之前触发：
  - 确认：`inj_call = 1`
  - 快照索引：`k_before = 0`，`k_fail = 1`，`k_preretry = 2`，`k_retry = 3`，`retry_call = 2`
  - 输出比对：`output_call = 2`，`control_output_call = 2`
- **判定情况 B（call2 命中）**：
  若第 64 次分配在 `r6_probe(2)` 之后、`r6_probe(3)` 之前触发：
  - 确认：`inj_call = 2`
  - 快照索引：`k_before = 2`，`k_fail = 3`，`k_preretry = 3`，`k_retry = 4`，`retry_call = 3`
  - 输出比对：`output_call = 3`，`control_output_call = 3`
- **判定情况 C（未命中或跨调用越界）**：
  若在整个两调用周期内分配计数未达 64，或在 `call3` 之后才触发，记为 `DIAGNOSIS_UNREACHED`，不填入正式矩阵，转入 S5 登记。

---

## 4. 补预注册表生成与冻结流程

在 M2b 阶段完成上述诊断并确认索引后，执行以下增补冻结流程：

1. **生成增补预注册表**：
   - 文件名：`checkpoints/p05/registries/s4r8/M2/r8m2b/PREREG_M2_WIN64_SUPP.tsv`
   - 格式：完全遵循 `PREREG_M2_EFFECTIVE_R8_M2a4.tsv` 的 53 列规范。
   - 状态标记：5 行的状态列必须明确填写为 `INFLUENCED`（U251），注明由 M2b 诊断运行推导得出，严禁伪称为盲测（BLIND）。
2. **冻结哈希与时间戳**：
   - 生成 `PREREG_M2_WIN64_SUPP.tsv.sha256` 与 `PREREG_M2_WIN64_SUPP_TIMESTAMP_UTC.txt`。
   - 随 M2b 产物一同提交归档。

---

## 5. 正式两遍运行与判定入口

补预注册冻结完成后，进入正式验证闭环：

1. **运行器入口**：
   - 由 `run_m2_r8m2a4.py`（或其 M2b 派生运行器）读取增补表，生成 10 行命令计划（5 点 × 2 passes），分配专用目录：
     `$EV/run/pass1/M2-01-*-F3/` 与 `$EV/run/pass2/M2-01-*-F3/`。
   - 进行两遍完全独立的正式运行（启用 gdb 脚本采集状态）。
2. **事实提取**：
   - 调用 `facts_m2_r8m2a4.py` 提取两遍事实，生成 `FACTS_WIN64_pass1.tsv` 与 `FACTS_WIN64_pass2.tsv`。
3. **状态分析**：
   - 调用 `state_judge_m2_r8m2a4.py`，依据补预注册表中的索引对两遍 gdb 日志与输出 dump 进行客观 I1–I6 判定。
4. **最终判定**：
   - 调用 `verdict_m2_r8m2a4.py` 判定 MATCH / MISMATCH / FLAKY，并纳入 M2 最终汇总台账。
