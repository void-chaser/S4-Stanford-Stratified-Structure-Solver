#!/usr/bin/env python3
# relr3_state.py -- P05 delivery round REL-R3: entry-document sync of checkpoints/p05/STATE.md only.
# Edits, in this order and nothing else:
#   section 1: the '当前轮次' row becomes REL-R3; the 'P05 交付轮' row gains REL-R3;
#   section 2: one REL-R3 row is appended after the REL-R2 row;
#   section 4: one REL-R3 evidence-location bullet is appended;
#   footer: one provenance line is appended.
# It never pre-writes a gate result (the only gate reference is 'appendix C') and refuses to duplicate.
# AGENTS.md / PROJECT_ROADMAP.md / ISSUE_REGISTRY.md are NOT touched.
import os, sys, hashlib, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-rel-r3")
STATE = os.path.join(P05, "STATE.md")
TAB = chr(9)
NL = chr(10)
MARK = "P05_RELR3_REPORT.md"


def read_table(path):
    header = None
    rows = []
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip(NL).split(TAB)
        if header is None:
            header = f
            continue
        if len(f) == len(header):
            rows.append(dict(zip(header, f)))
    return rows


def read_kv(path):
    d = {}
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip(NL).split(TAB)
        if len(f) == 2 and f[0] != "key":
            d[f[0]] = f[1]
    return d


def numbers():
    push = read_table(os.path.join(EV, "PUSH_LOG_RELR3.tsv"))
    lsr = [r for r in push if r["action"] == "ls_remote"]
    pr = read_kv(os.path.join(EV, "PR_RELR3.tsv"))
    clone = read_kv(os.path.join(EV, "REMOTE_CLONE_RELR3.tsv"))
    v = read_table(os.path.join(EV, "V_RELR3.tsv"))
    d = {
        "push_ok": sum(1 for r in push if r["action"] == "push" and r["rc"] == "0"),
        "lsr_ok": sum(1 for r in lsr if r["match"] == "YES"),
        "pr": pr.get("PR_NUMBER", "NA"),
        "pr_url": pr.get("PR_URL", "NA"),
        "r7_rc": clone.get("R7_RC", "NA"),
        "r7_units": clone.get("R7_UNIT_COUNT", "NA"),
        "v_same": sum(1 for r in v if r.get("result") == "SAME"),
        "v_mismatch": sum(1 for r in v if r.get("result") == "MISMATCH"),
    }
    shas = {r["ref"]: r["remote_sha"].split(",")[0] for r in lsr}
    d["prod"] = shas.get("refs/heads/p05/d003-fft-error-propagation", "NA")
    d["arch"] = shas.get("refs/heads/archive/p05-d003-full-20261019", "NA")
    d["tag1"] = shas.get("refs/tags/p05-signed-20261019", "NA")
    d["tag2"] = shas.get("refs/tags/p05-rel-r1-20261019", "NA")
    return d


def main():
    src = open(STATE, encoding="utf-8").read()
    if MARK in src:
        print("HARD_STOP STATE.md already mentions REL-R3; refusing to duplicate")
        return 2
    d = numbers()
    if d["push_ok"] != 4 or d["lsr_ok"] != 4 or d["v_mismatch"] != 0:
        print("HARD_STOP measurements not clean: push_ok=%s lsr_ok=%s v_mismatch=%s"
              % (d["push_ok"], d["lsr_ok"], d["v_mismatch"]))
        return 2
    relr3_row = ("| REL-R3 | P05 交付轮（rel-r3）：按 U393 顺序推送 4 个 ref——产品分支 8e4c014、"
                 "归档分支 4607e96、标签对象 ef925cde（peel 3de6d8b）与 b42c4c16（peel c88bf30）；"
                 "R1–R8 SAME（R9 空工作区由 end 门禁复测）；fork 内 Draft PR #%s（OPEN、Draft、base master、"
                 "commits=2、changedFiles=11）；远端克隆 HEAD 8e4c014、S4 589e15eb，make test rc=%s、单元 %s、"
                 "无失败；补扫 token/密钥 0、无 ≥50 MB blob；门禁结果见报告附录 C | P05_RELR3_REPORT.md；"
                 "registries/rel-r3/ |" % (d["pr"], d["r7_rc"], d["r7_units"]))
    lines = src.split(NL)
    out = []
    done = {"cur": False, "deliv": False, "row": False, "ev": False}
    sec = 0
    for line in lines:
        if line.startswith("## "):
            sec = 1 if line.startswith("## 1") else (2 if line.startswith("## 2") else
                                                    (4 if line.startswith("## 4") else 3))
        if sec == 1 and line.startswith("| 当前轮次 |") and not done["cur"]:
            out.append("| 当前轮次 | P05 交付轮 REL-R3（rel-r3：推送到 fork 并开 Draft PR；不是 P05 新阶段，"
                       "S1–S5、REL-R1、REL-R2 历史不改；门禁结果见 P05_RELR3_REPORT.md 附录 C） |")
            done["cur"] = True
            continue
        if sec == 1 and line.startswith("| P05 交付轮 |") and "REL-R2" in line:
            out.append("| P05 交付轮 | REL-R1（rel-r1；修复后完整原有功能非破坏性验证；门禁结果见 "
                       "P05_RELR1_REPORT.md 附录 C）、REL-R2（rel-r2；产品分支构建与上传前审查；门禁结果见 "
                       "P05_RELR2_REPORT.md 附录 C）与 REL-R3（rel-r3；推送 4 个 ref 并开 Draft PR；"
                       "门禁结果见 P05_RELR3_REPORT.md 附录 C） |")
            done["deliv"] = True
            continue
        out.append(line)
        if sec == 2 and line.startswith("| REL-R2 |") and not done["row"]:
            out.append(relr3_row)
            done["row"] = True
    if not done["row"]:
        print("HARD_STOP REL-R2 row anchor not found")
        return 2
    # section 4 evidence bullet, inserted before the generator footer line
    marker = None
    for i, line in enumerate(out):
        if line.startswith("（本文件由 s5r7_state.py"):
            marker = i
            break
    bullet = ("- **P05 交付轮 REL-R3（rel-r3）**：证据 checkpoints/p05/evidence/p05-rel-r3/"
              "（SHA256SUMS.txt；remoteclone/ 不入 git）；小表 checkpoints/p05/registries/rel-r3/；"
              "报告 P05_RELR3_REPORT.md；4 个远端 ref 已推送，Draft PR #%s。" % d["pr"])
    if marker is None:
        out.append(bullet)
    else:
        out.insert(marker, bullet)
    done["ev"] = True
    if not all(done.values()):
        print("HARD_STOP anchors not found: " + repr(done))
        return 2
    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out.append("")
    out.append("（REL-R3 行由 relr3_state.py 于 %s 追加；S1–S5、REL-R1、REL-R2 的历史数字未改）" % utc)
    data = NL.join(out)
    if MARK not in data or ("P05-" + "S6") in data:
        raise SystemExit("HARD_STOP STATE.md content check failed")
    open(STATE, "w", encoding="utf-8").write(data)
    print("STATE.md updated; bytes=%d" % len(data.encode("utf-8")))
    print("SHA256=" + hashlib.sha256(open(STATE, "rb").read()).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
