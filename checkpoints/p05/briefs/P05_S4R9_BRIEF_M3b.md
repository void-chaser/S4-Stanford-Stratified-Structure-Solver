# P05-S4 R9 M3b 任务书（轮次标识 r9m3b）

## 0. 身份与边界
- P05-S4 子轮次 R9 的 M3b（阶段收口第二步；不是新阶段，不得出现 P05-S6）。证据 checkpoints/p05/evidence/p05-s4r9/m3b；小表 checkpoints/p05/registries/s4r9/M3b/；报告 checkpoints/p05/P05_S4R9_M3b_REPORT.md；任务书原文经 safe_run 存为 checkpoints/p05/briefs/P05_S4R9_BRIEF_M3b.md。
- 本轮目的：① 把 §2 裁决与 §3 规划者 K 项登记成勘误；② 用新解析器只读重解析 M3a 的 4 份 make test 日志（不重跑 make test）；③ 修订 Python/Lua E2E 装置，做注入无关的校准，写新预注册 PREREG_E2E_R9M3B.tsv，冻结之后正式运行两遍并判定。
- 不允许：修改 S4/、判定器 judge_d003.py、历史装置（matrix_*.py、run_*.sh、safe_run.sh、summarize_r6.py、src/、seam/、所有已提交的 stage 脚本）、任何已提交文件（包括 registries/s4r9/M3a/ 全部文件和 PREREG_E2E_R9M3A.tsv）。m3a 及更早的证据目录只读。E2E 只链接未修改的 testing/d003/src/inject_d003.cpp。
- 禁止 git commit --amend、rebase；不在仓库根目录运行 make；不宣布阶段完成；报告结尾统一写"等待用户审核"。
- 开工先读：AGENTS.md → STATE.md → 本任务书 → P05_S4R9_M3a_REPORT.md（含附录 A/B）→ registries/s4r9/M3a/ → ERRATA_9.txt 的 E9-35..E9-45 → S4/main_lua.c 的 :229-240、:284-292、:2211-2239、:3495-3578 → S4/S4.cpp:2400-2439 → testing/d003/src/inject_d003.cpp 的 :37-77、:465-478、:554-580。
- 开工门禁（任一不符即停）：
  - HEAD = 6aa11d8b2eb3bea896406842c30eda742af19080；HEAD:S4 = 589e15eb11fcb04e031b524f25a443e7921946cf；判定器 sha256 = d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb；git status --short 为空。
  - /tmp 顶层只读快照（条目数与 sha256）。
  - RULINGS.tsv = 136951 字节，sha 579b73c9d8952c3465d7402231b167d09d5eb087dd5519d6b0cefbffbf089951，最大 U333。
  - ERRATA_9.txt = 38912 字节，sha d5d8d9a0f46086df6855cb4637b035a641b327dd2f95fff1773002b9fbdc49ee，最后一条 E9-45，共 45 条。
  - STATE.md = 5191 字节，sha 7ae31ae099345433f348369eb3b8cd29e611de73a0f660d384a07e4f274025d1。
  - registries/s4r9/M3a/SHA256SUMS.txt 的 sha = 1fdf80ac147a3aa7f29ea899433d13513ef8c0816e4d83878c89c2093899d3d8，17 项全部 OK；PREREG_E2E_R9M3A.tsv 的 sha = 88f020705cc4ab55b56baeabbcff4c53d111e281afac3a6b7babf42513de5b9e。M1R4、M1R3 等历史清单全部 OK（项数先由脚本数出来，再断言）。

## 1. 写入与执行纪律（沿用 M3a，【新】为本轮补充）
1. 每条含写入的命令开头先执行 REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m3b; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"，然后经 sh testing/d003/safe_run.sh p05-s4r9/m3b -- <命令> 运行。仓库文件一律用固定写法创建：python3 -I -B -c "import base64; open('<相对路径>','wb').write(base64.b64decode('<内容>'))"。改写一律换新文件名。
2. 【新】**每次写入单独一条 safe_run**。外层不得用 &&、;、| 串联多个写入（E9-45 的成因）。一个步骤要写多个文件时，写成一个脚本，用一次 safe_run 调用。
3. 【新】长任务（构建、正式运行）在 run_code 和 tools.bash 上都要传 timeoutMs（≤600000），或者用后台 job。估计超过 8 分钟的任务必须拆成可续跑的分段：运行器按 point_id 跳过已完成的点，已完成的结果文件不覆盖。
4. 写入目标只能在 $EV/、testing/d003/stage_s4r9/（文件名带 r9m3b）、checkpoints/p05/（本轮目录、STATE、报告、RULINGS/ERRATA_9 追加）之下。不得写到别的轮次目录，不得改动已提交文件。违反就是硬停止，不"恢复"。
5. 两个时期：
   - 试跑期（记录提交 (i) 之前）：任意次试跑，输出放 $EV/shakedown/<序号>/。
   - 冻结期（(i) 之后）：只能调用 FROZEN_SCRIPTS_R9M3B.tsv 里列出的脚本，每个只调用 1 次（分段续跑的运行器按"一个逻辑调用"计，每个分段都要在报告里列出）。不得新建或改写 testing/d003 下的任何文件。
   - 【新】**所有收尾脚本（包括 closeout_r9m3b.py：按结果表向报告追加附录 A、生成 STATE）必须在 (i) 之前写好、试跑并冻结。**
6. 冻结期遇到报错或断言失败：不修脚本、不重跑；保留现场，继续收尾，在报告"需用户裁决"一节列出。
7. 收尾固定顺序（每步一次，中间不插入别的命令）：closeout（报告附录 A + STATE）→ report_check → copy_registries → events → sha_sums → end 门禁 → 收尾提交 (ii)。end 门禁 FAIL 时，只允许用一条 safe_run 给报告追加附录 B，然后提交。

## 2. 用户裁决（本任务书下发即生效；以"旧文件 + 新行"的方式追加到 RULINGS.tsv，5 列，追加前断言前缀哈希）
- U334：M3a 中 run_maketest_r9m3a.py 被调用 2 次（第 1 次因会话 120 s 死线中断，现场在 maketest_interrupted/）。接受，以第 2 次调用的四遍结果为正式结果，不重跑。
- U335：closeout_report_state_r9m3a.py 在 (i) 之后写入 testing/d003；UNLOGGED_SELF=2（registries SHA256SUMS 由脚本内部生成；e2e_lua 的裸写入见 E9-45）。二者都接受，作为登记处理。今后收尾脚本必须在 (i) 之前冻结；脚本内部生成、但不出现在命令行里的产物，由门禁按"脚本声明的输出清单"归属。
- U336：M3a 的 report_check 有一项 NUM_STATE_BYTES FAIL：以 STATE 实际的 5191 字节为准，只登记勘误，不改报告。
- U337：M3a 的 end 门禁有 6 条缺陷（脚本名没有随版本号更新、start 语义检查放进了 end 模式、反引号解析失败），start 复核有 10 条 FAIL（轮次起点不变量在合法改动后不再成立）。全部按检查器缺陷接受。本轮门禁必须修好这些问题：调用计数从 FROZEN 清单读取实际文件名；start 不变量只在 start 模式检查，end 模式改为"只追加文件的前缀 sha 等于开工值"；清单解析允许反引号。
- U338：make test 不再运行。M3a 判定 NO_NEW_FAILURE 的成立，以本轮 S-B 只读重解析通过为条件。项目套件 test_lua_regression_negative.sh 写 /tmp/s4_lua_neg_XXXXXX（退出时删除）属于项目固有行为：补登记到本轮表一（标注轮次 r9m3a、项目套件固有、临时目录、开工与结束时 /tmp 快照均为 0），不算执行者违规。
- U339：PREREG_E2E_R9M3A.tsv 不批准（理由见 §3 的 K-1/K-2/K-3/K-7）。原文件保持不动，由本轮的 PREREG_E2E_R9M3B.tsv 取代。
- U340：E2E 点族按 §4 S-C1 执行。LinearSolve A/B/B2/B2-buf、FMM 返回码族 E、分配 seam 家族 C、kottke_alloc:31 这些只能通过 seam 补丁到达的族，不出 E2E 点。在 COVERAGE_E2E_R9M3B.tsv 中标为 SEAM_ONLY，并给出 M1/M2 中已有的覆盖行。
- U341：Lua 的批处理模式出错即退出进程，exp_retry_same 记为 NOT_APPLICABLE_PROCESS_EXIT；同对象重试改用 Lua 交互（REPL）模式观测。容差为逐元素相对误差 ≤1e-12，批准。
- U342：新预注册在任何注入运行之前写好并记录 sha 与 UTC 时间。之后可以先试跑、再冻结、再正式运行，不需要为预注册另停一轮等用户审核。

## 3. 规划者 K 项（逐条复核，写"属实"或"规划者事实有误"，行号由脚本从原文件算出；结果写 AUDIT_R9M3A_R9M3B.tsv；属实的项登记为 E9-46 起的勘误）
- K-1：run_e2e_r9m3a_v2.py 的 run() 把 S4FMM_INJECT/NTH 设给整个 Python 子进程；e2e_python_r9m3a.py 的第 1 步干净参考在同一个进程里。nth=1 时命中会落在参考那一步。
- K-2：e2e_lua_r9m3a.lua 读全局 arg（main_lua.c 只在 -a 时设置 S4.arg）；多余的 argv 会被当作脚本文件加载；SetDiscretizedEpsilon 不存在（实名 UseDiscretizedEpsilon），被 if 静默跳过。
- K-3：fmm_FFT.cpp:75/83 的 S4_malloc 在 PolBasis 之前执行，所以 jones/nv/vl 三族的 s4malloc nth=1 都会落在 fmm_FFT。
- K-4：E2E_API_SURVEY 的不可达结论有误：ClosedForm 是默认路径（S4.cpp:2421-2422）；Kottke 可以通过 SubpixelSmoothing / UseSubpixelSmoothing 到达；Lua 有 UseExperimentalFMM（Python 没有）；Lua 在 REPL 模式下出错不退出。
- K-5：judge_maketest_r9m3a_v3.py 丢掉了状态写在下一行的 docstring 单元。日志写 Ran 257，表里 s4test 只有 167 个单元。
- K-6：M3a 报告 §5 写了 /tmp 写入，但表一写"无"。
- K-7：judge_e2e_r9m3a.py 中 Lua 的 visible 条件含 len(stderr)>0，被 WITNESS 行满足，恒为真；posctrl 的 synthetic() 对 Lua 返回 None，没有覆盖 Lua。
- K-8：PREREG fft 行的选项和装置不一致（装置多设了 PolarizationDecomposition=True）；报告 §10 的编号是 1/2/4/3、§11 小节标题写成 10.1、§3 写 STATE 5062。
- 另外把 U334–U337 对应的事实各登记一条勘误。

## 4. 工作项
### S-B make test 只读重解析（不运行 make）
1. 新建 judge_maketest_r9m3b.py（不改 _v3）。读 m3a 证据目录下 maketest/{B,F4}_p{1,2}.log（只读）。unittest 单元按"test_x (mod.Class.test_x)"这一行，加上同一行或之后**直到下一个单元行为止**的第一个状态词来识别；状态词包括 ok/FAIL/ERROR/skipped/expected failure/unexpected success。
2. 对账断言（每遍、每树）：s4test 识别到的单元数 = 该段 "Ran N" 的 N；skipped 数 = "OK (skipped=k)" 里的 k；test_python_binding 段同样处理。不相等就报 FAIL，不得调整。
3. 阳性对照：在 $EV/posctrl/maketest/ 下落盘篡改副本（把一个 docstring 单元的 ok 改成 FAIL、删除一个单元行），调用正式脚本，应分别判出 NEW_FAILURE 和对账 FAIL。
4. 输出 MAKETEST_UNITS_R9M3B.tsv、MAKETEST_VERDICT_R9M3B.tsv（判据同 U333a）。

### S-C E2E 修订（试跑期）
1. 调研 v2：E2E_API_SURVEY_R9M3B.md，全部标注 [源码]。可达点族至少包括：
   - CF：默认选项 → FMMGetEpsilon_ClosedForm → s4malloc（fmm_closed.cpp:40）；
   - FFT：DiscretizedEpsilon=True、PolarizationDecomposition=False → plan / exec / s4malloc（fmm_FFT.cpp:75 或 83）；
   - KT：DiscretizedEpsilon=True + SubpixelSmoothing=True → plan / exec / s4malloc（fmm_kottke.cpp:87）；
   - JONES / NV / VL：DiscretizedEpsilon=True + PolarizationDecomposition=True + 对应的 Basis → s4malloc 打在 **PolBasis 文件内**的站点；
   - EXP：只有 Lua，UseExperimentalFMM → s4malloc（fmm_experimental.cpp:40）。
   不可达或只能靠 seam 的族，列出理由与 M1/M2 覆盖行，写进 COVERAGE_E2E_R9M3B.tsv。
2. 构建：在 $EV/trees/E2E_F4 中用新的 build_e2e_r9m3b.py 重建，链接参数与 M3a 相同。产物 sha 与 M3a 的 E2E_BUILD_R9M3A_v2.tsv 比对，相同或不同都照实记录。nm 核对 4 个 __wrap_ 符号。
3. 校准（注入无关，必须先于预注册）：对每个"前端 × 点族选项组"做无注入运行，用 gdb -nx -batch 在 __wrap__Z9S4_mallocm、__wrap__Z15fft_plan_dft_2d…、__wrap__Z13fft_plan_exec… 上打断点，记录调用序号、size（S4_malloc）和 bt 第 1 帧的函数名，写 CALIB_E2E_R9M3B.tsv。gdb 的命令文件放 $EV/tmp/。每个 s4malloc 点的 nth 取"目标文件内第一次 S4_malloc 的序号"，并同时记录该序号对应的 size。
4. Python 装置 e2e_python_r9m3b.py：
   - 参考值由运行器**另起一个无注入进程**得到；
   - 注入进程依次做：A 注入（进程内第一次求解）→ B 同对象重试（先 os.environ.pop 注入变量）→ C 同进程全新对象；
   - 运行器再起一个无注入进程，作为"全新进程重试"（R2）；
   - 输出 GetPowerFlux("Bottom") 的 4 个实数，以及异常类型和文本。
5. Lua 装置：
   - 批处理 e2e_lua_r9m3b.lua：参数用 S4_e2e -a "<spec>" e2e_lua_r9m3b.lua 传入 S4.arg；选项使用真实存在的方法（UseDiscretizedEpsilon、UseSubpixelSmoothing、UsePolarizationDecomposition、UseJonesVectorBasis、UseNormalVectorBasis、UseExperimentalFMM、SetResolution），方法缺失时报错退出，不得 pcall 静默跳过。
   - REPL 版 e2e_lua_repl_r9m3b.txt：通过 stdin 送入，每行少于 200 字节，只用全局变量。依次做：建模 → 求解（注入一次性命中）→ 打印结果 → 同一对象再求解 → 打印结果。期望：stderr 出现 "GetPoyntingFlux: " 开头的错误文本，第一次求解的返回值为 nil，第二次求解等于参考值。
6. 判定器 judge_e2e_r9m3b.py：
   - Python 与 Lua（批处理、REPL）分别判定；
   - visible 判据必须是具体错误文本：Python 为 RuntimeError 且文本含 "GetPowerFlux"；Lua 为含 "GetPoyntingFlux: " 的行，WITNESS/HIT 行不算；
   - 增加 HIT_OFF_TARGET 类别：HIT 行的序号和 size 必须等于 CALIB 记录的值；
   - 类别：E2E_OK、API_SILENT、RETRY_DIFF、RETRY_FAIL、INVALID、HIT_OFF_TARGET、FLAKY、CONTROL_OK、CONTROL_BAD。
   - 阳性对照：在 $EV/posctrl/e2e/ 下落盘篡改的记录文件（覆盖 Python、Lua 批处理、Lua REPL，每个类别至少 1 条；FLAKY 用两个落盘的 run 文件），调用正式脚本，输出 POSCTRL_E2E_R9M3B.txt。禁止常量自证。
7. 预注册 PREREG_E2E_R9M3B.tsv（状态 INFLUENCED；写好立即记录 sha 和 UTC 时间；在此之前不得有任何注入运行）：
   - 注入点：Python 覆盖 CF-s4m、FFT-plan/exec/s4m、KT-plan/exec/s4m、JONES-s4m、NV-s4m、VL-s4m（10 点）；Lua 批处理覆盖上述 10 点加 EXP-s4m（11 点）；Lua REPL 覆盖 FFT-plan、CF-s4m、KT-s4m、VL-s4m（4 点）。
   - 无注入对照：每个"前端 × 选项组"1 行。
   - 列：point_id、frontend（py/lua_batch/lua_repl）、选项、inject_mode、nth、目标文件:行、校准 size、exp_hit=1、exp_visible（具体文本模式）、exp_retry_same、exp_retry_fresh、tolerance、对应的 M1/M2 K 组。
8. 预注册写好之后，可以在 shakedown/ 里试跑注入点，用来调试装置。试跑结果不算数；exp_visible、exp_retry_* 一律不得改。如果发现 nth 或目标错误，只能写 PREREG_E2E_R9M3B_ERRATA.txt 说明原因，不改原文件。
9. 所有前端都必须冒烟：无注入对照行 Python、Lua 批处理、Lua REPL 各跑通一次。end 门禁用 --commit-i HEAD 试跑，并逐项打印 POST_I 块的每一项；report_check 对报告草稿跑通；STATE 草稿 ≤ 8192 字节。

### S-D 冻结期
run_e2e_r9m3b.py formal 运行两遍（pass1、pass2，可以分段续跑）→ judge_e2e_r9m3b.py posctrl → judge_e2e_r9m3b.py formal（读两遍结果）→ judge_maketest_r9m3b.py formal → 收尾（§1-7）。按 U333d：出现 API_SILENT 或 RETRY_DIFF/RETRY_FAIL，登记新红点（RED_POINTS_LEDGER_APPEND_R9M3B.tsv），本阶段不改 S4/；FLAKY、INVALID、HIT_OFF_TARGET 照实列入"需用户裁决"。

## 5. 顺序
start 门禁 → 裁决追加（U334–U342）→ K 项复核与勘误追加（E9-46..）→ S-B → S-C1..S-C9 → 冻结清单 FROZEN_SCRIPTS_R9M3B.tsv（至少包括 run_e2e、judge_e2e（posctrl 与 formal 各算一项）、judge_maketest、closeout、report_check、copy_registries、events、sha_sums、gate；PREREG_E2E_R9M3B 与 CALIB 两个文件记录 sha）→ start 前缀复核（只检查只追加文件的前缀 sha 与开工值一致）→ 记录提交 (i) → 冻结期 S-D → 收尾提交 (ii)。每完成一个阶段，向 $EV/PROGRESS_R9M3B.txt 追加一行（用固定小脚本）。

## 6. 报告结构
门禁 → K 项复核 → 裁决与勘误 → make test 重解析（4 遍对账：识别数 vs Ran N）→ E2E 调研 v2 与 COVERAGE → 构建与 sha 对照 → 校准 → 预注册（点数、sha、UTC、ERRATA 如果有）→ 试跑摘要（含全部前端冒烟、POST_I 逐项执行情况）→ 正式两遍结果（逐点类别、FLAKY、红点）→ 台账一致性 → 事件两张表（表一含 U338 补登记）→ 需用户裁决 → 交付物清单（条目不加反引号，项数与 SHA256SUMS 一致）。结尾写"本轮已完成/未完成 R9 M3b 范围，等待用户审核"，附 git log -1 与 git status --short。

## 7. 硬停止
开工门禁不符；写入越界或改动已提交文件；预注册之前运行了任何注入点；修改了 S4/、判定器或历史装置；冻结期新建或改写 testing/d003 下的文件。
