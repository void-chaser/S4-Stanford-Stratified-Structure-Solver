#!/usr/bin/env python3
# apply_patch_s5r2.py -- apply the P05-S5 registry patch v2 (P05_S5_REGISTRY_PATCH_V2.md) to
# testing/s4test/ISSUE_REGISTRY.md and PROJECT_ROADMAP.md (U371). The machine-readable PATCHSPEC
# block in the v2 file is authoritative. Before touching a file the script asserts its start
# sha256 from GATE_S5R2_start.txt; after applying it writes a unified diff, asserts that exactly
# the listed lines changed, and refuses forbidden completion/takeover wording.
#   --dry-run : write candidates + diff under $EV/shakedown (never touch the real files)
import os,sys,re,hashlib,base64,difflib,subprocess
REPO=subprocess.check_output(["git","rev-parse","--show-toplevel"],text=True).strip()
P05=os.path.join(REPO,"checkpoints/p05")
EV=os.path.join(P05,"evidence/p05-s5r2")
SHK=os.path.join(EV,"shakedown")
TAB=chr(9); NL=chr(10)
SPECF=os.path.join(P05,"P05_S5_REGISTRY_PATCH_V2.md")
FILES=["testing/s4test/ISSUE_REGISTRY.md","PROJECT_ROADMAP.md"]
FORB=["P05 完成","P05-S5 已签收","P05 已完成","P05-S5 已完成","P05-S6"]
DRY="--dry-run" in sys.argv
def sha_b(b): return hashlib.sha256(b).hexdigest()
def rdb(p): return open(p,"rb").read()
def rd(p): return open(p,encoding="utf-8").read()
def check_prefix(p):
 rp=os.path.realpath(p)
 base=os.path.join(REPO,"checkpoints/p05")+os.sep
 ok=rp.startswith(base) or rp.startswith(os.path.join(REPO,"testing/d003")+os.sep) or rp.startswith(os.path.join(REPO,"testing/s4test")+os.sep) or rp==os.path.join(REPO,"PROJECT_ROADMAP.md")
 if not ok: raise SystemExit("PATH_OUTSIDE_ALLOWED_PREFIX "+rp)
def wr(p,t):
 check_prefix(p); os.makedirs(os.path.dirname(p),exist_ok=True)
 open(p,"w",encoding="utf-8").write(t)
def start_records():
 p=os.path.join(EV,"GATE_S5R2_start.txt"); rec={}
 if not os.path.isfile(p): raise SystemExit("START_GATE_MISSING")
 for line in rd(p).splitlines():
  f=line.split(TAB)
  if len(f)>=3 and f[0]=="RECORD":
   v=f[2]; v=v[6:] if v.startswith("value=") else v
   rec[f[1]]=v
 return rec
def parse_spec():
 if not os.path.isfile(SPECF): raise SystemExit("SPEC_MISSING "+SPECF)
 lines=rd(SPECF).splitlines()
 try:
  a=lines.index("<!-- PATCHSPEC-BEGIN -->"); b=lines.index("<!-- PATCHSPEC-END -->")
 except ValueError:
  raise SystemExit("SPEC_MARKERS_MISSING")
 ops=[]
 for line in lines[a+1:b]:
  if not line.strip(): continue
  f=line.split(TAB)
  if len(f)!=6: raise SystemExit("SPEC_BAD_FIELDS "+line[:80])
  tag,kind,rel,ln,ob,nb=f
  if tag!="OP": raise SystemExit("SPEC_BAD_TAG "+tag)
  if kind not in ("REPLACE","INSERT_AFTER"): raise SystemExit("SPEC_BAD_KIND "+kind)
  if rel not in FILES: raise SystemExit("SPEC_BAD_FILE "+rel)
  old=base64.b64decode(ob).decode("utf-8") if kind=="REPLACE" else None
  new=base64.b64decode(nb).decode("utf-8")
  ops.append((kind,rel,int(ln),old,new))
 if not ops: raise SystemExit("SPEC_EMPTY")
 return ops
def build(rel,ops,orig):
 per={}
 for kind,r,ln,old,new in ops:
  if r!=rel: continue
  per.setdefault((kind,ln),[]).append((old,new))
 out=[]; replaced=[]
 for i,l in enumerate(orig,1):
  rl=per.get(("REPLACE",i))
  if rl:
   if len(rl)!=1: raise SystemExit("DUPLICATE_REPLACE %s:%d"%(rel,i))
   old,new=rl[0]
   if l!=old: raise SystemExit("OLD_LINE_MISMATCH %s:%d\n%r\n%r"%(rel,i,l,old))
   out.append(new); replaced.append(i)
  else:
   out.append(l)
  for old,new in per.get(("INSERT_AFTER",i),[]): out.append(new)
 nrep=sum(1 for k,r,ln,o,n in ops if r==rel and k=="REPLACE")
 nins=sum(1 for k,r,ln,o,n in ops if r==rel and k=="INSERT_AFTER")
 if len(replaced)!=nrep: raise SystemExit("REPLACE_COUNT_MISMATCH %s %d %d"%(rel,len(replaced),nrep))
 return out,replaced,nins
def main():
 ops=parse_spec(); rec=start_records()
 start_sha={}
 for rel in FILES:
  opath=os.path.join(REPO,rel)
  if not os.path.isfile(opath): raise SystemExit("TARGET_MISSING "+rel)
  cur=rdb(opath); cur_sha=sha_b(cur)
  key="ISSUE_REGISTRY_SHA256" if rel==FILES[0] else "ROADMAP_SHA256"
  exp=rec.get(key,"")
  if not exp: raise SystemExit("START_SHA_RECORD_MISSING "+key)
  if cur_sha!=exp: raise SystemExit("START_SHA_MISMATCH %s %s != %s"%(rel,cur_sha,exp))
  start_sha[rel]=cur_sha
 if not DRY and "| D017 /" in rd(os.path.join(REPO,FILES[0])):
  raise SystemExit("ALREADY_APPLIED")
 head=["# REGISTRY_APPLY_DIFF_S5R2.txt -- unified diff of the P05-S5 registry patch v2 (U371)",
       "# generator: apply_patch_s5r2.py; dry_run=%s"%DRY,
       "# start sha256 (asserted against GATE_S5R2_start.txt):"]
 for rel in FILES: head.append("#   %s %s"%(rel,start_sha[rel]))
 head.append("# after sha256 applied bytes:")
 results=[]; diffs=[]
 for rel in FILES:
  opath=os.path.join(REPO,rel)
  orig=rd(opath).splitlines()
  new,replaced,nins=build(rel,ops,orig)
  for w in FORB:
   for l in new:
    if w in l and not (w=="P05 完成" and ("不" in l or "未" in l)):
     raise SystemExit("FORBIDDEN_TOKEN %s %s"%(w,l[:60]))
  body=NL.join(new)+NL
  if DRY:
   dst=os.path.join(SHK,"ISSUE_REGISTRY.candidate.md" if rel==FILES[0] else "ROADMAP.candidate.md")
  else:
   dst=opath
  wr(dst,body)
  back=rd(dst)
  if back!=body: raise SystemExit("READBACK_MISMATCH "+rel)
  results.append((rel,replaced,nins,len(body.encode()),sha_b(body.encode())))
  diffs.append((rel,list(difflib.unified_diff(orig,new,fromfile="a/"+rel,tofile="b/"+rel,lineterm=""))))
 for rel,replaced,nins,nbytes,nsha in results:
  head.append("#   %s replaced_lines=%s inserted=%d after_bytes=%d after_sha256=%s"%(rel,",".join(str(x) for x in replaced),nins,nbytes,nsha))
 out=head[:]
 for rel,d in diffs:
  out.append("")
  out.append("### "+rel)
  out+=d
 out.append("")
 out.append("# ASSERT_ONLY_LISTED_LINES_CHANGED: PASS")
 out.append("# ASSERT_FORBIDDEN_TOKENS_ABSENT: PASS")
 txt=NL.join(out)+NL
 outpath=os.path.join(SHK if DRY else EV,"REGISTRY_APPLY_DIFF_S5R2.txt")
 wr(outpath,txt)
 print("APPLY dry_run=%s files=%d diff_bytes=%d"%(DRY,len(results),len(txt.encode())))
 for rel,replaced,nins,nbytes,nsha in results:
  print("APPLY %s replaced=%s inserted=%d after_sha256=%s"%(rel,",".join(str(x) for x in replaced),nins,nsha))
 print("WROTE "+os.path.relpath(outpath,REPO))
 return 0
if __name__=="__main__": sys.exit(main())
