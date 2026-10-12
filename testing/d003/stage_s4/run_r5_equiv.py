#!/usr/bin/env python3
# run_r5_equiv.py -- P05-S4 R5-2 step 2: equivalence check of the DEBUG (-O0 -g) builds against R4.
# New file.  judge_d003.py and matrix_r2.py are IMPORTED, not modified.
#
#   python3 -I -B testing/d003/stage_s4/run_r5_equiv.py PREREG_B DRV_DBG_B DRV_DBG_F R4_PLANCALL_PASS1 OUTDIR
#
# The 12 points: the 10 plan points twice NTH 12-16 (fft, kottke) and the control points fft plan K=3 and
# kottke plan K=3, each on B and F.  The rc/rc1/rc2/hit of every (point, tree) run on the debug driver must equal
# the R4 plancall pass1 result for the same (point, tree).  Any difference is printed and the script exits 3
# (the debug build then does not reproduce R4 and the gdb conclusions must not be used).
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
D003 = os.path.join(REPO, "testing", "d003")
sys.path.insert(0, D003)

import judge_d003 as J  # noqa: E402
import matrix_r2 as M  # noqa: E402

PLANCALL_RE = re.compile(r"^plancall:([1-9][0-9]*):([1-9][0-9]*)$")
HEADER = ["point_id", "r1_id", "tree", "route", "mode", "nth_K", "M", "request", "inj_call", "expected_class", "basis", "status"]
WANT = {
    "M-twice-fft-plan-12", "M-twice-fft-plan-13", "M-twice-fft-plan-14", "M-twice-fft-plan-15", "M-twice-fft-plan-16",
    "M-twice-kottke-plan-12", "M-twice-kottke-plan-13", "M-twice-kottke-plan-14", "M-twice-kottke-plan-15", "M-twice-kottke-plan-16",
    "M-once-fft-plan-3", "M-once-kottke-plan-3",
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_prereg(path):
    rows = []
    header = None
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                if f != HEADER:
                    raise SystemExit("REFUSED: prereg header mismatch")
                header = f
                continue
            if len(f) != 12:
                raise SystemExit("REFUSED: prereg line has %d fields" % len(f))
            d = dict(zip(HEADER, f))
            if d["point_id"] in WANT:
                rows.append(d)
    return rows


def load_r4(path):
    """R4 plancall pass1: key (point_id, tree) -> dict of rc, rc1, rc2, hit, observed."""
    out = {}
    with open(path, encoding="utf-8") as fh:
        header = None
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                header = f
                continue
            d = dict(zip(header, f))
            out[(d["point_id"], d["tree"])] = d
    return out


def main(argv):
    if len(argv) != 6:
        raise SystemExit("usage: run_r5_equiv.py PREREG_B DRV_DBG_B DRV_DBG_F R4_PLANCALL_PASS1 OUTDIR")
    prereg, drv_b, drv_f, r4path, outdir = argv[1:6]
    drivers = {"B": drv_b, "F": drv_f}
    for t, p in drivers.items():
        if not (os.path.isfile(p) and os.access(p, os.X_OK)):
            raise SystemExit("REFUSED: debug driver missing for %s: %s" % (t, p))
    os.makedirs(outdir, exist_ok=True)
    runs = os.path.join(outdir, "runs")
    os.makedirs(runs, exist_ok=True)
    rows = load_prereg(prereg)
    if len(rows) != 24:
        raise SystemExit("REFUSED: expected 24 prereg rows (12 points x B,F), got %d" % len(rows))
    r4 = load_r4(r4path)
    lines = []
    diffs = 0
    for d in rows:
        m = PLANCALL_RE.match(d["request"])
        if not m or m.group(1) != d["nth_K"] or m.group(2) != d["M"]:
            raise SystemExit("REFUSED: request/K/M disagree for %s" % d["point_id"])
        mrow = {"case": "R5EQ-" + d["point_id"] + "-" + d["tree"], "family": "R5EQ", "tree": d["tree"],
                "request": d["request"], "nth": "-", "stack": "pattern", "mode": d["mode"], "ng": "9",
                "expected": d["expected_class"], "basis": d["basis"], "lineno": 0}
        rc, log = M.run_row(drivers[d["tree"]], mrow, runs)
        with open(log, "rb") as fh:
            text = fh.read().decode("utf-8", errors="replace")
        facts = J.facts_from_log(text)
        ref = r4.get((d["point_id"], d["tree"]))
        if ref is None:
            raise SystemExit("REFUSED: no R4 reference for %s %s" % (d["point_id"], d["tree"]))
        r4facts = (ref["rc"], ref["rc1"], ref["rc2"], ref["hit"])
        mine = (str(rc), str(facts["rc1"]), str(facts["rc2"]), str(facts["hit"]))
        same = (r4facts == mine)
        if not same:
            diffs += 1
        lines.append("\t".join([d["point_id"], d["tree"], d["mode"], d["nth_K"], d["M"], d["request"],
                                ",".join(r4facts), ",".join(mine), "SAME" if same else "DIFF", sha256(log)]))
    path = os.path.join(outdir, "EQUIV_R5_DBG_vs_R4.tsv")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# EQUIV_R5_DBG_vs_R4.tsv -- R5-2 step 2: debug (-O0 -g) builds vs R4 plancall pass1 (rc,rc1,rc2,hit).\n")
        fh.write("point_id\ttree\tmode\tnth_K\tM\trequest\tR4_rc_rc1_rc2_hit\tDBG_rc_rc1_rc2_hit\tsame\tlog_sha256\n")
        for ln in lines:
            fh.write(ln + "\n")
    print("rows=%d diffs=%d -> %s" % (len(rows), diffs, path))
    return 0 if diffs == 0 else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv))
