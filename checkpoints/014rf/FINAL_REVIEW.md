# 014RF 有限证据补正独立复核

结论：LIMITED_OFFLINE_EVIDENCE_CHAIN_ACCEPTED。此次 A（保存 plan 的 item 绑定）及 B（公开失败接口）均闭合；R2/R3 保持已验收。无需继续修复，保持当前停止边界。

## 恢复的检查点

沿用上一独立根 independent-20261003T095820Z-6ecdaefc 的 independent_review.py、既有保存前像及四个独立反例。旧脚本处于未跟踪 audit-workspace 内，git diff 不提供其历史基线；本次没有覆盖该脚本。原科学正例已完成，剩余仅计划摘要绑定与非法输入失败接口。没有重跑科学正例。

## 独立证据

- 原 C01 的六份前像只读重建通过，条目数 23/23/23/23/21/21；G2B 当前路径漂移仍非致命。C02–C08 七个保存负例均拒绝，分别点名 raw、observation、执行 oracle、缺少 raw 字段、probe 闭包、损坏前像、摘要不一致。
- 共 26 个 API 输入全部符合预期，包括上次审核自行构造的四个反例。T02 事件与 RESULT 同时伪造摘要仍被拒绝；本次另用独立标准库代码从内容寻址保存 manifest→plan 计算 item 摘要 ec4c4296…03f637，并确认伪造字段为 64 个 f。
- T03 两类 EVIDENCE 的错误/缺少 item 摘要四例全部拒绝。源码 RESULT 与两个 EVIDENCE 分支均调用同一 verify_plan_item；依据来自 manifest 绑定的保存 plan，类型及 class/kind/event 对应检查可见于源码。
- T04/T05 API 返回 ok=false、MALFORMED_JSON，分别明确 ledger_parse/saved_manifest_parse。通过 runpy 执行原 CLI 的 __main__ 并捕获 SystemExit：成功输入退出 0，两种非法输入退出 1，stdout 均为可解析 JSON；没有创建子进程。另检查非法结构、缺失输入及独立注入的意外 RuntimeError，分类符合契约，意外异常保留 diagnostic。
- 独立内存回放 unified diff，与最终重建器逐字节一致；BEFORE 与上一交付重建器逐字节一致。交付根索引 91/91；另两份索引元数据不自包含，文件覆盖完整。
- 原计数口径保持 20 账本文件、117 事件；未生成新账本或 chain。候选 14 源文件与已审核 SHA256 全部相等。

## 保护和边界

原声明保护集 12705 路径重新校验全部相等；联合保护本次交付和上次独立审核文件共 12882 路径，审核前后 changed=[]、missing=[]。两项锚点包含在已校验保护集中。git status 前后逐字节一致，仍为 27 项。

本次 native/native compile/solver/S4 import/formal item/formal token/new chain/new SYNTHETIC spawn 均为 0。Python 源码的加载属于离线工具核验，不计作 native 编译。审查脚本安装写入隔离审核根及禁止子进程/native 动作的 audit hook。

本结论只验收有限离线证据重建链；不升级 native S4、论文数值验证、D001/D002/scalea/I3/I4/legacy 认证状态，不进入下一阶段。

## 执行质量与是否需要更换对话

本轮按要求限制在两项统一补正，未改 candidate_v5，未扩展签收框架。共享保存-plan 不变量取代了自报字段相等检查；公开失败接口也已统一。保留上次独立反例后仍通过，体现了实质收敛，没有发现本轮跑偏或新的阻断缺陷。

历史漏检不能证明模型达到能力上限。就本次限定目标而言，验收条件已经满足，不需要为了继续修复而更换对话或模型。继续无限添加控制会延长阶段而不改变此次结论。用户要求在仍需修正时提供续执行提示词；本次无需新增修复提示词，也不创建下一阶段任务。可向原执行会话反馈：“014RF 两项补正已独立复核通过；保存现有证据与停止状态，不修改旧根、候选或生产文件，不重跑正例，不自动进入下一阶段。”

## 审核过程记录

首次创建审核根前尝试 python 命令，环境未提供该别名，退出 127；随后使用现有 python3 完成审核。此为工具启动选择问题，没有产生科学验证 attempt，也未覆盖任何旧日志。独立审核脚本运行一次通过。
