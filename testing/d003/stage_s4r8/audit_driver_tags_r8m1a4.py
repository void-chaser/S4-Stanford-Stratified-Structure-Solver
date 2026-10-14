#!/usr/bin/env python3
"""P05-S4 R8 M1a 续3a audit (r8m1a4audit): driver tag cross-check.  New file.

Read-only with respect to the repository: reads the driver tables, checks file existence and sha256,
and writes one TSV into the evidence directory given as the argument.

Purpose: confirm that every driver row in the authoritative driver tables names a file that exists and whose
sha256 equals the recorded value.  Column meaning is taken from the generator of each table (printf order),
or from the table header where the table has one.  Nothing is inferred from file names (U179).

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/audit_driver_tags_r8m1a4.py OUTDIR
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
REG_R7 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7")
REG_M1A = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")

# (table name, path, column list or None when the table has a header row, driver-path column, sha column)
# Headerless R7 tables: column order is the printf order of the generator named in the comment.
TABLES = [
    # link_drivers_s4r7.sh: printf driver, tree, mode, lib sha, driver sha, driver path
    ("DRIVERS_R7", os.path.join(REG_R7, "DRIVERS_R7.tsv"),
     ["driver", "tree", "mode", "lib_sha256", "driver_sha256", "driver_path"], "driver_path", "driver_sha256"),
    # link_seam_drivers_r7.sh: printf name, tree, lib sha, driver sha, library path (no driver path column)
    ("DRIVERS_R7_SEAM", os.path.join(REG_R7, "DRIVERS_R7_SEAM.tsv"),
     ["driver", "tree", "lib_sha256", "driver_sha256", "lib_path"], None, "driver_sha256"),
    # header row present
    ("DRIVERS_R7_M3", os.path.join(REG_R7, "DRIVERS_R7_M3.tsv"), None, "driver_path", "driver_sha256"),
    # header row present
    ("DRIVERS_R7_cont1", os.path.join(REG_R7, "DRIVERS_R7_cont1.tsv"), None, "driver_path", "driver_sha256"),
    # link_r6b_seam_r7.sh: printf name, lib sha, driver sha, library path (no driver path column)
    ("DRIVER_R6B_SEAM_R7", os.path.join(REG_R7, "DRIVER_R6B_SEAM_R7.tsv"),
     ["driver", "lib_sha256", "driver_sha256", "lib_path"], None, "driver_sha256"),
    # link_r6b_seam_r7_f2.sh: same printf layout as above
    ("DRIVER_R6B_SEAM_R7_F2", os.path.join(REG_R7, "DRIVER_R6B_SEAM_R7_F2.tsv"),
     ["driver", "lib_sha256", "driver_sha256", "lib_path"], None, "driver_sha256"),
    # header row present (driver_path column)
    ("DRIVERS_R8_M1a", os.path.join(REG_M1A, "DRIVERS_R8_M1a.tsv"), None, "driver_path", "driver_sha256"),
    # header row present; this table names its driver file in column "path" and its sha in "sha256_now"
    ("DRIVERS_R8_M1a_F2_REUSED", os.path.join(REG_M1A, "DRIVERS_R8_M1a_F2_REUSED.tsv"), None, "path", "sha256_now"),
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_rows(path, explicit_cols):
    """Return list of (lineno, dict).  Comment (#) and blank lines are skipped.

    explicit_cols is None when the first non-comment line is the header; otherwise every non-comment line is data
    with the given column names.  Column count must equal the column list length.
    """
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    header = explicit_cols
    rows = []
    for n, line in enumerate(lines, 1):
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        if header is None:
            header = cols
            continue
        if len(cols) != len(header):
            raise SystemExit("REFUSED: column count %d != %d at %s:%d" % (len(cols), len(header), path, n))
        rows.append((n, dict(zip(header, cols))))
    if header is None:
        raise SystemExit("REFUSED: no header or data in %s" % path)
    return header, rows


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: audit_driver_tags_r8m1a4.py OUTDIR")
    out_dir = argv[1]
    out_path = os.path.join(out_dir, "DRIVER_TAG_AUDIT_R8_M1a4.tsv")
    if os.path.exists(out_path):
        raise SystemExit("REFUSED: exists (U17): %s" % out_path)

    records = []
    for tname, tpath, cols, dcol, scol in TABLES:
        if not os.path.isfile(tpath):
            raise SystemExit("REFUSED: table missing: %s" % tpath)
        header, rows = read_rows(tpath, cols)
        if dcol is None:
            # library-only table: the driver is named by the "driver" name; no driver file is checked here
            for n, r in rows:
                records.append((tname, n, r["driver"], r.get("tree", "-"), "-", r["driver_sha256"], "-",
                                "NO_DRIVER_PATH_COLUMN", r["lib_path"]))
            continue
        for n, r in rows:
            dpath = r.get(dcol, "")
            rec_sha = r.get(scol, "")
            tag = r.get("driver", r.get("role", "-"))
            tree = r.get("tree", "-")
            mode = r.get("mode", "-")
            if not dpath or not os.path.isfile(dpath):
                status = "FILE_MISSING"
                file_sha = "-"
            else:
                file_sha = sha256_file(dpath)
                if not rec_sha:
                    status = "NO_RECORDED_SHA"
                elif rec_sha == file_sha:
                    status = "SHA_MATCH"
                else:
                    status = "SHA_DIFFERENT"
            records.append((tname, n, tag, tree, mode, rec_sha or "-", file_sha, status, dpath or "-"))

    with open(out_path, "x", encoding="utf-8") as fh:
        fh.write("table\tline\tdriver_tag\ttree\tmode\trecorded_driver_sha256\tfile_driver_sha256\tstatus\tdriver_path\n")
        for rec in records:
            fh.write("\t".join(str(x) for x in rec) + "\n")

    counts = {}
    for rec in records:
        counts[rec[7]] = counts.get(rec[7], 0) + 1
    print("DRIVER_TAG_AUDIT rows=%d status_counts=%s" % (len(records), sorted(counts.items())))
    bad = [r for r in records if r[7] in ("FILE_MISSING", "SHA_DIFFERENT", "NO_RECORDED_SHA")]
    if bad:
        print("DRIVER_TAG_AUDIT BAD: %d rows" % len(bad))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
