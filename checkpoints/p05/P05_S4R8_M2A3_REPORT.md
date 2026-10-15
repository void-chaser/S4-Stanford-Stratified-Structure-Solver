# P05-S4 R8 M2a3（r8m2a3）报告：M2 有效预注册修正、双失败恢复索引与时序、对照映射、状态采集规划与正式判定器验证

> 阶段：P05-S4 子轮次 R8 M2a3（r8m2a3，不是新正式阶段）。  
> 本轮只完成进入 M2b 前必要的最小装置/预注册修正：  
> 1. 不运行任何 S4 驱动、运行器或 gdb；  
> 2. 运行不链接 S4 的合成数据自检，经本轮脚本和 safe_run；  
> 3. 不修改 S4/，不修改历史脚本、判定器或历史冻结预注册；  
> 4. 不做 M2b、M2c、M3，不跑 make test，不展开 Python/Lua E2E；  
> 5. 不宣布任何正式阶段完成，不询问签收；  
> 6. 不将规划建议登记成用户已批准的裁决；  
> 7. 不重做已经有效的构建、搜索表和历史证据；只修本任务指定缺口。

---

## 1. 开工基线与门禁核对

### 1.1 开工要求核对
- **HEAD**：`c66b7d2ca11927b5de652e5db8cfd8e7e215fbc8`（r8m2a2 记录提交，核对一致）
- **HEAD:S4**：`6cff923a02baf19e01966b2339755cbf3a5deeef`（F3 被测树，核对一致）
- **判定器 `testing/d003/judge_d003.py` sha256**：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`（核对一致）
- **历史冻结预注册 `PREREG_M2_R8_M2a2.tsv` sha256**：`1b60f95ccb1ab4b77e26d71fc1d9bf4f4fee25c29092ae0c3620a6c9e42be7ce`（保持逐字节不变）

### 1.2 开工门禁（`GATE_R8_M2a3_start.txt`）
- 本轮 start 门禁经 `sh testing/d003/safe_run.sh p05-s4r8/m2a3 -- sh testing/d003/stage_s4/gate_r8m2a3.sh p05-s4r8/m2a3 GATE_R8_M2a3_start.txt start 0 e3b0c442...` 运行通过，`PYTHON_CHECKS_FAILS=0`，`FAILS=0`。
- **基线构建产物清单**（`STRAY_BASELINE_R8_M2a3.tsv`）：准确记录 `testing/d003/__pycache__/judge_d003.cpython-314.pyc`（17900 B）与 `matrix_r2.cpython-314.pyc`（17250 B）及其历史 mtime。
- **`/tmp` 顶层只读快照**：条目数 0，sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。
- **门禁脚本差异**（`GATE_DIFF_R8_M2a3.txt`）：记录 `gate_r8m2a3.sh`、`gate_check_r8m2a3.py` 等相对于 r8m2a2 的规范化差异。

---

## 2. 静态审计发现与修正（`PREREG_EXECUTABILITY_AUDIT_R8_M2a3.tsv`）

通过 `audit_prereg_r8m2a3.py` 逐行扫描原 150 行预注册，全面定位可执行性缺口与定义冲突，共产生 174 处审计项（按严重度：CONFLICT 111，GAP 55，DEFECT 8）：

1. **私有状态采集器冲突（GDB_CONFLICT，49 处）**：
   - M2-01（12 点）、M2-04（2 点）、M2-05（4 点）以及 M2-03（31 点）在原表中均登记了 `exp_I1..I6=HOLD`，但其 `gdb_script` 字段全部写为 `-`。若不挂载 gdb 脚本，无法在 `r6_probe` 或 CLM 处读取私有指针与状态哈希。
2. **对照绑定缺口（CONTROL_BINDING，49 处）**：
   - 原表中除 `control_group=NO/YES` 之外，完全未指明测试点应与哪一个对照行比较，且缺少对比输出文件的调用序号（`output_call` 与 `control_output_call`）。
3. **M2-04 双失败恢复时序严重缺陷（SNAPSHOT_INDICES 6 处，I6_BINDING 2 处，DUAL_FAILURE 2 处）**：
   - 原表登记 `retry_call=2`、`k_retry=3`，但在实际驱动源码中，`call2` 是第二次注入失败事件（$rc_2=20$），根本不是成功恢复！真正的重试成功恢复发生在 `call3`（$rc_3=0$），对应快照为 `k=4`。
   - 原表未登记 `exp_rc3`，且 I6 输出对比错误指向了失败的 `call2`。
4. **Sanitizer 证据与私有状态冲突（SANITIZER，62 处）**：
   - 原表在 M2-03 同时登记了 `exp_I7=HOLD` 与 `exp_san=0`，两者定义重叠；更严重的是，原表为独立的 sanitizer 进程填写了 `I1..I6=HOLD`，但 gdb 并未也不能稳定挂载于 ASan 进程上，构成虚构私有状态观察入口的冲突。
5. **M2-09-01-F2 身份缺失（IDENTITY，2 处）**：
   - 原表中 F2 对照点的 `driver`、`driver_sha256`、`lib_sha256` 均缺省为 `-`。

---

## 3. 有效预注册修订（`PREREG_M2_EFFECTIVE_R8_M2a3.tsv`）

严格遵循“不得改原期望来消除未来 MISMATCH”、“保留原 150 行 point_id、driver/env、事实期望与 60/90 分类”原则，生成有效预注册，并由本轮 ERRATA 追加说明替代关系：

- **有效预注册文件名**：`PREREG_M2_EFFECTIVE_R8_M2a3.tsv`
- **SHA256**：`27e33b27ae4a7202e402e223a73f2634b66d70a1288596622be7071280a20a09`
- **UTC 冻结时间**：`2026-10-15T23:29:18Z`（保存在 `PREREG_M2_EFFECTIVE_R8_M2a3_TIMESTAMP_UTC.txt`）
- **字段扩展与规范化**：
  1. 显式增加 `target_layer`：明确各测试点与对照点目标层（例如 M2-01 为层 1，M2-05 按 P0/P2/PP1/PP2 分别指定 0, 2, 1, 2）。
  2. 显式增加 `control_point_id`：明确测试点绑定的对照行 ID。
  3. 显式增加 `output_call` 与 `control_output_call`：单次失败指定 2，双目标恢复指定 3，无注入对照指定 1。
  4. 显式增加 `exp_rc3`：双目标恢复明确登记 $rc_3=0$。
  5. 明确 `gdb_script` 与 `gdb_script_sha256`：M2-01、M2-04、M2-05 正式指定 `testing/d003/stage_s4/r6c_state_r8m2a3.gdb`（sha256 `5afecd95cc5a914e7ce8d7d6f054daea0d3942b294503833ae28ac59b7ce7221`）；M2-10 明确 `m210_b_r8m2a2_R2.gdb`（sha256 `bbab8579...`）。
  6. 依据 R7 登记表补齐 M2-09-01-F2 驱动为 `seam-fmmret-F2`（sha256 `a4061e4c...`，库 sha256 `b513f840...`）。
  7. 修正 M2-03 sanitizer 行：私有状态 I1–I6 明确标为 `UNOBSERVED`，`exp_I7=HOLD` 明确表征 `exp_san=0`（无内存安全违规）。
- **字段变动明细**：`PREREG_DIFF_R8_M2a3.tsv` 共记录 230 项精准差异。
- **勘误登记**：在 `checkpoints/p05/registries/s4r8/ERRATA_8.txt` 追加 E8-96–E8-100。

---

## 4. 双失败恢复索引、时序与对照规范（M2-04）

依据实际驱动源码（`driver_r6b_state.cpp` 与 `driver_r8m2a2_layers_R2.cpp`）及双目标注入逻辑（`inject_r8m2a2_dual_R3.cpp`），全面理顺双目标失败恢复事件链，不虚构任何快照点：

| 事件 | 对应调用 | 调用前快照 | 失败/完成快照 | 目标层 | 返回码断言 | 命中计数 | 适用不变量 |
|---|---|---|---|---|---|---|---|
| 第一次失败 | `call1` | $k=0$ | $k=1$ | 同层：层 1<br>跨层：层 1（Slab1） | $rc_1 = 20$ | 1 | I1（失败层模式为空），I4'（求解状态锁步） |
| 重试前状态 | — | — | $k=2$ | — | — | — | 重试前基准 |
| 第二次失败 | `call2` | $k=2$ | $k=3$ | 同层：层 1<br>跨层：层 2（Slab2） | $rc_2 = 20$ | 2 | 检查第二次失败目标层在 $k=3$ 模式为空 |
| 恢复前状态 | — | — | $k=3$ | — | — | — | 恢复重算基准 |
| 最终成功恢复 | `call3` | $k=3$ | $k=4$ | 同层：层 1<br>跨层：层 2（Slab2） | $rc_3 = 0$ | 2 | **I5**：重试重算最小性与 $rc_3=0$；<br>**I6**：`call3.txt` 输出与对照组一致 |

对照组同样在 `call3` 采集输出（`control_output_call = 3`），与测试点的 `call3.txt` 进行逐字节一致性断言。

---

## 5. 对照映射总表（`CONTROL_MAPPING_R8_M2a3.tsv`）

共确立 28 对显式映射关系（12 对 M2-01、2 对 M2-04、4 对 M2-05、1 对 M2-06、9 对 M2-07）：
- **M2-01**：12 个测试点精确映射至同模式、同 NG、同驱动的 9 个 M2-01-CTRL 对照点，比较 `call2.txt`。
- **M2-04**：同层双目标映射至 `M2-04-CTRL-01-F3`，跨层双目标映射至 `M2-04-CTRL-02-F3`（PP1 布局），比较 `call3.txt`。
- **M2-05**：P0/P2/PP1/PP2 布局测试点分别映射至同布局的 `M2-05-CTRL-*` 对照点，比较 `call2.txt`。
- **M2-06**：tensor nanbuf 注入点映射至 `M2-06-CTRL-01-F3`，比较 `call1.txt`。
- **M2-07**：9 个模式在 NG=5 的代表性注入点分别映射至同模式 NG=5 的 `M2-07-CTRL-*-ng5-F3` 对照点，比较 `call1.txt`。
- 其余行：M2-03 固有判定 `exp_san=0` 无需外部对照；M2-09 为 clean 对照自检；M2-10 为基线诊断点。

---

## 6. 不变量规范与状态采集规划（`INVARIANT_SPEC_R8_M2a3.md` / `STATE_COLLECTION_PLAN_R8_M2a3.tsv`）

### 6.1 不变量规范（`INVARIANT_SPEC_R8_M2a3.md`）
- 严格遵循 R6c v2 定义：I1 失败层 modes_null 1；I2 其他层保持；I3 PolBasis 场缓存一致（其余模式 N/A）；I4' 求解状态与 modes 锁步；I5 重试区间最小重算与返回码 0；I6 恢复输出与对照一致。
- 明确 I7 关系：`I7 == HOLD` 当且仅当 `san_reports == 0`，不重复设置独立断言。
- 明确独立 sanitizer 进程私有状态记为 `UNOBSERVED`，彻底消除由于未挂载 gdb 导致的形式冲突。

### 6.2 状态采集规划（`STATE_COLLECTION_PLAN_R8_M2a3.tsv`）
- 静态 `nm -C` 符号核验结果：
  - `init-F3-dbg`：含 `r6_probe`、`Simulation_ComputeLayerModes`、`Simulation_GetLayerSolution`；
  - `polyinj-F3-dbg`：含 `r6_probe`、`Simulation_ComputeLayerModes`、`Simulation_GetLayerSolution`；
  - `dual-F3-dbg`：含 `r6_probe`、`Simulation_ComputeLayerModes`、`Simulation_GetLayerSolution`；
  - `layers-F3-dbg`：含 `r6_probe`、`Simulation_ComputeLayerModes`、`Simulation_GetLayerSolution`；
  - `layers-dual-F3-dbg`：含 `r6_probe`、`Simulation_ComputeLayerModes`、`Simulation_GetLayerSolution`；
  - `r6dnv1-B-dbg`：含 `r6_probe`、`Simulation_ComputeLayerModes` 及预设断点。
- 逐点规划 150 行的采集器类型、断点符号、快照区间及适用范围，完全静态闭合。

---

## 7. 正式判定器与合成阳性对照

### 7.1 正式判定器实现（`verdict_m2_r8m2a3.py`）
- **只读导入校验**：核验 `testing/d003/judge_d003.py` sha256（`d2d04145...`）后导入，禁止就地修改判定器。
- **两遍独立对比**：分别对比 pass 1 与 pass 2 是否满足预期，单独统计与输出 `MISMATCH` 与 `FLAKY`。
- **全事实覆盖**：全面覆盖 $rc_1, rc_2, rc_3, signal, hit, class, san\_reports, I_1 \dots I_7$。
- **支持 NZ 记号**：$rc \ne 0$ 判通过，$rc=0$ 判 MISMATCH。
- **输入与契约防御**：全面检查 ID 唯一性、缺行、多行、树身份一致性、gdb 私有状态完整性、对照映射及输出 dump 文件存在性。输出路径支持任意指定，拒绝覆盖。

### 7.2 合成数据阳性对照结果（`POSCTRL_M2_R8_M2a3_R2.txt`）
通过 `posctrl_m2_r8m2a3.py` 调用正式判定脚本，对不链接 S4 的合成数据进行 11 组情形自检，全部符合事先设定的预期：

| 用例代号 | 测试目标 | 判定器预期行为 | 实测结果 |
|---|---|---|---|
| **Case A** | 完全匹配 | 全部 5 个合成点全 MATCH，MISMATCH=0, FLAKY=0, SCHEMA_ERRORS=0 | **PASS** |
| **Case B** | 改 rc1 | 准确捕获 `SYN-REP-01` 产生 MISMATCH（`exp_rc1`），总 MISMATCH=1 | **PASS** |
| **Case C** | 仅第二遍改值 | 准确捕获 `SYN-REP-01` 产生 FLAKY（`rc1`），总 FLAKY=1 | **PASS** |
| **Case D** | NZ 记号自检 | D0（$rc_1=0$）判 MISMATCH；D20（$rc_1=20$）判 MATCH | **PASS** |
| **Case E** | 改 I 观察值 | 准确捕获 `SYN-REP-01` 在 `exp_I1` 发生 MISMATCH | **PASS** |
| **Case F** | 双失败后 rc3 非零 | 准确捕获 `SYN-DUAL-01` 在 `exp_rc3` 发生 MISMATCH（20 != 0） | **PASS** |
| **Case G** | 缺 gdb 状态 | 准确拦截缺失状态行并判 `SCHEMA_ERROR`（`MISSING_GDB_STATE_PASS1`） | **PASS** |
| **Case H** | 重复/缺失/多余 ID | H1（重复）、H2（缺失）、H3（多余）全部准确判 `SCHEMA_ERROR` | **PASS** |
| **Case I** | tree 不符 | 准确捕获 `SYN-REP-01` 树不符（B != F3）并判 `SCHEMA_ERROR` | **PASS** |
| **Case J** | 控制点或输出 dump 错误 | 准确捕获双目标恢复 `call3.txt` 输出与对照不一致并判 `SCHEMA_ERROR` | **PASS** |
| **Case K** | sanitizer 报告非零 | 准确捕获 `SYN-SAN-01` 在 `exp_san` 发生 MISMATCH（1 != 0） | **PASS** |

**自检结论**：`POSCTRL_M2_R8_M2a3 total=11 passed=11 failed=0 -> PASS`。

---

## 8. 待处理事项与后续交接方案（严格维持原案，不越权裁决）

1. **M2-02（阶段 e）NOT_FOUND_IN_SCOPE 去向**：
   - 维持 r8m2a2 搜索表结果（227 处已登记点 stage e 恒为 0；CLM 体外 77 处非 D003 范围），状态为 `NOT_FOUND_IN_SCOPE`，等待规划者与用户在审核时裁决转入 S5 或关闭。
2. **M2-08（类别 C）原网格 NOT_FOUND 与 1D+FFT 候选**：
   - 维持 r8m2a2 搜索表结果（63 行网格点无执行期 FMM generic butterfly 分配），状态为 `NOT_FOUND`。
   - 网格外 1D+FFT 候选列为 `NEEDS_NEW_DRIVER_SCOPE_EXPANSION`，等待规划者与用户裁决是否扩大驱动范围。
3. **已披露偏离是否接受**：
   - r8m2a2 历史 safe_run 偏离（内联命令、dual_harness 运行等共 14 条）等待用户裁决接受。
4. **M2-01 五个 `win:64` 点的后续处理方案**：
   - 本轮严格**不混入**有效运行矩阵（维持 150 点不变）。
   - **后续交接方案（四步法）**：
     1. **诊断运行**：在 M2b 阶段，通过挂载 `r6c_state_r8m2a3.gdb` 与断点追踪，单步确认第 64 次 window malloc 在 call1 内部的实际命中位置；
     2. **确认索引**：依据实际 trace 确定瞬态快照索引，观察结果必须明确标记为 `INFLUENCED`，严禁回填假装为事前预言；
     3. **补预注册**：发布增补预注册表并计算冻结 SHA256；
     4. **正式运行**：进入两遍正式运行与判决。

---

## 9. 完整性检查（`COMPLETENESS_R8_M2a3.tsv`）

通过 `completeness_r8m2a3.py` 逐点检验全部 150 个预注册点的端到端证据链（采集入口、来源依据、分析规则、对照绑定）：
- 检查点总数：150 点
- 满足完整性判定点数：150 点
- 缺口/阻塞点数：0 点
- **完整性结果**：`COMPLETENESS_R8_M2a3 total=150 PASS=150 FAIL=0`。

---

## 10. 执行纪律、违规与偏离披露

### 10.1 表一：越界写入尝试表
无（无任何仓库外路径写入尝试，未向 `/tmp` 写入）。

### 10.2 表二：工具/脚本事件表与偏离披露
| 序号 | 发生时间（UTC） | 命令 / 事件摘要 | 是否落盘 | 处置说明 |
|---|---|---|---|---|
| 1 | 2026-10-15T23:35:10Z | `posctrl_m2_r8m2a3.py` 首次运行（R1）由于 set 运算类型笔误抛出 TypeError | 落盘至 R1 输出 | 依据 U17 保留原输出 `POSCTRL_M2_R8_M2a3.txt`，修正代码后以 `_R2` 重新运行全通过 |

### 10.3 根目录临时区快照
- **开工快照**：条目数 0，sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。
- **收尾快照**：条目数 0，sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。

---

## 11. 总结

本轮子轮次 R8 M2a3（r8m2a3）以最小必要修正原则，彻底解决了 M2 进入正式执行前的状态采集入口缺失、双失败恢复调用序号混淆、对照映射缺位及 sanitizer 判定冲突等核心隐患，冻结了 150 行有效预注册，并经 11 组合成阳性对照验证了正式判定脚本的严密性。

本轮未运行任何实际 S4 驱动或 gdb，未修改 `S4/` 源码，未修改历史冻结注册表。本轮工作已全部完成，等待规划者与用户审核。
