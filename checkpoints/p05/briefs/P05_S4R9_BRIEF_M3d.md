# P05-S4 R9 M3d 任务书（轮次标识 r9m3d）

## 0. 身份与边界
- 你是 P05-S4 R9 的执行者。开工先读仓库根 AGENTS.md、checkpoints/p05/STATE.md、PROJECT_ROADMAP.md 的 P05 行，再读本任务书。把本任务书原文保存为 checkpoints/p05/briefs/P05_S4R9_BRIEF_M3d.md（经 safe_run），随记录提交 (i) 一起提交。
- 本轮目的：把 P05-S3/P05-S4 的签收材料修正到彼此一致。① 把 §2 裁决登记入 RULINGS；② 复核 §3 的规划者 P 项；③ 生成修正版的最终红点台账、S5 移交清单（去重）、就绪审计和签收草稿 v2。
- 全程只读复核，不运行 S4 的任何程序：不跑 make、make test、E2E、d003 矩阵、gdb，不构建。
- 不允许修改：S4/、判定器、任何历史装置、任何已提交文件（包括 M3c 的全部产物：P05_S3_S4_SIGNOFF_DRAFT.md、registries/s4r9/M3c/*、M3c 报告、stage_s4r9 下已提交脚本）。修正一律写成新文件（文件名带 R9M3D 或 _v2）。RULINGS.tsv、ERRATA_9.txt 只能以“旧文件 + 新行”的方式追加，追加前断言前缀 sha。
- 不得宣布任何阶段完成或签收。签收草稿 v2 的标题和首行必须写“草稿，非签收；签收只由用户在对话中给出”。
- 开工门禁（任一不符就停下报告）：
  - HEAD = c4f67071e80f8dd573f3653c04250708e7339b7f；HEAD:S4 = 589e15eb11fcb04e031b524f25a443e7921946cf；判定器 sha256 = d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb；git status --short 为空；/tmp 顶层快照（条目数与 sha256）写入门禁文件。
  - RULINGS.tsv：sha 以 443d8a38 开头（142281 字节，最大编号 U350）；ERRATA_9.txt：sha 以 9bd2933d 开头（56754 字节，最后 E9-66，共 66 条）。完整 sha 由脚本从 HEAD 现场读出后写进门禁文件，前缀用来断言。
  - registries/s4r9/M3c/SHA256SUMS.txt 全部 OK；m3c 证据目录的 SHA256SUMS.txt 全部 OK；历史清单（s3r5、M0、M1、M1R2、M1R3、M1R4、M2、M2b、M2c、M3a、M3b、M3c）全部 OK。项数先由脚本数出，再断言。

## 1. 写入与执行纪律（沿用 M3c；带【新】的是本轮新增）
- 每条含写入的命令开头：REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m3d; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"。每条写入单独经 sh testing/d003/safe_run.sh p05-s4r9/m3d -- <命令> 运行；不得用外层 && 串联多个写入。
- 写入目标只能是 $EV/、$REPO/testing/d003/stage_s4r9/（新文件名带 r9m3d）、$REPO/checkpoints/p05/。不得出现 /tmp 或仓库外的写入目标，包括只读侦察命令里的 mktemp。不得用 2>/dev/null。不做沙箱探测或拒绝性测试。长输出带 head/tail。
- 所有读表脚本按列名取值，表头缺列就报错退出。门禁、closeout、report_check 中出现的脚本名一律从 FROZEN_SCRIPTS_R9M3D.tsv 读取。
- 【新】收尾链的顺序固定为：closeout → report_check → copy_registries → events → progress 最后一行 → sha_sums → end 门禁。sha_sums 必须是对 $EV 的最后一次写入。end 门禁的输出写到 $EV/gate/ 子目录，并且不纳入 SHA256SUMS。试跑期就要断言：sha_sums 之后 $EV 下没有任何文件的 mtime 更新（门禁文件自身除外）。
- 【新】计数脚本先去重：同一 id 或同一移交项只算一次。每张输出表尾部写“# UNIQUE=… ROWS=…”。
- run_code 与 tools.bash 的长任务都传 timeoutMs（≤600000）。

## 2. 用户裁决（本任务书下发即生效；以“旧文件 + 新行”追加到 RULINGS.tsv，5 列）
- U351：M3c 的 U343–U350 与 E9-58–E9-66 落账生效。
- U352：M3c 的 S-B 独立复核结果（DIFFS=0、E2E_OK=25、CONTROL_OK=17、阳性对照 16/16、REVERIFY FAILS=0）接受。U345 的关闭条件成立，RP-R6d-15 按 U345 的范围声明关闭。
- U353：M3c end 门禁 EVIDENCE_SHA256SUMS_OK 的 FAIL 判为执行顺序错误：sha_sums 之后又写了一行 progress。结果表未受影响。接受“删除误加行、逐项校验 16/16 一致”的处理，只登记勘误，不重跑。M3c 表二的三条顺序偏差同样接受，只登记勘误。
- U354：RP-R6d-14（其他层失败变体）不再转 S5。依据：U245 定义了 P0/P2/PP1/PP2 四种布局，R9 M2 在 F4 上正式两遍测了 M2-05 共 8 点（4 个注入点、4 个对照），全部 MATCH；另有补测点 M2-05-P0-F4-C，也是 MATCH。范围声明：仅限这四种布局、F4、驱动 driver_r8m2a2_layers。U20 的“推迟”由本裁决结束。前提：§3 P-1 复核属实；不属实时，本裁决不生效，并写入“需用户裁决”。
- U355：S5 移交清单以去重后的唯一项为准。最终红点台账里每个 TRANSFERRED_S5 的 id 都必须出现在移交清单中，反过来移交清单的每一项也必须能对应到台账 id 或 STATE 行，不能有只出现在一边的项。RP-R6d-3（no-TWICE 路径，OUT_OF_SCOPE_D003）和 RP-R6d-7（D016，B 侧 rc 来源未追踪）按台账现状转 S5，补进移交清单。
- U356：S1/S2 签收范围声明第 (2) 条（七处 info=NULL 的 LinearSolve 修前 seam 移交 P05-S4）以 M1R3 中 G6 组 R4-CL01..CL04、R4-PJ01、R4-PN01、R4-PV01（F4）的判定作为闭合证据。前提：§3 P-5 复核为 7/7 MATCH。签收草稿 v2 要单列一节写明这项移交已闭合，并注明 F4 上族 B 原有的 info=NULL 锚点已不存在（P05_S4R4_REPORT.md §2a），所以这 7 点测的是修复后的 &solve_info 路径。
- U357：就绪审计重算时，每一行的“裁决号”必须是 RULINGS.tsv 中真实存在的 U 编号，或者写 “-（事实项）”，不得写“见 STATE 行”。RP-R6d-15 那行改用 U345/U352。
- U358：M3c 已提交的产物不改；M3d 的修正版作为签收前的唯一现行版本。STATE 的开放问题表要同步反映 U354 与 U356。

## 3. 规划者 P 项（逐条用脚本复核，写“属实”或“规划者事实有误”并附实际值。行号和计数一律由脚本算出，不得照抄本任务书。结果写 AUDIT_R9M3C_R9M3D.tsv；属实的项各登记一条勘误，从 E9-67 起编号）
- P-1：registries/s4r9/M3c/RED_POINTS_LEDGER_FINAL_R9M3C.tsv 中 RP-R6d-14 的状态是 TRANSFERRED_S5，依据 U20。但 registries/s4r9/M2/VERDICT_R9.tsv 中 point_id 以 M2-05 开头的行（含 M2-05-CTRL 与 -C）判定全部为 MATCH。脚本要输出这些行的 id 清单与计数，并核对 U245 的布局定义与 RP-R6d-14 的位置描述（“two layers with a pattern; pattern layer not at position 1”）是否对应。
- P-2：S5_HANDOFF_R9M3C.tsv 共 10 个数据行，按规范化后的项名去重只剩 5 项。台账中 TRANSFERRED_S5 的 id 有 7 个（RP-R6d-3、-6、-7、-14、-16、-17、-18），其中 RP-R6d-3、RP-R6d-7 在移交表里没有对应项。
- P-3：READINESS_P05_S3S4_R9M3C.tsv 第①条写“红点行=27”，而台账唯一 id 数是 26。要找出多算的那 1 行（比如是否把表头算进去了），只读源码，给出脚本文件名与行号。
- P-4：P05_S3_S4_SIGNOFF_DRAFT.md 的“转入 S5 的项”有 10 条，含重复，并且缺 RP-R6d-3、RP-R6d-7。
- P-5：M1R3 判定表中 G6 组的 R4-CL01..04、R4-PJ01、R4-PN01、R4-PV01（F4）共 7 点，判定为 MATCH。脚本要列出 driver_name 与两遍类别，并核对 P05_S1_S2_SIGNOFF.md §2 第 (2) 条的原文。签收草稿 v1 中没有说明这项移交已闭合。
- P-6：READINESS 中 RP-R6d-15 行的 state 仍是“…待用户审核”的旧措辞；26 行里裁决列写“见 STATE 行”的行数需要数出来。

## 4. 工作项
### S-A 裁决与勘误
1. append_rulings_r9m3d.py 追加 U351–U358（U354、U356 的状态按 P-1、P-5 的复核结果写成“生效”或“未生效（前提不成立）”）。
2. audit_r9m3c_r9m3d.py 复核 P-1…P-6，写 AUDIT_R9M3C_R9M3D.tsv。
3. append_errata_r9m3d.py 从 E9-67 起追加勘误：每个属实的 P 项一条，U353 一条。

### S-B 修正版材料（只读输入，只新建文件）
1. red_ledger_final_r9m3d.py：以 M3c 台账为输入，应用 U352/U354/U355，输出 RED_POINTS_LEDGER_FINAL_R9M3D.tsv。每个被改动的 id 在文件尾列出“旧状态→新状态 | 依据裁决”。
2. s5_handoff_r9m3d.py：输出去重后的 S5_HANDOFF_R9M3D.tsv，列为 item_id、规范化名称、范围说明、来源裁决、对应台账 id、对应 STATE 行。双向核对，任一方向有孤项就报错退出。
3. readiness_r9m3d.py：重算三组判据（P05 验收三条、“无可做”七条、STATE §3 每行），输出 READINESS_P05_S3S4_R9M3D.tsv，并满足 U357。其中第①条的红点数必须等于新台账的唯一 id 数。
4. 写 checkpoints/p05/P05_S3_S4_SIGNOFF_DRAFT_v2.md，结构沿用 v1，另外：
   - P05-S3 一节补上：806/415/RP-S3R4-1、RNV1、K-1（U274/U281 的范围声明）、S3-4b（U29）、其他层失败变体（U354）。
   - P05-S4 一节新增“S1/S2 签收移交项的闭合”小节（U356）。
   - “转入 S5 的项”只列去重后的唯一项，每项注明来源裁决。
   - 末尾写“与 v1 的差异”表，逐条对应 P-1…P-6。
   - READINESS 中如有 GAP，原样列出。
5. 阳性对照（落盘在 $EV/posctrl/，调用正式脚本，禁止常量自证）：s5_handoff 对一份删掉 RP-R6d-7 的台账副本必须报错；readiness 对一份多出表头式行的台账副本，计数必须仍为唯一 id 数；report_check 对一份故意写错派生句的报告副本必须判 FAIL。

## 5. 顺序（严格执行，不得前移）
start 门禁 → S-A → S-B 试跑（含 posctrl）→ 收尾链试跑（输出到 $EV/shakedown/，顺序见 §1）→ 冻结清单 FROZEN_SCRIPTS_R9M3D.tsv → start 前缀复核 → 记录提交 (i) → 冻结期：red_ledger、s5_handoff、readiness 各跑一次，收尾链各跑一次 → 收尾提交 (ii)。冻结期不修脚本、不重跑；门禁的 FAIL 照实写入附录 B。出现顺序偏差就立即停下，写入表二。

## 6. 报告 checkpoints/p05/P05_S4R9_M3d_REPORT.md
结构依次为：门禁 → P 项复核 → 裁决与勘误 → 修正版台账/移交/就绪（各列唯一计数和变更清单）→ 签收草稿 v2 摘要 → 事件两张表 → 需用户裁决（与对话摘要逐条一致）→ 交付物清单（条目不加反引号，项数与 SHA256SUMS 一致）→ 附录 A（closeout 由表计算生成）→ 附录 B（end 门禁）。表格内不得有空行。STATE 更新后不超过 8192 字节。结尾写“本轮已完成/未完成 R9 M3d 范围，等待用户审核”，并附 git log -1 与 git status --short。

## 7. 收尾（AGENTS.md §7）
- 小表复制到 checkpoints/p05/registries/s4r9/M3d/，写 SHA256SUMS.txt，逐项比对原件。
- $EV/SHA256SUMS.txt 覆盖全部非二进制证据，但 $EV/gate/ 除外。
- 提交范围限 checkpoints/p05/ 与 testing/d003/stage_s4r9/；提交信息末尾写 awaiting user review。

## 8. 硬停止
只有以下情况停下报告：开工门禁不符；发现 S4/、判定器、历史装置或已提交文件被改动；出现无法解释的越界写入；P-1 或 P-5 复核不属实（此时 U354/U356 不生效，照实写入“需用户裁决”，继续完成其余各项，但签收草稿 v2 中相应项仍写为转 S5 或未闭合）。合法的中间产物使工作区非空，不构成停止理由。
