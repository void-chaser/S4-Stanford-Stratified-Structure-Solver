# P05-S2R6 勘误：fmm_kottke 不是"未修好的红点"

> **状态：未完成，等待用户审核。** 本文件是对 `P05_S2R6_CLOSEOUT.md` 的追加勘误，**不改写原报告**（历史报告不改写）。
> 本文件不宣布 P05-S1、S2、S3、S4 任一阶段完成，不代替用户签收 S2。

## 1. 被更正的陈述

`checkpoints/p05/P05_S2R6_CLOSEOUT.md` 第 201 行：

> `fmm_kottke:78`（S3 声称已处理、装置显示未修好的点）：本轮 S2R6 **未修**，仍为最高优先级红点。本轮 REG_3B 的 H 行与 S2R3 逐行相同，未改变其状态。

该陈述**不成立**。

## 2. 依据（均为仓库内已有记录）

| 来源 | 内容 |
|---|---|
| `P05_S2R6_CLOSEOUT.md` 第 223–224 行（同一份报告） | kottke work（`fft_alloc_complex(6*ng2)`，n=384，family D）：B=CRASH，A=REPORTED_FAILURE（rc1 20），H=REPORTED_FAILURE（rc1 20）；kottke discval（`S4_malloc`，16 B，NTH 1）：B=CRASH，A、H=REPORTED_FAILURE（rc1 20） |
| `P05_S2R2_HARNESS_CLOSEOUT.md` 第 379 行 | "它们是**已确认修好**的点，不是红点。本报告未发现 S3 声称已修而装置显示未修好的点。" |
| `P05_S2R3_HARNESS_GAPS.md`（8.3 节与续作二结论） | kottke 两点在 H 上均为 REPORTED_FAILURE，"未观察到未修好的情形" |

## 3. 更正后的陈述

- `fmm_kottke` 的两个分配点（`fft_alloc_complex` work 与 `S4_malloc` discval）在 A、H 两棵树上，注入分配失败后均为 REPORTED_FAILURE（rc1 20），在 B 树上为 CRASH。这是**装置观察**，不是 P05-S4 验证。
- `fmm_kottke:78` **不是**红点，也不是最高优先级项。
- 本轮没有发现"S3 声称已处理而装置显示未修好"的点。

## 4. 错误的来源

"fmm_kottke:78"作为"S3 声称已处理而装置显示未修好的点"的**举例**，最早出现在审核方给执行者的提示词和长期记忆条目里，本意是说明规则（若出现此类点，记为最高优先级红点），不是断言 kottke 存在该问题。执行者把举例当成了事实。审核方对此负责。长期记忆条目已于同日更正。

## 5. 未更正、仍然有效的内容

`P05_S2R6_CLOSEOUT.md` 的其余内容（统一入口、复现自检、驱动二进制 1/12 逐字节相同、历史 38 案为分类重放、六条违规记录等）**不受本勘误影响**。其中第 8 节未闭合缺口 1–5 仍然有效，需用户裁决。

## 6. 对下游的影响

- S3 补充收尾和 P05-S4 的输入中，不得再出现"fmm_kottke:78 为最高优先级红点"。
- 对 S2 的"未闭合缺口"没有影响。
