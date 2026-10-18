#!/usr/bin/env python3
# s5r2_prep.py -- P05-S5 R2 preparation: rulings U364-U371 (append-only), errata ES5-1..ES5-5,
# S5R1 report recheck, D017 inventory, D016 source trace, prereg, registry patch v2, open-items
# table, STATE and the frozen script list. Every path is derived from git rev-parse
# --show-toplevel and asserted to stay under the allowed prefixes (checkpoints/p05, testing/d003).
import os,sys,re,hashlib,subprocess,datetime,difflib
REPO=subprocess.check_output(["git","rev-parse","--show-toplevel"],text=True).strip()
P05=os.path.join(REPO,"checkpoints/p05")
EV=os.path.join(P05,"evidence/p05-s5r2")
SHK=os.path.join(EV,"shakedown")
REG=os.path.join(P05,"registries")
S5R2REG=os.path.join(REG,"s5r2")
STAGE=os.path.join(REPO,"testing/d003/stage_s5r2")
TAB=chr(9); NL=chr(10); BT=chr(96); FENCE=chr(96)*3
SHAKE="--shakedown" in sys.argv[2:]
RULINGS=os.path.join(REG,"RULINGS.tsv")
ISSUE="testing/s4test/ISSUE_REGISTRY.md"
ROAD="PROJECT_ROADMAP.md"
S1="checkpoints/p05/S1_BASELINE_AND_ENUMERATION.md"
S5R1REP="checkpoints/p05/P05_S5R1_REPORT.md"
def sha_b(b): return hashlib.sha256(b).hexdigest()
def sha_f(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(65536),b""): h.update(b)
 return h.hexdigest()
def rd(p): return open(p,encoding="utf-8").read()
def rdb(p): return open(p,"rb").read()
def lines_of(rel): return rd(os.path.join(REPO,rel)).splitlines()
def check_prefix(p):
 rp=os.path.realpath(p)
 ok=rp.startswith(os.path.join(REPO,"checkpoints/p05")+os.sep) or rp.startswith(os.path.join(REPO,"testing/d003")+os.sep)
 if not ok: raise SystemExit("PATH_OUTSIDE_ALLOWED_PREFIX "+rp)
 return p
def wr(p,t):
 check_prefix(p); os.makedirs(os.path.dirname(p),exist_ok=True)
 open(p,"w",encoding="utf-8").write(t)
def put(name,text):
 return wr(os.path.join(SHK if SHAKE else EV,name),text)
def start_records():
 p=os.path.join(EV,"GATE_S5R2_start.txt"); rec={}
 if not os.path.isfile(p): raise SystemExit("START_GATE_MISSING")
 for line in rd(p).splitlines():
  f=line.split(TAB)
  if len(f)>=3 and f[0]=="RECORD":
   v=f[2]; v=v[6:] if v.startswith("value=") else v
   rec[f[1]]=v
 return rec
def git_show(path_in_commit):
 return subprocess.check_output(["git","show",path_in_commit],text=True)
def git_diff(a,b,paths):
 return subprocess.check_output(["git","diff",a+".."+b,"--"]+paths,text=True)

# ---------------- rulings U364-U371 (append-only) ----------------
RULINGS_TEXT=[
 ("U364","M3a/M3b 的 make test 与 E2E 作为 F4 上的历史证据，可被 S5 引用；S5 收口轮（S5R3）在 F4 上重跑一次 make test 与全量 E2E（M3b 42 点加 D016 点）。修复前证据不得称为修复后验证。"),
 ("U365","D016 在 S5R2 用 Python 与 Lua 公共 API 实测（VL，n_G=1）；NV 的 -10 路径触发不了，维持 [源码] 结论。"),
 ("U366","F10 历史因果（S5-B-01）、R-P05-01 的反事实通量与 allzero 设计意图（S5-B-03/B-04/C-02）保持 OPEN，转出 P05，写入 S5 范围声明，不阻塞。"),
 ("U367","F8 历史目录（S5-B-02）不授权访问，保持未验证。"),
 ("U368","S1 报告 11.2 的 5 个哈希来源（S5-B-05..09）认定为无法判定，不改写 11.2 与 EVIDENCE.sha256。"),
 ("U369","非 FMM S4_malloc 登记为 D017；登记前先只读逐点列出清单。"),
 ("U370","ES3R4-5/528/1164 与 U99 登记为 R-P05-02，U100 登记为 R-P05-03；一律写 F4 行号，旧树行号放在括号里注明。"),
 ("U371","批准本轮把补丁 v2 应用到 testing/s4test/ISSUE_REGISTRY.md 与 PROJECT_ROADMAP.md，这两个文件纳入本轮提交范围；不改 AGENTS.md。"),
]
def cmd_rulings():
 t=rd(RULINGS)
 present=[u for u,_ in RULINGS_TEXT if re.search(r"(?m)^"+u+TAB,t)]
 if len(present)==len(RULINGS_TEXT):
  print("RULINGS already contain U364..U371; no append"); return
 if present: raise SystemExit("RULINGS_PARTIAL "+str(present))
 b0=rdb(RULINGS)
 rows=[]
 for u,txt in RULINGS_TEXT:
  rows.append(TAB.join([u,"P05-S5 R2 任务书 §1",txt,"P05-S5 R2 任务书 §1","生效"]))
 new=t+(NL if not t.endswith(NL) else "")+NL.join(rows)+NL
 if SHAKE:
  wr(os.path.join(SHK,"RULINGS.proposed.tsv"),new)
 else:
  wr(RULINGS,new)
  nb=rdb(RULINGS)
  if not nb.startswith(b0): raise SystemExit("RULINGS_PREFIX_BROKEN")
  ids=[int(m.group(1)) for m in re.finditer(r"(?m)^U(\d+)"+TAB,rd(RULINGS))]
  need=[u for u,_ in RULINGS_TEXT if ("U%d"%i) not in [("U%d"%x) for x in ids]]
  if max(ids)!=371 or need: raise SystemExit("RULINGS_MAX_OR_MISSING %d %s"%(max(ids),need))
 print("RULINGS appended U364..U371 bytes=%d%s"%(len(rd(RULINGS))," (shakedown)" if SHAKE else ""))

# ---------------- D017 inventory ----------------
def s4_files():
 out=subprocess.check_output(["git","ls-tree","-r","--name-only","05097a7","S4"],text=True).splitlines()
 return [f for f in out if re.search(r"\.(c|cpp|h|hpp)$",f)]
CTRL=set(("if","for","while","switch","return","else","do","case","sizeof","catch"))
def func_of(lines,idx):
 for j in range(idx-1,max(-1,idx-400),-1):
  s=lines[j]; st=s.strip()
  if not st or st.startswith(("//","#","*","/*")): continue
  if s.startswith((" ","\t")): continue
  cand=s
  if "(" not in cand: continue
  defin=cand.endswith("{")
  if not defin:
   for k in range(j+1,min(j+12,len(lines))):
    t=lines[k].strip()
    if not t: continue
    if "{" in t: defin=True; break
    if ";" in t: break
  if not defin: continue
  m=re.match(r"^[A-Za-z_][\w:<>,\*&\s]*?\b([A-Za-z_]\w*)\s*\(",cand)
  if m and m.group(1) not in CTRL: return m.group(1)
 return "UNKNOWN"
def extract_var(line):
 m=re.search(r"([A-Za-z_]\w*)\s*=\s*\(?\s*[^;]*S4_malloc",line)
 if m: return m.group(1)
 m=re.search(r"([A-Za-z_]\w*)\s*=",line)
 return m.group(1) if m else ""
def null_check(lines,idx,var):
 if not var: return "NO"
 for j in range(idx+1,min(idx+16,len(lines))):
  s=lines[j]
  if var in s and ("NULL" in s or "nullptr" in s): return "YES"
 return "NO"
def consequence(lines,idx,kind,var):
 if kind=="COMMENT": return "注释行，非分配点（[源码]）"
 if kind=="DEF": return "S4_malloc 定义（调试分配器），非调用点（[源码]）"
 if kind=="DECL": return "声明，非分配点（[源码]）"
 for j in range(idx+1,min(idx+22,len(lines))):
  m=re.search(r"return\s+(-?\d+)\s*;",lines[j])
  if m:
   return ("NULL 检查后按该函数错误路径返回 %s（[源码]）"%m.group(1)) if null_check(lines,idx,var)=="YES" else ("无 NULL 检查；该函数后续 return %s（[源码]）"%m.group(1))
 return ("NULL 检查存在（[源码]）" if null_check(lines,idx,var)=="YES" else "无 NULL 检查（[源码]）")
IN_S4={
 2323:"P05-S3R R2 / U29：ComputeLayerModes q 分配（mode/cache 安装路径）",
 2443:"P05-S3R R3 / U29：ComputeLayerModes rwork 分配",
 2468:"P05-S3R R4 / U29：ComputeLayerModes work 分配",
 4029:"P05-S3R D1 / U29：AddFieldToCache 分配（缓存安装路径）",
}
def d017_rows():
 rows=[]
 for f in s4_files():
  txt=git_show("05097a7:"+f); lines=txt.split(NL)
  for idx,s in enumerate(lines,1):
   if "S4_malloc" not in s: continue
   pos=s.find("S4_malloc"); cpos=s.find("//")
   kind="CALL"
   if s.strip().startswith("//") or (cpos>=0 and cpos<pos): kind="COMMENT"
   if re.search(r"void\s*\*\s*S4_malloc\s*\(\s*size_t\s+size\s*\)\s*\{",s): kind="DEF"
   if re.search(r"void\s*\*\s*S4_malloc\s*\(\s*size_t\s+size\s*\)\s*;",s): kind="DECL"
   fn=func_of(lines,idx-1)
   in_fmm="YES" if f.startswith("S4/fmm/") else "NO"
   scope="OUT"; basis="用户范围决策：不在模式/缓存安装验收路径，也不在 FMM/FFT 失败传播链"
   if kind in ("COMMENT","DEF","DECL"):
    scope="OUT"; basis="非分配点（注释/定义/声明）"
   elif in_fmm=="YES":
    scope="IN"; basis="D003 范围：FMM/FFT 失败传播链上的分配点（S3/S4 FMM 六文件候选；U38/U90/U95）"
   elif f=="S4/S4.cpp" and idx in IN_S4:
    scope="IN"; basis=IN_S4[idx]
   var=extract_var(s)
   rows.append({"file":f,"line":idx,"function":fn,"kind":kind,"in_fmm_dir":in_fmm,"d003_scope":scope,
                "d003_basis":basis,"null_check_present":null_check(lines,idx-1,var),
                "consequence_on_fail":consequence(lines,idx-1,kind,var)})
 return rows
def cmd_d017():
 rows=d017_rows()
 hdr=["file","line","function","kind","in_fmm_dir","d003_scope","d003_basis","null_check_present","consequence_on_fail"]
 total=len(rows); calls=sum(1 for r in rows if r["kind"]=="CALL")
 inn=sum(1 for r in rows if r["d003_scope"]=="IN"); outn=sum(1 for r in rows if r["d003_scope"]=="OUT")
 outc=sum(1 for r in rows if r["d003_scope"]=="OUT" and r["kind"]=="CALL")
 out=["# D017_S4MALLOC_INVENTORY_S5R2.tsv -- read-only inventory of every S4_malloc text occurrence",
     "# in git show 05097a7 S4/ (.c/.cpp/.h/.hpp). [源码] only; nothing was run for this table.",
     "# d003_scope IN = user scope decision (mode/cache installation acceptance path or FMM/FFT",
     "# failure propagation chain); OUT = D017 range (allocation points not in D003/P05).",
     "# COUNTS total_occurrences=%d call=%d in_scope=%d out_scope=%d out_scope_call=%d non_call=%d"%(total,calls,inn,outn,outc,total-calls),
     "# D017_SCOPE = OUT rows; out_scope_call=%d allocation sites (the D017 list), non_call=%d"%(outc,total-calls)]
 body=[TAB.join(hdr)]
 for r in rows:
  body.append(TAB.join([str(r[k]) for k in hdr]))
 put("D017_S4MALLOC_INVENTORY_S5R2.tsv",NL.join(out+body)+NL)
 print("D017 total=%d CALL=%d IN=%d OUT=%d OUT_CALL=%d"%(total,calls,inn,outn,outc))
 return rows

# ---------------- S5R1 errata ES5-1..ES5-5 ----------------
ES51=[("S5-B-05","logs/60-t6-results.json",359,478),
      ("S5-B-06","logs/60-t6-main.log",58,479),
      ("S5-B-07","logs/61-t6-diag-layer.log",374,480),
      ("S5-B-08","logs/62-t6-repeat.log",389,481),
      ("S5-B-09","s1_run.sh",485,485)]
def es51():
 s1=lines_of(S1); out=[]
 for iid,name,first,row in ES51:
  hit=[i+1 for i,l in enumerate(s1) if name in l]
  if not hit or hit[0]!=first: raise SystemExit("ES5-1 first occurrence mismatch %s got %s want %d"%(iid,hit[:3],first))
  pat=re.compile(r"^\| "+BT+re.escape(name)+BT+r" \| ([0-9a-f]{64}) \|$")
  m=pat.match(s1[row-1])
  if not m: raise SystemExit("ES5-1 table row not found at %d for %s"%(row,iid))
  out.append((iid,name,first,row,m.group(1),s1[row-1]))
 return out
def es52():
 res={}
 for label,ref in (("B","37a82e8:S4/pattern/pattern.c"),("A","876181c:S4/pattern/pattern.c"),("F4","05097a7:S4/pattern/pattern.c")):
  txt=git_show(ref); lines=txt.split(NL)
  d={}
  for i,l in enumerate(lines,1):
   if re.search(r"for\s*\(\s*j\s*=\s*i\s*\+\s*1;\s*i\s*<\s*nshapes;\s*\+\+i\s*\)",l) and "loop" not in d: d["loop"]=i
   if re.match(r"double shape_get_intersection_area\(",l) and "shape" not in d: d["shape"]=i
   if re.match(r"static void fprint_double\(",l) and "fprint" not in d: d["fprint"]=i
  res[label]=d
 if res["B"]["loop"]!=798 or res["A"]["loop"]!=798 or res["F4"]["loop"]!=815: raise SystemExit("ES5-2 loop lines unexpected "+repr(res))
 if res["F4"]["shape"]!=474 or res["F4"]["fprint"]!=1178: raise SystemExit("ES5-2 F4 function lines unexpected "+repr(res))
 return res
def es54():
 d=os.path.join(REPO,"checkpoints/p05/evidence/p05-s5r1")
 sums=os.path.join(d,"SHA256SUMS.txt")
 listed=set()
 for line in rd(sums).splitlines():
  line=line.strip()
  if not line or line.startswith("#"): continue
  a,n=line.split(None,1); listed.add(n.strip())
 miss=[]; bad=[]
 for r_,dirs,files in os.walk(d):
  dirs[:]=sorted(x for x in dirs if x not in ("tmp","gate"))
  for f in sorted(files):
   fp=os.path.join(r_,f); rel=os.path.relpath(fp,d)
   if os.path.basename(f)=="SHA256SUMS.txt" or rel=="safe_run.log": continue
   if rel not in listed: miss.append(rel)
   else:
    a=[x for x in listed if x==rel][0]
    h=None
    for line in rd(sums).splitlines():
     if line.strip().endswith("  "+rel): h=line.split()[0]
    if h and sha_f(fp)!=h: bad.append(rel)
 return {"items":len(listed),"missing":miss,"bad":bad}
def s5r1_report_recheck():
 checks=[]
 rep=rd(os.path.join(REPO,S5R1REP)); lines=rep.splitlines()
 forb=["P05-S6","P05 已完成","P05-S5 已完成","已签收 P05-S5","P05 完成"]
 def allowed(w,l):
  if w in ("P05 完成","已签收 P05-S5") and ("不宣布" in l or "未" in l or "不" in l): return True
  return False
 bad=[(w,i) for w in forb for i,l in enumerate(lines,1) if w in l and not allowed(w,lines[i-1])]
 checks.append(("FORBIDDEN_TOKENS_ABSENT",not bad,str(bad[:4])))
 items=[]
 in9=False
 for l in lines:
  if l.strip()=="## 9 交付物": in9=True; continue
  if in9 and l.startswith("## "): break
  if in9:
   m=re.match(r"^\s*(\d+)\.\s+(.+?)\s*$",l)
   if m: items.append(m.group(2).strip())
 checks.append(("DELIVERABLE_COUNT_8",len(items)==8,"%d"%len(items)))
 checks.append(("DELIVERABLE_LAST_SUMS",bool(items) and items[-1]=="SHA256SUMS.txt",items[-1] if items else "none"))
 checks.append(("DELIVERABLE_NO_BACKTICK",all(BT not in x for x in items),""))
 env=os.path.join(REPO,"checkpoints/p05/evidence/p05-s5r1")
 def tsv(name):
  rows=[l.split(TAB) for l in rd(os.path.join(env,name)).splitlines() if l.strip() and not l.startswith("#")]
  return rows
 inv=tsv("S5_INPUTS_S5R1.tsv"); tri=tsv("S5_TRIAGE_S5R1.tsv"); acc=tsv("P05_ACCEPTANCE_MAP_S5R1.tsv")
 gc={}
 for r in inv[1:]: gc[r[1]]=gc.get(r[1],0)+1
 cc={}
 for r in tri[1:]: cc[r[1]]=cc.get(r[1],0)+1
 yes=sum(1 for r in tri[1:] if r[6]=="YES"); blk=sum(1 for r in tri[1:] if r[4].startswith("YES"))
 ac={}
 for r in acc[1:]: ac[r[0]]=r[3]
 dd=rd(os.path.join(env,"S5_INPUTS_DEDUP_S5R1.txt"))
 pre=int(re.search(r"PRE_DEDUP_ROWS=(\d+)",dd).group(1)); mer=int(re.search(r"MERGED_ROWS=(\d+)",dd).group(1))
 need=["- A 组：%d 行"%gc.get("A",0),"- B 组：%d 行"%gc.get("B",0),"- C 组：%d 行"%gc.get("C",0),"- D 组：%d 行"%gc.get("D",0),
       "- 去重前 %d 行；合并记录 %d 条"%(pre,mer),"去重后 %d 行"%len(inv[1:])]
 for k in ["REGISTRY_ONLY","NEEDS_TEST","NEEDS_FIX_NEW_DEFECT","RECORD_ONLY_OPEN","NEEDS_USER_RULING"]:
  need.append("- %s=%d"%(k,cc.get(k,0)))
 need.append("- needs_user_ruling=YES 共 %d 行；blocks_P06_D004=YES 共 %d 行。"%(yes,blk))
 for k in ["AC-1","AC-2","AC-3","AC-4"]:
  need.append("- %s（"%k)
 miss=[x for x in need if x not in rep]
 checks.append(("COUNTS_MATCH_SOURCE_TABLES",not miss,str(miss[:5])))
 okac=all(ac.get(k,"") in rep for k in ("AC-1","AC-2","AC-3","AC-4"))
 checks.append(("ACCEPTANCE_STATUS_LINES",okac,""))
 gate=os.path.join(env,"gate/GATE_S5R1_end.txt")
 gl=rd(gate).splitlines()
 counts=[l for l in gl if l.startswith("COUNTS")]; fails=[l for l in gl if l.startswith("FAILS=")]
 fd=[l for l in gl if l.startswith("FAIL"+TAB)]
 block=counts+fails+["# FAIL detail lines:"]+fd
 miss2=[x for x in block if x not in rep]
 checks.append(("APPENDIX_B_MATCHES_FORMAL_GATE",not miss2,str(miss2[:3])))
 checks.append(("APPENDIX_A_MARK",("## 附录 A" in rep),""))
 checks.append(("APPENDIX_B_MARK",("## 附录 B" in rep),""))
 checks.append(("VERDICT_LINE",("本轮完成 P05-S5 R1 范围，等待用户审核" in rep),""))
 # process evidence: report_check not rerun after the formal gate; (ii) was amended
 log=rd(os.path.join(env,"safe_run.log")).splitlines()
 gate_idx=[i+1 for i,l in enumerate(log) if "gate_s5r1.sh end" in l and "--shakedown" not in l]
 after=log[gate_idx[-1]:] if gate_idx else []
 rc_after=[l for l in after if "s5r1_chain.py report_check" in l]
 amend=[l for l in log if "git commit --amend" in l]
 proc_ok=(len(rc_after)==0 and len(amend)>=1)
 checks.append(("REPORT_CHECK_NOT_RERUN_AFTER_GATE",proc_ok,"rc_after=%d amend=%d"%(len(rc_after),len(amend))))
 # draft diffs
 drafts=["checkpoints/p05/P05_S5_PLAN_DRAFT.md","checkpoints/p05/P05_S5_REGISTRY_PATCH_DRAFT.md"]
 try:
  d1=git_diff("6089637","9f537f7",drafts)
 except Exception as e:
  d1="GIT_DIFF_FAILED "+str(e)
 try:
  d2=git_diff("f46ac87","9f537f7",drafts+["checkpoints/p05/P05_S5R1_REPORT.md"])
  amend_stat=subprocess.check_output(["git","diff","--stat","f46ac87..9f537f7"],text=True)
 except Exception as e:
  d2="GIT_DIFF_FAILED "+str(e); amend_stat=""
 fails=sum(1 for c in checks if not c[1])
 return {"checks":checks,"fails":fails,"draft_diff":d1,"amend_diff":d2,"amend_stat":amend_stat}
def cmd_recheck():
 r=s5r1_report_recheck(); e4=es54()
 out=["# S5R1_REPORT_RECHECK_S5R2.txt -- read-only recheck of the final P05-S5 R1 report (ES5-3)",
      "# plus the ES5-4 coverage recomputation. No s5r1 product is modified; nothing is rerun.",
      "# recheck time: "+datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),""]
 out.append("## A. command checks on the final report")
 for name,ok,det in r["checks"]:
  out.append("CHECK\t%s\t%s\t%s"%(name,"PASS" if ok else "FAIL",det))
 out.append("RECHECK_FAILS=%d"%r["fails"]); out.append("")
 out.append("## B. 6089637..9f537f7 diff of the two S5R1 drafts (line by line)")
 out.append(r["draft_diff"].rstrip())
 out.append("")
 out.append("## C. amend evidence: f46ac87 (original (ii)) -> 9f537f7 (amended (ii))")
 out.append(r["amend_stat"].rstrip())
 out.append(r["amend_diff"].rstrip())
 out.append("")
 out.append("## D. ES5-4 coverage recomputation (exclude gate/ and shakedown/gate/ and tmp/)")
 out.append("S5R1_EVIDENCE_SUMS_ITEMS=%d"%e4["items"])
 out.append("MISSING_FROM_SUMS=%s"%(e4["missing"] if e4["missing"] else "none"))
 out.append("HASH_MISMATCH=%s"%(e4["bad"] if e4["bad"] else "none"))
 out.append("ES5_4_RESULT=%s"%("COVERS_ALL_AFTER_EXCLUDING_SHAKEDOWN_GATE" if not e4["missing"] and not e4["bad"] else "GAP"))
 put("S5R1_REPORT_RECHECK_S5R2.txt",NL.join(out)+NL)
 print("RECHECK fails=%d items=%d missing=%d"%(r["fails"],e4["items"],len(e4["missing"])))
 return r
def cmd_errata():
 r=s5r1_report_recheck(); e1=es51(); e2=es52(); e4=es54(); rows=d017_rows()
 total=len(rows); calls=sum(1 for x in rows if x["kind"]=="CALL")
 inn=sum(1 for x in rows if x["d003_scope"]=="IN"); outn=sum(1 for x in rows if x["d003_scope"]=="OUT")
 outc=sum(1 for x in rows if x["d003_scope"]=="OUT" and x["kind"]=="CALL")
 t=[]
 t.append("# ERRATA_S5.txt -- P05-S5 errata register (append-only from ES5-1; written by P05-S5 R2)")
 t.append("# This round creates the file with ES5-1..ES5-5. Later rounds append new ES5-n entries only.")
 t.append("# Written: "+datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
 t.append("")
 t.append("ES5-1")
 t.append("- 事实：S5R1 输入表 S5-B-05/06/07/08 的 source_locator 指向 S1_BASELINE_AND_ENUMERATION.md 全文第一次出现处（第 359/58/374/389 行），应为该报告 11.2 表的第 478/479/480/481 行；对应 current_status_text 应为表中的哈希原文。S5-B-09 的第 485 行无误。")
 for iid,name,first,row,h,rowtext in e1:
  t.append("  更正 %s：source_locator=S1_BASELINE_AND_ENUMERATION.md 第 %d 行（原第 %d 行）；current_status_text=%s"%(iid,row,first,rowtext))
 t.append("- 证据：checkpoints/p05/S1_BASELINE_AND_ENUMERATION.md 第 359/58/374/389 行（第一次出现）与第 478/479/480/481/485 行（11.2 表）；由脚本重新定位。")
 t.append("- 影响范围：只影响 S5R1 输入表中这 5 行的 locator 与 current_status_text；不影响任何判定或 S5R1 产物。")
 t.append("- 处理方式：只登记勘误；更正后的 5 行写进本轮 P05_S5_OPEN_ITEMS.tsv 与 ERRATA_S5.txt，不改 registries/s5r1/ 的任何文件。")
 t.append("")
 t.append("ES5-2")
 t.append("- 事实：S5R1 补丁草案与 U99 中的 pattern.c:798 是 B/A 树的行号，F4 上是第 815 行；528 与 1164 是旧树行号，F4 上 shape_get_intersection_area 在 474 行、fprint_double 在 1178 行。U99 原文不改。")
 t.append("  三棵树并列（由 git show 读出）：")
 for label in ("B","A","F4"):
  t.append("  %s: 内层循环 for(j = i+1; i < nshapes; ++i) 第 %d 行；shape_get_intersection_area 起始第 %d 行；fprint_double 起始第 %d 行"%(label,e2[label]["loop"],e2[label]["shape"],e2[label]["fprint"]))
 t.append("- 证据：git show 37a82e8:S4/pattern/pattern.c、876181c:S4/pattern/pattern.c、05097a7:S4/pattern/pattern.c；行号由脚本按文本匹配读出。")
 t.append("- 影响范围：只影响补丁草案与 U99 引用的行号；U99 原文与 S3R4 产物不改。")
 t.append("- 处理方式：补丁 v2 与 R-P05-02 登记一律写 F4 行号，旧树行号放括号内（U370）。")
 t.append("")
 t.append("ES5-3")
 t.append("- 事实：S5R1 正式门禁之后对报告与两份草案做了手工修改并 amend 了 (ii)，修改后没有重跑 report_check。reflog 显示 f46ac87（原 (ii)）被 amend 为 9f537f7（终版 (ii)），两次提交均改动了报告与两份草案的禁用字样。")
 t.append("- 证据：git reflog（9f537f7 commit (amend) ← f46ac87 commit）；git diff --stat f46ac87..9f537f7；6089637..9f537f7 的两份草案逐行差异见 checkpoints/p05/evidence/p05-s5r2/S5R1_REPORT_RECHECK_S5R2.txt 第 B 节；S5R1 safe_run.log 正式门禁行之后没有 report_check 调用。")
 t.append("- 只读复核结果：本轮对 S5R1 最终版报告重跑禁用词与数字/源表一致性检查，RECHECK_FAILS=%d（明细见 S5R1_REPORT_RECHECK_S5R2.txt）。"%r["fails"])
 t.append("- 影响范围：S5R1 已提交产物不改；本轮只登记流程违规与复核结果。")
 t.append("- 处理方式：只登记勘误；本轮严格遵守正式门禁后不再手工修改、不 amend、不 rebase（任务书 §3.5）。")
 t.append("")
 t.append("ES5-4")
 t.append("- 事实：S5R1 end 门禁的 EVIDENCE_SUMS_COVERS_ALL FAIL 是检查器缺陷：gate_check_s5r1.py 的覆盖检查只排除顶层 gate/，没有排除 shakedown/gate/。")
 t.append("- 复算：对 p05-s5r1 证据目录排除 gate/、shakedown/gate/ 与 tmp/ 后重算覆盖：清单 %d 项，MISSING_FROM_SUMS=%s，HASH_MISMATCH=%s。"%(e4["items"],e4["missing"] if e4["missing"] else "none",e4["bad"] if e4["bad"] else "none"))
 t.append("- 影响范围：S5R1 门禁结论只该是检查器缺陷，不是证据缺失；S5R1 产物不改。")
 t.append("- 处理方式：S5R2 的 end 门禁检查器把排除列表（gate/、shakedown/gate/、tmp/、trees/）写进门禁输出；S5R1 不重跑。")
 t.append("")
 t.append("ES5-5")
 t.append("- 事实：S5R1 输入表中非 FMM S4_malloc 写为约 35–43 处，从未逐点核实。")
 t.append("- 证据：本轮 D017 只读清单：F4 全部 S4_malloc 文本出现 %d 处（CALL %d；IN %d；OUT %d，其中 OUT CALL %d）；见 D017_S4MALLOC_INVENTORY_S5R2.tsv。"%(total,calls,inn,outn,outc))
 t.append("- 影响范围：D017 的范围与计数以本轮清单为准；S5R1 输入表原文不改。")
 t.append("- 处理方式：只登记勘误；补丁 v2 的 D017 行引用本清单计数。")
 txt=NL.join(t)+NL
 put("ERRATA_S5.txt",txt)
 regp=os.path.join(S5R2REG,"ERRATA_S5.txt")
 if SHAKE:
  pass
 else:
  wr(regp,txt)
  if sha_f(regp)!=sha_b(txt.encode()): raise SystemExit("ERRATA_S5 copy mismatch")
 print("ERRATA_S5 bytes=%d fails=%d"%(len(txt.encode()),r["fails"]))

# ---------------- D016 source trace ----------------
MSG_PY="GetPowerFlux: The layer eigensystem could not be solved; no solution was returned"
MSG_LUA="GetPoyntingFlux: The layer eigensystem could not be solved; no solution was returned."
INFO2="Layer eigensystem returned info = 2"
TRACE=[
 ("S4/pattern/pattern.c",2212,2215,"D016 零场/非有限检查：返回 -10（在 1./max_field 之前）",["if(!(max_field > 0) || !isfinite(max_field)){","return -10;"]),
 ("S4/fmm/fmm_PolBasisVL.cpp",144,152,"PolBasisVL 调用 Pattern_GenerateFlowField；error 非零时释放并原样返回",["int error = Pattern_GenerateFlowField(","if(0 != error){","return error;"]),
 ("S4/S4.cpp",2422,2429,"默认选项（ClosedForm）后进入 PolBasisVL",["fmm_ret = FMMGetEpsilon_ClosedForm(","fmm_ret = FMMGetEpsilon_PolBasisVL("]),
 ("S4/S4.cpp",2435,2438,"FMMGetEpsilon 返回非零 → ComputeLayerModes 返回 20",["if(0 != fmm_ret){","return 20;"]),
 ("S4/S4.cpp",1878,1881,"ComputeLayerSolution 原样传播 20",["Simulation_ComputeLayerModes(S, L, layer_modes)","return modes_error;"]),
 ("S4/S4.cpp",1828,1831,"GetLayerSolution 原样传播",["Simulation_ComputeLayerSolution(S, L, layer_modes, layer_solution)"]),
 ("S4/S4.cpp",2518,2522,"GetPowerFlux 返回 ret=20",["Simulation_GetLayerSolution(S, layer, &Lmodes, &Lsoln)","return ret;"]),
 ("S4/main_python.c",114,137,"Python 前端：错误码 20 映射为 RuntimeError 文本",["void HandleSolutionErrorCode(const char *fname, int code){","The layer eigensystem could not be solved; no solution was returned"]),
 ("S4/main_python.c",1351,1354,"Python GetPowerFlux 用 fname=GetPowerFlux 报错",["ret = S4_Simulation_GetPowerFlux(self->S, layer, &offset, power);","HandleSolutionErrorCode(\"GetPowerFlux\", ret);"]),
 ("S4/main_lua.c",269,270,"Lua 前端：错误码 20 文本（句末带点）",["The layer eigensystem could not be solved; no solution was returned"]),
 ("S4/main_lua.c",284,291,"Lua HandleSolutionErrorCode → S4L_error 打印（非交互模式退出）",["void HandleSolutionErrorCode(lua_State *L, const char *fname, int code){","S4L_error(L,",]),
 ("S4/main_lua.c",2227,2232,"Lua GetPoyntingFlux 用 fname=GetPoyntingFlux 报错",["ret = S4_Simulation_GetPowerFlux(S,","HandleSolutionErrorCode(L, \"GetPoyntingFlux\", ret);"]),
 ("S4/rcwa.cpp",882,884,"info=2 的 stderr 打印只在 SolveLayerEigensystem 实际运行且 info!=0 时发生",["fprintf(stderr, \"Layer eigensystem returned info = %d"]),
]
def cmd_trace():
 out=["# D016_TRACE_S5R2.md -- read-only source trace of the D016 -10 path on F4 ([源码]).",
      "# F4 = 05097a7:S4 (tree 589e15eb11fcb04e031b524f25a443e7921946cf). Nothing was run for this trace;",
      "# the line numbers below are asserted by the generator against the F4 working tree before writing.",
      "# written: "+datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),""]
 out.append("## 1 链路（文件:行号，均为 F4）")
 out.append("")
 out.append("| 步 | 文件:行 | 作用 | 关键文本（[源码]） |")
 out.append("|---|---|---|---|")
 for i,(f,a,b,note,keys) in enumerate(TRACE,1):
  lines=lines_of(f)
  seg=NL.join(lines[a-1:b])
  for k in keys:
   if k not in seg: raise SystemExit("TRACE_KEY_MISSING %s:%d-%d %r"%(f,a,b,k))
  out.append("| %d | %s:%d-%d | %s | %s |"%(i,f,a,b,note," ; ".join(x.replace("|","\\|") for x in keys)))
 out.append("")
 out.append("## 2 由此推出的公共 API 期望（[源码]，未运行）")
 out.append("")
 out.append("- 根因返回值：pattern.c 第 2214 行返回 -10（此前 S3R2 提交 3e77aa9 实施）。")
 out.append("- 传播：fmm_PolBasisVL.cpp 第 151 行原样返回 -10 → S4.cpp 第 2438 行统一转成 20。")
 out.append("- Python：S4.cpp 第 2522 行返回 20 → main_python.c 第 137 行文本 → HandleSolutionErrorCode 抛 RuntimeError，fname=GetPowerFlux，文本为：")
 out.append("  "+MSG_PY)
 out.append("- Lua：同一 20 → main_lua.c 第 269 行文本 → HandleSolutionErrorCode（fname=GetPoyntingFlux，main_lua.c 第 2232 行）经 S4L_error 打印到 stderr，文本为（句末带点）：")
 out.append("  "+MSG_LUA)
 out.append("- REPL 交互模式（无脚本参数、stdin 输入）下 S4L_error 只打印并返回，不退出进程；批处理模式下退出码为 1。因此 Lua 公共 API 实测使用 REPL，才能在同一进程内做重试与新对象恢复。")
 out.append("- stderr 的 "+INFO2+"：只在 SolveLayerEigensystem 实际运行且 info!=0 时由 rcwa.cpp 第 883 行打印。本链路在 2438 行提前返回 20，特征值求解没有被调用，因此该行不应出现。")
 out.append("- NV 的 -10 路径：NV 的 NG=1 max_field 非零（S1R [源码]），不触发 -10；维持 [源码] 结论（U365）。")
 txt=NL.join(out)+NL
 put("D016_TRACE_S5R2.md",txt)
 print("TRACE rows=%d bytes=%d"%(len(TRACE),len(txt.encode())))

# ---------------- D016 preregistration ----------------
def build_tsv():
 p=os.path.join(EV,"D016_BUILD_S5R2.tsv"); d={}
 if not os.path.isfile(p): raise SystemExit("D016_BUILD_MISSING")
 hdr=None
 for line in rd(p).splitlines():
  if not line.strip() or line.startswith("#"): continue
  f=line.split(TAB)
  if hdr is None: hdr=f; continue
  d[dict(zip(hdr,f)).get("check","")]=dict(zip(hdr,f)).get("value","")
 return d
def cmd_prereg():
 b=build_tsv()
 rows=[]
 hdr=["point_id","frontend","basis","NumBasis","kind","expected_status","expected_rc","expected_exception","expected_text","expected_finite","stderr_info2","rel_err_threshold","status","note"]
 def add(pid,fe,basis,nb,kind,st,rc,exc,text,fin,info2,rel,note,status="INFLUENCED"):
  rows.append([pid,fe,basis,str(nb),kind,st,rc,exc,text,fin,info2,rel,status,note])
 for nb in (1,2,3,4):
  add("VL_NB%d"%nb,"py","VL",nb,"FAILURE","EXCEPTION","20","RuntimeError",MSG_PY,"NO","ABSENT","-","源码追踪：pattern.c:2214 -10 → S4.cpp:2438 20 → main_python.c:137")
  add("VL_NB%d_RETRY"%nb,"py","VL",nb,"RETRY_SAME_OBJECT","EXCEPTION","20","RuntimeError",MSG_PY,"NO","ABSENT","-","同一对象同选项重试，期望同一失败（确定性失败，不崩溃）")
  add("VL_NB%d"%nb,"lua","VL",nb,"FAILURE","FAIL_VISIBLE","0","-",MSG_LUA,"NO","ABSENT","-","REPL 模式 S4L_error 打印后返回；进程不退出、不崩溃")
  add("VL_NB%d_RETRY"%nb,"lua","VL",nb,"RETRY_SAME_OBJECT","FAIL_VISIBLE","0","-",MSG_LUA,"NO","ABSENT","-","同一对象重试，期望同一可见失败")
 for tag,basis,nb in (("VL_NB5","VL",5),("VL_NB9","VL",9),("Jones_NB1","Jones",1),("NV_NB1","NV",1)):
  add(tag,"py",basis,nb,"CONTROL","RETURNED","0","-","-","YES","ABSENT","-","对照点：成功且结果有限")
  add(tag,"lua",basis,nb,"CONTROL","VALUES","0","-","-","YES","ABSENT","-","对照点：成功且结果有限")
 add("VL_NB9_RECOVER","py","VL",9,"RECOVERY","RETURNED","0","-","-","YES","ABSENT","1e-12","同一进程失败之后新建对象，与另起进程 VL_NB9_REF 逐元素相对误差 ≤1e-12")
 add("VL_NB9_RECOVER","lua","VL",9,"RECOVERY","VALUES","0","-","-","YES","ABSENT","1e-12","同一进程失败之后新建对象，与另起进程 VL_NB9_REF 逐元素相对误差 ≤1e-12")
 add("VL_NB9_REF","py","VL",9,"REFERENCE","RETURNED","0","-","-","YES","ABSENT","-","另起进程参考值")
 add("VL_NB9_REF","lua","VL",9,"REFERENCE","VALUES","0","-","-","YES","ABSENT","-","另起进程参考值")
 add("PY_RC","py","-","-","PROCESS","0","0","-","-","-","ABSENT","-","Python 主进程 exit code；不得崩溃")
 add("LUA_RC","lua","-","-","PROCESS","0","0","-","-","-","ABSENT","-","Lua REPL 进程 exit code（EOF 后正常退出）；不得崩溃")
 add("PY_STDERR_INFO2","py","-","-","PROCESS","ABSENT","-","-","-","-","ABSENT","-","Python 进程 stderr 不出现 Layer eigensystem returned info = 2")
 add("LUA_STDERR_INFO2","lua","-","-","PROCESS","ABSENT","-","-","-","-","ABSENT","-","Lua 进程 stderr 不出现 Layer eigensystem returned info = 2")
 add("LUA_STDERR_MSG_COUNT","lua","-","-","PROCESS","8","-","-",MSG_LUA,"-","ABSENT","-","4 个失败点 + 4 次同对象重试 = 8 条可见报错")
 add("PYEXT_SHA256","py","-","-","ARTIFACT",b.get("PYEXT_SHA256","MISSING"),"-","-","-","-","-","-","F4 构建的 Python 扩展（不注入）")
 add("LUA_SHA256","lua","-","-","ARTIFACT",b.get("LUA_FRONTEND_SHA256","MISSING"),"-","-","-","-","-","-","F4 构建的 Lua 可执行文件（不注入）")
 add("LIBS4A_SHA256","-","-","-","ARTIFACT",b.get("LIB_S4_A_SHA256","MISSING"),"-","-","-","-","-","-","F4 构建的 libS4.a")
 out=["# PREREG_D016_S5R2.tsv -- D016 public-API pre-registration (status INFLUENCED: expectations are",
     "# based on the S1R observations in t6_vl_nb1.py / P05_S1R_O1_ATTRIBUTION.md section 4 and on the",
     "# F4 source trace D016_TRACE_S5R2.md; recorded before the first formal D016 run, sha256 logged in",
     "# PREREG_D016_S5R2.tsv.sha256.txt. After the formal runs only new *_ERRATA* files may be created."]
 out.append(TAB.join(hdr))
 for r in rows: out.append(TAB.join(str(x) for x in r))
 txt=NL.join(out)+NL
 wr(os.path.join(S5R2REG,"PREREG_D016_S5R2.tsv"),txt)
 h=sha_b(txt.encode())
 wr(os.path.join(S5R2REG,"PREREG_D016_S5R2.tsv.sha256.txt"),"# sha256 of PREREG_D016_S5R2.tsv, written before the formal D016 runs"+NL+h+"  PREREG_D016_S5R2.tsv"+NL)
 put("PREREG_D016_S5R2.tsv",txt)
 put("PREREG_D016_S5R2.tsv.sha256.txt",rd(os.path.join(S5R2REG,"PREREG_D016_S5R2.tsv.sha256.txt")))
 print("PREREG rows=%d sha=%s"%(len(rows),h[:16]))
 return rows

import base64 as _b64
# ---------------- registry patch v2 ----------------
def verdict_result_text():
 p=os.path.join(EV,"D016_VERDICT_S5R2.tsv")
 if not os.path.isfile(p): return "正式两遍尚未运行（预注册见 checkpoints/p05/registries/s5r2/PREREG_D016_S5R2.tsv）"
 m=re.search(r"(?m)^SUMMARY\tMATCH=(\d+)\tMISMATCH=(\d+)\tFLAKY=(\d+)$",rd(p))
 if not m: return "正式结果文件存在但 SUMMARY 无法解析（照实报告）"
 a,b,c=int(m.group(1)),int(m.group(2)),int(m.group(3))
 if b==0 and c==0:
  return "正式两遍 MATCH=%d、MISMATCH=0、FLAKY=0（Python/Lua 公共 API；见 checkpoints/p05/registries/s5r2/D016_VERDICT_S5R2.tsv）"%a
 return "正式两遍 MATCH=%d、MISMATCH=%d、FLAKY=%d（见 checkpoints/p05/registries/s5r2/D016_VERDICT_S5R2.tsv；照实报告，不改期望）"%(a,b,c)
def patch_spec():
 rows=d017_rows()
 total=len(rows); calls=sum(1 for r in rows if r["kind"]=="CALL")
 inn=sum(1 for r in rows if r["d003_scope"]=="IN"); outn=sum(1 for r in rows if r["d003_scope"]=="OUT")
 outc=sum(1 for r in rows if r["d003_scope"]=="OUT" and r["kind"]=="CALL")
 res=verdict_result_text()
 note_d003=("> 2026-10-18 P05-S5 R2 记录：S3-4b（失败后模式/缓存不安装）由 U29 在 F4 上带范围声明关闭（202 注入点 HOLD 202/VIOLATED 0）；"
            "F4 上 M2 正式两遍 191/191 MATCH、M1R3 651 点两遍全 MATCH。U364：M3a/M3b 的 make test 与 E2E 作为 F4 上的历史证据可被 S5 引用；"
            "S5R3 在 F4 上重跑一次 make test 与全量 E2E（M3b 42 点加 D016 点）；修复前证据不得称为修复后验证。D003 本身仍为 OPEN。")
 notes_record=[
  "> 2026-10-18 P05-S5 R2 RECORD_ONLY_OPEN 落位（S5-M3D-01）：B 侧 jones/vl 静默、nv CRASH 只作为 B 列基线观察记录，不是修复证据（U359 范围声明 (a)）；S5 不重跑 B 树。",
  "> 2026-10-18 P05-S5 R2 RECORD_ONLY_OPEN 落位（S5-M3D-02）：NB=1–8 与类别 C：M2-07 81 点全 MATCH；类别 C（1D+FFT 候选）无 S4 内可执行用例，保持 OPEN（U249）。",
  "> 2026-10-18 P05-S5 R2 RECORD_ONLY_OPEN 落位（S5-M3D-05）：U2 stage e（I1 特殊规则）在 S4 内 NOT_FOUND_IN_SCOPE，保持 OPEN（U248）。",
  "> 2026-10-18 P05-S5 R2 RECORD_ONLY_OPEN 落位（S5-M3D-06）：RP-R6d-3 no-TWICE 路径属 OUT_OF_SCOPE_D003，保持 OPEN（U5；E9-76）。",
  "> 2026-10-18 P05-S5 R2 RECORD_ONLY_OPEN 落位（S5-M3D-07）：RP-R6d-7 的 D016 B 侧 rc 来源未追踪；F 侧归 D016/D003，B 列观察保持 OPEN。",
  "> 2026-10-18 P05-S5 R2 RECORD_ONLY_OPEN 落位（S5-C-03）：S2 对 fmm_kottke 的闭合仅限分配失败与 solve_info 传播，不含除数数值安全，保持 OPEN（P05_S1_S2_SIGNOFF.md 第 21 行）。",
 ]
 d016=("| D016 / P1（P05-S5 R2 核对完成；P05 期间提前登记） | 图案层向量场归一化遇到全零场时除以零得到 NaN 并仍返回成功：pattern_generate_flow_field 在 1./max_field 之前不检查 max_field，最终 return 0；"
       "下游 Pattern_GenerateFlowField 的调用方（PolBasisVL/Jones/NV）已有 if(0 != error) 清理路径，但该情形从未走入 | 2026-10-11 P05-S1R 实测：VL 基、n_G=1（NumBasis 1–4）时，图案层流场 max_field=0，场被写为 NaN，"
       "NaN 进入 Epsilon_inv/Epsilon2，特征值求解以 info=2 失败，公共 API 抛 RuntimeError、驱动 rc 20；B/A/H 三树一致。修法已实施：P05-S3R2 提交 3e77aa9；F4 源码 pattern.c 2210–2216（[源码]）。"
       "2026-10-18 P05-S5 R2 在 F4 上用 Python 与 Lua 公共 API 实测（U365）：在 F4 上、在该输入下经公共 API 可见失败且恢复正确；"+res+
       " | 现状：已实施（源码确认）且公共 API 已实测（S5R2）；NV 的 -10 路径触发不了，维持 [源码] 结论。R-P05-01（让 n_G=1 可计算）不包含在本条，见 R-P05-01 行 |")
 d017=("| D017 / P2（P05-S5 R2 期间登记；不在 P05 修；U369） | 非 FMM 路径的 S4_malloc 失败未逐点检查/未统一传播：F4 上 S4_malloc 共 %d 处文本出现（CALL %d；IN %d；OUT %d，其中 OUT CALL %d 即本条范围），"
       "非 FMM 其余分配点不属 D003/P05（用户范围决策） | 逐点清单（file:line/function/kind/in_fmm_dir/d003_scope/null_check/后果，[源码]）见 checkpoints/p05/registries/s5r2/D017_S4MALLOC_INVENTORY_S5R2.tsv；"
       "另有定义/声明/注释 %d 处不是分配点 | 不在 P05 修，不阻塞 P06；后续如需处理按独立工作项 |"%(total,calls,inn,outn,outc,total-calls))
 rp02=("| R-P05-02（P05-S5 R2 登记；OUT_OF_SCOPE_D003；U370） | ES3R4-5/528/1164 与 U99 既有问题：(a) pattern_get_containment_tree 第一个形状无效时返回 i+1=1，被 InitSolution 上报为内存分配失败；"
       "(b) F4 pattern.c 第 815 行（B/A 树第 798 行）内层循环 for(j = i+1; i < nshapes; ++i) 用 i 作条件与自增，nshapes>1 时只有 shape 0 被检查（U95/U99）；"
       "(c) shape_get_intersection_area 无调用者（死代码；F4 第 474 行，旧树行号 528）；(d) fprint_double 唯一调用点被注释（F4 第 1178 行，旧树行号 1164）（U90） | "
       "未验证/未修复：U99 明确修它会改变正常路径（既有输入可能新报错），故不在 P05-S3/S4 修；行号由脚本对 B(37a82e8)/A(876181c)/F4(05097a7) 三棵树核对（[源码]） | S5 登记，保持 OPEN；不在 P05 修，不阻塞 P06 |")
 rp03=("| R-P05-03（P05-S5 R2 登记；OUT_OF_SCOPE_D003；U370） | FFT/Kottke 忽略 Pattern_DiscretizeCell 的 -1..-9 返回值：fmm_FFT.cpp 与 fmm_kottke.cpp 只在返回 -12 时设 ret=1 并 goto cleanup，"
       "其余负值保持原行为（ES3R4-8；U100） | 未验证：U100 只要求写 [源码] 说明各返回码经公共 API 的可达性（文件:行号），未运行 | S5 登记，保持 OPEN；不在 P05 修，不阻塞 P06 |")
 p04=("| P04 | 固定候选clean保存流水线38步PASS、0unexpected、18/18产物绑定；主测试total257/pass256/skip1（OOM为Code Review Only）、Lua回归及binding smoke4/4；"
      "上述有限范围关闭；P05 已启动，当前处于 P05-S5 R2（登记落实与 D016 公共 API 实测，仅改文档与登记表） |")
 rp0401=("| R-P04-01 | A-10r 契约外短工作区越界；保存 SIGSEGV 探针存在，非正式 judged 用例。2026-10-10 正式复验观测：默认候选探针 rc -11（SIGSEGV）；ASan 候选与 seam 候选探针报告 heap-buffer-overflow（ztrevc_，Eigensystems.cpp:2936）。"
         "两者均为未判定探针，不计入候选 53/53、58/58，属本条范围 | 核对实际分配大小、lwork 与公开契约；确认正常公共调用能否触发。支持范围内则构造最小反例并修复，契约外则明确前置条件或制定防御行为 | "
         "P05 收口之后安排 RNP 防御专项（P05-S5 R2 登记交叉引用本条）；若正常受支持输入可达内存破坏则提前 |")
 rp0407=("| R-P04-07 | 历史 D002 等 provenance 未知；证据溯源事项 | 找到原定义/提交/输入则记录明确来源；找不到保持未知。不得用当前有限修复补造历史因果 | "
         "并行资料整理或文档阶段，默认不阻塞 P05（P05-S5 R2 登记交叉引用本条） |")
 last117=("下一轮默认修复顺序：P05 进入 S5 收口（前端与回归；U364：S5R3 在 F4 上重跑 make test 与全量 E2E），随后 P06/D004；P05 的 FMM/FFT 失败传播与 VL NB1 可达性已在 S3/S4 登记。"
          "以上后续事项仅在其自身任务明确启动后执行，不回头扩大本次 P04 验收。")
 p05row=("| P05 | Phase 2 A：D003 | 核对现有六文件 FMM 候选和 checkpoint 差异；针对实际启用的 FFT/Jones/NV/VL 等分支完成失败传播/清理/重试验证 | 每个受影响的 prepare/execute 点有正负对照；失败后模式/缓存不安装；Python/Lua 可见失败，恢复重试正确 | P04；固定选项、全新对象避免依赖 D004 | "
         "S1–S4 已由用户签收（带范围声明，见 checkpoints/p05/P05_S3_S4_SIGNOFF.md 第 2 节）；S5 进行中（R2：登记落实与 D016 公共 API 实测；U364：S5R3 收口在 F4 上重跑 make test 与全量 E2E）；验收映射见 checkpoints/p05/registries/s5r1/P05_ACCEPTANCE_MAP_S5R1.tsv |")
 d016b=("    - **D016**（已实施，归 D003 失败传播范围）：零场除零不应静默产生 NaN，应在根因处返回错误。修法已实施（P05-S3R2 提交 3e77aa9；F4 pattern.c 2210–2216，[源码]）。"
        "2026-10-18 P05-S5 R2 在 F4 上用 Python/Lua 公共 API 实测：在 F4 上、在该输入下经公共 API 可见失败且恢复正确（U365）；"+res+"；见 [登记表](testing/s4test/ISSUE_REGISTRY.md)。")
 rp0501=("    - **R-P05-01**（OPEN，经 U366 转出 P05，不阻塞）：让 n_G=1 可计算需先确认 allzero 到 1x1 的设计意图并取得独立参考解；反事实通量与 allzero 设计意图保持 OPEN，写进 S5 范围声明；见 [登记表](testing/s4test/ISSUE_REGISTRY.md) 的 R-P05-01 行。")
 b_f10="  - 2026-10-18 P05-S5 R2 登记（U366，转出 P05，不阻塞）：F10 历史因果（S5-B-01）保持 OPEN，详见 checkpoints/p05/P05_S5_OPEN_ITEMS.tsv。"
 b_f8="  - 2026-10-18 P05-S5 R2 登记（U367）：F8 历史目录（S5-B-02）不授权访问，保持未验证。"
 b_hash="  - 2026-10-18 P05-S5 R2 登记（U368）：S1 报告 11.2 的五个哈希来源（S5-B-05..09）认定为无法判定，不改写 11.2 与 EVIDENCE.sha256；更正后的行号见 checkpoints/p05/registries/s5r2/ERRATA_S5.txt ES5-1。"
 ops=[]
 def add_replace(rel,ln,must,new):
  cur=lines_of(rel)[ln-1]
  for k in must:
   if k not in cur: raise SystemExit("PATCHV2_OLD_MARKER_MISSING %s:%d %r"%(rel,ln,k))
  ops.append((rel,"REPLACE",ln,cur,new))
 def add_insert(rel,ln,newlines,must):
  cur=lines_of(rel)[ln-1]
  for k in must:
   if k not in cur: raise SystemExit("PATCHV2_ANCHOR_MISSING %s:%d %r"%(rel,ln,k))
  for x in newlines: ops.append((rel,"INSERT_AFTER",ln,"",x))
 add_insert(ISSUE,28,[note_d003]+notes_record,["D003"])
 add_replace(ISSUE,41,["D016"],d016)
 add_insert(ISSUE,41,[d017,rp02,rp03],["D016"])
 add_replace(ISSUE,85,["P04"],p04)
 add_replace(ISSUE,107,["R-P04-01"],rp0401)
 add_replace(ISSUE,113,["R-P04-07"],rp0407)
 add_replace(ISSUE,117,["下一轮默认修复顺序"],last117)
 add_replace(ROAD,51,["P05"],p05row)
 add_replace(ROAD,145,["D016"],d016b)
 add_replace(ROAD,146,["R-P05-01"],rp0501)
 add_insert(ROAD,146,[b_f10,b_f8,b_hash],["R-P05-01"])
 return ops,{"d017_counts":(total,calls,inn,outn,outc),"d016_result":res}
def content_after(rel,ops,orig):
 per={}
 for (r,kind,ln,old,new) in ops:
  if r!=rel: continue
  per.setdefault((kind,ln),[]).append(new)
 out=[]
 for i,l in enumerate(orig,1):
  rep=per.get(("REPLACE",i))
  out.append(rep[0] if rep else l)
  for x in per.get(("INSERT_AFTER",i),[]): out.append(x)
 return out
def cmd_patchv2():
 ops,meta=patch_spec()
 files=[ISSUE,ROAD]
 new={}
 for rel in files:
  new[rel]=content_after(rel,ops,lines_of(rel))
 L=[]
 L.append("# P05-S5 登记表补丁 v2（P05_S5_REGISTRY_PATCH_V2）")
 L.append("")
 L.append("> 依据 U371 批准应用：testing/s4test/ISSUE_REGISTRY.md 与 PROJECT_ROADMAP.md。本文件是 v2 的完整记录，")
 L.append("> 由 apply_patch_s5r2.py 按文末 PATCHSPEC 机械应用；先断言两个目标文件的起始 sha256，应用后输出 unified diff 并断言只改动了这里列出的行。")
 L.append("> 行号以本轮开工 HEAD 9f537f7c312b2ab7c64d5c0ea82da34e637da5d4 的两个文件为准；F4 源码行号见 ES5-2 与 R-P05-02。")
 L.append("> 本文件吸收 U364–U371 与 ES5-1..ES5-5；不含阶段完成或签收的字样；P05-S5 未完成、未签收。")
 L.append("")
 L.append("## 1. ISSUE_REGISTRY.md 变更（%d 个操作）"%len([o for o in ops if o[0]==ISSUE]))
 L.append("")
 L.append("- 第 28 行后插入：D003 收尾 / U364 记录 1 行 + 6 条 RECORD_ONLY_OPEN 落位（S5-M3D-01/02/05/06/07、S5-C-03）。")
 L.append("- 第 41 行替换：D016 行更新为已实施（3e77aa9，F4 pattern.c 2210–2216）并引用本轮公共 API 实测结论。")
 L.append("- 第 41 行后插入：D017（U369，计数引用本轮清单）、R-P05-02（U370，F4 行号）、R-P05-03（U100）。")
 L.append("- 第 85、107、113、117 行：P04/R-P04-01/R-P04-07/下一轮顺序的状态文字同步与交叉引用（U364/U371）。")
 L.append("")
 L.append(FENCE+"diff")
 a=lines_of(ISSUE)
 L+=list(difflib.unified_diff(a,new[ISSUE],fromfile="a/"+ISSUE,tofile="b/"+ISSUE,lineterm="",n=1))
 L.append(FENCE)
 L.append("")
 L.append("## 2. PROJECT_ROADMAP.md 变更（%d 个操作）"%len([o for o in ops if o[0]==ROAD]))
 L.append("")
 L.append("- 第 51 行 P05 行状态列：S1–S4 已由用户签收（带范围声明）；S5 进行中（R2）。")
 L.append("- 第 145 行 D016：已实施（3e77aa9）+ S5R2 公共 API 实测结论；第 146 行 R-P05-01：经 U366 转出 P05、保持 OPEN。")
 L.append("- 第 146 行后插入：U366（F10）、U367（F8）、U368（S1 报告 11.2 五哈希）三条转出登记。")
 L.append("")
 L.append(FENCE+"diff")
 L+=list(difflib.unified_diff(lines_of(ROAD),new[ROAD],fromfile="a/"+ROAD,tofile="b/"+ROAD,lineterm="",n=1))
 L.append(FENCE)
 L.append("")
 L.append("## 3. 数据引用")
 L.append("")
 L.append("- D017 计数（本轮只读清单）：S4_malloc 文本出现 %d 处，CALL %d，IN %d，OUT %d（OUT CALL %d）；见 D017_S4MALLOC_INVENTORY_S5R2.tsv。"%meta["d017_counts"])
 L.append("- D016 公共 API 实测：%s。"%meta["d016_result"])
 L.append("- ES5-1 更正后的 5 行、ES5-2 三树行号、ES5-3 复核、ES5-4 复算、ES5-5 计数以 ERRATA_S5.txt 与 P05_S5_OPEN_ITEMS.tsv 为准。")
 L.append("")
 L.append("## 4. 机器可读 PATCHSPEC（apply_patch_s5r2.py 读取）")
 L.append("")
 L.append("<!-- PATCHSPEC-BEGIN -->")
 for (rel,kind,ln,old,newl) in ops:
  bo=_b64.b64encode(old.encode("utf-8")).decode() if kind=="REPLACE" else "-"
  bn=_b64.b64encode(newl.encode("utf-8")).decode()
  L.append(TAB.join(["OP",kind,rel,str(ln),bo,bn]))
 L.append("<!-- PATCHSPEC-END -->")
 L.append("")
 L.append("## 5. 不在本补丁范围")
 L.append("")
 L.append("- 不改写 P05_S3_S4_SIGNOFF.md 与 P05_S1_S2_SIGNOFF.md 的签收原文；不改写 RULINGS.tsv 历史行；不改写任何历史报告。")
 L.append("- 不修改 AGENTS.md（U371）。")
 txt=NL.join(L)+NL
 wr(os.path.join(P05,"P05_S5_REGISTRY_PATCH_V2.md"),txt)
 if SHAKE: wr(os.path.join(SHK,"P05_S5_REGISTRY_PATCH_V2.proposed.md"),txt)
 print("PATCHV2 ops=%d bytes=%d result=%s"%(len(ops),len(txt.encode()),meta["d016_result"][:40]))
 return ops

# ---------------- S5 open items ----------------
OPEN_ITEMS=[
 ("S5-M3D-01","RECORD_ONLY_OPEN","S5R1 RECORD_ONLY_OPEN（B 列基线观察，不是修复证据）",ISSUE,"S5-M3D-01","B 列 jones/vl 静默、nv CRASH 只作为基线观察记录；S5 不重跑 B 树"),
 ("S5-M3D-02","RECORD_ONLY_OPEN","U249",ISSUE,"S5-M3D-02","NB=1–8 与类别 C；M2-07 81 点全 MATCH；类别 C 无 S4 内可执行用例，保持 OPEN"),
 ("S5-M3D-03","REGISTERED_R-P05-02","U90/U95/U99/U100",ISSUE,"| R-P05-02（","已登记 R-P05-02（F4 行号）与 R-P05-03（U100）"),
 ("S5-M3D-04","REGISTERED_D017","U369",ISSUE,"| D017 /","逐点清单与计数见 registries/s5r2/D017_S4MALLOC_INVENTORY_S5R2.tsv"),
 ("S5-M3D-05","RECORD_ONLY_OPEN","U248",ISSUE,"S5-M3D-05","U2 stage e 在 S4 内 NOT_FOUND_IN_SCOPE，保持 OPEN"),
 ("S5-M3D-06","RECORD_ONLY_OPEN","U5（E9-76）",ISSUE,"S5-M3D-06","RP-R6d-3 no-TWICE 路径 OUT_OF_SCOPE_D003，保持 OPEN"),
 ("S5-M3D-07","RECORD_ONLY_OPEN","S5R1 RECORD_ONLY_OPEN（B 侧基线）",ISSUE,"S5-M3D-07","RP-R6d-7 D016 的 B 侧 rc 来源未追踪；F 侧归 D016/D003"),
 ("S5-B-01","OPEN_TRANSFERRED_OUT","U366",ROAD,"F10 历史因果","F10 历史因果保持 OPEN，转出 P05，不阻塞"),
 ("S5-B-02","OPEN_TRANSFERRED_OUT","U367",ROAD,"F8 历史目录","不授权访问历史目录，保持未验证"),
 ("S5-B-03","OPEN_TRANSFERRED_OUT","U366",ISSUE,"| R-P05-01（","反事实通量保持 OPEN，转出 P05"),
 ("S5-B-04","OPEN_TRANSFERRED_OUT","U366",ISSUE,"| R-P05-01（","allzero 设计意图保持 OPEN，转出 P05"),
 ("S5-B-05","OPEN_TRANSFERRED_OUT","U368",ROAD,"S1 报告 11.2","无法判定，不改写 11.2 与 EVIDENCE.sha256；locator 更正为第 478 行（ES5-1）"),
 ("S5-B-06","OPEN_TRANSFERRED_OUT","U368",ROAD,"S1 报告 11.2","无法判定；locator 更正为第 479 行（ES5-1）"),
 ("S5-B-07","OPEN_TRANSFERRED_OUT","U368",ROAD,"S1 报告 11.2","无法判定；locator 更正为第 480 行（ES5-1）"),
 ("S5-B-08","OPEN_TRANSFERRED_OUT","U368",ROAD,"S1 报告 11.2","无法判定；locator 更正为第 481 行（ES5-1）"),
 ("S5-B-09","OPEN_TRANSFERRED_OUT","U368",ROAD,"S1 报告 11.2","无法判定；第 485 行 locator 本无误"),
 ("S5-C-01","TEST_S5R2","U365",ISSUE,"| D016 /","D016 公共 API 实测（Python/Lua，正式两遍）；见 registries/s5r2/D016_VERDICT_S5R2.tsv"),
 ("S5-C-02","OPEN_TRANSFERRED_OUT","U366",ISSUE,"| R-P05-01（","R-P05-01 保持 OPEN，转出 P05，不阻塞"),
 ("S5-C-03","RECORD_ONLY_OPEN","S5R1 RECORD_ONLY_OPEN",ISSUE,"S5-C-03","S2 对 fmm_kottke 的闭合不含除数数值安全，保持 OPEN"),
 ("S5-D-01","TEST_S5R3","U364",ISSUE,"S5R3 在 F4 上重跑一次 make test","S5R3 在 F4 上重跑 make test 与全量 E2E（M3b 42 点加 D016 点）"),
 ("S5-D-02","REGISTRY_SYNC","S5R1 REGISTRY_ONLY（文本同步）",ISSUE,"| P04 |","P04 行 P05 状态文字同步为 P05-S5 R2"),
 ("S5-D-03","OPEN_TRANSFERRED_OUT","S5R1 REGISTRY_ONLY（R-P04-01）",ISSUE,"| R-P04-01 |","R-P04-01 保持 OPEN，P05 收口之后安排；已补交叉引用"),
 ("S5-D-04","OPEN_TRANSFERRED_OUT","S5R1 REGISTRY_ONLY（R-P04-07）",ISSUE,"| R-P04-07 |","R-P04-07 保持 OPEN，默认不阻塞；已补交叉引用"),
 ("S5-D-05","REGISTRY_SYNC","S5R1 REGISTRY_ONLY（文本同步）",ISSUE,"下一轮默认修复顺序","下一轮顺序文字同步为 P05 进入 S5 收口，随后 P06/D004"),
 ("S5-D-06","TEST_S5R3","U364",ROAD,"| P05 | Phase 2 A：D003 |","P05 行状态更新；最终前端/回归证据由 S5R3 在 F4 上重跑提供"),
]
def locate(file_rel,marker):
 ls=lines_of(file_rel); hits=[i+1 for i,l in enumerate(ls) if marker in l]
 if len(hits)!=1: raise SystemExit("LOCATE_FAIL %s %r hits=%s"%(file_rel,marker,hits[:6]))
 return "%s:%d"%(file_rel,hits[0])
def cmd_open_items():
 src_issue=ISSUE; src_road=ROAD
 if SHAKE:
  ci=os.path.join(SHK,"ISSUE_REGISTRY.candidate.md"); cr=os.path.join(SHK,"ROADMAP.candidate.md")
  if not os.path.isfile(ci) or not os.path.isfile(cr): raise SystemExit("SHAKEDOWN_CANDIDATES_MISSING")
  src_issue=os.path.relpath(ci,REPO); src_road=os.path.relpath(cr,REPO)
 rows=[]
 for iid,disp,rul,fil,marker,note in OPEN_ITEMS:
  rel=src_issue if fil==ISSUE else src_road
  loc=locate(rel,marker)
  rows.append([iid,disp,rul,loc,note])
 hdr=["input_id","final_disposition","ruling","registry_location","scope_note"]
 out=["# P05_S5_OPEN_ITEMS.tsv -- the 25 de-duplicated S5R1 inputs with their final disposition (task brief section 6).",
      "# registry_location is computed after the registry patch is applied (file:line).",
      "# final_disposition values: REGISTERED_D016 / REGISTERED_D017 / REGISTERED_R-P05-0x / OPEN_TRANSFERRED_OUT /",
      "# RECORD_ONLY_OPEN / TEST_S5R2 / TEST_S5R3. REGISTRY_SYNC marks the pure text-sync rows of the S5R1",
      "# REGISTRY_ONLY class (S5-D-02, S5-D-05), which the brief's list does not name separately.",
      "# ES5-1 corrected locators: S5-B-05/06/07/08 -> 478/479/480/481 (see ERRATA_S5.txt)."]
 out.append(TAB.join(hdr))
 for r in rows: out.append(TAB.join(r))
 txt=NL.join(out)+NL
 if SHAKE:
  wr(os.path.join(SHK,"P05_S5_OPEN_ITEMS.proposed.tsv"),txt)
 else:
  wr(os.path.join(P05,"P05_S5_OPEN_ITEMS.tsv"),txt)
 print("OPEN_ITEMS rows=%d"%len(rows))
 c={}
 for r in rows: c[r[1]]=c.get(r[1],0)+1
 print("OPEN_ITEMS dispositions "+" ".join("%s=%d"%(k,c[k]) for k in sorted(c)))
 return rows

# ---------------- STATE ----------------
def state_text():
 t=[]
 t.append("# P05 当前状态（每轮结束更新，一页以内）")
 t.append("")
 t.append("> 规则见仓库根 AGENTS.md。本文件是摘要，细节以各轮报告为准。")
 t.append("")
 t.append("## 1. 当前位置")
 t.append("")
 t.append("| 项 | 值 |")
 t.append("|---|---|")
 t.append("| 分支 | codex/p05-d003-fft-error-propagation |")
 t.append("| 本轮开工基线 HEAD（s5r2） | 9f537f7c312b2ab7c64d5c0ea82da34e637da5d4（P05-S5 R1 (ii)） |")
 t.append("| HEAD:S4（冻结被测树 F4） | 589e15eb11fcb04e031b524f25a443e7921946cf（F4 提交 05097a7） |")
 t.append("| 判定器 sha256 | d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb |")
 t.append("| 阶段状态 | S1–S4 已由用户签收（带范围声明）；S5 进行中（R2：裁决入账、勘误、D017、登记落实、D016 公共 API 实测） |")
 t.append("| 当前轮次 | P05-S5 R2（s5r2）；不宣布 S5 或 P05 阶段完成 |")
 t.append("")
 t.append("## 2. 关键数字（每轮一行）")
 t.append("")
 t.append("| 轮 | 关键数字 | 报告/证据 |")
 t.append("|---|---|---|")
 t.append("| S4R9 M3c–M3e | 独立复核 DIFFS=0；签收落账 U359–U363 | M3c/M3d/M3e 报告 |")
 t.append("| S5R1 | 输入 25 行（去重前 29）；分类 REGISTRY_ONLY=5 NEEDS_TEST=3 NEEDS_FIX_NEW_DEFECT=1 RECORD_ONLY_OPEN=6 NEEDS_USER_RULING=10；勘误 E9-78/79 | P05_S5R1_REPORT.md |")
 t.append("| S5R2 | 裁决 U364–U371 入账；勘误 ES5-1..5；D017 只读清单 59 处（CALL 52；OUT 38，OUT CALL 31）；开放项 25 行落位；登记表补丁 v2 应用；D016 公共 API 实测（Python/Lua，F4，正式两遍） | P05_S5R2_REPORT.md |")
 t.append("")
 t.append("## 3. 开放问题（状态 · 去向 · 详情链接）")
 t.append("")
 t.append("| 项 | 状态 | 去向 | 详情链接 |")
 t.append("|---|---|---|---|")
 t.append("| S5 输入 25 行的最终处置 | 落位 | 本表为唯一入口 | P05_S5_OPEN_ITEMS.tsv |")
 t.append("| D017 非 FMM S4_malloc | OPEN（不在 P05 修） | 保持 OPEN，不阻塞 P06 | registries/s5r2/D017_S4MALLOC_INVENTORY_S5R2.tsv；ISSUE_REGISTRY D017 行 |")
 t.append("| R-P05-02 / R-P05-03 | OPEN（不在 P05 修） | 保持 OPEN，不阻塞 P06 | ISSUE_REGISTRY；ERRATA_S5.txt ES5-2 |")
 t.append("| F10/F8/反事实通量/allzero/11.2 五哈希 | OPEN / 未验证 | 经 U366–U368 转出 P05 | P05_S5_OPEN_ITEMS.tsv；ERRATA_S5.txt ES5-1 |")
 t.append("| S5R3 收口待办 | 待执行 | 下一轮 | 报告第 10 节 |")
 t.append("")
 t.append("## 4. S5R3 收口待办")
 t.append("")
 t.append("- 在 F4 上重跑一次 make test 与全量 E2E（M3b 42 点加 D016 点），作为 S5 收口的修复后验证（U364）。")
 t.append("- 就绪审计：F4 树、判定器、证据清单、STATE/registries/报告一致；AC-3/AC-4 的最终映射。")
 t.append("- 不宣布阶段完成；签收只由用户在对话中给出。")
 t.append("")
 t.append("## 5. 证据位置")
 t.append("")
 t.append("- **P05-S5 R2（s5r2）**：证据 checkpoints/p05/evidence/p05-s5r2/（SHA256SUMS.txt）；小表 checkpoints/p05/registries/s5r2/（SHA256SUMS.txt）；报告 P05_S5R2_REPORT.md；门禁附录 P05_S5R2_GATE_APPENDIX.md；开放项总表 P05_S5_OPEN_ITEMS.tsv；补丁 v2 P05_S5_REGISTRY_PATCH_V2.md。")
 t.append("- **P05-S5 R1（s5r1）**：证据 checkpoints/p05/evidence/p05-s5r1/；小表 checkpoints/p05/registries/s5r1/；报告 P05_S5R1_REPORT.md；草案 P05_S5_REGISTRY_PATCH_DRAFT.md、P05_S5_PLAN_DRAFT.md。")
 t.append("- 裁决总表 registries/RULINGS.tsv（追加 U364–U371）；S5 勘误 registries/s5r2/ERRATA_S5.txt；S4 勘误 registries/s4r9/ERRATA_9.txt。")
 t.append("")
 return NL.join(t)+NL
def cmd_state():
 t=state_text()
 if len(t.encode())>8192: raise SystemExit("STATE_TOO_LARGE %d"%len(t.encode()))
 if SHAKE: wr(os.path.join(SHK,"STATE.proposed.md"),t)
 else: wr(os.path.join(P05,"STATE.md"),t)
 print("STATE bytes=%d"%len(t.encode()))

# ---------------- frozen scripts ----------------
FROZEN_EXPECT={
 "gate_check_s5r2.py":("0","-"),
 "gate_s5r2.sh":("1","end"),
 "s5r2_appendix.py":("0","-"),
 "s5r2_chain.py":("6","-"),
 "s5r2_prep.py":("0","-"),
 "s5r2_startgate.py":("0","-"),
 "s5r2_build_d016.py":("0","-"),
 "apply_patch_s5r2.py":("0","-"),
 "d016_py_s5r2.py":("0","-"),
 "d016_run_s5r2.py":("0","-"),
 "d016_lua_s5r2.lua":("0","-"),
}
def frozen_rows():
 files=sorted(f for f in os.listdir(STAGE) if (("s5r2" in f) or f.startswith("gate_")) and f.endswith((".py",".sh",".lua")))
 out=["# FROZEN_SCRIPTS_S5R2.tsv -- frozen scripts after the shakedown chain, before record commit (i).",
      "# The end gate reads POST_I call expectations from this file BY COLUMN NAME (task brief section 3.7).",
      TAB.join(["path","sha256","expected_calls","mode"])]
 for f in files:
  if f not in FROZEN_EXPECT: raise SystemExit("FROZEN_EXPECT_MISSING "+f)
  exp,mode=FROZEN_EXPECT[f]
  fp=os.path.join(STAGE,f)
  if not os.path.isfile(fp): raise SystemExit("FROZEN_MISSING "+f)
  out.append(TAB.join(["testing/d003/stage_s5r2/"+f,sha_f(fp),exp,mode]))
 return out
def cmd_frozen():
 body=NL.join(frozen_rows())+NL
 if SHAKE: wr(os.path.join(SHK,"FROZEN_SCRIPTS_S5R2.tsv"),body)
 else: wr(os.path.join(EV,"FROZEN_SCRIPTS_S5R2.tsv"),body)
 print("FROZEN rows=%d%s"%(len(body.splitlines())-3," (shakedown)" if SHAKE else ""))

# ---------------- shakedown staging ----------------
def cmd_stage_shk():
 os.makedirs(SHK,exist_ok=True)
 copied=[]
 for f in ("GATE_S5R2_start.txt","ERRATA_S5.txt","D017_S4MALLOC_INVENTORY_S5R2.tsv","PREREG_D016_S5R2.tsv",
           "PREREG_D016_S5R2.tsv.sha256.txt","D016_TRACE_S5R2.md","S5R1_REPORT_RECHECK_S5R2.txt"):
  src=os.path.join(EV,f)
  if not os.path.isfile(src): raise SystemExit("STAGE_SHK_SRC_MISSING "+f)
  data=rdb(src); dst=os.path.join(SHK,f)
  open(dst,"wb").write(data); copied.append(f)
 calib=os.path.join(SHK,"d016_calib/CALIB_D016_S5R2.tsv")
 rows=[]
 if os.path.isfile(calib):
  for line in rd(calib).splitlines():
   if not line.startswith("POINT_"): continue
   f=line.split(TAB)
   if len(f)>=3:
    rows.append((f[0].replace("POINT_",""),f[1],f[2]))
 body=["# D016_VERDICT_S5R2.tsv -- SHAKEDOWN PLACEHOLDER, not a formal result.",
       "# The formal file is written by d016_run_s5r2.py formal --pass 2 in the frozen period."]
 body.append(TAB.join(["point_id","observed_calibration","would_be"]))
 for r in rows: body.append(TAB.join(r))
 open(os.path.join(SHK,"D016_VERDICT_S5R2.tsv"),"w",encoding="utf-8").write(NL.join(body)+NL)
 print("STAGE_SHK copied=%d calib_rows=%d"%(len(copied),len(rows)))

def main():
 sub=sys.argv[1] if len(sys.argv)>1 and not sys.argv[1].startswith("--") else "all"
 fn={"rulings":cmd_rulings,"d017":cmd_d017,"recheck":cmd_recheck,"errata":cmd_errata,"trace":cmd_trace,
     "prereg":cmd_prereg,"patchv2":cmd_patchv2,"open_items":cmd_open_items,"state":cmd_state,
     "frozen":cmd_frozen,"stage_shk":cmd_stage_shk,
     "all":lambda: (cmd_rulings(),cmd_recheck(),cmd_errata(),cmd_d017(),cmd_trace(),cmd_prereg(),cmd_patchv2(),cmd_state())}.get(sub)
 if fn is None: print("unknown subcommand "+sub); return 2
 fn(); return 0
if __name__=="__main__": sys.exit(main())
