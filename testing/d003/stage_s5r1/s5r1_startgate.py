#!/usr/bin/env python3
# s5r1_startgate.py -- P05-S5 R1 start gate. Writes $EV/GATE_S5R1_start.txt.
import os,sys,re,hashlib,subprocess,datetime
REPO=os.getcwd()
EV=os.path.join(REPO,"checkpoints/p05/evidence/p05-s5r1")
REG=os.path.join(REPO,"checkpoints/p05/registries")
TAB=chr(9); NL=chr(10)
HEAD_EXPECT="59e742d5b918b9c194f3aec10148801f7839f263"
S4_EXPECT="589e15eb11fcb04e031b524f25a443e7921946cf"
JUDGE_EXPECT="d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
BRANCH_EXPECT="codex/p05-d003-fft-error-propagation"
res=[]; recs=[]
def ck(n,ok,exp,act): res.append(("PASS" if ok else "FAIL",n,str(exp),str(act)))
def rec(n,v): recs.append((n,str(v)))
def safe(n,fn,exp):
 try:
  ok,act=fn(); ck(n,ok,exp,act)
 except Exception as e: ck(n,False,exp,"CHECK_CRASHED: %s: %s"%(type(e).__name__,e))
def sh(a): return subprocess.check_output(a,cwd=REPO,text=True,stderr=subprocess.STDOUT).strip()
def sha_b(b): return hashlib.sha256(b).hexdigest()
def sha_f(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(65536),b""): h.update(b)
 return h.hexdigest()
def read_sums(p):
 out=[]
 for line in open(p,encoding="utf-8"):
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
def spec(label,path,nb,sha16):
 def f():
  b=open(path,"rb").read()
  a=sha_b(b); rec(label+"_BYTES",len(b)); rec(label+"_SHA256",a)
  return (len(b)==nb and a[:16]==sha16),"bytes=%d sha=%s"%(len(b),a[:16])
 return f
pre=sys.argv[1] if len(sys.argv)>1 else "unknown"
START=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
rec("START_TIME_UTC",START); rec("HEAD",HEAD_EXPECT)
safe("EV_ABSENT_BEFORE_START",lambda:(pre=="absent","precheck="+pre),"absent")
safe("BRANCH_IS_EXPECTED",lambda:(sh(["git","branch","--show-current"])==BRANCH_EXPECT,sh(["git","branch","--show-current"])),BRANCH_EXPECT)
safe("HEAD_IS_M3E_BASE",lambda:(sh(["git","rev-parse","HEAD"])==HEAD_EXPECT,sh(["git","rev-parse","HEAD"])),HEAD_EXPECT)
safe("HEAD_S4_TREE_EQ_F4",lambda:(sh(["git","rev-parse","HEAD:S4"])==S4_EXPECT,sh(["git","rev-parse","HEAD:S4"])),S4_EXPECT)
safe("JUDGE_SHA256",lambda:(sha_f(os.path.join(REPO,"testing/d003/judge_d003.py"))==JUDGE_EXPECT,JUDGE_EXPECT[:8]+"..."),JUDGE_EXPECT[:8]+"...")
def c_status():
 s=sh(["git","status","--short"]); return (s=="",("no changes" if not s else "%d lines"%len(s.splitlines()))),"no changes"
safe("GIT_STATUS_EMPTY",c_status,"no changes")
SP=[("RULINGS",os.path.join(REG,"RULINGS.tsv"),146978,"d33990ca2312eefc"),
    ("ERRATA_9",os.path.join(REG,"s4r9/ERRATA_9.txt"),65771,"5a07fc22fd796f92"),
    ("STATE",os.path.join(REPO,"checkpoints/p05/STATE.md"),5318,"dc4c1083bc69284b"),
    ("SIGNOFF_S3S4",os.path.join(REPO,"checkpoints/p05/P05_S3_S4_SIGNOFF.md"),2077,"7b5b412a9fa363ad"),
    ("SIGNOFF_S1S2",os.path.join(REPO,"checkpoints/p05/P05_S1_S2_SIGNOFF.md"),1636,"b6174b499884a593"),
    ("S5_HANDOFF",os.path.join(REG,"s4r9/M3d/S5_HANDOFF_R9M3D.tsv"),1401,"7adf17662bc47b94"),
    ("ISSUE_REGISTRY",os.path.join(REPO,"testing/s4test/ISSUE_REGISTRY.md"),20720,"ad17b768c79a3f63"),
    ("ROADMAP",os.path.join(REPO,"PROJECT_ROADMAP.md"),20905,"2c8cbe18d479584a")]
for label,path,nb,sha16 in SP:
 safe(label+"_START_BYTES_SHA16",spec(label,path,nb,sha16),"bytes=%d sha16=%s"%(nb,sha16))
def c_rul_max():
 t=open(os.path.join(REG,"RULINGS.tsv"),encoding="utf-8").read()
 ns=[int(m.group(1)) for m in re.finditer(r"(?m)^U(\d+)"+TAB,t)]
 rec("RULINGS_MAX_U_START","U%d"%max(ns))
 return max(ns)==363,"U%d"%max(ns)
safe("RULINGS_MAX_U363",c_rul_max,"U363")
def c_err():
 t=open(os.path.join(REG,"s4r9/ERRATA_9.txt"),encoding="utf-8").read()
 ids=re.findall(r"(?m)^(E9-\d+)",t); rec("ERRATA_9_COUNT",len(ids))
 return (ids and ids[-1]=="E9-77" and len(ids)==77),"last=%s count=%d"%(ids[-1] if ids else "none",len(ids))
safe("ERRATA_9_LAST_E9_77_COUNT_77",c_err,"E9-77 count=77")
def c_m3ereg():
 ok,n,det=sums_dir(os.path.join(REG,"s4r9/M3e")); rec("M3E_REG_ITEMS",n)
 return ok and n==4,"%s count=%d"%(det,n)
safe("M3E_REGISTRY_SUMS_ALL_OK",c_m3ereg,"all 4 OK")
def c_m3eev():
 ok,n,det=sums_dir(os.path.join(REPO,"checkpoints/p05/evidence/p05-s4r9/m3e")); rec("M3E_EV_ITEMS",n)
 return ok and n==23,"%s count=%d"%(det,n)
safe("M3E_EVIDENCE_SUMS_ALL_OK",c_m3eev,"all 23 OK")
def c_rootreg():
 e=os.path.exists(os.path.join(REPO,"registries")); return not e,("absent" if not e else "EXISTS")
safe("ROOT_REGISTRIES_ABSENT",c_rootreg,"absent")
def c_brief():
 e=os.path.exists(os.path.join(REPO,"checkpoints/p05/briefs/P05_S5R1_BRIEF.md")); return not e,("absent" if not e else "EXISTS")
safe("BRIEF_ABSENT_BEFORE_SAVE",c_brief,"absent")
def c_drafts():
 a=os.path.join(REPO,"checkpoints/p05/P05_S5_REGISTRY_PATCH_DRAFT.md")
 b=os.path.join(REPO,"checkpoints/p05/P05_S5_PLAN_DRAFT.md")
 e=os.path.exists(a) or os.path.exists(b)
 return not e,("absent" if not e else "EXISTS")
safe("DRAFTS_ABSENT_BEFORE_PREP",c_drafts,"absent")
tc,ts=tmp_snap(); rec("TMP_COUNT",tc); rec("TMP_SHA256",ts)
safe("TMP_SNAPSHOT_RECORDED",lambda:(tc>=0,"count=%d sha=%s"%(tc,ts)),"recorded")
crashes=sum(1 for s,n,e,a in res if "CHECK_CRASHED" in a)
ck("CHECK_CRASHED_ZERO",crashes==0,0,crashes)
lines=["# P05-S5 R1 start gate GATE_S5R1_start.txt ("+START+")"]
lines+=["RECORD"+TAB+k+TAB+"value="+v for k,v in recs]
lines+=["%s\t%s\texpected=%s\tactual=%s"%(s,n,e,a) for s,n,e,a in res]
fails=sum(1 for r in res if r[0]=="FAIL")
lines.append("COUNTS\tpass=%d\tfail=%d\tskip=0\ttotal=%d"%(sum(1 for r in res if r[0]=="PASS"),fails,len(res)))
lines.append("FAILS=%d"%fails)
os.makedirs(EV,exist_ok=True)
open(os.path.join(EV,"GATE_S5R1_start.txt"),"w",encoding="utf-8").write(NL.join(lines)+NL)
print(NL.join(lines)); print("CHECK_CRASHED=%d"%crashes)
sys.exit(min(fails,255))
