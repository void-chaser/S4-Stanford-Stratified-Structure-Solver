#!/usr/bin/env python3
# m3e_chain_r9m3e.py -- P05-S4 R9 M3e closeout chain. Subcommands in required order:
#   report | report_check | copy | events | progress | sha_sums.  Run once each in the frozen period.
import os,sys,re,hashlib,shutil,subprocess,datetime
REPO=os.getcwd()
EV=os.path.join(REPO,"checkpoints/p05/evidence/p05-s4r9/m3e")
SHK=os.path.join(EV,"shakedown")
REPORT=os.path.join(REPO,"checkpoints/p05/P05_S4R9_M3e_REPORT.md")
REGDIR=os.path.join(REPO,"checkpoints/p05/registries/s4r9/M3e")
TAB=chr(9); NL=chr(10); BT=chr(96)
def sha_b(b): return hashlib.sha256(b).hexdigest()
def sha_f(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(65536),b""): h.update(b)
 return h.hexdigest()
def sh(a): return subprocess.check_output(a,cwd=REPO,text=True,stderr=subprocess.STDOUT).strip()
def outdir(shake): return SHK if shake else EV
def log_path(): return os.path.join(EV,"safe_run.log")
def log_lines():
 if not os.path.isfile(log_path()): return []
 return open(log_path(),encoding="utf-8",errors="replace").read().splitlines()
TS=re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\t")
def anchor_line(needle):
 lines=log_lines()
 for x in range(len(lines),0,-1):
  if needle in lines[x-1]: return x
 return 0
def report_text(shake):
 g=sh(["git","log","-1","--format=%H %s"]); st=sh(["git","status","--short"]) or "(clean)"
 t=[]
 t.append("# P05-S4 R9 M3e 报告（r9m3e）")
 t.append("")
 t.append("> 轮次：P05-S4 R9 M3e。只读复核 + 文档写入；未运行 S4 的任何程序（无 make / make test / E2E / d003 矩阵 / gdb / 构建）。")
 t.append("")
 t.append("## 1 门禁")
 t.append("")
 t.append("- 0a 自检：签收块非空、无占位符、含“签收”二字；签收日期原文为【2026-10-18】，去掉全角括号后为 YYYY-MM-DD 格式的 2026-10-18。开工前 m3e 证据目录与 brief 均不存在（test -e 断言），/tmp 顶层 0 条目。")
 t.append("- start 门禁：34 项 PASS、0 FAIL（GATE_R9M3E_start.txt）。HEAD=37fbc0f2…c02bd；HEAD:S4=589e15e…46cf（F4）；判定器 sha256=d2d04145…09eb；RULINGS.tsv 145103 B / sha 21ab76d2… / 最大 U358；ERRATA_9.txt 62654 B / sha d71543bb… / 最后 E9-73；STATE.md 6636 B / sha 6eeb7559…。M3d 小表 11/11 OK；m3d 证据目录 39/39 OK；历史 13 份清单全部 OK，项数由脚本数出后断言：s3r5=14、M0=25、M1=28、M1R2=33、M1R3=26、M1R4=11、M2=14、M2b=13、M2c=11、M3a=17、M3b=18、M3c=13、M3d=11；仓库根 registries/ 不存在。")
 t.append("- end 门禁：见附录 B（冻结期正式单次运行；输出写 $EV/gate/，不纳入 SHA256SUMS）。")
 t.append("")
 t.append("## 2 裁决（U359–U363）")
 t.append("")
 t.append("| 编号 | 内容摘要 | 依据 |")
 t.append("|---|---|---|")
 t.append("| U359 | 用户签收 P05-S3、P05-S4；内容列逐字引用签收块原文 | 用户对话（2026-10-18） |")
 t.append("| U360 | ① M3d 修正版为签收前唯一现行版本（M3c 产物保留为历史） | 签收块 (b) |")
 t.append("| U361 | ② v1→v2 的 P-1…P-6 差异不逐条再确认 | 签收块 (b) |")
 t.append("| U362 | ③ U354、U356 维持 | 签收块 (c)(d)(f) |")
 t.append("| U363 | ④ 无台账 id 的 2 项（ES3R4-5/528/1164、U2 stage e）以 STATE 行对应 | 签收块 (f) |")
 t.append("")
 t.append("## 3 勘误（E9-74–E9-77）")
 t.append("")
 t.append("- E9-74：M3d end 门禁 M3C_AND_M3B_COMMITTED_FILES_UNCHANGED 的 FAIL 是检查器口径缺陷（把新增 A 文件算作改动）。复核 c4f6707..37fbc0f 的 name-status 计数、全部 M 文件、以及 RULINGS.tsv/ERRATA_9.txt 的纯追加性质，事实见 ERRATA_RECHECK_R9M3E.txt。")
 t.append("- E9-75：M3d copy_registries 的 DEST 多写一级 ..；复核仓库根 registries/ 不存在、M3d 清单 11/11 OK。")
 t.append("- E9-76：S5_HANDOFF_R9M3D.tsv 的 S5-M3D-06 source_ruling 应为 U5（E6-4，no-TWICE 路径不在范围内）；核对 RULINGS.tsv 的 U5 行与 registries/s4r6/ERRATA_6.txt 的 E6-4 原文；不改 M3d 文件，S5 开工以本勘误为准。")
 t.append("- E9-77：M3d 门禁检查器口径与路径问题由 M3e 写入纪律修正（§2 后两条），只登记，不重跑 M3d。")
 t.append("")
 t.append("## 4 签收文件摘要")
 t.append("")
 t.append("- 新建 P05_S3_S4_SIGNOFF.md：§1 S1/S2 维持原记录（2026-10-11），S3/S4 已由用户签收（2026-10-18），S5 未开始；§2 签收块原文逐字照录；§3 S5 接收 S5_HANDOFF_R9M3D.tsv 的 7 项（S5-M3D-06 按 E9-76 记 U5）；§4 执行者声明（依据用户授权写入、未自行宣布阶段完成；P05-S5 未开始、未签收）。")
 t.append("- 只读断言：签收文件 §2 与任务书 BEGIN/END 之间文本逐字相同（脚本比对 PASS；end 门禁独立复核）。")
 t.append("")
 t.append("## 5 事件两张表")
 t.append("")
 t.append("### 5.1 表一：越界写入尝试")
 t.append("")
 t.append("| # | 命令/脚本 | 目标 | 是否落盘 |")
 t.append("|---|---|---|---|")
 t.append("| 1 | 首次 start 门禁写校验脚本（命令经 bash -c 传入，内层 $REPO/$EV 被外层 shell 先展开） | /checkpoints/p05/evidence/p05-s4r9/m3e/tmp/start_gate_r9m3e.py（仓库外，路径不存在） | 否（mkdir/open 失败，rc 非零） |")
 t.append("| 2 | 首次 start 门禁执行命令 | mkdir -p /tmp；TMPDIR=/tmp；python3 /tmp/start_gate_r9m3e.py | 否（脚本不存在，未生成文件；/tmp 顶层保持 0 条目） |")
 t.append("| 3 | 清理尝试（python os.unlink(/tmp/start_gate_r9m3e.py)） | /tmp | 否（FileNotFoundError） |")
 t.append("")
 t.append("原因：命令以 bash -c 包一层传入 safe_run 时，内层 $REPO/$EV 在 safe_run 之外先被外层 shell 展开。改为 safe_run 直接传参（python3 -c / python3 -I -B）后不再发生；当前 /tmp 顶层 0 条目。")
 t.append("")
 t.append("### 5.2 表二：工具与脚本事件")
 t.append("")
 t.append("| # | 事件 | 影响 |")
 t.append("|---|---|---|")
 t.append("| 1 | 首次 start 门禁的两次 safe_run 调用被记为失败命令（safe_run.log 第 1–2 行） | 无仓库内写入；已在表一披露 |")
 t.append("| 2 | start 门禁校验脚本放在 $EV/tmp/（未提交，不纳入 FROZEN） | end 门禁只对 stage_s4r9 下 r9m3e 脚本做冻结校验 |")
 t.append("")
 t.append("其余：本轮无裸跑写入、无 heredoc 残留、无框架落盘（/tmp/dsh-spill-* 未出现）、无仓库内路径拼错。")
 t.append("")
 t.append("## 6 需用户裁决")
 t.append("")
 t.append("- 无新增需用户裁决项：签收块字面对 §3 的 ①–④ 均有明确表态，已分别登记 U360–U363。")
 t.append("- M3d 报告 §7 第 5 条（不宣布完成）由本轮签收文件 §4 与本报告 §8 遵守，无需另行裁决。")
 t.append("")
 t.append("## 7 交付物")
 t.append("")
 t.append("复制到 checkpoints/p05/registries/s4r9/M3e/ 的小表（前 4 项 + 清单本身）：")
 t.append("")
 t.append("1. GATE_R9M3E_start.txt")
 t.append("2. ERRATA_RECHECK_R9M3E.txt")
 t.append("3. REPORT_CHECK_R9M3E.txt")
 t.append("4. FROZEN_SCRIPTS_R9M3E.tsv")
 t.append("5. SHA256SUMS.txt")
 t.append("")
 t.append("## 附录 B（end 门禁）")
 t.append("")
 t.append("正式 end 门禁输出：$EV/gate/GATE_R9M3E_end.txt（不纳入 SHA256SUMS）。运行后由收尾在本节追加实际内容。")
 t.append("")
 t.append("## 8 本轮状态与结论")
 t.append("")
 t.append("- 本轮只读复核 + 文档写入；未运行 S4 的任何程序；S4/、判定器、历史装置、M3d 已提交产物未改动（end 门禁按 BASE 前缀校验）。")
 t.append("- 签收只记录用户原文；执行者未自行宣布任何阶段完成或签收。P05-S5 未开始、未签收。")
 t.append("- 本轮已完成 R9 M3e 范围，等待用户审核。")
 t.append("")
 t.append("git log -1: "+g)
 t.append("git status --short: "+st.replace(NL,"; ") if st else "git status --short: (clean)")
 t.append("")
 return NL.join(t)
def cmd_report(shake):
 txt=report_text(shake)
 if shake:
  os.makedirs(SHK,exist_ok=True); open(os.path.join(SHK,"REPORT.proposed.md"),"w",encoding="utf-8").write(txt)
  print("SHAKEDOWN REPORT proposed bytes %d"%len(txt.encode()))
 else:
  open(REPORT,"w",encoding="utf-8").write(txt)
  print("REPORT written bytes %d"%len(txt.encode()))
 return 0
def cmd_report_check(shake):
 src=os.path.join(SHK,"REPORT.proposed.md") if shake else REPORT
 txt=open(src,encoding="utf-8").read()
 lines=txt.splitlines()
 order=["## 1 门禁","## 2 裁决","## 3 勘误","## 4 签收文件摘要","## 5 事件两张表","## 6 需用户裁决","## 7 交付物","## 附录 B"]
 pos=[next((i for i,l in enumerate(lines) if l.strip()==h or l.strip().startswith(h)), -1) for h in order]
 checks=[]
 checks.append(("SECTIONS_IN_ORDER", all(p>=0 for p in pos) and pos==sorted(pos)))
 sec7=[]
 in7=False
 for l in lines:
  if l.strip()=="## 7 交付物": in7=True; continue
  if in7 and l.startswith("## "): break
  if in7:
   m=re.match(r"^\s*(\d+)\.\s+(.+?)\s*$",l)
   if m: sec7.append(m.group(2).strip())
 checks.append(("DELIVERABLE_COUNT_5", len(sec7)==5))
 checks.append(("DELIVERABLE_LAST_SUMS", bool(sec7) and sec7[-1]=="SHA256SUMS.txt"))
 checks.append(("DELIVERABLE_NO_BACKTICK", all(BT not in x for x in sec7)))
 checks.append(("VERDICT_LINE", "本轮已完成 R9 M3e 范围，等待用户审核" in txt))
 checks.append(("GIT_LINES", ("git log -1:" in txt) and ("git status --short:" in txt)))
 checks.append(("MARK_U359_E974_E976", all(k in txt for k in ("U359","E9-74","E9-76"))))
 checks.append(("SIGNOFF_SUMMARY", ("P05_S3_S4_SIGNOFF.md" in txt) and ("逐字" in txt)))
 checks.append(("EVENTS_TWO_TABLES", ("5.1 表一" in txt) and ("5.2 表二" in txt)))
 fails=[k for k,v in checks if not v]
 out=os.path.join(SHK if shake else EV,"REPORT_CHECK_R9M3E.txt")
 os.makedirs(os.path.dirname(out),exist_ok=True)
 body=["# REPORT_CHECK_R9M3E.txt -- report structure and deliverable-list check"]+["CHECK"+TAB+k+TAB+("PASS" if v else "FAIL") for k,v in checks]+["FAILS=%d"%len(fails)]
 open(out,"w",encoding="utf-8").write(NL.join(body)+NL)
 print(NL.join(body))
 return 0 if not fails else 2
SMALL=["GATE_R9M3E_start.txt","ERRATA_RECHECK_R9M3E.txt","REPORT_CHECK_R9M3E.txt","FROZEN_SCRIPTS_R9M3E.tsv"]
def cmd_copy(shake):
 src=SHK if shake else EV
 dst=os.path.join(SHK,"registries_copy") if shake else REGDIR
 rp=os.path.realpath(dst)
 allowed=os.path.realpath(REPO+"/checkpoints/p05")
 if not rp.startswith(allowed+os.sep):
  print("HARD_STOP copy dest outside checkpoints/p05: "+rp); return 2
 os.makedirs(dst,exist_ok=True)
 copied=[]
 for f in SMALL:
  sp=os.path.join(src,f)
  if not os.path.isfile(sp):
   print("HARD_STOP missing small table "+f); return 2
  shutil.copyfile(sp,os.path.join(dst,f)); copied.append(f)
 lines=[]
 for f in copied:
  a=sha_f(os.path.join(dst,f)); b=sha_f(os.path.join(src,f))
  if a!=b:
   print("HARD_STOP copy sha mismatch "+f); return 2
  lines.append(a+"  "+f)
 open(os.path.join(dst,"SHA256SUMS.txt"),"w",encoding="utf-8").write("# SHA256SUMS.txt -- small-table registry for P05-S4 R9 M3e (copied from the raw evidence dir)"+NL+NL.join(lines)+NL)
 print("COPY %d files -> %s"%(len(copied),os.path.relpath(dst,REPO)))
 if not shake:
  outs=["checkpoints/p05/briefs/P05_S4R9_BRIEF_M3e.md","checkpoints/p05/registries/RULINGS.tsv","checkpoints/p05/registries/s4r9/ERRATA_9.txt","checkpoints/p05/STATE.md","checkpoints/p05/P05_S3_S4_SIGNOFF.md","checkpoints/p05/P05_S4R9_M3e_REPORT.md"]+["checkpoints/p05/registries/s4r9/M3e/"+f for f in copied+["SHA256SUMS.txt"]]
  open(os.path.join(EV,"REGISTRY_OUTPUTS_R9M3E.tsv"),"w",encoding="utf-8").write(NL.join(outs)+NL)
  print("REGISTRY_OUTPUTS_R9M3E.tsv: %d declared outputs"%len(outs))
 return 0
def cmd_events(shake):
 a=anchor_line("m3e_chain_r9m3e.py events")
 if a<=0:
  print("HARD_STOP no events anchor in log"); return 2
 lines=log_lines()
 parent=""
 rows={}
 for x in range(1,a+1):
  if x>len(lines) or not lines[x-1].strip(): continue
  m=TS.match(lines[x-1])
  if m: parent=m.group(1)
  rows[x]=parent
 body=["# EVENTS_R9M3E.tsv -- safe_run.log line -> UTC timestamp (rows 1..%d; anchor = events call line %d)"%(a,a),"log_line"+TAB+"ts_utc"]+["%d%s%s"%(x,TAB,rows[x]) for x in sorted(rows)]+["# ROWS=%d"%len(rows)]
 out=os.path.join(SHK if shake else EV,"EVENTS_R9M3E.tsv")
 os.makedirs(os.path.dirname(out),exist_ok=True)
 open(out,"w",encoding="utf-8").write(NL.join(body)+NL)
 print("EVENTS rows=%d anchor=%d -> %s"%(len(rows),a,os.path.relpath(out,REPO)))
 return 0
def cmd_progress(shake):
 out=os.path.join(SHK if shake else EV,"PROGRESS_R9M3E.txt")
 line=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")+"\tP05-S4 R9 M3e closeout: sha_sums is the next (last) $EV write"
 if not os.path.isfile(out):
  open(out,"w",encoding="utf-8").write("# PROGRESS_R9M3E.txt -- closeout chain progress (last line is the sha_sums predecessor)\n")
 open(out,"a",encoding="utf-8").write(line+NL)
 print("PROGRESS appended: "+line)
 return 0
def cmd_sha_sums(shake):
 ev=SHK if shake else EV
 a=anchor_line("m3e_chain_r9m3e.py sha_sums")
 if a<=0:
  print("HARD_STOP no sha_sums anchor"); return 2
 lines=log_lines()
 trunc=NL.join(lines[:a])+NL
 th=sha_b(trunc.encode("utf-8"))
 items=[]
 for root,dirs,files in os.walk(ev):
  dirs[:]=sorted(d for d in dirs if d not in ("tmp","gate"))
  for f in sorted(files):
   fp=os.path.join(root,f)
   rel=os.path.relpath(fp,ev)
   if rel in ("safe_run.log","SHA256SUMS.txt") or f=="SHA256SUMS.txt": continue
   items.append((sha_f(fp),rel))
 out=os.path.join(ev,"SHA256SUMS.txt")
 if not shake and os.path.dirname(os.path.realpath(out))!=os.path.realpath(EV):
  print("HARD_STOP sha_sums path"); return 2
 body=["# SHA256SUMS.txt -- P05-S4 R9 M3e evidence manifest","# safe_run.log up to line %d: %s"%(a,th)]+["%s  %s"%(h,rel) for h,rel in items]
 open(out,"w",encoding="utf-8").write(NL.join(body)+NL)
 print("SHA256SUMS %d items trunc_line=%d sha=%s"%(len(items),a,th))
 return 0
def main():
 if len(sys.argv)<2:
  print("usage: m3e_chain_r9m3e.py <report|report_check|copy|events|progress|sha_sums> [--shakedown]"); return 2
 sub=sys.argv[1]; shake="--shakedown" in sys.argv[2:]
 return {"report":cmd_report,"report_check":cmd_report_check,"copy":cmd_copy,"events":cmd_events,"progress":cmd_progress,"sha_sums":cmd_sha_sums}[sub](shake)
if __name__=="__main__": sys.exit(main())
