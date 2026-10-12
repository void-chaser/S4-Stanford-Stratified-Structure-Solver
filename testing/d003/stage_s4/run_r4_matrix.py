#!/usr/bin/env python3
# run_r4_matrix.py -- P05-S4 R4-3 runner.  New file.  matrix_r2.py and judge_d003.py are IMPORTED, not modified.
#
#   python3 -I -B testing/d003/stage_s4/run_r4_matrix.py PRE_REGISTRY OUTDIR DRIVERS_TSV PASS
#
#   PRE_REGISTRY : REGISTRY_S4_PRE_R4.tsv (9 columns: point_id r1_id tree family request mode expected_class basis status)
#   OUTDIR       : evidence directory for this pass (must be under checkpoints/p05/evidence/)
#   DRIVERS_TSV  : DRIVERS.tsv written by run_r4_seam.sh (name, sha256, path)
#   PASS         : 1 or 2 (each point is run twice; the two passes are written separately)
#
# Points are run with matrix_r2.run_row (same environment, same grid, same timeout), and classified with
# judge_d003.classify on facts only (rc, rc1, rc2, hit).  The driver PASS/FAIL line is never read.
# Each driver is verified against its pinned sha256 (DRIVERS.tsv) before any row runs.
#
# Tree mapping (pre-registration tree label -> matrix_r2 tree label): B -> BASE, A -> CUR, F -> F.
# Library mapping per family and tree is ERRATA_4 section e3; the FE points on B use seamAB-B (no fmm_ret
# library exists on B, ERRATA_4 e2), and the run result is reported as observed.
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
D003 = os.path.join(REPO, "testing", "d003")
sys.path.insert(0, D003)

import judge_d003 as J  # noqa: E402
import matrix_r2 as M  # noqa: E402

TREE_MAP = {"B": "BASE", "A": "CUR", "F": "F"}
EXPECTED_HEADER = ["point_id", "r1_id", "tree", "family", "request", "mode", "expected_class", "basis", "status"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_drivers(path):
    d = {}
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            name, sha, dpath = line.split("\t")
            d[name] = (sha.lower(), dpath)
    return d


def library_for(row):
    """Driver name for a pre-registered row (ERRATA_4 e3)."""
    fam, tree, r1 = row["family"], row["tree"], row["r1_id"]
    if fam == "E":
        if tree == "A":
            return "fmmret-A"
        if tree == "F":
            return "fmmret-F"
        return "seamAB-B"          # B: no fmm_ret library (ERRATA_4 e2); run as registered, result observed
    if fam == "C" and r1 == "ACF1" and tree == "F":
        return "seamF"
    if tree == "B":
        return "seamAB-B"
    if tree == "A":
        return "seamAB-A"
    return "seamF"


def load_pre(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        header = None
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                if f != EXPECTED_HEADER:
                    raise SystemExit("pre-registration header mismatch at line %d: %r" % (lineno, f))
                header = f
                continue
            if len(f) != 9:
                raise SystemExit("pre-registration line %d has %d fields (need 9)" % (lineno, len(f)))
            pid, r1, tree, fam, req, mode, exp, basis, status = f
            if tree not in TREE_MAP:
                raise SystemExit("pre-registration line %d: bad tree %r" % (lineno, tree))
            if status != "INFLUENCED":
                raise SystemExit("pre-registration line %d: status %r is not INFLUENCED" % (lineno, status))
            rows.append({"point_id": pid, "r1_id": r1, "tree": tree, "family": fam, "request": req,
                         "mode": mode, "expected": exp, "basis": basis, "lineno": lineno})
    return rows


def as_matrix_row(row, nxt_case):
    """Map a pre-registered row to the 10-column dict used by matrix_r2.run_row (stack pattern, NG 9, NTH -)."""
    return {"case": row["point_id"], "family": row["family"], "tree": TREE_MAP[row["tree"]],
            "request": row["request"], "nth": "-", "stack": "pattern", "mode": row["mode"], "ng": "9",
            "expected": row["expected"], "basis": row["basis"], "lineno": row["lineno"]}


def main(argv):
    if len(argv) != 5:
        raise SystemExit("usage: run_r4_matrix.py PRE_REGISTRY OUTDIR DRIVERS_TSV PASS")
    pre_path, outdir, drivers_tsv, pas = argv[1], argv[2], argv[3], argv[4]
    if pas not in ("1", "2"):
        raise SystemExit("PASS must be 1 or 2")
    os.makedirs(outdir, exist_ok=True)
    drivers = load_drivers(drivers_tsv)
    # verify every driver that the pre-registration needs, before any row runs
    needed = {library_for(r) for r in load_pre(pre_path)}
    for name in sorted(needed):
        if name not in drivers:
            raise SystemExit("REFUSED: no driver %s in %s" % (name, drivers_tsv))
        pin, dpath = drivers[name]
        if not (os.path.isfile(dpath) and os.access(dpath, os.X_OK)):
            raise SystemExit("REFUSED: driver not executable: %s" % dpath)
        got = sha256(dpath)
        if got != pin:
            raise SystemExit("REFUSED: driver sha256 mismatch for %s (pinned %s, actual %s)" % (name, pin, got))
    runs_dir = os.path.join(outdir, "runs")
    os.makedirs(runs_dir, exist_ok=True)
    out_rows = []
    for row in load_pre(pre_path):
        mrow = as_matrix_row(row, None)
        lib = library_for(row)
        dpath = drivers[lib][1]
        if not M.request_ok(mrow["request"]):
            out_rows.append((row, lib, None, None, "INVALID", "unparseable request", None))
            continue
        rc, log = M.run_row(dpath, mrow, runs_dir)
        with open(log, "rb") as fh:
            text = fh.read().decode("utf-8", errors="replace")
        facts = J.facts_from_log(text)
        cls, label, reason = J.classify(rc, facts["rc1"], facts["rc2"], facts["hit"],
                                        control=M.control_of(mrow), real=True,
                                        inj_call=M.inj_call_of(mrow))
        if cls == "UNDECLARED":
            raise SystemExit("UNDECLARED class for %s: stop" % row["point_id"])
        out_rows.append((row, lib, rc, facts, cls, reason + (" " + label if label else ""), log))
    path = os.path.join(outdir, "raw_R4_pass%s.tsv" % pas)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# raw_R4_pass%s.tsv -- P05-S4 R4-3 run facts (one line per pre-registered row).\n" % pas)
        fh.write("point_id\tr1_id\ttree\tfamily\trequest\tmode\texpected\tobserved\tlibrary\trc\trc1\trc2\thit\treason\tlog_sha256\n")
        for row, lib, rc, facts, cls, reason, log in out_rows:
            if facts is None:
                fields = [row["point_id"], row["r1_id"], row["tree"], row["family"], row["request"], row["mode"],
                          row["expected"], cls, lib, "-", "-", "-", "-", reason, "-"]
            else:
                fields = [row["point_id"], row["r1_id"], row["tree"], row["family"], row["request"], row["mode"],
                          row["expected"], cls, lib, str(rc), str(facts["rc1"]), str(facts["rc2"]), str(facts["hit"]),
                          reason, sha256(log) if log else "-"]
            fh.write("\t".join(fields) + "\n")
    n = len(out_rows)
    print("pass=%s rows=%d raw=%s" % (pas, n, path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
