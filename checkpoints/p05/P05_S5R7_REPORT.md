# P05-S5 R7 报告（s5r7）：P05-S5 签收入账（U391）与入口同步（纯文档子轮）

> 轮次：P05-S5 R7（s5r7，纯文档子轮；不是新阶段）。签收推理由用户在对话中给出，本轮只入账；执行者未自行宣布任何阶段完成。
> 本轮不运行 make、不构建、不跑 D016/E2E/make test，不重跑任何历史门禁（含 gate_check_s5r4.py、gate_check_s5r5.py、s5r6_check.py 的正式门禁结果）。
> 本报告正文写于正式 end 门禁之前；本次 end 门禁的结果（COUNTS/FAILS/FINAL_STATUS）一律见附录 C（门禁后追加）。

## 1 本轮范围与开工基线

- 纯文档子轮：把用户在对话中给出的 P05-S5 签收原文入账（签收文件、U391、STATE/ROADMAP/ISSUE 入口同步）、组装 s5r7 registry、跑 start/end 门禁。
- 未改 S4/、testing/d003/judge_d003.py、历史装置、历史报告正文、签收草稿 v1/v2/v3、P05_S3_S4_SIGNOFF.md、ERRATA_S5.txt、AGENTS.md。
- 开工基线：分支 codex/p05-d003-fft-error-propagation；HEAD 0358a06ee41f0b78984834bfdb758dd1a793296c（P05-S5 R6 (ii)）；HEAD:S4 = 589e15eb11fcb04e031b524f25a443e7921946cf（F4）；判定器 sha256 d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb；开工 git status --short 为空。

## 2 开工门禁（GATE_S5R7_start.txt）

- 脚本：testing/d003/stage_s5r7/s5r7_check.py --phase start（新增，只读；不读取任何门禁输出，只核对 S5R5/S5R6 门禁文件的 sha256 与 COUNTS/FAILS 行）。结果写入 checkpoints/p05/evidence/p05-s5r7/GATE_S5R7_start.txt（sha256 0368b119…）。
- COUNTS pass=48 fail=0 total=48；FAILS=0；CHECK_CRASHED=0。
- 覆盖项：分支 / HEAD=0358a06 / HEAD:S4=F4 / 判定器 sha / S4 零改动 / status 仅本轮 stage_s5r7 脚本；RULINGS.tsv 156852 B、sha256 d5742e70…、最大 U390、5 字段，且与 registries/s5r6/GATE_S5R6_end.txt 记录的 RULINGS sha 一致；ERRATA_S5.txt 17630 B、sha256 4af12052…、末条 ES5-17 且只出现 1 次；STATE.md sha256 303faf5d… 且无 S5R7 字样；P05_S5R5_REPORT.md / P05_S5R6_REPORT.md 及草稿 v1/v2/v3、P05_S3_S4_SIGNOFF.md 的 sha；P05_S5_SIGNOFF.md 不存在；registries/s5r4 15/15 OK、s5r5 12/12 OK、s5r6 4/4 OK、evidence/p05-s5r5 20/20 OK；S5R5 end 门禁 sha256 1fd85744… 且 FAILS=0；S5R6 end 门禁 sha256 58676104…、COUNTS 53/0/53、FAILS=0；顶层临时目录只读快照由 s5r7_tmpsnap.py 采集，0 条（sha256 01ba4719…）并落盘为 TMP_SNAPSHOT_S5R7.tsv；__pycache__ 基线 22 个（集合 sha256 fd6481c0…）；stage_s5r7 内只有 s5r7_tmpsnap.py 含单独的快照路径 token（TMP_TOKEN_ONLY_IN_TMSNAP）。
- 任务书 §0 写“GATE_S5R6_end.txt 含 … FINAL_STATUS=COMPLETE”；实测该文件含 COUNTS 53/0/53 与 FAILS=0，但 FINAL_STATUS=COMPLETE 实际写在 P05_S5R6_REPORT.md 附录 C（第 92 行）。start 门禁按“门禁文件 COUNTS/FAILS + 报告附录 C FINAL_STATUS”这一等价组合断言并记录实际位置（S5R6_FINAL_STATUS_LOCATION），未修改任何历史文件。这是文字位置差异，不改变 S5R6 已 COMPLETE 的事实。

## 3 签收入账（任务书第 2 节）

- 用户在对话中给出的 P05-S5 签收原文（任务书第 1 节）已逐字入账，未改写、未补全（含原文结尾的“。。”）。
- 新建 checkpoints/p05/P05_S5_SIGNOFF.md：2864 B（sha256 3093d4b5…）。§1 为 S1–S5 五行签收表（S5=已由用户签收，日期 2026-10-19，取对话日期）；§2 为范围声明原文逐字照录，与 stage_s5r7/s5r7_signoff_text.txt（1063 B，sha256 c7af2fb2…）逐字节相等（§2 sha256 c7af2fb2…）；§3 写对后续含义（P05 五个正式阶段全部由用户签收、转出项按原文 (e) 去向、P06 可启动、P05_S3_S4_SIGNOFF.md 的“P05-S5 未开始”为写于 S5 开始前的历史说明）；§4 为“本记录由执行者依据用户授权写入，执行者未自行宣布任何阶段完成”。
- RULINGS.tsv 只追加 U391（5 字段：id、来源=“用户对话签收原文（P05-S5 R7 任务书 §1）”、内容=签收原文 sha256 指针、依据、状态=生效），未改任何已有行：156852 B → 157296 B，sha256 d5742e70… → 1c0aad12…，旧前缀逐字节不变（前缀 sha256 仍 d5742e70…），U391 行 sha256 9d64674b…。小表 registries/s5r7/RULINGS_APPEND_S5R7.tsv（sha256 33ed90b0…）。
- P05_S3_S4_SIGNOFF.md 未改（sha256 7b5b412a…），其“P05-S5 未开始”只在新签收文件 §3 加历史说明，不回改该文件。

## 4 文档同步清单

| 文件 | 动作 | 结果 |
|---|---|---|
| checkpoints/p05/P05_S5_SIGNOFF.md | 新建 | 2864 B（sha256 3093d4b5…）；§2 原文 sha256 c7af2fb2… |
| checkpoints/p05/registries/RULINGS.tsv | 只追加 U391 | 156852 → 157296 B；前缀 sha 不变；新增恰好 1 行 |
| checkpoints/p05/STATE.md | 重写为 S5R7 版本 | 6050 B（sha256 d915ba20…）；阶段状态“S1–S5 已由用户签收（带范围声明）”；S5 签收行“已签收（U391）”；转出项保持 OPEN；不预写本轮门禁结果（只写“见 P05_S5R7_REPORT.md 附录 C”） |
| PROJECT_ROADMAP.md | 只在 P05 行末尾追加 + P06 行状态单元格 | P05 行追加“；P05-S5 已由用户签收（U391，见 checkpoints/p05/P05_S5_SIGNOFF.md），P05 有限范围收口”；P06 状态“待执行”→“待启动（前置 P05 已签收）”；其他行不变（6bb1cfb2… → 5bf8f44c…） |
| testing/s4test/ISSUE_REGISTRY.md | 只插入 1 行状态说明 | 新第 37 行；指向 P05_S5_OPEN_ITEMS.tsv；不改任何 OPEN 项（85cd329f… → 33eab5b7…） |
| ERRATA_S5.txt、草稿 v1/v2/v3、P05_S3_S4_SIGNOFF.md、S5R3–S5R6 历史报告、S4/、judge_d003.py、AGENTS.md | 未改 | sha256 不变（见附录 C 的 end 门禁） |

说明：PROJECT_ROADMAP.md 与 testing/s4test/ISSUE_REGISTRY.md 在 checkpoints/p05/ 与 testing/d003/ 之外；任务书第 2 节点名这两个文件，历史轮（S5R2/S5R4/S5R6）按同一惯例修改过，本轮照此执行并在 end 门禁白名单中列明这两个文件。P05 行按“只追加”规则保留了此前“P05-S5 等待用户签收”的历史文字；当前状态以行末追加的签收回口子句为准。

## 5 两张事件表

### 5.1 表一：越界写入尝试

| 轮次 | 命令 | 目标 | 是否落盘 |
|---|---|---|---|
| s5r7 | 无：本轮所有含写入的命令均以任务书规定的 preamble（REPO/EV/TMPDIR）开头并经 testing/d003/safe_run.sh 运行；顶层临时目录只经唯一的只读快照命令 python3 testing/d003/stage_s5r7/s5r7_tmpsnap.py 访问 | 无 | 不适用 |

### 5.2 表二：工具/脚本事件

| # | 事件 | 处理/影响 |
|---|---|---|
| 1 | 开工前有一条只读 python3 -c 扫描命令因 JSON 转义把 \n 当字面量而 SyntaxError（只读、无重定向、无目标路径、未落盘） | 未产生任何文件；该扫描改由 start 门禁内置的 TMP_TOKEN_ONLY_IN_TMSNAP 完成（48/48 PASS） |
| 2 | start 门禁首跑即通过 48/48（无需修正） | 无额外修正；GATE_S5R7_start.txt 即首跑结果 |
| 3 | end 门禁提交前试跑首跑 1 项 FAIL / 1 项 CRASHED：SIGNOFF_S5_SECTION2_SHA 的检查器 lambda 对 bytes 调 .encode（脚本缺陷，不涉及任何数据文件） | 修正该检查器表达式（sha_b(sec2) if isinstance(sec2, bytes) else "bad"）；同一脚本重跑 pre，试跑文件 GATE_S5R7_pre.txt 重新生成；正式门禁在提交 (i) 后运行，结果见附录 C |
| 4 | 框架落盘 /tmp/dsh-spill-*（单列，不算执行者违规） | 无：顶层临时目录开工与收尾快照均为 0 条 |
| 5 | heredoc 残留、仓库内路径拼写错误 | 无 |
| 6 | 写链脚本 s5r7_signoff.py / s5r7_rulings.py / s5r7_state.py / s5r7_entry.py / s5r7_registry.py 首跑即通过（各自内置基线与写后断言） | 无额外修正 |

## 6 交付物与小表

- checkpoints/p05/registries/s5r7/（门禁前）：GATE_S5R7_start.txt（sha256 0368b119…）、RULINGS_APPEND_S5R7.tsv（sha256 33ed90b0…）、TMP_SNAPSHOT_S5R7.tsv（sha256 e4890bb9…）、SHA256SUMS.txt（3/3 OK）；正式 end 门禁文件 GATE_S5R7_end.txt 在门禁后追加并更新清单。
- 证据目录 checkpoints/p05/evidence/p05-s5r7/（SHA256SUMS.txt 覆盖非二进制证据；tmp/ 与 safe_run.log 按轮次惯例不纳入清单）。
- 新增脚本：testing/d003/stage_s5r7/（s5r7_tmpsnap.py 为唯一的只读快照命令；其余为 check/signoff/rulings/state/entry/registry/appendix_c/sha_sums）。

## 7 收尾核对与建议

- end 门禁使用同一脚本 testing/d003/stage_s5r7/s5r7_check.py --phase end，只有输出名不同：提交前先以 GATE_S5R7_pre.txt 运行一次（FAIL 先修脚本或数据），提交后正式运行一次写 GATE_S5R7_end.txt；正式结果见附录 C。
- git log -1 与 git status --short 在附录 C 记录（正文写入时正式提交尚未发生）。
- 建议（AGENTS.md 本轮不改）：AGENTS.md 第 6 节“冻结提交与树（P05）”与第 2 节阶段编号可考虑在下一阶段开工时补一句“P05 已由用户签收（U391）、P06 待启动”，以降低新会话误读历史文本的风险；本轮按任务书要求只把建议写在此处。

FINAL_STATUS=PENDING_GATE

本轮已完成 P05-S5 R7 范围，等待用户审核。
