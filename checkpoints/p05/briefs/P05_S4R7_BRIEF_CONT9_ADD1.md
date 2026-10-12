# P05-S4 R7 续 9 补充 1:G6 驱动差异、U82 例外的认定方式、U38 的补充依据

先用 write 把本补充原文存为 checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT9_ADD1.md。续 9 的其他条款仍然有效。

## 用户裁决(用 edit 追加到 ERRATA_7.txt 与 RULINGS.tsv)
- U84:dbg 库和驱动的哈希与 R5、R6c 不同,只要能证明差异只在调试段,就接受(G5 与 G6 都适用)。
  证明方法(新脚本 check_dbg_strip_equiv_r7.sh,经 safe_run 运行,输出写到 $EV/):
  对 R7 与历史的每一对文件,即
    G5:R7 F-dbg 库 / R5 dbg F 库(b95712a4…);R7 r6bstate-F-dbg 驱动 / R6c 历史驱动;
    G6:R7 seamF-F、fmmret-F dbg 库 / R6c 的 seamF(26e4ba…)、fmmret-F 库;对应的驱动 / driver-r6b-seamF(7f0bf3b6…)、driver-r6b-fmmret-F,
  先复制到 $EV/strip_cmp/,再做 `objcopy --strip-debug`(只处理副本),然后比较 sha256。
  静态库(.a)请逐个成员比较,或者先解包再逐个 .o 去调试段后比较,避免 ar 头中的时间戳影响结果。
  全部相同:写 E7-37 "差异只在调试段",继续。有任何一对不同:停下报告,不要用解释代替。
  "编译选项差异 0 项" 按源码与编译命令行判断(执行者已核对);DWARF 路径不算编译选项差异。
- U85:U82 的例外数按 [源码] 构造性排除登记为 0,不做 gdb 调用栈探测。依据(写进预注册表头和 E7-38):
  (a) 177 点的注入方式只有 exec、plan、plancall:K:M、s4malloc 四种(RESULTS_R6c_STATE.tsv 的 request 列);
  (b) exec、plan、plancall 只在 arm 为 1 或 2 时生效(inject_r4_plan.cpp:79–100),arm 只在 fft plan 创建或执行的包装函数里置位(:588–615);
  (c) s4malloc 只截获 S4_malloc(__wrap__Z9S4_mallocm,:496–501);
  (d) S4/pattern/pattern.c 中没有 S4_malloc 调用(计数 0),也不调用 fft;
  因此这 177 个点在构造上不可能落到 pattern_generate_flow_field 窗口里。
  G6 的 25 个 seam 点:seam 补丁不修改 pattern.c(seamdiff 中 pattern.c 出现 0 次),同样登记为 0。
  F 基线对照(U81)与 F2 结果仍然要逐点比较,作为运行时的保障。
- U86:U38 分类的补充依据(执行者核对后写入 PATTERN_MALLOC_CLASS_R7.tsv;分类只是建议,裁决归用户):
  · 415(shape_get_intersection_area_quad,POLYGON 分支):调用者是 pattern_discretize_cell(pattern.c:1115),
    后者被 fmm_FFT.cpp:98 与 fmm_kottke.cpp:102 调用,所以 415 在 FFT/Kottke 的失败传播链上,只在多边形形状时触发;
    执行者原先写的 "面积积分路径" 不准确,建议改为 IN_D003_CANDIDATE(多边形条件)。
  · 528(shape_get_intersection_area):核对 S4/、ext/、modules/、S4r/ 中是否有调用者;没有就写 "无调用者(疑似死代码)",建议 OUT_OF_SCOPE 或 UNCLEAR。
  · 1164(fprint_double):唯一调用者 fprint_spmatrix,其唯一调用点在 pattern.c:1642,已被注释掉;建议 OUT_OF_SCOPE(调试输出,不可达)。
  · 806:同执行者的意见(IN_D003_CANDIDATE)。
  每一条都要列出 grep 或 read 的依据(文件:行号)。

## 继续执行
按续 9 第 2 节完成准备:LINEMAP_M3_R7.tsv、DRIVERS_R7_M3.tsv、check_dbg_strip_equiv(U84)、REGISTRY_S4_PRE_R7_M3.tsv
(表头写上 U85 的构造性排除依据,例外 0 行)、dry-run;追加 E7-36..E7-38 与 U79–U86;同步 STATE;提交准备。
然后按续 9 第 3–5 节跑 F 基线(m3f1)→ F2(m3r1)→ U38 分类 → R7 收尾。
除续 9 第 6 节的停止条件和 U84 的 strip 比较不同以外,不再中途停下请求确认;
遇到任务书没有覆盖的问题,在 ERRATA 中写明处理方式与理由,只要不改期望、不改判定器,就继续执行。
