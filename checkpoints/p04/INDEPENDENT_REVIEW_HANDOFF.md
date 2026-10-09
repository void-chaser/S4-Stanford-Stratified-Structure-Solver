# 独立审核交接：P04 第一阶段（D001 / D002）

**这是执行者的交接，不是独立验收。** 执行者自检结果不能冒充独立审核；审核人应在自己的全新 checkout 中重新运行，并判断证据是否充分。

## 1. 审核对象

| 项 | 值 |
|---|---|
| 基线 | `963ccf153855734de968e6cf71477f324e33329c` |
| 源码修复 | `44f4a097f8c88ba34ee21c4f1353ac8682fb214e` |
| 终验 tip（须以它为审核对象） | `8b13d67b792516baf0074a2fda73081dcdec7f7f`（产品代码与 44f4a09 相同；仅改流水线脚本标签） |
| 分支（本地，未推送） | `codex/p04-d001-d002-production-20261009T082631Z` |
| 产品差异 | `checkpoints/p04/evidence/PRODUCT_DIFF_963ccf1..8b13d67.patch`（S4/ 与 .gitignore，8 个文件，+140/−36） |
| 来源补丁 | `checkpoints/p04/review-inputs/`（选定 hunk 的来源；补丁 SHA256 `1adef26c…`） |

未推送，未建 PR，未合并 master，未关闭任何 issue 或 milestone。

## 2. 审核人应重点核对的点

1. **zgebak_ 索引（D001）**：`S4/RNP/Eigensystems.cpp` 中 `i = ilo - 1 - ii` 与 `k = (size_t)((int)scale[i] - 1)`。核对 0-based 换算：LAPACK 的 `I = ILO - II`（1-based）等价于此。scale[] 由 zgebal 以 1-based 写入（`--scale` 之后的 `scale[l] = j`）。
2. **zhseqr 状态（D002）**：仅值分支 `info = zhseqr_('E','N',…)` 是否被使用，并由 `RNP::Eigensystem` 返回。
3. **NULL z 偏移（D002）**：`zlaqr0_`/`zlaqr3_` 只在 `wantz` 为真时做 `z__ -= (1+ldz)`，并把 `_z__` 传给 zlaqr3_。核对 zlaqr3_ 中 z__ 除偏移外无其它使用。
4. **工作区归属（D002）**：`rcwa.cpp` 的 `owns_work` 在 lwork 被覆盖为 `(size_t)-1` 之前判定；失败路径不释放调用者的缓冲区，也不泄漏内部缓冲区。
5. **失败不安装（D002）**：`S4.cpp` 中 `Simulation_DiscardLayerModes` 只在 `ComputeLayerModes` 内、且 `*layer_modes` 为本次新建时调用；返回 20 之前无残留指针。核对 query 分支的 `S4_free(rwork)`。
6. **错误码 20 的上行传播**：ComputeLayerSolution、GetPropagationConstants、GetSMatrix、各 public API 的返回检查；Lua `GetAmplitudes` 的新检查。
7. **测试装置隔离**：普通构建不含 `S4_TEST_EIGEN_INFO` 与 `D002_TEST_SEAM`（`strings` 检查，结果为 0）。seam 头文件只经测试构建的 `-I` 引用。
8. **阈值未放宽**：D002 阈值来自 `testing/d002/PLAN.json`（冻结）；D001 绝对阈值 1e-10。检查 `run_d002.py` 与 `run_d001_*.py` 中没有任何阈值被改动。
9. **独立参考**：`oracle_d001.py`、`oracle_d001_ext.py` 只使用输入常数，不 import S4、不读取 solver 输出。
10. **阳性对照**：`run_d002.py positives` 中三个检测器确实报告注册签名。

## 3. 复现（在全新 checkout 中）

```sh
git clone -b codex/p04-d001-d002-production-20261009T082631Z <repo-url-or-path> /tmp/p04-review   # 不要在主检出中做
cd /tmp/p04-review && git checkout 8b13d67
sh testing/p04_run_all.sh /tmp/p04-review-run
cat /tmp/p04-review-run/STEPS.txt
```

预期（执行者的终验结果）：candidate 相关步骤返回 0；`d001_frozen_baseline`、`d001_ext_baseline`、`d002_judge_*_baseline` 返回 1（缺陷对照，预期失败）。

## 4. 执行者的终验结果（须由审核人独立复核）

| 项 | 结果 |
|---|---|
| D001 冻结 12 例 candidate | 12/12；baseline 8/12（失败为 N=9 的 B、C） |
| D001 扩展 113 例 candidate | 113/113；baseline 60/113 |
| D002 ord / asan / seam candidate | 53/53、53/53、58/58（另 5 个 seam 例不适用，1 个契约探针仅记录） |
| D002 baseline（ord / asan / seam） | 31/53、27/53、27/58（asan 结果在两次运行间为 25 与 27） |
| 阳性对照 | 3/3 |
| S4 错误码 20（Python / Lua / C） | 33/33 |
| s4test 套件（两棵树） | 257 OK，skipped=1（结果逐项一致） |
| Lua 回归、Python 冒烟 | 通过 |

原始数据位置：执行者的运行目录 `/srv/nvme/projects/S4-p04-runs-20261009T082631Z/verify-final/`（不在 Git 中，审核人可自行重新生成）；可提交的摘要在 `checkpoints/p04/evidence/`。

## 5. 已知边界（审核人需判断是否接受）

* **HAVE_LAPACK 分支未原生运行**（只做了 `-fsyntax-only`）。
* **query 失败路径没有注入测试**（注入装置只作用于主求解调用）。
* **Lua 非交互前端**：错误码 20 表现为进程退出，pcall 不能捕获（既有设计）。交互模式未测。
* **线程路径**（`main_lua.c` 约 310 行，`S4_Simulation_SolveLayer` 返回值被忽略）未修改，超出本轮。
* **A-10r 契约探针**（rwork 短于 2n）：ASan 报告 `ztrevc_` 的堆溢出，ord 身份段错误。按 PLAN 不判定，但它表明在该契约违反下仍有不安全行为。
* **ASan 盲区**：不检出未初始化读取（baseline 的 info 问题）；未使用 MSan 或 pattern 初始化。
* **n>75（P03 的 N2）**：仅 A-38（n=76）单点通过，未做全面扫描。
* **D002 历史 provenance 未知**，未补证。

## 6. 发布收尾时的关闭判断（建议，待独立审核后决定）

依据 `PROJECT_ROADMAP.md` 的关闭范围，三项判断如下，执行者不执行关闭：

* **#1 D001**：若审核人接受第 4 节的 D001 结果与第 5 节的边界，则 D001 限定范围（f∈{0.173,0.427,0.733}，θ∈{0°,30°}，s/p，N∈{1,9,25}，A/B/C，内存模式）已满足，可考虑关闭 #1。
* **#2 D002**：本轮覆盖了非恒等置换、左右分支、小 n、空/单元素区间、ld padding、工作区变体、scale[] 与 scalea、仅值状态与错误码 20 的上行传播。HAVE_LAPACK、query 失败注入、线程路径未覆盖。审核人需判断这些是否属于 #2 的必需范围；若不属于，可关闭 #2；否则 #2 保持开放。
* **P04（milestone 1）**：只有 #1 与 #2 都满足并经阶段验收后才可关闭。D001 满足而 D002 未满足时，只关 #1，P04 不关。

## 7. 其它说明

* 提交信息未包含模型标识行（系统对提交与模型标识的规则优先）。如需 `Co-Authored-By` 行，请由操作者在发布前自行添加。
* 主检出的 `.gitignore` 新增 `/.local-archive/`，该改动未提交。
