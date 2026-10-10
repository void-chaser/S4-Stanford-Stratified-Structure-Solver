# D002 A-36 判定规则修正（2026-10-10，执行者自审，修订二）

状态口径：**执行者自审的判定规则修正，尚未经独立审核**。这不是完成修正的前置条件，而是审核前的当前状态。本修正不改变 S4 产品源码（`S4/` 子树仍为 `1d738e64f9864a475fdb3de34cd3601605df2c64`），不改变 `PLAN.json` 中的任何阈值（`eig_rel_tol`、`residual_tol`、`vector_norm_tol`、`padding_init_value`），不放宽候选判定，不改变其他用例的分类。

修订历史：
- 修订一（commit `91bb715`）：asan_baseline 的 A-36 由 `must_pass` 改为 `may_fail`，注册站点崩溃为缺陷证据。
- 修订二（本文件，执行者自审复核后）：补上两个审核反例暴露的缺口。(1) 正常退出的数值失败曾被 `may_fail` 自动接受。(2) 站点检查只做两个独立正则搜索，注册报告后附加的无关 ASan 报告不会被拒绝。

## 1. 问题

固定旧基线 `963ccf1` 的 `asan_baseline` 身份中，A-36（values-only + scalea）的 `info` 未初始化。它在 `run_d002.py` 中原为 `must_pass`，沙箱外复跑中以 `rc=1` 的 ASan SEGV 退出，签名因此不成立（`not_passing=['A-36']`）。

修订一把它放宽为 `may_fail`，但修订一本身仍有两个缺口：

- 反例 CE1：从 `p04_schema2_control.tar.gz` 提取 asan_baseline 的完整控制记录，保持 `rc=0`、`info=0`、身份正确，把 `w 0 …` 改为 `w 0 1 0`。修订一判为 `ok`、`pass=False`，签名仍成立（`eig_rel_err=3.78e+159`）。
- 反例 CE2：合法的注册站点 SEGV 报告之后附加一段 `ERROR: AddressSanitizer: heap-buffer-overflow … #0 … in unrelated_bug`。修订一仍判为注册站点崩溃，签名成立。

两个反例的修正前后判定见第 6 节。

## 2. 机制（源码与运行记录互证）

基线 `S4/RNP/Eigensystems.cpp`（`963ccf1`）：

| 行 | 内容 |
|---|---|
| 4618 | `int info;`，未初始化 |
| 4661 | 仅值分支 `zhseqr_('E', 'N', ...)`，返回值被丢弃，`info` 未赋值 |
| 4664 | `if(info == 0){`，读取未初始化的 `info` |
| 4715 | `scalea` 时 `RescaleMatrix<'G'>(..., n - info, 1, &w[info], ...)` |

`RescaleMatrix<'G'>`（`S4/RNP/TLASupport.h`）对 `j < n`、`i < m` 访问 `a[i + j*lda]`。这里 `m = n - info`、`a = &w[info]`、`n = 1`，因此：

- `1 <= info <= n`：访问 `w[info..n-1]`，在数组内；`info = n` 时 `m = 0`，不访问内存。
- `info` 为负或大于 `n`：`n - info` 按 `size_t` 回绕，循环越出 `w`，表现为 ASan SEGV（或其他越界报告）。

候选 `5cf534c` 的对应修复：4620 `int info;`，4663 `info = zhseqr_('E', 'N', ...)`，4717 同一调用。产品修复本身不变，本修正只改判定器。

## 3. 证据与逐条计数

原始记录保留在 `testing/d002/evidence/A36_RAW_20261010.tar.gz`（由 `/tmp` 与 scratch 诊断目录打包，原件未修改，未重写任何返回码）。

### 3.1 逐条清单（80 条归档原始记录）

以“来源 + 变体 + 运行编号”去重；每条记录只计一次。`scratch/inventory.py` 用修订一与修订二的判定器各判定一遍（结果见第 8 节）。

| 来源 | asan_baseline | asan_candidate | seam_asan_baseline | seam_asan_candidate | ord_baseline | ord_candidate | 合计 |
|---|---|---|---|---|---|---|---|
| 2026-10-09 最终流水线控制归档（每变体 1 条） | 1 通过 | 1 通过 | 1 站点崩溃 | 1 通过 | 1 通过 | 1 通过 | 6 |
| 沙箱外复跑 `/tmp/s4-master-integration-native-20261010`（每变体 1 条） | 1 站点崩溃 | 1 通过 | 1 站点崩溃 | 1 通过 | — | — | 4 |
| 定向诊断 `/tmp/s4-master-integration-a36-diagnostic-20261010` 五次 | 3 站点崩溃 + 2 通过 | 5 通过 | — | — | — | — | 10 |
| 本轮重复 20 次×3 组（scratch 构建，`963ccf1` 归档） | 13 站点崩溃 + 7 通过 | — | 20 站点崩溃 | — | 20 通过 | — | 60 |
| **合计** | **27**（17 崩溃、10 通过） | **7** | **22** | **2** | **21** | **1** | **80** |

2026-10-10 的重跑（不含控制归档）为 74 条：asan_baseline 26（沙箱外复跑 1 + 诊断 5 + 重复 20；17 崩溃、9 通过）；asan_candidate 6；seam_asan_baseline 21；seam_asan_candidate 1；ord_baseline 20。

不计入清单的：
- 沙箱内原始流水线 `/tmp/s4-master-integration-results-20261010`：asan_baseline、asan_candidate、seam_asan_baseline 的 59 个用例全部 `rc=1`，stderr 为 LeakSanitizer `does not work under ptrace` 致命错误，A-36 判为 `exit_unknown`，与缺陷机制无关，不作依据。
- 2026-10-09 的两份保存 JUDGE 摘要（`checkpoints/p04/evidence/d002/JUDGE_asan_baseline.json` 与 `checkpoints/p04/independent-evidence/.../JUDGE_asan_baseline.json`）：只有判定摘要，没有随仓库保存原始 `outs`，无法逐条复判；它们记录的 A-36 为通过，与控制归档一致。

### 3.2 其它身份

- `ord_baseline` 重复 20 次：20/20 通过，info 0。这只是已观察结果，不构成未初始化读取必然通过的证明。
- `seam_asan_baseline` 重复 20 次与控制归档：全部在注册站点崩溃。
- `asan_candidate` 诊断 5 次与控制归档：全部通过，info 0。

## 4. 分类决定（分身份）

- **ord_baseline**：保持 `must_pass`。该处同样读取未初始化的 `info`，但观察结果稳定。若将来失败，应按本文方法重新分类，不得在此直接放宽。
- **asan_baseline**：`may_fail`，但 `may_fail` 只决定签名是否允许其失败，不替代 A-36 的结果规则。A-36 的结果必须属于第 5 节的已登记结果之一。
- **seam_asan_baseline**：保持 `must_fail`。其缺陷签名只能由注册站点崩溃显示，不接受任何数值失败。
- **asan_candidate / seam_asan_candidate / ord_candidate**：不变。A-36 仍为 `must_pass`，所有失败都是候选失败。

## 5. A-36 结果规则（修订二，与代码一致）

代码位置：`testing/d002/run_d002.py` 中的 `REGISTERED_SITES`、`site_registered`、`registered_verdict_failure`、`A36_OUTCOME_VARIANTS`、`A36_NONZERO_INFO_VARIANTS`，以及 `verdict` 与 `judge_case`。

### 5.1 异常退出（rc 非零）

只有同时满足以下条件，才记为注册站点崩溃（`kind=exit`，`basis=registered_site`）：

1. stderr 恰有一个 `ERROR: AddressSanitizer:` 头和一个 `SUMMARY:` 行，二者都是 SEGV；
2. 不含其他 sanitizer 标记（`runtime error:`、`LeakSanitizer`、`ThreadSanitizer`、`MemorySanitizer`、`UndefinedBehaviorSanitizer`）；
3. 恰有一个 `#0` 帧，即恰有一个调用栈；
4. 该调用栈中，`RNP::TLASupport::RescaleMatrix<…>` 紧接着是 `RNP::Eigensystem(…)`，位于 `Eigensystems.cpp:4715`。

其他情况均为 `exit_unknown`，计入 `damaged`。这包括：多个报告、附加的无关报告、报告类型与 SUMMARY 不一致、未符号化的帧（fail-closed）。`site_registered` 因此检查的是“同一份完整报告”，而不是两段独立文字的并存。

### 5.2 正常退出（rc 0，记录完整且身份正确）

判定的顺序是：先 info，再数值（特征值、残差、向量范数、padding）。

| 情形 | `asan_baseline` A-36 | `seam_asan_baseline` A-36 | 候选 |
|---|---|---|---|
| info 0，数值全部通过 | 通过（`pass=True`） | 通过（不构成 must_fail 缺陷） | 通过 |
| info 0，任一数值失败（特征值、残差、padding 等，`reason=numeric`） | `outcome_unregistered`（不是缺陷证据，计入 `damaged`） | `outcome_unregistered` | 失败 |
| info 非零且位于 `[1, n]`（`reason=info`，`n=2`，即 info 为 1 或 2） | 记为 `nonzero_info_window`，签名允许 | `outcome_unregistered` | 失败 |
| info 非零但不在 `[1, n]` | `outcome_unregistered` | `outcome_unregistered` | 失败 |

info 非零时为何属于已确认机制，理由有四点：

1. 源码：仅值分支返回 `info`，而该变量在这条路径上从未被赋值，返回值就是未初始化的读数。
2. 同一身份、同一分支的 A-07 已有 10 份真实诊断，返回的非零 info 正是这种读数（round-5 校正，最终审核已接受）。
3. 既有返回契约：API 用例要求 `info == 0`（`PLAN.json` 的 `expect` 为 `info=0`），非零即违反契约。
4. 窗口：`[1, n]` 之外，第 2 节的 `RescaleMatrix` 循环会越出 `w`，结果是崩溃而不是干净返回；因此干净返回的非零 info 只能落在窗口内。

需要明确的限制：**A-36 在 27 条 asan_baseline 记录中，目前没有任何 rc=0 且 info 非零的观察。** 第 1 条理由依靠 A-07 的同一分支证据，第 4 条依靠代码推导。窗口规则是保守的：它只接受窗口内的值，窗口外一律拒绝。

### 5.3 不变的部分

- `PLAN.json` 与全部阈值；候选的全部判定；rc=-11 的规则；UBSan 注册形式；损坏记录与身份检查；聚合器逻辑（聚合器重新调用同一判定器）。
- 其他历史 `may_fail` 用例（A-07、A-37、C-03）的规则未改，见第 9 节残余风险。

## 6. 两个审核反例的修正前后判定

在修正前后用同一脚本（`scratch/repro/repro_counterexamples.py`，读取同一控制归档与同一固定夹具）判定：

| 反例 | 修订一（修正前） | 修订二（修正后） |
|---|---|---|
| CE1：控制记录，rc 0、info 0，`w 0 1 0` | `kind=ok`，`pass=False`，`signature.ok=True`，**被接受** | `kind=outcome_unregistered`，`pass=False`，`damaged=['A-36']`，`signature.ok=False`，**被拒绝** |
| CE2：注册 SEGV 报告 + 附加无关 ASan 报告 | `kind=exit`，`signature.ok=True`，**被接受** | `kind=exit_unknown`（不在注册站点），`damaged=['A-36']`，`signature.ok=False`，**被拒绝** |

两个反例都已作为回归测试入库（第 7 节），因此仓库测试即可复现这张表；复现脚本本身未入库。

## 7. 测试

`testing/d002/test_run_d002.py`：137 → 151 项，全部通过（修订二新增 15 项，替换 1 项即修订一的 info=8 用例，净增 14 项）。

- `A36AsanBaselineTests`：
  - 窗口：info 1 与 2 为登记结果（`basis=nonzero_info_window`）；info -1、3、8 为 `outcome_unregistered`。
  - 数值：`w 0 1 0` 与相对误差 1e-3 的有限误差均使签名失败；相对扰动 1e-13 的正确控制通过。
  - 缺失记录：删去 `w 1` 为损坏（`evidence`）。
  - 站点：注册报告通过（`basis=registered_site`）；行号 4700、其他调用者、heap-buffer-overflow、rc=-11、错误身份的部分记录、无关报告附加、重复报告、SUMMARY 类型不一致、其他 sanitizer 标记、未符号化的帧，均拒绝。
- `A36RuleFunctionTests`：窗口规则只对 asan_baseline 有效；候选与其他用例不受影响；站点检查只接受一个完整注册报告。
- `AsanCandidateA36Tests`：候选上的注册报告、数值失败、窗口内非零 info 均不被接受。
- `SeamBaselineA36Tests`、`BaselineA36ClassTests`：保留修订一的站点与分类检查。

变异检查（在 scratch 副本上进行，未改仓库）：
- 去掉窗口限制（任意非零 info 均接受）：`info=-1, 3, 8` 的用例与规则函数用例失败。
- 把数值失败也当作注册结果：2 个数值反例与规则函数用例失败。
- 去掉单报告检查（只保留搜索）：附加报告、重复报告、其他 sanitizer 标记、规则函数的站点用例失败。SUMMARY 类型检查仍由站点规则中的 SUMMARY 正则拦截，属于纵深防御。

## 8. 复跑的判定结果（修订一与修订二并列）

对第 3.1 节的 80 条记录，分别用 `cada030` 的判定器（修订一）与当前判定器（修订二）逐条判定 A-36。结果：**80 条中没有任何一条的结论改变**（通过仍为通过，注册站点崩溃仍为注册站点崩溃）。修订二新增拒绝的情形（数值失败、窗口外的非零 info、多报告或附加报告）在归档中均不存在；它们只由第 6、7 节的反例与单元测试覆盖。

按身份汇总：

| 身份 | 修订一与修订二的结果 |
|---|---|
| asan_baseline（27） | 17 条 `exit`（注册站点）、10 条 `ok` 通过 |
| asan_candidate（7） | 7 条通过 |
| seam_asan_baseline（22） | 22 条 `exit`（注册站点） |
| seam_asan_candidate（2） | 2 条通过 |
| ord_baseline（21） | 21 条通过 |
| ord_candidate（1） | 1 条通过 |

沙箱外复跑整体签名：`asan_baseline` 为 `ok=True`，`not_failing=[]`，`not_passing=[]`，`damaged=[]`；`seam_asan_baseline` 仍为 `ok=True`；`asan_candidate` 53/53 与 `seam_asan_candidate` 58/58 仍被接受。

正式流水线的结果见交付报告；它是在修订二的最终提交上从全新 checkout 执行的。

## 9. 残余风险与限制

- ord_baseline 的 A-36 仍是未初始化读取。20/20 通过只是观察，不是证明。
- 窗口规则依赖第 5.2 节的代码推导。A-36 目前没有 rc=0 且 info 非零的观察；这条规则在 A-36 上尚未被实际数据直接证实。
- 站点规则依赖 ASan 符号化。未符号化的报告被拒绝（fail-closed）；此时应修复符号化环境，而不是放宽规则。
- 站点行号 4715 绑定 `963ccf1`，流水线 `BASE` 固定为该提交。
- **A-07、A-37、C-03 在 asan_baseline 仍是通用的 `may_fail`**：它们的任何判定失败都会被签名接受（只要记录完整），与 A-36 修订二的收紧不同。本轮没有这些用例的数值或站点证据，按要求没有改动它们的规则。这是一个已知的残余缺口，需要单独立项。
- round-5 对 A-07 的校正依据十份真实诊断（最终审核已接受）；本文 A-36 的校正依据是 2026-10-10 的重跑及修订二，尚未经独立审核。
- 沙箱内 LeakSanitizer 的 ptrace 限制会使正常退出的 ASan 运行失败。正式验收必须在允许 sanitizer 工作的环境中运行，且不得设置 `detect_leaks=0`。

## 10. 复现命令

```sh
# 判定器与测试（仓库内，不写入证据目录）
python3 -I -B testing/d002/test_run_d002.py -v

# 诊断构建（只用于重复观察，不替代正式 build）
git archive 963ccf153855734de968e6cf71477f324e33329c | tar -x -C SCRATCH/src
python3 -I -B testing/d002/run_d002.py build --src-root SCRATCH/src --variant asan_baseline --out-dir SCRATCH/bin
python3 -I -B testing/d002/run_d002.py run --variant asan_baseline --bin SCRATCH/bin/d002_asan_baseline --run-dir SCRATCH/asan/1 --cases A-36
```

`--cases A-36` 产生 `scope=subset` 记录，只用于诊断，不构成验收。
