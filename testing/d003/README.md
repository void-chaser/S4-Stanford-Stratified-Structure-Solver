# testing/d003 — D003 fault-injection harness (P05-S2 装置)

> **状态：未完成，等待用户审核。** 本目录是 P05-S2 的测试装置。它不宣布 P05-S1、S2、S3、S4 任一阶段完成。本目录产生的结果称"装置观察"，不称"验证"。

## 1. 目录结构

| 路径 | 作用 |
|---|---|
| `run_all.sh` | **统一入口**（P05-S2R6）。一条命令从零运行全部阶段：export、build、seam、drivers、matrix、judge、report。 |
| `safe_run.sh` | **安全包装**（P05-S2R6）。所有写入命令经它运行；输出目录若解析到仓库外则在运行任何子命令前拒绝（exit 2）。 |
| `summarize_r6.py` | judge 与 report 的实现（P05-S2R6）。只读输入、只写 `OUT/report/`；对每一行给出派生状态。 |
| `judge_d003.py` | 判定器（历史，**不修改**）。只依赖事实（rc、rc1、rc2、信号、命中数），不读驱动的 PASS/FAIL 退出码。 |
| `matrix_d003.py` | 历史 38 案矩阵运行器（`run`、`classify`、`sensitivity`、`inj-sensitivity`，**不修改**）。 |
| `matrix_r2.py` | 登记运行器（S2R 起，**不修改**）。按登记文件的 10 字段行运行，按树过滤，校验驱动 sha256。 |
| `run_d003.sh` | 早期入口（S2 原始，**不修改**）。导出**一个**提交（默认 `5b72793`，Master，可由第二参数指定），构建其库与驱动，运行一次矩阵。它不构建 B、A、H 三棵树，也不替代 `run_all.sh`。 |
| `src/driver_d003.cpp` | 驱动（模式 `fft`、`kottke`、`jones`、`nv`、`vl`、`experimental`、`closed1d`、`closed2d`、`tensor`、`fftjones`、`fftnv`、`fftvl`）。 |
| `src/inject_d003.cpp` | 注入器（请求前缀分派，见第 3 节）。 |
| `src/history/` | 历史驱动（S1B 参照）。 |
| `seam/apply_seam_r2.py` | 族 A、B、C、D 的 seam 写入器（导出副本）。 |
| `seam/apply_seam_b2.py` | 族 B2（H 树，7 站点）的 seam 写入器。 |
| `seam/apply_seam_r4_buf.py` | 族 B2buf（H 树，仅输出）的 seam 写入器。 |
| `seam/apply_seam_r5_fmmret.py` | 族 E 的 seam 写入器（`--tree A|H` 为 fmmret，`--tree B` 为 fmmbuf，`--tree BPERT` 为 fmmpert）。 |
| `seam/apply_seam_r5_addfield.py` | 族 F（H 树，AddFieldToCache 调用方检查）的 seam 写入器。 |
| `seam/apply_seam.py`、`seam/linearsolve_seam.patch` | S2.6 原始 seam（历史，保留）。 |
| `stage4/` | 选项扫描脚本（Jones），只读输出，不属于统一入口。 |

所有 `apply_seam_*.py` 只编辑通过 `--root` 给定的导出副本，并拒绝位于 `<repo>/S4/` 之下的根目录。`S4/` 本身不被修改。

## 2. 三棵树

| 树标签（任务书） | 运行器标签 | 提交 | 说明 |
|---|---|---|---|
| B | `BASE` | `37a82e8` | 历史基线。无 `fmm_ret` 检查（族 E 用 fmmbuf/fmmpert）。 |
| A | `CUR` | `876181c` | 历史"当前"树。`S4/` 与 `aa1c51d` 逐字节相同。 |
| H | `H` | `64eb0b5` | 参照树。H 的 `testing/` 取自 HEAD，`S4/` 取自 `64eb0b5`。 |

导出方式：`git archive <commit>` 到 `OUT/trees/<B|A|H>`。`Cgeom` 是 gitlink（模式 160000），`git archive` 不展开，三棵树相同，不是缺陷。

## 3. 请求前缀与宏对照表

每一行登记的 `request` 字段决定注入器的分派。下表列出前缀、所需宏、所需库构建。

| 请求前缀 | 族 | 宏（编译期） | 钩子 | 库构建（`run_all.sh` 名） | 适用树 |
|---|---|---|---|---|---|
| `alloc:ID:K` | C | `S4_TEST_ALLOC_SEAM` | `S4_TEST_ALLOC_HOOK` | `seamAB-*` / `seamH` | B、A、H |
| `s4malloc` | — | 无（链接期 `--wrap=_Z9S4_mallocm`） | 链接器 | 任何（驱动 LIBFLAGS） | B、A、H |
| `kottke_alloc:31:K` | D | `S4_TEST_KOTTKE_SEAM` | `S4_TEST_KOTTKE_HOOK` | `seamAB-*` / `seamH` | B、A、H |
| `linearsolve:SITE:K:MODE` | A | `S4_TEST_LINEARSOLVE_SEAM` | `S4_TEST_LINEARSOLVE_AFTER` | `seamAB-*` | B、A |
| `linearsolve_null:ID:K` | B | `S4_TEST_LINEARSOLVE_SEAM_NULLINFO` | `S4_TEST_LINEARSOLVE_NULLINFO_AFTER` | `seamAB-*` | B、A |
| `linearsolve_null2:ID:K` | B2 | `S4_TEST_LINEARSOLVE_SEAM_NULLINFO2` | `S4_TEST_LINEARSOLVE_NULLINFO2_AFTER` | `seamH` | H |
| `linearsolve_null2buf:ID:K` | B2buf | `S4_TEST_LINEARSOLVE_SEAM_NULLINFO2BUF` | `S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER` | `b2buf-H` | H |
| `fmmret:ID:K` | E（状态） | `S4_TEST_FMMRET_SEAM` | `S4_TEST_FMMRET_AFTER` | `fmmret-A`、`fmmret-H` | A、H |
| `fmmbuf:ID:K` | E（仅观察） | `S4_TEST_FMMBUF_SEAM` | `S4_TEST_FMMBUF_AFTER` | `fmmbuf-B` | B |
| `fmmpert:ID:K` | E（恒等扰动） | `S4_TEST_FMMPERT_SEAM` | `S4_TEST_FMMPERT_AFTER` | `fmmpert-B` | B |
| `addf:ID:K` | F | `S4_TEST_ADDFIELD_SEAM` | `S4_TEST_ADDFIELD_AFTER` | `addf-H` | H |

**族的互斥**：每个族有独立宏与独立钩子。同一库不混合族（例如 `fmmret` 库不含 B2 宏）。这正是各族使用不同库构建的原因。

## 4. 统一入口 `run_all.sh`

```
sh testing/d003/run_all.sh --out p05-s2r6/<目录名> [--trees B,A,H] [--stage LIST]
```

- `--out`：`checkpoints/p05/evidence/` 下的相对子目录。绝对路径、含 `..` 或解析到仓库外的路径被 `safe_run.sh` 拒绝（exit 2），且在任何子命令运行前拒绝。
- `--trees`：默认 `B,A,H`。
- `--stage`：默认全部，规范顺序 `export build seam drivers matrix judge report`。

阶段语义：

| 阶段 | 作用 | 输出 |
|---|---|---|
| `export` | `git archive` 三棵树；H 用 HEAD 的 `testing/` 覆盖 | `trees/<B\|A\|H>/` |
| `build` | 普通库（仓库默认选项），记录 CPU 与编译器 | `build-plain-*.log`、`libS4-plain-*.sha256`、`BUILD_OPTIONS.txt` |
| `seam` | 族库：每个族从该提交的**新导出**构建，应用对应 seam 脚本（先 `--check-only` 后写入） | `seam/<树>-<族>/`、`libS4-<族>-*.sha256` |
| `drivers` | 每个库链接一个驱动（LIBFLAGS 与 `run_d003.sh` 相同），记录 sha256 | `drivers/DRIVERS.tsv` |
| `matrix` | 每个（登记, 树, 族）生成**族过滤副本**，两遍运行 `matrix_r2.py` | `matrix/inputs/INPUTS.tsv`、`matrix/RUNS.tsv`、`matrix/runs/` |
| `judge` | `summarize_r6.py`：派生状态，UNDECLARED 使阶段失败 | `report/summary.tsv`、`report/SUMMARY.txt` |
| `report` | 输出文件的 sha256 清单 | `report/SHA256SUMS.txt` |

**幂等**：`OUT/STAGES.txt` 中同一阶段、同一树列表的 `DONE` 行使阶段被跳过；`FAILED` 行不算完成，重跑会再次执行，且两行都保留。

**失败**：任一阶段失败即停止，退出码 1，原因写入 stderr 与 `STAGES.txt`。UNDECLARED 行使 `judge` 失败（exit 3 来自 `summarize_r6.py`，`run_all.sh` 转为阶段失败）。

**族过滤副本**：`matrix_r2.py` 只按树过滤，不按族过滤。同一树的一个登记可能混合需要不同库的族（例如 H 上的 `linearsolve_null2` 与 `linearsolve_null2buf`），因此 `matrix` 阶段先写出按（树, 族）过滤的副本。冻结登记不被修改；每个副本记录其源 sha256 与副本 sha256（`INPUTS.tsv`）。

## 5. 如何解读结果

**B 列不是修复证据。** B（`37a82e8`）是未修复的基线。B 上的观察只说明该基线在相应注入下的行为，不能作为修复已生效的证据。

**"MATCHED" 的含义。** `MATCHED` 表示观察类别等于登记的期望（或等于冻结的历史结果）。它是对登记的一致性检查，**不是修复验证**。

**STRUCTURAL_DECLARED。** 历史 38 案与 R2-D 的 CUR/H 索引中有 18 个 `NO` 行，三份冻结记录的 `NO` 集合完全相同。这 18 行是 S2 修复的预期结构性差异（期望仍为修复前的 CRASH 或 SILENT_SWALLOW，观察为 REPORTED_FAILURE）。`summarize_r6.py` 通过集合相等判定该状态，不依赖标签。

**UNDECLARED。** 任何不属于上述三类的差异。它使 `judge` 失败，必须解释后才能继续。

**驱动二进制不可复现。** 历史驱动二进制无法仅凭记录逐字节复现：冻结的 S2R3 与 S2R5 普通 B 驱动互不相同，且没有记录链接命令。因此复现比较在**结果层**进行（类别、rc、命中数），而非驱动哈希。库（`libS4.a`）则可逐字节复现。

**历史 38 案的运行不可复现。** 历史 38 案运行只记录了 `raw_rc.json`（每例 rc 与日志哈希），未记录驱动路径或 sha256。因此 38 案的复现是**分类重放**（对冻结原始运行重新分类，结果与冻结索引逐字节相同），而非用固定驱动的新运行。

## 6. 已知限制（L1–L10 最新状态）

| 编号 | 限制 | 状态 |
|---|---|---|
| L1 | 公开 API 路径上的缓存命中仅经内部接口覆盖 | 已接受为已知限制（U-1） |
| L2 | B 上 PolBasis vfield 的类别按模式分裂 | 已接受为已知限制（U-2，[未验证]） |
| L3 | H 上无 family-B 点（求解改为 `&solve_info`） | 已接受为已知限制（D-U1，结构性） |
| L4 | AddFieldToCache 的调用方检查：H 上经族 F 隔离；A、B 为 void，无等价点 | 已闭合（H）；A、B 无等价点 |
| L5 | `FMMGetEpsilon` 返回接收点：A、H 为状态强制；B 为恒等模型（非 FMM 源码定义的失败值） | 已闭合（范围内）；B 列为所选模型，**不是修复证据** |
| L6 | 失败模型仅在 H 测得（结构性） | 已接受为已知限制 |
| L7 | 驱动 RESULT 文字不一致；判定只用事实 | 已接受为已知限制 |
| L8 | strace 与 `/tmp` 审计为抽样 | 已接受为已知限制 |
| L9 | 同名不同版本驱动：由 `--driver-sha256` 固定机制缓解 | 已接受为已知限制（用户决定） |
| L10 | 驱动只覆盖 NB=9、固定几何、θ=0 | 已接受为已知限制（用户决定） |

另：历史驱动二进制不可复现（第 5 节）；历史 38 案的运行不可复现（第 5 节）；S2R2 的 17 案源登记（`REGISTRY_T2_v2`、`REGISTRY_T4`、`REGISTRY_T4_NVVL` 等）只位于 `checkpoints/p05/evidence/p05-s2r2/`，未纳入 `registries/` 复现包（MANIFEST 将其列为范围外）。

## 7. 复现命令

从零复现（在仓库内新目录）：

```
sh testing/d003/run_all.sh --out p05-s2r6/repro-<编号>
```

只检查某阶段：

```
sh testing/d003/run_all.sh --out p05-s2r6/<目录> --trees A,H --stage judge,report
```

安全包装的用法（任何写入命令均应经它）：

```
sh testing/d003/safe_run.sh p05-s2r6/<目录> -- <命令> [参数]
```

判定器自检（只读）：

```
python3 -I -B testing/d003/judge_d003.py selftest
```

所有输出位于 `checkpoints/p05/evidence/`，该目录被 `.git/info/exclude` 忽略，不提交。
