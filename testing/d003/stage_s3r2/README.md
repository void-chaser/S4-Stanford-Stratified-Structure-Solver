# testing/d003/stage_s3r2 — P05-S3R2 装置与探针

> **状态：未完成，等待用户审核。** 本目录是 P05-S3R2（P05-S3 的补充子任务，不是新阶段）的装置与探针。它不宣布 P05-S1、S2、S3、S4 任一阶段完成。本目录产生的结果称"开发检查"或"探针观察"，不称"验证"。

## 1. 文件

| 文件 | 作用 | 对应 |
|---|---|---|
| `d138_probe.cpp` | D-138 探针：双形状（overlap、bigoverlap、concentric 三种布局），公共 API，模式 `fft`，把场写到 `D138_OUT` | R2-1 |
| `field_compare.py` | 场逐行文本比较（只读输入，只写标准输出） | R2-1 |
| `gdb_d138_normal.gdb` | 记录 `shape_get_normal` 的调用次数与指针 | R2-1 |
| `gdb_d138_fft_dump.gdb` | 在 `FMMGetEpsilon_FFT` 入口保存指针、返回处转储 Epsilon2 与 Epsilon_inv。模板含占位 `RET_OFF` 与 `OUTDIR`，须按反汇编结果替换 | R2-1 |
| `gdb_d138_nvec.gdb` | 记录每次 `shape_get_normal` 的输入点、指针与返回法向。模板含五个占位 `RET_OFF_1..5`，须按反汇编替换 | R2-1 |
| `nvec_compare.py` | 逐次比较两棵树的法向与指针（只读输入，只写标准输出） | R2-1 |
| `kottke_probe_dump.cpp` | R2-4c 探针：kottke、标量材料、公共 API；在 `KPD_OUT` 指定时转储第一次调用的完整场（S1R2 的 `kottke_probe.cpp` 未修改） | R2-4c |
| `gdb_d016_ret.gdb` | R2-4b：记录 `pattern_generate_flow_field` 每次返回的 `eax`，并计数 `SolveLayerEigensystem` 调用。模板含占位 `RET_OFF`，须按反汇编替换（新树为 422） | R2-4b |
| `r4a_run.sh` | R2-4a 矩阵运行器：非 Jones 9 个模式（fft、kottke、nv、vl、fftnv、fftvl、closed2d、experimental、tensor）与 Jones 2 个模式（jones、fftjones），共 11 个；2 栈 × 3 偏振 × NB∈{5,9}；三树；运行前核对驱动 pin | R2-4a |
| `r4a_compare.sh` | R2-4a 逐用例字节比较（new 对 start，start 对 base）与 rc 汇总（只读输入） | R2-4a |
| `rel_diff.py` | 两个场转储的逐值相对差（最大、中位、非有限计数；只写标准输出） | R2-4a（Jones 数值） |

R2-2b 的 seam 装置**不可测**，本目录没有 seam 补丁。判定理由见 `$EV/R2-2b_SEAM_RECORD.txt`（证据目录，不提交）。

## 2. R2-1 的复现步骤

前提：`REPO=$(git rev-parse --show-toplevel)`；`EV=$REPO/checkpoints/p05/evidence/p05-s3r2`；`mkdir -p "$EV/tmp"`；`export TMPDIR="$EV/tmp"`；所有写入经 `testing/d003/safe_run.sh p05-s3r2 -- ...`。

1. 导出 HEAD 到 `$EV/d138/src-orig`（`git archive HEAD | tar -x`）；复制为 `$EV/d138/src-alt`。
2. 在 `src-alt` 的 `S4/fmm/fmm_FFT.cpp` 第 138 行，把 `shapes[imat[0]]` 替换为 `shapes[(imat[0] >= 1 ? imat[0]-1 : imat[0])]`（**受限形式**，避免下标 −1，见 `R2-1_D138_AMENDMENT_1.txt`）。用 `diff` 核对只有该行不同。
3. 两棵树分别构建普通库（`make objdir` 与 `make ... build/libS4.a`，CPPFLAGS 为 `-IS4 -IS4/RNP -IS4/kiss_fft`）。
4. 编译探针：`g++ ... testing/d003/stage_s3r2/d138_probe.cpp ... -lS4 -llapack -lblas`（**不带** `--wrap`）。
5. 运行：`env FMM_MODE=fft D138_LAYOUT=bigoverlap D138_OUT=... ./d138-probe-<t>`。
6. 场比较：`python3 -I -B testing/d003/stage_s3r2/field_compare.py A B label`。
7. 转储：`gdb_d138_fft_dump.gdb` 中 `RET_OFF` 取自 `disassemble FMMGetEpsilon_FFT` 的 `ret` 偏移（orig 为 3795，alt 为 3810，两者不同，须各自取值）；`OUTDIR` 替换为转储目录。两份转储用 `cmp` 比较。
8. nvec：`gdb_d138_nvec.gdb` 中 `RET_OFF_1..5` 取自 `disassemble shape_get_normal` 的五个 `ret`（两棵树相同：305、610、833、839、845）；运行后用 `nvec_compare.py` 比较。

## 3. 注意事项

- 驱动 `testing/d003/src/driver_d003.cpp` 的单形状 pattern 栈在 `nnz >= 2` 时只产生 `imat[0] = 0` 的界面；本目录的探针为双形状，才能覆盖 `imat[0] >= 1`。
- 偏移（`ret`）必须由反汇编取得，不得手填。两棵树的 `FMMGetEpsilon_FFT` 偏移不同。
- 判定只依赖场数据、转储字节与 rc；不读取任何 PASS/FAIL 退出码。
- 期望与修正的时间线与 sha256 见 `$EV/R2-1_RESULT.txt` 与 `$EV/R2-1_D138_*.txt`。

## 4. 不修改的对象

- 不修改 `S4/`（R2-1 的所有源码修改只在导出副本中进行）。
- 不修改 `testing/d003/judge_d003.py`、既有驱动与注入器、`testing/d003/seam/`。
