# P05-S5 R6 报告（s5r6）：签收入账条件核对、ES5-17 文字更正、入口同步（纯文档子轮）

> 轮次：P05-S5 R6（s5r6，纯文档子轮；不是新阶段）。本轮不宣布任何阶段完成或签收；签收只由用户在对话中给出。
> 本轮不运行 make、不构建、不跑 D016/E2E/make test，不重跑任何历史门禁（含 gate_check_s5r4.py、gate_check_s5r5.py）。
> 本报告正文写于正式 end 门禁之前；本次 end 门禁的结果（COUNTS/FAILS/FINAL_STATUS）一律见附录 C（门禁后追加）。

## 1 本轮范围与开工基线

- 纯文档子轮：签收入账（条件未满足，见第 3 节）、ES5-17 三条文字更正、入口文档同步、end 门禁与 registry 组装。
- 未改 S4/、testing/d003/judge_d003.py、历史装置、RULINGS.tsv、签收草稿 v1/v2/v3、P05_S3_S4_SIGNOFF.md。
- 开工基线：分支 codex/p05-d003-fft-error-propagation；HEAD 8e55f6e534f95f6458e491423c09f624b4f1ae01（P05-S5 R5 (ii)）；HEAD:S4 = 589e15eb11fcb04e031b524f25a443e7921946cf（F4）；判定器 sha256 d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb；开工 git status --short 为空。

## 2 开工门禁（GATE_S5R6_start.txt）

- 脚本：testing/d003/stage_s5r6/s5r6_check.py --phase start（新增，只读核对；不读取任何门禁输出，只核对 GATE_S5R5_end.txt 的 sha256 与 FAILS=0 行）。结果写入 checkpoints/p05/evidence/p05-s5r6/GATE_S5R6_start.txt。
- COUNTS pass=39 fail=0 total=39；FAILS=0；CHECK_CRASHED=0。
- 覆盖项：分支 / HEAD=8e55f6e / HEAD:S4=F4 / 判定器 sha / S4 零改动 / status 仅本轮脚本；RULINGS.tsv 156852 B、sha256 d5742e70…、最大 U390、5 字段；ERRATA_S5.txt 15805 B、sha256 e1f02ee8…、最后条目 ES5-16；STATE.md sha256 c713a101…；P05_S5R5_REPORT.md sha256 9f90d6f7…、前 95 行 sha256 8f7f96b4…；签收草稿 v1/v2/v3 与 P05_S3_S4_SIGNOFF.md 的 sha；P05_S5_SIGNOFF.md 不存在；registries/s5r5 清单 12/12 OK（sha256 b8be693b…）；evidence/p05-s5r5 清单 20/20 OK（sha256 ff06d0ff…）；registries/s5r4 清单 15/15 OK；S5R5 end 门禁 sha256 1fd85744… 且 FAILS=0；/tmp 顶层快照 0 条（sha256 01ba4719…）落盘为 TMP_SNAPSHOT_S5R6.tsv；__pycache__ 基线 22 个（集合 sha256 fd6481c0…）。
- 首跑曾 FAIL 1/39（PYCACHE_BASELINE_SHA 的期望常量用 shell 的 find|sort 排序得到 2f1a4bd1…，与脚本内 Python sorted() 的 fd6481c0… 不同；同一 22 个目录，排序规则差异），修正期望常量后同一脚本重跑 39/39；见第 6.2 节事件 2。

## 3 签收入账（任务书第 2 节：跳过，条件未满足）

- 用户在对话中未给出 P05-S5 签收原文（任务书的占位符原样保留），因此第 2 节不执行。
- 未创建 checkpoints/p05/P05_S5_SIGNOFF.md；未追加 U391（RULINGS.tsv sha256 仍为 d5742e70…，最大编号 U390）；STATE.md 的“S5 签收”行写“等待用户签收”；PROJECT_ROADMAP.md 追加“P05-S5 等待用户签收”；P06 行保持“待执行”（不改为“待启动”）。
- 签收草稿 v1/v2/v3 均未改（sha256 c08bac3f… / 67876cd4… / c7fc843d…），P05_S3_S4_SIGNOFF.md 未改（sha256 7b5b412a…）。

## 4 勘误 ES5-17（三条文字更正；ERRATA 纯追加）

- ERRATA_S5.txt 15805 B → 17630 B（sha256 e1f02ee8… → 4af12052…），旧前缀逐字节不变（前缀 sha256 仍 e1f02ee8…）；最后条目 ES5-17，仅出现 1 次。小表 registries/s5r6/ERRATA_APPEND_S5R6.tsv。
- (a) 事实：R5 报告 §6.1 表一命令列的管道符未转义，原文 `awk -F'\t' ... | tee /dev/stderr | wc -l` 把 Markdown 表格拆成多列；正确写法是 `awk -F'\t' ... \| tee /dev/stderr \| wc -l`（同一命令、同一事件）。影响：只影响表格排版，不改任何判定。证据：checkpoints/p05/P05_S5R5_REPORT.md 第 50 行（R6 开工基线全文件 sha256 9f90d6f7…）。处理：R6 追加本勘误与 R5 报告附录 D(a)，第 1–95 行不改。
- (b) 事实：R5 报告 §7 把 POSCTRL_GATE_S5R5.txt 列入 registries/s5r5，但该文件实际只在证据目录交付：checkpoints/p05/evidence/p05-s5r5/POSCTRL_GATE_S5R5.txt（sha256 2c5e6f17…，checkpoints/p05/evidence/p05-s5r5/SHA256SUMS.txt 第 10 行）；registries/s5r5 清单实为 12 项（SHA256SUMS.txt 12 条；目录含清单自身共 13 个文件）。影响：只影响交付物清单文字，registry 冻结、不补文件。证据：P05_S5R5_REPORT.md 第 68 行；evidence/p05-s5r5/SHA256SUMS.txt（sha256 ff06d0ff…）；registries/s5r5/SHA256SUMS.txt（sha256 b8be693b…，12 条）；该 POSCTRL 文件头注明它本身就是 registry 聚合的阳性对照（registry↔posctrl 循环依赖的原因）。处理：附录 D(b)。
- (c) 事实：R5 报告附录 A 的 `COUNTS COUNTS\tpass=36\tfail=0\ttotal=36` 是 verifier 回显造成的重复，正确内容为 `COUNTS\tpass=36\tfail=0\ttotal=36`（shakedown 门禁文件第 44 行即该单行）。影响：只影响文字。证据：P05_S5R5_REPORT.md 第 79 行；checkpoints/p05/evidence/p05-s5r5/shakedown/gate/GATE_S5R5_end.txt 第 44 行。处理：附录 D(c)。
- R5 报告 10935 B → 12360 B，只追加“附录 D（S5R6 追加：文字更正，见 ES5-17）”；前 95 行 sha256 8f7f96b4… 前后不变，附录 A/C 未改（小表 registries/s5r6/REPORT_APPEND_S5R6.tsv）。

## 5 文档同步清单

| 文件 | 动作 | 结果 |
|---|---|---|
| checkpoints/p05/STATE.md | 重写为 S5R6 版本 | 5559 B（sha256 303faf5d…）；第 2 节补 S5R6 行、S5R5 行补“end 门禁 36/36 FINAL_STATUS=COMPLETE（附录 C）”；第 3 节 S5 签收=“等待用户签收”；无“无可做” |
| PROJECT_ROADMAP.md | 仅 P05 行行内追加（不删旧文字） | 追加“（ES5-15/16）…S5R5…36/36 FINAL_STATUS=COMPLETE 收口，见 P05_S5R5_REPORT.md 附录 C；P05-S5 等待用户签收”；P06 行未改（仍“待执行”） |
| testing/s4test/ISSUE_REGISTRY.md | 插入 1 行状态说明 | 新第 36 行；指向 R5 报告附录 C、R6 报告与签收文件；不改任何 OPEN 项状态 |
| checkpoints/p05/registries/s5r2/ERRATA_S5.txt | 纯追加 ES5-17 | 15805 → 17630 B，旧前缀不变 |
| checkpoints/p05/P05_S5R5_REPORT.md | 纯追加附录 D | 10935 → 12360 B，前 95 行 sha 不变 |
| checkpoints/p05/registries/RULINGS.tsv、P05_S5_SIGNOFF_DRAFT.md、P05_S5_SIGNOFF_DRAFT_v2.md、P05_S5_SIGNOFF_DRAFT_v3.md、P05_S3_S4_SIGNOFF.md、S4/、testing/d003/judge_d003.py | 未改 | sha256 不变（见附录 C 的 end 门禁） |

说明：PROJECT_ROADMAP.md 与 testing/s4test/ISSUE_REGISTRY.md 在 checkpoints/p05/ 与 testing/d003/ 之外；任务书第 4 节点名这两个文件，且历史轮（S5R2/S5R4）按同一惯例修改过，本轮照此执行，并在 end 门禁白名单中列明这两个文件。

## 6 两张事件表

### 6.1 表一：越界写入尝试

| 轮次 | 命令 | 目标 | 是否落盘 |
|---|---|---|---|
| s5r6 | `find . -name __pycache__ -not -path './.git/*' \| sed 's\|^\./\|\|' \| sort > /tmp/notallowed 2>/dev/null \|\| true`（重定向是误加；同一命令还违反“含写入的命令不得用 2>/dev/null”） | /tmp/notallowed（以 / 开头且不在 $REPO 下） | 未落盘：重定向未成功（错误被 2>/dev/null 隐藏）；随后只读快照 /tmp 顶层条目数=0、sha256 01ba4719…，与开工快照一致 |

### 6.2 表二：工具/脚本事件

| # | 事件 | 处理/影响 |
|---|---|---|
| 1 | s5r6_check.py 首跑 SyntaxError：ROUND_CHANGED_FILES_WITHIN_WHITELIST 的 lambda 用了跨行条件式而缺 else | 改为普通函数 changed_ok()；AST 语法检查通过后运行；未产生门禁输出 |
| 2 | start 门禁首跑 FAIL 1/39：PYCACHE_BASELINE_SHA 期望常量用 shell find\|sort 排序得 2f1a4bd1…，与脚本 Python sorted() 的 fd6481c0… 不同（同一 22 个目录，排序规则差异） | 期望改为 Python 口径 fd6481c0…；同一脚本重跑 39/39；首跑写出的 GATE_S5R6_start.txt（FAILS=1）被覆盖，最终以 39/39 版为准，事件如实记录 |
| 3 | 框架落盘 /tmp/dsh-spill-*（单列，不算执行者违规） | 无：/tmp 顶层开工与收尾均为 0 条 |
| 4 | heredoc 残留、仓库内路径拼写错误 | 无 |
| 5 | s5r6_append.py 首跑即通过（ERRATA 15805→17630 B、R5 报告 10935→12360 B，前 95 行 sha 不变） | 无额外修正 |

## 7 交付物与小表

- checkpoints/p05/registries/s5r6/：GATE_S5R6_start.txt、ERRATA_APPEND_S5R6.tsv、TMP_SNAPSHOT_S5R6.tsv、SHA256SUMS.txt（RULINGS 本轮无追加，故无 RULINGS_APPEND_S5R6.tsv）；正式 end 门禁文件 GATE_S5R6_end.txt 在门禁后追加并更新清单。
- 证据目录 checkpoints/p05/evidence/p05-s5r6/（SHA256SUMS.txt 覆盖非二进制证据；tmp/ 与 safe_run.log 按轮次惯例不纳入清单）。

## 8 收尾核对

- end 门禁使用同一脚本 testing/d003/stage_s5r6/s5r6_check.py --phase end，只有输出名不同：提交前先以 GATE_S5R6_pre.txt 运行一次（FAIL 先修脚本或数据），提交后正式运行一次写 GATE_S5R6_end.txt；正式结果见附录 C。
- git log -1 与 git status --short 在附录 C 记录（正文写入时正式提交尚未发生）。

FINAL_STATUS=PENDING_GATE

本轮已完成 P05-S5 R6 范围，等待用户审核。

## 附录 C（门禁后追加；只追加，不改正文）

正式 end 门禁在提交 (i) ddbb24a6da0f90fa72bd2dddd6682f649755583b 之后运行一次（冻结期规则：不修、不重跑、不放宽）。以下数值由 s5r6_appendix_c.py 从门禁文件派生：

- 门禁文件：checkpoints/p05/evidence/p05-s5r6/GATE_S5R6_end.txt（sha256 58676104fa8c02eaf2f6a4cf238a9e745ed0e12b40aa250074d242cf00212fd0）
- 提交前试跑（同一脚本，仅输出名不同）：GATE_S5R6_pre.txt（sha256 256490fbdf612058db514171a5ce3ecbda22ac3a085cdab59d0fff0d0a81d444），COUNTS pass=53 fail=0 total=53；FAILS=0
- 正式 COUNTS pass=53 fail=0 total=53；FAILS=0；CHECK_CRASHED=0
- 失败项：无
- 崩溃项：无
- 关键核对（全部 PASS）：S4/ 零改动且 HEAD:S4=F4；R5 报告前 95 行 sha256 8f7f96b4… 不变且纯追加；ERRATA_S5.txt 纯追加 ES5-17（前缀 e1f02ee8… 不变）；RULINGS.tsv 未改（无用户签收原文，U391 未写）；草稿 v1/v2/v3 与 P05_S3_S4_SIGNOFF.md 的 sha 不变；registries/s5r5 12/12 OK、registries/s5r4 15/15 OK、evidence/p05-s5r5 20/20 OK；判定器 sha 不变；本轮改动文件全部在白名单内；/tmp 前后快照一致（0 条）；无新建 __pycache__。
- git log -1：`ddbb24a6da0f90fa72bd2dddd6682f649755583b P05-S5 R6 (i): sign-off entry skipped (no user P05-S5 text -> no U391, no signoff file), errata ES5-17 text corrections (R5 report appendix D, first 95 lines sha unchanged), STATE/roadmap/issue-registry sync, s5r6_check 53 checks, s5r6 registry pre-gate tables; awaiting user review`
- git status --short（附录写入时，提交 (ii) 之前）：`M checkpoints/p05/registries/s5r6/SHA256SUMS.txt | ?? checkpoints/p05/registries/s5r6/GATE_S5R6_end.txt | ?? testing/d003/stage_s5r6/s5r6_appendix_c.py | ?? testing/d003/stage_s5r6/s5r6_sha_sums.py`（正式 end 门禁在提交 (i) 后立即运行，当时工作区干净；s5r6_appendix_c.py / s5r6_sha_sums.py 在其后新增，随提交 (ii) 入账）

FINAL_STATUS=COMPLETE

本轮已完成 P05-S5 R6 范围，等待用户审核。
