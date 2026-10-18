# P05-S4 R9 M3e 任务书（轮次标识 r9m3e）——完整版，取代此前下发的 M3e 任务书

## 0a. 自检（开工前第一件事，零写入）
- 用只读脚本检查下方签收块（BEGIN SIGNOFF 与 END SIGNOFF 之间）：若为空、含 "<<<" 或 ">>>" 或 "【在此填写" 字样、或不含“签收”二字；或签收日期不是 YYYY-MM-DD 格式，立即停止，不调用 safe_run，报告“任务书未填签收原文”。
- 本任务书文件 checkpoints/p05/briefs/P05_S4R9_BRIEF_M3e.md 由你在开工后经 safe_run 保存；开工前不存在属正常，不构成停止条件。
- 上一次 M3e 尝试在门禁处停止、零写入，不构成本轮的历史产物；本轮仍用轮次标识 r9m3e，证据目录 p05-s4r9/m3e 开工时应不存在（test -e 断言）。

签收原文（由用户给出，逐字照录；执行者不得改写、补充、解释）：
----BEGIN SIGNOFF----
同意签收 P05-S3、P05-S4。范围声明：(a) 验证对象为冻结被测树 F4（05097a7，S4/ 树 589e15e…），不含 B 树行为，B 列观察不是修复证据；(b) M3d 修正版为签收前唯一现行版本（红点唯一 id 26、S5 移交 7 项、READINESS 28 行 GAP=0、签收草稿 v2），M3c 产物保留为历史，v1→v2 的 P-1…P-6 不逐条再确认；(c) 其他层失败变体（RP-R6d-14）只覆盖 P0/P2/PP1/PP2 四种布局、F4、driver_r8m2a2_layers（U354）；(d) S1/S2 范围声明第 (2) 条按 U356 由裁决闭合，测的是修复后的 &solve_info 路径，修前 seam 本身仍不可测；(e) seam-only 族不出 E2E 点，Lua REPL 只覆盖 cf/fft/kt/vl 四族；(f) 转 S5 的 7 项按 S5_HANDOFF_R9M3D 处理，其中 ES3R4-5/528/1164 与 U2 stage e 两项以 STATE 行对应；U354、U356 维持。
----END SIGNOFF----
签收日期：【2026-10-18】

## 0. 身份与边界
- 你是 P05-S4 R9 的执行者。开工先读仓库根 AGENTS.md、checkpoints/p05/STATE.md、PROJECT_ROADMAP.md 的 P05 行，再读本任务书。通过自检后，第一条写入是把本任务书原文经 safe_run 保存为 checkpoints/p05/briefs/P05_S4R9_BRIEF_M3e.md，随提交 (i) 一起提交。
- 本轮目的：把用户给出的 P05-S3、P05-S4 签收落账。只读复核加文档写入，不运行 S4 的任何程序：不跑 make、make test、E2E、d003 矩阵、gdb，不构建。
- 不允许修改：S4/、判定器、任何历史装置、任何已提交文件（含 M3c、M3d 全部产物、P05_S1_S2_SIGNOFF.md、P05_S3_S4_SIGNOFF_DRAFT*.md）。RULINGS.tsv、ERRATA_9.txt 只能以“旧文件 + 新行”的方式追加，追加前断言前缀 sha。
- 签收文件只记录签收块原文；执行者不得自行宣布任何阶段完成或签收，不得在签收文件中加入签收块以外的范围解释。

## 1. 开工门禁（任一不符就停下报告）
- HEAD = 37fbc0f2b9c48010b81ad220293fe6f3af5c02bd；HEAD:S4 = 589e15eb11fcb04e031b524f25a443e7921946cf；判定器 sha256 = d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb；git status --short 为空；/tmp 顶层快照（条目数与 sha256）写入门禁文件。
- RULINGS.tsv：sha 前缀 21ab76d2，145103 字节，最大编号 U358。ERRATA_9.txt：sha 前缀 d71543bb，62654 字节，最后 E9-73。STATE.md：sha 前缀 6eeb7559，6636 字节。完整 sha 由脚本从 HEAD 现场读出后写进门禁文件。
- registries/s4r9/M3d/SHA256SUMS.txt 全部 OK；m3d 证据目录 SHA256SUMS.txt 全部 OK；历史清单（s3r5、M0、M1、M1R2、M1R3、M1R4、M2、M2b、M2c、M3a、M3b、M3c、M3d）全部 OK。项数先由脚本数出再断言；校验时对每个清单显式传入其所在目录作为工作目录。
- 只读断言：仓库根下不存在 registries/ 目录（test -e）。

## 2. 写入纪律（沿用 M3d）
- 每条含写入的命令开头：REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m3e; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"。每条写入单独经 sh testing/d003/safe_run.sh p05-s4r9/m3e -- <命令> 运行，不用外层 && 串联多个写入。
- 写入目标只能是 $EV/、$REPO/testing/d003/stage_s4r9/（新文件名带 r9m3e）、$REPO/checkpoints/p05/。不得出现 /tmp 或仓库外写入目标；不得用 2>/dev/null；不做沙箱探测或拒绝性测试；长输出带 head/tail。耗时较长的只读搜索限定目录（如 checkpoints/p05/），并传 timeoutMs。
- 任何复制/写入脚本的目标目录先用 realpath 解析，断言以 $REPO/checkpoints/p05/、$REPO/testing/d003/stage_s4r9/ 或 $EV/ 开头再写入（M3d 曾因 DEST 多写一级 .. 写到仓库根）。
- 读表脚本按列名取值，缺列报错退出。收尾链顺序：closeout → report_check → copy_registries → events → progress 最后一行 → sha_sums → end 门禁；sha_sums 是对 $EV 的最后一次写入；end 门禁输出写 $EV/gate/，不纳入 SHA256SUMS。
- end 门禁中“已提交文件未改动”只对 BASE 已存在的文件判 M/D，本轮新增 A 文件不算改动；RULINGS.tsv、ERRATA_9.txt 用“BASE 内容为新文件前缀 + 仅追加”判定；STATE.md 允许修改。

## 3. 裁决登记（追加到 RULINGS.tsv，5 列，从 U359 起）
- U359：用户签收 P05-S3、P05-S4；内容列逐字引用签收块原文，来源列写“用户对话（签收日期）”。
- 签收块原文若对以下各点有明确表态，各登记一条 U 编号（U360 起，按下列顺序，只登记有表态的）：① M3d 修正版为签收前唯一现行版本；② v1→v2 差异 P-1…P-6 是否逐条确认；③ U354、U356 维持；④ 无台账 id 的 2 项（ES3R4-5/528/1164、U2 stage e）以 STATE 行对应。判断“是否有表态”只看签收块字面；没有表态的不登记，写入报告“需用户裁决”。

## 4. 勘误（追加到 ERRATA_9.txt，从 E9-74 起）
- E9-74：M3d end 门禁 M3C_AND_M3B_COMMITTED_FILES_UNCHANGED 的 FAIL 是检查器口径缺陷（把新增 A 文件算作改动）。用脚本给出 c4f6707..37fbc0f 的 name-status 计数（A、M、D 各多少），列出全部 M 文件，并核对 RULINGS.tsv、ERRATA_9.txt 是否为纯追加。
- E9-75：M3d copy_registries 的 DEST 多写一级 ..，误写仓库根 registries/；已删除并在正确位置重建。用脚本复核仓库根 registries/ 不存在、M3d 清单全部 OK。
- E9-76：S5_HANDOFF_R9M3D.tsv 中 S5-M3D-06 的 source_ruling 写为 OUT_OF_SCOPE_D003，不是 U 编号；应为 U5（E6-4，no-TWICE 路径不在范围内）。用脚本核对 RULINGS.tsv 的 U5 行与 registries/s4r6/ERRATA_6.txt 的 E6-4 原文。不改 M3d 文件；S5 开工以本勘误为准。
- E9-77：M3d 门禁检查器口径及路径问题由 M3e 的写入纪律修正（§2 后两条），只登记，不重跑 M3d。

## 5. 签收文件
- 新建 checkpoints/p05/P05_S3_S4_SIGNOFF.md，格式沿用 P05_S1_S2_SIGNOFF.md：§1 签收表（S1、S2 维持原记录；S3、S4 写“已由用户签收”，日期为签收块下方日期；S5 写“未开始”）；§2 范围声明：签收块原文逐字照录；§3 对后续阶段的含义：S5 接收 S5_HANDOFF_R9M3D.tsv 的 7 项（S5-M3D-06 的来源裁决按 E9-76）；§4 声明：本记录由执行者依据用户授权写入，执行者未自行宣布任何阶段完成；P05-S5 未开始、未签收。
- 只读断言：签收文件 §2 文本与本任务书 BEGIN/END 之间文本逐字相同（脚本比对，去掉首尾空行后比较）。

## 6. STATE 与收尾
- STATE.md：当前轮次改为 P05-S4 R9 M3e；阶段状态改为“S1、S2、S3、S4 已由用户确认（带范围声明，见签收文件）；S5 未开始”；开放问题表只保留转 S5 的 7 项（指向 S5_HANDOFF_R9M3D.tsv 与 E9-76），已关闭的行压缩成一行并链接到 P05_S3_S4_SIGNOFF.md。STATE 不超过 8192 字节。
- 小表（门禁 start、勘误复核输出、REPORT_CHECK、FROZEN_SCRIPTS_R9M3E.tsv）复制到 checkpoints/p05/registries/s4r9/M3e/ 并写 SHA256SUMS.txt，逐项比对原件。
- 报告 checkpoints/p05/P05_S4R9_M3e_REPORT.md：门禁 → 裁决 → 勘误 → 签收文件摘要 → 事件两张表 → 需用户裁决 → 交付物（条目不加反引号，项数与 SHA256SUMS 一致）→ 附录 B（end 门禁）。结尾写“本轮已完成/未完成 R9 M3e 范围，等待用户审核”，附 git log -1 与 git status --short。
- 顺序：0a 自检 → start 门禁 → 保存任务书 → 裁决与勘误脚本试跑 → 收尾链试跑（$EV/shakedown/）→ 冻结 FROZEN_SCRIPTS_R9M3E.tsv → 记录提交 (i) → 冻结期正式各跑一次 → 收尾提交 (ii)。冻结期不修脚本、不重跑；门禁 FAIL 照实写入附录 B。
- 提交只含 checkpoints/p05/ 与 testing/d003/stage_s4r9/；提交信息末尾写 awaiting user review。

## 7. 硬停止
只在以下情况停下报告：0a 自检不通过；开工门禁不符；发现 S4/、判定器、历史装置或已提交文件被改动；出现无法解释的越界写入。合法的中间产物使工作区非空，不构成停止理由。
