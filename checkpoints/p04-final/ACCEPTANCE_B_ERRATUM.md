# ACCEPTANCE_B 行 3 勘误（撤销误报）

日期：2026-10-10（Australia/Sydney）

## 对象与保留

- 被勘误的原记录：`.p04-review/remediation/acceptance/acceptance-B-rows1-4-20261010/ACCEPTANCE_B_ROWS1-4.md`，SHA256 `64149930e3094f85d3132413d712e642c1a30c4a1405e86cb17a15a3f4852f07`。原文件保留，未覆盖。
- 本勘误不改写原记录，不改 `hashes.txt`，不要求负责人重新签 B。

## 撤销的内容

原记录第“本次新发现的核验缺口（未在闭环表中披露）”一节作废，包括以下三点：

1. 把 `hashes.txt` 的 12 个条目说成“保存目录内无法核验”。
2. 把 `build-seam-asan/libS4.a`、`build-seam-asan/S4k/rcwa.o` 与 `../lsan_controls/lost.c` 说成“不在保存目录内，无法核验”。
3. 据此把行 3 的 B 接受范围缩小为“不含上述条目”。

这些表述是误报。我当时把 `hashes.txt` 的全部条目都相对证据目录解析，没有核对 `round6/rcwa-failure-workspace/env.txt` 记载的 `tree=.p04-review/remediation/round6/src`，也没有按各条目真实来源分别解析。

## 正确解析（以第六轮独立审核记录和本次核验为准）

依据：`.p04-review/acceptance-B-followup-audit/REVIEW.md`（SHA256 `dd81d4face5dc57ba63749a114e7e2f17bb5e6d92e7ce763350c6a791487105f`）与 `ROW3_BINDINGS.json`（SHA256 `e93a137ad7d0f16c47d3c8b3b7cccc09d8747b617d131dbb61342069ef5078b5`）。

| 条目 | 解析根 | 期望与实际 |
|---|---|---|
| `S4/rcwa.cpp`、`S4/rcwa.h`、`S4/RNP/Eigensystems.cpp`、`testing/s4test/test_seams/seam.h` | `.p04-review/remediation/round6/src/` | 逐项相同 |
| `build-seam-asan/libS4.a`、`build-seam-asan/S4k/rcwa.o` | 同上 | 逐项相同 |
| `owned_failure_rcwa.cpp` | `remediation/repo/checkpoints/p04-remediation/repro/rcwa_failure_workspace/` | 相同 |
| `../lsan_controls/lost.c`、`freed.c`、`reachable.c` | `remediation/repo/checkpoints/p04-remediation/repro/lsan_controls/` | 相同 |
| `run.sh`、`check_results.py` | `remediation/repo` Git `4b20233` 的历史 blob | 相同 |
| 五个运行/控制二进制 | `.p04-review/remediation/round6/run-rcwa-final/` 绝对路径 | 相同 |

## 本次独立复核

- 直接重算 15 个文件哈希，全部与期望一致。
- `run.sh` 与 `check_results.py` 的 Git blob（`remediation/repo`，`4b20233`）经 `sha256sum` 复算，分别为 `74db3a91…62ae` 与 `49cfc72a…f405`，与期望一致。
- `ROW3_BINDINGS.json` 共 17 条，`match` 字段全为 true；15 条实际重算一致，2 条为 Git blob 复算一致。
- 本次没有重跑构建，也没有动态运行，只做保存文件与历史 blob 的摘要核对。

17/17 是保存文件与历史 blob 的摘要匹配，不是独立重建，也不是独立动态 LSan 认证。

## 对 B 接受的影响

- 行 1–4 的 B 接受不变：按负责人原文采用保存证据验收，原覆盖限制保持，不是独立动态 LSan 认证。
- 行 3 的 B 接受对象不因误报而缩小：它包括 round6 保存运行与当时所用的历史脚本（`run.sh`、`check_results.py` 的 `4b20233` 版本）。
- `run.sh` 与 `check_results.py` 的当前复现副本与历史版本不同，这是历史 provenance 差异。已在第八轮记录中披露，不能拿当前修正版本做错误比较。

## 授权来源

负责人对行 1–4 的 B 决定原文记录在上述 B 记录的“负责人原文”一节，且与本次会话中用户消息一致。本勘误未新增任何批准。

## 未改动

未修改主检出、候选、round6 保存目录、`hashes.txt` 或用户现场文件（`.gitignore`、`testing/s4test/DEFECTS.md` 与其他未跟踪文件）。
