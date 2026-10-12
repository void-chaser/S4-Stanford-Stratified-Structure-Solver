#!/usr/bin/env python3
"""P05-S4 R7 M1 pre-registration generator (new file).  Writes REGISTRY_S4_PRE_R7_M1.tsv; never runs a driver.

Must be run BEFORE any M1 injection run.  Sources (read only, sha256 recorded in the header):
  G7  checkpoints/p05/evidence/p05-s4r6d/RESULTS_R6d_RNV1_pass2_run2.tsv   (F class copied; F rows only)
  G8  checkpoints/p05/evidence/p05-s3r3/REGISTRY_S3R3_SELFCHECK.tsv         (section C2 rows: TRI-F-m*, TRI-F2-m*)
  4.2 checkpoints/p05/evidence/p05-s4r7/RNV1_JONES_MAP_R7.tsv              (window M values; jones, fftjones)
      + gdb_map_F_tri_{vl,jones}_ng9_run2.log (tri vl, jones window M values; measured)
Expectations:
  G7: F = historical class (CRASH, copied), F2 = REPORTED_FAILURE, expected_win1_rc = -11 (section 4 of the brief).
  G8: copied from the S3R3 pre-registration section C2 (F CRASH, F2 REPORTED_FAILURE); not changed.
  4.2: F = CRASH, F2 = REPORTED_FAILURE, basis "无历史 F 实测; [源码]+映射" (no historical F measurement for these points).
  Controls: one CONTROL_OK row per (driver, mode, NG) on F2, no injection, expected rc from run1 (vl/fftvl NG1 rc 20).
Usage (through safe_run; the single output file must not exist):
  python3 -I -B testing/d003/stage_s4r7/make_prereg_m1_r7.py EVDIR/REGISTRY_S4_PRE_R7_M1.tsv
"""
import hashlib
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EVD = os.path.join(REPO, "checkpoints", "p05", "evidence")
G7 = os.path.join(EVD, "p05-s4r6d", "RESULTS_R6d_RNV1_pass2_run2.tsv")
G8 = os.path.join(EVD, "p05-s3r3", "REGISTRY_S3R3_SELFCHECK.tsv")
MAP = os.path.join(EVD, "p05-s4r7", "RNV1_JONES_MAP_R7.tsv")
GDB_TRI = {"vl": os.path.join(EVD, "p05-s4r7", "gdb_map_F_tri_vl_ng9_run2.log"),
           "jones": os.path.join(EVD, "p05-s4r7", "gdb_map_F_tri_jones_ng9_run2.log")}
GDB_JF = {"jones": {1: "gdb_map_F_jones_ng1_run2.log", 5: "gdb_map_F_jones_ng5_run2.log", 9: "gdb_map_F_jones_ng9_run2.log"},
          "fftjones": {1: "gdb_map_F_fftjones_ng1_run2.log", 5: "gdb_map_F_fftjones_ng5_run2.log", 9: "gdb_map_F_fftjones_ng9_run2.log"}}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def table(path):
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
            rows.append(dict(zip(header, f)))
    return rows


def window_mallocs(log):
    """Return the pattern.c lines of the window mallocs in order (the 806 call is outside the window and dropped)."""
    with open(log, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    lines = [int(x) for x in re.findall(r"pattern\.c:(\d+)", txt)]
    return [ln for ln in lines if ln != 806]


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: make_prereg_m1_r7.py OUT.tsv")
    out = argv[1]
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    srcs = {"G7": G7, "G8": G8, "MAP": MAP}
    for k, p in srcs.items():
        if not os.path.isfile(p):
            raise SystemExit("missing source %s: %s" % (k, p))
    sha = {k: sha256_file(p) for k, p in srcs.items()}
    rows = []

    # G7: 36 RNV1 F points from R6d; the F class is READ from the source row (not typed), F2 expectation REPORTED_FAILURE
    g7_rows = [d for d in table(G7) if d["tree"] == "F"]
    if len(g7_rows) != 36:
        raise SystemExit("G7 F rows %d != 36" % len(g7_rows))
    for d in g7_rows:
        rows.append([d["point_id"].replace("RNV1-F-", "M1-G7-F2-"), "G7", "F2", d["mode"], d["NG"], d["M"],
                     "rnv1:%s" % d["M"], d["class"], "REPORTED_FAILURE", "-11",
                     "G7 F2 expectation [源码] window malloc -> -11 -> rc 20; F class copied from R6d source row",
                     "INFLUENCED"])

    # G8: TRI-F2 rows (F2 expected REPORTED_FAILURE); TRI-F rows (F expected CRASH) copied from the S3R3 section C2
    for d in table(G8):
        if d.get("section") != "C2":
            continue
        tree = d["tree"]
        expected = d["expected"]
        rows.append([d["point_id"].replace("TRI-", "M1-G8-"), "G8", tree, d["mode"], d["NG"], d["M"], d["request"],
                     "CRASH" if tree == "F" else "REPORTED_FAILURE", expected, "-11" if tree == "F2" else "-",
                     "G8 copied from S3R3 section C2 (expected unchanged)", "INFLUENCED"])

    # 4.2 new points: jones, fftjones (F and F2); M = the three measured window positions for each NG
    for mode in ("jones", "fftjones"):
        for ng in (1, 5, 9):
            for m in (1, 2, 3):
                for tree in ("F", "F2"):
                    rows.append(["M1-42-%s-%s-ng%d-m%d" % (tree, mode, ng, m), "4.2", tree, mode, str(ng), str(m),
                                 "rnv1:%d" % m, "CRASH" if tree == "F" else "REPORTED_FAILURE",
                                 "CRASH" if tree == "F" else "REPORTED_FAILURE", "-11" if tree == "F2" else "-",
                                 "无历史 F 实测; [源码]+映射 (RNV1_JONES_MAP_R7.tsv; window M=%d -> malloc %s)" %
                                 (m, {1: "1477 rect work", 2: "1481 rect iwork", 3: "1251 cg work"}[m]), "INFLUENCED"])

    # 4.2 new points: tri vl, jones at NG9 (F and F2); M = the three measured tri window positions
    tri_names = {1: "1656 tri work", 2: "1660 tri iwork", 3: "1251 cg work"}
    for mode in ("vl", "jones"):
        for m in (1, 2, 3):
            for tree in ("F", "F2"):
                rows.append(["M1-42-tri-%s-%s-ng9-m%d" % (tree, mode, m), "4.2", tree, mode, "9", str(m),
                             "rnv1:%d" % m, "CRASH" if tree == "F" else "REPORTED_FAILURE",
                             "CRASH" if tree == "F" else "REPORTED_FAILURE", "-11" if tree == "F2" else "-",
                             "无历史 F 实测; [源码]+映射 (gdb_map_F_tri_%s_ng9_run2.log; window M=%d -> %s)" %
                             (mode, m, tri_names[m]), "INFLUENCED"])

    # controls: F2 no-injection rows.  Expected rc is READ from the run1 results (not typed here).
    # run1 has modes nv, vl, fftnv, fftvl, jones, fftjones (square lattice); missing modes are reported, not guessed.
    run1 = os.path.join(EVD, "p05-s4r7", "RESULTS_R7_NOINJECT_run1.tsv")
    if not os.path.isfile(run1):
        raise SystemExit("missing control source run1")
    ctrl = {}
    # the rc of each (mode, NG, tree) is on the row "<mode> <NG> <lattice> <tree> rc1 rc2 run_rc=<n> -"
    with open(run1, encoding="utf-8") as fh:
        for raw in fh:
            f = raw.rstrip("\n").split("\t")
            if len(f) >= 7 and f[3] in ("F", "F2") and f[6].startswith("run_rc="):
                ctrl[(f[0], f[1], f[2], f[3])] = (f[4], f[5], f[6].split("=", 1)[1])
    for mode in ("vl", "fftvl", "nv", "fftnv", "jones", "fftjones"):
        for ng in (1, 5, 9):
            key = (mode, str(ng), "square", "F2")
            if key not in ctrl:
                rows.append(["M1-CTRL-F2-%s-ng%d" % (mode, ng), "control", "F2", mode, str(ng), "-", "none",
                             "CONTROL_OK", "NOT_IN_RUN1", "-", "no run1 row for this (mode,NG); control not defined", "INFLUENCED"])
                continue
            rc1, rc2, rcrun = ctrl[key]
            rows.append(["M1-CTRL-F2-%s-ng%d" % (mode, ng), "control", "F2", mode, str(ng), "-", "none",
                         "CONTROL_OK", "rc_first=%s,rc_retry=%s,run_rc=%s" % (rc1, rc2, rcrun), "-",
                         "no injection; expected values read from RESULTS_R7_NOINJECT_run1.tsv", "INFLUENCED"])

    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# REGISTRY_S4_PRE_R7_M1.tsv -- P05-S4 R7 M1 pre-registration (generated by make_prereg_m1_r7.py; brief section 4).\n")
        fh.write("# Status: INFLUENCED (window structure and the G7/G8 expectations were measured before this file).\n")
        fh.write("# Source sha256: G7=%s\n" % sha["G7"])
        fh.write("#                G8=%s\n" % sha["G8"])
        fh.write("#                MAP=%s\n" % sha["MAP"])
        fh.write("# Expectations are NOT changed after the runs.  Any change is a new ERRATA file.\n")
        fh.write("point_id\tgroup\ttree\tmode\tNG\tM\trequest\tfirst_expected_class\texpected_class\texpected_win1_rc\tbasis\tstatus\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
    print("rows=%d -> %s" % (len(rows), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
