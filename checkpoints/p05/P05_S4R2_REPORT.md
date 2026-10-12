# P05-S4 R2 报告（子轮次）：更正 R1、四树对照、冻结树 F 上的 FMM 三列运行

**状态：本轮未完成，等待用户审核。P05-S4 未签收。** 本报告是 P05-S4 的子轮次记录，不是新阶段。本报告不宣布 P05-S4 或任何其他阶段完成，也不把装置观察写成"验证通过"或"已修好"。

## 1. 完成项与未完成项

| 项 | 状态 | 证据 |
|---|---|---|
| R2-0 更正 R1 的错误陈述并复核四项事实 | 完成 | `evidence/p05-s4r2/ERRATA_2.txt` 第 1 节 |
| R2-0 basis 不符的 R1 行 | 完成 | ERRATA_2 第 3 节 |
| R2-1 树名对照 TREES.tsv（B、A、H、F） | 完成（历史树名映射仅 B/A/H/F 本身；S1–S3 报告的全部树名映射**未全面核对**，见第 8 节） | `evidence/p05-s4r2/TREES.tsv` |
| R2-2 四棵树导出、plain 构建、plain 驱动 | 完成（B、A、H、F 各一棵；seam 族库未构建） | `evidence/p05-s4r2/run2/`，`STAGES.txt` |
| R2-2 F 上 seam（族 A–D）check-only | **失败**：锚点不匹配，见第 5 节 | `run1/seam-check-F-ABCD.txt`（运行失败输出） |
| R2-3 预注册（运行前写入） | 完成（v2，sha256 `add404d7…`；草稿已保留并披露） | `evidence/p05-s4r2/REGISTRY_S4_PRE_R2_v2.tsv` |
| R2-4 三列运行（B、A、F；45 行） | 完成（范围收窄，见第 6 节） | `evidence/p05-s4r2/run3/raw_R2.tsv`，`RESULTS_R2.tsv` |
| R2-4 MISMATCH 与 INVALID 单列 | 完成（11 行，原因见第 5 节） | RESULTS_R2.tsv |
| 红点判定 | 完成（F 列无 CRASH/SILENT_SWALLOW；见第 6 节的限制） | — |
| SI01–SI02、AL18、FE01–FE10、info=NULL 七处、CLM1–4、ACF1、EXP40 | **未完成**，推迟到 R3 | — |
| V3 重试等价、V4 sanitizer、V5 残留项 | **未完成** | — |
| 违规披露 | 完成（第 9 节） | — |

## 2. ERRATA_2 摘要

- **apply_seam_r2.py "去向未查明"（R1）是错误陈述。** 文件在工作区，被 git 跟踪，内容与 HEAD 一致（`git diff --quiet HEAD`），最后提交为 `f5cae24`，被 `run_all.sh` 第 179–200 行调用。R1 的查找方法没有覆盖跟踪文件。
- R1 的四项事实（b00b630/de52142 的来源、A/S/H/F 的树哈希、fft_plan_exec 的计数 10 对 S1 的 12、S4_malloc 的 17 对任务的 16+1 得出的点数 45 对 44）已复核，**与 R1 一致**，其中 45/44 为既定的差异而非错误。
- R1 预注册中两行 basis 需要修正的说明：P01（"F: 见 S3R2 本轮 fft 计划"）的 F 检查来自 b00b630；AL12 的 "S3R2 历史" 指的是 B 上的历史运行，不是 F 的源码。第 74、75 行（D016、RNV1）引用 S3R2 是正确的。
- R2 预注册经历了三个版本（部分草稿、作废草稿、正式 v2），改名与改写过程均在 ERRATA_2 第 4 节披露。

## 3. TREES.tsv 摘要

| 标签 | 运行器标签 | 提交 | S4 树哈希 | b00b630 | de52142 | S3R 提交 | S3R2 提交 |
|---|---|---|---|---|---|---|---|
| B | BASE | 37a82e8 | 1d738e64… | 否 | 否 | 无 | 无 |
| A | CUR | 876181c | 85feec11… | 是 | 是 | 无 | 无 |
| H | H | 64eb0b5 | cb7fc613… | 是 | 是 | e83255f、73e00ef、df3bb02、35cd7b3 | 无 |
| F | F | 1c11905 | 4a6f6492… | 是 | 是 | 同 H | 3e77aa9、44bcf1c、ff6dd7c |

S 起点 35cd7b3 的 S4 树（`cb7fc613…`）与 H 相同。所有单元格来自 git rev-parse、merge-base --is-ancestor。

## 4. 构建摘要

| 树 | libS4.a sha256 | 驱动 sha256 | 备注 |
|---|---|---|---|
| B | `fb9ac3f5fd2c121619bb6cd464816f97a3085c8e4a2795a2b5037b370110ffba` | `f226117594f9dc91…` | 与 S2R 记录的基线库哈希一致（P05_S2R_HARNESS_SUPPLEMENT 第 46 行） |
| A | `865c58938e18220a3e…` | `5dd45f8b5c6381a6…` | 与 S3R 记录的起点库哈希一致（P05_S3R 第 36 行） |
| H | `f053bfea1ef045af…` | `4a16453ed6bca5e4…` | 无历史对照值 |
| F | `be17f4696f557b13…` | `08f48df540e2e29d…` | 无历史对照值；导出的 70 个 S4 文件与 git blob 逐一哈希一致 |

构建选项与 run_all.sh 的 build_lib 相同（`make objdir`，`make … build/libS4.a`，仓库默认选项）。所有构建日志无 error。

## 5. 三列运行结果

### 5.1 结果表（45 行，`RESULTS_R2.tsv`）

汇总：**34 MATCH，11 MISMATCH**。

| 列 | 观察类别分布 |
|---|---|
| B（BASE，未修复基线） | 7 CRASH，4 SILENT_SWALLOW，1 CONTROL_OK，3 INVALID |
| A（CUR） | 11 REPORTED_FAILURE，1 CONTROL_OK，3 INVALID |
| F（冻结树） | 11 REPORTED_FAILURE，1 CONTROL_OK，3 INVALID |

### 5.2 MISMATCH 与 INVALID（逐条）

| 行 | 树 | 期望 | 观察 | 原因（已验证的事实） |
|---|---|---|---|---|
| AL04-B | B | CRASH | SILENT_SWALLOW | NTH4 的实际分配为 **1024 B**（不是预注册写的 work）；rc 1，rc1 0。预注册映射错误（见 5.3） |
| AL10-B | B | CRASH | SILENT_SWALLOW | 同 AL04-B（vl 模式 NTH4 为 1024 B） |
| AL05-B/A/F | B/A/F | CRASH / REPORTED_FAILURE | INVALID（hit 0） | NTH5 在 jones 模式下**未被命中**（HITCOUNT 0），三树一致。预注册映射错误 |
| AL08-B/A/F | B/A/F | 同上 | INVALID（hit 0） | NTH5 在 nv 模式下未命中，三树一致 |
| AL11-B/A/F | B/A/F | 同上 | INVALID（hit 0） | NTH5 在 vl 模式下未命中，三树一致 |

这 11 行都不是 UNDECLARED。它们**不计为红点**：NTH5 未命中在三树上一致，是预注册的映射错误，不是树的行为差异。

### 5.3 预注册映射错误（已披露，未用改期望的方式消除）

R2 预注册 v2 的 NTH 映射取自历史记录（S2R3 第 131–132 行），对 PolBasis 三模式给出同一映射（ivalues/work/vfield = NTH 3/4/5）。运行日志（`run3/runs/*.log`，`S4FMM HIT … FMM call N B`）显示映射**不成立**：

| 模式 | NTH3 | NTH4 | NTH5 |
|---|---|---|---|
| fft（FFT 段，NTH1 6144 B，NTH2 16 B，plan 1864 B，均与预注册一致） | — | — | — |
| jones | 10720 B | 1024 B | 未命中 |
| nv | 11872 B | 1024 B | 未命中 |
| vl | 11872 B | 1024 B | 未命中 |

fft 模式的 NTH1 6144 B、NTH2 16 B、plan 1864 B 与预注册一致。因此 PolBasis 行的 "work/vfield" 标签**未被本轮运行验证**，只有上表的实测尺寸是经过验证的。预注册的期望未被修改，相应 MISMATCH 保留并附说明。

### 5.4 红点

- **红点定义**：预期 F 为 REPORTED_FAILURE 而观察为 CRASH 或 SILENT_SWALLOW；或注入未命中（且未命中不是映射错误所致）。
- **F 列 CRASH / SILENT_SWALLOW：0 行。** F 列 11 个有效命中全部为 REPORTED_FAILURE。
- **F 列未命中：3 行（AL05、AL08、AL11 的 F 行）。** 原因是 5.3 的映射错误，三树一致，按定义不计为红点；但它意味着 **NTH5 对应的 PolBasis 分配点在本轮没有被注入到**，这一部分 F 行为**没有覆盖**。
- 本轮**没有红点被证实**。这不等于没有红点，只是本轮覆盖的 33 个有效命中点范围内没有 CRASH/SILENT。

### 5.5 本轮 F 列的结论边界（必须遵守）

- F 列的 REPORTED_FAILURE 只说明："在该注入（fft/jones/nv/vl 的 S4_malloc 第 k 次调用、fft plan 第 1 次调用、fft exec 第 1、2 次边界模拟）下，冻结树 F 的第一次调用返回了非零码。"
- 它**不是**"已修好"，也**不是**"已验证"：本轮**没有做 V3 重试等价检查**，也没有做与全新对象的字节比较。
- EXEC 行为边界模拟（`exec` 模式让 wrapper 返回 1，不运行 plan），不是真实执行失败。
- B 列是未修复基线的观察，**不是修复证据**。

### 5.6 seam 尝试

F 上族 A–D 的 seam（`apply_seam_r2.py --check-only`）失败：`ANCHOR ERROR S4/fmm/fmm_PolBasisJones.cpp call(15): "…NULL, NULL);" matched 0 time(s)`。原因：F 已把该站点改为 `&solve_info`，历史锚点不再存在。这是 U2 所述 info=NULL 七处的问题，需要 R3 按"函数名 + 第 n 次出现 + 紧邻上下文"的新定位方式处理。本轮**未对 F 构建族库**，因此 SI、FE、info=NULL 类点**本轮未运行**。

## 6. 范围与限制（R2 实际覆盖）

- 运行：3 列 × 15 行 = 45 次运行（B、A、F）。覆盖：fft 的 FMM 分配（NTH1、2）、plan 第 1 次调用、exec 第 1、2 次（边界模拟）、PolBasis 三模式的 NTH3–5（其中 NTH5 未命中）、控制行。
- 未覆盖（推迟 R3）：AL18（kottke fft_alloc_complex，需 kottke_alloc 族）、SI01–SI02（solve_info，需 linearsolve 族，F 上 seam 锚点失败）、FE01–FE10（fmmret 族未在 F 上构建）、info=NULL 七处、CLM1–4、ACF1、EXP40、kottke 与 closed 的 S4_malloc 点、PolBasis 的 cache-hit 路由（S4FMM_TWICE=slab NTH7）、exec 与 plan 的其余调用序号。
- H 树已构建，但**未在矩阵中运行**。
- 未做：V3 重试等价、V4 sanitizer、V5 残留项。

## 7. R3 建议

1. 重建 PolBasis 三模式的 S4_malloc 调用序映射（以实测尺寸为准，不沿用 S2R3 的标签），并补齐 NTH5 的覆盖或确认它不可达。
2. F 上的 info=NULL 七处 seam：按"函数名 + 第 n 次出现 + 紧邻上下文"定位，先做 check-only，锚点唯一后再构建。
3. FE01–FE10（fmmret 族，F 上 `fmm_ret` 已有接收）与 CLM1–4、ACF1、EXP40。
4. solve_info（SI01–SI02）与 AL18（kottke fft_alloc_complex）的 F 上族库。
5. V3 重试等价（同一对象重试与全新对象的字节比较，计数器与 ComputeLayerModes 入口）。
6. V4 sanitizer 与 V5 残留项，仍按 P05-S4 的原定义。

## 8. 违规与偏离披露

### 8.1 表一：越界写入尝试（命令自身写了仓库外路径）

本轮**没有命令写入仓库外路径**。本轮的 `/tmp` 顶层快照在开始、中间与结束时均为 sha256 `e3b0c442…`、条目 0，未变。

| 编号 | 轮次 | 命令 | 是否落盘 |
|---|---|---|---|
| — | — | 无 | — |

### 8.2 表二：工具与脚本事件

| 编号 | 轮次 | 命令 / 事件 | 是否落盘 | 处理 |
|---|---|---|---|---|
| T-1 | R1（延续） | `git fsck --lost-found --no-reflogs` | **是**，写入 `.git/lost-found/other/`（148 个悬挂对象） | R1 已披露；R2 未删除，未再运行 fsck。`.git/lost-found` 目前存在（`ls -d` 确认） |
| T-2 | R2-0 | 构建后核对 `git ls-tree … > "$EV/tmp/F_expected_blobs.txt"` | 是（仓库内 `$EV/tmp`） | 未经 safe_run。目标合法，后续用 safe_run 重做了同一核对 |
| T-3 | R2-2 | `git archive 1c11905 S4 \| tar -x -C "$EV/tmp/seamchk"` 与其 `2>/dev/null` | 是（仓库内 `$EV/tmp`） | 未经 safe_run，且用了 2>/dev/null。目标合法。已披露 |
| T-4 | R2-2 | `apply_seam_r2.py --check-only` 首次调用，`--repo` 误设为副本路径 | 否（脚本拒绝，exit 1） | 脚本保护检查拒绝；改为真实仓库根后得到锚点错误 |
| T-5 | R2-3 | 预注册文件 `write` 因版本保护拒绝（"file no longer exists"） | 否 | 改用新文件名 `_v2`，见 ERRATA_2 第 4 节 |
| T-6 | R2-3 | 运行器参数调用只给 5 个参数（缺 3 个 sha） | 否（argparse 式退出，未运行矩阵） | 改正参数后运行 |
| T-7 | R2-4 | 运行器 request 校验拒绝裸 `plan`/`exec` | 否（未运行，INVALID 结果为零） | 运行器改为接受注入器的裸模式 |
| T-8 | R2-2 | 导出核对：`find S4 … \| while read …; printf … > "$EV/tmp/F_export_blob.txt"` 与 `git ls-tree … > "$EV/tmp/F_git_blob.txt"`，直接 bash 重定向，未经 safe_run（仓库内 `$EV/tmp`） | 是（仓库内） | 已披露；同一核对随后经 safe_run 以 `F_export_sha256.txt`、`F_git_blob_list.txt` 重做 |

R1 的 write_guard.sh 与 asan_probe.sh 在 R2 中未使用，按要求冻结。

### 8.3 其它偏离

- R2 预注册 v2 的 NTH 映射错误（5.3）：预注册依据错误，已披露，期望未改。
- R1 的 EX、AL、P 的依据（R1 预注册）部分错误，已在 ERRATA_2 第 3 节列出。
- 本轮 `write` 工具写入的 `REGISTRY_S4_PRE_R2.tsv` 与 `DRAFT_INVALID` 文件已保留，未删除。

## 9. 仍未闭合缺口

1. 七处 info=NULL 的修前/修后 seam：**未运行**（F 上锚点失败）。
2. solve_info（SI01–SI02）与 AL18：**未运行**。
3. FE01–FE10、CLM1–4、ACF1、EXP40：**未运行**。
4. PolBasis 三模式 NTH5 分配点身份：**未确认**（未命中）。
5. V3 重试等价、V4 sanitizer、V5 残留项：**未做**。
6. H 树在矩阵中未运行。
7. apply_seam_r2.py 去向：已更正为"存在且跟踪"（ERRATA_2 第 1.1 节），**但 R1 出错的原因未深究**。

## 10. 已知限制

- 驱动为本轮按注入器重建的 plain 驱动，与历史驱动不比较（用户已确认的已知限制）。
- 判定器只读 rc、rc1、rc2、hit；它不区分"分配点"身份，类别仅反映调用结果。
- EXEC 为边界模拟。
- matrix_r2.py 不接受树标签 F，因此 F 的运行由 `testing/d003/stage_s4/run_r2_matrix.py` 完成（它只 import matrix_r2 与 judge_d003 的只读函数，不修改它们）。
- 运行器 `run_r2_matrix.py` 中 `real=(mode != "exec")` 的设置与 judge 的 real 参数一致，未改判定逻辑。

## 11. 路径清单

- 更正与证据：`checkpoints/p05/evidence/p05-s4r2/ERRATA_2.txt`、`TREES.tsv`、`REGISTRY_S4_PRE_R2_v2.tsv`（+ 哈希）、`REGISTRY_S4_PRE_R2_DRAFT_INVALID.tsv`、`run1/`、`run2/`、`run3/raw_R2.tsv`、`run3/runs/`、`RESULTS_R2.tsv`、`safe_run.log`
- 脚本（提交）：`testing/d003/stage_s4/build_tree_r2.sh`、`build_four_r2.sh`、`run_s4r2_build.sh`、`make_trees_r2.sh`、`run_r2_matrix.py`
- 脚本（R1 产物，冻结，未用于 R2）：`testing/d003/stage_s4/write_guard.sh`、`gate_v0.sh`、`asan_probe.sh`
- 签收记录（提交）：`checkpoints/p05/P05_S1_S2_SIGNOFF.md`
- 本报告（提交）：`checkpoints/p05/P05_S4R2_REPORT.md`
- 未动：`S4/`、`RNP/`、`rcwa.cpp`、`testing/d003/` 的历史文件（judge_d003.py、matrix_r2.py、run_all.sh、safe_run.sh 等）

## 12. 收尾核对

| 项 | 结果 |
|---|---|
| S4/ 相对 1c11905 的 diff | 空（树哈希 `4a6f6492…`） |
| /tmp 顶层快照 | sha256 `e3b0c442…`，条目 0，未变 |
| .git/lost-found | 存在（R1 遗留，未删除） |
| judge_d003.py | 未修改（sha256 `d2d04145…` 不变） |

本轮未完成，等待用户审核。P05-S4 未签收。
