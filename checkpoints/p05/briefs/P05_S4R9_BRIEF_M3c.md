# P05-S4 R9 M3c 任务书（轮次标识 r9m3c）

## 0. 身份与边界
- 你是 P05-S4 R9 的执行者。开工先读仓库根 AGENTS.md、checkpoints/p05/STATE.md、PROJECT_ROADMAP.md 的 P05 行，再读本任务书。把本任务书原文保存为 checkpoints/p05/briefs/P05_S4R9_BRIEF_M3c.md（经 safe_run），随记录提交 (i) 一起提交。
- 本轮目的：① 把 §2 裁决与 §3 规划者 L 项登记成勘误；② 只读独立复核 M3b 的正式结果（不重跑任何东西）；③ 做 P05-S3/P05-S4 的签收就绪审计，写最终红点台账与签收范围声明草稿。
- 本轮全程只读复核，不运行 S4 的任何程序：不跑 make、make test，不跑 E2E，不跑 d003 矩阵，不跑 gdb，不构建。
- 不允许：修改 S4/、判定器 judge_d003.py、任何历史装置（matrix_*.py、run_*.sh、safe_run.sh、summarize_r6.py、src/、seam/）、任何已提交文件（包括 M3b 报告、registries/s4r9/M3b/ 全部文件、所有 stage 脚本、旧台账）。m3b 及更早的证据目录只读。只追加文件（RULINGS.tsv、ERRATA_9.txt）用"旧文件 + 新行"方式追加，追加前断言前缀 sha。
- 不得宣布任何阶段完成或签收。签收草稿文件的标题和首行必须写"草稿，非签收；签收只由用户在对话中给出"。
- 开工门禁（任一不符就停下报告）：
  - HEAD = 01fd3c0e4cf436aef5780486c8b8327c25849713；HEAD:S4 = 589e15eb11fcb04e031b524f25a443e7921946cf；判定器 sha256 = d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb；git status --short 为空；/tmp 顶层快照（条目数与 sha256）写入门禁文件。
  - RULINGS.tsv sha = 4bcebe609f7c280d1083f69fd117719ffa98fa8dc7793130e0168f0e36c9631a（139934 字节，最大 U342）；ERRATA_9.txt sha = 2d32e4f1d8e584e65c7122aa6e5efd710b32991ddd5cadac4ea5cec979412716（51809 字节，最后 E9-57，共 57 条）；STATE.md sha = a6aa2c49ab1a0a15b561b5ac836d97ff4951cc18fd91176b0454b43ff716d5b2（5534 字节）。
  - registries/s4r9/M3b/SHA256SUMS.txt sha = 4a802924ce529df402f79cfe721da9a3550a6293d2950fd637b5c42015e4dc59，18 项全部 OK；m3b 证据目录 SHA256SUMS.txt sha = da6ae764074b0e5f9227bf07f313b0e972cacbaf6d7b4b6bfc0fdbac95a4e118，全部 OK；M3b 报告 sha = 788417e8cc55fe836d0887fd69df295498a761d53a631e485d9e820ed5e81467。
  - 历史清单（s3r5、M0、M2、M2b、M2c、M1、M1R2、M1R3、M1R4、M3a、M3b）全部 OK。项数先由脚本数出来，再断言。

## 1. 写入与执行纪律（沿用 M3b，【新】为本轮补充）
- 每条含写入的命令开头：REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m3c; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"。每条命令单独经 sh testing/d003/safe_run.sh p05-s4r9/m3c -- <命令> 运行。不得用外层 && 串联多个写入；每条写入各占一次 safe_run。
- 写入目标只能是 $EV/、$REPO/testing/d003/stage_s4r9/（新文件名带 r9m3c）、$REPO/checkpoints/p05/。不得出现 /tmp 或仓库外的任何写入目标；不得用 2>/dev/null；不做沙箱探测或拒绝性测试；长输出带 head/tail。
- 进度：每完成一个阶段，用固定小脚本 progress_r9m3c.py 向 $EV/PROGRESS_R9M3C.txt 追加一行。
- 【新】所有读表脚本一律按列名（表头）取值，禁止用固定下标；表头缺列直接报错退出。
- 【新】门禁、closeout、report_check 中出现的任何脚本名，都必须从 FROZEN_SCRIPTS_R9M3C.tsv 读取，不得写死。试跑期用 grep 断言：stage_s4r9 下所有 *_r9m3c*.py / *.sh 中，不得出现其他轮次的脚本名，也不得出现本轮脚本的非终版名（可读历史证据路径的情况除外，这类例外列入白名单文件）。
- 【新】report_check 除了核对数字，还要核对附录 A 的每一句派生文字：把每句里的判断词（全部 OK / 存在 FAIL / none / PASS 等）与源表重新计算的结果比对。这项检查在试跑期必须对一份故意写错的报告副本跑一次（落盘在 $EV/posctrl/report_check/），并判出 FAIL。
- 【新】本轮顺序严格按 §5 执行，不得前移任何步骤。若出现偏差，立即停下并写入表二，不得事后补登记。
- run_code 与 tools.bash 的长任务都要传 timeoutMs（不超过 600000）。

## 2. 用户裁决（本任务书下发即生效；以"旧文件 + 新行"追加到 RULINGS.tsv，5 列，追加前断言前缀 sha）
- U343：PREREG_E2E_R9M3B.tsv 的 42 点布点、nth（CF/FFT/KT/EXP=1，JONES/NV/VL=3）、容差 1e-12、Lua 批处理 exp_retry_same=NOT_APPLICABLE_PROCESS_EXIT 与 REPL 观测口径，认可。
- U344：U340 的 SEAM_ONLY 处理（LinearSolve A/B/B2/B2-buf、FMM 返回码族 E、分配 seam 家族 C、kottke_alloc:31 不出 E2E 点，以 M1/M2 覆盖行代替），接受。
- U345：M3b 正式两遍判定（E2E_OK 25、CONTROL_OK 17，其余类别 0，新红点 0）接受，条件是 §4 S-B 的独立复核结果一致。若一致，RP-R6d-15（Python/Lua 可见性）带范围声明关闭。范围声明如下：F4 上经 Python 与 Lua 公共 API 可达的 7 个点族（CF/FFT/KT/JONES/NV/VL，EXP 仅 Lua），注入 s4malloc/plan/exec 三种方式，检查失败可见、同对象重试（Python 全族；Lua 仅 REPL 的 cf/fft/kt/vl 四族）、新对象/新进程重试等于参考值；seam-only 族由 M1/M2 覆盖；不含 B 树行为。
- U346：M3b 表二的两处顺序偏差（S-C 先于 start 门禁；start_recheck 先于冻结清单）接受，只登记勘误。理由：预注册早于任何注入运行这一不变量，已由 end 门禁检查成立。
- U347：M3b end 门禁 EVIDENCE_SHA256SUMS_OK 的 FAIL 判为检查器缺陷（gate_check_r9m3b_v3.py 写死了 v1 脚本名），接受；由本轮 S-B 的只读复验代替（m3b 证据清单全部 OK）。M3b 门禁文件不修改。
- U348：M3b 报告附录 A 中"4 遍 × 2 段对账 存在 FAIL"一句是 closeout 脚本的列下标错误（取了 skipped 期望列，而不是 ok 列），与事实相反。事实以 MAKETEST_VERDICT_R9M3B.tsv 的 8/8 OK 为准；报告不改，只登记勘误。
- U349：不另立 M3a 门禁更正件；U337 加 E9-57 已足够。
- U350：RP-R8-M2c-1/1b 已由 U304 关闭。旧台账不改，在本轮最终红点台账中按 U304 记为已关闭。

## 3. 规划者 L 项（逐条复核，写"属实"或"规划者事实有误"。行号必须由脚本从原文件算出，不得照抄本任务书的行号；本任务书给的行号若与脚本结果不符，写"规划者事实有误"并给出实际行号。结果写 AUDIT_R9M3B_R9M3C.tsv，属实的项登记为 E9-58 起的勘误）
- L-1：P05_S4R9_M3b_REPORT.md 附录 A 的 make test 那一句写"存在 FAIL"，而列出的 4 行最后一列都是 OK。成因：closeout_report_state_r9m3b.py 中 recon_bad 以 r[6] != "OK" 判定，而 r[6] 是 skipped 期望值列，OK 在 r[7]。另外，report_check_r9m3b.py 没有检出这句（REPORT_CHECK_R9M3B.txt 为 FAILS=0）。
- L-2：gate_check_r9m3b_v3.py 的 EVIDENCE_SHA256SUMS 检查写死了 "testing/d003/stage_s4r9/sha_sums_r9m3b.py"，与 FROZEN 清单中的 sha_sums_r9m3b_v2.py 不一致。这与 U337 要求的"调用计数从 FROZEN 清单读取实际文件名"相违背。
- L-3：M3b 报告 §9 表格在第 5 行之前、§12.2 表格在第 8 行之前各有一个空行，Markdown 表格因此被截断。
- L-4：执行者对话摘要中"需用户裁决"的第 5 项（end 门禁检查器缺陷）与报告 §13 的第 5 项（是否另立 M3a 门禁更正件）不一致；end 门禁缺陷只出现在附录 B 中。
- L-5：LEDGER_CHECK_R9M3B.tsv 把 RP-R8-M2c-1/1b 的去向写成"待用户裁决是否关闭"，与 U304 的关闭裁决不一致；并且把 RP-R8-M2c-1b 判为"STATE 中无对应行"，但 STATE 用的是合并行"RP-R8-M2c-1/1b"。
- L-6（范围事实，不是缺陷）：PREREG_E2E_R9M3B.tsv 中 lua_repl 只有 cf/fft/kt/vl 四个注入点与四个对照，jones/nv/exp 没有 REPL 点。用脚本列出这三族在每个前端各有多少点。

## 4. 工作项
### S-A 裁决与勘误
1. append_rulings_r9m3c.py 追加 U343–U350。
2. audit_r9m3b_r9m3c.py 复核 L-1…L-6，写 AUDIT_R9M3B_R9M3C.tsv。
3. append_errata_r9m3c.py 追加 E9-58 起的勘误：每个属实的 L 项一条，再加 U346、U347、U348 各一条。写入前断言审计表对应项都为"属实"；有"规划者事实有误"的项，按实际事实写。

### S-B M3b 结果的独立只读复核（新实现，不得 import 或调用任何 r9m3b 脚本）
1. rejudge_e2e_r9m3c.py：直接读 m3b/runs/pass1/points/*.json 与 pass2，按 PREREG_E2E_R9M3B.tsv 与 CALIB_E2E_R9M3B.tsv 独立重算每点类别，并输出逐点事实列：命中数（必须为 1，对照为 0）、HIT 行中的序号与 size 是否等于 CALIB、错误文本是否匹配 exp_visible、同对象/新对象/新进程重试值与参考值的最大相对误差（≤1e-12）、rc。输出 REJUDGE_E2E_R9M3C.tsv，并与 E2E_VERDICT_R9M3B.tsv 逐点比对，写 0 或 N 处差异。
2. 阳性对照：在 $EV/posctrl/rejudge/ 落盘篡改副本，每个前端至少覆盖 API_SILENT、RETRY_DIFF、HIT_OFF_TARGET、INVALID、CONTROL_BAD 各 1 例，加 FLAKY 1 例（两个 run 文件），调用正式脚本判出。禁止常量自证。
3. reverify_sums_r9m3c.py：对 m3b 证据目录与 registries/s4r9/M3b 的 SHA256SUMS 做逐项只读复验，并按列名从 MAKETEST_VERDICT_R9M3B.tsv 重算 8 行 reconcile 的 ok 列。结果写 REVERIFY_R9M3B_R9M3C.tsv。
4. 若 S-B 有任何差异：不修正、不重跑，照实写入报告的"需用户裁决"，U345 的关闭视为未生效。

### S-C 签收就绪审计（只读）
1. readiness_r9m3c.py 生成 READINESS_P05_S3S4_R9M3C.tsv，逐条列出以下三组判据，每条写：证据文件路径（registries 下）、由脚本重算的数字、对应裁决号、状态（MET / GAP / TRANSFERRED_S5 / CLOSED_BY_RULING）：
   - PROJECT_ROADMAP.md 的 P05 验收三条：每个受影响的 prepare/execute 点有正负对照；失败后模式/缓存不安装；Python/Lua 可见失败、恢复重试正确。
   - "无可做"七条：①范围内红点全部修复并完成修后回归；②开放项完成或经裁决转出；③无待跑运行；④STATE/registries/报告一致；⑤make test 相对基线无新增失败；⑥预注册矩阵无 MISMATCH/FLAKY/VALUE_DRIFT；⑦Python/Lua 正常与失败→可见报错→重试恢复。
   - STATE.md §3 开放问题表的每一行。
2. red_ledger_final_r9m3c.py 生成 RED_POINTS_LEDGER_FINAL_R9M3C.tsv：汇总历来所有已提交的红点台账（由脚本 glob registries 下 RED_POINTS_LEDGER*，先列出文件清单与行数），每个红点一行，列：id、首次出现轮次、位置、修复提交/树、修后验证证据、关闭裁决号、当前状态、去向。去重规则与冲突（同一 id 在不同台账状态不同）单独列在文件尾部；冲突以最新裁决为准，并在报告中列出。
3. 写 checkpoints/p05/P05_S3_S4_SIGNOFF_DRAFT.md（标题与首行写"草稿，非签收"）：P05-S3、P05-S4 各一节，内容为范围声明草稿（已验证内容、证据入口、不包含内容、转入 S5 的项）。READINESS 中任何 GAP 必须原样列出，不得隐去。
4. S5 移交清单 S5_HANDOFF_R9M3C.tsv：列出全部 TRANSFERRED_S5 项及其来源裁决。

## 5. 顺序（严格执行，不得前移）
start 门禁 → S-A → S-B（试跑：posctrl 加对 M3b 结果的一次试跑）→ S-C 草稿 → 收尾脚本试跑全链（closeout → report_check（含对故意写错副本的阳性对照）→ copy_registries → events → sha_sums → end 门禁，以 --shakedown 输出到 $EV/shakedown/）→ 冻结清单 FROZEN_SCRIPTS_R9M3C.tsv → start 前缀复核 → 记录提交 (i) → 冻结期：rejudge formal 一次、reverify 一次、readiness 一次、red_ledger_final 一次、收尾链各一次 → 收尾提交 (ii)。冻结期不修脚本、不重跑；门禁 FAIL 照实写入附录 B。

## 6. 报告 checkpoints/p05/P05_S4R9_M3c_REPORT.md
结构依次为：门禁 → L 项复核 → 裁决与勘误 → M3b 独立复核（逐点差异数、阳性对照）→ 签收就绪审计（MET/GAP/TRANSFERRED 计数与 GAP 明细）→ 最终红点台账摘要（含冲突）→ 事件两张表 → 需用户裁决（与对话摘要逐条一致）→ 交付物清单（条目不加反引号，项数与 SHA256SUMS 一致）→ 附录 A（closeout 由表计算生成）→ 附录 B（end 门禁）。表格内不得有空行。结尾写"本轮已完成/未完成 R9 M3c 范围，等待用户审核"，附 git log -1 与 git status --short。STATE 更新后不超过 8192 字节，并在开放问题表中反映 U345/U350 的结果。

## 7. 收尾（AGENTS.md §7）
- 小表复制到 checkpoints/p05/registries/s4r9/M3c/，并写 SHA256SUMS.txt，逐项比对原件。
- $EV/SHA256SUMS.txt 覆盖全部非二进制证据；门禁生成的 ALL_STATUS_* 快照不纳入。
- 提交范围限 checkpoints/p05/ 与 testing/d003/stage_s4r9/；提交信息末尾写 awaiting user review。

## 8. 硬停止
只有以下情况停下报告：开工门禁不符；发现 S4/、判定器、历史装置或已提交文件被改动；出现无法解释的越界写入；S-B 独立复核与 M3b 判定出现差异（记录后停在冻结期之前，不继续 S-C 的冻结运行）。合法中间产物使工作区非空，不构成停止理由。