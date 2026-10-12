#!/usr/bin/env python3
# run_r2_matrix.py -- P05-S4 R2 three-column runner.  New file; matrix_r2.py and judge_d003.py are imported,
# not modified.  matrix_r2.py refuses tree label F (its TREES tuple is BASE, CUR, H), so this runner
# accepts BASE, CUR and F, runs each row with matrix_r2.run_row (the same environment, the same grid and
# the same timeout), and classifies each run with judge_d003.classify (facts only).
#
#   python3 -I -B testing/d003/stage_s4/run_r2_matrix.py REGISTRY OUTDIR DRIVER_BASE DRIVER_CUR DRIVER_F \
#           SHA_BASE SHA_CUR SHA_F
#
# Writes OUTDIR/raw_R2.tsv (one line per row and tree) and OUTDIR/driver_manifest.json.
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

TREE_OK = ("BASE", "CUR", "F")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            if not line.strip() or line.startswith("#") or line.startswith("case\t"):
                continue
            f = line.split("\t")
            if len(f) != 10:
                raise SystemExit("registry line %d has %d fields (need 10)" % (lineno, len(f)))
            case, fam, tree, req, nth, stack, mode, ng, exp, basis = f
            if tree not in TREE_OK:
                raise SystemExit("registry line %d: bad tree %r" % (lineno, tree))
            if exp not in J.CLASSES:
                raise SystemExit("registry line %d: bad expected class %r" % (lineno, exp))
            rows.append({"case": case, "family": fam, "tree": tree, "request": req, "nth": nth,
                         "stack": stack, "mode": mode, "ng": ng, "expected": exp, "basis": basis,
                         "lineno": lineno})
    return rows


def main(argv):
    reg, outdir, d_base, d_cur, d_f, s_base, s_cur, s_f = argv[1:9]
    os.makedirs(outdir, exist_ok=True)
    drivers = {"BASE": (d_base, s_base), "CUR": (d_cur, s_cur), "F": (d_f, s_f)}
    actual = {}
    for t, (path, pin) in drivers.items():
        if not (os.path.isfile(path) and os.access(path, os.X_OK)):
            raise SystemExit("REFUSED: driver missing for %s: %s" % (t, path))
        got = sha256(path)
        if got != pin.lower():
            raise SystemExit("REFUSED: driver sha256 mismatch for %s: pinned %s actual %s" % (t, pin, got))
        actual[t] = got
    with open(os.path.join(outdir, "driver_manifest.json"), "w", encoding="utf-8") as fh:
        json.dump({t: {"driver": drivers[t][0], "sha256": actual[t]} for t in TREE_OK}, fh, indent=1, sort_keys=True)
        fh.write("\n")
    rows = load(reg)
    runs_dir = os.path.join(outdir, "runs")
    os.makedirs(runs_dir, exist_ok=True)
    out = []
    for row in rows:
        driver = drivers[row["tree"]][0]
        # matrix_r2.request_ok accepts only the prefixed requests and s4malloc.  The injector also takes the
        # bare modes "plan" and "exec" (inject_d003.cpp: mode() compared with "plan" and "exec"); accept them here.
        if row["request"] not in ("-", "plan", "exec") and not M.request_ok(row["request"]):
            out.append((row, None, None, "INVALID", "unparseable request", None))
            continue
        rc, log = M.run_row(driver, row, runs_dir)
        text = open(log, "rb").read().decode("utf-8", errors="replace")
        facts = J.facts_from_log(text)
        cls, label, reason = J.classify(rc, facts["rc1"], facts["rc2"], facts["hit"],
                                        control=M.control_of(row), real=(row["mode"] != "exec"),
                                        inj_call=M.inj_call_of(row))
        out.append((row, rc, facts, cls, reason + (" " + label if label else ""), log))
    with open(os.path.join(outdir, "raw_R2.tsv"), "w", encoding="utf-8") as fh:
        fh.write("# raw_R2.tsv -- P05-S4 R2 run facts.  Columns: case tree request nth mode expected observed match rc rc1 rc2 hit reason log_sha256\n")
        fh.write("case\ttree\trequest\tnth\tmode\texpected\tobserved\tmatch\trc\trc1\trc2\thit\treason\tlog_sha256\n")
        for row, rc, facts, cls, reason, log in out:
            if facts is None:
                fields = [row["case"], row["tree"], row["request"], row["nth"], row["mode"], row["expected"], cls,
                          "NO", "-", "-", "-", "-", reason, "-"]
            else:
                match = "MATCH" if cls == row["expected"] else "MISMATCH"
                fields = [row["case"], row["tree"], row["request"], row["nth"], row["mode"], row["expected"], cls, match,
                          str(rc), str(facts["rc1"]), str(facts["rc2"]), str(facts["hit"]), reason,
                          sha256(log) if log else "-"]
            fh.write("\t".join(fields) + "\n")
    print("rows=%d" % len(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
