#!/usr/bin/env python3
# r6c_prereg_v2.py -- P05-S4 R6c-2 (new file).  Builds the v2 pre-registration from v1 and checks v1/v2 line by line.
#
# v1 (REGISTRY_S4_PRE_R6b_STATE.tsv, sha256 f2523d14...c358) is read only and never written.
# v2 differs from v1 in exactly two ways (ERRATA_6c, U14):
#   (1) the definition of I4 is replaced by I4' (the header states the new definition);
#   (2) one new column k_before is inserted directly after retry_call (inj_call 1 -> 0; inj_call 2 -> 2).
# Every other data cell of every row is copied from v1 unchanged.  The point set of v2 equals the point set of v1.
#
# The script refuses to overwrite any existing output file (U17).
#
# Usage: python3 -I -B testing/d003/stage_s4/r6c_prereg_v2.py V1_TSV OUT_V2_TSV OUT_DIFF_TXT OUT_SHA256 OUT_TIMESTAMP
import datetime
import hashlib
import os
import sys

V1_EXPECT_SHA = "f2523d146e7e5adbf80cf99fdc35ba7b64b0e22ac5e4cc1409e97203cba0c358"
NEW_COL = "k_before"
INSERT_AFTER = "retry_call"
K_BEFORE = {"1": "0", "2": "2"}

HEADER_V2_COMMENT = [
    "# REGISTRY_S4_PRE_R6b_STATE_v2.tsv -- P05-S4 R6c-2 pre-registration v2 (S3-4b state judgement, 177 judgeable points, tree F).",
    "# v1 (REGISTRY_S4_PRE_R6b_STATE.tsv, sha256 f2523d146e7e5adbf80cf99fdc35ba7b64b0e22ac5e4cc1409e97203cba0c358) is VOID ONLY for I4.",
    "# v1 is void only in its I4 definition and in having no k_before column.  Its other columns, expected values and status are UNCHANGED",
    "# in v2.  Reason: ERRATA_6c U14 (user ruling; planner error in the R6b brief).  Record: ERRATA_6c, section 'U14'.",
    "# Written BEFORE any R6c state run.  Map: MAP_R6b_ALL.tsv (202 points; 25 seam points UNJUDGED, ERRATA_6b E6b-7; not in this table).",
    "# Snapshot indices by inj_call (U13, unchanged): inj_call 1 -> k_fail 1, k_preretry 2, k_retry 3, retry_call 2;",
    "#                                                inj_call 2 -> k_fail 3, k_preretry 3, k_retry 4, retry_call 3.",
    "# k_before (new, U14): the snapshot before the injected call:  inj_call 1 -> 0;  inj_call 2 -> 2.",
    "# Invariants (v2):",
    "#   I1: failed layer modes==NULL at k_fail (unchanged from v1)",
    "#   I2: other layers at k_fail: q hash, control installed, not re-entered (E6-8 option 1; unchanged from v1)",
    "#   I3: field_cache subset of control at k_fail (PolBasis modes only; else N/A; unchanged from v1)",
    "#   I4': (a) solved[req]@k_fail == solved[req]@k_before, i.e. the failing call does NOT change solved[req] from 0 to 1;",
    "#        (b) if solved[req]@k_fail == 1 then at k_fail modes==NULL for the request layer (if L->copy>=0: modes of the copied layer),",
    "#            so that S4.cpp:1805 forces recomputation.  req is read by gdb (R6CREQ lines), not assumed.  (U14; ERRATA_6c)",
    "#   I5: retry enters ComputeLayerModes only for modes==NULL layers at k_pre; each at most once; retry rc==0 (unchanged from v1)",
    "#   I6: retry output byte-identical to control call of the same number (unchanged from v1)",
    "#   I7: DEFERRED (U9).",
    "# Expected (status INFLUENCED): every applicable invariant HOLD (unchanged from v1).  Status is NOT BLIND.",
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def refuse_existing(*paths):
    for p in paths:
        if os.path.exists(p):
            raise SystemExit("REFUSED: output already exists (U17, never overwritten): %s" % p)


def read_table(path):
    """Return (header, rows) where each row is a list of fields.  Comment lines are skipped."""
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
            if len(f) != len(header):
                raise SystemExit("REFUSED: %s: row has %d fields, header has %d" % (path, len(f), len(header)))
            rows.append(f)
    return header, rows


def build_v2(header_v1, rows_v1):
    idx = header_v1.index(INSERT_AFTER)
    header_v2 = header_v1[:idx + 1] + [NEW_COL] + header_v1[idx + 1:]
    rows_v2 = []
    for r in rows_v1:
        d = dict(zip(header_v1, r))
        if d["inj_call"] not in K_BEFORE:
            raise SystemExit("REFUSED: inj_call %r has no k_before rule" % d["inj_call"])
        rows_v2.append(r[:idx + 1] + [K_BEFORE[d["inj_call"]]] + r[idx + 1:])
    return header_v2, rows_v2


def diff(header_v1, rows_v1, header_v2, rows_v2):
    """Line-by-line comparison.  Returns (report lines, n_mismatch)."""
    out = []
    n_mis = 0
    out.append("v1 rows: %d ; v2 rows: %d" % (len(rows_v1), len(rows_v2)))
    if len(rows_v1) != 177 or len(rows_v2) != 177:
        n_mis += 1
        out.append("MISMATCH: expected 177 rows in both files")
    ids1 = [r[0] for r in rows_v1]
    ids2 = [r[0] for r in rows_v2]
    same_set = set(ids1) == set(ids2) and len(ids1) == len(ids2)
    out.append("point-id set equal (order preserved): %s" % ("OK" if ids1 == ids2 else ("OK as set only" if same_set else "MISMATCH")))
    if not same_set:
        n_mis += 1
    expected_v2_header = header_v1[:header_v1.index(INSERT_AFTER) + 1] + [NEW_COL] + header_v1[header_v1.index(INSERT_AFTER) + 1:]
    hdr_ok = header_v2 == expected_v2_header
    out.append("v2 header == v1 header + %s after %s: %s" % (NEW_COL, INSERT_AFTER, "OK" if hdr_ok else "MISMATCH"))
    if not hdr_ok:
        n_mis += 1
    cells_checked = 0
    cells_diff_expected = 0
    cells_diff_unexpected = 0
    for r1, r2 in zip(rows_v1, rows_v2):
        if len(r2) != len(r1) + 1:
            n_mis += 1
            continue
        idx = header_v1.index(INSERT_AFTER)
        # v2 has the new column at idx+1; compare the others column by column
        mapped = r2[:idx + 1] + r2[idx + 2:]
        for c, (a, b) in enumerate(zip(r1, mapped)):
            cells_checked += 1
            if a != b:
                cells_diff_unexpected += 1
                n_mis += 1
                out.append("MISMATCH point %s column %s: v1=%r v2=%r" % (r1[0], header_v1[c], a, b))
        kb = r2[idx + 1]
        dd = dict(zip(header_v1, r1))
        if kb != K_BEFORE[dd["inj_call"]]:
            n_mis += 1
            out.append("MISMATCH point %s k_before=%r expected %r" % (r1[0], kb, K_BEFORE[dd["inj_call"]]))
        cells_diff_expected += 1
    out.append("cells compared (v1 columns, all rows): %d ; unexpected differences: %d" % (cells_checked, cells_diff_unexpected))
    out.append("k_before column checked for all rows: %d" % cells_diff_expected)
    out.append("RESULT: %s (mismatches=%d)" % ("PASS" if n_mis == 0 else "FAIL", n_mis))
    out.append("Expected differences only: header comment (I4 definition), new column %s.  Data rows: every v1 cell identical." % NEW_COL)
    return out, n_mis


def main(argv):
    if len(argv) != 6:
        raise SystemExit("usage: r6c_prereg_v2.py V1_TSV OUT_V2_TSV OUT_DIFF_TXT OUT_SHA256 OUT_TIMESTAMP")
    v1, out_v2, out_diff, out_sha, out_ts = argv[1:6]
    refuse_existing(out_v2, out_diff, out_sha, out_ts)
    v1_sha = sha256_file(v1)
    if v1_sha != V1_EXPECT_SHA:
        raise SystemExit("REFUSED: v1 sha256 %s != expected %s" % (v1_sha, V1_EXPECT_SHA))
    header_v1, rows_v1 = read_table(v1)
    if len(rows_v1) != 177:
        raise SystemExit("REFUSED: v1 has %d rows, expected 177" % len(rows_v1))
    header_v2, rows_v2 = build_v2(header_v1, rows_v1)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(out_v2, "w", encoding="utf-8") as fh:
        for c in HEADER_V2_COMMENT:
            fh.write(c + "\n")
        fh.write("# UTC written: %s\n" % ts)
        fh.write("\t".join(header_v2) + "\n")
        for r in rows_v2:
            fh.write("\t".join(r) + "\n")
    v2_sha = sha256_file(out_v2)
    with open(out_sha, "w", encoding="utf-8") as fh:
        fh.write("%s  REGISTRY_S4_PRE_R6b_STATE_v2.tsv\n" % v2_sha)
    with open(out_ts, "w", encoding="utf-8") as fh:
        fh.write("%s\n" % ts)
    # Re-read the written v2 file from disk and compare it with v1 (not with the in-memory copy).
    h2, r2 = read_table(out_v2)
    lines, n_mis = diff(header_v1, rows_v1, h2, r2)
    lines.insert(0, "# PREREG_V1_V2_DIFF -- written by r6c_prereg_v2.py (line-by-line check, computed by the script)")
    lines.insert(1, "# v1 sha256 (checked before reading): %s" % v1_sha)
    lines.insert(2, "# v2 sha256 (of the written file): %s ; UTC %s" % (v2_sha, ts))
    with open(out_diff, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("v2 written: sha256=%s ts=%s ; diff RESULT mismatches=%d" % (v2_sha, ts, n_mis))
    return 0 if n_mis == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
