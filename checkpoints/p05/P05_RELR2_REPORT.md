# P05 交付轮 REL-R2 报告（本地分支整理与上传前审查，不推送）

> 轮次标识：**P05 交付轮 REL-R2**（rel-r2）。P05 的 S1–S5 已由用户签收（U391），S1–S5 历史文件本轮一律未改。
> 本轮**不是 P05 的新阶段**，不引入任何新阶段编号；**本轮不修任何缺陷**，`S4/` 零改动；**不推送、不联网写远端**。
> 本报告正文在提交 (i) 冻结；正式 end 门禁结果只追加在结尾的附录 C（提交 (ii)）。

## 1 范围与开工门禁

目的：把 P05 的源码修复整理成可上传的产品分支，并完成上传前审查；不新增验证主张，不修缺陷。

| 开工门禁项 | 期望 | 实测 |
|---|---|---|
| HEAD | `c88bf30`（REL-R1 (ii)） | `c88bf30954a356e1cbdd49cf7a53218778c0ae3e` ✅ |
| `git rev-parse HEAD:S4` | `589e15eb11fcb04e031b524f25a443e7921946cf` | 同 ✅ |
| 判定器 sha256 | `d2d04145…209eb` | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` ✅ |
| `git status --short` | 空 | 空（开工首条命令） ✅ |
| RULINGS.tsv 末条 | U391 | U391（400 行，157296 B，sha256 `1c0aad12…19f545`） ✅ |
| registries/rel-r1/SHA256SUMS.txt | 逐项 OK | 18/18 OK ✅ |
| /tmp 顶层快照 | 记录（条目数+sha256） | 0 项；sha256 `01ba4719…a546b`（Python sorted() 口径） ✅ |
| 无预先存在的本轮标签/分支名 | 不存在 | `p05-signed-20261019`、`p05-rel-r1-20261019`、`refs/heads/p05/*` 均不存在 ✅ |

写入路径：本轮所有含写入命令都经 `sh testing/d003/safe_run.sh p05-rel-r2 -- …`，写入目标限于 `$EV/`、`testing/d003/`、`checkpoints/p05/`；唯一例外见 §8 表二第 1 条（裸跑写入，目标仍在允许目录内，未落盘到仓库外）。

## 2 产品分支构建

产品分支**只在 `$EV/prod` 的独立本地克隆中构建**（主仓库的 `git clone` 源只读；克隆内的 `checkout -b`、`commit` 属 U392 允许范围）。完整步骤记录在 `PROD_RELR2.tsv`。

| 项 | 值 |
|---|---|
| 分支 | `p05/d003-fft-error-propagation` |
| 基线 B | `5b72793051eb705f0e9b2e5398e1a5f0484da0cb`（S4 `1d738e64…`） |
| 源码来源 | `3de6d8bc7a35f036bf5ff6e508f5cdb5ef025505`（F4）的 `S4/` 树 |
| 提交 1 | `e6f5f52aa8e310cd04e4acf0f499518d22da373c` — `P05 D003: propagate FMM/FFT and pattern allocation failures to the public API` |
| 提交 2 | `8e4c01491b6edec9eb4eaa617265ce9ca53bd548` — `P05 D003: add the product-branch summary document` |
| 产品分支 HEAD | `8e4c01491b6edec9eb4eaa617265ce9ca53bd548` |
| **`HEAD:S4`（硬校验）** | **`589e15eb11fcb04e031b524f25a443e7921946cf`** ✅（提交后在克隆内实测） |
| 提交数（相对 B） | 2（每个提交都能构建：提交 1 的 S4 = F4，非 S4 构建输入 = B；提交 2 只加文档，构建输入不变） |
| 非 S4 新增路径 | 仅 `doc/P05_D003_SUMMARY.md`（95 行；sha256 `526e4716…01c71`） |
| 禁止路径 | 相对 B **没有新增** `checkpoints/`、`testing/d003/`、`AGENTS.md`；B 自带的 `checkpoints/014rf`、`checkpoints/p04-final`（111 个路径）是上游历史内容，未改动 |
| 产品分支工作树 | clean ✅ |

**`git diff --stat B..HEAD`**：

```
S4/S4.cpp                    | 103 ++++++++++++++++++++++++++++++-------
S4/S4_internal.h             |   4 +-
S4/fmm/fmm_FFT.cpp           |  18 +++++--
S4/fmm/fmm_PolBasisJones.cpp |  31 ++++++++---
S4/fmm/fmm_PolBasisNV.cpp    |  42 ++++++++++-----
S4/fmm/fmm_PolBasisVL.cpp    |  24 +++++++--
S4/fmm/fmm_closed.cpp        |  19 +++++--
S4/fmm/fmm_experimental.cpp  |   4 ++
S4/fmm/fmm_kottke.cpp        |  27 ++++++++--
S4/pattern/pattern.c         | 119 ++++++++++++++++++++++++++++++++++---------
doc/P05_D003_SUMMARY.md      |  95 ++++++++++++++++++++++++++++++++
```

10 个 S4 文件与 `git diff 5b72793 3de6d8b -- S4` 完全一致（+311/−80）；文档内容只依据该 diff 与 P05 报告写成，英文，≤200 行；不含"修复完成"一类主张，并注明故障注入装置不在产品分支。

## 3 免注入可达路径调研（可选最小回归测试的结论）

先只读调研，再用 9 个候选输入在 REL-R1 导出的 B、F4 树上各跑一次（F4 的 S4 源码与产品分支逐字节相同，故结果适用于产品分支）。每个候选在独立子进程中运行，崩溃会体现为进程返回码；证据：`NOREG_PROBE_RELR2.tsv`（18 行）、`NOREG_REPEAT_RELR2.tsv`（确定性对照 6 行）。

| 候选（公共 API 输入） | B | F4 / 产品分支源码 | 是否可区分 |
|---|---|---|---|
| `vl_nb1`：VL 基、NumBasis=1（D016 输入，触发 `pattern_generate_flow_field` 的 -10 路径） | RuntimeError 码 20 | RuntimeError 码 20（同一消息） | 否 |
| `nv_nb1` / `jones_nb1`：NV / Jones 基、NumBasis=1 | 返回有限值 | 返回有限值 | 否 |
| `cf_eps0`：闭式路径、ε=0 | 返回相同值 | 返回相同值 | 否 |
| `cf_epsbig`：闭式路径、ε=1e300 | 返回 -1.0（有限） | 返回 -1.0（有限） | 否 |
| `kt_eps0` / `kt_epsbig`：Kottke 路径、ε=0 / 1e300 | RuntimeError 码 20 | RuntimeError 码 20（F4 由新增非有限检查返回，B 由特征值求解返回；公共 API 层不可区分） | 否 |
| `cf_eps_singular_tensor` / `kt_eps_singular_tensor`：奇异 ε 张量 | 返回相同有限值 | 返回相同有限值 | 否 |

**结论：未找到免注入可达路径，产品分支不含 D003 专用测试。** 依据：

* D003 的修复点主要是**分配失败**与**求解状态**两类路径。分配失败（`S4.cpp`、`fmm_*/fmm_*.cpp`、`pattern.c` 的各 malloc、`fft_plan_dft_2d`、`Pattern_DiscretizeCell` 的 −12、containment tree 的 −4、流场 −11 等）在公共 API 下无法仅靠输入触发；P05 用**故障注入装置**才走到它们，而该装置是证据、不在产品分支（S5R3 的 E2E 结论见 §4 注）。
* 求解状态类路径（`LinearSolve` 零主元、流场零/非有限最大值）实测在 B 上同样以错误码 20 失败；两条树在公共 API 层的可观察结果相同，因此不能作为"B 失败/崩溃、产品分支返回可见错误"的判别性复现。
* 研究记录中另有一条观察（不作为任何主张）：`jones_nb1` 在 B 与 F4 上都是确定性的、但相差约 1.8e-18 绝对值；该配置属 R-P05-01 记录的 `n_G=1` 病态配置，本轮未追查（疑似与 `shape_get_intersection_area_quad` 改为 static 包装后的编译/内联差异有关，未验证），不改变 REL-R1 的非回归结论。

## 4 产品分支验证 V1–V6（预注册先行）

预注册：`PREREG_RELR2.tsv`（6 行，状态 **INFLUENCED**，sha256 `0d3c742d…f8d08`；`PREREG_RELR2.tsv.sha256.txt` 记录 UTC 2026-10-19T04:57:22Z），写在 V1–V6 任何运行之前；运行后未改写任何期望。

| 项 | 内容 | 结果 |
|---|---|---|
| V1 | 产品分支 `git rev-parse HEAD:S4` = `589e15eb…`（硬校验） | **SAME** |
| V2 | 产品分支非 S4 新增相对 B 只多出 `doc/P05_D003_SUMMARY.md`（≤200 行），无 `checkpoints/`、`testing/d003/`、`AGENTS.md`；白名单核对 | **SAME** |
| V3 | 产品分支的**新克隆**（`$EV/verifyclone`，HEAD 8e4c014、S4 589e15eb）里跑 `make test`：rc=0；单元集合 = REL-R1 T1 F4 单元集合；无失败；四段与 `Ran N`/skipped 对账 | **SAME**（rc=0；units=265；missing/extra/failing 均 none；recon=True） |
| V4 | 该克隆内 `cd testing && ./runtests.sh`：3 个独立参考全部 PASS，容差同 REL-R1 | **SAME**（rc=0；cases=3；输出 `Lua regression tests PASSED.`） |
| V5 | `build/S4`、`build/libS4.a` 的 sha256 与 REL-R1 F4 产物比较（只记录，不作门禁） | **RECORDED**：`build/S4` = `fb375c726101ae2d935e929fece54b1867aa0435b24e9fe92bdeda77314396f2`、`build/libS4.a` = `a28eaa5d6a0ed347870c9bf9f4c38d16cac23f340cfe17cf1725854f8c6d8b8d`，与 REL-R1 F4 **逐字节 SAME** |
| V6 | 两个附注标签存在且指向 `3de6d8b`、`c88bf30`；主仓库产品分支引用 = 克隆内产品分支 HEAD | **SAME**（tag1 type=tag→3de6d8b；tag2 type=tag→c88bf30；`refs/heads/p05/d003-fft-error-propagation` = 8e4c014 = 克隆 HEAD） |

<!-- COUNTS:BEGIN -->
PREREG_ROWS=6
PREREG_SHA256=0d3c742d3f5b4e7315986309fb9ef799f6d71c691e19aa81fe1adc5c40cf8d08
V_ROWS=6
V_SAME=5
V_RECORDED=1
V_MISMATCH=0
PROD_COMMITS_ABOVE_B=2
PROD_HEAD=8e4c01491b6edec9eb4eaa617265ce9ca53bd548
PROD_HEAD_S4=589e15eb11fcb04e031b524f25a443e7921946cf
PROD_DOC_LINES=95
V3_UNIT_COUNT=265
V3_FAILING=0
V3_MISSING=0
V3_EXTRA=0
V4_CASES=3
V5_BUILD_S4_SHA256=fb375c726101ae2d935e929fece54b1867aa0435b24e9fe92bdeda77314396f2
V5_LIBS4_SHA256=a28eaa5d6a0ed347870c9bf9f4c38d16cac23f340cfe17cf1725854f8c6d8b8d
A_NEW_BLOBS=3065
A_TOTAL_BYTES=48337858
A_LARGEST_BLOB_BYTES=1670487
A_BLOBS_GE_50MB=0
A_BLOBS_GE_100MB=0
P_NEW_BLOBS=11
P_TOTAL_BYTES=315165
P_BLOBS_GE_50MB=0
P_BLOBS_GE_100MB=0
SENSITIVE_TOKENS_A=0
SENSITIVE_TOKENS_P=0
SENSITIVE_ABS_SRV_A=5789
SENSITIVE_ABS_HOME_A=24
SENSITIVE_USERNAME_A=26
SENSITIVE_EMAIL_A=12
SENSITIVE_EMAIL_P=10
SENSITIVE_HOSTNAME=0
EVIDENCE_TOTAL_BYTES=12218966016
EVIDENCE_SUBDIRS=49
NOREG_PROBE_CASES=9
NOREG_PROBE_ROWS=18
NOREG_FOUND=0
RULINGS_APPENDED_ROWS=1
RULINGS_BEFORE_BYTES=157296
RULINGS_AFTER_BYTES=158104
TAGS_CREATED=2
<!-- COUNTS:END -->

下列代码块是报告中的派生数字（V 表、产品分支记录、体积/敏感信息审查表、备份清单、RULINGS 追加记录、/tmp 快照），end 门禁会逐项与源表比对（按 key 名）。

不重跑 REL-R1 的 T3（全部 examples）的推理：V1 已证明 `HEAD:S4` = F4 树；产品分支相对 B 的非 S4 改动只有 `doc/P05_D003_SUMMARY.md`，即 `Makefile*` 与 `examples/` 与 B、F4 相同（`git diff --name-only 5b72793..HEAD` 中非 S4 路径仅该文档）；REL-R1 的 T3 结论（SAME=317、BOTH_FAIL=12、NEW_FAIL=0、DIFF=0、FLAKY=0）在 F4 树上取得，F4 树与产品分支的 S4 相同、构建输入相同，故该结论按推理覆盖产品分支。这是推理，不是本轮重跑。

S5R3 的 E2E/注入结论（按 S5 报告原措辞）：42 点 = 25 注入点（Python 10、Lua batch 11、Lua REPL 4）+ 17 无注入对照；`CONTROL_OK=17`、`E2E_OK=25`，`FLAKY / INVALID / HIT_OFF_TARGET / API_SILENT / RETRY_* / MISSING_RUN` 均为 0；D016 点族 `MATCH=33 MISMATCH=0 FLAKY=0`。**这些注入点依赖 S5 的故障注入装置，该装置不在产品分支里。**

## 5 主仓库引用写入（U392）

| 项 | 结果 |
|---|---|
| `git tag -a p05-signed-20261019 3de6d8b -m "P05 S1-S5 signed off (U391)"` | 已建；tag 对象 `ef925cdea019a7cdf00acb66bc5b59d55f00d868`；peel 到 3de6d8b ✅ |
| `git tag -a p05-rel-r1-20261019 c88bf30 -m "P05 REL-R1 non-regression PASS"` | 已建；tag 对象 `b42c4c16298ce644f39c3c33ae6c26ef18820a96`；peel 到 c88bf30 ✅ |
| `git fetch <克隆> p05/d003-fft-error-propagation:p05/d003-fft-error-propagation` | 已建 `refs/heads/p05/d003-fft-error-propagation` = `8e4c014` = 克隆 HEAD ✅ |
| RULINGS.tsv 追加 U392 | 纯追加 1 行（5 字段，`生效`）；before 157296 B / `1c0aad12…`，after 158104 B / `ca9ab572…`；旧前缀逐字节与 sha256 不变 ✅（`RULINGS_APPEND_RELR2.tsv`） |
| 主仓库其它 .git 操作 | 无 checkout/switch/reset/stash/clean/gc/prune/fsck/worktree；唯一写入是上述 4 类（U392 授权） |

## 6 上传前审查（只读；不改写历史、不压缩、不备份）

### 6.1 体积（`PUBLISH_VOLUME_RELR2.tsv`）

| 候选 | 范围 | 新增 blob | 总大小 | 最大 blob | ≥50 MB | ≥100 MB |
|---|---|---|---|---|---|---|
| A 当前工作分支 | `5b72793..c88bf30` | 3065 | 48337858 B（46.10 MiB） | 1670487 B（1.59 MiB）`checkpoints/p05/registries/s4r9/M1R3/BARE_WRITE_AUDIT_R9M1R3.tsv` | 0 | 0 |
| P 产品分支 | `5b72793..8e4c014` | 11 | 315165 B（0.30 MiB） | 151229 B（0.14 MiB）`S4/S4.cpp` | 0 | 0 |

A 的范围口径：`c88bf30` 是本轮开工时的工作分支 tip；REL-R2 的记账提交（报告、registries/rel-r2、脚本、STATE、RULINGS）只新增 `checkpoints/p05/` 与 `testing/d003/stage_relr2/` 下的文本文件（见附录 C 的最终统计），均为 KB 级文本，不改变"无大文件"结论。两个候选都远低于 GitHub 的 50 MB 警告线与 100 MB 拒收线。

### 6.2 敏感信息（`PUBLISH_AUDIT_RELR2.tsv`，只记录、不改写）

| 模式 | A 命中（文件数） | P 命中（文件数） | 备注 |
|---|---|---|---|
| `ghp_` / `github_pat_` / `AKIA` / `BEGIN … PRIVATE KEY` / `password=` | 0 | 0 | 无 token/密钥类命中 |
| 绝对路径 `/srv/nvme/` | 5789（155） | 0 | 集中在 `checkpoints/p05/` 的历史报告/脚本（命令记录、证据路径） |
| 绝对路径 `/home/` | 24（11） | 0 | 同上（历史工作目录路径） |
| 用户名（`jackal`、`void-chaser`、`Ziyang Li`） | 26（13） | 0 | 同上 |
| 邮箱 | 12（12） | 10（10） | 两候选都只有上游作者 `vkl@stanford.edu` 的源码署名；P 的 10 处在改动的 S4 文件头部 |
| 主机名 | 0 | 0 | — |

扫描口径：A/P 对 `git diff --name-only 5b72793..<tip>` 的文件内容（`git show tip:path`）逐行匹配；D = 本轮尚未提交的文本文件（排除报告与审计脚本自身，因为它们按构造引用了这些模式串）。

### 6.3 远端状态（`PUBLISH_REMOTE_RELR2.tsv`，只读 `git ls-remote origin`）

* `origin` = `https://github.com/void-chaser/S4-Stanford-Stratified-Structure-Solver.git`（void-chaser fork）✅
* 远端现有 9 个 ref（6 个 `refs/heads/`：master、checkpoint/014rf-…、codex/master-integration-gate-…、codex/p04-acceptance-review-…、feature/python314-binding、fix/modern-linux-build）。
* `refs/heads/p05/*`、`refs/heads/archive/*`、两个新标签在远端**均不存在** ✅（本轮未推送、未联网写远端）。

### 6.4 证据目录离线备份清单（`EVIDENCE_BACKUP_RELR2.tsv`）

`checkpoints/p05/evidence` 当前磁盘占用 **12218966016 B（11.38 GiB）**，49 个子目录。Top 20（GiB）：p05-s4r8 1.95、p05-rel-r1 1.85、p05-s2r6 1.23、p05-s4r9 0.92、p05-rel-r2 0.80、p05-s2r3 0.56、p05-s4r7 0.55、p05-s4r5 0.41、p05-s3r 0.38、p05-s2r 0.35、p05-s4r4 0.27、p05-s3r2 0.26、p05-s2r5 0.23、p05-s2r2 0.20、p05-s1r 0.19、p05-s2b 0.18、p05-s3r4 0.17、p05-s2 0.16、p05-s3r3 0.14、p05-s5r3 0.13。

只给出方案，本轮**不执行备份、不压缩**（建议见 §9 待裁决 4）。注意：`p05-rel-r2` 下的 `prod/`、`verifyclone/` 是主仓库的本地硬链接克隆，`du` 会计入共享的 pack 块，故该目录的"磁盘占用"高估了它真正独有的数据；两个克隆都可由产品分支重建。

## 7 ROADMAP 与 ISSUE_REGISTRY 的相对 B diff 摘录（默认不带入产品分支）

`git diff 5b72793 HEAD` 统计：`PROJECT_ROADMAP.md` 10 行变更、`testing/s4test/ISSUE_REGISTRY.md` 22 行变更；合计 26 行新增、6 行删除（`git diff --stat 5b72793 HEAD`），其中 **10 行新增引用了 `checkpoints/p05` 路径**（产品分支不含该目录，直接带入会出现死链），0 行引用 `testing/d003`。

摘录（要点，非全文）：

* `PROJECT_ROADMAP.md`：P05 行从"待执行"改为 S1–S5 签收与 S5 收口记录（引用 `checkpoints/p05/P05_S3_S4_SIGNOFF.md`、`P05_S5R3/4/5_REPORT.md`、`registries/s5r3|s5r4|s5r5`）；P06 行状态格改为"待启动（前置 P05 已签收）"；风险/开放问题节新增 5 条 P05 登记（D016、R-P05-01、F10、F8、S1 报告 11.2 五哈希），引用 `checkpoints/p05/` 下多个文件。
* `testing/s4test/ISSUE_REGISTRY.md`：D003 行下新增 9 行记录（S3-4b 关闭、B 侧观察、RECORD_ONLY_OPEN 落位、P05-S5 签收入账）；新增 D016、D017、R-P05-02、R-P05-03 四行；P04/P05 状态文字与下轮顺序文字更新；其中 10 处引用 `checkpoints/p05/` 下的报告与 registries 文件。

是否带入产品分支、以及带入时如何裁剪，见 §9 待裁决 1。本轮按要求**未改** AGENTS.md、PROJECT_ROADMAP.md、ISSUE_REGISTRY.md。

## 8 违规披露（两张表）

### 表一 越界写入尝试（命令自身写了仓库外路径，即使被拒绝/未落盘）

| 轮次 | 命令 | 是否落盘 |
|---|---|---|
| rel-r2 | 无 | — |

### 表二 工具/脚本事件

| 轮次 | 事件 | 是否落盘 | 说明 |
|---|---|---|---|
| rel-r2 | 一次裸跑写入：`python3 - <<'EOF' … open('testing/d003/stage_relr2/relr2_noreg_probe.py','w') …`（为修正研究探针的 detail 字段） | 是（目标在允许目录内） | 未按 AGENTS.md §3 经 safe_run；写入目标 `testing/d003/stage_relr2/` 属允许范围，未落盘到仓库外。此后所有写入均经 safe_run |
| rel-r2 | 产品分支构建驱动在 `$EV/prod` 克隆内运行 `git clone / checkout -b / checkout -- / commit` | 是（均在 `$EV/prod`、`$EV/tmp` 内） | U392 明确允许；主仓库工作树未被 checkout/switch |
| rel-r2 | `relr2_prod.py` 首次运行因"禁止路径"检查口径（B 自带历史 `checkpoints/014rf`、`checkpoints/p04-final`）中止；第二、三次因脚本 bug（变量名/未定义变量）中止；每次中止后删除失败的 `$EV/prod` 并重建 | 是（仅 `$EV/prod`，已删除重建三次） | 检查口径改为"相对 B **新增**路径不含禁止目录"，并在报告中记录 B 自带的 111 个历史 checkpoints 路径；删除前用 `realpath` 核对目标确在 `$EV/` 下 |
| rel-r2 | `relr2_verify.py` 首次运行：V3 的 `make test` 日志把 stdout/stderr 分开捕获，导致解析顺序错乱（unittest 逐行输出在 stderr）；保留该日志为 `logs/maketest_attempt1_streams_unmerged.log` 后重跑 | 是 | 驱动器改为合并 stderr 到 stdout；期望与判定规则未改 |
| rel-r2 | `relr2_verify.py` 首次克隆后因 `%` 格式化笔误中止（克隆已成功，未删） | 是 | 修正后重跑，克隆复用 |
| rel-r2 | 免注入研究探针首版把 `GetPowerFlux` 返回值当标量处理（实际是 tuple），18 个候选全部报同一 Python 异常；修正后重跑（`NOREG_PROBE_RELR2.tsv` 为最终版） | 是（覆盖同一文件） | 研究探针不涉及预注册期望 |
| rel-r2 | 项目自带 `testing/runtests.sh` 在验证克隆内写 `tmpfile.*` 并用 `2>/dev/null` 隐藏 stderr | 是（克隆内；trap 退出即删） | 项目套件固有行为，非执行者违规（与 REL-R1 同一口径） |
| rel-r2 | 项目自带 `make test` 在验证克隆内执行 `rm -rf build`、重建 | 是（克隆内） | 项目套件固有行为 |
| rel-r2 | `$EV/safe_run.log` 由每次 safe_run 调用追加，内容随时间增长 | 是 | 故不纳入 `SHA256SUMS.txt` 的静态清单（在清单头部注明） |
| rel-r2 | /tmp 顶层快照 | start 与 end 各一次，均 0 项 | 由 `relr2_tmpsnap.py` 唯一负责；本机每条命令在私有 /tmp 中运行 |

## 9 待用户裁决

1. **ROADMAP / ISSUE_REGISTRY 是否带入产品分支**：默认不带入（本轮按任务书未带入）。若带入，建议裁剪：删除 10 处指向 `checkpoints/p05/` 的路径或改为"审计记录见归档分支/标签"的措辞；P05/P06 状态行保留；D016/D017/R-P05-02/R-P05-03 四行可保留（不含私有路径的表述需改写）。请裁决"不带入 / 带入并裁剪 / 带入全文"。
2. **敏感信息命中的处理**：A 候选有绝对路径（`/srv/nvme/` 5789 次、`/home/` 24 次）、用户名 26 次、上游作者邮箱 12 次；P 候选只有上游作者邮箱 10 次。本轮只记录、未改写历史。请裁决是否需要在 REL-R3 前对归档分支做历史改写/拆分（例如：敏感路径只保留在证据目录而不进归档分支，或接受现状）。 
3. **归档分支是否全量推送**：`archive/p05-d003-full-20261019` 含 `testing/d003/` 与全部 `checkpoints/p05/` 小表；是否全量推送，还是排除 `testing/d003` 下的历史大日志（体积审查显示新增 blob 仅 46.1 MiB、无 ≥50 MB 文件，故体积上不构成阻塞）。请裁决。
4. **证据离线备份介质**：`checkpoints/p05/evidence` 约 11.38 GiB（49 个子目录，Top 20 见 §6.4）；建议至少两份离线介质（例如一块外置 SSD + 一份校验过的归档副本），备份时保留 `SHA256SUMS.txt` 并逐项校验；`prod/`、`verifyclone/` 可由产品分支重建，可选择排除。请裁决介质与是否包含两个克隆。
5. **REL-R3 的 PR 目标**：建议在 void-chaser fork 内对 `master` 提 **Draft PR**（不直接推上游 `7fd00a2` 所在仓库），标题/正文引用 `doc/P05_D003_SUMMARY.md` 与本报告 §4 的 V1–V6；推送与 PR 需用户在 REL-R3 单独批准。

## 10 两阶段提交与门禁

* 提交 (i)：本报告正文、`registries/rel-r2/` 小表、`testing/d003/stage_relr2/` 脚本、STATE 入口同步、RULINGS.tsv 的 U392。
* 提交 (ii)：正式 end 门禁**只跑一次**（`relr2_check.py --phase end`）的结果追加为本报告附录 C，并把门禁文件放入 `registries/rel-r2/`。若 FAILS>0，不修、不重跑，照实写 INCOMPLETE。
* 门禁脚本 `relr2_check.py` 的 `--phase start/end` 共用同一条只读代码路径；按列名读表；脚本名从清单 `testing/d003/stage_relr2/relr2_scripts.txt` 读取；目录 sha 一律用 Python `sorted()` 口径。

## 附录 A 交付状态（正文冻结时）

```
$ git log -1
c88bf30954a356e1cbdd49cf7a53218778c0ae3e (REL-R1 (ii), 本轮开工基线；本轮提交见附录 C)
$ git status --short
(见附录 C 的收尾状态；正文冻结时工作树只有本轮待提交文件)
```

完整 `git log -1` 与 `git status --short` 见附录 C.1（门禁后追加）。

## 附录 B 证据与注册表位置

* 证据：`checkpoints/p05/evidence/p05-rel-r2/`（`SHA256SUMS.txt`；`prod/` 与 `verifyclone/` 为克隆，不入 git，不入校验清单）。
* 小表：`checkpoints/p05/registries/rel-r2/`（预注册、V 表、体积/敏感信息/远端/备份审查表、门禁文件、RULINGS 追加记录、SHA256SUMS.txt）。
* 脚本：`testing/d003/stage_relr2/`（本轮新增，清单 `relr2_scripts.txt`；不改任何已有装置）。
* 产品分支：`p05/d003-fft-error-propagation`（`8e4c014`）；标签：`p05-signed-20261019`（`3de6d8b`）、`p05-rel-r1-20261019`（`c88bf30`）。**均只在本机，待 REL-R3 推送。**

## 附录 C 正式 end 门禁结果（门禁后只追加）

本附录由 relr2_appendix_c.py 在提交 (i) 之后、按任务书第 7 节正式运行一次 `relr2_check.py --phase end` 的结果追加；
正式门禁若 FAILS>0 不修、不重跑，照实写 INCOMPLETE。
