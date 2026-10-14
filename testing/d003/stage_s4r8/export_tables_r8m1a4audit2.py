#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a audit part 2 (r8m1a4audit2), section 2 outputs: the 44-row table and the old-versus-new difference
table.  New file.  Read only.  Writes two new files into the round evidence directory.

  INVALID44_R8_M1a4AUDIT2_<name>.tsv   : one row per ADD_v3 row with historical expectation INVALID_NOT_REACHED (44 rows),
                                         with the source row, the unit, the counted value and the status.
  DIFF_OLD_NEW_R8_M1a4AUDIT2_<name>.tsv: one row per source row whose old coverage status differs from the new status,
                                         plus one summary row per (old, new) pair for the rows that are the same.

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/export_tables_r8m1a4audit2.py TARGETS_NAME
TARGETS_NAME: the REQUEST_TARGETS_R8_M1a4AUDIT2_<name>.tsv file (existing).  Output names are derived from it.
"""
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1a4audit2")
NAME_RE = re.compile(r"^REQUEST_TARGETS_R8_M1a4AUDIT2_([A-Za-z0-9_]+)\.tsv$")


def read_tsv(path):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    hdr = lines[0].split("\t")
    return hdr, [dict(zip(hdr, ln.split("\t"))) for ln in lines[1:] if ln]


def main(argv):
    if len(argv) != 2 or not NAME_RE.match(argv[1]):
        raise SystemExit("usage: export_tables_r8m1a4audit2.py REQUEST_TARGETS_R8_M1a4AUDIT2_<name>.tsv")
    tag = NAME_RE.match(argv[1]).group(1)
    src = os.path.join(EV, argv[1])
    if not os.path.isfile(src):
        raise SystemExit("REFUSED: targets table missing")
    out_inv = os.path.join(EV, "INVALID44_R8_M1a4AUDIT2_%s.tsv" % tag)
    out_diff = os.path.join(EV, "DIFF_OLD_NEW_R8_M1a4AUDIT2_%s.tsv" % tag)
    for p in (out_inv, out_diff):
        if os.path.exists(p):
            raise SystemExit("REFUSED: exists (U17): %s" % p)

    _, rows = read_tsv(src)
    inv = [r for r in rows if r.get("status") == "NOW_REACHED_WAS_NOT_REACHED"]
    # the 44 INVALID rows are those whose historical expectation is INVALID_NOT_REACHED; the status NOW_REACHED is
    # assigned by classify only to those rows, so the set is the same.  The count is checked against 44.
    if len(inv) != 44:
        raise SystemExit("REFUSED: INVALID rows %d != 44" % len(inv))
    with open(out_inv, "x", encoding="utf-8") as fh:
        fh.write("source_registry\tsource_row\tpoint_id\tgroup\trun_tree\tmode\tNG\troute\trequest_raw\tcanonical_target\t"
                 "unit_id\thistorical_expectation\told_reach_status\tnew_status\tdetail\n")
        for r in inv:
            fh.write("\t".join(str(x).replace("\t", " ") for x in (
                r["source_registry"], r["source_row"], r["point_id"], r["group"], r["run_tree"], r["mode"], r["NG"],
                r["route"], r["request_raw"], r["canonical_target"], r["unit_id"], "INVALID_NOT_REACHED",
                r["old_reach_status"], r["status"], r["detail"])) + "\n")

    cnt = Counter()
    diff_rows = []
    for r in rows:
        key = (r["old_reach_status"], r["status"])
        cnt[key] += 1
        if r["old_reach_status"] != r["status"]:
            diff_rows.append((r["source_registry"], r["source_row"], r["point_id"], r["group"], r["run_tree"],
                              r["request_raw"], r["unit_id"], r["old_reach_status"], r["status"], r["detail"]))
    with open(out_diff, "x", encoding="utf-8") as fh:
        fh.write("source_registry\tsource_row\tpoint_id\tgroup\trun_tree\trequest_raw\tunit_id\told_status\tnew_status\tdetail\n")
        for d in diff_rows:
            fh.write("\t".join(str(x).replace("\t", " ") for x in d) + "\n")
        fh.write("# summary of all source rows, old -> new (count)\n")
        for (o, n), c in sorted(cnt.items()):
            fh.write("# %s -> %s\t%d\n" % (o, n, c))
    print("export: INVALID44 rows=%d; diff rows=%d; pairs=%s" % (len(inv), len(diff_rows), dict(sorted(cnt.items()))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
