# P05-S4 R8 M1a 续3b1：审核接受、小瑕疵修正、M1b/M1c 正式预注册

你是 P05-S4 的验证执行者。本轮属于 P05-S4 R8 M1a 续3b 的第一部分（续3b1），不是新阶段，不得出现 P05-S6。
不得宣布任何阶段完成或签收，不写签收建议。不修改 S4/，不修改 testing/d003/ 下任何已提交文件。
不做任何失败注入，不执行任何驱动，不写 M1b/M1c 运行器，不做 dry-run（这些属于续3b2）。
工作量不是停止理由。任何停下（含技术停止）都必须做 end 门禁和记录提交；只有身份或完整性门禁不通过时才不提交。
"没有运行 start 门禁"属于执行遗漏，不是技术停止。

## 0. 开工与路径
- 先读 checkpoints/p05/STATE.md、AGENTS.md、PROJECT_ROADMAP.md 的 P05 行、本任务书。
  再读 briefs/P05_S4R8_BRIEF_M1a.md 的 §2（U139–U142）与 §7，以及 P05_S4R8_REPORT_M1a_CONT3a_AUDIT3.md。
- 基线：HEAD = abf3e420f5ba3600e079ecf213612bc1fc2a0aad，HEAD^ = 2a08aa5；HEAD:S4 = 6cff923a02baf19e01966b2339755cbf3a5deeef；
  a07b5ac:S4 = e124925f5b242486a913b813fa181664f665b048；判定器 sha256 = d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb。
- 用 write 把本任务书原文存为 checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3b1.md。
- 命名：新脚本 *_r8m1a5.*；新证据与小表 *_R8_M1a5*；证据目录 $EV = checkpoints/p05/evidence/p05-s4r8/m1a5
  （safe_run 的目录参数为 p05-s4r8/m1a5）；小表复制到 checkpoints/p05/registries/s4r8/M1a/；
  报告 checkpoints/p05/P05_S4R8_REPORT_M1a_CONT3b1.md。已有文件一律不覆盖（U17）。

## 1. 写入与命令规则（同 audit3 §七，以下为硬规则）
- 每个 shell 脚本第一行之后是标准首段：
  REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
  （不带 2>/dev/null；复制历史脚本时把 REPO 行换成这一段，diff 里这一行的变化属于预期）。
- 含写入的执行只能是 `sh testing/d003/safe_run.sh p05-s4r8/m1a5 -- <一个新脚本>`，不用 sh -c。Python 一律 python3 -I -B，不用 py_compile。
- 写入目标只能以 $EV/、$REPO/testing/d003/、$REPO/checkpoints/p05/ 开头。任何以 / 开头但不在仓库内的路径都不得出现，占位路径也不行。
- 内联命令不得含任何 > 字符（包括 2>&1）。只读内联只用于：git rev-parse / git status --short / git log -N --oneline / sha256sum <文件> / date -u，
  以及下面这一条临时区快照（开工、收尾各一次，原样使用）：
  date -u +%Y-%m-%dT%H:%M:%SZ; ls -A /tmp | wc -l; ls -A /tmp | sha256sum; date -u +%Y-%m-%dT%H:%M:%SZ
  其余核对写成脚本经 safe_run 运行；读文本用 read，搜索用 grep，找文件用 glob。
- 每个将要运行的脚本或数据文件，运行前用 grep 工具查以下正则，结果必须 0 行：
  /dev/null|DEVNULL|devnull|<<-?\s*['"]?[A-Za-z_]|sed -i|python3 -c|cat >|tee |rm -rf|(^|[^V])/tmp
  用 prerun_log_r8m1.sh 记录命中数与文件 sha256。没运行过的草稿查出问题后改正，不算违规（违规以实际执行为准）。
- ERRATA、RULINGS、报告正文写临时区时用"根目录临时区"，不写字面量。
- 不做拒绝性测试、反例测试或沙箱探测；不用 fsck/gc/prune/stash/checkout/switch/reset/clean；不删除任何已有文件。

## 2. 第一步：门禁（任何追加或运行之前）
2.1 先用 write 写两个允许列表数据文件，之后不得再修改（需要改就停下报告）：
  - testing/d003/stage_s4r8/gate_allow_r8m1a5_start.txt：恰好允许
    `?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3b1.md`、
    `?? testing/d003/stage_s4r8/gate12_r8m1a5.sh`、
    `?? testing/d003/stage_s4r8/gate_allow_r8m1a5_start.txt`、
    `?? testing/d003/stage_s4r8/gate_allow_r8m1a5_end.txt`。
  - testing/d003/stage_s4r8/gate_allow_r8m1a5_end.txt：在 start 允许项之外，再允许
    ` M checkpoints/p05/STATE.md`、` M checkpoints/p05/registries/RULINGS.tsv`、` M checkpoints/p05/registries/s4r8/ERRATA_8.txt`、
    `?? checkpoints/p05/P05_S4R8_REPORT_M1a_CONT3b1.md`、
    以及两条通配：`?? testing/d003/stage_s4r8/*r8m1a5*`、`?? checkpoints/p05/registries/s4r8/M1a/*M1a5*`。
    除此之外不允许任何项；不允许" M"出现在 testing/d003/ 下。
2.2 新增 testing/d003/stage_s4r8/gate12_r8m1a5.sh，以 gate11_r8m1a4audit3.sh 为蓝本（gate11 不改）：
  - 基线 HEAD = abf3e42…、HEAD^ = 2a08aa5；输出名 GATE_R8_M1a5_<名>.txt；
  - 派生复核名 S4R7_RECHECK_GATE_R8_M1A4_M1A5_<名大写>.tsv，必须匹配 ^S4R7_RECHECK_GATE_R8_M1A4_[A-Z0-9_]+\.tsv$，且不存在；
  - start 与 end 都只读上面两个允许列表文件，并把它们的 sha256 记成 RECORD；end 校验这两个 sha256 与 start 记录的相同；
  - *_HEAD_BLOB_EQ_WORKTREE 只在 start 检查；end 对 RULINGS.tsv、ERRATA_8.txt 用前缀与不截断检查；
  - end 的所有开工值从 START_FILE 读取，不通过位置参数传入；end 不检查 HEAD^ 以外的提交信息（end 在提交前运行）。
2.3 先运行 start（GATE_R8_M1a5_START.txt），FAILS=0 才能继续。FAILS 不为 0 时：只有门禁脚本自身缺陷才可以修正后以 _R2 重跑（原文件保留，在表二披露）；
  其余情况停下报告。

## 3. 裁决记录（start 通过后追加到 RULINGS.tsv：每行 5 列、4 个 TAB，来源写"R8 M1a 续3b1 任务书 §3"，状态写"生效"）
- U192：接受 audit3（abf3e42）与阶段 B 存量提交 2a08aa5 的结果及全部披露；续3a 审核修正到此关闭；准许进入续3b。
  这只是续3b 的进入许可，不是 M1a 或 P05-S4 的签收。表一中的 `> /tmp_none_x` 按执行偏离接受，不追认为合规。
- U193：对 58 个 PLANCALL 点（U189 中的 EVIDENCE_INSUFFICIENT），K 与 M 取请求文本 plancall:K:M，
  并与 M3_F2_STATE_R6c_pass1/pass2.tsv 的 env_as_run 中 S4FMM_INJECT 的值交叉核对；两遍都相等才记 K_FROM_REQUEST_AGREED，
  否则记 EVIDENCE_INSUFFICIENT，并按停止条件处理。
- U194：audit3 的记录瑕疵按 §4 修正：E8-68 缺失；end 规则在 start 后放宽；报告未附提交后 git 记录；STATE 超过一页、开放问题第 58 行去向已过时。
- U195：续3b 分两轮。续3b1 = 本轮（瑕疵修正与正式预注册）；续3b2 = M1b/M1c 运行器（只用 --dry）、dry-run（不执行驱动）、M1a 总报告与收尾。
- U196：预注册中 callseq_status 的规则：
  (a) 行映射到 REQUEST_TARGETS_R8_M1a4AUDIT3.tsv 的 unit_id，再映射到 CALLSEQ_F2_F3_R8_M1a4_R2.tsv 中的配对；配对为 IDENTICAL 时记 IDENTICAL；
  (b) CONTROL_NA 行记 N/A_CONTROL；(c) EXPECTED_NOT_REACHED 行记 IDENTICAL_NOT_REACHED，期望仍为 NOT_REACHED_AS_EXPECTED（U139(d)）；
  (d) S3R4 新增行按 ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT2_RUN2.tsv 记 MAPPING_VERIFIED_STRICT，
      其中 A-U96 三行记 NOT_VERIFIED_K0_VERIFY_BY_INJECTION（U191）；
  (e) 其他情况（找不到 unit 或配对、配对不是 IDENTICAL）一律停止，不得自行重映射（U140）。
- U197：R7 中 source_tree = F 的行，在 R8 中对应 F3 行。F3 行的期望按 U139(b) 取 R7 中 F2 两遍一致的 class 与 rc1；不使用 R7 的 F 结果作期望。
  F 树本身不再运行。
同时在 ERRATA_8.txt 追加 E8-68、E8-69（只追加，追加前先做前缀校验）：
- E8-68：补写 STATE 引用的 E8-68 正文，内容是 audit2 阶段 B 记录提交脚本清单缺少自身，由 audit3 补做提交 2a08aa5；
- E8-69：audit3 的 gate11 end 规则在 start 后放宽，已披露；本轮起允许列表改为开工前冻结的数据文件（U194）。
  另外，audit3 报告 §12 所说的提交后 git 记录并不存在；本轮用脚本把 `git log -3 --oneline` 与 status 写入 $EV/FINAL_GIT_R8_M1a4AUDIT3_POST.txt 补齐。
  旧报告不改。

## 4. STATE 压缩（用 edit）
- 只保留：当前位置表（当前轮次一格不超过 6 行）、关键数字表（每轮一行，每行不超过 3 行，历史细节改为链接到报告）、开放问题表、证据位置（只列最近三轮，其余写"见各轮报告"）。
- 开放问题第 58 行改为"已处置（U188–U191，U192 接受）"；新增一行"M1b/M1c 预注册：续3b1 已生成，dry-run 与运行器在续3b2"。
- 目标是 STATE 不超过 8 KB。被删的文字原样存入 checkpoints/p05/registries/s4r8/M1a/STATE_HISTORY_R8_M1a5.md（只追加，不改写原意）。

## 5. 正式预注册生成器 make_prereg_r8m1a5.py（新文件，只读输入）
- 输入只能是已提交的表，并写出每个输入的路径与 sha256：registries/s4r7/ 下 R7 M1/M2/M2_ADD_v3/M2_CTRL_SEAM/M3 的登记表、
  各组两遍 RESULTS（M1 run2，G1/G2a/G2c/CTRL_SEAM run7，G2b/G3/G4 run4，M3 的 M3_F2_RESULTS_R6c_STATE/SEAM），
  RESULTS_R7_M1_CTRL_REJUDGE_POSTHOC.tsv；registries/s3r4c2、s3r4c3 的 REGISTRY_S3R4C2_A、C3_A_CTRL、C3_B、C2_C_POLY；
  registries/s4r8/M1a/ 的 REQUEST_TARGETS_R8_M1a4AUDIT3.tsv、CALLSEQ_F2_F3_R8_M1a4_R2.tsv、ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT2_RUN2.tsv、
  DRIVERS_R8_M1a.tsv、DRIVERS_R8_M1a_F2_REUSED.tsv、K_SOURCE_G5F2_R8_M1a4AUDIT3.tsv。
- 输出（到 $EV/）：
  · REGISTRY_S4_PRE_R8_M1b.tsv：G7、G8、4.2、G2b、G3、G4、CTRL_SEAM、G2c、G1、G2a 每个点各两行（F2 基线行、F3 行），
    加 22 行 S3R4 新增（照原登记表的 F2 与 F3 行）和多边形 33 组合（F2 与 F3）；
  · REGISTRY_S4_PRE_R8_M1c.tsv：G5（177）、G6（25）、18 对照，F2 与 F3 各一套；期望照 REGISTRY_S4_PRE_R7_M3.tsv 中 F2 的判定，不变量 I1–I6，I7 写 DEFERRED。
  · 每行至少有这些列：group、point_id、tree（F2/F3）、driver_name、driver_sha256（取自驱动表）、env（由 matrix_r2.build_env 与 expected_env_independent_r7 推导，
    不读 ADD 的环境列，U75b）、expected_class、expected_rc1、expect_source（表:行）、callseq_status（U196）、k_source（U189/U193）、status=INFLUENCED。
  · 期望规则：U139(a)–(e)、U197。期望只能由脚本生成，不得手写。F2 两遍 class 或 rc1 不一致的点不得生成期望，记入停止表。
  · K_SOURCE_PLANCALL58_R8_M1a5.tsv（U193）。
  · PREREG_COUNTS_R8_M1a5.tsv：每组一行，列为组、R7 点数（从 R7 RESULTS 计）、预注册 F2 行数、F3 行数、OK/BAD。
  · PREREG_STOP_R8_M1a5.tsv：停止项（应只有表头）。
- 两份预注册写完后，立即用单独的脚本记录 sha256 与 UTC，写入 PREREG_RECORD_R8_M1a5.txt。之后只能新建 *_ERRATA*.txt，不改原文件。
- 生成器先在内存中做完全部校验，再写任何输出；任一校验失败，只写 PREREG_STOP 表。

## 6. 收尾（顺序固定）
1. 证据清单 $EV/SHA256SUMS.txt（覆盖本轮全部非二进制证据），并做 sha256sum -c 核对。
2. 复制小表到 registries/s4r8/M1a/（两份预注册、PREREG_COUNTS、PREREG_RECORD、PREREG_STOP、K_SOURCE_PLANCALL58、门禁文件、
   FINAL_GIT_R8_M1a4AUDIT3_POST.txt、STATE_HISTORY），写 SHA256SUMS_M1a5.txt，并逐个与原件比对 sha256。
3. STATE 按 §4 更新。当前轮次只能写两种之一："续3b1 预注册已生成，下一步续3b2（待用户审核）"，或"续3b1 未完成（停止点：…）"。
4. 报告 P05_S4R8_REPORT_M1a_CONT3b1.md 依次写：门禁；U192–U197；E8-68、E8-69；STATE 压缩；预注册各组计数；callseq_status 分布；
   K 来源；停止项；违规两张表；内联命令自查（逐条列出 UTC 与原文）；待用户裁决（没有就写"无"）。
   每项只写"完成""未完成（原因）""不可行（依据）"之一。
5. 运行 gate12 end（GATE_R8_M1a5_END.txt），FAILS=0。
6. 提交脚本 commit_rec_r8m1a5.sh：逐路径 git add --（清单必须包含提交脚本自己），不用 -A 或 `.`；
   提交信息为：P05-S4 R8 M1a cont3b1: audit3 accepted (U192), STATE compacted, E8-68/E8-69, M1b/M1c formal pre-registration and counts (no runs); awaiting user review
   提交后用脚本把 git log -3 --oneline 与 git status --short 写入 $EV/FINAL_GIT_R8_M1a5.txt，在对话中原样贴出。status 应为空。
   提交后不再修改任何已跟踪文件。

## 7. 停止条件（只有这些）
身份或完整性不符；start 门禁失败（门禁自身缺陷除外，见 2.3）；需要修改允许列表、S4/ 或已提交的历史装置；
PREREG_COUNTS 中出现 BAD；F2 两遍不一致；U196(e) 的情况；U193 中出现不一致。
命中停止条件时：先登记，继续做不依赖该项的步骤，然后照常走第 6 节收尾（预注册不完整时不写 PREREG_RECORD）。

## 8. 最终回复
纯 Markdown，不超过 40 行，不含 HTML 标签。结尾只写"本轮已完成 R8 M1a 续3b1 范围，等待用户审核"或"本轮未完成 R8 M1a 续3b1 范围（停止点：…），等待用户审核"。
