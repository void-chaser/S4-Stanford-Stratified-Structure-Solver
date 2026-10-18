# P05-S4 R9 M3a 任务书（轮次标识 r9m3a）——M1R4 勘误收口 + make test 主套件回归 + Python/Lua 端到端装置与预注册（不跑端到端）

## 0. 身份与边界
- P05-S4 子轮次 R9 的 M3a（阶段收口的第一步；不是新阶段，不得出现 P05-S6）。证据目录 checkpoints/p05/evidence/p05-s4r9/m3a；小表目录 checkpoints/p05/registries/s4r9/M3a/；报告 checkpoints/p05/P05_S4R9_M3a_REPORT.md；任务书原文经 safe_run 存为 checkpoints/p05/briefs/P05_S4R9_BRIEF_M3a.md。
- 本轮目的：①把 r9m1r4 的流程缺陷登记为勘误并补正（只读）；②在导出树上运行项目既有主套件 make test（B 与 F4 各两遍），判定 F4 相对 B 无新增失败；③设计并构建 Python/Lua 公共 API 端到端（E2E）装置，写好预注册并冻结；**不运行任何 E2E 点**，完成后停下等用户审核预注册。
- 允许：在 $EV/trees/ 下导出树并编译（make、setup.py、g++），只为 make test 和 E2E 装置构建。
- 不允许：修改 S4/、判定器、历史装置（judge_d003.py、matrix_*.py、run_*.sh、safe_run.sh、summarize_r6.py、src/、seam/、已提交的全部 stage 脚本）以及任何已提交文件（含 registries/s4r9/M1R4/ 全部文件）。E2E 装置只能链接**未修改的** testing/d003/src/inject_d003.cpp，需要变体时复制成带 r9m3a 的新文件。p05-s4r9 下 m1、m1r2、m1r3、m1r4 证据目录只读。
- 禁止 git commit --amend、rebase；报告不写收尾提交哈希；不得宣布阶段完成，不得询问签收（报告里也不要写含"签收"二字的否定句，统一写"等待用户审核"）。
- 开工先读：AGENTS.md → STATE.md → 本任务书 → P05_S4R9_M1R4_REPORT.md → registries/s4r9/M1R4/ → registries/s4r9/ERRATA_9.txt → Makefile.common 的 test、test-python、test-fast、test-lua 目标 → testing/d003/run_d003.sh 的 LIBFLAGS（--wrap 列表）→ testing/d003/src/inject_d003.cpp。
- 开工门禁（任一不符即停）：
  - HEAD = 2f86aa11c7ee1bb16f663abf03ddbf04674a6912；HEAD:S4 = 589e15eb11fcb04e031b524f25a443e7921946cf；判定器 sha256 = d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb；git status --short 为空；
  - /tmp 顶层只读快照（条目数与 sha256）；
  - RULINGS.tsv = 134794 字节、sha 8b3d0e31fff12ddd84827e2f508f458f73c8574681feb2100aa684f9a3428ae2，最大 U 号 U327；
  - ERRATA_9.txt = 30931 字节、sha 49add16f2343c92893fc500d25f3d37b6b1c4c76be5e7cb3eb891308037f5748，最后一条 E9-34；
  - registries/s4r9/M1R4/SHA256SUMS.txt sha = 57d72574415e9b255f2805cf65b88049964123d6a6980487d6565a46311e5d75，11 项全部 OK；s3r5、M0、M2、M2b、M2c、M1、M1R2、M1R3 各清单全部 OK（项数先由脚本数出来再断言，不要手填）。

## 1. 写入与执行纪律（沿用 M1R4，补充项标【新】）
1. 每条含写入的命令开头：REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m3a; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"，然后经 sh testing/d003/safe_run.sh p05-s4r9/m3a -- <命令>。
2. 仓库内一切文件的创建与修改都经 safe_run（固定写法：python3 -I -B -c "import base64; open('<相对路径>','wb').write(base64.b64decode('<内容>'))"），不得用编辑器工具直接写仓库文件。改写一律换新文件名（_v2、_v3），已执行过的文件不得覆盖。
3. 写入目标只能在 $EV/、testing/d003/stage_s4r9/（文件名带 r9m3a）、checkpoints/p05/（本轮目录、STATE、报告、RULINGS 与 ERRATA_9 的追加）之下。写到其他轮次的证据目录、或改动任何已提交的 registries 文件，都是硬停止，不"恢复"。
4. 【新】make test 与构建要在导出树里跑：make -C "$EV/trees/<名>" ...，并设置 PYTHONDONTWRITEBYTECODE=1。make test 会执行 rm -rf build 和 rm -f S4*.so，所以必须确认 -C 的目录在 $EV/trees/ 之下，先 ls -d 核对，不得在仓库根目录运行 make test 或 make clean。试跑期先只读查看 testing/runtests.sh、test_lua_regression_negative.sh 等脚本，确认它们只写导出树内部或 $TMPDIR，结论写进报告。
5. 两个时期：
   - 试跑期（记录提交 (i) 之前）：可以任意次试跑，输出只放 $EV/shakedown/<序号>/，每次都经 safe_run。必须在试跑期完成以下几件事：
     a) end 门禁以 end 模式对本轮真实目录跑通。为了让 POST_I 块真正执行，试跑时用 --commit-i HEAD 参数模拟 (i)，并在输出中断言 POST_I 块的每一项都执行了（逐项打印名称）。
     b) report_check 对报告草稿跑通。
     c) STATE 草稿字节数 ≤ 8192。
     d) 所有阳性对照跑通（见 §4）。
   - 冻结期（(i) 之后）：只能调用 FROZEN_SCRIPTS_R9M3A.tsv 列出的脚本，每个只调用 1 次（make test 的 4 次运行由一个冻结脚本 run_maketest_r9m3a.py 一次完成）；不得新建或改写 testing/d003 下的任何文件。(i) 已提交的文件（包括 registries）在冻结期不得改写：冻结期产出一律用新文件名（如 *_FINAL.tsv）。
6. 冻结期遇到脚本报错、断言失败或核证不一致：不修脚本、不重跑；保留现场，继续执行后面的收尾步骤，在报告"需用户裁决"一节逐条列出。
7. 【新】收尾固定顺序（每步调用一次，中间不插入任何命令）：报告与 STATE 落盘 → report_check → copy_registries → events → sha_sums → end 门禁 → 收尾提交 (ii)。不再设 finalize：copy_registries 自己完成复制和逐项 sha 比对，并写 registries/SHA256SUMS.txt。门禁 FAIL 时，只允许在门禁之后用一条 safe_run 命令给报告追加附录（只追加，不改正文），然后提交。
8. 措辞：没有日志依据的原因写"原因未查明"；规划者给的事实与原始文件不符，照实写"规划者事实有误"并给出正确值。行号一律由脚本从原文件算出，不得照抄任务书。

## 2. 输入事实（M1R4 缺陷；执行者用 audit_r9m1r4_r9m3a.py 按原始文件逐条复核，结论写"属实"或"规划者事实有误"）
- J-1 阳性对照无效：recert_r9m1r4_v2.py 第 373–382 行，case3 比较的是常量 sha256(b"tampered_fact") 与 EXPECTED_P1_SHA，case4 比较的是 158-1 与 158，两项恒为真；case1/2 只改内存里的字典，不读落盘的篡改文件；$EV(m1r4)/shakedown/posctrl/ 不存在（任务书 S-D 要求篡改副本放在这里）。
- J-2 补做断言不完整：recert 的 target_scripts 只有 posctrl、smoke、formal、verdict、compare 这 5 个；FROZEN_SCRIPTS_R9M1R3 中按脚本计的有 14 个。按 m1r3 safe_run.log 中时间 ≥ 2026-10-18T04:28:39Z 的 cmd= 字段计数（只算以 python3/sh 调用该脚本的行），规划者统计：events_r9m1r3.py 2 次（物理第 158、160 行），report_check_r9m1r3.py 3 次（第 155–157 行），其余各 1 次（posctrl 148、smoke 149、formal 150、verdict 151、compare 152、summarize 153、cmp_vs 154、copy_registries 159、sha_sums 162、gate_v5.sh 163、finalize 164）。
- J-3 H-5 行号：m1r3 safe_run.log 中 gate_r9m1r3_v4.sh start _v5 的物理行号是 94（规划者在 M1R4 任务书里写的 82 有误，第 82 行是 heredoc 内容）；AUDIT_R9M1R3_R9M1R4.tsv 把它写成"属实（物理82）"。
- J-4 (i) 已提交文件被改写：registries/s4r9/M1R4/UNLOGGED_WRITES_R9M1R3.tsv 在 786b150 提交，又在 2f86aa1 被修改（RULINGS.tsv、ERRATA_9.txt 两行的 mtime 从 03:44:43Z 变为 05:23:53Z，后者是 r9m1r4 有日志记录的 append_rulings/append_errata，即 m1r4 log 第 14、15 行），现在这两行把 r9m1r4 的写入时间当作 r9m1r3 的未记录写入。gate_check_r9m1r4_v3.py 第 493–495 行的 COMMITTED_I 检查只覆盖 testing/d003 和 briefs，不覆盖 registries。
- J-5 end 门禁：
  - POST_I_CALL_COUNT_FINALIZE 期望 1，但收尾顺序中 finalize 在门禁之后，门禁时刻应为 0；
  - EVENTS 锚点取 "gate_r9m1r4_v3.sh end" 或 "gate_r9m1r4_v2.sh end" 的首次出现，匹配到了试跑行（第 29 行）；
  - shakedown/2、shakedown/3 的 end 试跑都是 COMMIT_I_PRESENT=missing，POST_I 块没有执行；
  - EVENTS_R9M1R4.tsv 有 54 行，log_line 覆盖到第 56 行（events 自身那一行），正式门禁在第 58 行，第 57 行（sha_sums）没有覆盖。报告附录 A.2 说"真实覆盖了门禁前的全部 54 条日志记录"，与此不符。
- J-6 收尾质量：
  - report_check 在禁用词检查处因误中"不询问是否签收"而提前退出，第 3 步数字核对没有执行；
  - STATE.md 8480 字节，超过任务书要求的 8192；
  - 报告正文 §9 写"需用户裁决：无"，与附录 A.3 的 4 项矛盾；
  - 报告 §10.1 列了 13 项小表（含 EVENTS_R9M1R4.tsv），registries/s4r9/M1R4/SHA256SUMS.txt 只有 11 项，EVENTS_R9M1R4.tsv 和失败的初版 GATE_R9M1R4_start.txt 没有进 registries；
  - 报告 §1 写开工门禁"41 项全数 PASS"，没有在同一节说明初版 start 门禁 FAILS=1（M1R2_SUMS_34）。
- J-7 规划者独立复核（只作为参考，执行者在 S-B 中自行复算）：m1r3 两遍 FORMAL_FACTS 各 651 行，键唯一，12 个事实字段两遍之间 0 处不同；已提交的 VERDICT 为 626/22/3；EQUIV 为 648 EQUIVALENT + 3 NOT_RUN，HIT 为 529/119/3。

## 3. 用户裁决（start 门禁通过后，由 append_rulings_r9m3a.py 以"新文件 = 旧文件 + 新行"追加，5 列，从 U328 起；前缀断言失败即硬停止）
- U328：r9m1r4 的独立复算（RECERT_R9M1R3.tsv 中 VERDICT/EQUIV/SUMMARY/FORMAL_FACTS 各项）连同规划者复核（J-7），作为 M1 有效结果（r9m1r3 的 VERDICT、F3_F4_EQUIV、M1_SUMMARY）的核证。M1 不再开修正轮。J-1..J-6 按事实登记勘误。
- U329：r9m1r4 的阳性对照（POSCTRL_RECERT_R9M1R4.txt）不作为有效对照。本轮 S-B 用落盘篡改副本对 recert 的复算逻辑重做阳性对照，作为替代。
- U330：r9m1r3 门禁补做断言以本轮 S-B 产出的 BACKFILL_FULL_R9M1R3.tsv 为准（覆盖全部 14 个脚本）。events=2、report_check=3 按事实记为 FAIL，与 E9-32 对应，不另作处理。
- U331：J-4 中 UNLOGGED_WRITES_R9M1R3.tsv 不再改写。本轮输出更正表 UNLOGGED_CORR_R9M3A.tsv，逐行说明两份版本的差异，并按 m1r3/m1r4 日志重新判定那两行的归属。
- U332：r9m1r4 附录 A.3 的 4 项：项一接受（报告中没有询问签收的语句，属检查器误匹配）；项二接受（门禁设计缺陷，finalize 在门禁后单次执行）；项三不按原文接受，以 J-5 的事实为准（EVENTS 覆盖到第 56 行）；项四由本轮把 STATE 压缩到 ≤ 8192 字节。
- U333：M3 范围：a) make test，在导出树上 B 与 F4 各两遍，判据为"F4 的失败测试集合 ⊆ B 的失败测试集合，且 F4 两遍一致"；b) Python/Lua 公共 API E2E（正常 → 注入失败 → 可见报错 → 同一对象重试恢复 / 全新对象重试恢复），在 M3a 只做设计、构建和预注册，用户审核后由 M3b 运行；c) U38 已由 U90 裁决（806、415 已修；528、1164 转 S5），M3 只核对台账，不重新分类；d) E2E 中发现 API 层没有报错（SILENT_SWALLOW）或重试后结果不一致，都登记为新红点，按 U4 处理，本阶段不改 S4/。

## 4. 步骤
- S-A 门禁 gate_r9m3a.sh + gate_check_r9m3a.py：
  - 每项检查都包在 try/except 里，异常时写 "FAIL<TAB><名><TAB>CHECK_CRASHED<TAB><异常>" 后继续；FAIL 数以输出中 ^FAIL<TAB> 的行数为准，并等于退出码（封顶 255）；
  - 常量集中写在文件头，自检"常量中不含 m1r2、m1r3、m1r4"；
  - start 模式：断言 §0 的开工门禁全部项。
  - end 模式至少断言：
    1. (i) 之后每个冻结脚本的调用次数等于门禁时刻的应有值（gate 自己 = 1，其余 = 1；按 safe_run.log 的 cmd= 字段计数，只匹配以 python3/sh 调用该脚本的行）；
    2. (i) 之后没有写入 testing/d003；
    3. FROZEN 清单逐项 sha 不变；
    4. git diff --name-only <i> HEAD 和工作区相对 (i) 都没有修改 (i) 已提交的任何文件（范围：testing/d003、checkpoints/p05/briefs、checkpoints/p05/registries，RULINGS.tsv 与 ERRATA_9.txt 只断言前缀不变）；
    5. EVENTS 的行集合 = 冻结的 events 逻辑对"本次 events 调用行及之前全部物理行"重算的结果（锚点取 (i) 之后最后一次 events 调用的行号，不取首次匹配）；
    6. 证据 SHA256SUMS 全部 OK，截断哈希行号 = sha_sums 调用行号且哈希正确；
    7. 开工门禁之后 mtime 更新的每个仓库文件，都能在日志中找到写入它的命令（UNLOGGED_SELF = 0；扫描范围含 testing/d003/stage_s4r9、checkpoints/p05 下除 evidence 外的全部文件）；
    8. 他轮证据目录（m1、m1r2、m1r3、m1r4）中没有 mtime 晚于本轮开工门禁的文件；
    9. registries/s4r9/M1、M1R2、M1R3、M1R4 与 HEAD 2f86aa1 完全相同；
    10. STATE.md ≤ 8192 字节；
    11. registries/s4r9/M3a/SHA256SUMS.txt 全部 OK，且项数 = 报告"交付物"一节列出的数量（由脚本解析报告得到）；
    12. 仓库根目录下没有 build/ 新改动、没有新增 *.so（与开工基线对比）；
    13. /tmp 快照与开工时一致。
- S-B M1R4 勘误收口（只读）：
  1. audit_r9m1r4_r9m3a.py 复核 J-1..J-6，行号全部由脚本计算，输出 AUDIT_R9M1R4_R9M3A.tsv。
  2. backfill_full_r9m3a.py 按 J-2 的口径对 m1r3 的 14 个脚本计数，输出 BACKFILL_FULL_R9M1R3.tsv（脚本、期望 1、实际、物理行号列表、结论、对应勘误号）。
  3. posctrl_recert_r9m3a.py：把 m1r3 的 VERDICT、F3_F4_EQUIV、FORMAL_FACTS pass1，以及 m1r4 的 EVENTS_RECALC_R9M1R3，复制到 $EV/posctrl/<case>/，在副本上各篡改 1 处（VERDICT 改 1 行 verdict；EQUIV 改 1 行 G6 的 I3；FORMAL_FACTS 改 1 行 rc1；EVENTS_RECALC 删 1 行），然后用本轮新写的复算函数逐行比对，期望每个 case 恰好检出 1 处、未篡改的基准副本检出 0 处。复算函数可以复制 recert_r9m1r4_v2.py 的逻辑（复制成本轮文件，不得 import 或调用原脚本）。输出 POSCTRL_R9M3A.txt。
  4. unlogged_corr_r9m3a.py 输出 UNLOGGED_CORR_R9M3A.tsv（786b150 与 2f86aa1 两个版本逐行对比，以及每行按日志重新判定的结论）。
  5. append_errata_r9m3a.py 从 E9-35 起追加，至少覆盖 J-1..J-6（J-6 按 4 个子项拆分或合并都可以，但每个子项都要有报告行号或文件行号）。
- S-C make test 主套件回归：
  1. 导出两棵树：
     - F4：git archive HEAD | tar -x -C "$EV/trees/F4"；
     - B：git archive HEAD -- . ':!S4' | tar -x -C "$EV/trees/B"，再 git archive 37a82e8 S4 | tar -x -C "$EV/trees/B"。
     断言 B 树中 S4/ 的内容与 37a82e8:S4 一致（逐文件 sha 与 git ls-tree 比对），F4 树与 HEAD 一致。记录两棵树的 S4/ 文件清单 sha。
  2. 预注册 PREREG_MAKETEST_R9M3A.tsv，在任何正式 make test 运行之前写好并记录 sha 与 UTC 时间。内容：
     - 测试单元的识别规则：unittest -v 的 "test_x (mod.Class) ... ok|FAIL|ERROR|skipped|expected failure"、test-fast 的退出码、test-lua 三段各自的退出码和逐项输出；
     - 判据：F4 失败集合 ⊆ B 失败集合 → NO_NEW_FAILURE；F4 两遍不一致 → FLAKY；两树的测试单元集合不同 → SUITE_DIFF（需用户裁决）；
     - 状态写 INFLUENCED（参考了历史 S3R5 收口记录）。
     试跑期可以对 F4 跑一次 make test，用来调好解析脚本，输出放 shakedown/；这次结果不算正式结果，报告里要列出。
  3. 冻结期由 run_maketest_r9m3a.py 一次完成：顺序为 B 第一遍、F4 第一遍、B 第二遍、F4 第二遍（每遍都是完整的 make -C <tree> test PYTHON=python3，包含它自己的 rm -rf build 重建）。保存每遍的完整日志（$EV/maketest/<tree>_p<n>.log）和退出码。之后由 judge_maketest_r9m3a.py 输出 MAKETEST_UNITS_R9M3A.tsv（逐单元 × 4 遍）和 MAKETEST_VERDICT_R9M3A.tsv。
  4. 阳性对照（试跑期）：用解析脚本处理一份人为构造的日志副本（F4 比 B 多 1 个 FAIL，以及 F4 两遍之间有 1 处不同），期望分别判为 NEW_FAILURE 和 FLAKY。输出 POSCTRL_MAKETEST_R9M3A.txt。冻结期再用同一个 judge 脚本的 posctrl 模式正式调用 1 次。
- S-D E2E 装置与预注册（不运行 E2E）：
  1. 只读源码，写 E2E_API_SURVEY_R9M3A.md，标注 [源码]：
     - Python 扩展（S4/main_python.c 或实际文件）和 Lua 前端（S4/main_lua.c 等），对 S4 内部非零返回码怎么处理：抛异常、lua_error、还是忽略。按 API 函数逐个列出 SetOptions、GetPowerFlux、GetAmplitudes、GetFields 等实际会触发求解的调用，以及每个调用对应的错误路径行号；
     - 哪些 S4 选项组合能从公共 API 进入 M1/M2 已覆盖的失败点族：FFT 离散化、PolarizationDecomposition 与 PolarizationBasis 的 Jones/Normal/VL（只能写源码里真实存在的选项名）、ClosedForm、LinearSolve 相关路径。不能从公共 API 到达的点，写 NOT_REACHABLE_VIA_API 和理由。
  2. 构建（只在 $EV/trees/E2E_F4 中，S4/ 来自 HEAD，不改源码）：
     - Python 扩展：链接 inject_d003.cpp 的 -fPIC 目标文件，链接参数与 run_d003.sh 的 --wrap 列表一致（malloc、fft_plan_exec、fft_plan_dft_2d、S4_malloc 的修饰名照抄）；
     - Lua 前端：build/S4 用同样的 --wrap 重新链接；
     - 记录产物 sha256 和构建日志。用 nm/readelf 只读核对 __wrap_ 符号确实存在，结果写 E2E_BUILD_R9M3A.tsv。
  3. 装置脚本 e2e_python_r9m3a.py 和 e2e_lua_r9m3a.lua（另加一个驱动 run_e2e_r9m3a.py，每个点开一个全新子进程，捕获 rc、stdout、stderr、S4FMM HIT 行、Python 异常类型与消息、Lua 错误文本）。每个点按顺序做 4 步：
     - (1) 干净参考：不注入，求解并记录数值结果；
     - (2) 注入：设置 S4FMM_INJECT 与 S4FMM_NTH（注入器每次调用都读 getenv，且只有第 nth 次分配失败），调用 API，记录是否可见报错、HIT 数；
     - (3) 同一对象重试：不改选项，再调用一次，记录数值；
     - (4) 全新对象重试：新建 Simulation，用相同输入求解，记录数值。
     数值比对的容差在预注册中写明（建议逐元素相对误差 ≤ 1e-12，或要求完全相同；二选一并说明理由）。
  4. 预注册 PREREG_E2E_R9M3A.tsv（写好就记录 sha 与 UTC 时间，状态 INFLUENCED）。每个点一行，列：point_id、frontend（py/lua）、选项、注入模式与 nth、对应的 M1/M2 点族或 K 组、exp_hit（≥1）、exp_visible（YES：Python 抛异常 / Lua 报错，具体期望写清楚）、exp_retry_same（EQUAL_REF）、exp_retry_fresh（EQUAL_REF）、无注入对照行（每个前端 × 选项组合至少 1 行，期望 hit=0、无报错、两次结果相同）。点数由 S-D1 的调研决定，原则上每个"公共 API 可达的失败点族 × 前端"至少 1 点。不可达的点族在表外单列，并给出理由。
  5. E2E 判定脚本 judge_e2e_r9m3a.py：类别为 E2E_OK、API_SILENT（注入命中但 API 没有报错）、RETRY_DIFF、RETRY_FAIL、INVALID（hit=0）、FLAKY（M3b 跑两遍）、CONTROL_OK。用合成事实做阳性对照（每个类别至少 1 行），输出 POSCTRL_E2E_R9M3A.txt。**本轮不运行任何真实 E2E 点**；如需验证装置能加载，只允许对无注入对照行跑 1 次冒烟（smoke），输出到 shakedown/，报告里写明"冒烟不算 E2E 结果"。
- S-E STATE 压缩与台账：
  - STATE.md ≤ 8192 字节。当前轮次改为 R9 M3a；"S4R9 M1R4"那一行改写为"r9m1r4 复核结果经 U328 采纳；流程缺陷见 E9-35..";
  - 开放项里删掉"U38 分类"的旧说法，改为"U38 已由 U90 裁决，M3 只核对台账"；
  - 历史行合并成更短的摘要，细节指向各轮报告。
  - 只读检查 RED_POINTS_LEDGER（最新版本）与 STATE 开放项表的一致性，输出 LEDGER_CHECK_R9M3A.tsv（每个红点：台账状态、STATE 状态、是否一致）。

## 5. 执行顺序
start 门禁 → 裁决追加（U328–U333）→ S-B 取证与勘误追加 → 试跑期：S-C 导出与 make test 试跑、解析与阳性对照；S-D 调研、构建、装置、预注册、E2E 判定阳性对照、可选冒烟；end 门禁以 --commit-i HEAD 试跑并确认 POST_I 块全部执行；report_check 与 STATE 草稿检查 → 冻结清单 FROZEN_SCRIPTS_R9M3A.tsv（至少包含：run_maketest、judge_maketest（formal 与 posctrl 两种模式各算一项）、report_check、copy_registries、events、sha_sums、gate；PREREG_MAKETEST 与 PREREG_E2E 两个文件也写入清单，记 sha）→ start 门禁复核 → 记录提交 (i)（brief、RULINGS/ERRATA 追加、预注册、装置脚本、试跑期小表）→ 冻结期：run_maketest → judge_maketest posctrl → judge_maketest formal → 收尾（§1-7）→ 收尾提交 (ii)。

## 6. 报告结构
门禁 → J-1..J-6 复核（逐条写"属实"或"规划者事实有误"，并给出脚本算出的行号）→ 裁决与勘误 → 试跑期摘要（每次：目录、改了什么、结果；end 门禁试跑要列出 POST_I 块逐项执行的情况）→ make test 结果（4 遍逐单元汇总、失败集合、判定）→ E2E 调研（API 错误路径 [源码]、可达与不可达点族）→ E2E 装置与预注册（点数、sha、阳性对照、冒烟情况）→ 台账一致性 → 事件两张表（表一：越界写入尝试；表二：工具与脚本事件，含全部重跑）→ 需用户裁决（至少包括：E2E 预注册审核；SUITE_DIFF 或 NEW_FAILURE（如果出现）；不可达点族的处理）→ 交付物清单（与 registries/SHA256SUMS.txt 项数一致）。结尾写"本轮已完成/未完成 R9 M3a 范围，等待用户审核"，附 git log -1 与 git status --short。

## 7. 硬停止条件
1. 开工门禁任一项不符。
2. 追加脚本的前缀断言失败，或 U 号、E 号重复。
3. 越界写入；safe_run 以外的写入（含编辑器工具）；写他轮证据目录；改写已提交文件（含 registries）；改 S4/、判定器或历史装置；改写 git 历史；在仓库根目录运行 make test、make clean 或任何构建。
4. 冻结期调用清单外的脚本、改写 testing/d003 下的任何文件、任一冻结脚本调用超过 1 次。
5. 运行了任何真实 E2E 注入点（冒烟只限无注入对照行，且只在试跑期跑 1 次）。
6. 冻结期脚本报错、核证不一致或阳性对照失败（照实记录，不修不重跑，按 §1-6 处理）。

## 8. 规划者补充说明（本轮开工前追加，随任务书一并归档）
1. 上一次执行因模型流中断（STREAM_CLOSED）终止。规划者已只读核实：HEAD=2f86aa1，git status 为空，evidence/p05-s4r9/m3a/ 不存在，没有任何 r9m3a 文件落盘。本轮从开工门禁重新开始，不披露上次中断；如需提及，写进表二"工具框架事件"（上次会话中断，未落盘）。
2. 仓库根 build/ 被 git 忽略，是 2026-10-11 的历史产物（libS4.a、S4k/、modules/），不属于本轮违规，也不是停止条件。end 门禁第 12 项的口径：start 门禁把 build/ 下的文件清单（路径、大小、mtime、sha256）记到 $EV/BUILD_BASELINE_R9M3A.tsv，end 时与它比对，一致就 PASS；同时断言仓库根没有新增 *.so。不清理、不改动 build/。
3. 单轮步数控制：每完成 §5 中的一个阶段（start 门禁、裁决追加、S-B、S-C 试跑、S-D、冻结、冻结期、收尾），在 $EV/PROGRESS_R9M3A.txt 追加一行（经 safe_run，用固定小脚本写）。如果再次中断，接手的人先读这个文件和 safe_run.log，从断点继续；已执行过的脚本不得重跑覆盖，在报告的试跑摘要里说明中断点。
4. 其余按 M3a 任务书原文执行，§7 硬停止条件不变。
