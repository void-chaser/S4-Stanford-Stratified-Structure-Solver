#!/usr/bin/env python3
"""P05-S4 R8 M1a, section 5.1: the list of drivers and libraries that M1b/M1c need, and what M0 lacks.  New file.

Writes $EV/NEEDS_R8_M1a.tsv (new file; refused if it exists).  Reads only:
  - the R7 driver records (registries/s4r7/DRIVERS_R7.tsv, DRIVERS_R7_cont1.tsv, DRIVERS_R7_SEAM.tsv, DRIVERS_R7_M3.tsv,
    DRIVER_R6B_SEAM_R7.tsv, DRIVER_R6B_SEAM_R7_F2.tsv);
  - the M0 driver table registries/s4r8/DRIVERS_R8.tsv (which F3 drivers exist already);
  - the R7 link log (checkpoints/p05/evidence/p05-s4r7/safe_run.log), for the line numbers of the link commands.
Every row names: the group, the driver family, the mode, the library kind, the tree, the R7 driver record (file, path,
sha256), the F3 driver name that M1b/M1c would use, whether M0 already has it, and the source the choice is read from.
No driver is built or run.  Usage (through safe_run):  python3 -I -B testing/d003/stage_s4r8/make_needs_r8m1.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
REG7 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7")
REG8 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8")
LOG7 = "checkpoints/p05/evidence/p05-s4r7/safe_run.log"
OUT = os.path.join(EV, "NEEDS_R8_M1a.tsv")
R7_DRV_DIR = "checkpoints/p05/evidence/p05-s4r7/drivers_r7"


def table_rows(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            rows.append(line.split("\t"))
    return rows


def find_lines(log_rel, needle):
    """1-based line numbers of the lines of a log that contain needle (read only)."""
    out = []
    with open(os.path.join(REPO, log_rel), encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh, 1):
            if needle in line:
                out.append(i)
    return out


def load_r7():
    """{record name: (file, lib_sha256, driver_sha256, driver_path, tree)} for every R7 driver, by its directory name."""
    rec = {}
    # DRIVERS_R7.tsv: driver, tree, mode, lib_sha256, driver_sha256, driver_path (the driver path names the record)
    for r in table_rows(os.path.join(REG7, "DRIVERS_R7.tsv")):
        if r[0] == "driver":
            continue
        name = "%s-%s-%s" % (r[0], r[1], r[2])
        rec[name] = ("DRIVERS_R7.tsv", r[3], r[4], r[5], r[1])
    # DRIVERS_R7_cont1.tsv: tree, mode(=tri), lib_sha256, driver_sha256, driver_path (tri dbg)
    for r in table_rows(os.path.join(REG7, "DRIVERS_R7_cont1.tsv")):
        if r[0] == "tree":
            continue
        name = "tri-%s-dbg" % r[0]
        rec[name] = ("DRIVERS_R7_cont1.tsv", r[2], r[3], r[4], r[0])
    # DRIVERS_R7_SEAM.tsv: name, tree, lib_sha256, driver_sha256, library_path (column 5 is the LIBRARY)
    for r in table_rows(os.path.join(REG7, "DRIVERS_R7_SEAM.tsv")):
        name = "seam-%s" % r[0]
        rec[name] = ("DRIVERS_R7_SEAM.tsv", r[2], r[3], "%s/%s/driver" % (R7_DRV_DIR, name), r[1])
    # DRIVER_R6B_SEAM_R7*.tsv: name, lib_sha256, driver_sha256, library_path
    for fname in ("DRIVER_R6B_SEAM_R7.tsv", "DRIVER_R6B_SEAM_R7_F2.tsv"):
        for r in table_rows(os.path.join(REG7, fname)):
            tree = "F2" if fname.endswith("_F2.tsv") else "F"
            rec[r[0]] = (fname, r[1], r[2], "%s/%s/driver" % (R7_DRV_DIR, r[0]), tree)
    return rec


def main(argv):
    if len(argv) != 1:
        raise SystemExit("usage: make_needs_r8m1.py  (no arguments)")
    if os.path.exists(OUT):
        raise SystemExit("REFUSED: exists, never overwritten (U17): %s" % OUT)

    r7 = load_r7()
    m0 = {}
    for r in table_rows(os.path.join(REG8, "DRIVERS_R8.tsv")):
        if r[0] == "driver":
            continue
        m0[r[0]] = r  # driver, tree, mode, lib_sha256, driver_sha256, lib_path, driver_path

    # R7 link command line numbers in safe_run.log (the command text is quoted there; read only)
    link_lines = {
        "d003-F-dbg": find_lines(LOG7, "drivers_r7/d003-F-dbg "),
        "d003plan-F-dbg": find_lines(LOG7, "drivers_r7/d003plan-F-dbg "),
        "r6bstate-F-dbg": find_lines(LOG7, "drivers_r7/r6bstate-F-dbg "),
        "r6dnv1-F-dbg": find_lines(LOG7, "drivers_r7/r6dnv1-F-dbg "),
        "d003-F-plain": find_lines(LOG7, "drivers_r7/d003-F-plain "),
        "d003plan-F-plain": find_lines(LOG7, "drivers_r7/d003plan-F-plain "),
        "r6bstate-F-plain": find_lines(LOG7, "drivers_r7/r6bstate-F-plain "),
        "r6dnv1-F-plain": find_lines(LOG7, "drivers_r7/r6dnv1-F-plain "),
        "tri-plain (loop)": find_lines(LOG7, 'O="$1/drivers_r7/tri-$T-plain"'),
        "tri-dbg (loop)": find_lines(LOG7, 'O="$1/drivers_r7/tri-$T-dbg"'),
        "seam-seamF-F (link_seam_drivers)": find_lines(LOG7, "drivers_r7/seam-seamF-F "),
        "r6bseam-seamF-F": find_lines(LOG7, "drivers_r7/r6bseam-seamF-F "),
    }

    # (group, driver family, mode, library kind, tree, R7 record name or None, F3 driver name, source)
    # Each row is one (group, tree, driver) line, so that no choice depends on a joined string.
    spec = []
    for tree in ("F", "F2"):
        spec += [
            ("M1-G7", "r6dnv1", "plain", "plain", tree, "r6dnv1-%s-plain" % tree, "r6dnv1-F3-plain",
             "run_m1_r7.py:35-36 (rnv1 family, plain as built by link_drivers_s4r7.sh)"),
            ("M1-G8", "tri", "dbg", "plain", tree, "tri-%s-dbg" % tree, "tri-F3-dbg",
             "run_m1_r7.py:37-38 (tri family, dbg); DRIVERS_R7_cont1.tsv"),
            ("M1-4.2-rnv1", "r6dnv1", "plain", "plain", tree, "r6dnv1-%s-plain" % tree, "r6dnv1-F3-plain",
             "run_m1_r7.py:35-36 (rnv1 family, plain)"),
            ("M1-4.2-tri", "tri", "dbg", "plain", tree, "tri-%s-dbg" % tree, "tri-F3-dbg",
             "run_m1_r7.py:37-38 (tri family, dbg)"),
            ("G2b", "d003plan", "plain", "plain", tree, "d003plan-%s-plain" % tree, "d003plan-F3-plain",
             "run_m2_r7.py:245-247 (d003plan family for non-G1 groups)"),
            ("G3", "d003plan", "plain", "plain", tree, "d003plan-%s-plain" % tree, "d003plan-F3-plain",
             "run_m2_r7.py:245-247"),
            ("G4", "d003plan", "plain", "plain", tree, "d003plan-%s-plain" % tree, "d003plan-F3-plain",
             "run_m2_r7.py:245-247"),
            ("G1", "d003", "plain", "plain", tree, "d003-%s-plain" % tree, "d003-F3-plain",
             "run_m2_r7.py:246 (d003 family for G1)"),
            ("G2c", "d003plan", "plain", "plain", tree, "d003plan-%s-plain" % tree, "d003plan-F3-plain",
             "run_m2_r7.py:245-247 (d003plan family for G2c)"),
            ("G5", "r6bstate", "dbg", "dbg", tree, "r6bstate-%s-dbg" % tree, "r6bstate-F3-dbg",
             "make_prereg_m3_r7.py (G5 from REGISTRY_S4_PRE_R6b_STATE_v2); DRIVERS_R7_M3.tsv"),
            ("G2a-seamF", "seamF", "plain", "seam plain", tree, "seam-seamF-%s" % tree, "seam-seamF-F3",
             "run_m2b_all_r7.py:112-116 (seam_driver_name), DRIVERS_R7_SEAM.tsv"),
            ("G2a-fmmret", "fmmret", "plain", "seam plain", tree, "seam-fmmret-%s" % tree, "seam-fmmret-F3",
             "run_m2b_all_r7.py:112-116 (seam_driver_name), DRIVERS_R7_SEAM.tsv"),
            ("CTRL_SEAM-seamF", "seamF", "plain", "seam plain", tree, "seam-seamF-%s" % tree, "seam-seamF-F3",
             "REGISTRY_S4_PRE_R7_M2_CTRL_SEAM.tsv (seamF rows); run_m2b_all_r7.py:112-116"),
            ("CTRL_SEAM-fmmret", "fmmret", "plain", "seam plain", tree, "seam-fmmret-%s" % tree, "seam-fmmret-F3",
             "REGISTRY_S4_PRE_R7_M2_CTRL_SEAM.tsv (fmmret rows); run_m2b_all_r7.py:112-116"),
            ("G6-seamF", "r6bseam-seamF", "dbg", "seam dbg", tree, "r6bseam-seamF-%s" % tree, "r6bseam-seamF-F3",
             "DRIVER_R6B_SEAM_R7.tsv / _F2.tsv; link_r6b_seam_r7.sh (G6 and G6c)"),
            ("G6-fmmret", "r6bseam-fmmret", "dbg", "seam dbg", tree, "r6bseam-fmmret-%s" % tree, "r6bseam-fmmret-F3",
             "DRIVER_R6B_SEAM_R7.tsv / _F2.tsv; link_r6b_seam_r7.sh (G6 and G6c)"),
        ]
    # the 22-row additions and the polygon group use drivers that R7 did not build (U142; S3R4 scripts)
    spec += [
        ("22-ROW-ADD", "init", "plain", "plain", "F3", None, "init-F3",
         "stage_s3r4c2/link_init_c2.sh (copied for R8, library F3 plain); registries/s3r4c3/R8_ADDITIONS_S3R4C3.tsv"),
        ("22-ROW-ADD-F2", "init", "plain", "plain", "F2", "init-F2 (S3R4 record)", "init-F2 (reused, U142)",
         "stage_s3r4c2/link_init_c2.sh (S3R4 F2 driver, reused read only)"),
        ("POLY-33", "polyinj", "plain", "plain", "F3", None, "polyinj-F3",
         "stage_s3r4c3/link_poly_inj_c3.sh (copied for R8, library F3 plain); U142"),
        ("POLY-33-F2", "polyinj", "plain", "plain", "F2", "polyinj-F2 (S3R4 record)", "polyinj-F2 (reused, U142)",
         "stage_s3r4c3/link_poly_inj_c3.sh (S3R4 F2 driver, reused read only)"),
        ("POLY-33-base", "poly", "plain", "plain", "F3", None, "poly-F3",
         "stage_s3r4c2/link_c2.sh kind poly (copied for R8, library F3 plain); U142"),
        ("POLY-33-base-F2", "poly", "plain", "plain", "F2", "poly-F2 (S3R4 record)", "poly-F2 (reused, U142)",
         "stage_s3r4c2/link_c2.sh kind poly (S3R4 F2 driver, reused read only)"),
    ]

    lines = ["# NEEDS_R8_M1a.tsv -- P05-S4 R8 M1a section 5.1.  Written by make_needs_r8m1.py (read only; no driver built or run).",
             "# r7_record: the R7 record name (directory of drivers_r7/).  f3_driver: the name M1b/M1c would use.",
             "# in_M0: YES if registries/s4r8/DRIVERS_R8.tsv holds the F3 driver of that name, NO otherwise.",
             "# R7 link command line numbers in safe_run.log: " + "; ".join(
                 "%s=%s" % (k, ",".join(str(x) for x in v) or "-") for k, v in sorted(link_lines.items())),
             "\t".join(["group", "driver_family", "mode", "library_kind", "tree", "r7_record", "r7_record_file",
                        "r7_lib_sha256", "r7_driver_sha256", "r7_driver_path", "f3_driver", "in_M0", "source"])]
    n_rows = 0
    n_missing_r7 = 0
    for grp, fam, mode, libkind, tree, rec_name, f3name, src in spec:
        if rec_name is None:
            rfile, rlib, rdrv, rpath = "-", "-", "-", "-"
        elif rec_name.endswith("(S3R4 record)"):
            rfile, rlib, rdrv, rpath = "S3R4 registry (not R7)", "-", "-", "-"
        else:
            rec = r7.get(rec_name)
            if rec is None:
                rfile, rlib, rdrv, rpath = "NOT_RECORDED", "-", "-", "-"
                n_missing_r7 += 1
            else:
                rfile, rlib, rdrv, rpath = rec[0], rec[1], rec[2], rec[3]
        in_m0 = "YES" if f3name in m0 else "NO"
        lines.append("\t".join([grp, fam, mode, libkind, tree, rec_name or "-", rfile, rlib, rdrv, rpath,
                                f3name, in_m0, src]))
        n_rows += 1
    text = "\n".join(lines) + "\n"
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write(text)
    print("NEEDS rows=%d r7_not_recorded=%d -> %s" % (n_rows, n_missing_r7, OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
