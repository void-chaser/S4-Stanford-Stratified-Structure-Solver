# P05 交付轮 REL-R3 报告（推送到 fork 并开 Draft PR）

> 轮次标识：**P05 交付轮 REL-R3**（rel-r3）。P05 的 S1–S5 已由用户签收（U391），S1–S5 与 REL-R1、REL-R2 的历史文件本轮一律未改。
> 本轮**不是 P05 的新阶段**，不引入任何新阶段编号；**本轮不修任何缺陷**，`S4/` 零改动，产品分支 `8e4c014` 未改写、未追加提交。
> 本轮是 P05 第一次写远端；所有远端写入只限 U393 的 4 个 ref。本报告正文在提交 (i) 冻结；正式 end 门禁结果只追加在结尾的附录 C（提交 (ii)）。

## 1 范围与开工门禁

目的：把 REL-R2 建好的产品分支、归档分支与两个附注标签推送到 void-chaser fork，并在 fork 内开一个 Draft PR；不新增验证主张，不修缺陷，不签收。

| 开工门禁项 | 期望 | 实测 |
|---|---|---|
| HEAD | `4607e96`（REL-R2 (ii)） | `4607e969ba138f8bcaffa4fba6340dd3b2e1f25b` ✅ |
| `git rev-parse HEAD:S4` | `589e15eb11fcb04e031b524f25a443e7921946cf` | 同 ✅ |
| 判定器 sha256 | `d2d04145…209eb` | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` ✅ |
| `git status --short` | 空 | 空（开工首条命令） ✅ |
| RULINGS.tsv 末条 | U392 | U392（396 行，158104 B，sha256 `ca9ab572…73c7`） ✅ |
| registries/rel-r2/SHA256SUMS.txt | 逐项 OK | 15/15 OK ✅ |
| 本地 `refs/heads/p05/d003-fft-error-propagation` | `8e4c014…`，其 `HEAD:S4` = `589e15eb…` | 同 ✅ |
| 两个标签 peel | `3de6d8b` / `c88bf30` | 同 ✅（tag 对象 `ef925cde…` / `b42c4c16…`） |
| 本地 `refs/heads/archive/*` | 不存在 | 不存在 ✅ |
| 只读 `git ls-remote origin` 与 REL-R2 记录 | 一致（无 p05/*、archive/*、两个新标签；master=`5b72793`；9 个 ref） | 一致（9 个 ref，master=`5b72793`） ✅ |
| `gh auth status` | 已登录 void-chaser（只读） | void-chaser，https，token scope 含 repo ✅ |
| /tmp 顶层快照 | 记录（条目数 + Python sorted() 口径 sha256） | 0 项；sha256 `01ba4719…a546b` ✅ |

写入路径：本轮所有含写入命令都经 `sh testing/d003/safe_run.sh p05-rel-r3 -- …`，写入目标限于 `$EV/`、`testing/d003/stage_relr3/`、`checkpoints/p05/`；未出现仓库外写入尝试（§8 表一为空）。

## 2 推送前补审（只读）

### 2.1 敏感信息补扫（`PUBLISH_AUDIT_RELR3.tsv`）

范围 `c88bf30..4607e96`（REL-R2 的两个记账提交，34 个文件），模式表与计数口径同 REL-R2 §6.2。

| 模式 | 命中（文件数） | 分类 |
|---|---|---|
| `ghp_` / `github_pat_` / `AKIA` / `BEGIN … PRIVATE KEY` / `password=` | 0 / 0 / 0 / 0 / 1 | **真实凭据 0**；唯一的 1 次是 `password=` 正则命中 REL-R2 报告审计表里**模式名本身**的表格行（该行写的正是这五个模式名的列表），按 REL-R2 §6.2 "报告/审计脚本因必然引用模式串而排除" 的同一口径归为 `PATTERN_QUOTE_NOT_SECRET`，**不计入 token/密钥类** |
| 绝对路径 `/srv/nvme/` | 9（7） | RECORD_ONLY（历史报告/STATE 中的路径） |
| 绝对路径 `/home/` | 8（5） | RECORD_ONLY |
| 用户名（jackal / void-chaser / Ziyang Li） | 10（4） | RECORD_ONLY |
| 邮箱 | 4（2） | RECORD_ONLY（上游作者署名与提交作者信息） |
| 主机名 | 0 | — |

结论：**真实 token/密钥类 = 0**，不触发硬停止（U397 的前提成立）。模式名自引用 1 次如实记录，见 §8 表二。

### 2.2 体积（`PUBLISH_VOLUME_RELR3.tsv`）

| 候选 | 范围 | 新增 blob | 总大小 | 最大 blob | ≥50 MB | ≥100 MB |
|---|---|---|---|---|---|---|
| A 归档分支 | `5b72793..4607e96` | 3101 | 48701808 B（46.45 MiB） | 1670487 B（1.59 MiB）`checkpoints/p05/registries/s4r9/M1R3/BARE_WRITE_AUDIT_R9M1R3.tsv` | 0 | 0 |
| P 产品分支 | `5b72793..8e4c014` | 11 | 315165 B（0.30 MiB） | 151229 B `S4/S4.cpp` | 0 | 0 |

**没有 ≥50 MB 的 blob**，不触发硬停止。

### 2.3 推送对象（`PUSH_PLAN_RELR3.tsv`）

| 顺序 | ref | 本地 sha | `git rev-list --count 5b72793..<ref>` |
|---|---|---|---|
| (a) | `refs/heads/p05/d003-fft-error-propagation` | `8e4c01491b6edec9eb4eaa617265ce9ca53bd548` | 2 |
| (b) | `refs/heads/archive/p05-d003-full-20261019` | `4607e969ba138f8bcaffa4fba6340dd3b2e1f25b` | 182 |
| (c) | `refs/tags/p05-signed-20261019` | tag 对象 `ef925cdea019a7cdf00acb66bc5b59d55f00d868`（peel `3de6d8b`） | 178 |
| (d) | `refs/tags/p05-rel-r1-20261019` | tag 对象 `b42c4c16298ce644f39c3c33ae6c26ef18820a96`（peel `c88bf30`） | 180 |

## 3 预注册与推送计划

`PREREG_RELR3.tsv` 在任何推送之前写好：9 行（R1–R9），状态 **INFLUENCED**；sha256 `4140c853dc67483afa66a0c877fda34c5ee21d7c1caf4c17666e9870d1304197`，UTC 2026-10-19T05:22:08Z（`PREREG_RELR3.tsv.sha256.txt`）。预注册之后未改写；无 ERRATA。

R9 的判定分两部分（预注册 method 列已写明）：V 表记录生成时的实测（HEAD 未被改写、工作区仅本轮记账文件）；"最终 `git status --short` 为空" 由 end 门禁在提交 (i) 之后复测（`RECORD STATUS_CLEAN_AFTER_COMMIT`）——比较表自身无法证明一个包含它自己的工作区为空。

## 4 推送执行（U393）

执行顺序 (a)→(b)→(c)→(d)，每条只推一次，**未加任何强制参数**；每条推完立刻只读 `git ls-remote origin <ref>` 并记录（`PUSH_LOG_RELR3.tsv`，stderr 合并进 stdout，未用 `2>/dev/null`）。

| 顺序 | 命令 | push rc | 推送后 ls-remote | 匹配 |
|---|---|---|---|---|
| (a) | `git push origin refs/heads/p05/d003-fft-error-propagation:refs/heads/p05/d003-fft-error-propagation` | 0 | `8e4c01491b6edec9eb4eaa617265ce9ca53bd548` | YES |
| (b) | `git push origin refs/heads/archive/p05-d003-full-20261019:refs/heads/archive/p05-d003-full-20261019` | 0 | `4607e969ba138f8bcaffa4fba6340dd3b2e1f25b` | YES |
| (c) | `git push origin refs/tags/p05-signed-20261019` | 0 | `ef925cdea019a7cdf00acb66bc5b59d55f00d868` | YES |
| (d) | `git push origin refs/tags/p05-rel-r1-20261019` | 0 | `b42c4c16298ce644f39c3c33ae6c26ef18820a96` | YES |

本地引用（U394）：`git branch archive/p05-d003-full-20261019 4607e96` 在推送前执行一次，核对 ref = `4607e96`、其 `HEAD:S4` = `589e15eb…`；未用 `-f`。主仓库其余 .git 写入只有 push 自动更新的 `refs/remotes/origin/*`；无 checkout/switch/reset/stash/clean/gc/prune/fsck/worktree。

推送后远端共 13 个 ref（9 个旧 ref + 4 个新 ref）：master 仍为 `5b72793`，6 个旧分支 sha 全部未变，`refs/pull/*` 未变（`REMOTE_BEFORE_RELR3.tsv` / `REMOTE_AFTER_RELR3.tsv`）。未向上游 victorliu/S4 写任何东西（`git remote` 只有 `origin`）。

## 5 Draft PR（U395）

用 `gh pr create` 在 fork 内开 **Draft** PR（参数逐字按 U395；正文用 `--body-file $EV/PR_BODY_RELR3.md`，英文，83 行）：

- PR：**#17** — https://github.com/void-chaser/S4-Stanford-Stratified-Structure-Solver/pull/17
- 只读核对（`gh pr view 17 --json state,isDraft,baseRefName,headRefName,commits,changedFiles`）：state=OPEN，isDraft=true，base=master，head=p05/d003-fft-error-propagation，commits=2，changedFiles=11。
- 未 merge、未 ready-for-review、未加 reviewer，未向上游开 PR。

PR 正文只引用 `doc/P05_D003_SUMMARY.md` 的内容与 REL-R2 §4 的 V1–V6 计数，并写明：故障注入装置不在本分支、本分支不带 D003 专用测试；审计记录在归档分支与两个标签上（ref 名已写出）；summary 文档 §6 的 "pending the REL-R3 push" 是写作当时的状态，推送已在本轮完成；不含"已修好""已实测可达"一类主张。

## 6 R6 远端克隆与 R7 make test

全部在 `$EV/remoteclone` 内进行（不入 git）；主仓库只读。

| 项 | 期望（预注册） | 实测 | 结果 |
|---|---|---|---|
| R6 克隆 | `git clone --branch p05/d003-fft-error-propagation <origin URL>` → HEAD=`8e4c014`、`HEAD:S4`=`589e15eb…` | clone rc=0；HEAD=`8e4c01491b6edec9eb4eaa617265ce9ca53bd548`；`HEAD:S4`=`589e15eb11fcb04e031b524f25a443e7921946cf` | **SAME** |
| R7 make test | rc=0；单元集合 = REL-R2 V3 的 265 个；无失败（合并 stderr 后再解析） | rc=0；units=265；failing=none；missing=none；extra=none；recon=True | **SAME** |

## 7 证据离线备份（只计划、不执行）

按 U398：备份由用户手工执行，本轮**不执行备份、不写仓库外路径**。已产出：

- `EVIDENCE_BACKUP_PLAN_RELR3.md`：rsync / tar 命令清单（可排除 `p05-rel-r2/prod`、`p05-rel-r2/verifyclone`、`p05-rel-r3/remoteclone` 与各轮 `tmp/`）、逐轮 `sha256sum -c` 校验步骤、以及 `relr3_backup_verify.py` 的只读用法。
- `testing/d003/stage_relr3/relr3_backup_verify.py`：只读校验脚本（对介质只读，报告只写 `$EV`）。**本轮未运行它去访问仓库外路径。**
- 当前 `checkpoints/p05/evidence` 约 **12256514048 B（11.42 GiB）**。

## 8 违规披露（两张表）

### 表一 越界写入尝试（命令自身写了仓库外路径，即使被拒绝/未落盘）

| 轮次 | 命令 | 是否落盘 |
|---|---|---|
| rel-r3 | 无 | — |

### 表二 工具/脚本事件

| 轮次 | 事件 | 是否落盘 | 说明 |
|---|---|---|---|
| rel-r3 | 审计脚本首次运行在 PUSH_PLAN 阶段中止：归档分支尚未创建，`git rev-list --count 5b72793..refs/heads/archive/…` 报 unknown revision | 否（仅已写的两张表被覆盖） | 改为对 tip commit（`4607e96`）计数后重跑；修复在预注册之前 |
| rel-r3 | 审计脚本第二次运行中止：tag 的 `git rev-parse` 输出带换行，拼进 `rev-list` 参数；同时表内 tag sha 会带换行 | 否（表被覆盖） | 对四个 tag sha 加 `.strip()` 后重跑；修复在预注册之前 |
| rel-r3 | 推送脚本 post-push 快照首次把 annotated tag 的 peeled `^{}` 行也当作 ref（写出 15 行而不是 13 行） | 是（`$EV/REMOTE_AFTER_RELR3.tsv`） | 只读改正：给推送脚本加 `--snapshot-only`（只做 ls-remote 并重写该表），**未重跑任何 push**；REMOTE_AFTER 只保留 ref 行 |
| rel-r3 | 预注册前写过一个 `testing/d003/stage_relr3/_probe.txt` 探测文件 | 是（允许目录内） | 经 safe_run 的 `rm -f` 删除，未进 manifest |
| rel-r3 | `gh auth status` / `gh pr create` / `gh pr view` 由工具自身可能写用户目录下的缓存或配置 | 用户目录（工具事件，未探测） | 按任务书 §6：不为此专门探测，只如实记录 gh 命令现象；PR 创建 rc=0、view rc=0 |
| rel-r3 | `git push` ×4 与 push 自动更新 `refs/remotes/origin/*` | 是（远端 + .git；U393/U394 授权） | 4 条 rc=0，无强制参数；每条推后只读 ls-remote 复核 |
| rel-r3 | R6 的 `git clone` 与 R7 的 `make test` 在 `$EV/remoteclone` 内写构建产物/测试临时文件 | 是（仅在 `$EV/remoteclone`） | 项目套件固有行为（与 REL-R2 同一口径）；克隆不入 git |
| rel-r3 | `$EV/safe_run.log` 由每次 safe_run 追加 | 是 | 故不纳入 `SHA256SUMS.txt` 的静态清单（在清单头部注明） |
| rel-r3 | /tmp 顶层快照 | start 与 end 各一次，均 0 项 | 由 `relr3_tmpsnap.py` 唯一负责 |

补充披露（审计分类）：补扫的 `password=` 模式在 `checkpoints/p05/P05_RELR2_REPORT.md` 命中 1 次，命中行是 REL-R2 报告里"五个模式名列表"的表格行本身；按 REL-R2 同一口径归类为 `PATTERN_QUOTE_NOT_SECRET`，真实凭据 0。该分类与原始命中均留在 `PUBLISH_AUDIT_RELR3.tsv`（两行汇总：`TOKEN_SECRETS_TOTAL=0`、`TOKEN_PATTERN_QUOTES_TOTAL=1`）。

## 9 待用户裁决

1. **归档分支是否快进**：`archive/p05-d003-full-20261019` 当前指向 `4607e96`（不含 REL-R3 的记账提交）。是否把归档分支快进到包含 REL-R3 记录的提交（会新增第 5 个待推 ref，需另行授权，不在 U393 范围内）？
2. **PR 转 ready / 合并**：PR #17 现在是 Draft。何时转 ready-for-review、是否合并到 fork 的 `master`（或先讨论），由用户决定；本轮不做。
3. **证据备份是否完成**：`EVIDENCE_BACKUP_PLAN_RELR3.md` 给了命令与只读校验步骤；是否执行、选什么介质、是否包含三个可重建克隆目录，由用户决定。
4. **敏感信息处理**：U397 已裁决接受现状、不改写历史；本轮记录的数字（§2.1）供用户复核。

## 10 两阶段提交与门禁

- 提交 (i)：本报告正文、`registries/rel-r3/` 小表、`testing/d003/stage_relr3/` 脚本、RULINGS.tsv 追加 U393–U398、STATE.md 新增 REL-R3 行。均为**本地提交，不推送**。
- 门禁：`relr3_check.py --phase start/end` 共用同一条只读代码路径（只差 `--out`）；按列名读表；跳过列数不等于表头的记录行；脚本名从 `testing/d003/stage_relr3/relr3_scripts.txt` 读取；状态解析用不经 strip 的原始 stdout；git 调用写成 `["git","-C",…]`；证据 SHA256SUMS 排除自身、`safe_run.log` 与门禁输出文件。end 门禁额外只读核对：远端四个 ref 的 sha、远端旧分支未变、PR 仍是 Draft 且未合并、提交 (i) 之后工作区为空。
- 提交 (ii)：正式 end 门禁**只跑一次**，结果只追加为本报告附录 C，门禁文件放入 `registries/rel-r3/`。FAILS>0 时不修、不重跑，照实写 INCOMPLETE。提交 (ii) 同样是**本地提交，不推送**。

<!-- COUNTS:BEGIN -->
PREREG_ROWS=9
PREREG_SHA256=4140c853dc67483afa66a0c877fda34c5ee21d7c1caf4c17666e9870d1304197
V_ROWS=9
V_SAME=9
V_MISMATCH=0
PUSH_REFS=4
PUSH_SUCCESS=4
PUSH_LS_REMOTE_MATCH=4
PUSH_PRODUCT_SHA=8e4c01491b6edec9eb4eaa617265ce9ca53bd548
PUSH_ARCHIVE_SHA=4607e969ba138f8bcaffa4fba6340dd3b2e1f25b
TAG1_OBJECT_SHA=ef925cdea019a7cdf00acb66bc5b59d55f00d868
TAG2_OBJECT_SHA=b42c4c16298ce644f39c3c33ae6c26ef18820a96
REMOTE_MASTER_SHA=5b72793051eb705f0e9b2e5398e1a5f0484da0cb
REMOTE_OLD_HEADS_CHANGED=0
PR_NUMBER=17
PR_STATE=OPEN
PR_ISDRAFT=true
PR_BASE=master
PR_HEAD=p05/d003-fft-error-propagation
PR_COMMITS=2
PR_CHANGED_FILES=11
R6_HEAD=8e4c01491b6edec9eb4eaa617265ce9ca53bd548
R6_HEAD_S4=589e15eb11fcb04e031b524f25a443e7921946cf
R7_RC=0
R7_UNIT_COUNT=265
R7_FAILING=none
A_NEW_BLOBS=3101
A_TOTAL_BYTES=48701808
A_LARGEST_BLOB_BYTES=1670487
A_BLOBS_GE_50MB=0
A_BLOBS_GE_100MB=0
SENSITIVE_NEW_TOKENS=0
RULINGS_APPENDED_ROWS=6
RULINGS_BEFORE_BYTES=158104
RULINGS_AFTER_BYTES=160477
ARCHIVE_BRANCH_SHA=4607e969ba138f8bcaffa4fba6340dd3b2e1f25b
ARCHIVE_BRANCH_S4=589e15eb11fcb04e031b524f25a443e7921946cf
<!-- COUNTS:END -->

下列代码块是报告中的派生数字（V 表、推送、PR、R6/R7、体积/敏感信息补审、RULINGS 追加），end 门禁会逐项与源表比对（按 key 名）。

不重跑任何 P05 历史验证的说明：本轮没有重跑 REL-R1 的 T3 或 S5 的 E2E；R7 只重跑产品分支克隆里的 `make test`。S5 的注入点依赖故障注入装置，该装置不在产品分支。

## 附录 A 交付状态（正文冻结时）

```
$ git log -1
4607e969ba138f8bcaffa4fba6340dd3b2e1f25b (REL-R2 (ii), 本轮开工基线；本轮提交见附录 C)
$ git status --short
(正文冻结时工作树只有本轮待提交文件；提交 (i) 之后的最终状态见附录 C)
```

## 附录 B 证据与注册表位置

* 证据：`checkpoints/p05/evidence/p05-rel-r3/`（`SHA256SUMS.txt`；含远端新克隆 `remoteclone/`，不入 git、不入校验清单）。
* 小表：`checkpoints/p05/registries/rel-r3/`（预注册及其 sha、PUSH_PLAN、PUSH_LOG、PUBLISH_AUDIT、PUBLISH_VOLUME、PUBLISH_REMOTE、REMOTE_BEFORE/AFTER、REMOTE_CLONE、PR、V、备份清单、RULINGS 追加记录、/tmp 快照、门禁文件、SHA256SUMS.txt）。
* 脚本：`testing/d003/stage_relr3/`（本轮新增，清单 `relr3_scripts.txt`；不改任何已有装置）。
* 远端：产品分支 `p05/d003-fft-error-propagation`（`8e4c014`）、归档分支 `archive/p05-d003-full-20261019`（`4607e96`）、标签 `p05-signed-20261019`（对象 `ef925cde`）、`p05-rel-r1-20261019`（对象 `b42c4c16`）；Draft PR #17。

## 附录 C 正式 end 门禁结果（门禁后只追加）

# 本附录由 relr3_appendix_c.py 在提交 (i) 之后、按任务书第 7 节正式运行一次 `relr3_check.py --phase end` 的结果追加；
# 正式门禁若 FAILS>0 不修、不重跑，照实写 INCOMPLETE。
