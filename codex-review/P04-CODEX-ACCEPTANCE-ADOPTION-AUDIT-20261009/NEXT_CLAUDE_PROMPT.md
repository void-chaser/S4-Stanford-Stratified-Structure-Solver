# 下一阶段：D001/D002 最小生产集成与可提交回归

请直接执行，不只回复计划。建议将本提示词发送到新的 Claude 会话。本正文由用户实际发送后，授权隔离源码开发、必要 clean build/native targeted 回归、形成可审查提交与推送 codex/ 开发分支、创建 draft PR；不要把磁盘正文冒称真实用户授权。完成工程与自检后交独立审核，满足关闭条件再关闭对应 issue/milestone；不合并 master，不进入 P05。

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

明确区分：当前是隔离候选通过，生产 102 项未采纳，D001/D002/P04 OPEN。原始 D002 历史 provenance 未知保持。旧 RUN/原报告/first-freeze 全部只读。

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

## 5. GitHub、审核与关闭

远端 master 是默认分支，既有 checkpoint 分支 BASE 不改写。推送新的 codex/ 开发分支，建立 draft PR，说明每项修复、实际验证和剩余边界；审核前仅使用 References #1/#2，避免自动关闭关键字。

README/路线图/当前 registry 更新必须按证据区分 implemented、targeted complete、pending independent production acceptance。不改 legacy DEFECTS 的编号或用户已有内容。提供独立审核 handoff：精确源码 commit、diff、命令、原始结果位置、必要覆盖表。不得将执行者自检冒称独立审核。

逐项关闭：各 issue 在自己的约定有限范围内完成产品修复、提交版本验证、独立审核并记录 Git checkpoint 后即可关闭，不等待全部项目修复。D001 先满足就先关闭 #1，D002 未满足则 #2 保持开放；不以一个结果替另一项验收，也不要求 D003–D015 完成。两个 issue 可共享阶段审核和 checkpoint，不增加每项独立整链。二者关闭且 P04 阶段验收通过才关闭 P04（number 1），不等待 P05–P14。本会话如果没有所需审核结果，明确停在 pending independent review；不要为了“全部完成”自行签收。P09/P12/P14 无 issue 不等于阶段完成，不关闭。

## 6. 完成与停止条件

交付应是可恢复的最小产品改动+正常测试资产+准确提交版本验证+远端开发 PR。完成这些后停止，不启动 P05、不合并 master、不生成另一份控制器/后继对象。

遇到具体阻塞时，给出唯一失败命令/输入、原始 stderr/exit、owner 和最小下一动作；保留已完成成果，不重复重读所有旧报告。没有原生结果不能写生产关闭，已披露边界也不能自动升级为无限任务。
