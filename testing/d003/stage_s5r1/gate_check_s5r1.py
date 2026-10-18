#!/usr/bin/env python3
# gate_check_s5r1.py -- P05-S5 R1 end gate. Output lives in $EV/gate/ (or $EV/shakedown/gate/ in shakedown) and is excluded from SHA256SUMS.
# Frozen POST_I counts are read from FROZEN_SCRIPTS_S5R1.tsv BY COLUMN NAME (task brief section 5).
# safe(name, fn, exp) always receives a CALLABLE fn (E9-78 discipline); CHECK_CRASHED count is asserted to be 0.
import os,sys,re,hashlib,subprocess,datetime
REPO=os.getcwd()
EV=os.path.join(REPO,"checkpoints/p05/evidence/p05-s5r1")
SHK=os.path.join(EV,"shakedown")
REG=os.path.join(REPO,"checkpoints/p05/registries")
RUL=os.path.join(REG,"RULINGS.tsv"); ERR=os.path.join(REG,"s4r9/ERRATA_9.txt")
ST=os.path.join(REPO,"checkpoints/p05/STATE.md")
BRIEF=os.path.join(REPO,"checkpoints/p05/briefs/P05_S5R1_BRIEF.md")
PATCH=os.path.join(REPO,"checkpoints/p05/P05_S5_REGISTRY_PATCH_DRAFT.md")
PLAN=os.path.join(REPO,"checkpoints/p05/P05_S5_PLAN_DRAFT.md")
STAGE=os.path.join(REPO,"testing/d003/stage_s5r1")
BASE="59e742d5b918b9c194f3aec10148801f7839f263"
TAB=chr(9); NL=chr(10)
TS=re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\t")
OUT=sys.argv[1]; shake=False; commit_i_override=None
i=2
while i<len(sys.argv):
 if sys.argv[i]=="--shakedown": shake=True; i+=1
 elif sys.argv[i]=="--commit-i" and i+1<len(sys.argv): commit_i_override=sys.argv[i+1]; i+=2
 else: i+=1
OUTDIR=os.path.dirname(OUT)
REPORT=os.path.join(SHK,"REPORT.proposed.md") if shake else os.path.join(REPO,"checkpoints/p05/P05_S5R1_REPORT.md")
REGDIR=os.path.join(SHK,"registries_copy") if shake else os.path.join(REG,"s5r1")
RCK=os.path.join(SHK,"REPORT_CHECK_S5R1.txt") if shake else os.path.join(EV,"REPORT_CHECK_S5R1.txt")
EVF=os.path.join(SHK,"EVENTS_S5R1.tsv") if shake else os.path.join(EV,"EVENTS_S5R1.tsv")
SUMS=os.path.join(SHK,"SHA256SUMS.txt") if shake else os.path.join(EV,"SHA256SUMS.txt")
FROZEN=os.path.join(SHK,"FROZEN_SCRIPTS_S5R1.tsv") if shake else os.path.join(EV,"FROZEN_SCRIPTS_S5R1.tsv")
OUTDECL=os.path.join(SHK,"REGISTRY_OUTPUTS_S5R1.tsv") if shake else os.path.join(EV,"REGISTRY_OUTPUTS_S5R1.tsv")
SUMSROOT=SHK if shake else EV
res=[]; recs=[]
def ck(n,ok,exp,act): res.append(("PASS" if ok else "FAIL",n,str(exp),str(act)))
def rec(n,v): recs.append((n,str(v)))
def safe(n,fn,exp):
 try:
  ok,act=fn(); ck(n,ok,exp,act)
 except Exception as e: ck(n,False,exp,"CHECK_CRASHED: %s: %s"%(type(e).__name__,e))
def sh(a): return subprocess.check_output(a,cwd=REPO,text=True,stderr=subprocess.STDOUT).strip()
def shb(a): return subprocess.check_output(a,cwd=REPO,stderr=subprocess.DEVNULL)
def sha_b(b): return hashlib.sha256(b).hexdigest()
def sha_f(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(65536),b""): h.update(b)
 return h.hexdigest()
def rd(p): return open(p,encoding="utf-8",errors="replace").read()
def read_sums(p):
 out=[]
 for line in rd(p).splitlines():
  line=line.strip()
  if not line or line.startswith("#"): continue
  a,n=line.split(None,1); out.append((a,n.strip()))
 return out
def sums_dir(d):
 sp=os.path.join(d,"SHA256SUMS.txt")
 if not os.path.isfile(sp): return False,0,"missing sums"
 n=0
 for a,name in read_sums(sp):
  fp=os.path.join(d,name)
  if not os.path.isfile(fp) or sha_f(fp)!=a: return False,n,"mismatch "+name
  n+=1
 return True,n,"all %d OK"%n
def tmp_snap():
 root=os.sep+"tmp"; e=sorted(os.listdir(root)) if os.path.isdir(root) else []
 return len(e),sha_b(("\n".join(e)+("\n" if e else "")).encode("utf-8"))
def start_records():
 p=os.path.join(EV,"GATE_S5R1_start.txt"); rec={}
 if not os.path.isfile(p): return rec
 for line in rd(p).splitlines():
  f=line.rstrip(NL).split(TAB)
  if len(f)>=3 and f[0]=="RECORD":
   v=f[2]
   if v.startswith("value="): v=v[6:]
   rec[f[1]]=v
 return rec
def log_recs():
 p=os.path.join(EV,"safe_run.log"); out=[]
 if not os.path.isfile(p): return out
 for idx,line in enumerate(rd(p).splitlines(),1):
  m=TS.match(line)
  if not m: continue
  cmd=""
  for part in line.rstrip(NL).split(TAB)[1:]:
   if part.startswith("cmd="): cmd=part[4:]; break
  out.append((idx,m.group(1),cmd))
 return out
def epoch(ts):
 try: return int(datetime.datetime.strptime(ts,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp())
 except Exception: return 0
def frozen_rows():
 p=FROZEN
 if not os.path.isfile(p): return [],None
 header=None; rows=[]
 for line in rd(p).splitlines():
  if not line.strip() or line.startswith("#"): continue
  f=line.rstrip(NL).split(TAB)
  if header is None:
   header=f
   for c in ("path","sha256","expected_calls","mode"):
    if c not in header: raise SystemExit("FROZEN_HEADER_MISSING_COLUMN "+c)
   continue
  d=dict(zip(header,f)); rows.append(d)
 return rows,header
def parse_report_items():
 if not os.path.isfile(REPORT): return []
 insec=False; items=[]
 for line in rd(REPORT).splitlines():
  if line.strip()=="## 9 交付物": insec=True; continue
  if insec and line.startswith("## "): break
  if insec:
   m=re.match(r"^\s*(\d+)\.\s+(.+?)\s*$",line)
   if m: items.append(m.group(2).strip())
 return items

frozen,header=frozen_rows()
rec("FROZEN_COLUMNS",",".join(header) if header else "MISSING")
safe("BRANCH_IS_EXPECTED",lambda:(sh(["git","branch","--show-current"])=="codex/p05-d003-fft-error-propagation",sh(["git","branch","--show-current"])),"codex/p05-d003-fft-error-propagation")
start=start_records()
safe("START_RECORDS_PRESENT",lambda:(len(start)>0,"%d records"%len(start) if start else "missing"),"records present")
def c_s4():
 t=sh(["git","rev-parse","HEAD:S4"]); return t=="589e15eb11fcb04e031b524f25a443e7921946cf",t
safe("HEAD_S4_TREE_EQ_F4",c_s4,"589e15eb11fcb04e031b524f25a443e7921946cf")
def c_judge():
 a=sha_f(os.path.join(REPO,"testing/d003/judge_d003.py")); return a=="d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb",a
safe("JUDGE_SHA256",c_judge,"d2d04145...09eb")
def c_s4zero():
 d=sh(["git","diff","HEAD","--","S4"]); return d=="",("S4 unmodified" if not d else d[:120])
safe("S4_DIR_ZERO_MODIFICATION",c_s4zero,"S4 unmodified")
ALLOW_M={"checkpoints/p05/STATE.md","checkpoints/p05/registries/s4r9/ERRATA_9.txt"}
def c_base():
 lines=[l for l in sh(["git","diff","--name-status",BASE]).splitlines() if l.strip()]
 mods=[l.split(TAB)[1] for l in lines if l.startswith("M"+TAB)]
 dels=[l.split(TAB)[1] for l in lines if l.startswith("D"+TAB)]
 add=sum(1 for l in lines if l.startswith("A"+TAB))
 badm=[x for x in mods if x not in ALLOW_M]
 rec("BASE_DIFF_A",add); rec("BASE_DIFF_M",len(mods)); rec("BASE_DIFF_D",len(dels))
 return (not badm) and (not dels),("A=%d M=%d D=%d badM=%s badD=%s"%(add,len(mods),len(dels),badm[:4],dels[:4]))
safe("BASE_COMMITTED_ONLY_ALLOWED_MD",c_base,"only allowed M/D; new A allowed")
def c_tracked():
 d=[x for x in sh(["git","diff","--name-only","HEAD"]).splitlines() if x.strip()]
 bad=[x for x in d if x not in ALLOW_M]
 return not bad,("none" if not bad else str(bad[:6]))
safe("TRACKED_MODIFIED_WITHIN_END_ALLOW_LIST",c_tracked,"none")
rb=open(RUL,"rb").read(); eb=open(ERR,"rb").read()
rs=start.get("RULINGS_SHA256",""); rbn=int(start.get("RULINGS_BYTES","0") or 0)
es=start.get("ERRATA_9_SHA256",""); ebn=int(start.get("ERRATA_9_BYTES","0") or 0)
safe("RULINGS_UNCHANGED_FROM_START",lambda:(sha_b(rb)==rs,sha_b(rb)),rs)
safe("ERRATA_PREFIX_OF_START_UNCHANGED",lambda:(sha_b(eb[:ebn])==es,sha_b(eb[:ebn])),es)
safe("ERRATA_NOT_TRUNCATED",lambda:(len(eb)>=ebn,len(eb)),">= %d"%ebn)
def c_rul_max():
 lines=[l for l in rb.decode("utf-8","replace").splitlines() if l.strip() and not l.strip().startswith("#")]
 ids={}
 for l in lines:
  f=l.split(TAB)
  if len(f)!=5: return False,"bad fields: "+l[:40]
  if f[0] in ids: return False,"dup "+f[0]
  ids[f[0]]=f
 ns=[int(k[1:]) for k in ids if re.match(r"^U\d+$",k)]
 rec("RULINGS_MAX_U_END","U%d"%max(ns)); rec("RULINGS_BYTES_END",len(rb))
 return max(ns)==363,"U%d"%max(ns)
safe("RULINGS_MAX_U363_END",c_rul_max,"U363")
def c_err():
 t=eb.decode("utf-8","replace"); ids=re.findall(r"(?m)^(E9-\d+)",t)
 rec("ERRATA_9_COUNT_END",len(ids)); rec("ERRATA_9_BYTES_END",len(eb))
 need=["E9-78","E9-79"]
 return (ids and ids[-1]=="E9-79" and len(ids)==79 and all(x in ids for x in need)),("%s count=%d"%(ids[-1] if ids else "none",len(ids)))
safe("ERRATA_END_LAST_E9_79_COUNT_79",c_err,"E9-79 count=79")
def c_err_append():
 b0=shb(["git","show",BASE+":checkpoints/p05/registries/s4r9/ERRATA_9.txt"])
 return eb.startswith(b0) and len(eb)>len(b0),"prefix=%s delta=%d"%(eb.startswith(b0),len(eb)-len(b0))
safe("ERRATA_BASE_PREFIX_PLUS_APPEND_ONLY",c_err_append,"BASE content is prefix and file grew")
def c_rul_prefix():
 b0=shb(["git","show",BASE+":checkpoints/p05/registries/RULINGS.tsv"])
 return rb==b0,"equal" if rb==b0 else "delta=%d"%len(rb)-len(b0)
safe("RULINGS_BASE_PREFIX_UNCHANGED",c_rul_prefix,"BASE content unchanged")
sb=open(ST,"rb").read()
safe("STATE_BYTES_LE_8192",lambda:(0<len(sb)<=8192,len(sb)),"<= 8192")
def c_state():
 t=sb.decode("utf-8","replace")
 keys=["P05-S5 R1","S5 进行中","S5_TRIAGE_S5R1.tsv","已由用户签收","P05_S5_PLAN_DRAFT.md"]
 miss=[k for k in keys if k not in t]
 return not miss,("all markers" if not miss else str(miss))
safe("STATE_MARKERS",c_state,"state markers present")
def c_brief():
 if not os.path.isfile(BRIEF): return False,"missing"
 t=rd(BRIEF); return (len(t.encode())>1000 and "P05-S5 R1" in t and "checkpoints/p05/briefs/P05_S5R1_BRIEF.md" in t),"bytes=%d"%len(t.encode())
safe("BRIEF_PRESENT",c_brief,"brief present with markers")
def c_drafts():
 miss=[]
 if not os.path.isfile(PATCH): miss.append("PATCH")
 else:
  t=rd(PATCH)
  for k in ["P05_S5_REGISTRY_PATCH_DRAFT","D016","R-P05-02","unified diff"]:
   if k not in t: miss.append("PATCH:"+k)
 if not os.path.isfile(PLAN): miss.append("PLAN")
 else:
  t=rd(PLAN)
  for k in ["Q1","PREREG_S5R2","P05_S5_PLAN_DRAFT"]:
   if k not in t: miss.append("PLAN:"+k)
 return not miss,("both present" if not miss else str(miss))
safe("DRAFTS_PRESENT",c_drafts,"both drafts with markers")
safe("FROZEN_LIST_PRESENT",lambda:(len(frozen)>0,"%d rows"%len(frozen)),"rows")
def c_frozen_cov():
 stage=set("testing/d003/stage_s5r1/"+f for f in os.listdir(STAGE) if (("s5r1" in f) or f.startswith("gate_s5r1")) and (f.endswith(".py") or f.endswith(".sh")))
 fz=set(r.get("path","") for r in frozen if "/stage_s5r1/" in r.get("path",""))
 return stage==fz,("equal" if stage==fz else "stage-only=%s frozen-only=%s"%(sorted(stage-fz),sorted(fz-stage)))
safe("FROZEN_COVERS_ROUND_SCRIPTS",c_frozen_cov,"frozen == round scripts")
def c_frozen_sha():
 bad=[]
 for r in frozen:
  fp=os.path.join(REPO,r["path"])
  if not os.path.isfile(fp) or sha_f(fp)!=r["sha256"]: bad.append(r["path"])
 return not bad,("all %d OK"%len(frozen) if not bad else str(bad[:4]))
safe("FROZEN_SCRIPTS_SHA_UNCHANGED_END",c_frozen_sha,"all frozen OK")
commit_i=""
if shake:
 commit_i=commit_i_override or ""
 safe("SHAKEDOWN_SIMULATED_COMMIT_I",lambda:(commit_i.startswith("sim:line"),commit_i or "missing"),"sim:lineN")
 try: anchor=int(commit_i.split("sim:line",1)[1])
 except Exception: anchor=0
else:
 if not commit_i:
  try: commit_i=sh(["git","log","--grep=P05-S5 R1 (i)","-1","--format=%H"])
  except Exception: commit_i=""
 safe("COMMIT_I_PRESENT",lambda:(bool(commit_i),commit_i or "missing"),"commit (i) found")
rec("COMMIT_I_SHA",commit_i)
recs_all=log_recs(); rec("LOG_RECORDS",len(recs_all))
if shake:
 post=[r for r in recs_all if r[0]>anchor]
 rec("POST_I_LOG_RECORDS",len(post))
else:
 ci_epoch=0
 if commit_i:
  try: ci_epoch=int(sh(["git","log","-1","--format=%ct",commit_i]))
  except Exception: ci_epoch=0
 rec("COMMIT_I_EPOCH",ci_epoch)
 post=[r for r in recs_all if epoch(r[1])>=ci_epoch]
 rec("POST_I_LOG_RECORDS",len(post))
def is_call(cmd,rel,mode):
 toks=cmd.split()
 if not (toks and toks[0] in ("python3","sh","bash")): return False
 if rel not in cmd: return False
 if mode and mode!="-": return mode in toks
 return True
def count_calls(rel,mode):
 return [x for (x,ts,cmd) in post if is_call(cmd,rel,mode)]
for r in frozen:
 if r.get("expected_calls","0")=="0": continue
 key=os.path.basename(r["path"]).replace(".py","").replace(".sh","").upper()+"_"+r.get("mode","-").upper()
 def mkc(rr=r,kk=key):
  hits=count_calls(rr["path"],rr["mode"]); rec("CALL_LINES_"+kk,",".join(str(h) for h in hits))
  return len(hits)==int(rr["expected_calls"]),"%d"%len(hits)
 safe("POST_I_CALL_COUNT_"+key,mkc,r.get("expected_calls"))
def c_no_d003():
 bad=[]
 for (x,ts,cmd) in post:
  if ("open('testing/d003/" in cmd) or ('open("testing/d003/' in cmd) or re.search(r">\s*testing/d003/",cmd): bad.append((x,cmd[:60]))
 return not bad,(0 if not bad else str(bad[:3]))
safe("POST_I_NO_TESTING_D003_WRITES",c_no_d003,0)
def c_events():
 if not os.path.isfile(EVF): return False,"missing EVENTS"
 ev_lines=[x for (x,ts,cmd) in post if "s5r1_chain.py events" in cmd]
 if not ev_lines: return False,"no events call after (i)"
 anch=max(ev_lines); rec("EVENTS_ANCHOR_LINE",anch)
 rows={}
 for line in rd(EVF).splitlines():
  if not line.strip() or line.startswith("#") or line.startswith("log_line"+TAB): continue
  f=line.rstrip(NL).split(TAB)
  if len(f)>=2 and f[0].isdigit(): rows[int(f[0])]=f[1]
 raw=rd(os.path.join(EV,"safe_run.log")).splitlines()
 ts_of={x:ts for (x,ts,cmd) in recs_all}
 expect={}; parent=""
 for x in range(1,anch+1):
  if x>len(raw) or not raw[x-1].strip(): continue
  if x in ts_of: parent=ts_of[x]
  expect[x]=parent
 if set(rows)!=set(expect):
  return False,"row set differs missing=%s extra=%s"%(sorted(set(expect)-set(rows))[:4],sorted(set(rows)-set(expect))[:4])
 diff=[x for x in expect if rows[x]!=expect[x]]
 rec("EVENTS_ROWS",len(rows))
 return not diff,("rows=%d anchor=%d all match"%(len(rows),anch) if not diff else str(diff[:4]))
safe("EVENTS_ROW_SET_EQ_RECOMPUTATION",c_events,"row set equals recomputation")
def c_rc():
 if not os.path.isfile(RCK): return False,"missing REPORT_CHECK"
 fails=None
 for line in rd(RCK).splitlines():
  if line.startswith("FAILS="): fails=int(line.strip().split("=")[1])
 return fails==0,"FAILS=%s"%fails
safe("REPORT_CHECK_FAILS_ZERO",c_rc,"FAILS=0")
def c_reg():
 ok,cnt,det=sums_dir(REGDIR)
 if not ok: return False,det
 items=parse_report_items(); rec("REGISTRY_S5R1_ITEMS",cnt); rec("REPORT_DELIVERABLES",len(items))
 if not items: return False,"no report items"
 if cnt!=len(items)-1: return False,"sums %d != items-1 %d"%(cnt,len(items)-1)
 if items[-1]!="SHA256SUMS.txt": return False,"last item not SHA256SUMS.txt"
 return True,"%s; report items=%d"%(det,len(items))
safe("REGISTRIES_S5R1_SUMS_ALL_OK_AND_REPORT_ITEMS",c_reg,"all OK matching report")
def c_sums():
 if not os.path.isfile(SUMS): return False,"missing sums"
 lines=rd(SUMS).splitlines()
 if len(lines)<2: return False,"too short"
 m=re.search(r"up to line (\d+):\s*([0-9a-f]{64})",lines[1])
 if not m: return False,"no trunc header: "+lines[1][:60]
 trunc_line,trunc_sha=int(m.group(1)),m.group(2)
 ss=[x for (x,ts,cmd) in post if "s5r1_chain.py sha_sums" in cmd]
 if not ss: return False,"no sha_sums call after (i)"
 anchor=max(ss); rec("SHA_SUMS_ANCHOR_LINE",anchor)
 if trunc_line!=anchor: return False,"trunc %d != anchor %d"%(trunc_line,anchor)
 log_text=NL.join(rd(os.path.join(EV,"safe_run.log")).splitlines()[:trunc_line])+NL
 if sha_b(log_text.encode("utf-8"))!=trunc_sha: return False,"log hash mismatch"
 ok,cnt,det=sums_dir(SUMSROOT); rec("EVIDENCE_SUMS_ITEMS",cnt)
 return ok,"trunc line %d; %s"%(trunc_line,det)
safe("EVIDENCE_SHA256SUMS_OK",c_sums,"all OK")
def c_cov():
 listed=set(n for a,n in read_sums(SUMS))
 root_abs=os.path.abspath(SUMSROOT); out_abs=os.path.abspath(SUMS); gate=os.path.join(root_abs,"gate")
 miss=[]
 for r_,dirs,files in os.walk(SUMSROOT):
  dirs[:]=sorted(d for d in dirs if d!="tmp")
  for f in sorted(files):
   fp=os.path.abspath(os.path.join(r_,f))
   if fp==out_abs or fp.startswith(gate+os.sep): continue
   if f in ("safe_run.log","SHA256SUMS.txt"): continue
   rel=os.path.relpath(fp,root_abs)
   if rel not in listed: miss.append(rel)
 return not miss,("all %d covered"%len(listed) if not miss else str(miss[:6]))
safe("EVIDENCE_SUMS_COVERS_ALL",c_cov,"manifest covers every non-gate file")
def c_nowrite():
 sm=os.path.getmtime(SUMS); root_abs=os.path.abspath(SUMSROOT)
 gate=os.path.join(root_abs,"gate"); tmpd=os.path.join(root_abs,"tmp")
 out_abs=os.path.join(root_abs,"SHA256SUMS.txt"); bad=[]
 for r_,dirs,files in os.walk(SUMSROOT):
  for f in files:
   fp=os.path.abspath(os.path.join(r_,f))
   if fp==out_abs or fp.startswith(gate+os.sep) or fp.startswith(tmpd+os.sep): continue
   if f=="safe_run.log": continue
   if os.path.getmtime(fp)>sm+0.5: bad.append(os.path.relpath(fp,root_abs))
 return not bad,("no $EV write after sha_sums" if not bad else str(sorted(bad)[:6]))
safe("EV_NO_WRITE_AFTER_SHA_SUMS",c_nowrite,"sha_sums last $EV write")
def c_unlogged():
 sep=epoch(start.get("START_TIME_UTC","")) if start.get("START_TIME_UTC") else 0
 logtxt=rd(os.path.join(EV,"safe_run.log")) if os.path.isfile(os.path.join(EV,"safe_run.log")) else ""
 decl=set()
 if os.path.isfile(OUTDECL):
  for line in rd(OUTDECL).splitlines():
   if line.strip() and not line.startswith("#"): decl.add(line.strip())
 decl.update([os.path.relpath(ST,REPO),os.path.relpath(ERR,REPO),os.path.relpath(RUL,REPO),os.path.relpath(BRIEF,REPO),os.path.relpath(PATCH,REPO),os.path.relpath(PLAN,REPO),os.path.relpath(REPORT,REPO)])
 bad=[]
 targets=[os.path.join(REPO,"checkpoints","p05"),STAGE]
 for target in targets:
  for r_,dirs,files in os.walk(target):
   if "evidence" in r_.split(os.sep): continue
   for f in files:
    fp=os.path.join(r_,f); rel=os.path.relpath(fp,REPO)
    if sep and int(os.path.getmtime(fp))>=sep:
     if rel in decl: continue
     if rel in logtxt or os.path.basename(rel) in logtxt: continue
     bad.append(rel)
 rec("UNLOGGED_SELF",len(bad)); rec("DECLARED_OUTPUTS",len(decl))
 return not bad,(0 if not bad else str(bad[:8]))
safe("UNLOGGED_SELF_ZERO",c_unlogged,0)
def c_other():
 sep=epoch(start.get("START_TIME_UTC","")) if start.get("START_TIME_UTC") else 0
 bad=[]
 for r_ in ("m0","m1","m1r2","m1r3","m1r4","m2","m2b","m2c","m3a","m3b","m3c","m3d","m3e"):
  p=os.path.join(REPO,"checkpoints/p05/evidence/p05-s4r9",r_)
  if not os.path.isdir(p): continue
  for root2,dirs2,files2 in os.walk(p):
   for f in files2:
    fp=os.path.join(root2,f)
    if sep and int(os.path.getmtime(fp))>sep: bad.append(os.path.relpath(fp,REPO))
 return not bad,("none" if not bad else str(bad[:6]))
safe("OTHER_ROUND_EVIDENCE_UNTOUCHED",c_other,"none")
def c_rootreg():
 e=os.path.exists(os.path.join(REPO,"registries")); return not e,("absent" if not e else "EXISTS")
safe("ROOT_REGISTRIES_ABSENT",c_rootreg,"absent")
tc,ts=tmp_snap(); rec("TMP_COUNT_END",tc); rec("TMP_SHA256_END",ts); rec("TMP_COUNT_START",start.get("TMP_COUNT","?"))
safe("TMP_SNAPSHOT_RECORDED",lambda:(tc>=0,"count=%d sha=%s"%(tc,ts)),"recorded")
def c_audit():
 files=[f for f in os.listdir(STAGE) if (("s5r1" in f) or f.startswith("gate_s5r1")) and (f.endswith(".py") or f.endswith(".sh"))]
 bad=[f for f in files if re.search(r"_v[0-9]+\.(py|sh)$",f)]
 foreign=[f for f in files if re.search(r"r9m3|s4r9",f)]
 return (not bad and not foreign),("%d s5r1 files; nonfinal=%s foreign=%s"%(len(files),bad,foreign))
safe("SCRIPT_NAME_AUDIT",c_audit,"no non-final/foreign s5r1 names")
def c_tables():
 miss=[]
 for n in ("S5_INPUTS_S5R1.tsv","S5_INPUTS_DEDUP_S5R1.txt","S5_TRIAGE_S5R1.tsv","P05_ACCEPTANCE_MAP_S5R1.tsv"):
  p=os.path.join(EV,n)
  if not os.path.isfile(p): miss.append(n)
 if miss: return False,str(miss)
 inv=[l for l in rd(os.path.join(EV,"S5_INPUTS_S5R1.tsv")).splitlines() if l.strip() and not l.startswith("#")]
 tri=[l for l in rd(os.path.join(EV,"S5_TRIAGE_S5R1.tsv")).splitlines() if l.strip() and not l.startswith("#")]
 return (len(inv)-1==25 and len(tri)-1==25),"inventory=%d triage=%d"%(len(inv)-1,len(tri)-1)
safe("S5_TABLES_PRESENT_25_ROWS",c_tables,"inventory=25 triage=25")
crashes=sum(1 for s,n,e,a in res if "CHECK_CRASHED" in a)
ck("CHECK_CRASHED_ZERO",crashes==0,0,crashes)
rec("CHECK_CRASHED_COUNT",crashes)
now=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
lines=["# P05-S5 R1 end gate "+os.path.basename(OUT)+" ("+now+")"]
lines+=["RECORD"+TAB+k+TAB+"value="+v for k,v in recs]
lines+=["%s\t%s\texpected=%s\tactual=%s"%(s,n,e,a) for s,n,e,a in res]
fails=sum(1 for r in res if r[0]=="FAIL")
lines.append("COUNTS\tpass=%d\tfail=%d\tskip=0\ttotal=%d"%(sum(1 for r in res if r[0]=="PASS"),fails,len(res)))
lines.append("FAILS=%d"%fails)
body=NL.join(lines)+NL
os.makedirs(OUTDIR,exist_ok=True)
open(OUT,"w",encoding="utf-8").write(body)
st2=sh(["git","status","--short","-uall"]); hd=sh(["git","rev-parse","HEAD"])
open(os.path.join(OUTDIR,"ALL_STATUS_S5R1_end.txt"),"w",encoding="utf-8").write(st2+NL+"HEAD"+TAB+hd+NL)
sys.exit(min(fails,255))
