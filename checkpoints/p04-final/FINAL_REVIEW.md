# P04 固定候选最终生产技术审核

审核日期：2026-10-10（Australia/Sydney，AEDT）。审核会话：本次独立 Codex 审核会话，与 Claude 执行会话分离。审核依据为本会话实际读取的候选源码、差异、原始保存记录、独立历史审核及本次独立复算；不是代抄执行者签收，也不代负责人签名。

**最终结论：D001 接受；D002 接受；P04 接受，均限下述冻结范围。固定候选在上述有限范围最终生产技术审核接受，可提交负责人批准本地采纳和正式状态落地。** 本次没有尚未满足的冻结技术条件，没有新发现的实质阻断反例。必要有限 leak 按负责人四行 B 验收，非独立动态 LSan 认证。实施批准尚未取得，不属于技术审核失败。

当前主 HEAD 仍为 `963ccf153855734de968e6cf71477f324e33329c`，未实施采纳；D001/D002/P04 正式状态仍 OPEN。P05 未启动。本审核不 fetch/switch/apply 正式文件/commit/push，也未重试 fatal/ptrace 通道或修改候选。

## 1. 身份与实际核验

主路径 `/home/jackal/nvme_ssd/projects/S4-Stanford-Stratified-Structure-Solver`，realpath `/srv/nvme/projects/S4-Stanford-Stratified-Structure-Solver`。以下历史路径相对于此根，新增证据位于本目录。

| 检查 | 本次实测 |
|---|---|
| 候选 | `.p04-review/remediation/round9/adoption-20261010-a745a3e/candidate`，HEAD `5cf534ce5ec223a6388d29bbb2c58f981f070241`，父为上述主 HEAD |
| 候选组成 | 33 路径，7 修改/26 新增，与 PATHS 白名单一致；33/33 blob 与 remediation/repo 的 `a745a3ea5bdd585f052898271b7c34015e27392b` 一致；实际工作文件与候选提交一致 |
| patch | 独立生成 `git diff --binary --full-index`，与保存 adoption.patch 字节相同；SHA256 `eb9b76d68ace80e58ea849e7a297c376d0d7d17cbd078d938abb6c29f8a712b5` |
| clean 身份/保存重聚合 | STEPS 的 root_commit 为固定候选；本次从候选正式 aggregate 函数只读重算，38 执行步骤 PASS、0 unexpected，与保存 AGGREGATE 完全一致；39 聚合记录包含额外的产物检查，不是39执行步骤 |
| 产物绑定 | 逐项读取实物重新计算，18/18 SHA256 匹配，涵盖默认/基线/seam 库、CLI、Python 扩展与D002驱动；未仅相信日志路径 |
| 证据清单 | round9 2353/2353；round3 118/118；round6 78/78；round11最终selfrun MANIFEST 60/60、BINARIES 7/7 |
| 默认构建 | 默认 lib/pyext 原始构建日志 `S4_TEST_EIGEN_INFO` 与 `HAVE_LAPACK` 均0次；源码宏隔离、流水线单独 seam 构建相符 |
| 实时采纳预检 | 本次执行 round13 只读 preflight：24项PASS、0失败；候选patch可apply-check，用户修改无交集，新路径无冲突，两个拟建分支不存在；主状态仅有既已具名允许的round12/13提示词增量 |

原始可追踪结果：`CHECKS.json`、`verification-output.txt`、`ARTIFACT_BINDINGS.json`、`aggregate_recomputed.json`、各 manifest 逐项 JSON、`product.diff`、`preflight/PREFLIGHT_OUTPUT.txt`；重算入口 `verify.py`。本次没有重新构建/运行整套solver；源码和已验来源一致，沿用已绑定clean运行与历史独立接受，符合本任务冻结策略。

根历史 manifest 正确跳过3行注释后为 **158/161** 匹配；三处仍不匹配：`checkpoints/p04-remediation/evidence/README.md`、`REMAINING_ITEMS.md`、`REMEDIATION_REPORT.md`。这与已披露的文档差异相同，不涉及本次四行原始目标证据/候选产品，不据此伪称总清单全过，也不升格新solver阻断。

## 2. D001：接受

实际阅读 `S4/RNP/Eigensystems.cpp` 的 zgebal/zgebak 及 Eigensystem 调用。zgebal 使用1-based内部索引（`--scale`，置换存入原始1-based j）；Eigensystem 以 `ilo-1, ihi-1` 传入 zgebak。左右向量两处各由 `i=ilo-ii` 改为 `i=ilo-1-ii`，使低端交换从0-based边界前一项逆序开始；两处 k 由 `scale[i]` 改为 `scale[i]-1`，把保存置换转换为0-based数组索引。中间平衡区间被跳过，右/左对应处理一致。四行修改与实际调用约定相合。

冻结默认 Linux（HAVE_LAPACK未定义）12例及扩展113例通过；比较条件为R/T有限、入射flux正、绝对误差各≤1e-10，本次阅读两个正式runner确认阈值未放宽。第九轮独立TMM记录 `claude-round9-audit/d001_independent_tmm.json` 冻结12/12（最大1.11e-16）、扩展113/113（最大3.33e-16），基线分别8/12、60/113；独立公式复算的性质为保存数值复算，不是本会话动态物理运行。结合本次源码/产物/manifest匹配，这些证据适用于同一最终候选。

**技术签收接受；技术条件全部满足。** 未决仅负责人批准及本地采纳/正式状态实施；主分支旧索引不撤销已完成的候选集成验证。不扩大到其它材料/参数的数学证明或其它构建配置。

## 3. D002 非leak：接受

实际阅读最终候选七产品文件差异和相关调用点：

- RNP仅值分支实际为 `info=zhseqr_('E','N',...)`，后续向量计算与逆平衡在 `info==0` 内，最后返回原info；NULL复数工作区/短工作区由内部2n分配并按原始条件delete，NULL实工作区单独分配/释放。zlaqr0/zlaqr3的 z 指针偏移在wantz时进行，下游传原始_z__，避免仅值NULL路径的偏移。契约内可选向量、布局、空区间与工作区采用冻结原生测试覆盖；不外推A-10r等契约外情形。
- rcwa复数默认路径在改写lwork为query sentinel前记录owns_work；NULL/短内部工作区释放，足够的借用工作区不释放，NULL rwork同样有独立释放。接收真实RNP info，非零时不进行q平方根后处理；返回info给S4。数值数组可能已被底层求解写入，失败不安装不等于输出保持sentinel。
- S4中q是kp/phi/Epsilon等内外指针共同分配的所有者。失败分支释放临时work/rwork，并由Simulation_DiscardLayerModes释放q及结构体、将指针置NULL，然后返回公开20。ComputeLayerSolution、GetPropagationConstants、GetSMatrix检查并返回失败，避免继续使用失败模式或构造成功结果。
- Python错误表覆盖20，失败GetAmplitudes释放amp并返回NULL；Lua使用共用错误表，GetAmplitudes错误释放amp，公共调用传播错误。SolveInParallel的worker记录rc，所有worker join后取首个非零状态、释放data、再报错，涵盖所有非零状态，不只20。
- seam只在 `S4_TEST_EIGEN_INFO` 测试宏下包含；本次阅读seam.h，严格解析注入且真实非零优先，不能把真实失败改成成功。默认日志不含此宏；派生RNP seam探针不冒称产品字节。

证据组合：候选clean保存ord53/53、asan53/53、seam58/58；第五轮独立正式judge124/124、aggregate71/71，B1–B4拒绝且控制保留、真实十份A-07诊断有限校正接受；第九轮error20保存43/43，包含同对象解除注入重试恢复，不能从始终注入的C驱动推断恢复。s4test候选/基线各total257/pass256/skip1（OOM Code Review Only），Lua regression与binding smoke4/4保持。第九轮源码阅读/独立保存审核与本次产物绑定共同支持最终连接，无需从零重跑全部工具单元测试。

**非leak冻结技术条件满足，接受。** R-D002-BOUNDARY-01为已有有限机制覆盖，不声称任意损坏证据全面认证；没有具体新反例，不新增无限关闭条件。

## 4. 必要有限leak：四行均按B接受

原批准来源：保存记录 `.p04-review/remediation/acceptance/acceptance-B-rows1-4-20261010/ACCEPTANCE_B_ROWS1-4.md` 的“负责人原文（批准依据）”，明确“接受第十一轮闭环表中行1–4”的保存证据及独立保存核验，接受披露限制、不构成独立动态LSan认证、不扩大冻结范围。本次实测SHA256为 `64149930e3094f85d3132413d712e642c1a30c4a1405e86cb17a15a3f4852f07`，与用户给定值一致；本轮用户明确确认该决定的效力。本会话未取得另一个外部签名/原聊天导出，批准溯源限于此书面原文和本任务的负责人决定输入，不制造身份认证或签名。

| 行 | 有限目标及证据 | 本次结论 |
|---|---|---|
| 1 | round3/rnp-seam-workspace，n=2 dense工作区失败/重复调用，18进程；round3/lsan有lost真实泄漏报告且rc23，freed/reachable rc0；清单118/118 | B接受。控制-O0与目标-O1、非同一二进制的限制保持；rc0没有单独替代阳性能力证据 |
| 2 | evidence/rcwa/candidate，n=2 dense成功，NULL/short/exact/query保存结果；根清单对应原始文件匹配，rcwa/RNP blob与候选一致；沿用保存阳性通道 | B接受。非seam成功库与失败seam库分开；保存query成功不外推query扩展/防御失败认证 |
| 3 | round6/rcwa-failure-workspace，NULL/short/sufficient lwork24，六进程各三次，原生info0/1；真实lost/target-linked-leak与阴性控制；第六至八轮独立保存重判 | B接受完整原闭环表对象。17/17绑定已本次重新计算，详见ROW3_BINDINGS_RECOMPUTED.json |
| 4 | round10探针及round11最终selfrun，S4非均匀失败q释放；本次核对lost rc23与真实报告，突变rc23、4处17136字节栈指向Simulation_ComputeLayerModes，目标unset/inject rc0且注入4条RESULT均20；60/60及7/7 | B接受。第十轮未记录的机器rc不补造；采用第十一轮完整记录支撑。突变是能力反证，未改候选 |

**本次直接勘误**：原B记录末尾“行3新缺口/缩小接受对象”的推断为误报，予以撤销；原批准覆盖保持。env.txt明示树round6/src，hashes.txt混合源码树相对路径、probe相对路径与运行绝对路径。四源码/两个对象从round6/src读取，probe与三个控制源从原repro解析，run.sh/check_results.py从4b20233历史Git blob读取，五个运行二进制按记录绝对路径读取，独立重算17/17。与 `acceptance-B-followup-audit/REVIEW.md` 和 ROW3_BINDINGS.json一致。不是伪造缺失对象，也不是独立重建。本审核已完成勘误确认，无需等待Claude另写文件，更无需重做A。

**必要有限leak按B验收，非独立动态LSan认证。** 不把普通rc0当无泄漏证明，不声称本会话运行LSan；不重新尝试已fatal/ptrace的独立通道。行1–3限n=2 dense，行4限非均匀层，均匀张量未动态运行；Python/Lua未在sanitizer下运行；Lua GetAmplitudes新增分支未命中。这些是已接受覆盖限制，不扩范围、不抹掉其余技术接受。

## 5. 范围、状态与负责人可批准对象

范围外登记保持：HAVE_LAPACK原生、query扩展、新pthread、n>2、A-10r、D012、历史provenance。现有默认/保存pthread有限结果保留，SolveInParallel所有非零状态报错的实际行为已签收知悉，不要求额外重开该修复。根历史manifest三处文档差异保留披露。

| 项目 | 最终技术结论 | 技术条件 | 真正未决 |
|---|---|---|---|
| D001 | 接受 | 全满足，限默认冻结12例/扩展113例及1e-10 | 负责人批准与采纳/正式状态落地 |
| D002 | 接受 | 非leak冻结条件满足，必要leak四行B已满足 | 同上；独立动态LSan未认证为披露限制，不是B路径未决 |
| P04 | 接受 | 候选集成clean、回归、身份、两缺陷及必要leak最终审核满足 | 同上；当前正式OPEN，尚未实施 |

读取的Claude状态差异只有round10/11 STATUS_DRAFT.patch，未发现B决定后的新状态副本或独立勘误文件。round11草案可apply但仍写B/最终审核未完成，是过时的预备文本，不作为已生效状态。缺新副本不阻止本次最终候选接受。

为提供具体可批准对象，本目录新增 **STATUS_REVIEWED.patch**：仅基于当前用户PROJECT_ROADMAP.md与ISSUE_REGISTRY.md生成，保留其余内容和历史记录，更新有限关闭表、审核引用、四行B强度/勘误、行为/范围限制。SHA256 `f7346e456ab652b58214cac935c7118e9b74bb950b495f8a12b82186245d4a4c`；本次 `git apply --check` rc0，未实际应用。补丁中的CLOSED/已采纳是**授权并验证采纳后拟落地的状态**，不是本次已实施的事实；不得提前应用。生成入口prepare_status.py；该补丁是本审核准备的具体提案，不冒称Claude最新副本。

负责人下一步可批准：固定候选完整SHA；本地新分支 **codex/p04-adoption-20261010** 指向该固定SHA；本目录上述已审核状态差异；本报告D001/D002/P04有限关闭范围及B限制。建议批准后按round12 CLOSEOUT_DELTA §6和round13 preflight的失败停止规则办理本地获取/切换，保留检查点分支与用户修改，不强制覆盖。实时预检重核通过、负责人明确批准、主HEAD及分支确认为固定SHA、四用户文件保持后，才应用状态差异；若状态基点发生漂移则停止并定向复核差异，不重跑整个solver矩阵。正式状态另提交时记录真实产生的状态提交SHA，不能用占位值。采纳源码预期SHA已固定为5cf534c，本次真实已采纳SHA为**无（未实施）**。

未授权项：本次不替负责人批准，不批准push/PR/tag/P05。实施授权不是本技术审核的附加失败条件。

## 6. 历史引用与审核边界

本会话已读P04_TEMP_CHECKLIST；round11 P04_CLOSEOUT_RECORD §2、§5–6及采纳计划；claude-round9-audit/REVIEW、verification.json、独立TMM记录；claude-round5-audit/REVIEW（正式工具/B1–B4/A-07）；claude-round13-audit/REVIEW及最新preflight；acceptance-B-followup-audit/REVIEW与ROW3_BINDINGS；负责人B记录。第六至八轮保存核验结论用于leak既有独立接受，未声称本会话重复动态认证。原始清单和关键输入SHA另见INPUT_SHA256.txt。

旧轮次“待最终审核”在当时成立，已由**本次实际最终审核接受**取代，不能继续当作一个无人执行的技术待办。主分支采纳与正式关闭的实施事实仍待负责人批准和执行；这一区分不会撤回任何已有技术接受。
