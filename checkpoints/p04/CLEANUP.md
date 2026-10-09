# 本地目录清理报告（P04 第一阶段，第 5 节）

执行时间：2026-10-09 UTC（清单快照 08:49Z；归档移动自 08:51Z 开始）。
源码改动与清理分开记录：清理未改动 solver 的任何运行缓存语义，也没有使用 `git clean -fdx` 或无范围的 `rm -rf`。
主仓库：`/srv/nvme/projects/S4-Stanford-Stratified-Structure-Solver`（检出分支 `checkpoint/014rf-offline-evidence-accepted-20261003`，未切换分支，未 reset/stash）。

## 1. 前后大小

| 项目 | 清理前 | 清理后 |
|---|---|---|
| `codex-review/` | 26,426,758,584 B，1,368,258 个文件 | 已移入归档（见第 3 节） |
| `audit-workspace/` | 5,394,270,338 B，2,323,017 个文件 | 已移入归档 |
| `testing/phase1-d001/` | 255,236 B，18 个文件 | 已移入归档 |
| `testing/phase1-d002/` | 739,655 B，24 个文件 | 已移入归档 |
| `testing/phase1-prep/` | 138,756 B，18 个文件 | 已移入归档 |
| `handoff/` | 2,744,099 B，162 个文件 | 已移入归档 |
| 根目录 `build/` | 3,945,238 B，30 个文件 | 已移入归档 |
| 根目录旧 `S4.cpython-314-x86_64-linux-gnu.so` | 742,368 B | 已移入归档 |
| `__pycache__` 目录（376 个） | 14,455,256 B | 已删除 |
| 主仓库（不含 `.git`） | 31,838,232,987 B | 8,221,641 B（约 8.2 MB，不含归档） |
| 归档 `.local-archive/p04-history-20261009T085100Z/` | — | 31,335,777,126 B，3,685,331 个文件 |

说明：归档位于同一块磁盘上，所以移动操作不释放空间。磁盘使用量在清理前后都是 `df` 显示的 65G（69,667,676,160 字节）。真正释放的空间是：归档内删除的编译产物 574,248,583 B（10,152 个文件，见第 2 节），缓存 14,455,256 B，以及下列重复 checkout 的构建产物（未逐项测量）。若要真正回收约 31 GB，需要用户决定是否删除归档。

## 2. 直接删除（可再生缓存与编译产物）

| 对象 | 数量 | 大小 | 依据 |
|---|---|---|---|
| `__pycache__` 目录（主仓库全部，其中 codex-review 36 个、audit-workspace 338 个、testing 2 个） | 376 个目录，其中 `.pyc` 在 codex+audit 中为 606 个 | 14,455,256 B | 字节码，可再生 |
| 归档内编译产物（`.o`、`.a`、`.so*`，以及带执行位的 ELF 文件；仅来自 codex-review 与 audit-workspace） | 10,152 个 | 574,248,583 B | **删除前已逐个记录 SHA256 与字节数**：`.local-archive/p04-history-20261009T085100Z/DELETED_BINARIES_INDEX.tsv`。源码、脚本、JSON 与报告保留 |
| 工作副本中的 `build/`、`build-seam/`、根目录 `.so`（product worktree） | — | 小 | 可再生，由 `testing/p04_run_all.sh` 重新生成 |
| `testing/s4test/__pycache__/`（product worktree） | — | 小 | 缓存 |

未删除的旧 `.so`（根目录）与旧 `build/`：作为“旧身份”证据移入归档，未直接删除。

## 3. 移入归档的历史数据（旧路径 → 归档路径）

归档根：`/srv/nvme/projects/S4-Stanford-Stratified-Structure-Solver/.local-archive/p04-history-20261009T085100Z/`（已加入主仓库 `.gitignore` 的 `/.local-archive/`，该改动尚未提交）。

| 旧路径 | 归档路径 | 原因 |
|---|---|---|
| `codex-review/` | `codex-review/` | P04 审核与运行历史树（大量重复的候选、object、replay 副本）。当前结论已摘录到 `checkpoints/p04/review-inputs/` |
| `audit-workspace/` | `audit-workspace/` | 早期审计工作区与历史 RUN，本阶段不再使用 |
| `testing/phase1-d001/` | `testing/phase1-d001/` | P02 原始 D001 运行；其模型与参考已复制为正常路径 `testing/d001/` |
| `testing/phase1-d002/` | `testing/phase1-d002/` | P03 D002 交接包；驱动与矩阵已复制为 `testing/d002/` |
| `testing/phase1-prep/` | `testing/phase1-prep/` | P01 准备包；模型与 oracle 已复制为 `testing/d001/` |
| `handoff/` | `handoff/` | 历史 DeepSeek/Codex 交接提示词，未被当前测试引用 |
| `build/`（根目录） | `root-old-identity/build/` | 旧构建产物，被新的 `build/` 取代 |
| `S4.cpython-314-x86_64-linux-gnu.so`（根目录） | `root-old-identity/S4.cpython-314-x86_64-linux-gnu.so` | 旧扩展身份；SHA256 `00c960a9b8fd21cf6b35c6b175ad069cc0d2a680cb8dead05ff0f50730c780af`（见第 5 节） |
| 早期探索运行（`d001-*`、`d002`、`error20`、`regress`、`verify-clean`） | `p04-runs-earlier/` | 中间版本脚本的输出，已被终验 `verify-final` 取代，仍作为历史证据保留（约 74 MB） |

## 4. 保留在原位的文件（未动）

| 路径 | 原因 |
|---|---|
| `testing/s4test/DEFECTS.md` | 用户已有修改（`git status` 中的 M），按要求原样保留，SHA256 `e79dfde9…` |
| `testing/s4test/ISSUE_REGISTRY.md` | 未跟踪的当前登记表；已追加“2026-10-09 P04 第一阶段状态”节（口径：implemented / targeted complete / pending independent production acceptance），原表与编号未改（清理后 SHA 与清理前不同，原因即此） |
| `PROJECT_ROADMAP.md`、`DEEPSEEK_P01_EXECUTION_PROMPT.md` | 当前计划文档（未跟踪）。`PROJECT_ROADMAP.md` 仅更新了 P02/P03/P04 的状态单元格（未改阶段编号与关闭范围） |
| `.diag_path_tmp` | 来源不明的未跟踪文件，内容为一条路径，未识别，保留 |
| `.claude/`、`.gitignore`（仅追加一行） | 工具配置；`.gitignore` 的新增行尚未提交 |
| 其余所有已跟踪文件 | 不属于本次清理范围 |

清理过程中我自己产生的临时文件（主仓库根目录的 `.p04_*` 中间文件，以及 `/tmp` 中的一个副本）已删除，已确认它们不是用户文件。

## 5. 完整性核对

* 归档后文件数：codex-review 1,358,621；audit-workspace 2,321,896；handoff 162。
  与清理前的数字核对：`1,368,258 + 2,323,017 − 1,358,621 − 2,321,896 − 10,152` = 606，即删除的 `.pyc` 数量（与 pycache 删除一致）。
* 关键文件 SHA256 在移动前后逐一相同（`PRODUCTION_ENGINEERING.patch` `1adef26c…`，`LANDING_MANIFEST.json` `359f9582…`，`REVIEW.md` `a8cc129c…`，`NEXT_CLAUDE_PROMPT.md` `78532839…`，`DEFECTS.md` `e79dfde9…`，`PROJECT_ROADMAP.md` `5ea088b7…`，`ISSUE_REGISTRY.md` 清理时 `19497d5b…`）。
* 审核输入的副本（`checkpoints/p04/review-inputs/`）与原件 SHA256 相同，清单见 `review-inputs/SHA256SUMS.txt`。
* 旧身份：根目录 `.so` 与 `build/` 移入归档前后未修改（只改位置）。归档内的身份记录：
  * `S4.cpython-314-x86_64-linux-gnu.so` `00c960a9…`
  * `build/libS4.a` `879a4606…`（与在 963ccf1 源码上重新构建的 libS4.a 的 SHA 相同，说明旧 build 对应 BASE 源码）
  * `build/S4` `19daaa77…`

## 6. 当前入口（清理后仍可用的位置）

| 用途 | 位置 |
|---|---|
| 产品源码、测试与 P04 流水线 | git worktree `/srv/nvme/projects/S4-p04-product-d001-d002`，分支 `codex/p04-d001-d002-production-20261009T082631Z` |
| 一键验证 | `sh testing/p04_run_all.sh <新运行目录>`（在任何干净 checkout 中执行，不依赖归档） |
| 终验运行证据（不在 Git 中） | `/srv/nvme/projects/S4-p04-runs-20261009T082631Z/verify-final/`（17 MB；`STEPS.txt`、`ARTIFACTS.sha256`、各 SUMMARY/JUDGE） |
| 提交的最小证据 | `checkpoints/p04/evidence/` |
| 历史归档 | `.local-archive/p04-history-20261009T085100Z/`（非构建输入，不被任何当前测试引用） |

清理后的正常测试入口不依赖归档：`testing/p04_run_all.sh` 从 `git archive 963ccf1` 导出 baseline，所有其它输入都在产品分支的跟踪文件中（已在全新克隆中验证）。

## 7. 未处理的具体阻塞

1. **空间未回收**：归档仍在同一磁盘上（31.3 GB）。删除归档需要用户明确决定，本次未删除。
2. **主检出没有可用的 Python 扩展**：根目录旧 `.so` 已移入归档。在主检出中使用 Python 需先运行 `make S4_pyext`（它会先生成 `build/libS4.a`，再运行 `setup.py build_ext --inplace`）。
3. **旧路径引用失效**：以下文件仍写着旧路径，归档后无法直接打开（本次未改写，只在本报告中登记映射）：`checkpoints/014rf/PROVENANCE.json`、`S4_HANDOFF.md`、`PROJECT_ROADMAP.md`、`testing/fmm-runner/README.md`、`DEEPSEEK_P01_EXECUTION_PROMPT.md`、`testing/s4test/ISSUE_REGISTRY.md`（引用的 `codex-review/`、`testing/phase1-*`）。
4. **`.gitignore` 的改动未提交**：主检出中新增 `/.local-archive/`，需要用户决定提交位置。
5. **归档文件数很大**（约 368 万个文件）：未压缩。压缩会生成新文件，超出本次“只移动、不复制”的范围，留待用户决定。
