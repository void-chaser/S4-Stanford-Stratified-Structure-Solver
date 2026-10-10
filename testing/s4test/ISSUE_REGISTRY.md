# S4 当前缺陷登记表

更新：2026-10-10（Australia/Sydney）。执行顺序和阶段验收见 [PROJECT_ROADMAP.md](../../PROJECT_ROADMAP.md)。

## 编号与证据口径

本表采用用户本次提供的规划中的 D001–D015，作为今后的唯一执行编号。
该表覆盖科学结果、核心状态、构建安装和公共 API，且保留了既有审计的 D001 称呼。
本轮未取得原图片/原始表附件；编号定义的直接来源是本次用户提供的文字，不能据此补证历史来源。

[DEFECTS.md](DEFECTS.md) 中的 D1–D15 一律称为 **legacy D1–D15**。
历史编号不重写，也不通过补零建立映射；按症状、调用路径和证据范围关联。
审计 Task010/Task014 等任务号同样不是缺陷编号。

**D002 的完整名称始终是 D002 (current working registry definition)。**
它是当前可执行工作项；原始历史 D002 定义/因果的 provenance 仍未知。
修复当前工作项不改变这个历史结论。

以下“源码观察”来自本轮静态阅读，“历史有限通过”来自已保存的独立审核。
本段为建立登记表时的静态阅读口径；D001/D002 后续有限生产验收、采纳与关闭以本表 2026-10-10 最终记录为准，其它条目仍按各自证据状态处理。

## 当前工作项

| 编号 / 优先级 | 当前定义 | 已知状态与证据强度 | 下一动作 / 关闭判据 |
|---|---|---|---|
| D001 / P0 | scalar、同材质区域、isotropic tensor 等价表示产生不同物理解 | 有限范围 CLOSED；固定候选 5cf534ce5ec223a6388d29bbb2c58f981f070241 已采纳于 codex/p04-adoption-20261010；Codex 最终生产技术审核接受，详见末节 | 默认 Linux 冻结12例及扩展113例，绝对阈值1e-10；其余材料/参数和配置不作全面认证 |
| D002 / P1 | RNP backtransform 防御性内存缺陷；仅值分支返回状态不可靠（current working registry definition） | 默认构建冻结范围 CLOSED；与D001相同采纳SHA，必要leak按负责人四行B验收，非独立动态LSan认证，详见末节 | 原生契约、仅值状态接收、rcwa失败清理不安装及S4/Python/Lua错误20传播；HAVE_LAPACK 原生运行、query 扩展/失败注入、新 pthread、n>2、A-10r、D012、历史 provenance为范围外登记 |
| D003 / P1 | FFT prepare/execute 失败处理及上层传播不完整 | checkpoint 已含 FFT wrapper/kiss FFT/网格路径的部分处理。历史六文件 FMM 候选和 runner 存在；完整候选未生产验收/集成 | 列实际计算分支、计划/执行调用点；复用候选与现有注入器，补缺口；失败不得安装模式/缓存；恢复后重试与全新对象一致；Python/Lua 报错可见 |
| D004 / P1 | 求解后 SetOptions 沿用旧模式/缓存 | Python SetOptions 直接更新 options 后返回，当前函数未显式失效旧状态；现有测试主要在首次求解前设置选项，未覆盖该缺陷 | 同对象 solve→SetOptions→solve 与按最终选项新建的对象比较；覆盖改变截断/离散化/偏振基/内存模式的选项；非法选项失败后的对象状态有明确契约 |
| D005 / P1 | 核心更新未重新链接 Python extension；header dependency 缺失 | Makefile 多数对象只声明 cpp/c 依赖；setup.py 链接既有 build/libS4.a。make test-python 使用清空构建的绕行方法，普通增量构建问题仍有历史记录 | 核心实现、头文件、binding 各一次有可观测影响的修改，普通构建自动更新应受影响产物且加载新代码；清空重建不作为增量修复证明 |
| D006 / P1 | clean wheel/editable 与 sdist 回装失败 | setup.py 依赖预先存在的 build/libS4.a；本轮未执行安装矩阵 | 在隔离环境分别做 clean wheel、editable、sdist→wheel→安装；从源码目录外 import/执行解析物理 smoke；不依赖开发树残留 archive/so |
| D007 / P1 | Python robust geometry predicates 未初始化 | threadsafe_init 定义含 exactinit，但 PyInit_S4 中调用被注释；本轮未动态验证几何后果 | 在 fresh Python 进程验证正确初始化生命周期；稳健/近退化几何回归，用独立几何预期核验，辅以 Python/Lua 一致性 |
| D008 / P2 | Python conversion/warning 异常传播不完整 | 已有部分转换检查；仍存在数值转换和 warning 返回值待审查点 | 能抛异常的 __float__/__bool__、warnings-as-errors 等触发测试；保留原异常，不出现带 pending exception 的成功返回；操作失败后的状态符合契约 |
| D009 / P2 | polygon 错误路径资源泄漏 | 历史 legacy D6 是输入转换问题，不证明资源问题已关闭；当前工作项待定点复现 | malformed vertices、转换异常、相关分配失败的所有权检查；针对该路径的 sanitizer/leak 检查及成功对照 |
| D010 / P2 | C API message-handler setter 缺返回值 | S4_Simulation_SetMessageHandler 非 NULL 分支源码确实缺 return | 先核对头文件/调用者确定返回契约；C 调用验证替换/清空/NULL simulation 的返回值及 callback/data 行为 |
| D011 / P2 | add/set 负厚度规则不一致 | 已有 SetLayer 负厚度测试，不覆盖所有 Add/Set/Copy/C API 路径 | 确定一致规则，测试相关入口拒绝与有效的零厚度；失败后原对象仍可求解 |
| D012 / P2 | Python SolveInParallel 静默 no-op | 当前 Python 实现直接 Py_RETURN_NONE；不能将 Lua 线程实现或 MPI 覆盖状况当成同一缺陷 | 默认先明确报 NotImplementedError 并测试，保留名称便于兼容；除非后续明确需要并行功能，不扩成线程/MPI 实现项目 |
| D013 / P2，条件提前 | Cgeom metadata 不完整 | Git 索引有 Cgeom gitlink 2837c629…，根目录未见 .gitmodules；历史 source snapshot 保留 PARTIAL | 核对实际构建/发布依赖后补正确 metadata，或在证明无依赖后有意移除遗留引用；若阻塞 clone/install 则纳入 P07，否则 P10 处理 |
| D014 / P2，最后完成 | 分平台安装文档与 C API example 已过时 | 待稳定构建/API 后逐条校验 | 对实际支持的平台给可执行步骤；C example 用当前公共头文件/库编译运行；当前文档入口不引用失效流程 |
| D015 / P1 | 非网格导出崩溃，或写失败仍返回成功 | Python Postscript/POVRay 入口可见 fopen 结果未检查；输出/关闭错误待动态复现。不是 legacy D15 网格错误处理 | 覆盖正常导出、不可打开目标、延迟写/关闭失败、stdout 所有权和失败清理；Python/Lua/C 相关入口传播明确失败 |

## 与历史测试的关联（不是编号等同）

| 当前项 | 可复用的历史记录 / 测试 | 不能外推的部分 |
|---|---|---|
| D001 | test_analytic_reference.py、test_two_layer_acceptance.py、test_structures.py；004/007/008/010/011 审核 | 守恒、helper 正确或旧 binary 通过，均不等于当前公共 API 闭合 |
| D002 | test_eigensolver_workspace.py、test_zlahqr_direct.py | legacy D2 是 Clone；QR 空区间保护不等于 backtransform 完整安全或仅值状态正确 |
| D003 | legacy D15；testing/fmm-runner；FFT/kiss FFT 已有错误处理 | 网格路径有限通过和假驱动 runner 通过，不认证所有 FMM 分支 |
| D004 | legacy D9、test_sweep_frequency.py、test_python_api.py | SetFrequency 的缓存失效不等于 SetOptions 的缓存失效 |
| D005/D006 | DEFECTS.md 的 stale extension 警示，现有 make test-python | 强制删除旧构建不证明普通增量构建或 clean package install 正确 |
| D008/D009 | legacy D6、test_python_api.py 的 polygon 输入测试 | 接受 list/tuple 与正确资源释放是不同契约 |
| D015 | legacy D12–D15 的网格/field-plane 路径、test_grid_output_safety.py | 网格安全不能关闭非网格 Postscript/POVRay 的文件错误路径 |

## 更新规则

编号固定；新缺陷追加 D016 起，先查症状重复，避免因同文件另起重复项。
一个编号内部可以拆子项，但保持原有关闭条件可追踪。
实现完成、targeted 通过、阶段验收通过、生产关闭分别记录，不用一列 FIXED 混合表达。
完成后在对应行补提交、测试命令/结果、证据位置和实际覆盖范围；未知项保持未知。
当前表不是全部已知技术债的全集，长期边界见路线图，不能将 D001–D015 全关等同于无限范围科学认证。

## 2026-10-09 P04 第一阶段状态（D001 / D002）

口径：implemented（已实现）／targeted complete（定向验证完成）／pending independent production acceptance（待独立生产验收）。生产关闭状态仍为 OPEN。

| 编号 | implemented | targeted complete | pending independent production acceptance | 证据 |
|---|---|---|---|---|
| D001 | 源码 `S4/RNP/Eigensystems.cpp` zgebak_ 四行索引（提交 44f4a09） | 冻结 12 例 candidate 12/12，baseline 8/12；扩展 113 例 candidate 113/113（f 0.173/0.427/0.733，θ 0/30，s/p，N 1/9/25，A/B/C，内存模式）；终验绑定 8b13d67 | 独立审核与生产集成复验；范围外：其它材料/参数的数学证明 | `checkpoints/p04/REPORT.md`，`checkpoints/p04/evidence/` |
| D002 | Eigensystems.cpp（zhseqr 状态、NULL z、工作区归属），rcwa.cpp/rcwa.h（返回与失败不安装），S4.cpp，main_python.c/main_lua.c（错误码 20） | D002 原生 59 例：candidate ord 53/53、asan 53/53、seam 58/58；错误码 20 Python/Lua/C 33/33；HAVE_LAPACK 仅语法检查 | 独立审核；HAVE_LAPACK 分支原生运行；query 失败注入；线程路径；历史 provenance 仍未知 | 同上 |

注：legacy DEFECTS 的编号与用户已有内容未改动。baseline 的失败结果是缺陷对照，不是流水线失败。

## 2026-10-10 P04 最终有限关闭记录

最终生产技术审核：Codex 独立审核会话，记录 `checkpoints/p04-final/FINAL_REVIEW.md`。D001、D002、P04 在以下有限范围技术接受。负责人批准并完成本地采纳后本节才可落地；本节不是批准签名。

采纳源码 SHA：`5cf534ce5ec223a6388d29bbb2c58f981f070241`，父 `963ccf153855734de968e6cf71477f324e33329c`；本地分支 `codex/p04-adoption-20261010`。状态文档提交另记录实际产生的提交号，不将本文预备文本当作已执行操作。

| 项 | 有限关闭范围与证据 |
|---|---|
| D001 | 默认 Linux、HAVE_LAPACK未定义；zgebak四行置换索引修正；冻结12/12、扩展113/113、绝对阈值1e-10；第九轮独立TMM保存数值复算12/12与113/113，非独立动态物理运行 |
| D002 非leak | 默认构建原生契约ord53/53、asan53/53、seam58/58；第五轮独立正式judge124/124、aggregate71/71，B1–B4及A-07有限校正保持；zhseqr仅值状态接收、NULL/工作区归属、rcwa失败清理及S4/Python/Lua错误20，error20保存43/43 |
| 必要有限leak | 负责人原批准记录 `.p04-review/remediation/acceptance/acceptance-B-rows1-4-20261010/ACCEPTANCE_B_ROWS1-4.md`（SHA256 64149930e3094f85d3132413d712e642c1a30c4a1405e86cb17a15a3f4852f07）；行1–4全部采用B保存证据验收，非独立动态LSan认证。行3路径解析误报已在最终审核撤销，正确绑定17/17；不缩小原批准范围 |
| P04 | 固定候选clean保存流水线38步PASS、0unexpected、18/18产物绑定；主测试total257/pass256/skip1（OOM为Code Review Only）、Lua回归及binding smoke4/4；上述有限范围关闭，P05未启动 |

覆盖限制：行1–3仅n=2 dense；行4仅S4非均匀层失败，均匀张量未动态运行；Python/Lua未在sanitizer下运行；Lua GetAmplitudes新增分支未独立命中。SolveInParallel在所有worker join且释放data后，对首个非零层状态报错，包括20以外状态；保留既有默认/保存pthread有限结果，不称线程全面认证。

范围外（不升格关闭前提）：HAVE_LAPACK 原生运行、query 扩展/失败注入、新 pthread、n>2、A-10r、D012、历史 provenance。根历史manifest中evidence/README.md、REMAINING_ITEMS.md、REMEDIATION_REPORT.md三处文档差异仍披露。上方2026-10-09状态表为历史记录，其旧待审项不覆盖本次有限最终结论。

## P04 范围外后续登记（2026-10-10）

这些事项不撤销已验的 D001/D002/P04 有限关闭。先登记已知反例、待验证契约和配置覆盖缺口，未验证不写成已确认生产缺陷；R-P04 编号是后续登记引用，不替代 D001–D015。正常受支持输入中新确认的独立缺陷再按更新规则追加 D016 起，避免重复编号。以下排期是建议，尚未开始执行。

| 引用 | 项目与当前性质 | 下一次有限核验 / 完成标准 | 建议排期与提前条件 |
|---|---|---|---|
| R-P04-01 | A-10r 契约外短工作区越界；保存 SIGSEGV 探针存在，非正式 judged 用例 | 核对实际分配大小、lwork 与公开契约；确认正常公共调用能否触发。支持范围内则构造最小反例并修复，契约外则明确前置条件或制定防御行为 | P05 主线之后安排 RNP 防御专项；若正常受支持输入可达内存破坏则提前 |
| R-P04-02 | query 防御性失败路径，属于未覆盖契约 | query 失败不安装模式、不继续使用无效尺寸，临时资源释放；用具名失败输入/最小 seam 及成功对照，不重跑全部矩阵 | RNP/rcwa 防御专项；若新证据影响默认求解则提前 |
| R-P04-03 | HAVE_LAPACK 原生运行未认证；额外构建配置覆盖缺口 | 固定实际编译/链接配置，核验真实 LAPACK 分支、原生 info、工作区所有权及前端错误传播；语法通过不当作原生通过 | 声明支持该配置前必做，发布支持配置矩阵前安排；非当前默认构建关闭前提 |
| R-P04-04 | pthread/HAVE_UNISTD_H、ParallelInvoke、线程池/OOM；配置及生命周期核验缺口 | 固定线程配置，定向检查构建、worker/join、参数/分配失败和资源清理；具名场景分别接受，区分 Lua 与 Python 入口 | 声明线程配置支持前专项；若受支持正常调用出现崩溃/泄漏/无效成功则提前 |
| R-P04-05 | n>2、其它层类型、线程下所有权覆盖扩展 | 先选代表矩阵与实际变更/风险路径，分别核验成功/失败/重复调用、必要阳性能力和清理；保持每个配置的覆盖限制 | 随相关路径变更或发布范围扩展分批安排，不建无限“全面认证”前提 |
| R-P04-06 | D001 新科学矩阵与更广材料/参数；科学覆盖扩展 | 用独立物理参考挑选新增材料/各向异性/参数情形，保存输入及误差阈值；发现正常输入实质反例时登记影响范围 | 科学验证扩展专项；出现具名错误物理结果则提前 |
| R-P04-07 | 历史 D002 等 provenance 未知；证据溯源事项 | 找到原定义/提交/输入则记录明确来源；找不到保持未知。不得用当前有限修复补造历史因果 | 并行资料整理或文档阶段，默认不阻塞 P05 |
| D012（既有 issue） | Python SolveInParallel 静默 no-op，已有 P2 条目 | 按原条目默认 NotImplementedError/unsupported 契约及回归；不另起重复 issue，不外推为实现完整并行 | 仍按 P11 排期；若当前用户流程依赖该入口，可单独提前小修复 |

下一轮默认修复顺序仍为 P05/D003 → P06/D004；P05 应核对实际 FMM/FFT 失败传播和已登记 VL NB1 可达性。以上后续事项仅在其自身任务明确启动后执行，不回头扩大本次 P04 验收。
