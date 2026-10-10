# D002 A-36 判定规则修正（2026-10-10，执行者自审）

状态口径：**执行者自审的判定规则修正，尚未经独立审核**。本修正不改变 S4 产品源码（`S4/` 子树仍为 `1d738e64f9864a475fdb3de34cd3601605df2c64`），不改变 `PLAN.json` 中的任何阈值（`eig_rel_tol`、`residual_tol`、`vector_norm_tol`、`padding_init_value`），不放宽候选判定。

## 1. 问题

固定旧基线 `963ccf1` 的 `asan_baseline` 身份中，A-36 在 `run_d002.py` 的 `BASELINE_SIGNATURE` 里被列为 `must_pass`。沙箱外复跑（`/tmp/s4-master-integration-native-20261010`，只读引用）中，A-36 以 `rc=1` 退出，stderr 为 ASan SEGV。签名因此不满足（`not_passing=['A-36']`，`damaged=[]`，`not_failing=[]`），聚合器判为 unexpected。

同一身份中 A-07、A-37 与 A-36 走同一条 values-only 分支，已在 round-5 校正为 `may_fail`；A-36 没有同等规模的重复样本，分类时只依据了通过的记录。

## 2. 机制（源码与运行记录互证）

基线 `S4/RNP/Eigensystems.cpp`（`963ccf1`）：

| 行 | 内容 |
|---|---|
| 4618 | `int info;`，未初始化 |
| 4661 | 仅值分支 `zhseqr_('E', 'N', ...)`，返回值被丢弃，`info` 未赋值 |
| 4664 | `if(info == 0){`，读取未初始化的 `info` |
| 4715 | `scalea` 时 `RescaleMatrix<'G'>(..., n - info, 1, &w[info], ...)`，未初始化的 `info` 作为下标 |

候选 `5cf534c` 的对应修复：4620 `int info;`，4663 `info = zhseqr_('E', 'N', ...)`，4717 同一调用。产品修复本身不变，本修正只改判定器。

ASan 栈（诊断、沙箱外复跑与重复运行的全部 SEGV 记录指向同一站点，逐条核对见第 3 节）：

```
#1 RNP::TLASupport::RescaleMatrix<'G'>(...)  TLASupport.h:429
#2 RNP::Eigensystem(...)                     Eigensystems.cpp:4715
```

崩溃为 `ERROR: AddressSanitizer: SEGV on unknown address`，读地址远离 `w`，与 `&w[info]` 下标为垃圾值一致。

## 3. 证据

原始记录全部保留在 `testing/d002/evidence/A36_RAW_20261010.tar.gz`（由 `/tmp` 与 scratch 诊断目录打包，原件未修改，未重写任何返回码）。

asan_baseline 身份的 A-36 记录：

| 来源 | 次数 | 结果 |
|---|---|---|
| 2026-10-09 保存运行 `checkpoints/p04/evidence/d002/JUDGE_asan_baseline.json` 与 `checkpoints/p04/independent-evidence/.../JUDGE_asan_baseline.json` | 2 | pass（info 0） |
| 2026-10-09 最终流水线控制归档 `testing/d002/tests/fixtures/p04_schema2_control.tar.gz` | 1 | rc 0，pass |
| 沙箱内原始流水线 `/tmp/s4-master-integration-results-20261010` | 1 | **不作为依据**：asan_baseline、asan_candidate、seam_asan_baseline 的 59 个用例全部 rc=1，stderr 为 LeakSanitizer `does not work under ptrace` 致命错误；A-36 判为 `exit_unknown`，与缺陷机制无关 |
| 沙箱外复跑 `/tmp/s4-master-integration-native-20261010` | 1 | rc 1，ASan SEGV 于 4715 站点 |
| 定向诊断 `/tmp/s4-master-integration-a36-diagnostic-20261010` 五次 | 5 | rc 1,1,1,0,0；三次 SEGV 于 4715 站点，两次 pass（info 0） |
| 本轮重复（scratch 构建，同一 `build` 命令、`963ccf1` 归档） | 20 | 13 次 SEGV 于 4715 站点，7 次 pass（info 0） |

2026-10-10 的 asan_baseline 重跑合计 26 次（沙箱外复跑 1 + 诊断 5 + 重复 20）：**17 次在注册站点崩溃，9 次通过（info 0）**，同一基线、同一输入、不同运行结果。

其它身份：

| 身份 | 次数 | 结果 |
|---|---|---|
| ord_baseline 重复 | 20 | 20/20 pass，info 0 |
| seam_asan_baseline 重复 | 20 | 20/20 SEGV 于 4715 站点 |
| seam_asan_baseline 沙箱外复跑与控制归档 | 2 | 均为 SEGV 于 4715 站点 |
| asan_candidate 诊断 | 5 | 5/5 pass，info 0（candidate 无崩溃） |

## 4. 分类决定（分身份）

- **ord_baseline**：保持 `must_pass`。20/20 重复与历次保存记录均为 info 0。该处同样属于未初始化读取，只是观察到的结果稳定；若将来出现失败，应按本文同一方法重新分类，不得在此直接放宽。
- **asan_baseline**：由 `must_pass` 改为 `may_fail`。通过（info 0）与注册站点崩溃都允许；其它任何 ASan 报告、未注册退出、损坏记录均拒绝（见第 5 节）。
- **seam_asan_baseline**：保持 `must_fail`，因为 20/20 重复与控制归档都在注册站点崩溃；新增站点规则，使其它崩溃不能冒充缺陷。
- **asan_candidate / seam_asan_candidate / ord_candidate**：不变，A-36 仍为 `must_pass`，所有失败均为候选失败。

## 5. 判定规则变更（`testing/d002/run_d002.py`）

1. `BASELINE_SIGNATURE["asan_baseline"]["may_fail"]` 加入 `A-36`，`must_pass` 去掉 `A-36`。
2. 新增 `REGISTERED_SITES`，对 `(asan_baseline, A-36)` 与 `(seam_asan_baseline, A-36)` 要求：报告含 `ERROR: AddressSanitizer: SEGV on unknown address`，且连续两帧为 `RNP::TLASupport::RescaleMatrix<…>` 后接 `RNP::Eigensystem(…)` 位于 `Eigensystems.cpp:4715`。
3. `verify_integrity` 在异常退出分支中调用 `site_registered()`。不满足站点的 ASan 报告为 `exit_unknown`（非注册机制），不是缺陷证据，并计入 `damaged`。

未变动：`PLAN.json`、全部阈值、候选的判定、rc=-11 的规则、UBSan 注册形式、损坏记录与身份检查、聚合器逻辑（聚合器重新调用同一判定器）。

## 6. 为何这不是掩盖产品失败

- 候选 A-36 仍为严格 `must_pass`：`asan_candidate` 诊断 5/5、正式 53/53、seam 58/58 均要求数值与身份完整。
- 基线 A-36 的通过记录仍走完整 verdict（特征值、残差、向量范数、padding、身份）；只有“站点崩溃”和“info 非零导致的判定失败”被接受，且二者都是同一未初始化 `info` 的后果。
- 任何其它崩溃位置、其它 ASan 报告、rc=-11、损坏或错误身份的 A-36 记录，都会使签名不成立。

## 7. 测试

`testing/d002/test_run_d002.py`：124 → 137 项，全部通过。新增 13 项：

- `A36AsanBaselineTests`（9 项）：may_fail 分类；info 0 通过；info 非零判定失败；站点崩溃为缺陷；行号 4700 的崩溃、其它调用者、heap-buffer-overflow 站点、rc=-11、错误身份的部分记录均为损坏（拒绝）。
- `SeamBaselineA36Tests`（2 项）：站点崩溃为 seam 缺陷；其它行的崩溃不算缺陷。
- `AsanCandidateA36Tests`（1 项）：候选上的同一基线崩溃不被接受。
- `BaselineA36ClassTests`（1 项）：各身份分类表与站点表。

变异检查（在 scratch 副本上进行，未改仓库）：
- 关闭站点规则（`site_registered` 恒真）：4 个站点负例失败。
- 把 A-36 放回 asan_baseline 的 `must_pass`：4 个用例失败（含分类、非零 info、站点通过）。

## 8. 复跑的判定结果（新判定器，只读副本）

对上述 26 次 2026-10-10 asan_baseline 运行、20 次 ord 重复、20 次 seam 重复与 5 次 candidate 诊断，逐次以新判定器判定 A-36：全部 70 条记录只落在 `ok`（通过）或 `exit`（注册站点）两类，无 `exit_unknown`、无 `damaged`。

沙箱外复跑整体签名：`asan_baseline` 由 `ok=False`（`not_passing=['A-36']`）变为 `ok=True`（`not_failing=[]`，`not_passing=[]`，`damaged=[]`）；`seam_asan_baseline` 仍为 `ok=True`；`asan_candidate` 53/53、`seam_asan_candidate` 58/58 仍接受。

## 9. 残余风险与限制

- ord_baseline 的 A-36 仍是未初始化读取，本轮 20/20 通过只是观察，不是证明。
- 站点规则依赖 ASan 符号化（栈帧需显示函数与 `Eigensystems.cpp:4715`）。若报告未符号化，A-36 的基线崩溃会被拒绝（fail-closed），此时须修复符号化环境，不得放宽规则。
- 站点绑定 `963ccf1` 基线的行号；流水线 `BASE` 固定为该提交，行号稳定。
- A-07、A-37 的 asan_baseline 规则仍是通用 ASan 注册机制，未站点化。本轮没有它们的站点证据，未扩大修改范围。
- round-5 对 A-07 的校正依据十份真实诊断（最终审核已接受）；本次 A-36 的校正依据是本轮 26 次重跑，属于新证据，尚未经独立审核。
- 沙箱内 LeakSanitizer 的 ptrace 限制会使正常退出的 ASan 运行失败；正式验收必须在允许 sanitizer 工作的环境中运行，且不得设置 `detect_leaks=0`。

## 10. 复现命令

```sh
# 判定器与测试（仓库内，无写入证据目录）
python3 -I -B testing/d002/test_run_d002.py -v

# 诊断构建（只用于重复观察，不替代正式 build）
git archive 963ccf153855734de968e6cf71477f324e33329c | tar -x -C SCRATCH/src
python3 -I -B testing/d002/run_d002.py build --src-root SCRATCH/src --variant asan_baseline --out-dir SCRATCH/bin
python3 -I -B testing/d002/run_d002.py run --variant asan_baseline --bin SCRATCH/bin/d002_asan_baseline --run-dir SCRATCH/asan/1 --cases A-36
```

`--cases A-36` 产生 `scope=subset` 记录，只用于诊断，不构成验收。
