#!/usr/bin/env python3
# r6c_seam_prereg.py -- P05-S4 R6c-2 seam pre-registration (new file).  Written BEFORE any seam state run (brief 4.4).
#
# Input : SEAM_INJCALL_R6c.tsv (inj_call measured under gdb; the 25 seam points, tree F).
# Output: REGISTRY_S4_PRE_R6c_SEAM.tsv (25 rows), a sha256 file and a UTC timestamp file.  Refuses to overwrite (U17).
#
# Rules (the same invariant set as REGISTRY_S4_PRE_R6b_STATE_v2.tsv, ERRATA_6c U14 for I4'):
#   inj_call 1 (all 25 measured):  k_before 0, k_fail 1, k_pre 2, k_retry 3, retry_call 2.
#   I1..I6 as in v2; I7 DEFERRED (U9).  Applicable invariants: I1, I2, I4, I5, I6, plus I3 for PolBasis modes (jones, nv, vl).
#   Expected: HOLD (all applicable).  Status INFLUENCED (the seam points were run for equivalence and inj_call before this
#   file; the state invariants have not been run for them).
# The script refuses any inj_call other than 1 (STOP: a different index rule would be needed).
#
# Usage: python3 -I -B testing/d003/stage_s4/r6c_seam_prereg.py SEAM_INJCALL OUT_TSV OUT_SHA256 OUT_TS
import datetime
import hashlib
import os
import sys

POLBASIS = {"jones", "nv", "vl", "fftjones", "fftnv", "fftvl"}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv):
    if len(argv) != 5:
        raise SystemExit("usage: r6c_seam_prereg.py SEAM_INJCALL OUT_TSV OUT_SHA256 OUT_TS")
    src, out, out_sha, out_ts = argv[1:5]
    for p in (out, out_sha, out_ts):
        if os.path.exists(p):
            raise SystemExit("REFUSED: exists, never overwritten (U17): %s" % p)
    rows = []
    header = None
    with open(src, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                header = f
                continue
            rows.append(dict(zip(header, f)))
    if len(rows) != 25:
        raise SystemExit("REFUSED: expected 25 seam rows, got %d" % len(rows))
    for r in rows:
        if r["inj_call"] != "1":
            raise SystemExit("STOP: inj_call %r for %s; a different snapshot rule is needed" % (r["inj_call"], r["point_id"]))
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cols = ["point_id", "library", "mode", "request", "route", "inj_call", "k_before", "k_fail", "k_preretry", "k_retry",
            "retry_call", "applicable_invariants", "expected", "status"]
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# REGISTRY_S4_PRE_R6c_SEAM.tsv -- P05-S4 R6c-2 seam pre-registration (25 points, tree F, state invariants).\n")
        fh.write("# Written BEFORE any seam state run (brief 4.4).  inj_call measured under gdb (SEAM_INJCALL_R6c.tsv): all 25 = 1.\n")
        fh.write("# Snapshot indices (U13, inj_call 1): k_before 0, k_fail 1, k_pre 2, k_retry 3, retry_call 2.\n")
        fh.write("# Invariants: I1..I6 as REGISTRY_S4_PRE_R6b_STATE_v2.tsv; I4 is I4' (U14).  I7 DEFERRED (U9).\n")
        fh.write("# Expected HOLD for every applicable invariant.  Status INFLUENCED (equivalence and inj_call were run before this file).\n")
        fh.write("# UTC written: %s\n" % ts)
        fh.write("\t".join(cols) + "\n")
        for r in rows:
            mode = r["mode"]
            inv = ["I1", "I2", "I4", "I5", "I6"]
            if mode in POLBASIS:
                inv.insert(2, "I3")
            fh.write("\t".join([r["point_id"], r["library"], mode, r["request"], "once", "1", "0", "1", "2", "3", "2",
                                ",".join(inv), "HOLD(all applicable)", "INFLUENCED"]) + "\n")
    s = sha256_file(out)
    with open(out_sha, "w", encoding="utf-8") as fh:
        fh.write("%s  REGISTRY_S4_PRE_R6c_SEAM.tsv\n" % s)
    with open(out_ts, "w", encoding="utf-8") as fh:
        fh.write("%s\n" % ts)
    print("seam prereg rows=%d sha256=%s ts=%s" % (len(rows), s, ts))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
