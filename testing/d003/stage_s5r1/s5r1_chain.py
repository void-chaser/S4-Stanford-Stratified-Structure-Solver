#!/usr/bin/env python3
# s5r1_chain.py -- P05-S5 R1 closeout chain. Subcommands in required order:
#   report | report_check | copy | events | progress | sha_sums.  Run once each in the frozen period.
import os,sys,re,hashlib,shutil,subprocess,datetime
REPO=os.getcwd()
EV=os.path.join(REPO,"checkpoints/p05/evidence/p05-s5r1")
SHK=os.path.join(EV,"shakedown")
REPORT=os.path.join(REPO,"checkpoints/p05/P05_S5R1_REPORT.md")
REGDIR=os.path.join(REPO,"checkpoints/p05/registries/s5r1")
TAB=chr(9); NL=chr(10); BT=chr(96); FENCE=chr(96)*3
def sha_b(b): return hashlib.sha256(b).hexdigest()
def sha_f(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(65536),b""): h.update(b)
 return h.hexdigest()
def rd(p): return open(p,encoding="utf-8").read()
def wr(p,t):
 os.makedirs(os.path.dirname(p),exist_ok=True)
 open(p,"w",encoding="utf-8").write(t)
def sh(a): return subprocess.check_output(a,cwd=REPO,text=True,stderr=subprocess.STDOUT).strip()
def outdir(shake): return SHK if shake else EV
def log_path(): return os.path.join(EV,"safe_run.log")
def log_lines():
 if not os.path.isfile(log_path()): return []
 return rd(log_path()).splitlines()
TS=re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\t")
def anchor_line(needle):
 lines=log_lines()
 for x in range(len(lines),0,-1):
  if needle in lines[x-1]: return x
 return 0
def read_tsv(rel):
 p=os.path.join(REPO,rel)
 rows=[l.rstrip(NL).split(TAB) for l in rd(p).splitlines() if l.strip() and not l.startswith("#")]
 return rows
def counts():
 inv=read_tsv("checkpoints/p05/evidence/p05-s5r1/S5_INPUTS_S5R1.tsv")
 tri=read_tsv("checkpoints/p05/evidence/p05-s5r1/S5_TRIAGE_S5R1.tsv")
 acc=read_tsv("checkpoints/p05/evidence/p05-s5r1/P05_ACCEPTANCE_MAP_S5R1.tsv")
 gc={}
 for r in inv[1:]: gc[r[1]]=gc.get(r[1],0)+1
 cc={}
 for r in tri[1:]: cc[r[1]]=cc.get(r[1],0)+1
 yes=sum(1 for r in tri[1:] if r[6]=="YES")
 blk=sum(1 for r in tri[1:] if r[4].startswith("YES"))
 ac={}
 for r in acc[1:]: ac[r[0]]=r[3]
 dd=rd(os.path.join(REPO,"checkpoints/p05/evidence/p05-s5r1/S5_INPUTS_DEDUP_S5R1.txt"))
 pre=int(re.search(r"PRE_DEDUP_ROWS=(\d+)",dd).group(1))
 mer=int(re.search(r"MERGED_ROWS=(\d+)",dd).group(1))
 # eliminated = pre-unique
 elim=pre-len(inv[1:])
 return gc,cc,yes,blk,ac,pre,mer,elim,len(inv[1:]),len(tri[1:])

def start_summary():
 p=os.path.join(EV,"GATE_S5R1_start.txt")
 if not os.path.isfile(p): return "start gate file missing"
 t=rd(p).splitlines()
 keys=["COUNTS","FAILS"]
 rec={}
 for l in t:
  f=l.split(TAB)
  if f and f[0]=="RECORD" and len(f)>=3: rec[f[1]]=f[2].replace("value=","")
 return {"counts":[l for l in t if l.startswith("COUNTS")],"fails":[l for l in t if l.startswith("FAILS")],"rec":rec,"lines":t}

def gate_summary(path):
 if not os.path.isfile(path): return None
 t=rd(path).splitlines()
 d={"path":os.path.relpath(path,REPO),"counts":"","fails":"","crashed":"","post":[],"alltxt":t}
 for l in t:
  if l.startswith("COUNTS"): d["counts"]=l
  if l.startswith("FAILS="): d["fails"]=l
  if l.startswith("PASS") and "POST_I_CALL_COUNT" in l: d["post"].append(l)
  if l.startswith("FAIL") and "POST_I_CALL_COUNT" in l: d["post"].append(l)
  if l.startswith("PASS") and "CHECK_CRASHED_ZERO" in l: d["crashed"]=l
  if l.startswith("FAIL") and "CHECK_CRASHED_ZERO" in l: d["crashed"]=l
 return d

def report_text(shake):
 gc,cc,yes,blk,ac,pre,mer,elim,nu,nt=counts()
 ss=start_summary()
 sg=gate_summary(os.path.join(SHK,"gate","GATE_S5R1_end.txt"))
 g=sh(["git","log","-1","--format=%H %s"]); st=sh(["git","status","--short"]) or "(clean)"
 t=[]
 t.append("# P05-S5 R1 报告（s5r1）：S5 输入只读盘点、分类分流、登记表补丁草案")
 t.append("")
 t.append("> 轮次：P05-S5 R1。只读盘点 + 文档写入；未运行 S4 的任何程序（无 make、make test、E2E、d003 矩阵、构建、gdb）。")
 t.append("> 本轮不宣布 P05-S5 或 P05 阶段完成；签收只由用户在对话中给出。")
 t.append("")
 t.append("## 1 门禁")
 t.append("")
 t.append("- start 门禁：%s，%s（GATE_S5R1_start.txt；CHECK_CRASHED=0）。HEAD=59e742d5…f263；HEAD:S4=589e15eb…46cf（F4）；判定器 sha256=d2d04145…09eb；工作区干净。"%(ss["counts"][0] if ss["counts"] else "?","；".join(ss["fails"])))
 t.append("- 起始文件字节数与 sha256 由脚本断言：RULINGS.tsv 146978 B（d33990ca2312eefc，最大 U363）、ERRATA_9.txt 65771 B（5a07fc22fd796f92，最后 E9-77）、STATE.md 5318 B（dc4c1083bc69284b）、P05_S3_S4_SIGNOFF.md 2077 B（7b5b412a9fa363ad）、P05_S1_S2_SIGNOFF.md 1636 B（b6174b499884a593）、S5_HANDOFF_R9M3D.tsv 1401 B（7adf17662bc47b94）、ISSUE_REGISTRY.md 20720 B（ad17b768c79a3f63）、PROJECT_ROADMAP.md 20905 B（2c8cbe18d479584a）。")
 t.append("- registries/s4r9/M3e/SHA256SUMS.txt 4/4 OK；m3e 证据 SHA256SUMS.txt 23/23 OK；仓库根 registries/ 不存在；/tmp 顶层 0 条目（sha256 e3b0c442…b855）。")
 t.append("- 开工前证据目录与 brief 均不存在（test -e 断言，EV_ABSENT_BEFORE_START / BRIEF_ABSENT_BEFORE_SAVE）。")
 t.append("- end 门禁：见附录 B（冻结期正式单次运行；输出写 $EV/gate/，不纳入清单）。")
 t.append("")
 t.append("## 2 勘误 E9-78 / E9-79")
 t.append("")
 t.append("- E9-78：M3e end 门禁的两项 POST_I 调用计数 FAIL 是检查器缺陷（gate_check_r9m3e.py 第 244 行把 mkc() 返回元组当可调用对象传入 safe()，TypeError: tuple object is not callable）；根因是试跑期未实跑 end 门禁 POST_I 块。只读复算：提交 (i) 后 chain 6 次（safe_run.log 第 59–64 行）、gate end 1 次（第 65 行）；GATE_R9M3E_end.txt 第 14 行 CALL_LINES_M3E_CHAIN_R9M3E_- 为空。只登记，不重跑 M3e。复算文件 ERRATA_RECHECK_S5R1.txt。")
 t.append("- E9-79：M3e 表一 3 次越界写入尝试（safe_run.log 第 1、2、3 行，均未落盘）的成因是 safe_run 接 bash -c 时外层先展开变量；修正方式见任务书第 2 节第 1 条。只登记，不重跑 M3e。")
 t.append("")
 t.append("## 3 输入盘点计数")
 t.append("")
 t.append("- A 组：%d 行（S5-M3D-01..07，S5-M3D-06 来源按 E9-76 记 U5）"%gc.get("A",0))
 t.append("- B 组：%d 行（S1/S2 签收范围第 (3) 条四项 + S1 报告 11.2 的五个哈希来源）"%gc.get("B",0))
 t.append("- C 组：%d 行（D016、R-P05-01、fmm_kottke 除数数值安全；U99/U100 并入 S5-M3D-03）"%gc.get("C",0))
 t.append("- D 组：%d 行（ISSUE_REGISTRY 的 D003 行与全部含 P05 的行、PROJECT_ROADMAP 的 P05 行）"%gc.get("D",0))
 t.append("- 去重前 %d 行；合并记录 %d 条（消除 %d 行）；去重后 %d 行（S5_INPUTS_S5R1.tsv；合并关系见 S5_INPUTS_DEDUP_S5R1.txt）。"%(pre,mer,elim,nu))
 t.append("")
 t.append("## 4 分类计数")
 t.append("")
 for k in ["REGISTRY_ONLY","NEEDS_TEST","NEEDS_FIX_NEW_DEFECT","RECORD_ONLY_OPEN","NEEDS_USER_RULING"]:
  t.append("- %s=%d"%(k,cc.get(k,0)))
 t.append("- needs_user_ruling=YES 共 %d 行；blocks_P06_D004=YES 共 %d 行。"%(yes,blk))
 t.append("")
 t.append("## 5 验收映射")
 t.append("")
 t.append("- AC-1（每个受影响的 prepare/execute 点有正负对照）：%s"%ac.get("AC-1"))
 t.append("- AC-2（失败后模式/缓存不安装）：%s"%ac.get("AC-2"))
 t.append("- AC-3（Python/Lua 可见失败，恢复重试正确）：%s"%ac.get("AC-3"))
 t.append("- AC-4（M3a/M3b 的 make test 与 E2E 能否作为 S5 前端与回归证据）：%s；利弊见 P05_ACCEPTANCE_MAP_S5R1.tsv 与计划草案 Q1。"%ac.get("AC-4"))
 t.append("- 明细见 P05_ACCEPTANCE_MAP_S5R1.tsv；GAP 行 0。")
 t.append("")
 t.append("## 6 草案摘要")
 t.append("")
 t.append("- P05_S5_REGISTRY_PATCH_DRAFT.md：对 ISSUE_REGISTRY.md 与 PROJECT_ROADMAP.md 的逐条 unified diff 草案（只写不应用），覆盖 D003 状态与关闭范围（引用 P05_S3_S4_SIGNOFF.md 第 2 节原文，不改写）、D016 核对结果（已实施 3e77aa9、Python 文本未实测）、非 FMM S4_malloc 另立登记项（建议 D017）、ES3R4-5/528/1164 与 U99/U100 登记（R-P05-02/R-P05-03）、P05 行状态文字。")
 t.append("- P05_S5_PLAN_DRAFT.md：S5R2 与收口计划草案；NEEDS_TEST 项预注册思路（期望值运行前写入并记录 sha256）、Python/Lua 驱动与预计运行量（约 28 点两遍，若 Q1 需独立复跑追加约 50 次）、Q1..Q8 需用户裁决问题（每条附推荐与理由）。")
 t.append("")
 t.append("## 7 事件两张表")
 t.append("")
 t.append("### 7.1 表一：越界写入尝试")
 t.append("")
 t.append("| # | 命令/脚本 | 目标 | 是否落盘 |")
 t.append("|---|---|---|---|")
 t.append("| 1 | 首次写 s5r1_startgate.py（目标目录当时不存在） | testing/d003/stage_s5r1/s5r1_startgate.py（仓库内） | 否（FileNotFoundError，未生成文件） |")
 t.append("")
 t.append("无仓库外写入尝试；/tmp 顶层开工 0 条目、收尾快照见附录 B 记录。")
 t.append("")
 t.append("### 7.2 表二：工具与脚本事件")
 t.append("")
 t.append("| # | 事件 | 影响 |")
 t.append("|---|---|---|")
 t.append("| 1 | 首次脚本写入因 stage_s5r1 目录不存在而失败（safe_run.log 一条失败命令） | 无文件生成；随后先 mkdir 再写入 |")
 t.append("| 2 | 框架未产生 /tmp/dsh-spill-* 落盘 | 无 |")
 t.append("")
 t.append("其余：无裸跑写入、无 heredoc 残留、无仓库内路径拼错（除事件 1）。")
 t.append("")
 t.append("## 8 需用户裁决")
 t.append("")
 t.append("- AC-3/AC-4：M3a/M3b 的 make test 与 E2E 结果能否作为 S5 前端与回归证据（推荐见 Q1）。")
 t.append("- Q1..Q8：见 P05_S5_PLAN_DRAFT.md 第 5 节（F10/F8 历史输入、反事实通量与 allzero 意图、11.2 五哈希来源、D017 编号、R-P05-02/03 登记）。")
 t.append("- 本轮不自行认定上述任一项。")
 t.append("")
 t.append("## 9 交付物")
 t.append("")
 t.append("复制到 checkpoints/p05/registries/s5r1/ 的小表（7 项 + 清单本身）：")
 t.append("")
 t.append("1. GATE_S5R1_start.txt")
 t.append("2. S5_INPUTS_S5R1.tsv")
 t.append("3. S5_INPUTS_DEDUP_S5R1.txt")
 t.append("4. S5_TRIAGE_S5R1.tsv")
 t.append("5. P05_ACCEPTANCE_MAP_S5R1.tsv")
 t.append("6. REPORT_CHECK_S5R1.txt")
 t.append("7. FROZEN_SCRIPTS_S5R1.tsv")
 t.append("8. SHA256SUMS.txt")
 t.append("")
 t.append("## 附录 A（试跑 end 门禁摘要）")
 t.append("")
 if sg:
  t.append("- 试跑输出：$EV/shakedown/gate/GATE_S5R1_end.txt（模拟 commit-i；不纳入 SHA256SUMS）。")
  t.append("- %s"%sg["counts"])
  t.append("- %s"%sg["fails"])
  t.append("- %s"%sg["crashed"])
  for l in sg["post"]: t.append("- %s"%l)
 else:
  t.append("- 试跑 end 门禁尚未运行（本报告在试跑门禁之前生成）；正式报告将在此处写入试跑门禁实际摘要。")
 t.append("")
 t.append("## 附录 B（正式 end 门禁原文摘要）")
 t.append("")
 t.append("PENDING_FORMAL_END_GATE")
 t.append("")
 t.append("本轮完成 P05-S5 R1 范围，等待用户审核。")
 t.append("")
 t.append("git log -1: "+g)
 t.append("git status --short: "+(st.replace(NL,"; ") if st else "(clean)"))
 t.append("")
 return NL.join(t)

def cmd_report(shake):
 txt=report_text(shake)
 if shake: wr(os.path.join(SHK,"REPORT.proposed.md"),txt)
 else: wr(REPORT,txt)
 print("REPORT bytes=%d shake=%s"%(len(txt.encode()),shake)); return 0

def cmd_report_check(shake):
 src=os.path.join(SHK,"REPORT.proposed.md") if shake else REPORT
 txt=rd(src); lines=txt.splitlines()
 order=["## 1 门禁","## 2 勘误","## 3 输入盘点计数","## 4 分类计数","## 5 验收映射","## 6 草案摘要","## 7 事件两张表","## 8 需用户裁决","## 9 交付物","## 附录 A","## 附录 B"]
 pos=[next((i for i,l in enumerate(lines) if l.strip()==h or l.strip().startswith(h)),-1) for h in order]
 checks=[]
 checks.append(("SECTIONS_IN_ORDER", all(p>=0 for p in pos) and pos==sorted(pos)))
 sec9=[]; in9=False
 for l in lines:
  if l.strip()=="## 9 交付物": in9=True; continue
  if in9 and l.startswith("## "): break
  if in9:
   m=re.match(r"^\s*(\d+)\.\s+(.+?)\s*$",l)
   if m: sec9.append(m.group(2).strip())
 checks.append(("DELIVERABLE_COUNT_8", len(sec9)==8))
 checks.append(("DELIVERABLE_LAST_SUMS", bool(sec9) and sec9[-1]=="SHA256SUMS.txt"))
 checks.append(("DELIVERABLE_NO_BACKTICK", all(BT not in x for x in sec9)))
 checks.append(("VERDICT_LINE", "本轮完成 P05-S5 R1 范围，等待用户审核" in txt))
 checks.append(("GIT_LINES", ("git log -1:" in txt) and ("git status --short:" in txt)))
 checks.append(("MARK_E978_E979", ("E9-78" in txt) and ("E9-79" in txt)))
 checks.append(("EVENTS_TWO_TABLES", ("7.1 表一" in txt) and ("7.2 表二" in txt)))
 checks.append(("APPENDIX_A_MARK", ("## 附录 A" in txt)))
 checks.append(("APPENDIX_B_MARK", ("## 附录 B" in txt)))
 # counts versus recomputation
 gc,cc,yes,blk,ac,pre,mer,elim,nu,nt=counts()
 need=["- A 组：%d 行"%gc.get("A",0),"- B 组：%d 行"%gc.get("B",0),"- C 组：%d 行"%gc.get("C",0),"- D 组：%d 行"%gc.get("D",0),
       "- 去重前 %d 行；合并记录 %d 条"% (pre,mer), "去重后 %d 行"%nu]
 for k in ["REGISTRY_ONLY","NEEDS_TEST","NEEDS_FIX_NEW_DEFECT","RECORD_ONLY_OPEN","NEEDS_USER_RULING"]:
  need.append("- %s=%d"%(k,cc.get(k,0)))
 need.append("- needs_user_ruling=YES 共 %d 行；blocks_P06_D004=YES 共 %d 行。"%(yes,blk))
 miss=[x for x in need if x not in txt]
 checks.append(("COUNTS_MATCH_SOURCE_TABLES", not miss))
 # forbidden tokens (avoid false-positive on compliant negations)
 forb=["P05-S6","P05 已完成","P05-S5 已完成","已签收 P05-S5","P05 完成"]
 bad=[]
 for w in forb:
  for i,l in enumerate(lines,1):
   if w in l: bad.append((w,i))
 # allow the exact negation patterns
 allowed=lambda w,l: (w=="P05 完成" and ("不宣布" in l or "未" in l)) or (w=="已签收 P05-S5" and ("不" in l or "未" in l))
 bad=[(w,i) for (w,i) in bad if not allowed(w,lines[i-1])]
 checks.append(("FORBIDDEN_TOKENS_ABSENT", not bad))
 checks.append(("P05_S5_NOT_CALLED_DONE", ("P05-S5 未完成" in txt) or ("P05-S5 未签收" in txt) or ("不宣布 P05-S5" in txt)))
 fails=[k for k,v in checks if not v]
 out=os.path.join(SHK if shake else EV,"REPORT_CHECK_S5R1.txt")
 body=["# REPORT_CHECK_S5R1.txt -- report structure, counts, appendix and forbidden-token check"]
 body+=["CHECK"+TAB+k+TAB+("PASS" if v else "FAIL") for k,v in checks]
 if bad: body.append("FORBIDDEN_HITS="+str(bad[:6]))
 if miss: body.append("COUNTS_MISSING="+str(miss[:6]))
 body.append("FAILS=%d"%len(fails))
 wr(out,NL.join(body)+NL)
 print(NL.join(body)); return 0 if not fails else 2

SMALL=["GATE_S5R1_start.txt","S5_INPUTS_S5R1.tsv","S5_INPUTS_DEDUP_S5R1.txt","S5_TRIAGE_S5R1.tsv","P05_ACCEPTANCE_MAP_S5R1.tsv","REPORT_CHECK_S5R1.txt","FROZEN_SCRIPTS_S5R1.tsv"]
def cmd_copy(shake):
 src=SHK if shake else EV
 dst=os.path.join(SHK,"registries_copy") if shake else REGDIR
 rp=os.path.realpath(dst); allowed=os.path.realpath(os.path.join(REPO,"checkpoints/p05"))
 if not rp.startswith(allowed+os.sep):
  print("HARD_STOP copy dest outside checkpoints/p05: "+rp); return 2
 os.makedirs(dst,exist_ok=True)
 copied=[]
 for f in SMALL:
  sp=os.path.join(src,f)
  if os.path.isfile(sp):
   shutil.copyfile(sp,os.path.join(dst,f)); copied.append(f)
  elif not shake:
   print("HARD_STOP missing small table "+f); return 2
 lines=[]
 for f in copied:
  a=sha_f(os.path.join(dst,f)); b=sha_f(os.path.join(src,f))
  if a!=b:
   print("HARD_STOP copy sha mismatch "+f); return 2
  lines.append(a+"  "+f)
 wr(os.path.join(dst,"SHA256SUMS.txt"),"# SHA256SUMS.txt -- small-table registry for P05-S5 R1 (copied from the raw evidence dir)"+NL+NL.join(lines)+NL)
 print("COPY %d files -> %s"%(len(copied),os.path.relpath(dst,REPO)))
 docs=["checkpoints/p05/briefs/P05_S5R1_BRIEF.md","checkpoints/p05/registries/s4r9/ERRATA_9.txt","checkpoints/p05/STATE.md",
       "checkpoints/p05/P05_S5_REGISTRY_PATCH_DRAFT.md","checkpoints/p05/P05_S5_PLAN_DRAFT.md"]
 if not shake:
  docs.append("checkpoints/p05/P05_S5R1_REPORT.md")
  docs+=["checkpoints/p05/registries/s5r1/"+f for f in copied+["SHA256SUMS.txt"]]
 scripts=sorted("testing/d003/stage_s5r1/"+f for f in os.listdir(os.path.join(REPO,"testing/d003/stage_s5r1")) if f.startswith("s5r1") or f.startswith("gate"))
 decl=docs+scripts
 out=os.path.join(SHK if shake else EV,"REGISTRY_OUTPUTS_S5R1.tsv")
 wr(out,"# REGISTRY_OUTPUTS_S5R1.tsv -- declared non-EV outputs written after START_TIME (shakedown copy lists real docs only)"+NL+NL.join(decl)+NL)
 print("REGISTRY_OUTPUTS: %d declared"%len(decl)); return 0

def cmd_events(shake):
 a=anchor_line("s5r1_chain.py events")
 if a<=0: print("HARD_STOP no events anchor in log"); return 2
 lines=log_lines(); parent=""; rows={}
 for x in range(1,a+1):
  if x>len(lines) or not lines[x-1].strip(): continue
  m=TS.match(lines[x-1])
  if m: parent=m.group(1)
  rows[x]=parent
 body=["# EVENTS_S5R1.tsv -- safe_run.log line -> UTC timestamp (rows 1..%d; anchor = events call line %d)"%(a,a),"log_line"+TAB+"ts_utc"]+["%d%s%s"%(x,TAB,rows[x]) for x in sorted(rows)]+["# ROWS=%d"%len(rows)]
 wr(os.path.join(SHK if shake else EV,"EVENTS_S5R1.tsv"),NL.join(body)+NL)
 print("EVENTS rows=%d anchor=%d"%(len(rows),a)); return 0

def cmd_progress(shake):
 out=os.path.join(SHK if shake else EV,"PROGRESS_S5R1.txt")
 line=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")+TAB+"P05-S5 R1 closeout: sha_sums is the next (last) $EV write"
 if not os.path.isfile(out):
  wr(out,"# PROGRESS_S5R1.txt -- closeout chain progress (last line is the sha_sums predecessor)"+NL)
 open(out,"a",encoding="utf-8").write(line+NL)
 print("PROGRESS appended: "+line); return 0

def cmd_sha_sums(shake):
 ev=SHK if shake else EV
 a=anchor_line("s5r1_chain.py sha_sums")
 if a<=0: print("HARD_STOP no sha_sums anchor"); return 2
 lines=log_lines(); trunc=NL.join(lines[:a])+NL; th=sha_b(trunc.encode("utf-8"))
 items=[]
 for root,dirs,files in os.walk(ev):
  dirs[:]=sorted(d for d in dirs if d not in ("tmp","gate"))
  for f in sorted(files):
   fp=os.path.join(root,f); rel=os.path.relpath(fp,ev)
   if rel in ("safe_run.log","SHA256SUMS.txt") or f=="SHA256SUMS.txt": continue
   items.append((sha_f(fp),rel))
 out=os.path.join(ev,"SHA256SUMS.txt")
 if not shake and os.path.dirname(os.path.realpath(out))!=os.path.realpath(EV):
  print("HARD_STOP sha_sums path"); return 2
 body=["# SHA256SUMS.txt -- P05-S5 R1 evidence manifest","# safe_run.log up to line %d: %s"%(a,th)]+["%s  %s"%(h,rel) for h,rel in items]
 wr(out,NL.join(body)+NL)
 print("SHA256SUMS %d items trunc_line=%d"%(len(items),a)); return 0

def main():
 if len(sys.argv)<2:
  print("usage: s5r1_chain.py <report|report_check|copy|events|progress|sha_sums> [--shakedown]"); return 2
 sub=sys.argv[1]; shake="--shakedown" in sys.argv[2:]
 return {"report":cmd_report,"report_check":cmd_report_check,"copy":cmd_copy,"events":cmd_events,"progress":cmd_progress,"sha_sums":cmd_sha_sums}[sub](shake)
if __name__=="__main__": sys.exit(main())
