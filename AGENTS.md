# AGENTS.md — 本仓库的 agent 工作规则

> 本文件给任何在本仓库工作的 agent(规划者、执行者、复核者)读。它不依赖任何会话记忆。
> 与用户在当前对话中的明确指示冲突时,以用户指示为准;与 P05 已提交的阶段报告冲突时,以报告为准并在本轮报告中指出冲突。

## 1. 开工先读(按顺序)

1. `checkpoints/p05/STATE.md`:P05 当前轮次、冻结哈希、关键数字、开放问题。**每轮开工第一件事是读它并核对 HEAD。**
2. `PROJECT_ROADMAP.md`:项目主线与 P05 的验收标准(P05 行)。
3. 本轮任务书(用户给出的提示词)。
4. 需要历史细节时再读 `checkpoints/p05/*.md` 的各轮报告。`S4_HANDOFF.md` 写于 2026-10-01,分支与状态已过时,只作历史参考。

## 2. 阶段编号(固定,不得改)

- P05 只有五个正式阶段:P05-S1、P05-S2、P05-S3、P05-S4、P05-S5。
- 执行中追加的测试、补证、审计都记为原阶段的**子轮次**(例如 P05-S4 R5),不得升级为新阶段,不得出现 P05-S6。
- 历史文件名不改写。编号冲突时建对照表。
- **agent 不得宣布任何阶段完成或签收。** 签收只由用户在对话中给出,并记录到 `checkpoints/p05/` 的签收文件。
- 修复前的证据收集不得称为修复后的验证。

## 3. 写入路径硬规则(无例外)

每条含写入的命令开头先执行:

```
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/<本轮目录>; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
```

- "含写入"指出现 `>`、`>>`、`tee`、`cp`、`mv`、`mkdir`、`touch`、`tar -x`、`git archive`、`sed -i`,或任何会生成文件的程序(`make`、`g++`、`python` 脚本输出、`py_compile`)。**小管道、临时文件、核对命令一样算。**
- 这类命令一律经 `sh testing/d003/safe_run.sh <本轮目录> -- <命令>` 运行,不得裸跑。
- 写入目标只能以 `$EV/`、`$REPO/testing/d003/`、`$REPO/checkpoints/p05/` 开头。
- **任何以 `/` 开头但不在 `$REPO` 下的写入目标都不得出现,包括 `/tmp`、`/tmp_none` 之类的占位路径。核对命令需要临时文件时,用 `$EV/tmp/`。**
- 含写入的命令不得用 `2>/dev/null` 隐藏 stderr。核对路径只用 `ls -d` 或 `test -e`。
- 不做"沙箱是否拦截写入"的探测,不做拒绝性测试或反例测试。
- 长输出必须带 `head`/`tail`,或用读取工具的 offset/limit。
- 禁止会写 `.git` 或改工作区的 git 命令:`fsck`(尤其 `--lost-found`)、`gc`、`prune`、`stash`、`checkout`、`switch`、`reset`、`clean`。需要某提交的文件时,用 `git archive`(经 safe_run)导出到 `$EV/`,或 `git show` 只读。
- `.git/lost-found/` 是 P05-S4 R1 的 fsck 遗留,不删除、不再产生。
- 违规必须披露,分两张表:
  - 表一"越界写入尝试":命令自身写了仓库外路径(即使被拒绝、未落盘);
  - 表二"工具/脚本事件":裸跑写入、框架落盘(`/tmp/dsh-spill-*` 属框架,单列,不算执行者违规)、heredoc 残留、路径拼错等。
  每条写轮次、命令、是否落盘。
- 每轮开始与结束各对 `/tmp` 顶层做一次只读快照(条目数与 sha256),写入本轮 `$EV/` 的门禁文件。

## 4. 修改范围与提交范围

- 未经用户在对话中明确批准,不得修改 `S4/`(含 `S4/RNP/`、`S4/rcwa.cpp`、LinearSolve seam)。
- 不得修改 `testing/d003/` 下的历史装置:`judge_d003.py`、`matrix_d003.py`、`matrix_r2.py`、`run_d003.sh`、`run_all.sh`、`safe_run.sh`、`summarize_r6.py`、`src/`、`seam/`,以及 `testing/d003/stage_s4/` 下已提交的脚本。新脚本只能新增,文件名带本轮编号(如 `r5`)。
- `testing/d003/stage_s4/write_guard.sh` 冻结,不再使用、不再开发同类"守卫"脚本。
- 提交范围限 `checkpoints/p05/` 与 `testing/d003/`(以及经用户批准的 `AGENTS.md`)。提交信息末尾写 `awaiting user review`。
- `checkpoints/p05/evidence/` 被 `.git/info/exclude` 忽略,不提交。**小型结果表必须复制到 `checkpoints/p05/registries/<轮次>/` 提交**(见第 7 节)。

## 5. 判定与措辞规则

- 判定器 `testing/d003/judge_d003.py`(sha256 `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`)只依据事实:rc、rc1、rc2、信号、命中数。不读驱动的 PASS/FAIL 行。不修改判定器。
- 期望值必须在运行之前写入预注册文件并记录 sha256。之后的修改只能新建 `*_ERRATA*.txt`,不得改原文件,不得通过改期望消除 MISMATCH。
- 预注册受历史观察影响时,状态写 `INFLUENCED`,不得写 `BLIND`。
- 类别:CRASH、SILENT_SWALLOW、REPORTED_FAILURE、INVALID(未命中)、CONTROL_OK。
- **REPORTED_FAILURE 只表示"在该注入下返回码非零"。** 不得写"已修好""已验证""静态可达"。没有实测支撑的写"未验证",只读源码得到的写"[源码]"。
- B 列(未修复基线)的观察不是修复证据。
- 驱动的 `fft` 模式不进入 PolBasis,不得称为"VL 分支"。

## 6. 冻结提交与树(P05)

| 标签 | 提交 | `S4/` 树哈希 | 含义 |
|---|---|---|---|
| B | `37a82e8` | `1d738e64f9864a475fdb3de34cd3601605df2c64` | 未修复基线(运行器标签 `BASE`;与 Master `5b72793` 的 `S4/` 相同) |
| A | `876181c` | `85feec1151b36bbb7c8a7146fb6037609d9ff765` | 历史"当前"树(运行器标签 `CUR`);含 S3 提交 `b00b630`、`de52142`,不含 S3R/S3R2 |
| H | `64eb0b5` | `cb7fc613b28929db078a3e33025feea0074e87d8` | S2 参照树(与 `35cd7b3` 的 `S4/` 相同) |
| F | `1c11905` | `4a6f64927a30537740dd0c8f11f9a5aae5e46ba4` | P05-S4 的冻结被测树(含 S3、S3R、S3R2 全部修复;与 `ff6dd7c` 的 `S4/` 相同) |
| F2 | `a07b5ac` | `e124925f5b242486a913b813fa181664f665b048` | P05-S3R3 修复后的冻结被测树(RNV1 方案 R3 + 注释 U31) |
| F3 | `8d8202a` | `6cff923a02baf19e01966b2339755cbf3a5deeef` | P05-S3R4 修复后的冻结被测树(806、415 链路、RP-S3R4-1;U91 批准的四个文件);自检不是 S4 验证,修复后验证由 P05-S4 R8 在 F3 上完成 |

- 当前分支:`codex/p05-d003-fft-error-propagation`。
- 开工门禁:HEAD 与 `STATE.md` 记录一致;`git rev-parse HEAD:S4` 等于 F3 的树哈希(`6cff923a02baf19e01966b2339755cbf3a5deeef`,P05-S3R4 批准的门禁修改;除非用户已批准新的修复轮);判定器 sha256 一致;`git status --short` 为空(或仅含任务书点名的文件)。任一不符就停下报告。

## 7. 每轮结束必须做

1. 把本轮的小型结果表(预注册 tsv 与其 sha256、RESULTS、SITEMAP、COVERAGE、红点表、ERRATA、门禁文件;单个文件一般不超过 1 MB)复制到 `checkpoints/p05/registries/<轮次>/`,并在该目录写 `SHA256SUMS.txt`。复制后逐个比对 sha256 与原件一致。
2. 在本轮证据目录 `$EV/` 写 `SHA256SUMS.txt`,覆盖全部非二进制证据文件(日志、tsv、txt)。导出的树、库、驱动只记录 sha256,不复制进 git。
3. 更新 `checkpoints/p05/STATE.md`:当前轮次、HEAD、`S4/` 树哈希、本轮关键数字、开放问题的增减、证据目录与清单位置。保持一页以内;历史细节放在各轮报告里,STATE 只留摘要与链接。
4. 写本轮报告 `checkpoints/p05/P05_S4R<n>_REPORT.md`(其他阶段按其命名),结尾写"本轮未完成/已完成 R<n> 范围,等待用户审核",并附 `git log -1` 与 `git status --short`。
5. 提交以上文件,提交前核对 `git status --short`。
