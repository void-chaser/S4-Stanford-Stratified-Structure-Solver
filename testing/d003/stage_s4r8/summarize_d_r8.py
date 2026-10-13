#!/usr/bin/env python3
"""P05-S4 R8 M0 step 4: summary of the two D smoke passes (new file).

Usage (through safe_run):  python3 -I -B testing/d003/stage_s4r8/summarize_d_r8.py
Reads RESULTS_R8_D_pass1.tsv and RESULTS_R8_D_pass2.tsv (both must exist).  Writes D_SUMMARY_R8.txt (new, U17).
FLAKY (AGENTS section 5, cont. U66 rule): for the same point, pass 1 and pass 2 differ in class, verdict, rc, rc1, rc2 or hit.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
KEYS = ("class", "verdict", "rc", "rc1", "rc2", "hit")


def rows_of(path):
    header, out = None, {}
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                header = f
                continue
            r = dict(zip(header, f))
            out[(r["point_id"], r["group"])] = r
    return out


def main(argv):
    if len(argv) != 1:
        raise SystemExit("usage: summarize_d_r8.py")
    out = os.path.join(EV, "D_SUMMARY_R8.txt")
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    p1 = rows_of(os.path.join(EV, "RESULTS_R8_D_pass1.tsv"))
    p2 = rows_of(os.path.join(EV, "RESULTS_R8_D_pass2.tsv"))
    keys = sorted(set(p1) | set(p2))
    lines = ["# D_SUMMARY_R8.txt -- P05-S4 R8 M0 step 4 (D smoke, U113/U119/U124/U125).  Two passes; FLAKY per the rule in this file's docstring.",
             "point_id\tgroup\tpass1_verdict\tpass2_verdict\tpass1_class\tpass2_class\trc1_pass1\trc1_pass2\tpoint_result"]
    counts = {"MATCH": 0, "MISMATCH": 0, "FLAKY": 0, "MISSING": 0}
    for k in keys:
        a, b = p1.get(k), p2.get(k)
        if a is None or b is None:
            res = "MISSING"
        elif any(a[x] != b[x] for x in KEYS):
            res = "FLAKY"
        elif a["verdict"] == "MATCH":
            res = "MATCH"
        else:
            res = "MISMATCH"
        counts[res] += 1
        lines.append("\t".join([k[0], k[1], a["verdict"] if a else "-", b["verdict"] if b else "-",
                                a["class"] if a else "-", b["class"] if b else "-",
                                a["rc1"] if a else "-", b["rc1"] if b else "-", res]))
    lines.append("# counts: MATCH=%d MISMATCH=%d FLAKY=%d MISSING=%d (points=%d)" % (
        counts["MATCH"], counts["MISMATCH"], counts["FLAKY"], counts["MISSING"], len(keys)))
    with open(out, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("summary: MATCH=%d MISMATCH=%d FLAKY=%d MISSING=%d -> %s" % (
        counts["MATCH"], counts["MISMATCH"], counts["FLAKY"], counts["MISSING"], out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
