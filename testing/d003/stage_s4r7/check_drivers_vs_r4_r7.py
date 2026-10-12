#!/usr/bin/env python3
"""P05-S4 R7 cont5 section 3.1: compare the R7 seam drivers with the R4 seam drivers (new file; read only except OUT).

Reads $EV/DRIVERS_R7_SEAM.tsv and registries/s4r4/DRIVERS.tsv; writes one new file OUT (U17).
For each R7 seam driver whose R4 counterpart exists (seamF, fmmret-F; the tree F pair), records whether the driver sha256
is SAME or DIFFERENT, and whether the library sha256 is SAME or DIFFERENT.  Nothing stops on DIFFERENT (cont5 3.1):
the libraries are byte-identical per U51, and any driver difference is stated in the errata.
Usage (through safe_run):  python3 -I -B testing/d003/stage_s4r7/check_drivers_vs_r4_r7.py EVDIR OUT.tsv
Exit status 0 always when the comparison is written; 1 if an R4 reference or an R7 row is missing.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
R4_DRIVERS = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r4", "DRIVERS.tsv")
R4_LIBS = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r4", "LIBS_R4.tsv")  # U64: library hashes come from here
R4_LIB_PAIRS = {"seamF-F": "seamF", "fmmret-F": "fmmret-F"}  # R7 driver name -> R4 driver name (tree F only)


def rows(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            out.append(line.split("\t"))
    return out


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: check_drivers_vs_r4_r7.py EVDIR OUT.tsv")
    ev, out = argv[1], argv[2]
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    r7 = {r[0]: r for r in rows(os.path.join(ev, "DRIVERS_R7_SEAM.tsv"))}
    r4 = {r[0]: r for r in rows(R4_DRIVERS)}
    libs = {r[0]: r[1] for r in rows(R4_LIBS)}  # name -> library sha256 (U64)
    lines = ["# R7 seam drivers vs R4 seam drivers (tree F pairs only).  SAME/DIFFERENT only; no stop on DIFFERENT (cont5 3.1).",
             "r7_name\tr4_name\tr7_lib_sha256\tr4_lib_sha256_ref\tlib_comparison\tr7_driver_sha256\tr4_driver_sha256\tdriver_comparison"]
    missing = 0
    for r7n, r4n in R4_LIB_PAIRS.items():
        if r7n not in r7 or r4n not in r4:
            missing += 1
            lines.append("%s\t%s\tMISSING\tMISSING\tMISSING\tMISSING\tMISSING\tMISSING" % (r7n, r4n))
            continue
        a, b = r7[r7n], r4[r4n]
        # library: R4 sha256 from registries/s4r4/LIBS_R4.tsv (U64, column 2; the name is column 1)
        if r4n not in libs:
            lib_cmp, r4_lib = "MISSING_R4_LIB", "-"
            missing += 1
        else:
            r4_lib = libs[r4n]
            lib_cmp = "SAME" if a[2] == r4_lib else "DIFFERENT"
        drv_cmp = "SAME" if a[3] == b[1] else "DIFFERENT"
        lines.append("\t".join([r7n, r4n, a[2], r4_lib, lib_cmp, a[3], b[1], drv_cmp]))
    lines.append("# pairs=%d missing=%d" % (len(R4_LIB_PAIRS), missing))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("pairs=%d missing=%d -> %s" % (len(R4_LIB_PAIRS), missing, out))
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
