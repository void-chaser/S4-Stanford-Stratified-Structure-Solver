# P04 第一阶段执行报告：D001 / D002 最小源码修复、定向验证与本地清理

状态口径：**已实现（implemented）**、**定向验证完成（targeted complete）**、**待独立生产验收（pending independent production acceptance）**。
本报告不宣称生产关闭。D001、D002、P04 仍为 OPEN；未推送、未建 PR、未关闭 issue/milestone。

## 1. 绑定版本

| 项 | 值 |
|---|---|
| 基线 | `963ccf1`（checkpoint/014rf-offline-evidence-accepted-20261003） |
| 源码修复提交 | `44f4a09` fix: D001 zgebak permutation index and D002 RNP status/workspace propagation |
| 终验版本（最终 tip） | `8b13d67` test: P04 pipeline run() no longer clobbers the caller's loop variable（仅改流水线脚本标签；产品代码与 `44f4a09` 相同） |
| 分支 | `codex/p04-d001-d002-production-20261009T082631Z`（本地，未推送） |
| 工作位置 | `/srv/nvme/projects/S4-p04-product-d001-d002`（git worktree） |
| 产品代码差异 | `S4/` 与 `.gitignore`：8 个文件，140 行新增，36 行删除（见 `evidence/PRODUCT_DIFF_963ccf1..8b13d67.patch`） |

终验绑定到 `8b13d67`：在 `git clone` 得到的全新 checkout 中从头运行 `sh testing/p04_run_all.sh`，结果见第 4 节，原始摘要在 `evidence/`，完整运行目录在 `/srv/nvme/projects/S4-p04-runs-20261009T082631Z/verify-final/`（不在 Git 中）。

## 2. 源码改动与来源映射

改动来自 `codex-review/P04-CLAUDE-RECOVERY-DIAGNOSTIC-CLOSEOUT-20261009T071842Z-d5f1a3/package/engineering/PRODUCTION_ENGINEERING.patch`（SHA256 `1adef26c…`，已核对）中的选定 hunk，并非整包应用。选取依据是实际 diff，不是旧 hunk 行号。补丁文件的正文行为 LF，而仓库文件为 CRLF，应用时已按目标文件转换。Eigensystems.cpp 全部 8 个 hunk 的应用结果 SHA 与清单 `after_sha256 71817d22…` 完全一致。

| 文件 | 改动 | 缺陷归属 |
|---|---|---|
| `S4/RNP/Eigensystems.cpp` zgebak_ | 左、右两支的后向置换：下标由 1-based 修正为 0-based（4 行） | D001 |
| `S4/RNP/Eigensystems.cpp` zlaqr3_/zlaqr0_ | wantz 为假时不再对 NULL z 做指针偏移（UB），并把 `_z__` 传给 zlaqr3_ | D002（相邻 NULL z） |
| `S4/RNP/Eigensystems.cpp` RNP::Eigensystem | 仅值分支 `zhseqr_` 的返回值被接收到 `info` | D002（仅值状态） |
| `S4/rcwa.cpp` SolveLayerEigensystem(_real) | 工作区归属在 lwork 被查询哨兵覆盖之前判定（`owns_work`）；返回 RNP info；失败时跳过后处理与 MakeKPMatrix；循环以 `info==0` 为条件 | D002（工作区所有权、失败不安装） |
| `S4/rcwa.h` | SolveLayerEigensystem 返回类型 `int`，注释说明 | D002 |
| `S4/S4.cpp` | ComputeLayerModes：特征求解失败与查询失败时丢弃新建的 LayerModes（`Simulation_DiscardLayerModes`）并返回 20；ComputeLayerSolution / GetPropagationConstants / GetSMatrix 向上传播 | D002（错误码 20 上行） |
| `S4/main_python.c` | 错误码表登记 20（19 为占位） | D002 |
| `S4/main_lua.c` | 错误码表登记 20；`GetAmplitudes` 检查 `Simulation_GetAmplitudes` 的返回值 | D002 |
| `S4/S4_internal.h` | 错误码注释补充 20 | 文档 |
| `.gitignore` | 忽略 `/build-seam/` | 工程卫生 |

未纳入（按要求排除）：GetWaves 重写及其 11 字段文档、`geom_*` 辅助函数删除、cubature 改动、死代码 `ConvertUnits` 删除、`SolveInParallel` 清理、`S4.h` 与 `ext_lua.c` 的 GetWaves 部分、102 项补丁中的其它全部内容。普通构建中这些清理未被阻塞，因此未引入。

测试注入装置（不进入普通构建）：
* `S4_TEST_EIGEN_INFO` 的 S4 传播 seam：头文件已从源码树移到 `testing/s4test/test_seams/seam.h`，只由测试构建的 `-I` 引用；`rcwa.cpp` 中的 `#ifdef` 保留。
* `-DD002_TEST_SEAM` 的 RNP 状态 seam：只在驱动的派生源码副本中把单个定义改名（`zhseqr_` → `d002_inner_zhseqr_`），三处调用保持不变，由驱动里的包装器接收。
* 普通构建验证：`strings` 检查，普通库与扩展中两个宏的字符串均为 0 次出现；seam 构建中各出现 2 次。

## 3. 构建环境

gcc/g++ 15.2.0（Ubuntu 15.2.0-16ubuntu1）、GNU make、Python 3.14.4、lua5.2 头文件与解释器、liblapack/libblas（链接用）。编译参数沿用 `Makefile.Linux`（`-O3 -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC`）。Python 扩展由 `setup.py build_ext --inplace` 生成。`HAVE_LAPACK` 未启用（见第 6 节）。

清理前的构建产物是旧的：仓库根目录的 `S4.cpython-314-x86_64-linux-gnu.so`（742,368 字节）与 `build/`，已移入归档（见 CLEANUP.md）。终验在不含它们的全新克隆中完成。

## 4. 终验结果（提交 8b13d67，全新克隆，`sh testing/p04_run_all.sh`）

`STEPS.txt` 每一步的返回码已记录；所有 candidate 步骤返回 0，baseline 的 D001 与 D002 判定返回 1，这是缺陷对照的预期结果，不是流水线失败。

| 检查 | 候选（candidate） | 基线（baseline，963ccf1） | 判定规则 |
|---|---|---|---|
| D001 冻结 12 例（f=0.427，N=1/9，s，A/B/C，r1/r2，独立进程） | **12/12**，最大 \|ΔR\|,\|ΔT\| 1.1e-16 | 8/12；失败为 N=9 的 B、C（R=0.9488、T=0.0512；参考 R=0.3479、T=0.6521） | 绝对 1e-10，独立 Airy 参考 |
| D001 扩展 113 例（f∈{0.173,0.427,0.733}，θ∈{0°,30°}，s/p，N∈{1,9,25}，A/B/C；内存模式 5 例） | **113/113**，最大误差 4.4e-16 | 60/113；失败全部为 B/C 且 N>1（含内存模式） | 绝对 1e-10，Fresnel 几何级数参考（θ=0 与 Airy 一致，1e-14 自检） |
| D002 ord（生产参数）59 冻结例 | **53/53 判定**（5 个 seam 例不适用，1 个契约探针仅记录） | 31/53 | 冻结 PLAN 阈值：eig 1e-10、残差 1e-10、向量范数 1e-12、query work[0]=2n |
| D002 asan（ASan+UBSan，-O1 -g） | **53/53** | 27/53（两次运行为 25 与 27，见第 6 节） | 同上，并且 stderr 出现 sanitizer 报告即失败 |
| D002 seam（asan + `-DD002_TEST_SEAM`，含 C-01~C-06） | **58/58** | 27/58 | 注入的强制状态须被接收；真实 last info=0 |
| 阳性对照（pos_asan / pos_ubsan / pos_asan_ubsan） | 3/3 通过，各自报告注册签名 | — | 检测器确实报告 |
| S4 错误码 20 传播（Python 进程内；Lua、C 各为独立进程） | **33/33** | — | 见第 5 节 |
| s4test 套件（unittest discover） | **257 项 OK，skipped=1** | 257 项 OK，skipped=1（结果逐项一致） | 既有套件，未改 |
| Lua 回归 `testing/runtests.sh` | PASSED | — | 既有 |
| `testing/test_python_binding.py` | 4/4 OK | — | 既有 |

D002 中 candidate 的最大判定误差（ord 身份）：特征值 6.1e-15（阈值 1e-10）、右向量残差 6.1e-15、左向量残差 6.0e-15、向量范数误差 5.6e-16。

## 5. 覆盖表（对应 GitHub #1 D001、#2 D002 的必需条件）

### D001（#1）

| 必需条件 | 证据 | 状态 |
|---|---|---|
| f=0.427、N=1/9、s、A/B/C，独立进程重复，真实 G 与通量 | 冻结 12 例；每例一个子进程；原始记录含实际 G 与四个复数通量 | 已验证（终验） |
| 同 flags 新 baseline/candidate 复现 baseline N9 B/C 大偏差，candidate 修正，控制不退化 | baseline N9 B/C 偏差；candidate 全部通过；A 与 N=1 在两侧均通过 | 已验证（终验） |
| f=0.173 / 0.733，s/p，明确非截止斜入射（30°），较大 basis（N=25），实际内存模式（ConserveMemory） | 扩展矩阵 113 例 | 有限集成覆盖，已验证 |
| 独立参考只从输入计算，不用 S4 输出 | `oracle_d001.py`（Airy/TMM/Fresnel，自检）与 `oracle_d001_ext.py`（斜入射 Fresnel；θ=0 与 Airy 的差 2.2e-16） | 已实现 |
| 同材质 region 视为均匀物理模型（B 与 A 同参考） | B 的结果与 A 的参考一致 | 已验证 |
| 没有放宽阈值 | 1e-10 在运行前固定，未调整 | 符合 |

边界：扩展矩阵中的斜入射只覆盖 θ=30°、两种偏振，不覆盖其它角度与任意材料；内存模式只覆盖 ConserveMemory=True 的 5 例。

### D002（#2）

| 必需条件 | 证据 | 状态 |
|---|---|---|
| 非恒等上下置换（真实左右分支，小 n，ilo>1 或 ihi<n） | HELPER_GEBAK H-01～H-11（置换含 ilo>1、ihi<n，非恒等）；API 中 A-15～A-24、A-32/33、A-39～A-41 | candidate 通过；baseline 失败 |
| 左右分支：vl（6）、vr（15）、both（13）、none（8） | PLAN 计数 | 已验证 |
| 小 n 与空/单元素活动区间 | n∈{0,1,2,3,4,6,40,76}；n=0（A-01）；ilo=ihi（A-02、A-03） | 已验证 |
| 实际 ld/stride/padding（ldv > n） | ldvl∈{1,2,3,5}，ldvr∈{1,2,3,4,5,6,40,76}，含 padding | 已验证 |
| caller/internal workspace；query、short、null_lwork；rwork exact/internal/null | work：exact 18、internal 21、query 1、null_lwork 1、short 1；rwork：exact 19、internal 21、null 2 | 已验证（rwork short 仅在契约探针 A-10r 中，见第 6 节） |
| NULL optional outputs | want=none（8 例） | 已验证 |
| 非单位 backtransform scale[]（真实平衡缩放因子） | A-25、A-26、A-27、H-09、H-10 中出现非整数的缩放值 | 已验证 |
| 极端 scalea（与 scale[] 分开统计） | scalea=1：A-28～A-31、A-36、A-37 | 已验证 |
| n>75（P03 记录的既有问题 N2） | A-38（n=76）在 candidate 上通过；未做 n>75 的全面扫描 | 单点通过，范围外 |
| 仅值分支状态被接收、并由上层可达 | seam：C-01～C-06；baseline 在 C-01～C-04 中读到未初始化的 info（18582、16 等） | 已验证 |
| 失败不安装 modes/缓存；恢复重试 | S4 层：失败后在同一对象上清除注入，结果与参考一致（间接证明未安装坏缓存） | 间接验证，未直接检查内部指针 |
| 错误码 20 沿 rcwa→S4→Python/Lua/C | error20 33/33 | 已验证（见第 6 节 Lua 行为） |
| ASan/UBSan 阳性对照与容量布局 | 3 个阳性对照通过；驱动以精确容量分配（`new[]`），越界可被 ASan 检出 | 已验证；盲区见第 6 节 |
| 普通构建不含注入宏 | `strings` 检查（0 次） | 已验证 |
| HAVE_LAPACK 分支 | `rcwa.cpp -DHAVE_LAPACK -fsyntax-only` 0 错误（baseline 同样 0） | 仅语法检查，未运行 |

## 6. 发现、边界与未解决项

1. **契约探针 A-10r**：rwork 长度小于 2n，属于调用方违反契约。按 PLAN 登记为探针，只记录、不判定。candidate 的 ord 身份段错误（退出 -11），ASan 身份报告 `heap-buffer-overflow` 于 `ztrevc_`（`Eigensystems.cpp` 约 2936 行）。这不是 P04 的修复范围，也没有升级为普通失败。
2. **baseline 的 asan 结果有波动**（25/53 与 27/53）：baseline 读取未初始化的 `int info`，结果依赖栈内容。candidate 在多次运行中稳定（53/53）。
3. **sanitizer 盲区**：ASan 不检出未初始化读取（这正是 baseline 的 info 问题）；本轮未使用 MSan 或 `-ftrivial-auto-var-init=pattern`（P03 曾用后者，只用于使该读取确定化）。LeakSanitizer 随 ASan 构建启用，驱动退出时未报告泄漏。
4. **Lua 前端的错误行为**：非交互模式下 `S4L_error` 打印后直接 `exit(EXIT_FAILURE)`，`pcall` 捕获不到。测试据此检查了非零退出、stderr 中的公共消息以及没有任何结果行输出（这是既有设计，未改动）。交互模式未测试。
5. **线程路径**：`main_lua.c` 中工作线程内调用 `S4_Simulation_SolveLayer` 时忽略返回值（约 310 行）。它属于 SolveInParallel/线程路径，超出本轮范围，未修改，待单独登记。
6. **query 调用**：`S4.cpp` 中工作区查询调用现在检查返回值（非零则返回 20）。注入装置只作用于主求解调用，因此 query 失败路径没有注入测试覆盖；D002 的 A-08 只验证 query 的 work[0]=2n。
7. **HAVE_LAPACK 分支**：默认构建不编译 `SolveLayerEigensystem_real`，本轮只做了语法检查，没有 LAPACK 配置下的原生运行，因此该分支不宣称已认证。依赖：liblapack 与 `RNP::Eigensystem_real`。
8. **D002 历史 provenance 未知**，本轮未补证。
9. **生产未采纳**：102 项补丁仍未采纳，本分支只含上述最小集合。`DEFECTS.md` 的用户修改未触碰。
10. **legacy 编号**：未改动 `DEFECTS.md` 的编号与内容；`testing/s4test/ISSUE_REGISTRY.md` 的 D001/D002 行已按上述口径更新（该文件在主仓库中是未跟踪文件）。

## 7. 复现

```sh
git clone -b codex/p04-d001-d002-production-20261009T082631Z <repo> /tmp/x   # 或使用本 worktree
sh testing/p04_run_all.sh /path/to/new-run-dir
cat /path/to/new-run-dir/STEPS.txt
```
细节见 `testing/README-P04.md`。单项入口：`testing/d001/run_d001_matrix.py`、`testing/d001/run_d001_extension.py`、`testing/d002/run_d002.py {build,run,judge,positives}`、`testing/s4test/error20/run_error20.py`。

## 8. 与发布收尾的关系

本报告不关闭任何 issue。关闭判断依据见 `INDEPENDENT_REVIEW_HANDOFF.md` 与 README 的口径说明。未经独立审核的执行者自检不计为独立验收。
