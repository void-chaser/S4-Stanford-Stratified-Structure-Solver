# P04 当前交付状态（2026-10-09，Australia/Sydney）

本次交付完成 D001/D002 最小修复的代码整合、clean native 构建、相关运行复验和本地目录整理。已完成的成果纳入 `feature/python314-binding`；未完成事项留待后续处理。本次不关闭 issue/milestone，也不宣称所有配置或输入均已认证。

本文件是当前状态入口。`REPORT.md`、`INDEPENDENT_REVIEW_HANDOFF.md`、`CLEANUP.md` 和原 evidence 保留为执行阶段历史记录；其中“未推送”“待独立复跑”等时间状态由本文件更新，已知表述问题由下面的说明更正。

## 版本与实际验证

- 对照基线：`963ccf153855734de968e6cf71477f324e33329c`。
- 修复提交：`44f4a097f8c88ba34ee21c4f1353ac8682fb214e`。
- 已执行 clean build / 终验 / 独立复跑的源码与测试版本：`8b13d67b792516baf0074a2fda73081dcdec7f7f`。
- 原执行报告提交：`3f4a767c76db052cf582ece4d6296b19af56b780`。
- 本次发布整理仅追加文档、既有证据和 ignore 规则；未修改 S4/、构建或测试实现。下列结果绑定上述已测试版本，不冒充在新版本上重新运行。

| 已运行检查 | candidate | baseline / 对照 |
|---|---|---|
| D001 冻结物理矩阵 | 12/12 | 8/12，N9 B/C 复现原缺陷 |
| D001 扩展物理矩阵 | 113/113 | 60/113 |
| D002 native ord | 53/53 | 31/53 |
| D002 native ASan+UBSan | 53/53 | 独立复跑 26/53；执行者记录 25/53 或 27/53，已知未初始化 info 导致抖动 |
| D002 native seam + ASan+UBSan | 58/58 | 27/58 |
| ASan/UBSan 检测器阳性对照 | 3/3 签名检出 | ASan heap-buffer-overflow、UBSan signed integer overflow |
| 错误码 20，Python/Lua/C 定向路径 | 33/33 | 不覆盖所有 Lua 调用路径 |
| s4test | 两棵树各 257 项 OK，skipped=1 | 同样结果 |
| Lua 回归 / Python binding smoke | PASSED / 4 项 OK | 独立复跑一致 |

D002 每变体输入 59 例：ord/asan 中 5 例 seam 不适用、1 例契约探针仅记录；seam 中 1 例探针仅记录。因此 53/53 和 58/58 不表示探针通过。seam 是测试装置，普通构建的隔离有预处理和行为检查支撑。

独立审核使用自己的物理参考复核 D001；另对保存的六个 D002 变体增加过程返回码、维度、有限性与布局检查，逐用例结果均无翻转。D001 有限范围的修复效果和默认构建的整合运行得到支持。ASan/UBSan 通过仅覆盖所列合法测试范围，不外推为完整内存安全证明。

## 当前可查的证据

执行者原证据见 `evidence/`。本次新增可提交的独立复跑摘要、逐用例判定、构建记录、回归日志和负例记录见 `independent-evidence/`，清单见该目录 `SHA256SUMS.txt`（相对于仓库根目录运行校验）。`RESULT_COMPARISON.json` 从同一次 RUN 的保存结果生成，六个变体的 `(status, pass)` 翻转均为 0；原审核报告关于 asan_baseline C-03 翻转 1 项的表述不采用。

这些摘要保留既有运行的身份记录和绝对路径；原始二进制/大目录不纳入 Git。源码、测试和必要输入已在分支内，运行入口仍为 `sh testing/p04_run_all.sh <全新输出目录>`。目前应逐步检查 STEPS 和 JSON，不能仅凭脚本整体 rc=0 判定成功。

## 已完成的整理

历史目录已移入本地 `.local-archive/`，关键哈希及文件数经独立核对一致；没有将约 31.3 GB 的归档或审核构建树提交到 Git。归档位于同一磁盘，移动本身不释放空间；约 0.6 GB 的编译/字节码产物删除有清单记录。清理详情仍见 `CLEANUP.md`。主检出与发布分支是不同 checkout，主检出仍保留其用户改动与旧基线。

## 后续工作与准确边界

1. **判定器**：原 run_d002.py 可接受 NaN、空/不完整结果、错误 n 或索引等损坏输入。独立辅助 strict 判定器也漏比较 helper 虚部；因此辅助工具不称为已加固的正式验收工具。实际保存数据的复跑与重判结果成立，正式工具加固另做。
2. **流水线**：p04_run_all.sh 记录失败后继续，整体 rc 不聚合失败；后续需区分预期 baseline 缺陷与意外执行失败。
3. **查询**：当前 complex RNP workspace query 对满足前提的调用返回 0，RCWA 查询分支也返回 0；S4 新检查是防御性检查，不能称为已验证的 query 失败传播。real/HAVE_LAPACK 分支尚未原生认证。
4. **LSan**：此前 native 项目明确验证 ASan/UBSan，没有独立有效的 LSan 阳性对照。旧审核 leaktest2 将指针保留在全局变量中，不是有效的不可达泄漏对照；不能据此证明 LSan 静默失效。Codex 当前执行通道的三组配对尝试报 LSan fatal error/ptrace 限制，也不能外推此前执行环境。动态泄漏检测能力未验证；“未报告泄漏”不作为无泄漏证据。workspace 所有权修复有代码审查支持。
5. **Lua SolveInParallel**：worker 忽略求解返回值，默认无 pthread 的同步 fallback 也调用该 worker。该缺口保留待办，与 Python 静默 no-op 的 D012 区分，不宣称所有 Lua 路径已传播错误 20。
6. **A-10r**：rwork 短于约定容量的契约外探针，candidate 仍出现 SIGSEGV / ztrevc_ 越界；继续记录，未修复，不计作通过。
7. **来源与扩展范围**：修复是原补丁子集加本次新增的小改动（Lua GetAmplitudes 检查、S4 query 检查及释放、注释等）；HAVE_LAPACK 原生运行、Lua 交互路径、全面 n>75 扫描和历史 D002 provenance 不作已验证声明。

下一轮按这些具体未完成项推进；本次发布不为它们追加源码修复、不重新清理归档、不扩大验证矩阵。D001/D002 的实现与已测范围已登记，正式问题关闭与完整阶段验收分别处理。
