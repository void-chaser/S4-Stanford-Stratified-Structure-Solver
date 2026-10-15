# P05-S4 R8 M2a（r8m2a）任务书：M1c4 审核登记 + M2 设计、装置构建与预注册冻结（不运行 S4 驱动）

> 本轮是 P05-S4 的子轮次 R8 M2a。不宣布任何阶段完成。先读 AGENTS.md 与 checkpoints/p05/STATE.md。
> 本轮**不运行任何 S4 驱动、运行器或 gdb**。允许：读源码与已提交文件、写新装置源码、经脚本编译（库、驱动、sanitizer 探针）、git archive 导出 F3 树、写设计表与预注册、用合成数据检验判定脚本。
> 工作量不是停止理由。只有 §1.5 列出的情况可以停止；任何停下都必须先跑 end 门禁，再做记录提交（U158）。
> 第一步：用 **write 工具**把本任务书原文保存为 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a.md`。

## 0. 开工基线（任一不符就停）
- HEAD = `ef8b087d33d26a4727f896b8dad88d862de93b3f`（r8m1c4 收尾提交）
- `git rev-parse HEAD:S4` = `6cff923a02baf19e01966b2339755cbf3a5deeef`（F3）
- 判定器 `testing/d003/judge_d003.py` sha256 = `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`
- `RULINGS.tsv` 89347 字节，sha256 `d52291a36549fccdf92aa5e725450c1e83fadd9341c2932721999662a76b469d`
- `ERRATA_8.txt` 66346 字节，sha256 `1930bc2b389c1859fd8c4a7b9c103dc7e01495f26ca8c199bda1b73ee6768ba4`
- `STATE.md` 8029 字节，sha256 `d64525cb12f7dd2126033e332d211a76cee8fa19693025df884dcf59097830de`
- `registries/s4r8/M1c/r8m1c4/M1_SUMMARY_R8_M1c4.tsv` sha256 = `f678af1fb3b62fddb840cba3086e8ef6d4030ff9e7d1577adc179adb37ab6d8b`
- `registries/s4r8/M1c/r8m1c4/FIX_COVERAGE_M1_R8_M1c4_R2.tsv` sha256 = `1226f73bf96d44185444b4b9b4c82f01aae8a9b762c482feb82a7a0e2cfa53b7`
- `registries/s4r8/M1c/r8m1c4/SHA256SUMS.txt`（24 项）与 `SHA256SUMS_END.txt`（2 项）全部 `-c` OK；该目录共 28 个文件
- `testing/d003/stage_s4/postcommit_r8m1c4.py` 已被跟踪，sha256 = `07752ac2f8d7b31df69ee7f3d27a885028030d62f82f94ddc4d3bc53ca1ab05f`
- 开工时 `git status --short` 只允许：`?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a.md` 和本轮新建的 `?? testing/d003/stage_s4/*r8m2a*`
- `EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a`；safe_run 的目录参数为 `p05-s4r8/m2a`
- `testing/d003/stage_s4/` 下所有已提交文件（含 `*r8m1*`）冻结，不修改、不运行（§1.6 的例外除外）。`evidence/p05-s4r8/` 下其他子目录只读。

## 1. 执行纪律（与 r8m1c4 相同，另加 §1.6）
### 1.1 写文件只有两条途径
**途径 A：write/edit 工具**，只能用于：本任务书副本；本轮新建的脚本、源码与允许列表（`testing/d003/stage_s4/*r8m2a*`）；本轮报告 `checkpoints/p05/P05_S4R8_M2A_REPORT.md`；`checkpoints/p05/STATE.md`。
**途径 B：经 `sh testing/d003/safe_run.sh p05-s4r8/m2a -- <本轮脚本及参数>` 运行的脚本。** 证据产物、编译产物、git archive 导出、RULINGS/ERRATA 追加（前缀校验）、registries 复制、提交、提交后记录，只能走途径 B。
**一律禁止：** 在 bash 中直接写任何文件（heredoc、`cat >`、`echo >`、`printf >`、`tee`、`cp`、`mkdir`，目标在仓库内也一样）；`safe_run.sh -- sh -c "<内联>"`。safe_run 后面只能接本轮的脚本文件。

脚本的其他要求：
- shell 脚本首行逐字为：
  `REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"`
- Python 一律用 `python3 -I -B`；EV 常量写成 m2a；临时路径写成 `os.path.join(EV, "tmp", ...)`。
- 编译器输出（`-o`）、依赖文件、目标文件一律落在 `$EV/build/` 下；编译命令显式写 `-o`，不得在仓库其他位置生成 `.o`、`a.out`、`__pycache__`。
- 不删除、不移动、不覆盖任何文件（U17）。产物作废时用 `_R2` 后缀新建，并在报告中标明。
- 复制到 registries 时保留原文件名（U226）。
- 源码、数据、ERRATA、报告正文中不写 `/tmp` 字面量，一律写"根目录临时区"。只有 §1.2 的快照命令例外。
- 追加 RULINGS/ERRATA 时，要追加的文本放在本轮新建的 builder `.py` 中，shell 追加脚本只调用 builder，不得含 heredoc。
- 复制历史源码（驱动、注入库、脚本）作为新装置起点时：新文件名带 `r8m2a`；把复制品中的 `REPO=$(git rev-parse --show-toplevel 2>/dev/null)` 换成标准首段，diff 中这一行的变化属预期；每个复制品用 `diff_src_r8m2a.sh` 把与原件的 `diff -u` 写入 `$EV/SRC_DIFF_R8_M2a_<名>.txt`，报告逐处说明。

### 1.2 内联命令白名单（不得含任何 `>` 字符，包括 `2>&1`）
- `git rev-parse HEAD`、`git rev-parse HEAD:S4`、`git status --short`、`git log -1 --format=%H%n%s`
- `sha256sum <仓库内文件>`、`ls -d <仓库内路径>`、`test -e <仓库内路径>`
- `date -u +%FT%TZ`
- 根目录临时区快照，逐字为：`date; ls -A /tmp | wc -l; ls -A /tmp | sha256sum; date`
- `sh testing/d003/safe_run.sh p05-s4r8/m2a -- <本轮脚本及参数>`
- 看文件用 read 工具（offset/limit），搜索用 grep 工具，找文件用 glob 工具。`ls -l`、`git ls-files`、`grep -c`、`ls`、`wc`、`head`、`tail`、`cut`、`awk`、`sed`、`git show`、`git diff` 一律不得内联使用；需要时写成本轮脚本经 safe_run 输出到 `$EV/`，再用 read 读取。

### 1.3 运行前检查（每个新脚本运行前都要做，包括门禁脚本与构建脚本）
顺序固定：用 write 写好脚本 → 跑 `date -u +%FT%TZ` → 用 grep 工具按下列正则查该脚本 → 0 行才可运行。查出问题后改正、重新查，不算违规（违规以执行为准）。报告逐条列出脚本名、UTC、命中行数。
正则（沿用 r8m1c4 收紧版；不得命中标准首段的 `"$EV/tmp"` 与 Python 的 `1 << 20`）：
`(^|[\s"'=(])/tmp([/\s"']|$)|/dev/null|<<[^ 0-9]|sed -i|git (checkout|switch|reset|clean|stash|gc|prune|fsck)|\bcp\s|\bmv\s|\btouch\b|\bsh -c\b|\bcat\s*>`
C/C++ 源码不跑 shell 正则，改查：`/tmp|getenv\("TMPDIR"\)|fopen\("/`，必须 0 行。

### 1.4 内联命令自查
报告"内联命令自查"一节逐条列出本轮执行过的全部内联命令（UTC 与原文）；白名单外的命令单列为偏离。

### 1.5 停止条件（仅限以下各项）
① 写入目标在仓库外；② 写入没走 §1.1 的两条途径；③ 运行了检查未通过的脚本；④ 门禁不符；⑤ 需要**实际修改** `S4/` 或已提交的历史装置才能继续本轮工作；⑥ 运行了任何 S4 驱动、运行器或 gdb；⑦ §4.6 判定脚本合成数据阳性对照失败。
- 设计中某项"需要改 `S4/` 才能测"不是停止条件：在设计表中标 `NEEDS_S4_CHANGE`，写明理由，继续其余项。
- 停止后仍要做 §8 收尾。

### 1.6 历史脚本的运行限制（U233）
本轮不运行任何已提交的历史脚本。若确需其功能，用 read 读原件，复制为 `*_r8m2a*` 新脚本（§1.1 复制品规则），把 EV 常量与输出名改为本轮，再按 §1.3 检查后运行。

## 2. 门禁（第一步做：先跑 start，再做任何追加或生成）
- 用 read 读 `testing/d003/stage_s4/gate_r8m1c4.sh`、`gate_check_r8m1c4.py`、`gate_allow_r8m1c4_start.txt`、`gate_allow_r8m1c4_end.txt`、`diff_gate_r8m1c4.sh`，用 write 新建对应 `*_r8m2a*` 五个文件。只改：基线 HEAD（§0）；证据目录与参数改为 `p05-s4r8/m2a`；输出名 `GATE_R8_M2a_<X>.txt` 及派生子输出名；自引用脚本名与允许列表名；RULINGS/ERRATA 前缀基准（§0）；允许列表内容（下文）；start 模式的附加核对项（下文）。
- `diff_gate_r8m2a.sh` 把五对文件的 `diff -u` 写入 `$EV/GATE_DIFF_R8_M2a.txt`（diff 返回 1 属正常）。
- start 允许列表（先写全，再跑）：`?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a.md`、`?? testing/d003/stage_s4/*r8m2a*`。
- start 附加核对：r8m1c4 两份清单（24 + 2 项）`-c` OK；§0 中 M1_SUMMARY、FIX_COVERAGE_R2、STATE、postcommit_r8m1c4.py 的 sha256；postcommit_r8m1c4.py 已被跟踪。
- end 模式：开工快照值与前缀基准从 start 门禁文件读取。status 只允许：
  - ` M`：`checkpoints/p05/STATE.md`、`checkpoints/p05/registries/RULINGS.tsv`、`checkpoints/p05/registries/s4r8/ERRATA_8.txt`
  - `??`：`checkpoints/p05/P05_S4R8_M2A_REPORT.md`、`checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a.md`、`checkpoints/p05/registries/s4r8/M2/r8m2a/*`、`testing/d003/stage_s4/*r8m2a*`
- end 另外核对：RULINGS 与 ERRATA 开工部分作为前缀逐字节不变；`registries/s4r8/M1c/r8m1c4/` 下 26 个被清单覆盖的文件 sha256 不变；仓库内无本轮产生的 `__pycache__`、`.o`、`a.out`（在 `$EV/` 之外）。
- 两份门禁 FAILS 都必须为 0。

## 3. 裁决与勘误登记（start 门禁通过后做）
### 3.1 RULINGS.tsv 追加（`append_rulings_r8m2a.sh` 调用 `build_rulings_r8m2a.py`；5 列；status"生效"；来源"P05-S4 R8 M2a 任务书 §3"；前缀校验）
- **U229**：接受 r8m1c4（`ef8b087`）的结果：独立重比 CHECKS=6840 DIFFS=0，U223 的条件满足，F3 236 行 MATCH 采信；M1 总表 1302 = MATCH 1252 + NOT_REACHED_AS_EXPECTED 44 + NOT_RUN_AS_EXPECTED 6，MISMATCH 0、FLAKY 0；806、1729/RP-S3R4-1、415 的 F3 行按返回码与类别口径 MATCH（U225）；阳性对照 A=2、A2=1、B=0、J=1；正式复现 7554/7554 相同。M1 的数据部分到此闭合，不构成任何阶段结论。
- **U230**：r8m1c4 任务书 §4.5 的"27 个文件"是规划者的计数错误：r8m1c3 registries 顶层有 29 个文件，其中 27 个由两份清单覆盖，另 2 个是清单本身。执行者在断言失败（写文件前退出）后把断言改为 29，按任务书数字更正接受，不算"看到结果后改期望"。
- **U231**：ADD22-A-10 的预注册（M1a6，`REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv` 第 740–741 行，env `FMM_MODE=closed1d;S4FMM_NG=1`）与映射表第 10 行和来源 `REGISTRY_S3R4C3_A_CTRL.tsv` 第 2–7 行（closed2d-ng1、fft-ng5、kottke-ng5 × F2/F3 共 6 个无注入对照）不一致，是 M1a6 预注册错误。M1b 中 A-10 两行按其登记的 env（closed1d NG=1）判定为 MATCH，结果保留，但不是映射第 10 行的对照。已提交的映射表与预注册不改（U17）。上述三个组合的无注入对照以 M0 的 `RESULTS_R8_NOINJECT_run1.tsv` 为准，本轮 §4.1 做只读交叉核对；M0 中缺少的组合，列入 M2 预注册（M2-00）。
- **U232**：修订 U225 中"I1–I6 不进 M2"的部分：806（A-1/2/3）、1729/RP-S3R4-1（A-4/5/6）、415（B-11…21）在 F3 上共 17 个注入点的 I1–I6 状态判定纳入 M2（项 M2-01）。F2 侧 806、415 为 CRASH，无法观察状态，不做；1729 的 F2 基线可选，做了也只作基线。U225 的其余部分（映射规则、返回码与类别口径已覆盖、U96 转 S5）不变。
- **U233**：r8m1c4 中 `verdict_m1c_r8m1c3.py` 的覆盖模式输出落在 m1c3 证据目录的 tmp 下（该脚本 EV 硬编码为 m1c3），这是 r8m1c4 任务书未核对 EV 常量造成的，按已披露接受；m1c3 证据目录的正式产物与清单不受影响。自本轮起，不运行任何历史脚本；需要其功能时复制为本轮脚本并改 EV（§1.6）。
- **U234**：r8m1c4 中白名单外的内联命令（`ls -l`、`git ls-files`）按执行偏离接受，不追认为合规。
- **U235**：M2 的执行方式：M2a 只做设计、装置源码与构建、预注册冻结、判定脚本合成检验，不运行 S4 驱动；M2b 按冻结的预注册运行（两遍，F3 为主，F2 作基线，B 只用于 M2-10）；M2c 做判定、汇总与红点台账更新。M2a 结束后停下，等用户审核预注册。Python/Lua 可见性（RP-R6d-15）并入 M3 的端到端链路，不在 M2 做。M2b 中检出的新红点按 U4 处理：修复位置和时机由用户另行决定，S4 轮不改 `S4/`。

### 3.2 ERRATA_8.txt 追加（`append_errata_r8m2a.sh` 调用 `build_errata_r8m2a.py`；只追加；前缀校验）
- **E8-88**：M1a6 预注册中 ADD22-A-10 的 env（closed1d NG=1）与映射表第 10 行和来源 A_CTRL 第 2–7 行不一致（U231）。r8m1c4 `FIX_COVERAGE_M1_R8_M1c4_R2.tsv` 中的 MAP_ENV_MISMATCH 2 行如实反映了这一点。原条目与原表不改。
- **E8-89**：r8m1c4 任务书 §4.5"27 个文件"应为"29 个文件（27 个由清单覆盖 + 2 份清单）"（U230）。
- **E8-90**：r8m1c4 的判定阳性对照在 m1c3 证据目录的 tmp 下生成了 `verdict_override.tsv`（U233）。

## 4. 本轮工作（全部输出到 `$EV/`；不运行 S4 驱动）
### 4.1 A-10 对照交叉核对（`a10_crosswalk_r8m2a.py`，输出 `A10_CONTROL_CROSSWALK_R8_M2a.tsv`）
- 输入：`registries/s3r4c3/REGISTRY_S3R4C3_A_CTRL.tsv`（6 行）、`registries/s4r8/EXPECT_R8_NOINJECT.txt`、`registries/s4r8/RESULTS_R8_NOINJECT_run1.tsv`（sha256 应为 `8d8effde9012b02da5c09c24e8f7ac973463fac24cb248f9694d95868cea027f`，先核对）。
- 对 closed2d NG=1、fft NG=5、kottke NG=5，逐个列出 M0 中 F2、F3 的 rc1、rc2、call1–3 比较结果与 M0 期望；状态写 `COVERED_BY_M0`（F3 rc1=rc2=0 且与期望一致）或 `MISSING_IN_M0` / `M0_DIFFERS`。
- 非 `COVERED_BY_M0` 的组合列入 §4.5 预注册的 M2-00（无注入对照，F2/F3 各一行）。

### 4.2 装置盘点（`inventory_r8m2a.py`，输出 `APPARATUS_INVENTORY_R8_M2a.tsv`）
- 用 grep 工具与本轮脚本只读扫描 `testing/d003/src/`、`testing/d003/seam/`、`testing/d003/stage_s4/`、`testing/d003/stage_s4r7/`、`testing/d003/stage_s4r8/`（以及其他 `stage_*` 中被 R7/R8 使用的驱动与注入源码）：每个 `getenv("...")` 的文件:行号、可取值（从源码读出，标[源码]）；每个驱动支持的 `FMM_MODE` 值；每个注入库支持的 `S4FMM_INJECT` 前缀（plan、exec、alloc、win、init、fmmret、linearsolve 等）及其计数方式。
- 列出 R8 已构建的 F3/F2 库与驱动（`registries/s4r8/BUILD_R8.tsv`、`DRIVERS_R8.tsv`、`DRIVERS_R8_F2_REUSED.tsv`），对每个文件重算 sha256 并与记录比较（`SAME`/`DIFFERENT`/`MISSING`）。不同或缺失的不得在 M2 复用。

### 4.3 M2 设计（输出 `M2_DESIGN_R8_M2a.tsv` 与 `M2_DESIGN_R8_M2a.md`）
设计表每项一行，列：item、需求来源（U 编号 / RP 编号 / 报告节）、目的、方法、驱动与注入库（现有 / 新建文件名）、树、env 模板、点数、期望依据（文件:行号 [源码] 或历史结果文件）、预注册状态（一律 `INFLUENCED`，除非能证明未看过相关结果）、判定规则、可行性（`FEASIBLE_EXISTING` / `FEASIBLE_NEW_APPARATUS` / `NEEDS_S4_CHANGE` / `NOT_FOUND`）、局限。`.md` 逐项说明方法与理由。各项的**最低要求**如下，不得缩减；如果做不到，写明原因与可行性类别，由用户裁决：

- **M2-00**（若 §4.1 有缺）：A_CTRL 三组合的无注入对照。
- **M2-01（U232）**：17 个 F3 注入点（ADD22 A-1…6、B-11…21 的 env 原样）在状态驱动上的 I1–I6 判定，规则与 R6c/R7 M3 的 G5 判定相同（引用规则来源文件与行号），两遍。若现有状态驱动（`driver_r6b_state.cpp` 系）不能与 win:/init: 注入库同时链接，设计新驱动 `driver_r8m2a_state_add.cpp`（复制品规则）。
- **M2-02 阶段 e**：定义取自 `registries/s4r6d/ERRATA_6d.txt` 第 50–70 行（HIT 位于所有层的 ENTER/RETURN 区间之外）。列出所有候选注入请求，并逐个写明位置（文件:行号）与是否在 D003 范围内（对照 U5b/E6-4：无 TWICE 时第 12 次 plan 来自 GetFieldOnGrid，属范围外）。如果候选全部在范围外，写 `NOT_FOUND_IN_SCOPE`，交用户裁决，不自行扩大范围。
- **M2-03 I7 sanitizer**：先写 `san_probe_r8m2a.sh`（新脚本，不得运行历史 `asan_probe.sh`），检查 `-fsanitize=address,undefined` 工具链是否可用（只编译运行一个不链接 S4 的探针；这不是 S4 驱动）。设计 F3 的 sanitizer 构建（库与驱动均在 `$EV/build/san/`），点集至少包括：G5/G6 中每个（mode × stage × inj_kind）单元格各 1 点，加上 ADD22 中 F3 的全部 17 个修复注入点。判定规则：sanitizer 报告数为 0，且 rc/类别与非 sanitizer 运行一致。
- **M2-04 双目标注入**：一次运行中触发两处失败，至少包含（a）同一层两处注入、（b）两层各一处。现有注入库不支持时，新建 `inject_r8m2a_dual.cpp`（复制品规则，只追加第二目标的逻辑，原有分支逐字不变）。期望：返回码非零、无信号，I1–I6 成立（规则来源同 M2-01）。
- **M2-05 其他层失败变体**（U20）：至少包含（a）图案层位于第 0 层、（b）图案层位于第 2 层、（c）两个图案层，分别在第一个或第二个上失败。需要新驱动时新建 `driver_r8m2a_layers.cpp`。
- **M2-06 K-1 张量路径**（RP-R6d-8）：`FMM_MODE=tensor`，目标是 `fmm_closed.cpp:244–246`（[源码]，F3 树中重新核对行号）的失败与 K-1 有限性检查。列出触发失败的注入方式（seam / alloc），期望写返回码与类别，不写"已修好"。
- **M2-07 NB=1–8**（RP-R6d-16）：NG=1…8 × 模式 {closed2d、fft、kottke，以及盘点中存在的 PolBasis 模式}：每格一个无注入对照，每个模式至少一个代表性注入。记录可得的 n_G（S3 T14 的口径）。无注入 rc 的期望依据 S3 T14 与 M0（例如 vl NG=1 的 rc 20），标 `INFLUENCED`。
- **M2-08 类别 C**（RP-R6d-17）：中间量错误到最终输出的传播。列出搜索过的配置（NB≥2 且执行期窗口内有分配的配置；S3 T13 指出 NB=9 无分配）。在 F3 上的判定是：失败被上报（rc≠0），且输出缓冲保持哨兵值或不被使用。没找到可用配置时写 `NOT_FOUND`，附搜索表。
- **M2-09 fmmret plain 干净对照与 CTRL_SEAM fmmret 完整补测**：依据 `registries/s3r4c5/CTRL_SEAM_DRIVER_RESOLUTION_C5.tsv` 与 ES3R4-29、U118、U124。点集覆盖 R7 M2b CTRL_SEAM 的全部 fmmret 行。
- **M2-10 RP-R6d-7**（BASELINE_ONLY）：B 侧 vl NG=1 无注入 rc 20 的来源。设计 B 上的 gdb 断点方案（断点位置写文件:行号 [源码]），结果只作基线，不是修复证据。
- 设计表末尾写一行 `M3_DEFERRED`：Python/Lua 可见性（RP-R6d-15），按 U235 在 M3 做。

### 4.4 新装置源码与构建
- 新源码只能是 `testing/d003/stage_s4/*r8m2a*`；复制品按 §1.1 规则产出 SRC_DIFF。
- 需要导出 F3（或 B）树时，用本轮脚本经 safe_run 执行 `git archive 8d8202a S4 ...` 到 `$EV/tree_F3/`（B 用 `37a82e8` 到 `$EV/tree_B/`）；导出后核对树哈希（`git rev-parse <提交>:S4`）并记录。
- 构建脚本 `build_r8m2a.sh`：编译库与全部新驱动（含 sanitizer 版）；产物在 `$EV/build/`；输出 `BUILD_R8_M2a.tsv`（产物名、路径、sha256、源文件 sha256、编译命令、UTC、rc）。任何一项编译失败如实记录，对应设计项改标 `BUILD_FAILED`，不得改 `S4/`。
- 本轮不运行任何构建出的驱动（停止条件 ⑥）。

### 4.5 预注册冻结（`prereg_r8m2a.py`，输出 `PREREG_M2_R8_M2a.tsv`、`PREREG_M2_R8_M2a.sha256`、`PREREG_M2_R8_M2a_TIMESTAMP_UTC.txt`）
- 列：point_id（`M2-<项>-<序号>-<树>`）、item、tree、driver、driver_sha256（取自 BUILD 或 DRIVERS 记录）、lib_sha256、env（完整键值对）、passes（2）、exp_rc1、exp_rc2、exp_signal、exp_hit、exp_class、exp_I1…exp_I7（不适用写 `-`）、exp_stage、basis、status。
- 每个可行项都必须有点；`NEEDS_S4_CHANGE` / `NOT_FOUND` 项不出点，但在汇总中列出。
- 汇总 `PREREG_M2_COUNT_R8_M2a.txt`：按 item × tree 计数，**断言各项之和 = 总行数**，断言失败就不写预注册文件、输出 FAIL。
- 预注册写完后不得修改；之后的更正只能新建 `*_ERRATA*`。

### 4.6 判定脚本与合成数据阳性对照
- 新建 `verdict_m2_r8m2a.py`：输入为 RESULTS 目录（相对仓库根，参数传入）、预注册路径、OUT_PREFIX（输出名由它生成，必须实际使用）。返回码与类别部分调用 `judge_d003.py` 的分类结果或按其规则只读重写（引用规则行号）；I1–I7 与阶段规则引用来源文件与行号。
- `posctrl_m2_r8m2a.py`：从预注册生成合成 RESULTS 到 `$EV/tmp/posctrl_*/`：A = 全部等于期望 → 期望 MISMATCH 0；B = 改一个 exp_rc1 对应的观察值 → MISMATCH 1，且被改的 point_id 出现在输出中；C = pass1 与 pass2 不一致 → FLAKY 1。必须用 subprocess 调用正式的 `verdict_m2_r8m2a.py`。计数如实记录，输出 `POSCTRL_M2_R8_M2a.txt`，以 `POSCTRL=PASS/FAIL` 结尾。FAIL → 停止条件 ⑦。

## 5. 措辞
- 设计与预注册只写"期望"，不写结果；本轮没有任何 S4 运行结果。
- REPORTED_FAILURE 只表示"该注入下返回码非零"。只读源码得到的写"[源码]"。B/F2 观察不是修复证据。不写"已修好""已验证"。驱动 fft 模式不称"VL 分支"。

## 6. 报告数字核对（`check_report_counts_r8m2a.py`）
- 报告中写核对标记：`M2A_PREREG_ROWS=`、`M2A_ITEMS_FEASIBLE=`、`M2A_ITEMS_NEEDS_S4_CHANGE=`、`M2A_ITEMS_NOT_FOUND=`、`M2A_BUILD_OK=`、`M2A_BUILD_FAILED=`、`M2A_A10_COVERED_BY_M0=`、`M2A_POSCTRL_A_MISMATCH=`、`M2A_POSCTRL_B_MISMATCH=`、`M2A_POSCTRL_C_FLAKY=`、`M2A_INVENTORY_SHA_DIFFERENT=`。
- 脚本从证据表重新计算每一项后比对，输出 `REPORT_COUNT_CHECK_R8_M2a.txt`（`ALL_MATCH` 或列出不一致项）；另外独立断言 PREREG 总行数等于各项之和。

## 7. 本轮不做
不运行 S4 驱动、运行器、gdb；不做 M2b/M2c/M3；不修改任何已提交文件（STATE、RULINGS、ERRATA 的追加除外）。

## 8. 收尾（完成或停止都要做）
1. 先写好 `postcommit_r8m2a.py`（输出 `$EV/POSTCOMMIT_R8_M2a.txt`，U17 拒绝覆盖），提交前通过 §1.3 检查并随本轮提交，提交后只运行（U222）。
2. `copy_registries_r8m2a.py`：复制到 `checkpoints/p05/registries/s4r8/M2/r8m2a/`，**保留原名**；先确认全部输入存在再建目录；写 `SHA256SUMS.txt` 并逐个比对 sha256。复制范围：start 门禁、GATE_DIFF、A10_CROSSWALK、APPARATUS_INVENTORY、M2_DESIGN（tsv 与 md）、全部 SRC_DIFF、BUILD_R8_M2a.tsv、PREREG 三件与 COUNT、POSCTRL、REPORT_COUNT_CHECK（含 `_R2`，如有）。单个文件超过 1 MB 的只记 sha256。编译产物与导出的树不复制。end 门禁文件在 end 门禁后单独追加复制，写入 `SHA256SUMS_END.txt`。
3. `sums_ev_r8m2a.py`：在 `$EV/` 写 `SHA256SUMS.txt`，覆盖全部非二进制证据（不含 `tmp/`、`build/`、`tree_*/`；二进制产物的 sha256 已在 BUILD 表中）。
4. 用 edit 工具更新 STATE.md，必须 ≤ 8192 字节（字节数用本轮脚本确认）：本轮开工基线改为 `ef8b087`；当前轮次改为 r8m2a（M2 设计与预注册，待用户审核）；关键数字新增一行 M2a（预注册行数、可行项数、构建结果）；开放问题中"806、415、RP-S3R4-1"一行的去向改为"I1–I6 纳入 M2-01（U232）"；双目标/I7、其他层、K-1、NB=1–8、类别 C、阶段 e、RP-R6d-7、CTRL_SEAM fmmret 各行的去向写成对应的 M2 项编号；Python/Lua 一行写"M3（U235）"；证据位置只保留最近三轮（m2a、m1c4、m1c3）。
5. 用 write 写报告 `checkpoints/p05/P05_S4R8_M2A_REPORT.md`，须包含：开工门禁；U229–U235；E8-88–E8-90；§4.1–§4.6 的结果；各 M2 项的设计摘要表（项、方法、点数、可行性、局限）；需要用户裁决的事项（`NEEDS_S4_CHANGE`、`NOT_FOUND`、阶段 e 的范围问题等）；"运行前检查"与"内联命令自查"两节；违规表一、表二；根目录临时区的开工与收尾快照。结尾写"本轮未完成/已完成 R8 M2a 范围，等待用户审核"。写完后运行 `check_report_counts_r8m2a.py`；不是 ALL_MATCH 就用 edit 修正报告后重跑（输出加 `_R2` 后缀），两次结果都保留。
6. 跑 end 门禁（FAILS=0），再用 `commit_r8m2a.sh` 经 safe_run 提交（脚本内先核对 status，只 add 指定路径）。提交信息：
   `P05-S4 R8 M2a (r8m2a): U229-U235, E8-88..E8-90, A-10 control crosswalk, apparatus inventory, M2 design (items M2-00..M2-10), new apparatus build, M2 prereg frozen (<n> rows), verdict posctrl on synthetic data; no S4 driver run; awaiting user review`
   在停止条件处停下时，提交信息改为说明停在哪一步，同样以 `awaiting user review` 结尾。
7. 提交后经 safe_run 运行 `postcommit_r8m2a.py`，并在最终回复中原文给出它的输出。此后不再新建任何文件；`git status --short` 应为空。

## 9. 最终回复（简短中文）
列出：U229–U235、E8-88–E8-90 是否已登记；A-10 交叉核对结果；装置盘点中 sha256 不一致的数量；M2 各项的可行性与点数表；构建结果；预注册总行数与 sha256；判定阳性对照 A/B/C 的计数；违规表；提交后的 `git log -1` 与 `git status --short`；需要用户裁决的事项。
不得出现"签收""已修好""已验证"等字样（否定用法也避免）。
