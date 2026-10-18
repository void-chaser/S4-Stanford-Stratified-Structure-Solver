#!/usr/bin/env python3
# ledger_check_r9m3a.py -- read-only consistency check between the red-point ledger and the STATE open-item table.
# usage: python3 -I -B testing/d003/stage_s4r9/ledger_check_r9m3a.py OUT.tsv
import os, sys

REPO = os.getcwd()
TAB = chr(9)
NL = chr(10)


def find_ledger():
    cands = []
    for root, dirs, files in os.walk(os.path.join(REPO, "checkpoints/p05")):
        if "evidence" in root.split(os.sep):
            continue
        for f in files:
            if f.startswith("RED_POINTS_LEDGER") and f.endswith(".tsv"):
                cands.append(os.path.join(root, f))
    cands.sort(key=lambda p: (os.path.getmtime(p), p))
    return cands[-1] if cands else None


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3a/LEDGER_CHECK_R9M3A.tsv")
    led = find_ledger()
    state = os.path.join(REPO, "checkpoints/p05/STATE.md")
    st = open(state, encoding="utf-8").read() if os.path.isfile(state) else ""
    rows = []
    n = 0
    if led:
        lines = [l for l in open(led, encoding="utf-8").read().splitlines() if l.strip() and not l.startswith("#")]
        hdr = lines[0].split(TAB)
        for line in lines[1:]:
            f = line.split(TAB)
            rec = dict(zip(hdr, f))
            rid = rec.get("red_point_id") or rec.get("id") or (f[0] if f else "")
            status = rec.get("status") or rec.get("state") or (f[1] if len(f) > 1 else "")
            n += 1
            in_state = rid in st
            rows.append((rid, status, "PRESENT" if in_state else "ABSENT", "CONSISTENT" if in_state else "STATE_MISSING_ENTRY", rec.get("owner_round", "")))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# LEDGER_CHECK_R9M3A.tsv -- ledger vs STATE open-item table (read only); ledger=" + str(led) + NL)
        fh.write(TAB.join(["red_point_id", "ledger_status", "state_presence", "consistency", "owner_round"]) + NL)
        for r in rows:
            fh.write(TAB.join(str(x) for x in r) + NL)
    print("ledger=%s rows=%d absent_in_state=%d" % (led, n, sum(1 for r in rows if r[2] == "ABSENT")))
    print("WROTE " + out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
