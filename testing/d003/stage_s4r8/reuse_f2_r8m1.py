#!/usr/bin/env python3
"""P05-S4 R8 M1a, section 5.3 (U126): verify the F2 drivers and the F2 library that M1b/M1c reuse.  New file.

No driver is linked here.  For each F2 driver that the M1b/M1c runners will use, the sha256 of the file on disk is
compared with the sha256 recorded earlier:
  - R7 records: registries/s4r7/DRIVERS_R7.tsv (F2 rows), DRIVERS_R7_cont1.tsv (F2 tri), DRIVERS_R7_SEAM.tsv (F2 seam),
    DRIVER_R6B_SEAM_R7_F2.tsv (F2 G6);
  - S3R4 records: registries/s3r4c5/BINARIES_C3.tsv (init-F2 SAME record 29bb377c..., polyinj-F2 FIRST_RECORD 237bbefc...,
    F2-plain-lib c63d180a...); poly-F2 has no sha record in registries/s3r4c2 (FIRST_RECORD, E8 entry).
Each row is SAME (the file equals the record), DIFFERENT (it does not), or FIRST_RECORD (no record exists; the
current value is written and recorded).  A DIFFERENT row does not stop the script; it is reported.
Output (new file, refused if it exists): $EV/DRIVERS_R8_M1a_F2_REUSED.tsv
Usage (through safe_run):  python3 -I -B testing/d003/stage_s4r8/reuse_f2_r8m1.py
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
REG7 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7")
REG3C5 = os.path.join(REPO, "checkpoints", "p05", "registries", "s3r4c5")
EVR7 = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r7")
EV3C2 = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s3r4c2")
EV3C3 = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s3r4c3")
EV3 = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s3r4")
OUT = os.path.join(EV, "DRIVERS_R8_M1a_F2_REUSED.tsv")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def table_rows(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            rows.append(line.split("\t"))
    return rows


def r7_f2_records():
    """(name, path, recorded driver sha256, record source) for the R7 F2 drivers that M1b/M1c use."""
    out = []
    for r in table_rows(os.path.join(REG7, "DRIVERS_R7.tsv")):
        if r[0] == "driver" or r[1] != "F2":
            continue
        name = "%s-F2-%s" % (r[0], r[2])
        out.append((name, r[5], r[4], "DRIVERS_R7.tsv"))
    for r in table_rows(os.path.join(REG7, "DRIVERS_R7_cont1.tsv")):
        if r[0] != "F2":
            continue
        out.append(("tri-F2-dbg", r[4], r[3], "DRIVERS_R7_cont1.tsv"))
    for r in table_rows(os.path.join(REG7, "DRIVERS_R7_SEAM.tsv")):
        if r[1] != "F2":
            continue
        drv = os.path.join(EVR7, "drivers_r7", "seam-" + r[0], "driver")
        out.append(("seam-%s" % r[0], drv, r[3], "DRIVERS_R7_SEAM.tsv"))
    for r in table_rows(os.path.join(REG7, "DRIVER_R6B_SEAM_R7_F2.tsv")):
        drv = os.path.join(EVR7, "drivers_r7", r[0], "driver")
        out.append((r[0], drv, r[2], "DRIVER_R6B_SEAM_R7_F2.tsv"))
    return out


def s3r4_f2_records():
    """S3R4 F2 drivers reused by the 22-row additions and the polygon group (read only)."""
    return [
        ("init-F2", os.path.join(EV3C2, "drivers", "init-F2", "driver"),
         "29bb377c4eb5e1d393d2916d2ad9a05d9ecf781fc4cc709dd87332f8904d1158", "BINARIES_C3.tsv (SAME record)"),
        ("polyinj-F2", os.path.join(EV3C3, "drivers", "polyinj-F2", "driver"),
         "237bbefc169524db939a64dce091207495f5d844c4e5e5b68d730299a80f7559", "BINARIES_C3.tsv (FIRST_RECORD)"),
        ("poly-F2", os.path.join(EV3C2, "drivers", "poly-F2", "driver"),
         None, "no sha record in registries/s3r4c2 (FIRST_RECORD; E8)"),
    ]


def main(argv):
    if len(argv) != 1:
        raise SystemExit("usage: reuse_f2_r8m1.py  (no arguments)")
    if os.path.exists(OUT):
        raise SystemExit("REFUSED: exists (U17): %s" % OUT)
    rows = []
    for name, path, rec_sha, src in r7_f2_records() + s3r4_f2_records():
        if not os.path.isfile(path):
            rows.append([name, path, "-", rec_sha or "-", "MISSING", src])
            continue
        cur = sha256_file(path)
        if rec_sha is None:
            verdict = "FIRST_RECORD"
        else:
            verdict = "SAME" if cur == rec_sha else "DIFFERENT"
        rows.append([name, path, cur, rec_sha or "-", verdict, src])
    # the F2 plain library used by the R7 F2 drivers (R7 record c63d180a... ; S3R4 record BINARIES_C3 c63d180a...)
    lib = os.path.join(EV3, "build", "F2-plain", "build", "libS4.a")
    if os.path.isfile(lib):
        cur = sha256_file(lib)
        rec = "c63d180aff6c5b5e443faefeb6de44abce430dafbb846db434ac15da85fbc185"
        rows.append(["F2-plain-lib (S3R4 build)", lib, cur, rec, "SAME" if cur == rec else "DIFFERENT",
                     "BINARIES_C3.tsv (SAME record) and DRIVERS_R7.tsv lib column"])
    else:
        rows.append(["F2-plain-lib (S3R4 build)", lib, "-", "-", "MISSING", "-"])
    lines = ["# DRIVERS_R8_M1a_F2_REUSED.tsv -- P05-S4 R8 M1a section 5.3 (U126).  No F2 driver is linked; files read only.",
             "# verdict: SAME (file equals the record), DIFFERENT (does not; recorded, not a stop), FIRST_RECORD (no record; E8), MISSING.",
             "\t".join(["driver", "path", "sha256_now", "sha256_record", "verdict", "record_source"])]
    for r in rows:
        lines.append("\t".join(r))
    counts = {}
    for r in rows:
        counts[r[4]] = counts.get(r[4], 0) + 1
    lines.append("# counts: " + ", ".join("%s=%d" % (k, counts[k]) for k in sorted(counts)))
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("F2 reuse rows=%d counts=%s -> %s" % (len(rows), ", ".join("%s=%d" % (k, counts[k]) for k in sorted(counts)), OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
