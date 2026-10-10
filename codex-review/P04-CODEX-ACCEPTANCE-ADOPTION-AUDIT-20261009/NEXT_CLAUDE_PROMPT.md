# 下一阶段：先完成 D001/D002 源码修复、验证与本地清理

请直接执行，不只回复计划。建议将本提示词发送到新的 Claude 会话。本正文由用户实际发送后，授权隔离源码开发、必要 clean build/native targeted 回归、形成可审查本地提交，以及第 5 节明确规定的缓存清除和历史产物整理；不要把磁盘正文冒称真实用户授权。

用户规定两个顺序明确的阶段：**第一阶段先把本轮审核发现尚未做好的工程事项修好，将最小修复纳入源码，完成验证并清理杂乱本地目录；第二阶段才进行 Git push 收尾并判断可关闭 issue/milestone。** 本提示词执行第一阶段。交独立审核后，Git push/PR 与关闭事项由后续发布收尾统一执行，本轮不提前关闭、不推送产品分支、不合并 master、不进入 P05。

## 1. 唯一起点及现有结论

REPO=/home/jackal/nvme_ssd/projects/S4-Stanford-Stratified-Structure-Solver
WORK=REPO/codex-review/P04-CLAUDE-RECOVERY-DIAGNOSTIC-CLOSEOUT-20261009T071842Z-d5f1a3
ACCEPT=WORK/native-acceptance-20261009T075603Z
PKG=WORK/package
RUN=PKG/object-RUN
REVIEW=REPO/codex-review/P04-CODEX-ACCEPTANCE-ADOPTION-AUDIT-20261009
BASE=963ccf153855734de968e6cf71477f324e33329c
REMOTE=https://github.com/void-chaser/S4-Stanford-Stratified-Structure-Solver.git

统一 /home 与 /srv 的 realpath。先读 REVIEW/REVIEW.md、本文件、ACCEPT 的两份 Markdown、PROJECT_ROADMAP.md 的 P02/P03/P04 和关闭范围、testing/s4test/ISSUE_REGISTRY.md 的 D001/D002。按需读取工程补丁与对应源码，禁止全库历史考古。只读 GitHub #1/#2 当前验收要求，生成简短 coverage 表。

接受已有结论：137=132+2+3；D001 106 raw 独立参考通过；D002 注册的 48 条数值/消费链通过；SHIM 首次身份一致；内层 FINAL 25/25。不要重复修这些已完成任务，也不要重新生成授权/预算/冻结控制平台。

明确区分：当前是隔离候选通过，生产 102 项未采纳，D001/D002/P04 OPEN。原始 D002 历史 provenance 未知保持。提取和验证期间旧 RUN/原报告/first-freeze 全部只读；验证完成后按第 5 节整体整理归档，不篡改旧证据内容。

## 2. 隔离工程分支与最小代码

检查当前 HEAD/status，不覆盖用户 DEFECTS.md 修改或未跟踪资产。建立从 BASE 出发的新隔离 checkout 或 worktree，分支 codex/p04-d001-d002-production-<UTC>。若 .git 权限受限，可在允许写入的目录建独立 clone；不 reset/clean/stash 用户现场，不使用 git add -A。

核对 PKG/engineering/PRODUCTION_ENGINEERING.patch SHA256=1adef26caf8765eb9392091a26548cfce3318e4b9f82f6c1442cba07b621076e，与 LANDING_MANIFEST.json 对照。该补丁是已测候选来源，不等于获准整包 apply。按实际 diff 提取 A 类最小改动，不能机械按旧 hunk 行号修改。

第一批 D001：Eigensystems.cpp 左右 zgebak 的四行索引修复。第二批 D002：zhseqr info 接收、相邻 NULL z 指针偏移修复、caller/internal workspace 所有权、失败不安装 modes/缓存、错误码 20 沿 rcwa→S4→Python/Lua/C 的返回传播。相互依赖的共享修复可同分支，但分别列缺陷归因及回归。

保持 GetWaves 现有公共行为，本批不纳入独立 GetWaves 重写、geom 删除或对应新文档。cubature、死 ConvertUnits、SolveInParallel 清理等只有在实际 clean build 受阻时才引入必要最小改动，并列原因；不顺手关闭 D008/D012。

保留测试能力：S4_TEST_EIGEN_INFO 的 S4 传播 seam 与 D002_TEST_SEAM 的 RNP seam 是两种装置。可将 seam.h 移到 testing 并通过测试构建 include 路径引用，或建立等价 overlay；不要仅为了目录整洁删除上层注入点。普通构建禁止开启注入宏，验证正常库无注入行为。

产出可审查最小 diff、来源映射、测试构建方法。不复制 102 项全部改动，不整体提交 89 资产，不加入 runtime authority 或历史巨型 fixture。

## 3. 必要回归资产与覆盖缺口

将当前批次所需 driver、最小矩阵/spec/reference、Python/Lua 物理输入和简洁执行入口放正常 testing 路径。可复用现有源码，保证只含已提交文件的 checkout 可构建执行，无旧 .so、绝对旧 RUN 路径或旧账本依赖。

运行前固定输入/阈值/判据；沿用 D001 绝对 1e-10，D002 冻结的 eig/residual/vector-norm 阈值，不能按结果放宽。编译装置变化不得把实际容量人为放大来掩盖索引越界。

对 #1/#2 的必需条件逐项映射已有证据、最终版本需复验项和缺口。重点：

- D001：从现有 P02 明确文件读取 baseline 反例来源；最终版本重新验证 f=.427、N=1/9、s、A/B/C、独立进程重复及真实 G/flux。同 flags 的新 baseline/candidate 构建能复现 baseline N9 B/C 大偏差、candidate 修正且控制不退化。若已有 baseline 证据身份足够且源码一致，可有据复用并解释，无需历史整链。
- 按路线图完成 f=.173/.733、s/p、明确非截止斜入射、较大 basis、实际内存模式的有限集成覆盖。独立参考只从模型输入计算，跨前端一致/守恒不能替代 R/T 参考。
- D002：复用非恒等上下置换 helper/API case；真实左右分支、小 n、空/单元素活动区间、实际 ld/stride/padding、caller/internal workspace、NULL optional outputs。H-01/H-08 恒等置换不够。
- 分别测试非单位 backtransform scale[] 与 extreme scalea；报告实际覆盖，不互相替代。已有 n>75/N2 和短 rwork 探针按适用范围与风险处置，不把契约外输入升级为普通失败，不掩盖范围内重大错误。
- 仅值分支失败状态使用明确 test-only seam 或自然失败，验证 RNP 返回及 S4 上层可达路径、Python/Lua/C 错误码 20、失败清理、不安装缓存和恢复重试。query 调用的返回规则单列，不伪称所有调用路径都忽略错误。
- ASan/UBSan 带各自阳性对照；记录原始容量/地址布局及 sanitizer 盲区。真实 leak 相关路径按需要验证，不能吞 stderr、关闭检查或将非零强行计为成功。
- HAVE_LAPACK 默认未启用；以 #2 实际要求判断是否需要隔离 LAPACK 配置 targeted 验证。无法验证时列具体依赖与影响，不能宣称该分支已认证，也不能把它变成无限平台扩展。

这是新生产集成工作，不受上一次“只准离线”的限制；不需要新建旧门控平台申请 token。执行合理的 targeted→相邻回归→一次最终集成，失败按真实 owner 修复重测，只因新改动/新失败才扩大测试。

## 4. 最终提交版本验证

产品实现和测试资产准备完成后，提交明确最小源码/测试版本。用只含提交文件的新 checkout clean build，记录 compiler/flags、依赖、源码 commit、extension/Lua/driver 实际路径与 SHA。

在该版本运行 D001 生产物理矩阵、D002 必需原生契约、Python smoke、Lua harness/negative、相关 C/RNP、s4test 与相邻历史回归。test_structures 是 import smoke，不冒称 unittest。真实统计 ran/executed/pass/fail/skip，列唯一或新增 skip 的理由/影响，不能把 skip 算 pass。

保存简短执行报告、原始关键输入/输出和独立参考结果到新的运行目录。最小原始数据可纳入 checkpoint；大编译产物与历史现场不整体 Git 上传。一次源提交之后若改产品代码，必须重新验证受影响路径，报告明确绑定最后源码 commit；纯报告提交不冒称换了二进制。

## 5. 清理缓存、重复运行树和杂乱历史目录（必须实际完成）

用户明确要求减少本地目录噪声和旧产物误用风险，不能只回复“以后清理”。源码、复现输入和最小回归先落地并通过干净构建，之后完成整理。清理与源码改动分开记录，不通过改 solver 的运行缓存语义实现文件夹清理。

先做目录级清单，不递归逐条打印海量文件：列当前 build、Python/test 缓存、audit-workspace、codex-review、testing/phase1-*、旧 candidate/RUN/overlay/fixture 等的大小、用途、是否仍被当前执行路径引用、是否唯一副本。确认没有活跃任务正在使用待处理目录，不停止别人的任务。git status 中 DEFECTS.md 的用户修改及其他未识别手写文件保留。

按以下具体规则执行，不用 git clean -fdx 或无范围 rm -rf：

- **直接删除可再生缓存/产物**：已确认不被活跃任务使用的 __pycache__、pyc、pytest/mypy/ruff 缓存、旧 .o/.a/.so、失效 build/temp、重复临时 checkout。仅处理清单确认的具体路径；.so/驱动若仍为唯一验证身份依据，先保留相应最小证据与身份记录，不能误当普通缓存删掉。
- **将有价值历史数据移出日常工作目录**：原始反例、冻结账本、报告、唯一输入/补丁和需要保留的 raw 不当作缓存删除。把本阶段不再使用的历史 audit/RUN/变异 fixture 整理到单一归档位置，默认 REPO/.local-archive/p04-history-<UTC>/，保留原相对路径和原内容；不再次复制成多套候选/后继包。该隐藏归档目录加入 .gitignore，让默认 rg、Git 和正常源码工具不再扫描它。归档内不保留可丢弃的大型重复构建产物。若用户已有长期归档目录且权限允许，可改放那里并记录实际路径；不要把唯一证据放 /tmp。
- **保持正常仓库入口简洁**：正常 testing 路径只保留本批可复用测试，当前阶段保留一个简短报告/索引与必要原始结果。可以将当前需要的最小审核材料整理到 checkpoints/p04/；对旧目录使用索引映射，避免满仓库保留成百个同级历史根。
- **迁移后验证**：归档前记录被保留关键文件的 SHA/bytes，归档后核对；移动整树时只需合理的完整性检查，不新建递归控制平台。原报告的历史绝对路径不改写为新证据，清理索引明确 old→archive 映射及失效的历史 replay 路径。当前测试/构建入口必须不依赖被移走的绝对路径。
- **证明摆脱旧产物依赖**：对最终提交源码在不含 .local-archive、旧 .so 和旧 audit 树的干净 checkout 完成第 4 节验证。若这项验证已经由同一源码提交完成，只核对来源，无须无理由再跑全套。

交一份简短 CLEANUP.md：删除/归档路径、保留原因、前后目录大小、释放空间、仍保留的唯一证据、当前入口位置和未处理的具体阻塞。清理后工作区不能依赖归档才能运行当前回归。清理中如发现无法区分的唯一手写文件，保留该文件并准确列出，不因此放弃其余明确可清理项。

## 6. 独立审核与后续 Git push 收尾

远端 master 是默认分支，既有 checkpoint 分支 BASE 不改写。本轮交付可审查本地源码提交和独立审核 handoff，暂不推送产品分支、不创建产品 PR、不关闭 issue/milestone。源码修复、验证和清理完成并经复核后，后续 Git push 收尾统一推送新的 codex/ 分支、建立 PR，并依据届时证据决定关闭哪些事项。该规则不影响已有的文档 PR #16。

README/路线图/当前 registry 更新必须按证据区分 implemented、targeted complete、pending independent production acceptance。不改 legacy DEFECTS 的编号或用户已有内容。提供独立审核 handoff：精确源码 commit、diff、命令、原始结果位置、必要覆盖表。不得将执行者自检冒称独立审核。

后续发布时逐项判断关闭：各 issue 在自己的约定有限范围内完成产品修复、提交版本验证、独立审核并记录 Git checkpoint 后即可关闭，不等待全部项目修复。D001 满足而 D002 未满足时，发布收尾可只关 #1，#2 保持开放；不以一个结果替另一项验收，也不要求 D003–D015 完成。两个 issue 可共享阶段审核和 checkpoint，不增加每项独立整链。二者关闭且 P04 阶段验收通过才关闭 P04（number 1），不等待 P05–P14。本轮只记录判断依据，不执行关闭。P09/P12/P14 无 issue 不等于阶段完成。

## 7. 完成与停止条件

交付应是可恢复的最小产品改动+正常测试资产+准确提交版本验证+已完成的本地清理+可审查本地提交及独立审核 handoff。完成这些后停止，将 Git push 与关闭事项留给审核通过后的发布收尾。不启动 P05、不合并 master、不生成另一份控制器/后继对象。

遇到具体阻塞时，给出唯一失败命令/输入、原始 stderr/exit、owner 和最小下一动作；保留已完成成果，不重复重读所有旧报告。没有原生结果不能写生产关闭，已披露边界也不能自动升级为无限任务。
