# PRE_FIX_SOURCE_S3R4 -- 修复前源码确认(F2 树 = HEAD:S4 = e124925f…;修复前的行号)

所有行号为修复前 F2 的行号。每条 [源码] 依据均为读取所得,未经运行。

## 1. 806:pattern_get_containment_tree 的 area(S4/pattern/pattern.c)

- 函数定义:pattern.c:782–841。
- 分配:pattern.c:806 `area = (double*)malloc(sizeof(double)*nshapes);`,**无 NULL 检查**。
- 使用:pattern.c:809 `area[i] = shape_area(&shapes[i]);`;pattern.c:815–817 排序读写 area;无其他使用。
- 释放:pattern.c:838 `free(area);`(只在成功路径末尾执行,即 840 之前)。
- 现有返回码(全部在该函数内):
  - 0:成功(pattern.c:789 nshapes==0 与 840 成功路径);
  - −1:nshapes<0(790);
  - −2:shapes==NULL(791);
  - −3:parent==NULL(792);
  - i+1(1..nshapes):shape i 无效(797);
  - nshapes+i+1:shape i 与 j 相交(800)。
  - 注意:第 798 行循环变量 `++i` 写成 `i`,是现有缺陷,本轮不改(超出范围,记入待裁决)。
- 新返回码选择:**−4**。依据:[源码] 该函数内 −4 未被使用;全库 `pattern_*` 中 −4 已用于其他函数(pattern.c:861、907、1061、2136),
  但那些是各自函数的参数错误码,本函数的返回码集合 {0,−1,−2,−3,正整数} 与 −4 不冲突。
  注:−4 在 pattern_discretize_cell 中是 "2 == dim && 0 == det"(1061);调用方 InitSolution 只在 pattern_get_containment_tree
  返回非零时上报,不跨函数比较。新码含义仅限本函数,与 1061 的含义不同,需在注释中写明。
- 调用点:S4.cpp:1730 `int error = Pattern_GetContainmentTree(&L->pattern);`;S4.cpp:1731–1734 `if(0 != error){ S4_TRACE(...); return error; }`。
  即非零直接作为 InitSolution 的返回值向上返回。因此 −4 会直接成为 InitSolution 的返回码(与 S4_internal.h 的约定 "−n = n-th argument invalid" 冲突?
  → 见第 5 节)。

## 2. 415:shape_get_intersection_area_quad 的 POLYGON 分支(S4/pattern/pattern.c)

- 函数定义:pattern.c:301;返回类型 `double`。
- POLYGON 分支:pattern.c:408–447。
- 分配:pattern.c:415 `int *tri = (int*)malloc(sizeof(int)*3*(s->vtab.polygon.n_vertices-2));`,**无 NULL 检查**。
- 第一次使用:pattern.c:430 `polygon_triangulate(s->vtab.polygon.n_vertices, s->vtab.polygon.vertex, tri);`
  (`intersection.c:281–`,`t` 为 NULL 时返回 −3,intersection.c:297,但返回值在 430 处被丢弃)。
- 第二次使用:pattern.c:436–444 循环读取 `tri[3*i+j]`。
- 释放:pattern.c:445 `free(tri);`,随后 446 `return a;`。
- 失败标记选择:**不用负值,不用 NaN**(U93)。原因见 ES3R4-1:[源码] pattern.c:1104 inv_pixel_area 在行列式为负时为负;
  intersection.c:30–36 polygon_area 为带符号的鞋带公式;pattern.c:1116 `a > 0` 过滤负值。负值不能作为失败标记。
- 修复方案(U93):`static double shape_get_intersection_area_quad_st(..., int *status)` 承载原逻辑;
  原函数 `shape_get_intersection_area_quad` 保留签名与行为,作为薄包装调用 `_st` 并丢弃 status。
  tri 为 NULL 时 `*status = 1` 并返回 0.0;成功时 `*status = 0`。
- 调用点:pattern.c:1115 `double a = shape_get_intersection_area_quad(&shapes[k], p0, duv) * inv_pixel_area;`
  (在 pattern_discretize_cell 的 2D 分支,1114 循环内)。
- 上游 pattern_discretize_cell:pattern.c:1044–1139,现有返回码:
  - −1:nshapes<0(1058);−2:shapes==NULL 且 nshapes!=0(1059)及 1079 `RECTANGLE != s->type`;−3:parent==NULL(1060);
  - −4:2D 且 det==0(1061);−5:nu<1(1062);−6:nv<1(1063);−7:iu 越界(1064);−8:iv 越界(1065);−9:value==NULL(1066);0:成功(1138)。
  - 新返回码选择:**−10 已被 pattern_generate_flow_field 使用(pattern.c:2188)、−11 已被 pattern_generate_flow_field 使用(2182)**。
    但 pattern_discretize_cell 与 pattern_generate_flow_field 是不同函数,返回码只在各自函数内有意义;
    **为避免混淆,选 −12**([源码] 全库检索:`grep -rn "\-12" S4/pattern` 与本函数相关处无匹配,见 section 6 的核对)。
  - 注释须写明:−12 = 内部分配失败(shape_get_intersection_area_quad_st 的 tri 分配失败)。
- 调用点(均丢弃返回值):
  - S4/fmm/fmm_FFT.cpp:98 `Pattern_DiscretizeCell(&L->pattern, S->Lr, ngrid[0], ngrid[1], ii[0], ii[1], discval);`
  - S4/fmm/fmm_kottke.cpp:102 同形式调用。
- fmm_FFT.cpp 资源与错误返回:
  - 函数内 `int ret = 0;`(40);分配 work(75,S4_malloc)、discval(83,S4_malloc);
  - 失败返回现有方式:`if(NULL == work){ return 1; }`(76)、`if(NULL == discval){ S4_free(work); return 1; }`(84);
  - 其余失败:`ret = 1; goto cleanup;`(90、188、210、218);
  - cleanup 段(237–245):销毁 plans[0..4]、S4_free(discval)、S4_free(work)、return ret。
  - **U94 方案**:在 98 调用后检查返回值,非零则 `ret = 1; goto cleanup;`(由 cleanup 释放 plans、discval、work)。
- fmm_kottke.cpp 资源与错误返回:
  - `int ret = 0;`(56);work 用 `fft_alloc_complex`(78,不用 S4_malloc);discval 用 S4_malloc(87);
  - 失败返回:`if(NULL == work){ return 1; }`(79)、`if(NULL == discval){ fft_free(work); return 1; }`(88);
  - 其余 `ret = 1; goto cleanup;`(94、268、285、293、309、312);
  - cleanup 段(315–324):销毁 plans、S4_free(discval)、fft_free(work)、return ret。
  - **U94 方案**:102 后检查,非零则 `ret = 1; goto cleanup;`(cleanup 中 work 用 fft_free,保持不变)。

## 3. 1729:S4.cpp 的 L->pattern.parent 分配

- 上下文 S4.cpp:1725–1734:
  ```
  1725  // Initialize the layer pattern
  1726  if(NULL != L->pattern.parent){ free(L->pattern.parent); }
  1729  L->pattern.parent = (int*)malloc(sizeof(int)*L->pattern.nshapes);   // 无 NULL 检查
  1730  int error = Pattern_GetContainmentTree(&L->pattern);
  1731  if(0 != error){ S4_TRACE(...); return error; }
  ```
- **无 NULL 检查**:1729 之后直接调用 Pattern_GetContainmentTree(&L->pattern)。若 malloc 返回 NULL,
  函数第 792 行 `if(NULL == parent){ return -3; }` 返回 −3(pattern.c:792,[源码])。
- InitSolution 的错误码约定:S4_internal.h:253–262:"−n n-th argument is invalid; 0 successful; 1 allocation error; 9..15 其他"。
  因此 1 = allocation error 是现有约定。
- 修复(RP-S3R4-1):parent 为 NULL 时返回 1 并保持 L->pattern.parent 为 NULL(不留悬挂指针)。
  注:第 1729 行之后 `L->pattern.parent` 被赋为 NULL 即可(它已经是 NULL,不需要额外操作)。
  但要注意:1726–1728 已经 free 过旧指针,若不把 L->pattern.parent 设为 NULL,下次 InitSolution 会 double free。
  因此修复必须显式写 `L->pattern.parent = NULL;`(或保证 malloc 结果 NULL 的赋值本身就是 NULL,它是)。

## 4. 修复后 806 的"窗口"(供自检 A 的映射参考)

- 806 的 malloc 在 Pattern_GetContainmentTree 窗口内(pattern_get_containment_tree 被 S4.cpp:1730 调用)。
- 1729 的 malloc 在 InitSolution 内,先于 1730。

## 5. 返回码冲突的核对

- 806 新码 −4 在 pattern_get_containment_tree 内唯一;与 S4.cpp:1731–1733 的 "非零直接向上返回" 相容。
  但 InitSolution 的约定里 "−n = n-th argument invalid",−4 会被解释成 "4th argument invalid"。这与 "内存分配失败" 语义冲突。
  → 需要修正:806 的 area 分配失败应向 InitSolution 报告 **1(allocation error)**,这与 RP-S3R4-1 的 1 一致。
  因此 pattern_get_containment_tree 的 area 失败码应为一个 **不会被 InitSolution 误解** 的值。
  方案:**返回 −4 在 pattern.c 内部并在 S4.cpp:1731 之前映射为 1**?—— 这会改动 S4.cpp 的 1730–1734 附近逻辑(属于 U91 范围内,但超出 "只改 1729 附近" 的字面范围)。
  **停下点**:此处需用户裁决(见 ERRATA_S3R4.txt ES3R4-4)。在裁决前不修改 806 的返回值。

## 6. 核对命令的结果

(见 $EV/SOURCE_CHECK_S3R4.txt,由 safe_run 生成。)
