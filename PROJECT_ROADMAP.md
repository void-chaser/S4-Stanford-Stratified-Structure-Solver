# S4 项目执行路线与计划表

更新：2026-10-10（Australia/Sydney）。下一次工作从本文、[P04 当前交付状态](checkpoints/p04/CURRENT_STATUS.md) 和 [当前缺陷登记表](testing/s4test/ISSUE_REGISTRY.md) 开始；主线为 **P05/D003**，再 P06/D004。
2026-10-10 更新只同步 P01–P04 的状态与当前入口：P01–P04 的有限范围关闭以已有证据为准，未启动 P05，未合入或推送 Master，未关闭 GitHub issue。
表中“待执行”仍表示尚无该阶段运行结果；“已完成”只指该行目标已满足。

## 1. 当前基线与目标

基线提交：963ccf153855734de968e6cf71477f324e33329c。
分支：checkpoint/014rf-offline-evidence-accepted-20261003。
本轮只读 Git 观察：该分支与本地 origin 跟踪引用一致，生产 tracked 文件无未提交修改；audit-workspace/、handoff/ 是既有 untracked 目录。
没有重新联网 fetch，不将本地跟踪引用状态冒称远端的实时核验。

[014RF checkpoint](CHECKPOINT_014RF_LIMITED_OFFLINE_EVIDENCE_ACCEPTED.md) 和 [最新独立复核](checkpoints/014rf/FINAL_REVIEW.md)
接受的是有限离线证据重建/签收链。保留这一结论并结束 014RF 修复循环。
本 checkpoint 保存源码、测试和摘要，不代表 D001/D002 生产关闭或全项目科学认证。

下一主目标：让用户经 S4 公共 API 调用时，物理等价输入给出经独立参考核验的等价结果；随后修复状态、错误传播、构建安装和资源/API 契约。
历史独立审核 010/011 已支持四行逆平衡候选在有限均匀膜矩阵中的物理效果，不能把它写成“从未做过真实物理验证”。
当前生产文件仍保留旧索引，因此要完成的是当前源码的验证、候选集成和集成后回归。

## 2. 对原规划的取舍

| 原建议 | 采用方式与理由 |
|---|---|
| 风险 + 依赖关系排序 | 采用。D001 优先；D003/D004 控制核心状态；D005/D006 保证交付可复现 |
| 014RF freeze + checkpoint | 阶段已有接受结论和提交，不再另造冻结/封存系统；只补下一阶段必需的可恢复输入 |
| D001/D002 同属 Phase 1 | 同阶段、分验收。D001 看公共 API 物理量；D002 看真实 RNP 内存/返回状态，不能用一个结果替另一项关闭 |
| original/candidate/reference 比较 | 保留。“original”是未改基线，“candidate”是最小生产改动，“reference”是独立 Airy/TMM；旧 binary 只用于历史交叉核对 |
| 继续大量均匀膜采样或 validator | 收益低。复用 010/011 的有限成果，优先当前构建、调用路径和未覆盖边界；确有判定漏洞才局部修工具 |
| D005/D006 等到 Phase 2 | 完整修复照此安排，但 Phase 1 前必须有隔离 clean build 和加载身份记录；若无法可靠执行则最小解除构建阻塞后再继续 |
| P1/P2 按批次集成 | 采用。批次是集成边界，每个缺陷仍保留可审查的最小改动与 targeted regression |
| 每项都做大型 E2E / 独立审核 | 改为每项 targeted + 相邻路径检查，阶段才做完整集成和独立复核；P0 和实质内存风险按需要增加验证 |
| D014 最后处理 | 最终安装文档/example 验收放最后；改变异常/API 契约时同步必要的 docstring/简短说明，避免阶段内误导用户 |
| D012 实现、报错或移除 | 默认明确 unsupported，避免为了关闭静默 no-op 引入并行实现的大项目；真正并行需求另定范围 |
| 所有历史 D002 来源再追查 | 不作为主线。使用 D002 (current working registry definition)，历史 provenance 未知保留 |
| D001 关闭要求“全域证明” | 不采用无限条件。先固定可执行的生产覆盖矩阵，关闭已复现缺陷并明确未覆盖范围；重大已知反例不能用缩小范围绕过 |

## 3. 可以逐项推进的主计划表

状态：**已完成**只指该行目标已满足；**待执行**尚无本阶段运行结果；**待阶段验收**表示 targeted 实现完成后还需集成证据。
Pxx 是计划步骤，不是优先级、缺陷号或历史 Task 号。

| 步骤 | 阶段 / 项目 | 具体动作 | 验收和交付物 | 前置条件 | 当前状态 |
|---|---|---|---|---|---|
| P00 | Phase 0：基线与编号 | 采用 963ccf1 checkpoint；区分当前 D001–D015、legacy D1–D15 和审计 Task 号 | 本路线图 + 当前登记表；014RF 接受边界保持 | 无 | 已完成（本轮文档） |
| P01 | Phase 1 前置：恢复与构建 | 从基线建立新的隔离源码目录；核对 D001 四行候选、最小原失败输入、独立公式及必要 D002 用例；把必要源码/patch/输入纳入可恢复交付 | 新环境不依赖整份 audit-workspace 或旧 .so；明确实际 flags、源提交/patch、库/extension 路径及哈希 | P00 | 已完成（有限前置）：D001 四行候选 44f4a09；最小原失败输入 `testing/d001/cases/d001_first_matrix.json`；独立参考 `testing/d001/oracle_d001*.py`；D002 PLAN `testing/d002/PLAN.json`；补丁 `checkpoints/p04/review-inputs/patches/`。流水线 `testing/p04_run_all.sh` 从 Git 树与 963ccf1 归档构建并记录 ARTIFACTS.sha256。新 clone 的正式复验见执行者自审报告 |
| P02 | D001：当前生产反例与候选 | 用相同 flags 新构建 baseline/candidate；先看 baseline 的 A/B/C，再比较候选和独立参考；保留原始 flux/G/R/T | baseline 复现已知 N9 B/C 错误；candidate 修正且 A/N1 控制不退化；最小差异、原始结果与常规回归测试 | P01 | 已完成（有限范围）：2026-10-09 实现并定向验证（分支 codex/p04-d001-d002-production-20261009T082631Z @ 8b13d67），baseline N9 B/C 复现，candidate 修正；2026-10-10 随 P04 固定候选 5cf534c 经 Codex 最终生产技术审核接受并有限关闭（`checkpoints/p04-final/FINAL_REVIEW.md`）。D001 范围限制见 ISSUE_REGISTRY |
| P03 | D002：RNP 两类契约 | 分开处理 backtransform 边界/布局和仅值返回状态；复用既有候选/保护，缺什么补什么；核对左右/仅值路径和工作区 | 真实 native RNP 入口 targeted；相关 ASan/UBSan、必要 leak 检查及阳性对照；错误状态不会变成成功；明确生产可达性 | P02 初步结果；共用文件改动可审查 | 已完成（有限范围）：native RNP 契约 ord 53/53、asan 53/53、seam 58/58，阳性对照通过；必要 leak 按负责人 B 保存证据验收，非独立动态 LSan 认证；随 P04 固定候选有限关闭。历史来源不补证。2026-10-10 执行者自审修正 asan_baseline 的 A-36 判定（may_fail 加注册站点），尚未经独立审核，见 `testing/d002/evidence/A36_RULE_CORRECTION.md` |
| P04 | Phase 1：生产集成验收 | 将通过的最小修复集成到工作分支并全新构建；经 Python、Lua 和相关 C/RNP 路径复验；跑既有主套件 | D001 生产物理矩阵通过；D002 原生契约通过；相关历史回归无新增失败；独立复核后记录源码提交和关闭范围 | P02、P03 | 2026-10-10 有限范围 CLOSED：固定候选 5cf534ce5ec223a6388d29bbb2c58f981f070241 经 Codex 最终生产技术审核接受（checkpoints/p04-final/FINAL_REVIEW.md）；必要 leak 行1–4按负责人B保存证据验收，非独立动态LSan认证。负责人批准后采纳于 codex/p04-adoption-20261010，采纳SHA为上述固定候选；范围与限制见登记表。P05未启动。 |
| P05 | Phase 2 A：D003 | 核对现有六文件 FMM 候选和 checkpoint 差异；针对实际启用的 FFT/Jones/NV/VL 等分支完成失败传播/清理/重试验证 | 每个受影响的 prepare/execute 点有正负对照；失败后模式/缓存不安装；Python/Lua 可见失败，恢复重试正确 | P04；固定选项、全新对象避免依赖 D004 | S1–S4 已由用户签收（带范围声明，见 checkpoints/p05/P05_S3_S4_SIGNOFF.md 第 2 节）；S5 收口轮 R3：F4 上 make test / E2E 42 点 / D016 重跑（MATCH=33 MISMATCH=0 FLAKY=0），验收映射见 checkpoints/p05/registries/s5r3/P05_ACCEPTANCE_MAP_S5R3.tsv（等待用户审核）；（ES5-9）S5R4 收口补齐：独立重判 DIFFS=0（E2E 42 点、D016 33 行为点 + ROOT_CAUSE_RC 记 NOT_JUDGED_SOURCE_RECORD）、S5R3 end 门禁 8 项 FAIL 全消解、readiness GAP=0、S5R3 registry 26/26，见 checkpoints/p05/P05_S5R4_REPORT.md 与 registries/s5r4/（等待用户审核）；（ES5-15/16）S5R4 正式 end 门禁 1 项 FAIL 为检查器字符串缺陷，FINAL_STATUS=INCOMPLETE；S5R5 在 R4 冻结数据上修正重判并以 end 门禁 36/36 FINAL_STATUS=COMPLETE 收口，见 P05_S5R5_REPORT.md 附录 C；P05-S5 等待用户签收；P05-S5 已由用户签收（U391，见 checkpoints/p05/P05_S5_SIGNOFF.md），P05 有限范围收口 |
| P06 | Phase 2 A：D004 + core smoke | 修正 solve 后 SetOptions 的失效/状态契约；测试同对象和全新对象一致，再测 D003 失败→改选项→重试组合 | targeted + D003/D004 core smoke；原生产物理回归仍通过；两缺陷各有最小 diff | P05 | 待启动（前置 P05 已签收） |
| P07 | Phase 2 B：D005/D006 | 先修增量依赖/重新链接，再修 clean wheel/editable/sdist；从只含提交文件的新 clone 构建安装 | 增量可观测改动确实进入产物；安装矩阵通过；源码目录外加载正确安装模块并跑独立解析物理 smoke | P06；D013 若构成阻塞在本步提前处理 | 待执行 |
| P08 | Phase 2 C：D007/D015 | 分别修 Python 几何初始化、非网格文件导出错误；各自 targeted 后跑 geometry + I/O smoke | fresh Python 初始化与独立几何预期；打不开/写失败/close 失败明确报错且正确释放；正常输出保持 | P07；几何若阻塞前期测试则提前处理 D007 | 待执行 |
| P09 | P1 integration checkpoint | 从提交状态新构建并运行主套件、物理 smoke、核心错误恢复、安装/导出检查 | P0/P1 关闭项与范围、准确 pass/fail/skip、独立复核、Git checkpoint | P04、P06、P07、P08 | 待执行 |
| P10 | Phase 3 A：D008/D010/D011/D013 | 逐项处理转换/警告、setter 返回、厚度规则、metadata；每 2–3 项做 API integration smoke | API 正负契约和失败后状态一致；C 返回值有效；metadata 有依赖证据；必要 docstring 同步 | P09；D013 可能已在 P07 完成 | 待执行 |
| P11 | Phase 3 B：D009/D012 | polygon 资源路径专项；Python SolveInParallel 先消除静默成功，按 unsupported 契约回归 | 内存路径 targeted + sanitizer/成功对照；调用 unsupported API 明确抛异常；不声称已实现并行 | P10；若 D008 的最小修复同时解决 polygon 泄漏，则合并实现、分别验收 | 待执行 |
| P12 | P2 integration checkpoint | 汇总 P2，运行完整 API smoke + P0/P1 关键回归；复核失败清理/异常与安装 | 无新增回归；变更契约清楚；独立复核和 checkpoint；registry 按证据更新 | P10、P11 | 待执行 |
| P13 | Phase 4：D014 | 校正实际支持平台的安装说明；让 C API example 使用当前头文件/库；梳理文档入口与历史说明 | 文档命令可复现；C example 编译运行；没有用过期测试计数冒充当前状态 | P12 | 待执行 |
| P14 | release candidate | 新 clone/环境完成 build/install→公共 API 物理结果→全套回归；对实际支持配置复验 | 发布候选提交、简短验证摘要、已知限制/剩余项；达到明确范围的 release readiness | P13；范围内缺陷关闭或有明确处理决定 | 待执行；发布/合并另按用户要求执行 |

固定主线：P01 → P02/P03 → P04 → P05/P06 → P07 → P08 → P09 → P10/P11 → P12 → P13 → P14。
同阶段共享代码按顺序协调，不能仅因编号同组就把多项改动混成不可归因的补丁。
遇到确定依赖，只提前最小必需工作并在此表登记原因；不会重排整条路线去追零散低优先级问题。

## 4. Phase 1 的具体生产关闭范围

### D001：先接续已有成果，再补相邻边界

首轮复用既有反例的完整模型参数，不能只照抄频率、N 或材料名字。
三种表示必须由测试确认物理等价：同材质 region 不改变介电函数；tensor 为该 scalar 的各向同性表示。
保留实际 G 列表和原始 flux，R/T 的符号/归一化复用已记录约定。

第一道检查采用 f=0.427、N=1/9、s 偏振、A/B/C；重复在独立进程中执行。
这是新提交/新构建的回归，不重开旧 004/010/011 的封存与历史认证。
通过后扩展既有 f=0.173/0.733、s/p、N=1/9 的场景，并加入少量明确非截止的斜入射/较大 basis 和实际使用的内存模式。
同材质 region 是均匀物理模型，不能拿真实非均匀结构与同一解析膜参考直接比较。

独立 Airy/Fresnel/TMM 必须仅从输入参数计算，不能从 S4 输出生成答案。
已认证的正入射有限矩阵沿用纯绝对误差 1e-10，不因候选结果调整阈值。
新增物理模型在运行前确定适用公式与阈值；discretized/polarization 等近似选项需先确认等价条件和收敛判据。
守恒 R+T≈1、重复一致、A/B/C 相等都只是辅助检查：004 的错误 B/C 本身仍守恒，必须同时检查独立 R/T。
当前实际值与旧报告不一致时先查输入、路径、构建和源码差异；保留失败，不直接放宽容差。

首轮通过后的 P04 验收必须针对最终集成版本重新执行。
Python 是主要用户路径；Lua 验证共享核心，C/RNP 补 API 和原生边界。
三个前端共享核心，所以跨前端一致性不能替代独立物理参考。
满足矩阵、相邻回归和相关原生安全检查后，关闭“已复现等价表示缺陷”，明确覆盖范围，不宣称所有材料/参数的数学证明。

### D002：内存安全与状态传播分别验收

候选触及左右逆平衡索引时，应有真实 native 左/右分支边界检查。
S4 当前 rcwa 路径传入 vl=NULL；公共 RNP 左向量可用直接 native 驱动验证，不能伪造“生产 S4 实际调用了左分支”。
布局检查覆盖小 n、空/单元素活动区间、上下置换、实际 stride/padding、caller/internal workspace 和 NULL optional outputs。
只测人工加大 allocation 或 sentinel 没变不等于原生产布局安全；普通 R/T 正确也不能代替访问合法性。
ASan/UBSan 检查与地址/容量审查互补，若 sanitizer 对形成非法指针本身无诊断，要把盲区写明。

仅值分支需要证明算法失败状态被实际接收并由相关调用者处理。
可用确定的失败用例或明确标注的 test-only seam 触发状态；不能只检查源码新增了赋值。
极端 scalea 全矩阵缩放与 backtransform 的非单位 scale[] 是不同覆盖项，不互相代替。
若该范围发现可达重大错误，按实际风险阻止该项关闭；尚未认证的扩展范围单独登记，不无限扩张 Phase 1。

Phase 1 后只标明各已验证范围的关闭结论；D002 原始历史 provenance 仍保持未知。

## 5. 后续阶段的执行与验证节奏

每个缺陷按同一流程：**最小 reproduce → 最小 fix → targeted regression → 相邻 integration**。
阶段末：**E2E → 独立复核 → checkpoint**。
原有测试优先复用；新增测试针对实际缺口，不为低影响文案或单纯实现细节复制测试。

已有主要入口：Makefile.common 的 make test、testing/s4test、testing/fmm-runner。
使用前核对当前入口、依赖和运行范围，计划中的命令不冒称已执行。
make test-python 会删除构建产物，应只在隔离开发/验证目录运行，避免覆盖另一任务的产物。
历史 122、257 等测试数字仅属历史版本；后续实际统计 total/pass/fail/skip/expected failure，不把 skip 算作通过。
每个 skip 列理由和影响；范围内必需测试缺依赖时不能靠 skip 通过验收。

阶段 smoke 的最低内容：

| 验收点 | 必须保留的路径 |
|---|---|
| P04：科学主线 | D001 的独立 R/T；D002 原生边界/返回状态；two-layer、cutoff 安全、clone、频率失效等相邻历史回归 |
| P06：核心状态 | 固定选项下 FFT 正负分支；失败清理→恢复重试；SetOptions 热对象与新对象一致 |
| P07：交付构建 | 增量核心/头文件/binding 改动；wheel/editable/sdist；新 clone + 源码目录外 import/解析物理 smoke |
| P08/P09：P1 集成 | geometry 独立预期；正常导出与 I/O 错误；完整主套件及 P0/core/package 关键检查 |
| P12：P2 集成 | conversion/warning、C callback、厚度、polygon 资源和 unsupported API；P0/P1 关键结果 |
| P14：release candidate | 已声明支持的构建配置、安装方式、公共 API 物理回归和全套工程回归；已知边界披露 |

每项只需留下：提交/patch、复现输入、实际命令和 flags、退出码、加载路径、必要原始输出、简短判定。
结果日志放新的运行目录，不覆盖旧证据；把可复用测试和最小 reference/input 放到正常版本控制路径。
不整体提交历史 audit fixture，不重跑封存索引，不新建递归 manifest/预算/签收控制平台。
工具缺陷真的妨碍判定时局部修复并保留对应反例，修好后回到 solver。

失败时暂停依赖该结果的后续步骤，判断是源码、输入、环境还是测试装置；不自动扩大任务。
P02 baseline 不复现时不能直接宣布 candidate 修复成功；P07 新 clone 失败时不能用开发目录已有 .so 替代。
同一阶段 reviewer 可以离线复算关键原始值和审查 diff，必要时从源码独立构建；不必对每个小缺陷都复制历史大控制循环。
独立审核作为后续交付环节，本轮没有委派审核，也不把执行者自检当成独立结论。

## 6. 主线之外保留的已知边界

下列事项不是通过这十五项就自动完成。执行阶段发现其影响当前发布范围时，再按实际风险建立独立工作项：

- 精确衍射截止点：现有“安全报错/非有限拒绝”与可信物理极限解分别记录（见 legacy D10）。
- VL NB1 的既有非有限现象：P05 核实是否可达当前支持选项；若形成普通输入下的新重大反例，提升为核心阻塞项。
  - 2026-10-11 P05-S1R 更新（提前登记，P05-S5 时核对；依据 `checkpoints/p05/P05_S1R_O1_ATTRIBUTION.md`）：VL 基在 `n_G=1`（NumBasis 1–4）下确定性失败（`info=2`，错误码 20），B/A/H 三树一致，是显式报告而非静默错误数值。根因是图案层向量场归一化遇全零场时除零得 NaN 且仍返回成功。已按用户裁决拆为两条：
    - **D016**（已实施，归 D003 失败传播范围）：零场除零不应静默产生 NaN，应在根因处返回错误。修法已实施（P05-S3R2 提交 3e77aa9；F4 pattern.c 2210–2216，[源码]）。2026-10-18 P05-S5 R2 在 F4 上用 Python/Lua 公共 API 实测：在 F4 上、在该输入下经公共 API 可见失败且恢复正确（U365）；正式两遍 MATCH=31、MISMATCH=2、FLAKY=0；MISMATCH=2 为比较器格式缺陷（ES5-6），行为点全 MATCH；S5R3 重跑结果见 checkpoints/p05/registries/s5r3/D016_VERDICT_S5R3.tsv（MATCH=33 MISMATCH=0 FLAKY=0）；见 [登记表](testing/s4test/ISSUE_REGISTRY.md)。；（ES5-9）2026-10-18 P05-S5 R4 独立重判（U379）对该判定表重判 DIFFS=0（33 行为点全 SAME，ROOT_CAUSE_RC 记 NOT_JUDGED_SOURCE_RECORD），S5R3 数据 sha 不变；见 checkpoints/p05/registries/s5r4/REJUDGE_S5R4.tsv。
    - **R-P05-01**（OPEN，经 U366 转出 P05，不阻塞）：让 n_G=1 可计算需先确认 allzero 到 1x1 的设计意图并取得独立参考解；反事实通量与 allzero 设计意图保持 OPEN，写进 S5 范围声明；见 [登记表](testing/s4test/ISSUE_REGISTRY.md) 的 R-P05-01 行。
  - 2026-10-18 P05-S5 R2 登记（U366，转出 P05，不阻塞）：F10 历史因果（S5-B-01）保持 OPEN，详见 checkpoints/p05/P05_S5_OPEN_ITEMS.tsv。
  - 2026-10-18 P05-S5 R2 登记（U367）：F8 历史目录（S5-B-02）不授权访问，保持未验证。
  - 2026-10-18 P05-S5 R2 登记（U368）：S1 报告 11.2 的五个哈希来源（S5-B-05..09）认定为无法判定，不改写 11.2 与 EVIDENCE.sha256；更正后的行号见 checkpoints/p05/registries/s5r2/ERRATA_S5.txt ES5-1。
- scalea 极端缩放、完整 RNP 左向量和更广材料/各向异性范围：仅登记实际覆盖，不能由有限膜样本外推。
- Python 初始化/深层 OOM、插值器已知 skip、其他 Lua 资源路径：按当前范围可达性和泄漏后果决定优先级。
- FFTW、真实线程/MPI、额外平台：需要声明支持配置；无法验证的配置不能写成已认证。
- 论文定量复现：属于更高层科学 benchmark，需要独立参数/参考与收敛设计，不作为所有 bug 的前置任务。

P14 之前重查这些已知边界：若属于声明支持范围内的重大错误则阻止 release readiness；否则明确限制/另列后续，不能靠“主表全关”隐去。

## 7. 后续如何对照执行

下一次从 **P05/D003** 开始，单次工作携带当前步骤、基线、涉及缺陷与验收条件即可；P05 先核对实际 FMM/FFT 失败传播和已登记 VL NB1 可达性，随后进入 P06/D004。
P01–P04 已有有限范围关闭记录，上表与登记表是其状态来源；这里不再把 P01 作为下一步。
不要求新的会话阅读整份 audit-workspace，也不让旧 S4_HANDOFF.md 的历史“下一轮”覆盖本文。

每完成一步，更新本表状态以及当前登记表的提交、证据和关闭范围。
各阶段 checkpoint 使用明确的源码提交锚点；新开发分支默认用 codex/ 前缀。
2026-10-10 同步不启动 P05，不合并或推送 Master；后续按用户要求执行具体阶段。

## 8. 本次规划依据

可在 Git 恢复的当前材料：

- [014RF checkpoint](CHECKPOINT_014RF_LIMITED_OFFLINE_EVIDENCE_ACCEPTED.md)、[FINAL_REVIEW](checkpoints/014rf/FINAL_REVIEW.md)、[PROVENANCE](checkpoints/014rf/PROVENANCE.json)。
- [Makefile.common](Makefile.common)、[setup.py](setup.py)、[Eigensystems.cpp](S4/RNP/Eigensystems.cpp)、[rcwa.cpp](S4/rcwa.cpp)、[Python binding](S4/main_python.c)、[S4 core](S4/S4.cpp)。
- [既有测试说明](testing/s4test/README.md)、[legacy 缺陷记录](testing/s4test/DEFECTS.md)。

以下历史审核/候选在本地未跟踪目录，仅支持本次范围判断；P01 应提取下一阶段必需的最小输入，不能假定 fresh clone 自带这些文件：

- [004 原反例审核](audit-workspace/codex-review/004/Execution_Review_004.md)。
- [007 逆平衡定位审核](audit-workspace/codex-review/007/Execution_Review_007.md)。
- [008 四行候选](audit-workspace/008/008-20261001T112902Z-ce38513c/CANDIDATE_FIX.patch)。
- [010 限定原生构建/物理审核](audit-workspace/codex-review/010/Task010控制审核/审核结论.md)。
- [011 两频率/两偏振有限科学审核](audit-workspace/codex-review/011/Task011控制审核/审核结论.md)。
