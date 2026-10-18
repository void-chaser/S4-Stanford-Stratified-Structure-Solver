# P05-S5 计划草案（P05_S5_PLAN_DRAFT）

> 本文件是 S5R2 及收口的计划草案，不表示任何阶段完成或签收。
> 输入：checkpoints/p05/registries/s5r1/S5_INPUTS_S5R1.tsv、S5_TRIAGE_S5R1.tsv、P05_ACCEPTANCE_MAP_S5R1.tsv。

## 1. S5R2 范围（NEEDS_TEST 项）

本轮分类统计：REGISTRY_ONLY=5、NEEDS_TEST=3、NEEDS_FIX_NEW_DEFECT=1、RECORD_ONLY_OPEN=6、NEEDS_USER_RULING=10；needs_user_ruling=YES 共 12 行；blocks_P06_D004=YES 共 2 行。

NEEDS_TEST 项（S5R2 预注册并实测）：

| 编号 | 事项 | 期望值登记方式 |
|---|---|---|
| S5-C-01 | D016 的 Python 公共异常文本（n_G=1 零场） | 运行前写 PREREG_S5R2_D016.tsv 并记录 sha256；期望：公共 API 抛 RuntimeError、驱动 rc 20、根因处返回 -10（源码映射） |
| S5-D-01 | D003 验收标准的前端观测（Python/Lua 可见失败、恢复重试） | 运行前写 PREREG_S5R2_E2E.tsv + sha256；期望：注入点 rc 非零且 Python/Lua 可见同一错误；同对象重试等于参考值；新对象/新进程重试等于参考值 |
| S5-D-06 | PROJECT_ROADMAP P05 行验收标准的逐条映射 | 映射表本身在 S5R1 已提交（P05_ACCEPTANCE_MAP_S5R1.tsv），S5R2 只做增量核对；不改写验收标准 |

## 2. 需要的驱动与前端

- Python：公共 API 正常路径 + 注入失败路径 + 同对象重试 + 新进程重试；覆盖 FFT/Jones/NV/VL 点族（沿用 testing/d003/stage_s4r9/e2e_python_r9m3b.py 的装置思路，新脚本按 S5R2 编号另建，不改历史装置）。
- Lua：REPL 覆盖 cf/fft/kt/vl 四族（与 U345/U359(e) 的范围声明一致）；失败、可见报错、重试恢复。
- 预注册：所有期望值必须先写入预注册 tsv 并记录 sha256；受历史观察影响的标 INFLUENCED；不得事后改期望（只允许新建 *_ERRATA*）。

## 3. 预计运行量

- S5R2 前端点族：Python 每族正常/失败/同对象重试/新进程重试 4 类，5 族约 20 点；Lua REPL 4 族约 8 点；合计约 28 点，两遍约 56 次运行。
- 若 Q1 裁决为需独立复跑以作 S5 证据，则追加 M3b E2E 的 25 点两遍（约 50 次）。
- 复用既有驱动/库时先核对 sha256，不重建 S4 产物（S5 只读 F4 冻结树）。

## 4. S5 收口条件（草案，待用户确认）

1. NEEDS_TEST 项全部完成预注册 + 正式实测，预期值一致（MISMATCH 0）。
2. NEEDS_USER_RULING 项全部经用户裁决，或明确保持开放并写入 S5 报告的范围声明。
3. P05_ACCEPTANCE_MAP_S5R1.tsv 的 GAP 行清零或经用户裁决；NEEDS_USER_RULING 行（AC-3/AC-4）有裁决结论。
4. 仅改文档/登记表的项（REGISTRY_ONLY、RECORD_ONLY_OPEN、NEEDS_FIX_NEW_DEFECT）写入登记表草案并落实。
5. STATE.md 不超过 8192 B；门禁 CHECK_CRASHED=0；证据 SHA256SUMS 全 OK。
6. 不宣布 P05 完成；P05-S5 签收只由用户在对话中给出。

## 5. 需用户裁决的问题（Q1..Q8，附推荐）

| 编号 | 问题 | 推荐选项与理由 |
|---|---|---|
| Q1 | M3a/M3b 的 make test 与 E2E 结果能否作为 S5 前端与回归的已提交证据？ | 推荐：可引用，但 S5R2 至少复跑一遍前端 E2E。理由：M3b 在 F4 上有预注册与 U352 独立复核（DIFFS=0），完全重审成本高；但修复前证据不得称修复后验证，S5 若零运行只引用旧证据，界线会模糊。 |
| Q2 | D016 的 Python 公共异常文本是否需在 S5R2 实测？ | 推荐：需要。理由：S3R2 只做了源码映射与驱动级观测（P05_S3R2_CLOSEOUT.md 186/187 行），而 P05 验收含 Python/Lua 可见失败，D016 正是可见失败点。 |
| Q3 | F10 历史因果（S5-B-01）是否需在 S5 补历史输入？ | 推荐：不需要，保持 OPEN 并转后续。理由：D016 修法不依赖 F10 因果；提供历史负载输入的成本高且不在 S5 范围。 |
| Q4 | F8 历史候选目录哈希（S5-B-02）是否授权访问历史目录？ | 推荐：不授权，保持未验证。理由：S5 修复对象是当前仓库源码，不引用历史候选目录的 bit 级一致性。 |
| Q5 | R-P05-01 的反事实通量正确性 + allzero 设计意图是否在 S5 处理？ | 推荐：不在 S5 处理，保持 OPEN。理由：需独立参考解与设计意图确认，属行为变更而非失败传播；S5 只登记。 |
| Q6 | S1 报告 11.2 的 5 个哈希来源（S5-B-05..09）如何处置？ | 推荐：用户确认来源或明确保持未验证，不改写 11.2 与 EVIDENCE.sha256。理由：现有证据无法区分抄写错误与较早时刻内容。 |
| Q7 | 非 FMM S4_malloc（S5-M3D-04）另立登记号是否用 D017？ | 推荐：D017。理由：ISSUE_REGISTRY 更新规则规定新缺陷从 D016 起追加；D016 已被占用。 |
| Q8 | ES3R4-5/528/1164、U99、U100（S5-M3D-03）登记为独立 R-P05-02/R-P05-03 是否可接受？ | 推荐：可接受。理由：它们均 OUT_OF_SCOPE_D003，不是 P05 修复项，独立登记可保持 D003 范围清晰。 |

## 6. 预注册与文件命名

- 预注册文件：checkpoints/p05/registries/s5r2/PREREG_S5R2_*.tsv + .sha256.txt，在正式运行之前提交。
- 运行脚本：testing/d003/stage_s5r2/，文件名带 s5r2；门禁与收尾链同 S5R1 结构。
- 证据目录：checkpoints/p05/evidence/p05-s5r2/；小表复制到 checkpoints/p05/registries/s5r2/。

