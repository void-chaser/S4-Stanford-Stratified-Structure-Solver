# P05-S4 R7 续 9 补充 2:U84 的 build-id 边界

先用 write 把本补充原文存为 checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT9_ADD2.md。续 9 及补充 1 的其他条款仍然有效。

## 用户裁决(用 edit 追加到 ERRATA_7.txt 与 RULINGS.tsv)
- U87:U84 补充。可执行文件的 .note.gnu.build-id 是链接器对全部输入(包括调试段中的构建路径)计算的哈希,
  调试段一变,它就跟着变,不影响程序行为。U84 没有预先写明这一点(规划者遗漏)。执行者按字面停下是正确的。
  证明方法改为 "去调试段 + build-id 清零":
  (a) 对 $EV/strip_cmp/ 中已去调试段的副本(r7.stripped、hist.stripped)再各复制一份 *.masked;
  (b) 用 readelf -n 读出每个文件 build-id 描述符的偏移与长度(在 .note.gnu.build-id 段的文件偏移 + 16 处,长 20 字节;以 readelf 实际读出的为准),
      只把这 20 字节清零(新脚本 mask_build_id_r7.py,经 safe_run 运行,只处理 *.masked 副本);
  (c) 比较 *.masked 的 sha256。三对驱动全部相同:通过;有任何不同:停下报告。
  不使用 objcopy --remove-section(删段会改变文件布局)。
  预期(INFLUENCED,规划者已只读核对):三对驱动去调试段后都只差 20 字节,位于偏移 864–883,
  全部落在 .note.gnu.build-id(偏移 0x350,长 0x24)之内,清零后应当相同。
  库(24 个成员 × 3)已 EQUAL_AFTER_STRIP,不需要再处理。
  E7-37 写:"三个库去调试段后逐成员相同;三个驱动去调试段并将 build-id 清零后逐字节相同;差异只来自调试段及由它导出的 build-id"。
- U88:违规记录。在 $EV/tmp/probe_strip/ 中直接用 bash 执行 rm -rf、mkdir -p、ar x,没有经过 safe_run,
  违反续 5 第 0 节 A(写入);写入位置在 $EV 内,没有越界。记入表二(E7-39),目录保留,不删除。
  从下一条命令起,所有写入都经 safe_run 或 edit/write,包括探测和临时解包。

## 继续执行
1. 运行 mask_build_id_r7.py 与比较,结果写 $EV/strip_cmp/MASKED_EQUIV_R7.tsv。
2. 通过后:追加 E7-36..E7-39 与 U79–U88;按续 9 第 2 节完成 LINEMAP_M3_R7.tsv、DRIVERS_R7_M3.tsv、
   REGISTRY_S4_PRE_R7_M3.tsv(表头写 U85 的构造性排除,例外 0 行)、dry-run;同步 STATE;提交准备
   (包括 check_dbg_strip_equiv_r7.sh、link_r6b_seam_r7.sh、mask_build_id_r7.py,以及 STRIP_EQUIV、MASKED_EQUIV 两张表的副本)。
3. 然后按续 9 第 3–5 节跑 F 基线(m3f1)→ F2(m3r1)→ U38 分类 → R7 收尾。
   除续 9 第 6 节的停止条件,以及 MASKED 比较不同或写入规则被违反之外,不再中途停下。
