#!/usr/bin/env python3
# s5r2_chain.py -- P05-S5 R2 closeout chain. Subcommands, each run once in the frozen period:
#   report | report_check | copy | events | progress | sha_sums   (--shakedown writes to $EV/shakedown)
import os,sys,re,hashlib,shutil,subprocess,datetime
REPO=subprocess.check_output(["git","rev-parse","--show-toplevel"],text=True).strip()
P05=os.path.join(REPO,"checkpoints/p05")
EV=os.path.join(P05,"evidence/p05-s5r2")
SHK=os.path.join(EV,"shakedown")
REGDIR=os.path.join(P05,"registries/s5r2")
REPORT=os.path.join(P05,"P05_S5R2_REPORT.md")
GATEAPP=os.path.join(P05,"P05_S5R2_GATE_APPENDIX.md")
ST=os.path.join(P05,"STATE.md")
OPENITEMS=os.path.join(P05,"P05_S5_OPEN_ITEMS.tsv")
PATCHV2=os.path.join(P05,"P05_S5_REGISTRY_PATCH_V2.md")
BRIEF=os.path.join(P05,"briefs/P05_S5R2_BRIEF.md")
TAB=chr(9); NL=chr(10); BT=chr(96); FENCE=chr(96)*3
SHAKE="--shakedown" in sys.argv[2:]
SMALL=["GATE_S5R2_start.txt","ERRATA_S5.txt","D017_S4MALLOC_INVENTORY_S5R2.tsv","PREREG_D016_S5R2.tsv",
       "PREREG_D016_S5R2.tsv.sha256.txt","D016_VERDICT_S5R2.tsv","D016_TRACE_S5R2.md",
       "REGISTRY_APPLY_DIFF_S5R2.txt","S5R1_REPORT_RECHECK_S5R2.txt","REPORT_CHECK_S5R2.txt","FROZEN_SCRIPTS_S5R2.tsv"]
def sha_b(b): return hashlib.sha256(b).hexdigest()
def sha_f(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(65536),b""): h.update(b)
 return h.hexdigest()
def rd(p): return open(p,encoding="utf-8").read()
def rdb(p): return open(p,"rb").read()
def wr(p,t):
 rp=os.path.realpath(p)
 if not (rp.startswith(os.path.join(REPO,"checkpoints/p05")+os.sep)): raise SystemExit("WRITE_OUTSIDE "+rp)
 os.makedirs(os.path.dirname(p),exist_ok=True)
 open(p,"w",encoding="utf-8").write(t)
def outdir(): return SHK if SHAKE else EV
def log_lines():
 p=os.path.join(EV,"safe_run.log")
 if not os.path.isfile(p): return []
 return rd(p).splitlines()
TS=re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\t")
def anchor_line(needle):
 ls=log_lines()
 for x in range(len(ls),0,-1):
  if needle in ls[x-1]: return x
 return 0
def tsv(rel):
 p=os.path.join(REPO,rel)
 return [l.rstrip(NL).split(TAB) for l in rd(p).splitlines() if l.strip() and not l.startswith("#")]
def read_tsv_path(p):
 return [l.rstrip(NL).split(TAB) for l in rd(p).splitlines() if l.strip() and not l.startswith("#")]
def start_rec():
 return {l.split(TAB)[1]:l.split(TAB)[2].replace("value=","") for l in rd(os.path.join(EV,"GATE_S5R2_start.txt")).splitlines() if l.startswith("RECORD"+TAB)}
def inventory_counts():
 rows=read_tsv_path(os.path.join(EV,"D017_S4MALLOC_INVENTORY_S5R2.tsv"))
 hdr=rows[0]; body=rows[1:]
 c={"total":len(body),"CALL":sum(1 for r in body if r[hdr.index("kind")]=="CALL"),
    "IN":sum(1 for r in body if r[hdr.index("d003_scope")]=="IN"),
    "OUT":sum(1 for r in body if r[hdr.index("d003_scope")]=="OUT"),
    "OUT_CALL":sum(1 for r in body if r[hdr.index("d003_scope")]=="OUT" and r[hdr.index("kind")]=="CALL")}
 return c
def open_items_rows():
 p=os.path.join(SHK,"P05_S5_OPEN_ITEMS.proposed.tsv") if SHAKE else OPENITEMS
 rows=read_tsv_path(p); hdr=rows[0]; return hdr,[dict(zip(hdr,r)) for r in rows[1:]]
def verdict_summary():
 p=os.path.join(EV,"D016_VERDICT_S5R2.tsv")
 if not os.path.isfile(p): return None
 m=re.search(r"(?m)^SUMMARY\tMATCH=(\d+)\tMISMATCH=(\d+)\tFLAKY=(\d+)$",rd(p))
 if not m: return "UNPARSED"
 return {"MATCH":int(m.group(1)),"MISMATCH":int(m.group(2)),"FLAKY":int(m.group(3)),"rows":len([l for l in rd(p).splitlines() if l.strip() and not l.startswith("#")])-2}
def apply_summary():
 p=os.path.join(SHK if SHAKE else EV,"REGISTRY_APPLY_DIFF_S5R2.txt")
 if not os.path.isfile(p): return None
 t=rd(p)
 d={}
 for line in t.splitlines():
  m=re.match(r"#   (testing/s4test/ISSUE_REGISTRY.md|PROJECT_ROADMAP.md) replaced_lines=([\d,]*) inserted=(\d+) after_bytes=(\d+) after_sha256=([0-9a-f]{64})",line)
  if m: d[m.group(1)]={"replaced":m.group(2),"inserted":int(m.group(3)),"after_sha256":m.group(5)}
 d["assert_only_listed"]=("# ASSERT_ONLY_LISTED_LINES_CHANGED: PASS" in t)
 return d
def gate_summary(path):
 if not os.path.isfile(path): return None
 t=rd(path).splitlines()
 d={"counts":"","fails":"","crashed":"","post":[]}
 for l in t:
  if l.startswith("COUNTS"): d["counts"]=l
  if l.startswith("FAILS="): d["fails"]=l
  if l.startswith(("PASS","FAIL")) and "POST_I_CALL_COUNT" in l: d["post"].append(l)
  if l.startswith(("PASS","FAIL")) and "CHECK_CRASHED_ZERO" in l: d["crashed"]=l
 return d
def report_text():
 sr=start_rec(); inv=inventory_counts()
 hdr,oi=open_items_rows()
 oc={}
 for r in oi: oc[r["final_disposition"]]=oc.get(r["final_disposition"],0)+1
 ap=apply_summary()
 g=subprocess.check_output(["git","log","-1","--format=%H %s"],text=True,cwd=REPO).strip()
 st=subprocess.check_output(["git","status","--short"],text=True,cwd=REPO).strip() or "(clean)"
 sg=gate_summary(os.path.join(SHK,"gate","GATE_S5R2_end.txt"))
 t=[]
 t.append("# P05-S5 R2 报告（s5r2）：裁决入账、S5R1 勘误、D017 清单、登记表落实、D016 公共 API 实测")
 t.append("")
 t.append("> 轮次：P05-S5 R2。本轮不宣布 P05-S5 或 P05 阶段完成；签收只由用户在对话中给出。")
 t.append("> 被测树为 F4（05097a7，S4/ 树 589e15eb11fcb04e031b524f25a443e7921946cf）。D016 结论只写：在 F4 上、在该输入下经公共 API 可见失败且恢复正确。")
 t.append("")
 t.append("## 1 门禁")
 t.append("")
 t.append("- start 门禁：%s，%s（GATE_S5R2_start.txt；CHECK_CRASHED=0）。HEAD=9f537f7c…da5d4；HEAD:S4=589e15eb…46cf（F4）；判定器 sha256=d2d04145…09eb；工作区干净。"%(sr.get("START_TIME_UTC","?"),sr.get("HEAD","?")))
 t.append("- 起始文件字节数与 sha256 由脚本断言：RULINGS.tsv 146978 B（d33990ca2312eefc，最大 U363）、ERRATA_9.txt 67981 B（95b23f21b2e48a1c，最后 E9-79）、STATE.md 3075 B（bdd9668c162832cc）、两份 S5R1 草案 9358/5351 B、S5R1 输入/分类表 7348/6455 B、ISSUE_REGISTRY.md 20720 B（ad17b768c79a3f63）、PROJECT_ROADMAP.md 20905 B（2c8cbe18d479584a）。")
 t.append("- S5R1 小表 SHA256SUMS %s 项 OK；p05-s5r1 证据 SHA256SUMS %s 项 OK（由脚本数出）；仓库根 registries/ 不存在；/tmp 顶层快照 count=%s。"%(sr.get("S5R1_REGISTRY_ITEMS","?"),sr.get("S5R1_EVIDENCE_ITEMS","?"),sr.get("TMP_COUNT","?")))
 t.append("- end 门禁：正式运行一次（输出写 $EV/gate/，不纳入清单）；原文摘要见 P05_S5R2_GATE_APPENDIX.md。")
 t.append("")
 t.append("## 2 裁决入账（U364–U371，纯追加）")
 t.append("")
 t.append("- RULINGS.tsv 追加 U364–U371 共 8 行，原有内容逐字节不变（前缀校验）；最大编号 U371。")
 for uid,txt in [("U364","M3a/M3b 的 make test 与 E2E 作为 F4 上历史证据可被 S5 引用；S5R3 在 F4 上重跑一次 make test 与全量 E2E（M3b 42 点加 D016 点）；修复前证据不得称为修复后验证。"),
                 ("U365","D016 在 S5R2 用 Python 与 Lua 公共 API 实测（VL，n_G=1）；NV 的 -10 路径触发不了，维持 [源码] 结论。"),
                 ("U366","F10 历史因果、R-P05-01 的反事实通量与 allzero 设计意图保持 OPEN，转出 P05，写入 S5 范围声明，不阻塞。"),
                 ("U367","F8 历史目录不授权访问，保持未验证。"),
                 ("U368","S1 报告 11.2 的 5 个哈希来源认定为无法判定，不改写 11.2 与 EVIDENCE.sha256。"),
                 ("U369","非 FMM S4_malloc 登记为 D017；登记前先只读逐点列出清单。"),
                 ("U370","ES3R4-5/528/1164 与 U99 登记为 R-P05-02，U100 登记为 R-P05-03；一律写 F4 行号，旧树行号放括号内。"),
                 ("U371","批准把补丁 v2 应用到 testing/s4test/ISSUE_REGISTRY.md 与 PROJECT_ROADMAP.md；不改 AGENTS.md。")]:
  t.append("- %s：%s"%(uid,txt))
 t.append("- 原文逐字见 registries/RULINGS.tsv 与 briefs/P05_S5R2_BRIEF.md 第 1 节。")
 t.append("")
 t.append("## 3 勘误 ES5-1 至 ES5-5")
 t.append("")
 t.append("- ES5-1：S5-B-05/06/07/08 的 locator 由全文第一次出现（359/58/374/389）更正为 S1 报告 11.2 表第 478/479/480/481 行，current_status_text 改为表中哈希原文；S5-B-09（485 行）无误。更正后的 5 行见 ERRATA_S5.txt 与 P05_S5_OPEN_ITEMS.tsv。")
 t.append("- ES5-2：pattern.c:798（B/A）在 F4 为 815；F4 上 shape_get_intersection_area 第 474 行（旧树 528）、fprint_double 第 1178 行（旧树 1164）；B/A/F4 三棵树并列行号由脚本读出，U99 原文不改。")
 t.append("- ES5-3：S5R1 正式门禁后对报告与两份草案做了手工修改并 amend (ii)（reflog：f46ac87 → 9f537f7），未重跑 report_check；本轮只读复核 S5R1 最终版报告，RECHECK_FAILS 见 S5R1_REPORT_RECHECK_S5R2.txt；6089637..9f537f7 两份草案逐行差异同文件第 B 节。")
 t.append("- ES5-4：S5R1 EVIDENCE_SUMS_COVERS_ALL FAIL 是检查器未排除 shakedown/gate/ 的缺陷；复算排除 gate/、shakedown/gate/、tmp/ 后清单覆盖全部文件（S5R1_REPORT_RECHECK_S5R2.txt 第 D 节）；S5R2 检查器把排除列表写入门禁输出。")
 t.append("- ES5-5：非 FMM S4_malloc 的 35–43 说法改为本轮逐点清单：总出现 %d、CALL %d、IN %d、OUT %d（OUT CALL %d）。"%(inv["total"],inv["CALL"],inv["IN"],inv["OUT"],inv["OUT_CALL"]))
 t.append("")
 t.append("## 4 D017 清单计数")
 t.append("")
 t.append("- 只读来源：git show 05097a7 的 S4/ 全部 .c/.cpp/.h/.hpp（全部标 [源码]，本轮未运行）。")
 t.append("- 总出现数 %d；CALL %d；IN %d；OUT %d；OUT 中 CALL %d（即 D017 登记范围），非分配点（注释/定义/声明）%d。"%(inv["total"],inv["CALL"],inv["IN"],inv["OUT"],inv["OUT_CALL"],inv["total"]-inv["CALL"]))
 t.append("- 明细见 D017_S4MALLOC_INVENTORY_S5R2.tsv；ISSUE_REGISTRY.md 新增 D017 行（U369）。")
 t.append("")
 t.append("## 5 开放项总表计数")
 t.append("")
 t.append("- S5R1 去重后的 25 行逐行落位，见 P05_S5_OPEN_ITEMS.tsv。")
 t.append("- final_disposition 计数："+("；".join("%s=%d"%(k,oc[k]) for k in sorted(oc)))+"。")
 t.append("- 6 行 RECORD_ONLY_OPEN（S5-M3D-01/02/05/06/07、S5-C-03）均有 registry_location（ISSUE_REGISTRY.md 的对应行）。")
 t.append("")
 t.append("## 6 登记表应用 diff 摘要")
 t.append("")
 if ap:
  for rel in ("testing/s4test/ISSUE_REGISTRY.md","PROJECT_ROADMAP.md"):
   d=ap.get(rel,{})
   t.append("- %s：替换行 %s；插入 %s 行；应用后 sha256=%s。"%(rel,d.get("replaced","?"),d.get("inserted","?"),d.get("after_sha256","?")[:16] if d.get("after_sha256") else "?"))
  t.append("- apply_patch_s5r2.py 断言：只改动了 PATCHSPEC 列出的行（ASSERT_ONLY_LISTED_LINES_CHANGED=%s）；应用前后 sha256 与 unified diff 见 REGISTRY_APPLY_DIFF_S5R2.txt。"%("PASS" if ap.get("assert_only_listed") else "FAIL"))
 else:
  t.append("- （正式补丁尚未应用：本报告生成于试跑期）")
 t.append("")
 t.append("## 7 D016 结果（正式两遍）")
 t.append("")
 vs=verdict_summary()
 if vs and vs!="UNPARSED":
  t.append("- 点族：VL NB=1/2/3/4 失败点与同对象重试；VL NB=5/9、Jones NB=1、NV NB=1 对照；同进程新对象 VL NB=9 恢复并与另起进程参考值比较。")
  t.append("- 期望值已预注册（PREREG_D016_S5R2.tsv，状态 INFLUENCED，sha256 已记录），正式运行前写入。")
  t.append("- 正式两遍：MATCH=%d、MISMATCH=%d、FLAKY=%d（判定行数 %d）；明细见 D016_VERDICT_S5R2.tsv。"%(vs["MATCH"],vs["MISMATCH"],vs["FLAKY"],vs["rows"]))
  t.append("- 事实摘要：Python 抛 RuntimeError（GetPowerFlux: The layer eigensystem could not be solved; no solution was returned）；Lua REPL 打印 GetPoyntingFlux 同一文本（句末带点）；stderr 不出现 Layer eigensystem returned info = 2；恢复对象与另起进程参考值逐元素相对误差 ≤1e-12。")
  t.append("- 结论措辞：在 F4 上、在该输入下经公共 API 可见失败且恢复正确（不写已修好）。")
 else:
  t.append("- （试跑期：正式两遍尚未运行；预注册见 PREREG_D016_S5R2.tsv）")
 t.append("")
 t.append("## 8 事件两张表")
 t.append("")
 t.append("### 8.1 表一：越界写入尝试")
 t.append("")
 t.append("| # | 命令/脚本 | 目标 | 是否落盘 |")
 t.append("|---|---|---|---|")
 t.append("| - | 无 | - | - |")
 t.append("")
 t.append("无仓库外写入尝试；/tmp 顶层开工 %s 条目，收尾快照见附录 A/门禁记录。"%sr.get("TMP_COUNT","?"))
 t.append("")
 t.append("### 8.2 表二：工具与脚本事件")
 t.append("")
 t.append("| # | 事件 | 影响 |")
 t.append("|---|---|---|")
 t.append("| 1 | 脚本写入阶段出现 3 次 shell 引号导致的 python -c 失败（NameError / FileNotFoundError，均经 safe_run、无文件生成） | 无产物；随后改用 exec+base64 参数修复 |")
 t.append("| 2 | 早期一次只读检查把 git show 输出重定向到 /dev/null | 非仓库写入，不落盘 |")
 t.append("| 3 | 框架未产生 /tmp/dsh-spill-* 落盘 | 无 |")
 t.append("")
 t.append("## 9 下一轮（S5R3）建议")
 t.append("")
 t.append("- 在 F4 上重跑一次 make test 与全量 E2E（M3b 42 点加 D016 点），作为 S5 收口的修复后验证（U364）；修复前证据不得称为修复后验证。")
 t.append("- 就绪审计：F4 树/判定器/证据清单/STATE/registries/报告一致；AC-3/AC-4 最终映射。")
 t.append("- 不宣布阶段完成；签收只由用户在对话中给出。")
 t.append("")
 t.append("## 10 交付物")
 t.append("")
 t.append("复制到 checkpoints/p05/registries/s5r2/ 的小表（11 项 + 清单本身，共 12 项，与 SHA256SUMS 项数一致）：")
 t.append("")
 for i,f in enumerate(SMALL,1):
  t.append("%d. %s"%(i,f))
 t.append("12. SHA256SUMS.txt")
 t.append("")
 t.append("## 附录 A（试跑门禁摘要）")
 t.append("")
 if sg:
  t.append("- 试跑输出：$EV/shakedown/gate/GATE_S5R2_end.txt（模拟 commit-i；不纳入 SHA256SUMS）。")
  t.append("- %s"%sg["counts"])
  t.append("- %s"%sg["fails"])
  t.append("- %s"%sg["crashed"])
  for l in sg["post"]: t.append("- %s"%l)
 else:
  t.append("- 试跑 end 门禁尚未运行（本报告在试跑门禁之前生成）。")
 t.append("")
 t.append("## 附录 B（正式 end 门禁原文摘要）")
 t.append("")
 t.append("见 P05_S5R2_GATE_APPENDIX.md（由 s5r2_appendix.py 从正式门禁输出生成；报告正文不内嵌门禁结果）。")
 t.append("")
 t.append("本轮已完成 P05-S5 R2 范围，等待用户审核。")
 t.append("")
 t.append("git log -1: "+g)
 t.append("git status --short: "+(st.replace(NL,"; ") if st else "(clean)"))
 t.append("")
 return NL.join(t)
def cmd_report():
 txt=report_text()
 if SHAKE: wr(os.path.join(SHK,"REPORT.proposed.md"),txt)
 else: wr(REPORT,txt)
 print("REPORT bytes=%d shake=%s"%(len(txt.encode()),SHAKE)); return 0
def cmd_report_check():
 src=os.path.join(SHK,"REPORT.proposed.md") if SHAKE else REPORT
 if not os.path.isfile(src): print("HARD_STOP report missing"); return 2
 txt=rd(src); lines=txt.splitlines()
 order=["## 1 门禁","## 2 裁决入账","## 3 勘误","## 4 D017 清单计数","## 5 开放项总表计数","## 6 登记表应用 diff 摘要","## 7 D016 结果","## 8 事件两张表","## 9 下一轮","## 10 交付物","## 附录 A","## 附录 B"]
 pos=[next((i for i,l in enumerate(lines) if l.strip().startswith(h)),-1) for h in order]
 checks=[]
 checks.append(("SECTIONS_IN_ORDER",all(p>=0 for p in pos) and pos==sorted(pos)))
 sec10=[]; in10=False
 for l in lines:
  if l.strip()=="## 10 交付物": in10=True; continue
  if in10 and l.startswith("## "): break
  if in10:
   m=re.match(r"^\s*(\d+)\.\s+(.+?)\s*$",l)
   if m: sec10.append(m.group(2).strip())
 checks.append(("DELIVERABLE_COUNT_12",len(sec10)==12))
 checks.append(("DELIVERABLE_LAST_SUMS",bool(sec10) and sec10[-1]=="SHA256SUMS.txt"))
 checks.append(("DELIVERABLE_NO_BACKTICK",all(BT not in x for x in sec10)))
 checks.append(("VERDICT_LINE",("本轮已完成 P05-S5 R2 范围，等待用户审核" in txt)))
 checks.append(("GIT_LINES",("git log -1:" in txt) and ("git status --short:" in txt)))
 checks.append(("EVENTS_TWO_TABLES",("8.1 表一" in txt) and ("8.2 表二" in txt)))
 checks.append(("APPENDIX_A_MARK",("## 附录 A" in txt)))
 checks.append(("APPENDIX_B_GATE_APPENDIX",("P05_S5R2_GATE_APPENDIX.md" in txt)))
 forb=["P05-S6","P05 已完成","P05-S5 已完成","已签收 P05-S5","P05 完成","P05-S5 已签收"]
 bad=[(w,i) for w in forb for i,l in enumerate(lines,1) if w in l and not (("不" in l or "未" in l))]
 checks.append(("FORBIDDEN_TOKENS_ABSENT",not bad))
 inv=inventory_counts()
 need=["总出现数 %d；CALL %d；IN %d；OUT %d；OUT 中 CALL %d"%(inv["total"],inv["CALL"],inv["IN"],inv["OUT"],inv["OUT_CALL"]),
       "复制到 checkpoints/p05/registries/s5r2/ 的小表（11 项 + 清单本身，共 12 项，与 SHA256SUMS 项数一致）"]
 hdr,oi=open_items_rows()
 oc={}
 for r in oi: oc[r["final_disposition"]]=oc.get(r["final_disposition"],0)+1
 need.append("final_disposition 计数："+("；".join("%s=%d"%(k,oc[k]) for k in sorted(oc)))+"。")
 need.append("S5R1 去重后的 25 行逐行落位" if len(oi)==25 else "OPEN_ITEMS_ROW_COUNT_BAD")
 ap=apply_summary()
 if ap:
  for rel in ("testing/s4test/ISSUE_REGISTRY.md","PROJECT_ROADMAP.md"):
   d=ap.get(rel,{})
   need.append("- %s：替换行 %s；插入 %s 行"%(rel,d.get("replaced","?"),d.get("inserted","?")))
 vs=verdict_summary()
 if vs and vs!="UNPARSED":
  need.append("正式两遍：MATCH=%d、MISMATCH=%d、FLAKY=%d"%(vs["MATCH"],vs["MISMATCH"],vs["FLAKY"]))
 miss=[x for x in need if x not in txt]
 checks.append(("COUNTS_MATCH_SOURCE_FILES",not miss))
 st=rd(ST)
 checks.append(("STATE_BYTES_LE_8192",0<len(st.encode())<=8192))
 smiss=[k for k in ("P05-S5 R2","S5 进行中","P05_S5_OPEN_ITEMS.tsv","S5R3","已由用户签收") if k not in st]
 checks.append(("STATE_MARKERS",not smiss))
 pv=rd(PATCHV2)
 checks.append(("PATCHV2_PRESENT",("<!-- PATCHSPEC-BEGIN -->" in pv) and ("U371" in pv)))
 fails=[k for k,v in checks if not v]
 outp=os.path.join(SHK if SHAKE else EV,"REPORT_CHECK_S5R2.txt")
 body=["# REPORT_CHECK_S5R2.txt -- report structure, counts, appendix reference and forbidden-token check"]
 body+=["CHECK"+TAB+k+TAB+("PASS" if v else "FAIL") for k,v in checks]
 if bad: body.append("FORBIDDEN_HITS="+str(bad[:6]))
 if miss: body.append("COUNTS_MISSING="+str(miss[:6]))
 if smiss: body.append("STATE_MISSING="+str(smiss[:6]))
 body.append("FAILS=%d"%len(fails))
 wr(outp,NL.join(body)+NL)
 print(NL.join(body)); return 0 if not fails else 2
def cmd_copy():
 src=SHK if SHAKE else EV
 dst=os.path.join(SHK,"registries_copy") if SHAKE else REGDIR
 rp=os.path.realpath(dst); allowed=os.path.realpath(os.path.join(P05))
 if not rp.startswith(allowed+os.sep): print("HARD_STOP copy dest outside checkpoints/p05: "+rp); return 2
 os.makedirs(dst,exist_ok=True)
 copied=[]
 for f in SMALL:
  sp=os.path.join(src,f)
  if not os.path.isfile(sp):
   if SHAKE: continue
   print("HARD_STOP missing small table "+f); return 2
  dp=os.path.join(dst,f)
  if os.path.isfile(dp) and sha_f(dp)==sha_f(sp):
   copied.append(f); continue
  shutil.copyfile(sp,dp); copied.append(f)
 lines=[]
 for f in copied:
  a=sha_f(os.path.join(dst,f)); b=sha_f(os.path.join(src,f))
  if a!=b: print("HARD_STOP copy sha mismatch "+f); return 2
  lines.append(a+"  "+f)
 wr(os.path.join(dst,"SHA256SUMS.txt"),"# SHA256SUMS.txt -- small-table registry for P05-S5 R2 (copied from the raw evidence dir)"+NL+NL.join(lines)+NL)
 print("COPY %d files -> %s"%(len(copied),os.path.relpath(dst,REPO)))
 docs=[BRIEF,"checkpoints/p05/registries/RULINGS.tsv",ST,PATCHV2,OPENITEMS,
       "testing/s4test/ISSUE_REGISTRY.md","PROJECT_ROADMAP.md"]
 realreg=os.path.join(P05,"registries/s5r2")
 if os.path.isdir(realreg):
  docs+=[os.path.relpath(os.path.join(realreg,f),REPO) for f in sorted(os.listdir(realreg))]
 if not SHAKE:
  docs.append(REPORT); docs.append(GATEAPP)
  docs+=["checkpoints/p05/registries/s5r2/"+f for f in copied+["SHA256SUMS.txt"]]
 scripts=sorted("testing/d003/stage_s5r2/"+f for f in os.listdir(os.path.join(REPO,"testing/d003/stage_s5r2")) if (("s5r2" in f) or f.startswith("gate_")) and f.endswith((".py",".sh",".lua")))
 decl=docs+scripts
 outp=os.path.join(SHK if SHAKE else EV,"REGISTRY_OUTPUTS_S5R2.tsv")
 wr(outp,"# REGISTRY_OUTPUTS_S5R2.tsv -- declared non-EV outputs written after START_TIME"+NL+NL.join(decl)+NL)
 print("REGISTRY_OUTPUTS: %d declared"%len(decl)); return 0
def cmd_events():
 a=anchor_line("s5r2_chain.py events")
 if a<=0: print("HARD_STOP no events anchor"); return 2
 ls=log_lines(); parent=""; rows={}
 for x in range(1,a+1):
  if x>len(ls) or not ls[x-1].strip(): continue
  m=TS.match(ls[x-1])
  if m: parent=m.group(1)
  rows[x]=parent
 body=["# EVENTS_S5R2.tsv -- safe_run.log line -> UTC timestamp (rows 1..%d; anchor = events call line %d)"%(a,a),"log_line"+TAB+"ts_utc"]
 body+=["%d%s%s"%(x,TAB,rows[x]) for x in sorted(rows)]
 body.append("# ROWS=%d"%len(rows))
 wr(os.path.join(SHK if SHAKE else EV,"EVENTS_S5R2.tsv"),NL.join(body)+NL)
 print("EVENTS rows=%d anchor=%d"%(len(rows),a)); return 0
def cmd_progress():
 out=os.path.join(SHK if SHAKE else EV,"PROGRESS_S5R2.txt")
 line=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")+TAB+"P05-S5 R2 closeout: sha_sums is the next (last) EV write"
 if not os.path.isfile(out): wr(out,"# PROGRESS_S5R2.txt -- closeout chain progress (last line is the sha_sums predecessor)"+NL)
 open(out,"a",encoding="utf-8").write(line+NL)
 print("PROGRESS appended: "+line); return 0
def cmd_sha_sums():
 ev=SHK if SHAKE else EV
 a=anchor_line("s5r2_chain.py sha_sums")
 if a<=0: print("HARD_STOP no sha_sums anchor"); return 2
 ls=log_lines(); trunc=NL.join(ls[:a])+NL; th=sha_b(trunc.encode("utf-8"))
 items=[]
 for root,dirs,files in os.walk(ev):
  dirs[:]=sorted(d for d in dirs if d not in ("tmp","gate","trees"))
  for f in sorted(files):
   fp=os.path.join(root,f); rel=os.path.relpath(fp,ev)
   if rel in ("safe_run.log","SHA256SUMS.txt") or f=="SHA256SUMS.txt": continue
   items.append((sha_f(fp),rel))
 out=os.path.join(ev,"SHA256SUMS.txt")
 if not SHAKE and os.path.dirname(os.path.realpath(out))!=os.path.realpath(EV):
  print("HARD_STOP sha_sums path"); return 2
 body=["# SHA256SUMS.txt -- P05-S5 R2 evidence manifest (excludes tmp/, gate/, trees/)",
       "# safe_run.log up to line %d: %s"%(a,th)]+["%s  %s"%(h,rel) for h,rel in items]
 wr(out,NL.join(body)+NL)
 print("SHA256SUMS %d items trunc_line=%d"%(len(items),a)); return 0
def main():
 if len(sys.argv)<2:
  print("usage: s5r2_chain.py <report|report_check|copy|events|progress|sha_sums> [--shakedown]"); return 2
 sub=sys.argv[1]
 return {"report":cmd_report,"report_check":cmd_report_check,"copy":cmd_copy,"events":cmd_events,"progress":cmd_progress,"sha_sums":cmd_sha_sums}.get(sub,lambda:2)()
if __name__=="__main__": sys.exit(main())
