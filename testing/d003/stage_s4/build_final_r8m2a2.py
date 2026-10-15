#!/usr/bin/env python3
# build_final_r8m2a2.py -- P05-S4 R8 M2a2 CONT1 section 3: BUILD_FINAL table.
# Reads BUILD_R8_M2a2_R3.tsv (the final build table; R1 and R2 are superseded, kept) and recomputes the sha256 of every
# artifact on disk.  A record that does not match the disk is STALE and must not enter the prereg.
# Output: $EV/BUILD_FINAL_R8_M2a2.tsv   columns: artifact, path, rc_recorded, sha256_recorded, sha256_disk, status, utc
import hashlib
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
SRC = os.path.join(EV, "BUILD_R8_M2a2_R3.tsv")
OUT = os.path.join(EV, "BUILD_FINAL_R8_M2a2.tsv")


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if os.path.exists(OUT):
        print("build_final_r8m2a2: REFUSED exists (U17)")
        return 2
    rows = []
    with open(SRC, encoding="utf-8") as fh:
        raw = [l.rstrip("\n") for l in fh if l.strip()]
    # BUILD_R8_M2a2_R3.tsv has no column-name row: its column list is in the first comment line
    # ("# BUILD_R8_M2a2_R3 -- columns: artifact<TAB>path<TAB>...").  The header is parsed from that comment.
    head_comment = next(l for l in raw if l.startswith("#") and "columns:" in l)
    head = head_comment.split("columns:", 1)[1].strip().split("\t")
    head = [h.strip() for h in head]
    recs = [dict(zip(head, l.split("\t"))) for l in raw if not l.startswith("#")]
    counts = {"OK": 0, "STALE": 0, "MISSING": 0, "BUILD_FAILED": 0}
    for r in recs:
        art = r["artifact"]
        path = os.path.join(REPO, r["path"])
        rc = r["rc"]
        if rc != "0":
            status = "BUILD_FAILED"
            disk = "-"
        elif not os.path.exists(path):
            status = "MISSING"
            disk = "-"
        else:
            disk = sha256_file(path)
            status = "OK" if disk == r["sha256"] else "STALE"
        counts[status] += 1
        rows.append([art, r["path"], rc, r["sha256"], disk, status, r.get("utc", "-")])
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("# BUILD_FINAL_R8_M2a2 -- recomputed sha256 of the final build table BUILD_R8_M2a2_R3.tsv (CONT1 section 3)\n")
        fh.write("artifact\tpath\trc_recorded\tsha256_recorded\tsha256_disk\tstatus\tutc\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
        fh.write("# ROWS=%d OK=%d STALE=%d MISSING=%d BUILD_FAILED=%d\n" %
                 (len(rows), counts["OK"], counts["STALE"], counts["MISSING"], counts["BUILD_FAILED"]))
    print("build_final_r8m2a2: rows=%d OK=%d STALE=%d MISSING=%d BUILD_FAILED=%d" %
          (len(rows), counts["OK"], counts["STALE"], counts["MISSING"], counts["BUILD_FAILED"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
