#!/usr/bin/env python3
"""P05-S4 R7 cont8: check every count quoted in the M2 final report against the run7 files (new file; read only).

The report P05_S4R7_REPORT_M2_FINAL.md quotes counts as lines "COUNT <key> = <value>".  This script reads the run7 summary
files and recomputes each key; a quoted value that differs from the recomputed value is a FAIL.  It does not read the report
for anything else.  Exit status 0 only if every quoted count is present and matches.

Keys checked (computed from the files, not from the report):
  CTRL_SEAM_MATCH_pass1/pass2, G2c_MATCH_pass1/pass2, G1_MATCH_pass1/pass2, G1_NOT_REACHED_pass1/pass2, G1_MISMATCH_pass1/pass2,
  G2a_MATCH_pass1/pass2, FLAKY_total, MISMATCH_total, VALUE_DRIFT_total, ENV_DRIFT_total, ENV_absent_total, points_value_compared,
  INVALID_hit_nonzero (hit != 0 among the NOT_REACHED rows, both trees).

Usage (through safe_run, absolute paths):
  python3 -I -B testing/d003/stage_s4r7/check_report_counts_r7.py EVDIR REPORT.md OUT.txt
"""
import os
import re
import sys

PAT = re.compile(r"^COUNT ([A-Za-z0-9_]+) = (-?\d+)\s*$", re.M)


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


def computed(ev):
    out = {}
    reg = table(os.path.join(ev, "REGRESS_R7_M2b_run7.tsv"))
    for r in reg:
        if r.get("group") in ("CTRL_SEAM", "G2c", "G1", "G2a") and r.get("pass") in ("1", "2"):
            key = "%s_MATCH_pass%s" % (r["group"], r["pass"])
            out[key] = int(r["MATCH"])
            if r["group"] == "G1":
                out["G1_NOT_REACHED_pass%s" % r["pass"]] = int(r["NOT_REACHED_AS_EXPECTED"])
                out["G1_MISMATCH_pass%s" % r["pass"]] = int(r["MISMATCH"])
    out["FLAKY_total"] = sum(int(r["FLAKY_points"]) for r in reg if r.get("FLAKY_points", "").isdigit())
    out["MISMATCH_total"] = sum(int(r["MISMATCH"]) for r in reg if r.get("MISMATCH", "").isdigit())
    vd = 0
    vh = os.path.join(ev, "VALUES_VS_HISTORY_run7.tsv")
    for line in open(vh, encoding="utf-8"):
        if line.startswith("# points_compared="):
            m = re.search(r"points_compared=(\d+) value_drift=(\d+)", line)
            out["points_value_compared"] = int(m.group(1))
            vd = int(m.group(2))
    out["VALUE_DRIFT_total"] = vd
    ed = None
    for line in open(os.path.join(ev, "ENV_DRIFT_R7_M2b_run7.tsv"), encoding="utf-8"):
        if line.startswith("# points="):
            m = re.search(r"points=(\d+) env_drift=(\d+) absent=(\d+)", line)
            out["ENV_points"] = int(m.group(1))
            out["ENV_DRIFT_total"] = int(m.group(2))
            out["ENV_absent_total"] = int(m.group(3))
            ed = True
    if ed is None:
        raise SystemExit("REFUSED: no ENV_DRIFT totals found")
    # hit != 0 among NOT_REACHED rows (both trees, pass 1 and 2)
    nz = 0
    for p in ("1", "2"):
        for raw in open(os.path.join(ev, "RESULTS_R7_G1_pass%s_run7.tsv" % p), encoding="utf-8"):
            if raw.startswith("#") or raw.startswith("point_id"):
                continue
            f = raw.rstrip("\n").split("\t")
            if len(f) > 12 and f[6] == "INVALID_NOT_REACHED" and f[8] == "NOT_REACHED_AS_EXPECTED" and f[12] != "0":
                nz += 1
    out["INVALID_hit_nonzero"] = nz
    return out


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: check_report_counts_r7.py EVDIR REPORT.md OUT.txt")
    ev, report, out = argv[1], argv[2], argv[3]
    if not (os.path.isabs(ev) and os.path.isabs(report) and os.path.isabs(out)):
        raise SystemExit("REFUSED: all paths must be absolute")
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    want = {}
    with open(report, encoding="utf-8") as fh:
        for m in PAT.finditer(fh.read()):
            want[m.group(1)] = int(m.group(2))
    have = computed(ev)
    lines = ["# report count check (cont8).  Quoted counts in the report are compared with counts recomputed from the run7 files."]
    fails = 0
    if not want:
        lines.append("FAIL no COUNT lines in the report")
        fails += 1
    for k in sorted(set(want) | set(have)):
        if k not in want:
            lines.append("NOT_QUOTED\t%s\t%s" % (k, have[k]))
            continue
        if k not in have:
            lines.append("FAIL\t%s\tquoted=%s\tnot computed" % (k, want[k]))
            fails += 1
            continue
        status = "OK" if want[k] == have[k] else "FAIL"
        if status == "FAIL":
            fails += 1
        lines.append("%s\t%s\tquoted=%s\tcomputed=%s" % (status, k, want[k], have[k]))
    lines.append("# checks_failed=%d" % fails)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("failed=%d -> %s" % (fails, out))
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
