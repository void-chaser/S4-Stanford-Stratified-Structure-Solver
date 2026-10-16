# INVARIANT_SPEC_R8_M2a4: M2 执行链不变量规范、Sanitizer 冻结规则与运行器接口

> 轮次：P05-S4 R8 M2a4（r8m2a4）  
> 依据：`PREREG_M2_EFFECTIVE_R8_M2a4.tsv`、`VERDICT_AUDIT_R8_M2a4.tsv`、`COMMAND_PLAN_R8_M2a4.tsv`；用户裁决 U246、U251、U252。  
> 原则：沿用 R6c v2 不变量语义；冻结 ASAN/UBSAN 参数与报告计数；规范运行器输出与事实/状态/判定器接口映射。

---

## 1. 不变量定义与判定语义（I1–I7）

### 1.1 I1：失败层模式清空
- **单次失败（M2-01, M2-05）**：在快照点 $k_{\text{fail}}$，注入失败的目标层 `target_layer` 其私有模式指针 `modes` 必须为 NULL（`modes_null == 1`）。
- **双目标失败（M2-04）**：
  - 目标 1：在快照点 $k_{\text{fail}}$（1），`fail_layer1`（层 1）其 `modes_null` 必须为 1；
  - 目标 2：在快照点 $k_{\text{fail2}}$（3），`fail_layer2` 其 `modes_null` 必须为 1。
  - 对于 M2-04-01-F3，`fail_layer2 = 1`；对于 M2-04-02-F3，`fail_layer2 = UNRESOLVED`（由运行时 R6CREQ/CLM 记录实际失败层并核验 modes_null==1）。
- **状态分析器判定**：`HOLD` / `VIOLATED` / `N/A` / `UNJUDGED`。

### 1.2 I2：其他层模式保持
- **定义**：在快照点 $k_{\text{fail}}$，除失败层之外的其他已安装层（`modes_null == 0`），其本征模特征值与本征向量哈希（`q_sha256`）必须与同配置无注入对照组在同快照点完全一致，且在对照组中亦处于已安装状态。
- **适用性**：存在其他已安装层且对照组存在的测试点。若无其他层已安装，记为 `N/A`。

### 1.3 I3：场缓存一致性（PolBasis 专属）
- **定义**：在快照点 $k_{\text{fail}}$，`S->field_cache` 链表中的节点集合与对照组在同快照点的节点集合一致（每个节点的层号与 $P$ 矩阵哈希完全相同）。
- **适用性**：仅适用于 `PolBasis` 模式（`jones`, `nv`, `vl`, `fftjones`, `fftnv`, `fftvl`）。对于标量 FMM 模式（`closed1d`, `closed2d`, `experimental`, `fft`, `kottke`, `tensor`），本项记为 `N/A`。

### 1.4 I4'：求解状态与模式锁步
- **定义**：在快照点 $k_{\text{fail}}$，请求层 `req` 的 `solution->solved[req]` 状态必须等于调用前快照点 $k_{\text{before}}$ 的值。若该值为 1，则请求层的 `modes_null` 必须为 1，确保下次调用强制重新求解。
- **双失败（M2-04）**：I4' 在 call1 的快照区间 $(k_{\text{before}}=0 \dots k_{\text{fail}}=1)$ 针对目标 1 求解状态进行判定。

### 1.5 I5：重试重算最小性与成功恢复
- **定义**：在重试区间（$k_{\text{preretry}} \dots k_{\text{retry}}$）内：
  1. `Simulation_ComputeLayerModes` 仅对在 $k_{\text{preretry}}$ 处于 NULL 状态的层重新计算，每层至多进入一次；在 $k_{\text{preretry}}$ 未处于 NULL 状态的层不得重新进入；
  2. 重试调用的返回码 `rc_retry` 必须为 0（成功恢复）。
- **单次失败（M2-01, M2-05）**：重试区间为 $(k_{\text{preretry}}=2 \dots k_{\text{retry}}=3)$，重试调用为 `call2`，要求 $rc_2 = 0$。
- **双目标失败（M2-04）**：重试区间为 $(k_{\text{preretry}}=3 \dots k_{\text{retry}}=4)$，重试调用为 `call3`，要求 $rc_3 = 0$。

### 1.6 I6：恢复输出与对照组完全一致
- **定义**：成功恢复调用（`output_call`）输出的场分布文件（`call<output_call>.txt`），必须与对应无注入对照组在对照调用（`control_output_call`）的输出文件逐字节完全一致（DIFFS = 0）。
- **单次失败**：比较测试点 `call2.txt` 与对照点 `call2.txt`（`output_call = 2`, `control_output_call = 2`）。
- **双目标失败**：比较测试点 `call3.txt` 与对照点 `call3.txt`（`output_call = 3`, `control_output_call = 3`）。
- **异常分类修正（D3 / Case J）**：若输出不一致，判定为 `I6=VIOLATED -> MISMATCH(I6)`，严禁记为 `SCHEMA_ERROR`。

### 1.7 I7：内存安全与 Sanitizer 报告
- **定义**：在启用 AddressSanitizer 与 UndefinedBehaviorSanitizer 编译构建的运行中，进程 stderr 及专用日志中 ASan/UBSan 的错误报告块数量必须严格为 0（`san_reports == 0`）。
- **核心关系**：`I7 == HOLD ⇔ san_reports == 0`。

---

## 2. Sanitizer 运行选项与计数规则（M2-03）

### 2.1 环境变量冻结
所有 M2-03 sanitizer 运行严格使用以下冻结环境变量，日志路径必须严格限制在仓库证据目录内，禁止指向仓库外路径：
- `ASAN_OPTIONS="detect_leaks=0:abort_on_error=0:log_path=$EV/run/pass<n>/<point_id>/asan.log"`
- `UBSAN_OPTIONS="abort_on_error=0:log_path=$EV/run/pass<n>/<point_id>/ubsan.log"`

### 2.2 报告匹配与累加规则
`facts_m2_r8m2a4.py` 按以下规则扫描并累加 `san_reports` 计数：
1. **匹配模式**：
   - AddressSanitizer：匹配行首 `^==\d+==ERROR: AddressSanitizer:`；
   - UndefinedBehaviorSanitizer：匹配 `: runtime error: `。
2. **扫描文件范围**：
   - 进程标准错误文件：`$EV/run/pass<n>/<point_id>/stderr.txt`；
   - 专用日志文件：`$EV/run/pass<n>/<point_id>/asan.log*` 以及 `ubsan.log*`（ASan 自动在 `log_path` 后追加 pid 后缀）。
3. **累加计算**：跨上述所有文件匹配到的总块数记为 `san_reports`。若总数为 0，则判定无违规；若大于 0，判定发生内存安全违规。

### 2.3 halt 与 exitcode 对返回码的影响
- 设置 `abort_on_error=0` 确保 UBSan 未定义行为和非致命 ASan 错误不会发送 SIGABRT 中断进程，允许驱动完整执行并打印返回码与状态；
- 若发生致命内存错误（如非法地址访问 SEGV），ASan 接管信号并正常退出报错，使进程退出码 $rc \ne 0$，在事实提取中如实记录退出码与信号。

### 2.4 非 Sanitizer 对照参照规则（U246 / §5.2d）
依据 U246「sanitizer 报告数为 0，且 rc 与类别与非 sanitizer 运行一致」：
- **REP-INIT 与 REP-POLY（12 点）**：显式绑定 `san_ref_point_id` 为 M2-01 同 env 的非 sanitizer 测试点（`M2-01-01..06`, `M2-01-11..20`）。判定器核验两者两遍的 $rc_1$ 与类别是否完全相同；
- **G5 与 G6（19 点）**：由于 M1/R7 历史运行仅在 NG=9 进行，而 M2-03 设定在 NG=1 与 NG=5，经全库匹配确认无同 env 历史非 sanitizer 行（`find_san_refs_r8m2a4.py`），故在预注册中严格登记 `san_ref_point_id = NO_REF`；
- **NO_REF 判定规则**：对于 `NO_REF` 的 19 点，该对照项由于设计限制不可比对，判定器将其归入 `UNJUDGED_BY_DESIGN`，不计入 MATCH，亦不报错。

---

## 3. 调用时序与快照索引总表

| 类别 | 适用项 | inj_call | k_before | k_fail | k_before2 | k_fail2 | k_preretry | k_retry | retry_call | output_call | control_output_call |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 单次失败 | M2-01, M2-05 | 1 | 0 | 1 | - | - | 2 | 3 | 2 | 2 | 2 |
| 双目标失败 | M2-04 | 1 | 0 | 1 | 2 | 3 | 3 | 4 | 3 | 3 | 3 |
| 张量路径 | M2-06 | 1 | 0 | 1 | - | - | - | - | - | 1 | - |
| 网格注入 | M2-07 注入 | 1 | 0 | 1 | - | - | - | - | - | 1 | - |
| 干净对照 | M2-01/04/05/06/07-CTRL | - | 0 | - | - | - | - | - | - | 1 或 2 或 3 | 1 或 2 或 3 |
| 基线诊断 | M2-10 | 1 | 0 | 1 | - | - | - | - | - | 1 | - |

---

## 4. 运行器输出目录结构与事实/判定器接口映射

运行器 `run_m2_r8m2a4.py` 生成的目录结构与后续提取/分析/判定脚本形成严格一对一输入输出绑定：

```
$EV/run/
├── pass1/
│   └── <point_id>/
│       ├── stdout.txt         <-- 驱动标准输出（供 facts_m2 提取 rc1, rc2, rc3, hit, hit2）
│       ├── stderr.txt         <-- 驱动标准错误（供 facts_m2 提取 san_reports, INJECT2 标志）
│       ├── exitcode.txt       <-- 进程退出码与信号（供 facts_m2 提取 rc, signal）
│       ├── gdb.log            <-- gdb 日志（仅 dbg 驱动，供 state_judge 提取 R6BSTATE/R6BCLM/R6CREQ）
│       ├── call1.txt          <-- call1 输出场分布（通过 S4FMM_DUMP_DIR 落盘）
│       ├── call2.txt          <-- call2 输出场分布（通过 S4FMM_DUMP_DIR 落盘）
│       ├── call3.txt          <-- call3 输出场分布（通过 S4FMM_DUMP_DIR 落盘）
│       └── asan.log.<pid>     <-- ASan 专用日志（仅 san 驱动，供 facts_m2 提取）
└── pass2/
    └── <point_id>/            <-- 结构同 pass1，完全独立隔离
```

### 4.1 管道衔接关系
1. **运行器 -> 事实提取**：`facts_m2_r8m2a4.py` 读取 `$EV/run/pass<n>/<point_id>/` 下的文本与 dump，输出 `FACTS_R8_M2a4_pass<n>.tsv`；
2. **运行器 -> 状态分析**：`state_judge_m2_r8m2a4.py` 读取 `$EV/run/pass<n>/<point_id>/gdb.log` 与 `call*.txt`，输出 `STATE_R8_M2a4_pass<n>.tsv`；
3. **事实与状态 -> 最终判定**：`verdict_m2_r8m2a4.py` 同时读取 `PREREG_M2_EFFECTIVE_R8_M2a4.tsv`、两遍 FACTS 与两遍 STATE，输出 `VERDICT_M2_R8_M2a4.tsv` 与 `VERDICT_SUMMARY_R8_M2a4.txt`。
