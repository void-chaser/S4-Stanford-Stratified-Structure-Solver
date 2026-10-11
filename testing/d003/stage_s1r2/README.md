# testing/d003/stage_s1r2 — P05-S1R2 J1–J6 探针与分析脚本

> **状态：未完成，等待用户审核。** 本目录是 P05-S1R2（P05-S1 的补充子任务）的探针与分析脚本。它不宣布 P05-S1、S2、S3、S4 任一阶段完成。本目录产生的结果称"装置观察"或"探针观察"，不称"验证"。

## 1. 文件

| 文件 | 作用 | 对应 |
|---|---|---|
| `classify_j1.py` | J1 矩阵判定（读 gdb 输出；只写标准输出）。v3：有信号的 PolBasis 返回判为 CRASHED | J1 |
| `compare_j1_dump.py` | J1 全矩阵逐位比较（读 `J1_DUMP/` 的二进制转储；只写标准输出） | J1 |
| `kottke_probe.cpp` | J2 探针（仅公共 API；标量或张量图案材料；kottke 模式） | J2 |
| `shape_probe.cpp` | J3 探针（公共 API 构造多形状；内部头文件只读取基址） | J3 |
| `shape_index_stats.py` | J3 统计：把 `shape_get_normal` 的指针换算为下标（只写标准输出） | J3 |
| `j4_hash_table.py` | J4 逐条哈希表（只读证据树；只写标准输出） | J4 |
| `gdb_j1_full.gdb`、`gdb_j1_dump.gdb`、`gdb_j1_clmret.gdb`、`gdb_j1_cache_order.gdb`、`gdb_j1_flow_ret.gdb` | J1 的 gdb 模板（读内存；不修改程序状态） | J1 |
| `gdb_j2_inv8.gdb`、`gdb_j2_inv.gdb`、`gdb_j2_solve.gdb` | J2 的 gdb 模板 | J2 |
| `gdb_j3_normal.gdb` | J3 的 gdb 模板（记录 `shape_get_normal` 的指针） | J3 |
| `gdb_j6_ng1_ret.gdb` | J6 的 gdb 模板（读 `pattern_generate_flow_field` 返回码） | J6 |
| `j1_matrix_run.sh`、`j1_dump_run.sh`、`j1_clm_run.sh` | J1 运行器 | J1 |
| `j2_sweep_run.sh`、`j2_trees_run.sh` | J2 运行器 | J2 |
| `j3_run.sh` | J3 运行器 | J3 |

## 2. 运行前提

- 所有写入只发生在证据目录 `checkpoints/p05/evidence/p05-s1r2/` 之内，并经 `testing/d003/safe_run.sh` 运行。
- 运行器通过 `$EV/tmp/` 读取 gdb 模板，并通过 `$EV/trees/`、`$EV/drivers/` 读取导出的树与驱动。因此运行前必须：
  1. 设 `REPO=$(git rev-parse --show-toplevel)`、`EV="$REPO/checkpoints/p05/evidence/p05-s1r2"`，并 `mkdir -p "$EV/tmp"`、`export TMPDIR="$EV/tmp"`。
  2. 把本目录的 gdb 模板与运行器复制到 `$EV/tmp/`（运行器假定它们在那里）。
  3. 按第 3 节导出三棵树、构建库与驱动。

## 3. 构建与生成步骤（复现顺序）

1. 导出三棵树（`git archive`）：`37a82e8`（B）、`876181c`（A）、`64eb0b5`（H）→ `$EV/trees/{B,A,H}/`。
2. 构建普通库：每棵树 `make objdir` 与 `make ... build/libS4.a`（CPPFLAGS 为 `-IS4 -IS4/RNP -IS4/kiss_fft`）。
3. 编译驱动（当前注入器）：`g++ ... testing/d003/src/driver_d003.cpp testing/d003/src/inject_d003.cpp ... -L "$EV/trees/<t>/build" -lS4 $LIBFLAGS`，输出 `$EV/drivers/driver-d003-<t>`。
   `LIBFLAGS` 与 `run_all.sh` 相同（含 `--wrap`）。
4. 编译 J2 探针：`kottke_probe.cpp` 与树的 `S4` 头文件，链接 `-lS4 -llapack -lblas`（**不带** `--wrap`；探针不依赖注入器）。输出 `$EV/drivers/j2-kottke-probe-<t>`。
5. 编译 J3 探针：`shape_probe.cpp`，包含 `S4`、`S4/fmm`、`S4/pattern` 的头文件；输出 `$EV/drivers/j3-shape-probe-<t>`。
6. 按模板生成每树的 `gdb_j1_clmret_<t>.gdb`：把模板中的 `+ 1087)` 替换为该树反汇编中 `ret` 的偏移（B 为 1057、A 为 1058、H 为 1087；**偏移必须由 `disassemble Simulation_ComputeLayerModes` 取得，不得手填**）。
7. 运行：`sh j1_matrix_run.sh "$EV"`、`sh j1_dump_run.sh "$EV"`（先按 `gdb_j1_dump.gdb` 的占位 `OUTDIR` 替换规则生成每格副本）、`sh j1_clm_run.sh "$EV"`；J2：`sh j2_sweep_run.sh "$EV"`、`sh j2_trees_run.sh "$EV"`；J3：`sh j3_run.sh "$EV"`。
8. 统计：`python3 -I -B testing/d003/stage_s1r2/classify_j1.py "$EV/J1"`；`compare_j1_dump.py "$EV/J1_DUMP"`；`shape_index_stats.py "$EV/J3_RUNS"`；J4：`j4_hash_table.py "$REPO/checkpoints/p05/evidence"`（该目录须含 `EVIDENCE.sha256`）。

## 4. 已知的复现缺口（如实记录）

- **运行器中的模板路径是硬编码的**（`$EV/tmp/...`）。必须按第 2 节的第 2 步复制模板，否则运行器找不到它们。
- **`j1_dump_run.sh` 依赖占位替换**：模板中的 `OUTDIR` 需在每格生成副本时替换为该格的目录。运行器已内置该替换，但其输入模板必须是本目录的 `gdb_j1_dump.gdb`。
- **`gdb_j1_clmret.gdb` 的 `+ 1087` 是 H 的偏移**。`j1_clm_run.sh` 实际使用的是每树生成的副本（第 3 节第 6 步）。
- **gdb 的 `finish` 在 SIGSEGV 后打印的 `PB_RETURN` 不是正常返回**（见 `J1_RESULT.txt` 第五节）。分类器 v3 以信号判定 CRASHED。
- **gdb 栈参数读取不可靠**：`pattern_generate_flow_field` 的第 8 个参数（`field`）未能用 `rsp+16` 读取（见 `J6_NG1/README.txt`）。本目录的脚本不依赖该读取。
- 历史 `/tmp` 与仓库外写入：本目录的脚本不写仓库外路径。运行器的输出只进入证据目录。

## 5. 不修改的对象

- 不修改 `S4/`；不修改 `testing/d003/judge_d003.py`；不修改既有驱动与注入器。
- 不修改已提交的报告原文，不修改 `testing/s4test/ISSUE_REGISTRY.md` 与 `PROJECT_ROADMAP.md`。
