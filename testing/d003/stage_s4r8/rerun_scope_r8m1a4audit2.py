#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a audit part 2 (r8m1a4audit2), section 4 step 4: rerun scope table.  New file.

Read only.  Builds the RERUN_SCOPE_R8_M1a4AUDIT2_<name>.tsv from the unit table and the tracer-audit gap list.  The rerun is
NOT executed in this round (section 4: a gap that is not empty stops at the planned stop point; the rerun is left to the
next round).

Gap list (from TRACER_AUDIT_R8_M1a4AUDIT2_RUN1.tsv, EVIDENCE_INSUFFICIENT rows):
  G1 T1_FINISH_OUT_OF_SCOPE : every unit (198).  The out_of_scope() callbacks write no record; the raw logs cannot show
                              that they did not fire.  Affects every pair.
  G2 T6_PLAN_BP_NOT_REQUIRED: the 138 units whose families do not contain plan or plancall.  Their plan breakpoint is shown
                              only by symbol query, and only for the driver families queried (see SYMQ files).
  G3 P0048 plan breakpoint  : resolved by symbol query on both F2 (r6dnv1-F2-plain) and F3 (r6dnv1-F3-plain): closed by evidence.
A pair is in the rerun scope if at least one of its two units carries a G1 or G2 gap.  Since G1 covers every unit, every pair
is in scope.  A pair is listed as a whole (both sides), as section 4 requires (complete F2/F3 pairs).

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/rerun_scope_r8m1a4audit2.py SCOPE_NAME
SCOPE_NAME: RERUN_SCOPE_R8_M1a4AUDIT2_<name>.tsv (bare name, must not exist, U17).
"""
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1a4audit2")
REG_M1A = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")
UNITS = os.path.join(REG_M1A, "CALLSEQ_UNITS_R8_M1a4_R3.tsv")
AUDIT = os.path.join(EV, "TRACER_AUDIT_R8_M1a4AUDIT2_RUN1.tsv")
NAME_RE = re.compile(r"^RERUN_SCOPE_R8_M1a4AUDIT2_[A-Za-z0-9_]+\.tsv$")


def read_tsv(path):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    hdr = lines[0].split("\t")
    return [dict(zip(hdr, ln.split("\t"))) for ln in lines[1:] if ln]


def main(argv):
    if len(argv) != 2 or not NAME_RE.match(argv[1]):
        raise SystemExit("usage: rerun_scope_r8m1a4audit2.py RERUN_SCOPE_R8_M1a4AUDIT2_<name>.tsv")
    out = os.path.join(EV, argv[1])
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    units = read_tsv(UNITS)
    audit = read_tsv(AUDIT)
    gaps_by_unit = {}
    for r in audit:
        if r["status"] == "EVIDENCE_INSUFFICIENT":
            gaps_by_unit.setdefault(r["unit_id"], []).append(r["check"])
    pairs = {}
    for u in units:
        pairs.setdefault(u["pair_id"], {})[u["run_tree"]] = u
    rows = []
    cnt = Counter()
    for pid in sorted(pairs):
        d = pairs[pid]
        if set(d) != {"F2", "F3"}:
            rows.append((pid, "-", "-", "INCOMPLETE_PAIR", "not in rerun scope: pair incomplete (EVIDENCE_INSUFFICIENT)", "-"))
            cnt["INCOMPLETE_PAIR"] += 1
            continue
        f2, f3 = d["F2"], d["F3"]
        g2 = sorted(set(gaps_by_unit.get(f2["unit_id"], [])))
        g3 = sorted(set(gaps_by_unit.get(f3["unit_id"], [])))
        in_scope = bool(g2) or bool(g3)
        reason = "G1 T1_FINISH_OUT_OF_SCOPE on both units (out_of_scope callbacks write no record)" if in_scope else "no gap"
        if "T6_PLAN_BP_NOT_REQUIRED" in g2 or "T6_PLAN_BP_NOT_REQUIRED" in g3:
            reason += "; G2 T6 plan breakpoint shown only by symbol query for this driver family"
        status = "RERUN_IN_SCOPE" if in_scope else "NOT_IN_SCOPE"
        cnt[status] += 1
        rows.append((pid, f2["unit_id"], f3["unit_id"], status, reason,
                     "%s|%s" % (f2["mode"], f2["NG"])))
    with open(out, "x", encoding="utf-8") as fh:
        fh.write("pair_id\tF2_unit\tF3_unit\tstatus\treason\tmode_NG\n")
        for r in rows:
            fh.write("\t".join(str(x).replace("\t", " ") for x in r) + "\n")
    print("rerun scope pairs=%d %s" % (len(rows), dict(sorted(cnt.items()))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
