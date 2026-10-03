# S4 当前交接入口

> 更新日期：2026-10-01（Australia/Sydney）。先读本文，再按需查历史。
> 本次更新只整理文档和归档已有测试材料，没有执行构建/测试，没有修改生产代码或候选，没有提交/推送。
> 原交接文档完整保存在 [S4_HANDOFF_HISTORY.md](S4_HANDOFF_HISTORY.md)。其快照、计划和“本次”均指原生成时，不能直接当作最新状态或当前授权。

## 1. 项目与真实工作树

S4 是 C/C++ 核心、Python/Lua 前端的 RCWA 电磁仿真软件。当前目标是现代 Python/Linux 的可靠构建、数值验证和错误/资源处理；尚未独立定量复现论文。

- 真实树：`/srv/nvme/projects/S4-Stanford-Stratified-Structure-Solver`。
- 分支：`feature/python314-binding`；HEAD：`b97f63989c4d8192faee119e4dbcb70ef4a27219`。
- D15 及此前修复已集成真实工作树，但仍未提交。HEAD 不代表当前全部成果。
- 整理前 Git 简略状态 24 条：19 个 tracked 修改、5 个 untracked 组；暂存为空。整理新增历史文档和 handoff/，条数会变化，不以旧条数作为无修改证明。
- 最近有效 D15 主套件基准：257 总计、256 通过、1 跳过、expected failures 0；不是“257 通过”。本次整理没有重跑。

## 2. 当前任务分层：不要混为已完成

| 层 | 当前状态 |
|---|---|
| 真实树 D15 网格错误传播 | 已集成，有此前有限范围验收 |
| FMM 六文件生产候选 | 独立副本有修复，尚未完整验收/同步 |
| FMM 驱动 | 重试前模式/缓存、输出/哨兵、恢复有限性检查已独立运行 |
| 串行测试链接包装 | Codex 固定 8 场景实测成功；后续 agent 独立干净 -O1 构建和原始八场景记录与之相符 |
| 验收 runner | 最终成功标记和实际分支匹配仍有已复现漏洞；最新负向矩阵无效 |
| 下一轮 | 新上下文，仅修 runner 两缺陷并完成 20 项假驱动矩阵 |

八场景：FFT NB1/NB9、Jones NB9、VL NB9 正常控制；FFT NB1 真实 16B scratch、FFT NB9 第二计划分配、Jones NB9 第四局部执行模拟、VL NB9 计划分配故障。故障首次 1、重试 0、重试前模式/缓存空，有限性/哨兵通过；这是有范围的历史证据，不是完整候选验收。

## 3. 当前 FMM 候选与边界

候选：`/home/jackal/s4-fmm-20260930T132345Z`。
六文件：fmm_FFT.cpp、fmm_kottke.cpp、fmm_PolBasisJones.cpp、fmm_PolBasisNV.cpp、fmm_PolBasisVL.cpp、S4.cpp。
冻结哈希：[candidate.sha256](handoff/fmm-runner/evidence/candidate.sha256)。相对路径均以候选根目录为基准。

候选检查 10 个 FMM FFT 执行调用点、计划创建 NULL、错误清理与四个层模式调用方传播。实现存在不证明全部失败路径正确。真实树仍没有这些六文件候选修复。

未完成：全部分支故障矩阵、失败后 LU/缓存安装执行见证、相关 ASan/UBSan/LSan 正向对照、同标志数值前后对比、Python/Lua 传播、完整工程回归。因此不能同步、提交或声称候选已验收。

## 4. 最近失败的准确归属

- r6 runner 修复 probe/baseline 分类并跑通一组负向控制，但仍有两个漏洞：故障诊断替代最终 PASS；wbranch 仅打印不检查。
- r7 Codex 对抗测试独立复现这两个漏洞，并用串行链接包装跑通八场景。
- r8 报告称补丁破坏 runner；实际留存 run-one.sh 与 r6 **逐字节相同**，fake.sh 与 r7 审核用的固定 vl stub **逐字节相同**。九个负向标签实际都运行同一 stub，不算有效负向验收。
- 原因不能仅据报告认定；临时命令的 unbound variable 不证明交付文件已打补丁。24轮/711步不等于压缩了24次，也不能证明模型普遍能力上限。
- 长会话状态混淆和混合目录继承已发生。新 agent 不继承整份复核目录，只取明确白名单。

## 5. 新对话先读什么、唯一任务是什么

1. 本文：当前状态。
2. [handoff/fmm-runner/README.md](handoff/fmm-runner/README.md)：文件角色与校验。
3. [handoff/fmm-runner/TASK.md](handoff/fmm-runner/TASK.md)：本轮任务、固定20项矩阵及停止点。
4. 如需项目背景，再读 S4_HANDOFF_HISTORY.md，不把它第10/13节旧计划当作本轮任务。

只继承 `handoff/fmm-runner/inputs/run-one.sh` 和 `inputs/fake.sh` 到新建 `/tmp` 私有目录。
本轮只修改这两个隔离文件，不跑真实仿真、不重写注入器、不构建项目、不扩大验收范围。
`reference/` 只读；`evidence/` 是历史证据，读取不算本轮实测。
禁止继承 `/tmp/s4-fmm-r7-review-bxw1hv4_/fake.sh` 或 r8 的同名文件。
本轮满足20项后停止，由独立审核者裁定；用户另行决定下一阶段。

## 6. 环境与工作规则

- Linux 主机 38X-Ubuntu；历史核实 x86_64、GCC15.2、Python3.14.4。新会话先核实，不用安装依赖。
- Windows 客户端通过 SSH 到服务器执行；SMB 是真实树映射，不是隔离副本。历史 Git SSH signal-pipe 失败时系统 OpenSSH 可用。
- 已在服务器则直接运行 Linux 命令，无需绕 SSH。检查适用 AGENTS.md。
- 不 reset/checkout/stash/clean，不覆盖或中断其他 agent 工作，不 commit/push/PR。
- 用户本次授权的是整理交接，不是同步 FMM 候选。下轮范围由 TASK.md 和用户当前请求共同确定。
- 构建阶段若以后获授权：make 命令行 CFLAGS/CXXFLAGS 才能覆盖默认追加 -O3；记录实际 flags/源代码/二进制，不凭时间戳认定加载正确。
- C/C++ CRLF 保留；测试/文档 LF。本轮不改这些生产文件。

## 7. 长期待办，不属于下一轮

D10 精确截止点可信物理解、VL NB1 既有非有限问题、Python PyInit1760B/2处分配、插值器深层OOM唯一skip、Lua其他资源路径、平台扩展和论文定量复现。不能以通过 runner 小任务宣称这些已解决。

## 8. 状态如何更新

主负责人维护本交接入口；执行 agent 交付隔离文件、diff、SHA256、原始日志、判定结果。
每次结论标明：本轮实测/此前独立运行/历史报告/代码审查/未知。
更新完成状态必须有独立审核，不能靠执行者自述升级。
如交接包校验失败或输入缺失，先报告并核对，不从其他目录挑同名文件替代。
后续证据先归档到明确角色目录，不整目录复制 /tmp 实验现场。
