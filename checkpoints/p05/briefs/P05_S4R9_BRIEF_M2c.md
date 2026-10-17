# P05-S4 R9 M2c 任务书：M2b 流程纠正（RULINGS 截断、门禁吞 FAIL、未披露的裸写、KGRP-071 前提更正、事件表统一）与两项裁决落实

## 0. 身份与边界
- P05-S4 子轮次 R9 的 M2c（不是新阶段）。轮次标识 r9m2c；证据目录 checkpoints/p05/evidence/p05-s4r9/m2c；小表目录 checkpoints/p05/registries/s4r9/M2c/；补充报告 checkpoints/p05/P05_S4R9_M2c_REPORT.md；任务书原文存为 checkpoints/p05/briefs/P05_S4R9_BRIEF_M2c.md。
- 本轮只做登记与只读脚本：不运行任何 S4 驱动、gdb 或构建；不改预注册；不改 S4/、判定器、历史装置，也不改任何已提交的 r9/r9m2b 脚本、allow 文件、报告或小表（包括 gate_r9m2b.sh、gate_check_r9m2b.py、gate_allow_r9m2b_end.txt）。需要的新脚本一律新建，文件名带 r9m2c。
- 禁止 git commit --amend、rebase 以及任何改写历史的 git 操作。fbf3054 中被截断的 RULINGS 留在历史里，只做披露。
- 不得宣布阶段完成，不得询问是否签收。报告里不写本轮收尾提交的哈希。
- 开工先读：AGENTS.md → STATE.md → 本任务书 → P05_S4R9_M2b_REPORT.md → registries/s4r9/M2b/ → testing/d003/stage_s4r9/{gate_r9m2b.sh,gate_check_r9m2b.py,events_r9m2b.py,hitseq_r9m2b.py}。
- 开工门禁：HEAD = 42d7d9751ca6506601c47271c46f3b3242ad2453；HEAD:S4 = 589e15eb11fcb04e031b524f25a443e7921946cf；判定器 sha256 = d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb；git status --short 为空，或仅含本任务书点名的新文件；registries/s4r9/{M0,M2,M2b}/SHA256SUMS.txt 与 registries/s3r5/SHA256SUMS.txt 逐项通过；RULINGS.tsv 为 122611 字节、sha256 1ebffb14520317619132305baacd87e11a86991f10a9db681346e8e6084075a5，且前 121086 字节的 sha256 = f17bd838a699282b7a993f82ee93455aceae06e3ba3bb3d07b5277a5d20e6986（= ebf3d00 版本）。任一不符就停下报告。

## 1. 写入与执行纪律（硬规则，与 M2b 相同，另加 7–9 三条）
1. 每条含写入的命令开头先执行：REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2c; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"，然后经 sh testing/d003/safe_run.sh p05-s4r9/m2c -- <命令> 运行。
2. 写入目标只能以 $EV/、$REPO/testing/d003/、$REPO/checkpoints/p05/ 开头；其他轮次的证据目录（p05-s4r9/m0、m2、m2b，p05-s4r8/）只读。
3. 内联命令不得含 > 字符（含 2>&1）；不用 2>/dev/null；核对路径只用 ls -d 或 test -e；不做沙箱探测或反例测试。
4. 新脚本放 testing/d003/stage_s4r9/，文件名带 r9m2c，第一段用标准首段；Python 一律用 python3 -I -B。运行前用 grep 工具查禁止项。
5. 每一次 rm、mv、重跑覆盖都进事件表二。行号由脚本从 $EV/safe_run.log 提取。门禁重跑用 _R2、_R3 等新文件名。
6. 停止策略：只有真实基线异常、无法解释的越界改动和第 6 节的硬停止条件才停。合法的中间产物使工作区非空，不是停止理由。
7. 【新】任何文件都不得经 safe_run 以外的途径写入，包括编辑工具直接改文件。发现需要修复已提交文件时，停下写进报告，不得静默修复。
8. 【新】活文件（RULINGS.tsv、ERRATA_9.txt、STATE.md 以外的登记文件）只能由脚本追加。追加脚本必须先断言"新文件 = 旧文件字节 + 新行"，然后才落盘；否则拒绝写入。
9. 【新】门禁的 FAILS 以输出文件中 ^FAIL	 开头的行数为准。门禁脚本最后一步自检：ok 的条件是 FAIL 行数等于 FAILS 值，且 FAILS = 0。

## 2. 输入事实（规划者只读核实；执行者须用脚本按原始文件复核，复核不符就照实写，不得沿用本节文字）
- G-1 RULINGS 截断：git show --stat fbf3054 显示 RULINGS.tsv +3 / −155。fbf3054 版本共 155 行，末尾是 U142、U143、U299、U300、U301，即 U144 至 U298 段被删。ebf3d00 版本为 307 行、121086 字节。现行版本（42d7d97）为 310 行、122611 字节，前 121086 字节与 ebf3d00 相同，U299–U301 三行与 fbf3054 相同。现行文件 mtime 为 2026-10-16T21:16:11Z，该时刻在 m2b 的 safe_run.log 中没有对应条目。
- G-2 门禁吞 FAIL：GATE_R9M2b_end.txt 第 30、35、36、44 行为 FAIL（RULINGS_BASE_PREFIX_UNCHANGED、RULINGS_PREFIX_OF_START_UNCHANGED、RULINGS_NOT_TRUNCATED、STRAY_NEW_OR_CHANGED_NONE），末行却是 FAILS=0。原因是 gate_check_r9m2b.py 的 __main__ 不以 fails 作退出码，gate_r9m2b.sh 只累加 Python 退出码。gate_check_r9.py 写法相同；对应的 GATE_R9_start.txt 与 GATE_R9_end.txt 中 FAIL 开头的只有 FAILS=0 行本身。
- G-3 已提交门禁被改且未披露：gate_check_r9m2b.py（mtime 21:17:02Z，加入 end_R2→end 映射）、gate_r9m2b.sh（mtime 21:17:59Z，加入 end_R2 与 BASE_MODE，并把 TRACKED_TESTING_D003_NO_MOD_DEL_SINCE_START 的比较基准由 HEAD 改为 $BASE）、gate_allow_r9m2b_end.txt（新增 " M testing/d003/stage_s4r9/*"）。三者都在 fbf3054 中已经提交，改动随 42d7d97 入库，不在 safe_run.log、RUNNER_DIFF_R9M2b.txt 与报告中。
- G-4 KGRP-071 前提错误：R9 M2b 任务书 F-1 写"F3 命中 4 次、F4 命中 2 次"是规划者错误。K_INHERIT_RAW_R9.txt 第 820–829 行显示两边各 4 次（第 4 次为 arg=22 func=- -:0）。R9 原始日志中各组的两边命中数都相等（1-1 共 16 组，2-2 共 8 组，4-4 共 40 组；另有 9 组 CITED，不在统计内），原脚本的真实缺陷是 min 截断、第 4 次命中未取 bt、大小不同时直接 pass。M2b 报告 §4.3 第 1 点后半与第 2 点（"较少 continue""LSAN 提前终止"导致 2 次）没有日志依据。
- G-5 事件数不一致：报告 §7.2 与 STATE 写 54 项；执行总结写 58 项 + 1 项；EVENTS_R9_ALL_R9M2b.tsv 实有 62 行数据（r9m0 27 行、r9m2 11 行 + reflog 1 行、r9m2b 23 行）；m2b safe_run.log 有 24 行（最后一行 21:19:56Z 的 copy_registries 未进表）。报告 §7.2 只列到 m2b 第 15 行，G-1、G-3 的裸写都未记录。
- G-6 HIT 等价口径：HITSEQ_F3_F4_R9M2b.tsv 的 346 行中，178 行两边都是空串 sha（e3b0c442…），168 行非空且相同。10 组 NO_SEQ 对应的注入点为：M2-07-INJ-{closed1d,closed2d,experimental,fft,kottke,tensor,jones,nv,vl}-ng5-F4（d003plan，KGRP-001…009），以及 M2-06-DIAG-01-F4、M2-06-01-F4-C（nan，KGRP-025）。这些点两遍的 HIT 行都非空且与 F3 相同。
- G-7 措辞：M2b 报告出现"严格""彻底""完全"等词，违反 M2b 任务书 §5。

## 3. 用户裁决（start 门禁通过后，由 append_rulings_r9m2c.py 按 §1-8 追加到 RULINGS.tsv，5 列）
- U302：R9 M2b 的数据采信（HITSEQ、K_INHERIT_R9M2b、SOLN_SUPP_JUDGE_R9M2b），判定不变。G-1 至 G-7 记为 E9-7 至 E9-13，追加到 ERRATA_9.txt；E9-1 中"4 vs 2"由 E9-10 更正，原行不改；M2b 报告不改，由 M2c 报告补充更正。
- U303：K 继承的替代证据。10 组 NO_SEQ_EVIDENCE_R2 采信 HIT 行等价作为替代证据，条件是 hitseq_split_r9m2c.py 断言：每组对应的注入点在两遍中都是 NONEMPTY_IDENTICAL。范围仅限 k_max=1 的这 10 组；任一组不满足，则该组保持 NO_SEQ 并列入"需用户裁决"。
- U304：U301 生效（追加本行，U301 原行不改）。RP-R8-M2c-1/1b 带范围声明关闭。范围：F4 上 S4.cpp Simulation_InitSolution 1760–1774 段的分配失败清理；证据为 18 个 SOLN 修后验证点（1763/1764/1765 × closed2d-ng1/fft-ng5/kottke-ng5 × dbg/san/san-AL），rc1=1、重试 call2 与无注入对照相同（I6 两遍都 HOLD）、san 行报告数为 0 且无崩溃。不覆盖：非 FMM 的 S4_malloc（OUT_OF_SCOPE_D003，转 S5）；Python/Lua 可见性（M3）；B 树行为（B 列不是修复证据）。
- U305：门禁与活文件纪律（自本轮起生效）：①门禁 FAILS 以输出文件中 ^FAIL	 的行数为准，并自检一致；②已提交的门禁脚本和 allow 文件不得修改，需要变化时新建带新轮次编号的文件；③活文件只能由带前缀断言的脚本追加；④门禁发现 FAIL 时，先停下写进报告，再按任务书处理，不得先修复后重跑来掩盖。

## 4. 步骤
- S-A 门禁：新建 gate_r9m2c.sh 与 gate_check_r9m2c.py（以已提交的 42d7d97 版 gate_r9m2b.sh、gate_check_r9m2b.py 为蓝本复制修改，原件不动），差异写入 RUNNER_DIFF_R9M2c.txt。必须修正：Python 以 fails 作退出码；shell 末尾以 grep -c '^FAIL	' 计数，写入 FAILS 并断言两者一致；只有 start 与 end 两种模式，重跑通过参数指定 _R2 等输出名，不改脚本。内容包括第 0 节各项、/tmp 顶层只读快照、__pycache__/.o 基线、RULINGS 与 ERRATA_9 的字节数、sha256 与 ebf3d00 前缀检查。allow 文件新建为 gate_allow_r9m2c_{start,end}.txt。
- S-B 裁决与勘误（记录提交 (i)）：append_rulings_r9m2c.py 追加 U302–U305；append_errata_r9m2c.py 追加 E9-7 至 E9-13，每条写事实、证据文件与行号（由 S-C 的脚本输出提供）、影响范围、处理方式：
  - E9-7 对应 G-1（含首次 end 门禁已检出、恢复方式未经 safe_run、恢复后内容核对结果）；
  - E9-8 对应 G-2（含全仓门禁扫描结果）；
  - E9-9 对应 G-3（逐文件列出 diff 段与 mtime）；
  - E9-10 对应 G-4（更正 E9-1 的"4 vs 2"，撤回 M2b 报告 §4.3 第 1 点后半与第 2 点）；
  - E9-11 对应 G-5；
  - E9-12 对应 G-6；
  - E9-13 对应 G-7。
  提交前先跑 start 门禁，FAILS=0 才提交。提交信息末尾写 awaiting user review。
- S-C 只读核对脚本（全部写入 $EV/，经 safe_run 运行）：
  1. rulings_integrity_r9m2c.py → RULINGS_INTEGRITY_R9M2c.txt：用 git show 只读比较 ebf3d00、fbf3054、42d7d97 三个版本的行数、字节数与 sha256；列出 fbf3054 相对 ebf3d00 删除的 U 编号（脚本计数，不手写）；断言现行版本前缀等于 ebf3d00 版本、U299–U301 与 fbf3054 版本相同、U 编号唯一、数据行均为 5 列。
  2. audit_gates_r9m2c.py → GATE_AUDIT_R9M2c.tsv：扫描 checkpoints/p05/registries/ 下全部已跟踪的 GATE*.txt，逐个列出 ^FAIL	 行数、末行 FAILS 值与一致性（无 FAILS= 行的旧格式记 NO_FAILS_LINE）；列出所有"FAIL 行数 > 0 且 FAILS=0"的文件。
  3. gate_edits_r9m2c.py → GATE_EDITS_R9M2b_UNDISCLOSED.txt：git diff fbf3054 42d7d97 -- testing/d003/stage_s4r9/gate_* 的统一 diff，附上三个文件和 RULINGS 的当前 mtime（UTC），并与 m2b safe_run.log 的时间戳对照，标出"无对应 safe_run 条目"。
  4. kgrp_counts_r9m2c.py → KGRP_HITCOUNT_R9_R9M2b.tsv：逐组统计 R9 M0 与 M2b 原始日志中 F3、F4 的命中数，附 KGRP-071 在两份原始日志中的行号区间。
  5. hitseq_split_r9m2c.py → HITSEQ_SPLIT_R9M2c.tsv 与汇总：每行分类为 NONEMPTY_IDENTICAL、BOTH_EMPTY 或 DIFFERENT，按 item 汇总；再给出 10 组 NO_SEQ 组与注入点的对应关系及逐点逐遍分类，按 U303 的条件逐组给出 SUBSTITUTE_OK 或 SUBSTITUTE_NOT_MET。
  6. events_r9m2c.py → EVENTS_R9_ALL_R9M2c.tsv：读 m0、m2、m2b、m2c 四份 safe_run.log，每条日志条目一行（多行命令按时间戳行计）；表尾追加 reflog 的 amend 行（只读 git reflog）；再加 G-1、G-3 的裸写行（来源为脚本 3 的 mtime，类别"裸写(未经 safe_run)"）。断言：总行数 = 四份日志条目数之和 + 1 + 裸写行数；各轮行数分别打印。本脚本必须在收尾的最后一次 safe_run 写入之后再跑一遍，最后一遍的结果作为最终版本，且事件表中要包含该遍之前的全部条目。
- S-D 收尾：
  - P05_S4R9_M2c_REPORT.md 结构：门禁（列出 FAIL 行数与 FAILS 一致性）、裁决与勘误、RULINGS 截断与恢复、门禁缺陷与扫描、未披露的门禁改动、KGRP-071 更正、HIT 等价口径与 U303 逐组结果、事件两张表（数字只引用 events_r9m2c.py 的输出）、需用户裁决（只列 SUBSTITUTE_NOT_MET 组和本轮新发现的问题，没有就写"无"）。
  - STATE.md（≤ 8192 字节）：当前轮次改为 R9 M2c；RP-R8-M2c-1/1b 改为"按 U304 带范围声明关闭"；在 K 继承一行注明 U303 的结果；更正 M2b 那一行的"事件表 54 项"；开放项中写明下一步为 R9 M1，之后是 M3。
  - 小表复制到 registries/s4r9/M2c/（不改名），写 SHA256SUMS.txt 并逐个比对；证据目录也写 SHA256SUMS.txt。
  - 跑 end 门禁，FAILS=0 且自检一致后，做收尾提交 (ii)，提交信息末尾写 awaiting user review。提交后只在终端输出 git log -3 --oneline 和 git status --short。

## 5. 措辞
- 不写"100%""完全""严格""彻底""证实""精确""全面闭环"。REPORTED_FAILURE 只表示返回码非零。B 列不是修复证据。
- 没有日志依据的原因一律写"原因未查明"，不得推测。规划者给的事实与原始文件不符时，照实写"规划者事实有误"。
- 结尾写"本轮已完成/未完成 R9 M2c 范围，等待用户审核"。

## 6. 硬停止条件
1. 开工门禁任一项不符。
2. rulings_integrity 断言失败（现行 RULINGS 前缀不等于 ebf3d00 版本，或 U 编号重复）。
3. 任何追加脚本的前缀断言失败。
4. 任何越界写入、safe_run 之外的写入、对 S4/ 或已提交文件的改动、写入其他轮次证据目录，或改写 git 历史。
5. 门禁出现 FAIL：停下写报告，不得修改门禁后重跑来消除。

SUBSTITUTE_NOT_MET 不算硬停止：照实记录，列入"需用户裁决"。
