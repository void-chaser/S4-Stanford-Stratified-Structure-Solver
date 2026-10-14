#!/usr/bin/env python3
"""P05-S4 R8 M1a, section 5.4: summary of every F3 driver and library of this round, with the comparison to history.  New file.

Reads only (no driver is built or run):
  - registries/s4r8/DRIVERS_R8.tsv (M0): F3 plain and seam plain drivers and libraries;
  - $EV/DRIVERS_R8_M1a_LINKED.tsv (this round): r6dnv1-F3-plain, d003-F3-dbg, d003plan-F3-dbg, r6bstate-F3-dbg, tri-F3-dbg;
  - $EV/DRIVER_R6B_SEAM_R8_M1a.tsv (this round): r6bseam-seamF-F3, r6bseam-fmmret-F3;
  - $EV/DRIVERS_S3R4_R8_M1a_F3.tsv (this round): init-F3, polyinj-F3, poly-F3;
  - $EV/DRIVERS_R8_M1a_F2_REUSED.tsv (section 5.3): the F2 drivers (for the record only);
  - the S3R4 records registries/s3r4c5/BINARIES_C3.tsv (libraries and drivers already recorded there).
Output (new file, refused if it exists): $EV/DRIVERS_R8_M1a.tsv
Columns: driver, tree, mode, lib_sha256, driver_sha256, lib_path, driver_path, link_script, history_compare, history_note.
history_compare: SAME (equal to a recorded value), DIFFERENT (recorded, not equal; reported, not a stop), FIRST_RECORD (no
recorded value to compare with).  The S3R4 record of a driver is only used as a comparison value when BINARIES_C3 gives one.
Usage (through safe_run):  python3 -I -B testing/d003/stage_s4r8/make_drivers_summary_r8m1.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
REG8 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8")
REG3C5 = os.path.join(REPO, "checkpoints", "p05", "registries", "s3r4c5")
OUT = os.path.join(EV, "DRIVERS_R8_M1a.tsv")

# S3R4 F3 library records (BINARIES_C3.tsv): name -> sha256 (FIRST_RECORD rows give no comparison value)
S3R4_LIB = {"F3-plain-lib": "abbc01c78f0a422f3494556bb43e212e397fbbf49d03370132ae45e2c268e5de",
            "F3-dbg-lib": "10ea03b37ccdb6f256bd65904763520e6570e297ba2060416f28253e1f065afa"}


def table_rows(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            rows.append(line.split("\t"))
    return rows


def s3r4_binaries():
    """driver name -> (sha256, compare) from BINARIES_C3.tsv (the S3R4 records of the drivers used here)."""
    out = {}
    for r in table_rows(os.path.join(REG3C5, "BINARIES_C3.tsv")):
        if r[0] == "name":
            continue
        out[r[0]] = (r[2], r[3])
    return out


def main(argv):
    if len(argv) != 1:
        raise SystemExit("usage: make_drivers_summary_r8m1.py  (no arguments)")
    if os.path.exists(OUT):
        raise SystemExit("REFUSED: exists (U17): %s" % OUT)
    s3 = s3r4_binaries()
    rows = []

    # M0 drivers (F3 plain and seam plain): DRIVERS_R8.tsv columns driver, tree, mode, lib_sha256, driver_sha256, lib_path, driver_path
    for r in table_rows(os.path.join(REG8, "DRIVERS_R8.tsv")):
        if r[0] == "driver":
            continue
        name, tree, mode, lsha, dsha, lpath, dpath = r[0], r[1], r[2], r[3], r[4], r[5], r[6]
        hist = "FIRST_RECORD"
        note = "M0 driver (DRIVERS_R8.tsv)"
        if mode == "plain" and tree == "F3" and lsha == S3R4_LIB["F3-plain-lib"]:
            note = "F3 plain library equals the S3R4 record abbc01c7 (SAME); driver has no S3R4 record"
        rows.append([name, tree, mode, lsha, dsha, lpath, dpath, "M0 build (seam_r8.sh / build_s4r8.sh / link_drivers_r8.sh)",
                     hist, note])

    # this round's links (DRIVERS_R8_M1a_LINKED.tsv): name, tree, mode, lib sha, driver sha, library path
    for r in table_rows(os.path.join(EV, "DRIVERS_R8_M1a_LINKED.tsv")):
        name, tree, mode, lsha, dsha, lpath = r[0], r[1], r[2], r[3], r[4], r[5]
        dpath = os.path.join(EV, "drivers_r8m1", name, "driver")
        hist, note = "FIRST_RECORD", "linked in M1a (link_drivers_r8m1.sh); no R8 or S3R4 driver record"
        if mode == "dbg" and lsha == "56f72c5882d4293bbb2d45a272d7c7727e401085b900854b1f49b851effd897a":
            note = "F3 dbg library (M0 build, sha 56f72c58); S3R4 record 10ea03b3 is DIFFERENT (E8-9; strip equivalence shown in M1a)"
            hist = "DIFFERENT_LIBRARY_ONLY"
        rows.append([name, tree, mode, lsha, dsha, lpath, dpath, "link_drivers_r8m1.sh", hist, note])

    # seam dbg drivers (DRIVER_R6B_SEAM_R8_M1a.tsv): name, lib_sha256, driver_sha256, library_path
    for r in table_rows(os.path.join(EV, "DRIVER_R6B_SEAM_R8_M1a.tsv")):
        name, lsha, dsha, lpath = r[0], r[1], r[2], r[3]
        dpath = os.path.join(EV, "drivers_r8m1", name, "driver")
        rows.append([name, "F3", "dbg", lsha, dsha, lpath, dpath, "link_r6b_seam_r8m1.sh", "FIRST_RECORD",
                     "F3 seam debug library built in M1a (build_seam_r8m1.sh); no R8 or S3R4 driver record"])

    # S3R4-style F3 drivers (DRIVERS_S3R4_R8_M1a_F3.tsv): name, lib_sha256, driver_sha256, library_path
    for r in table_rows(os.path.join(EV, "DRIVERS_S3R4_R8_M1a_F3.tsv")):
        name, lsha, dsha, lpath = r[0], r[1], r[2], r[3]
        dpath = os.path.join(EV, "drivers_r8m1", name, "driver")
        rec = s3.get(name + "-driver")
        if rec is None:
            hist, note = "FIRST_RECORD", "no S3R4 record for the F3 driver"
        else:
            sha_rec, cmp_rec = rec
            if cmp_rec == "FIRST_RECORD":
                hist = "SAME" if dsha == sha_rec else "DIFFERENT"
                note = "S3R4 BINARIES_C3 lists %s as FIRST_RECORD with sha %s; compared to that recorded value" % (name, sha_rec[:8])
            else:
                hist = "SAME" if dsha == sha_rec else "DIFFERENT"
                note = "S3R4 BINARIES_C3 record (%s) compared" % cmp_rec
        rows.append([name, "F3", "plain", lsha, dsha, lpath, dpath, "link_s3r4_r8m1.sh (copy of S3R4 link scripts)", hist, note])

    # F2 drivers reused (DRIVERS_R8_M1a_F2_REUSED.tsv): verdict from section 5.3, no link
    for r in table_rows(os.path.join(EV, "DRIVERS_R8_M1a_F2_REUSED.tsv")):
        if r[0] == "driver":
            continue
        name, path, cur, rec, verdict, src = r[0], r[1], r[2], r[3], r[4], r[5]
        if name.startswith("F2-plain-lib"):
            continue
        rows.append([name, "F2", "reused", "-", cur, "-", path, "reused read only (R7 or S3R4 link)", verdict, src])

    lines = ["# DRIVERS_R8_M1a.tsv -- P05-S4 R8 M1a section 5.4.  Summary of the drivers and libraries of this round and of the reused F2 drivers.",
             "# No driver is run here.  history_compare: SAME, DIFFERENT (recorded, not a stop) or FIRST_RECORD (no value to compare with).",
             "\t".join(["driver", "tree", "mode", "lib_sha256", "driver_sha256", "lib_path", "driver_path", "link_script",
                        "history_compare", "history_note"])]
    for r in rows:
        lines.append("\t".join(r))
    counts = {}
    for r in rows:
        counts[r[8]] = counts.get(r[8], 0) + 1
    lines.append("# counts: " + ", ".join("%s=%d" % (k, counts[k]) for k in sorted(counts)))
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("DRIVERS summary rows=%d counts=%s -> %s" % (len(rows), ", ".join("%s=%d" % (k, counts[k]) for k in sorted(counts)), OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
