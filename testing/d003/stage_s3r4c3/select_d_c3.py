#!/usr/bin/env python3
"""select_d_c3.py -- P05-S3R4 CONT3 (D) smoke point selection (new file).

From the R7 run7 pass-1 result tables, select per group (CTRL_SEAM, G2c, G1, G2a) the first and the last point
by point_id in byte order (no locale).  Writes REGISTRY_S3R4C3_D.tsv pre-registration rows with the expected
class and rc1 from run7.  Must run before any D run.  Invoked through safe_run only.
"""
import os
import sys

REPO = os.environ["REPO"]
EV = os.environ["EV"]
R7 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7")
GROUPS = [
    ("CTRL_SEAM", "RESULTS_R7_CTRL_SEAM_pass1_run7.tsv"),
    ("G2c", "RESULTS_R7_G2c_pass1_run7.tsv"),
    ("G1", "RESULTS_R7_G1_pass1_run7.tsv"),
    ("G2a", "RESULTS_R7_G2a_pass1_run7.tsv"),
]


def read_rows(path):
    with open(path, "rb") as f:
        lines = f.read().decode("utf-8").splitlines()
    header = None
    rows = []
    for ln in lines:
        if not ln or ln.startswith("#"):
            continue
        cols = ln.split("\t")
        if header is None:
            header = cols
            continue
        rows.append(dict(zip(header, cols)))
    return header, rows


def main():
    out = os.path.join(EV, "REGISTRY_S3R4C3_D.tsv")
    if os.path.exists(out):
        print("REFUSED: exists %s" % out)
        return 2
    lines = ["group\tpoint_id\ttree\tmode\trequest\tinj_call\texpected_class\texpected_rc1\tsource\tstatus"]
    for grp, fname in GROUPS:
        header, rows = read_rows(os.path.join(R7, fname))
        rows.sort(key=lambda r: r["point_id"].encode("utf-8"))
        picks = [rows[0], rows[-1]] if len(rows) >= 2 else rows
        for r in picks:
            lines.append("\t".join([
                grp, r["point_id"], r["tree"], r["mode"], r["request"], r["inj_call"],
                r["class"], r["rc1"], fname, "INFLUENCED"]))
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("D prereg written: %s rows=%d" % (out, len(lines) - 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
