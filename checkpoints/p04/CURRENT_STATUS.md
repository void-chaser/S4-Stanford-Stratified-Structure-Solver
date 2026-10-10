# P04 当前交付状态（2026-10-10，Australia/Sydney）

## 当前状态分层（Master 合并前整合闸门，2026-10-10）

每一项独立判断，不得互相替代：

- **技术接受**：D001、D002、P04 在冻结有限范围经 Codex 最终生产技术审核接受（[最终审核](../p04-final/FINAL_REVIEW.md)）。本轮未改变该结论。
- **有限范围关闭**：D001、D002、P04 在[登记表](../../testing/s4test/ISSUE_REGISTRY.md)所列范围 CLOSED。必要 leak 为负责人 B 保存证据验收，不是独立动态 LSan 认证；HAVE_LAPACK 原生运行、query 扩展/失败注入、新 pthread、材料/参数扩展（D001 行所列其余材料、参数与配置）、n>2、A-10r（R-P04-01）、D012、历史 provenance 不在关闭范围内。
- **Feature 已发布**：远端分支 `origin/feature/python314-binding` 位于 `2c3bf89f171dcfd68e57c67b5fb4bd1ef8ac3580`，其 S4 源码子树 `1d738e64f9864a475fdb3de34cd3601605df2c64` 与固定候选 `5cf534ce5ec223a6388d29bbb2c58f981f070241` 相同。
- **GitHub issue #1/#2**：仍为 OPEN；本轮未关闭、未修改 milestone。
- **尚未合入 Master**：`origin/master` 仍为 `7fd00a231610bff51f5c7de5f723e3956eab7453`；Feature 相对 master 为 0/12，可快进，但本轮未合并、未推送。
- **本次执行者自审**：在本地隔离分支 `codex/master-integration-gate-20261010` 上完成，结论见交付报告。这是执行者自审，不是独立审核。

本轮改动：
- 修订一（`91bb715`）：D002 判定器 A-36 规则（asan_baseline 由 must-pass 改为 may-fail，并要求注册站点；seam 基线保持 must-fail 并加站点规则）。
- 修订二（`168d081`，后续纯文档与测试提交见 Git 历史，执行者自审）：收紧 A-36 结果规则。正常退出的数值失败不再被 may-fail 接受；窗口 `[1, n]` 外的非零 info 不接受；注册崩溃须为一份完整的 ASan SEGV 报告。判定测试 124→137→153。
- 证据与逐条计数：[A36_RULE_CORRECTION.md](../../testing/d002/evidence/A36_RULE_CORRECTION.md)（80 条归档记录逐条复判，结论无变化）。
- P01–P03 状态与路线图入口同步。产品源码、PLAN 阈值与其他用例分类未改。

安装验证的当前结论：预构建核心库后的 wheel 构建/安装，以及已有构建树上的 editable 安装，通过并可从源码目录外导入、通过物理烟雾。这只说明预构建路径。全新 checkout 不先执行 make 时，wheel 与 editable 安装失败（缺 `build/libS4.a`，链接期失败）；sdist 不自包含，回装失败。以上均登记为 D006 后续工作，未修复。D005 的 mtime/dry-run 观测（头文件变化不触发重编；核心库变化不重新链接扩展）只是有限证据，未做行为修复验证。

环境注记：本轮审核前的沙箱内原始流水线中，ASan 相关步骤的 LeakSanitizer 报 `does not work under ptrace`，该轮 ASan 结果不能作为验收依据。正式复验时 LeakSanitizer 正常工作，未设置 `detect_leaks=0`，未删除 stderr，未关闭沙箱。

下一主线：**P05/D003**，再 P06/D004。P05 未启动。

## 历史记录（保留）

本次在已有发布分支 `feature/python314-binding` 保留2026-10-09提交历史，整合最终审核候选 `5cf534ce5ec223a6388d29bbb2c58f981f070241` 的33路径产品/测试成果。候选父为 `963ccf153855734de968e6cf71477f324e33329c`。发布整合版本的这些blob与固定候选逐项相同；未重跑已冻结的完整solver流水线。

D001、D002、P04在冻结有限范围最终技术审核接受；负责人四行B保存证据验收与本地采纳/正式状态已完成。B不是独立动态LSan认证，覆盖限制保持。独立审核原文见[最终审核](../p04-final/FINAL_REVIEW.md)，B原记录须连同[勘误](../p04-final/ACCEPTANCE_B_ERRATUM.md)阅读；[归档入口](../p04-final/README.md)和[登记表](../../testing/s4test/ISSUE_REGISTRY.md)提供当前范围及后续工作。

保存clean流水线38步PASS、0unexpected，18/18产物绑定；D001冻结12/12、扩展113/113；D002 ord53/53、asan53/53、seam58/58；error20为43/43；s4test total257/pass256/skip1。正式judge及aggregate加固和Lua SolveInParallel状态传播已纳入最终候选，不再作为昨日待修项。

原REPORT、INDEPENDENT_REVIEW_HANDOFF、CLEANUP及independent-evidence保留为历史记录，其当时待审核/未验收状态不覆盖当前最终结论。完整历史构建/clone未纳入Git。候选采纳SHA与发布整合提交SHA分别记录，不能把发布整合误称为新的solver验证运行。

后续主线优先P05/D003，再P06/D004；R-P04范围外事项按登记表独立排期，不重开本次有限验收。P05尚未启动。
