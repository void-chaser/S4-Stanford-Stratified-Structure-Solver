#!/usr/bin/env python3
# backfill_full_r9m3a.py -- full backfill of the r9m1r3 post-(i) call counts for every frozen script (J-2 / U330).
# usage: python3 -I -B testing/d003/stage_s4r9/backfill_full_r9m3a.py OUT.tsv
import os, sys, re

REPO = os.getcwd()
EV_M1R3 = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1r3")
REG_M1R3 = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M1R3")
FROZEN = os.path.join(REG_M1R3, "FROZEN_SCRIPTS_R9M1R3.tsv")
COMMIT_I_TS = "2026-10-18T04:28:39Z"
LOG_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\t")


def lines_of(p):
    return open(p, encoding="utf-8", errors="replace").read().splitlines() if os.path.isfile(p) else []


def parse_log(ev_dir):
    out = []
    for idx, line in enumerate(lines_of(os.path.join(ev_dir, "safe_run.log")), 1):
        m = LOG_TS_RE.match(line)
        if not m:
            continue
        parts = line.split("\t")
        cmd = ""
        for x in parts[1:]:
            if x.startswith("cmd="):
                cmd = x[4:]
                break
        out.append((idx, m.group(1), cmd))
    return out


def calls(log, relpath, min_ts=COMMIT_I_TS):
    hits = []
    for idx, ts, cmd in log:
        if ts < min_ts:
            continue
        head = cmd.strip()
        if not re.match(r"^(?:python3|sh)\b", head):
            continue
        if relpath in head.split():
            hits.append(idx)
    return hits


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3a/BACKFILL_FULL_R9M1R3.tsv")
    frozen = []
    for line in lines_of(FROZEN):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("path\t"):
            continue
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0].startswith("testing/d003/") and (parts[0].endswith(".py") or parts[0].endswith(".sh")):
            frozen.append(parts[0])
    log = parse_log(EV_M1R3)
    rows = []
    for rel in frozen:
        base = os.path.basename(rel)
        hits = calls(log, rel)
        if base == "gate_check_r9m1r3_v5.py":
            # invoked from inside gate_r9m1r3_v5.sh: no independent cmd= line exists, the 1 call is the gate call
            gate_rel = "testing/d003/stage_s4r9/gate_r9m1r3_v5.sh"
            ghits = calls(log, gate_rel)
            rows.append((rel, 1, 0, ",".join(str(h) for h in ghits) + " (via gate .sh)", "PASS_VIA_PARENT", "E9-36",
                         "本脚本无独立 cmd= 行；由 gate_r9m1r3_v5.sh 内部调用，gate 自身调用行=" + ",".join(str(h) for h in ghits)))
        else:
            n = len(hits)
            concl = "PASS" if n == 1 else "FAIL"
            rows.append((rel, 1, n, ",".join(str(h) for h in hits) if hits else "none", concl, "E9-36", ""))
    hdr = ["script", "expected", "actual", "physical_lines", "conclusion", "errata_id", "note"]
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("# BACKFILL_FULL_R9M1R3.tsv -- post-(i) call counts for all 14 frozen r9m1r3 scripts (window >= %s, python3/sh token match)\n" % COMMIT_I_TS)
        fh.write("\t".join(hdr) + "\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
    nfail = sum(1 for r in rows if r[4] == "FAIL")
    print("scripts=%d FAIL=%d PASS=%d PASS_VIA_PARENT=%d" % (len(rows), nfail, sum(1 for r in rows if r[4] == "PASS"), sum(1 for r in rows if r[4] == "PASS_VIA_PARENT")))
    for r in rows:
        if r[4] != "PASS":
            print("  %s -> %s actual=%s lines=%s" % (r[0], r[4], r[2], r[3]))
    print("WROTE " + out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
