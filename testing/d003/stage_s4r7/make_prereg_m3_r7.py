#!/usr/bin/env python3
# make_prereg_m3_r7.py -- P05-S4 R7 cont9 (M3, U80-U85): pre-registration of the G5/G6 state expectations on F and F2 (new file).
#
# The expectations are copied MECHANICALLY from the historical R6c pre-registration files (sha256 recorded in the header):
#   G5 : registries/s4r6c/REGISTRY_S4_PRE_R6b_STATE_v2.tsv   (177 rows; columns point_id, applicable_invariants, expected, status)
#   G6 : registries/s4r6c/REGISTRY_S4_PRE_R6c_SEAM.tsv          (25 rows)
#   G6c: registries/s4r6c/REGISTRY_S4_PRE_R6c_SEAM_CONTROL.tsv  (18 rows; control_id, library, mode, route)
# Each point is written twice: tree F (m3f1 baseline) and tree F2 (m3r1), with the same expectation (U82).
# No expectation is derived by this script; it only copies and checks counts.  The exception list (U82, U85) is written empty
# and is checked to be empty: the count of exceptions is 0 by construction (U85 (a)-(d)).  A non-empty list would stop this script.
#
# Usage: python3 -I -B make_prereg_m3_r7.py REPO OUT_DIR   (writes OUT_DIR/REGISTRY_S4_PRE_R7_M3.tsv; refuses to overwrite)
import hashlib
import os
import sys
import time

REG = "checkpoints/p05/registries/s4r6c/"
SRC = {
    "G5": REG + "REGISTRY_S4_PRE_R6b_STATE_v2.tsv",
    "G6": REG + "REGISTRY_S4_PRE_R6c_SEAM.tsv",
    "G6c": REG + "REGISTRY_S4_PRE_R6c_SEAM_CONTROL.tsv",
}
EXPECTED_ROWS = {"G5": 177, "G6": 25, "G6c": 18}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def read_table(path):
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
                raise SystemExit("REFUSED: %s: %d fields, header %d" % (path, len(f), len(header)))
            rows.append(dict(zip(header, f)))
    return rows


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: make_prereg_m3_r7.py REPO OUT_DIR")
    repo, out_dir = argv[1], argv[2]
    out = os.path.join(out_dir, "REGISTRY_S4_PRE_R7_M3.tsv")
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists, never overwritten (U17): %s" % out)
    hashes = {}
    g5 = read_table(os.path.join(repo, SRC["G5"]))
    g6 = read_table(os.path.join(repo, SRC["G6"]))
    g6c = read_table(os.path.join(repo, SRC["G6c"]))
    for k, rows in (("G5", g5), ("G6", g6), ("G6c", g6c)):
        if len(rows) != EXPECTED_ROWS[k]:
            raise SystemExit("REFUSED: %s rows %d != %d" % (k, len(rows), EXPECTED_ROWS[k]))
        hashes[k] = sha256(os.path.join(repo, SRC[k]))
    # exception check (U82/U85): any point whose expected is not HOLD(all applicable) and not INFLUENCED control stops the script
    for r in g5 + g6:
        if r["expected"] != "HOLD(all applicable)":
            raise SystemExit("STOP: unexpected expected %r for %s" % (r["expected"], r.get("point_id")))
    exceptions = []  # U85: constructed to be empty; a point would be listed here with a [source] basis
    if exceptions:
        raise SystemExit("STOP: exceptions listed: %r" % exceptions)

    utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    cols = ["group", "point_id", "tree", "library", "mode", "route", "request", "inj_call", "k_before", "k_fail",
            "k_preretry", "k_retry", "retry_call", "applicable_invariants", "expected", "status", "source_file"]
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# REGISTRY_S4_PRE_R7_M3.tsv -- P05-S4 R7 cont9 (M3) pre-registration of the G5/G6 state expectations, trees F and F2.\n")
        fh.write("# Written BEFORE any M3 run (cont9 section 2.3).  UTC %s.\n" % utc)
        fh.write("# Sources (copied mechanically; sha256 of each source):\n")
        for k in ("G5", "G6", "G6c"):
            fh.write("#   %s  %s  sha256 %s\n" % (k, SRC[k], hashes[k]))
        fh.write("# Expectation rule (U82): F2 expectation = historical R6c judgement on F, point by point; I1-I6; I7 DEFERRED (U9).\n")
        fh.write("# Exception rule (U82, U85): a point whose failure path passes the RNV1 window (pattern_generate_flow_field) must be listed\n")
        fh.write("#   here before any run, with a [source] basis.  Basis for the count 0 (U85):\n")
        fh.write("#   (a) the 177 points use only the requests exec, plan, plancall:K:M and s4malloc (RESULTS_R6c_STATE.tsv, request column);\n")
        fh.write("#   (b) exec is injected at entry of __wrap__Z13fft_plan_execP12tag_fft_plan (inject_r4_plan.cpp:602-612), returning 1 before the\n")
        fh.write("#       real execution; it does not use malloc and does not depend on arm.  plan and plancall set arm=1 only inside\n")
        fh.write("#       __wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i (:583-601) and inject only in __wrap_malloc while arm==1 (:79-100).\n")
        fh.write("#       arm=2 is set only in the real fft_plan_exec (:613-615) and affects only the scratch mode (:95-100), not used here;\n")
        fh.write("#   (c) s4malloc intercepts only S4_malloc (__wrap__Z9S4_mallocm, inject_r4_plan.cpp:496-501);\n")
        fh.write("#   (d) S4/pattern/pattern.c contains no S4_malloc call and no fft call (counted 0);\n")
        fh.write("#   the 25 seam points: the seam patch does not modify pattern.c (checked: seamdiff has no pattern.c entry).\n")
        fh.write("# Exceptions listed: none (0 rows).  Status INFLUENCED (R6c results are the source of the expectations).\n")
        fh.write("# Controls (G6c): 18 no-injection controls, status INFLUENCED; the R6c seam control registry is the source.\n")
        fh.write("\t".join(cols) + "\n")
        n = 0
        for d in g5:
            for tree in ("F", "F2"):
                fh.write("\t".join(["G5", d["point_id"], tree, "-", d["mode"], d["route"], d["request"], d["inj_call"],
                                    d["k_before"], d["k_fail"], d["k_preretry"], d["k_retry"], d["retry_call"],
                                    d["applicable_invariants"], d["expected"], "INFLUENCED", "G5:" + SRC["G5"]]) + "\n")
                n += 1
        for d in g6:
            for tree in ("F", "F2"):
                fh.write("\t".join(["G6", d["point_id"], tree, d["library"], d["mode"], d["route"], d["request"], d["inj_call"],
                                    d["k_before"], d["k_fail"], d["k_preretry"], d["k_retry"], d["retry_call"],
                                    d["applicable_invariants"], d["expected"], "INFLUENCED", "G6:" + SRC["G6"]]) + "\n")
                n += 1
        for d in g6c:
            for tree in ("F", "F2"):
                fh.write("\t".join(["G6c", d["control_id"], tree, d["library"], d["mode"], d["route"], "-", "NA",
                                    "-", "-", "-", "-", "-", "control", "CONTROL_OK_EXPECTED", d["status"],
                                    "G6c:" + SRC["G6c"]]) + "\n")
                n += 1
    print("written %s rows(data)=%d sha256_sources=%s" % (out, n, hashes))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
