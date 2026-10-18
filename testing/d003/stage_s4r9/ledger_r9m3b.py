#!/usr/bin/env python3
# ledger_r9m3b.py -- red-point ledger append for the E2E result (U333d) and the consistency check between the
# latest red-point ledger and the STATE open-item table. New file (r9m3b).
# usage: python3 -I -B testing/d003/stage_s4r9/ledger_r9m3b.py
import os, re

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b")
TAB = chr(9)
NL = chr(10)
RED = os.path.join(EV, "RED_POINTS_LEDGER_APPEND_R9M3B.tsv")
CHK = os.path.join(EV, "LEDGER_CHECK_R9M3B.tsv")
RED_THRESHOLD = ("API_SILENT", "RETRY_DIFF", "RETRY_FAIL")


def read_tsv(path):
    rows = []
    hdr = None
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        rows.append(dict(zip(hdr, f)))
    return rows


def main():
    e2e = read_tsv(os.path.join(EV, "E2E_VERDICT_R9M3B.tsv"))
    mk = read_tsv(os.path.join(EV, "MAKETEST_VERDICT_R9M3B.tsv"))
    mkv = {r.get("item"): r.get("value") for r in mk}
    cats = {}
    for r in e2e:
        cats[r.get("verdict", "?")] = cats.get(r.get("verdict", "?"), 0) + 1
    reds = [r for r in e2e if r.get("verdict") in RED_THRESHOLD]
    with open(RED, "w", encoding="utf-8") as fh:
        fh.write("# RED_POINTS_LEDGER_APPEND_R9M3B.tsv -- red points opened by the M3b E2E verdict (U333d)" + NL)
        fh.write(TAB.join(["id", "source_round", "site", "tree", "category", "evidence", "status", "destination"]) + NL)
        if not reds:
            fh.write(TAB.join(["RP-R9M3B-NONE", "R9 M3b", "Python/Lua public-API E2E", "F4", "无新红点",
                               "正式两遍全部 E2E_OK/CONTROL_OK（%s）；无 API_SILENT/RETRY_DIFF/RETRY_FAIL" % str(sorted(cats.items())),
                               "无新红点", "无（本阶段不改 S4/）" ]) + NL)
        for i, r in enumerate(reds, 1):
            fh.write(TAB.join(["RP-R9M3B-%02d" % i, "R9 M3b", "E2E point " + r.get("point_id", "?"), "F4",
                               r.get("verdict", "?"), "E2E_VERDICT_R9M3B.tsv:" + r.get("point_id", "?") + " " + r.get("detail", ""),
                               "新红点（待用户裁决）", "S5（本阶段不改 S4/）"]) + NL)
    # consistency: latest committed ledger vs STATE open items
    led_p = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M2/RED_POINTS_LEDGER_APPEND_R9.tsv")
    led = read_tsv(led_p) if os.path.isfile(led_p) else []
    state = open(os.path.join(REPO, "checkpoints/p05/STATE.md"), encoding="utf-8").read()
    rows = []
    for r in led:
        rid = r.get("id")
        found = rid in state
        rows.append((rid, r.get("status", ""), "YES" if found else "NO", r.get("destination", ""),
                     "present in STATE open items" if found else "not found in STATE open items (see report)"))
    with open(CHK, "w", encoding="utf-8") as fh:
        fh.write("# LEDGER_CHECK_R9M3B.tsv -- latest red-point ledger vs STATE open-item table (read-only)" + NL)
        fh.write(TAB.join(["ledger_id", "ledger_status", "state_has_row", "destination", "note"]) + NL)
        for r in rows:
            fh.write(TAB.join(r) + NL)
        fh.write("# e2e_verdict_counts\t" + str(sorted(cats.items())) + NL)
        fh.write("# maketest_verdict\t" + str(mkv.get("verdict", "?")) + NL)
        fh.write("# new_red_points\t" + str(len(reds)) + NL)
    print("E2E_CATS " + str(sorted(cats.items())))
    print("RED_ROWS=%d LEDGER_ROWS=%d" % (len(reds), len(rows)))
    print("MAKETEST " + str(mkv.get("verdict", "?")))
    print("WROTE " + RED)
    print("WROTE " + CHK)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
