#!/usr/bin/env python3
"""P05-S4 R7 cont3: check that the ADD table's G1 inj_call equals the FIELDCALL cross-check table, point by point (new file).

Reads (read only): CHECK_FIELDCALL_R7.tsv (141 F injection rows, value = FIELDCALL_MAP field_call) and REGISTRY_S4_PRE_R7_M2_ADD.tsv
(G1 rows; the tree-F row of each point).  Writes one new file: argv[1].  Refuses if the output exists (U17).
Exit status is non-zero if any point differs or is missing.
Usage (through safe_run): python3 -I -B testing/d003/stage_s4r7/check_add_vs_fieldcall_r7.py EVDIR/CHECK_ADD_VS_FIELDCALL_R7.tsv
"""
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r7")
CHECK = os.path.join(EV, "CHECK_FIELDCALL_R7.tsv")
ADD = os.path.join(EV, "REGISTRY_S4_PRE_R7_M2_ADD.tsv")


def table(path):
    header, rows = None, []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                header = f
                continue
            rows.append(dict(zip(header, f)))
    return rows


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: check_add_vs_fieldcall_r7.py OUT.tsv")
    out = argv[1]
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    check = {r["point_id"]: r for r in table(CHECK) if r.get("status") in ("OK", "DIFFER", "MISSING")}
    add_g1 = {r["point_id"]: r for r in table(ADD) if r["group"] == "G1" and r["tree"] == "F"}
    lines = ["# CHECK_ADD_VS_FIELDCALL_R7.tsv -- ADD G1 inj_call vs FIELDCALL cross-check, point by point (read only).",
             "point_id\tfieldcall_map\tADD_inj_call\tstatus"]
    bad = 0
    for pid in sorted(check):
        want = check[pid]["fieldcall_map"]
        a = add_g1.get(pid + "-F")
        got = a["inj_call"] if a else "MISSING_IN_ADD"
        ok = (a is not None and got == want)
        if not ok:
            bad += 1
        lines.append("\t".join([pid, want, got, "OK" if ok else "DIFFER"]))
    lines.append("# points checked: %d; not equal or missing: %d" % (len(check), bad))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("points=%d differ_or_missing=%d -> %s" % (len(check), bad, out))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
