# INVARIANT_SPEC_R8_M2a3: M2 不变量规范、采集路径、双失败恢复与对照判定

> 轮次：P05-S4 R8 M2a3（r8m2a3）  
> 依据：`PREREG_M2_EFFECTIVE_R8_M2a3.tsv`、`CONTROL_MAPPING_R8_M2a3.tsv`、`PREREG_EXECUTABILITY_AUDIT_R8_M2a3.tsv`。  
> 原则：沿用 R6c v2 不变量定义，不重写其含义；明确采集路径与限制；修正双失败恢复断言与索引。

---

## 1. 不变量定义（I1–I7）

### 1.1 I1：失败层模式清空
- **定义**：在失败发生后的快照点 $k_{\text{fail}}$，注入失败的目标层 `target_layer` 其私有模式指针 `modes` 必须为 NULL（`modes_null == 1`）。
- **来源**：R6c v2 规则；S3-4b 核心契约（失败层不得安装模式）。
- **采集方式**：通过 gdb 脚本在断点 `r6_probe(k_fail)` 读取 `S->layer[target_layer].modes`，输出 `R6BSTATE <k> layer <target_layer> modes_null 1`。

### 1.2 I2：其他层模式保持
- **定义**：在失败发生后的快照点 $k_{\text{fail}}$，除失败层之外的其他已安装层（`modes_null == 0`），其本征模特征值与本征向量哈希（`q_sha256`）必须与同配置无注入对照组在同快照点完全一致。
- **适用性**：存在其他已安装层且对照组存在的测试点。若无其他层已安装，记为 `N/A`。
- **采集方式**：gdb 读取 `modes->q`（$2 \times n_G \times 16$ 字节）计算 SHA256，与 `control_point_id` 在 $k_{\text{fail}}$ 的哈希比对。

### 1.3 I3：场缓存一致性（PolBasis 专属）
- **定义**：在快照点 $k_{\text{fail}}$，`S->field_cache` 链表中的节点集合与对照组在同快照点的节点集合一致。
- **适用性**：仅适用于 `PolBasis` 模式（`jones`, `nv`, `vl`, `fftjones`, `fftnv`, `fftvl`）。对于标量 FMM 模式（`closed1d`, `closed2d`, `experimental`, `fft`, `kottke`, `tensor`），本项记为 `N/A`（不产生也不读取 field_cache）。
- **采集方式**：gdb 遍历 `S->field_cache` 链表输出各节点层号及矩阵 $P$ 的 SHA256。

### 1.4 I4'：求解状态与模式锁步
- **定义**：在快照点 $k_{\text{fail}}$，请求层 `req` 的 `solution->solved[req]` 状态必须等于调用前快照点 $k_{\text{before}}$ 的值。若该值为 1，则请求层的 `modes_null` 必须为 1，确保下次调用强制重新求解。
- **采集方式**：gdb 断点 `Simulation_GetLayerSolution` 记录请求层 `R6CREQ <call> <req>`，并在 `r6_probe(k_before)` 与 `r6_probe(k_fail)` 读取 `solution->solved` 数组。

### 1.5 I5：重试重算最小性与成功恢复
- **定义**：在重试区间（$k_{\text{preretry}} \dots k_{\text{retry}}$）内：
  1. `Simulation_ComputeLayerModes` 仅对在 $k_{\text{preretry}}$ 处于 NULL 状态的层重新计算，每层恰好进入一次；未处于 NULL 状态的层不得重新进入；
  2. 重试调用的返回码 `rc_retry` 必须为 0（成功恢复）。
- **采集方式**：gdb 在 `Simulation_ComputeLayerModes` 记录 `R6BCLM ENTER` 与 `RETURN`，统计重试区间内的进入次数与每层状态。

### 1.6 I6：恢复输出与对照组完全一致
- **定义**：最终成功恢复调用（`output_call`）输出的场分布文件（`call<output_call>.txt`，含 E 场与 H 场），必须与对应无注入对照组在对照调用（`control_output_call`）的输出文件逐字节完全一致（DIFFS = 0）。
- **绑定规则**：测试行显式绑定 `control_point_id`、`output_call` 与 `control_output_call`。

### 1.7 I7：内存安全与 Sanitizer 报告
- **定义**：在启用 AddressSanitizer 与 UndefinedBehaviorSanitizer（`-fsanitize=address,undefined`）编译构建的运行中，进程 stderr 中 ASan/UBsan 的错误报告块数量必须严格为 0（`san_reports == 0`）。
- **关系说明**：`I7` 是不变量断言形式（`I7 == HOLD` 当且仅当 `san_reports == 0`），`exp_san = 0` 是其量化期望值。两者表征同一事实，不重复构造独立断言。

---

## 2. 快照索引与调用时序规范

### 2.1 单次失败（Once Route，M2-01、M2-05）
驱动调用序列：`call1`（注入失败） $\to$ `call2`（重试恢复） $\to$ `call3`（二次重试备用）。
- $k=0$：`call1` 调用前（`k_before = 0`）
- $k=1$：`call1` 失败后（`k_fail = 1`，断言 $rc_1 = 20$）
- $k=2$：进入重试前（`k_preretry = 2`）
- $k=3$：`call2` 成功恢复后（`k_retry = 3`，`retry_call = 2`，断言 $rc_2 = 0$）
- $k=4$：`call3` 运行后（`k = 4`）
- 输出比较：比较测试点 `call2.txt` 与对照点 `call2.txt`（`output_call = 2`, `control_output_call = 2`）。

### 2.2 双目标失败与最终恢复（Dual Failure，M2-04）
驱动调用序列：`call1`（第 1 次注入失败） $\to$ `call2`（第 2 次注入失败） $\to$ `call3`（重试恢复成功）。
驱动仅提供 $k=0, 1, 2, 3, 4$ 五个标准探测点，严禁虚构不存在的新快照。
- **第一次失败事件**：
  - 调用：`call1`，注入目标 1 生效（同层为层 1；跨层为层 1 `Slab1`）。
  - 调用前状态：$k_{\text{before}} = 0$
  - 失败后状态：$k_{\text{fail1}} = 1$
  - 返回码断言：$rc_1 = 20$，信号 0，命中计数 1。
  - 不变量适用：检查失败层 modes_null == 1（I1），I4' 锁步。
- **第二次失败事件**：
  - 调用：`call2`，注入目标 2 生效（同层仍为层 1；跨层为层 2 `Slab2`）。
  - 调用前状态：$k = 2$
  - 失败后状态：$k_{\text{fail2}} = 3$
  - 返回码断言：$rc_2 = 20$，信号 0，累计命中计数 2。
  - 不变量适用：检查第二次失败目标层在 $k=3$ 的 modes_null == 1。
- **最终成功恢复事件**：
  - 调用：`call3`（不再有注入，驱动正常完成全部层求解）。
  - 恢复前状态：$k_{\text{preretry}} = 3$
  - 恢复后状态：$k_{\text{retry}} = 4$
  - 返回码断言：$rc_3 = 0$（必须显式覆盖，不可缺省）。
  - 不变量适用：
    - I5：检查在区间 $(k=3 \dots k=4)$ 内进入 `ComputeLayerModes` 的层数必须等于 $k=3$ 时 modes 为 NULL 的层数，且 $rc_3 = 0$。
    - I6：检查测试点 `call3.txt` 与对照点 `call3.txt`（`output_call = 3`, `control_output_call = 3`）逐字节一致。

---

## 3. 采集路径与可执行性矩阵

| 测试项 | 驱动类型 | 状态采集器（gdb_script） | I1–I6 判定能力 | I7 / exp_san 判定能力 | 对照绑定模式 |
|---|---|---|---|---|---|
| M2-01 | dbg 库 + dbg 驱动 | `r6c_state_r8m2a3.gdb` | 完全可判（HOLD） | N/A（`-`） | 显式绑定 `M2-01-CTRL-*` |
| M2-03 | san 库 + san 驱动 | `-`（不运行 gdb） | UNOBSERVED | 完全可判（`exp_san=0`, I7=HOLD） | 固有判定（无对照依赖） |
| M2-04 | dbg 库 + dual-dbg 驱动 | `r6c_state_r8m2a3.gdb` | 完全可判（基于 call3 恢复） | N/A（`-`） | 显式绑定 `M2-04-CTRL-*` |
| M2-05 | dbg 库 + layers-dbg 驱动 | `r6c_state_r8m2a3.gdb` | 完全可判（指定 target_layer） | N/A（`-`） | 显式绑定 `M2-05-CTRL-*` |
| M2-06 | plain 库 + nanbuf 驱动 | `-` | N/A（`-`） | N/A（`-`） | 绑定 `M2-06-CTRL-01-F3` |
| M2-07 | plain 库 + plan 驱动 | `-` | N/A（`-`） | N/A（`-`） | 绑定 `M2-07-CTRL-*-ng5-F3` |
| M2-09 | plain 库 + fmmret 驱动 | `-` | N/A（`-`） | N/A（`-`） | 自身对照（F3 与 F2） |
| M2-10 | dbg 库 + r6dnv1-B-dbg | `m210_b_r8m2a2_R2.gdb` | N/A（基线断点诊断） | N/A（`-`） | BASELINE_ONLY |

---

## 4. 判定规则与异常分类

判定器只依据客观事实，不读取驱动的 PASS/FAIL 文本：
1. **MISMATCH**：任一已注册的非空期望字段与观测值不符（含 $rc_1, rc_2, rc_3, signal, hit, class, I_1..I_7, san$）。
2. **FLAKY**：第 1 遍与第 2 遍的观测值在任一字段出现不一致。
3. **UNOBSERVED / UNJUDGED**：因装置或环境限制未采集私有状态的项，明确输出未观测/未判定，严禁当作通过或冒充 HOLD。
4. **NZ 记号规则**：对于预注册中期望为 `NZ` 的项，观测值非零即判通过，观测值为 0 判 MISMATCH。
