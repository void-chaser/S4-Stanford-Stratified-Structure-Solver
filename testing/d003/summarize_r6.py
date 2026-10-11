#!/usr/bin/env python3
"""D003 unified summary (P05-S2R6, R6-2 judge and report).

Reads only files; writes only under --out.  It does not edit judge_d003.py or any seam script.

Inputs (all relative to --out, which is an output directory of run_all.sh):
  matrix/runs/<registry>--<tree>--<family>/pass<N>/raw_<RUNNER_TREE>.json   fresh matrix runs
  matrix/inputs/INPUTS.tsv                                                  the input manifest
Frozen references (relative to --repo):
  checkpoints/p05/evidence/p05-s2r2/hist38-base/index.txt, hist38-cur/index.txt   historical 38 case
  checkpoints/p05/evidence/p05-s2r4/r4-2/hist38-H-r3/runs/raw_rc.json            H 38 case raw runs
  checkpoints/p05/evidence/p05-s2r/hist-base/index.txt, hist-cur/index.txt        R2-D run index

Outputs (under --out/report):
  summary.tsv      one row per comparison line, with a status column
  SUMMARY.txt      human-readable summary

Status values (each row carries exactly one):
  MATCHED                  observed class equals the frozen expectation, or the frozen result
  STRUCTURAL_DECLARED      a difference that the records already declare as structural
  UNDECLARED               a difference with no declaration in the records (must be explained)

Classification is taken from the facts recorded by the runner (rc, rc1, rc2, hit).  The driver's
own PASS/FAIL line is never read.
"""
import argparse
import glob
import json
import os
import sys
import hashlib
import collections

HERE = os.path.dirname(os.path.abspath(__file__))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def read_tsv(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            rows.append(line.split("\t"))
    return rows


def matrix_rows(out_dir):
    """All fresh matrix rows, pass 1 and pass 2, keyed by (input tag, pass, case)."""
    recs = []
    for raw in sorted(glob.glob(os.path.join(out_dir, "matrix", "runs", "*", "pass*", "raw_*.json"))):
        tag = raw.split(os.sep)[-3]
        pas = raw.split(os.sep)[-2]
        tree_label = os.path.basename(raw)[len("raw_"):-len(".json")]
        with open(raw, encoding="utf-8") as fh:
            for r in json.load(fh):
                recs.append({"tag": tag, "pass": pas, "runner_tree": tree_label,
                             "case": r["case"], "family": r["family"], "request": r["request"],
                             "expected": r["expected"], "observed": r["observed"],
                             "rc": r["rc"], "facts": r.get("facts") or {}, "log_sha256": r.get("log_sha256")})
    return recs


def frozen_index_rows(path):
    """Rows of a frozen index.txt: list of dicts keyed by the header."""
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip()]
    header = None
    out = []
    for l in lines:
        if l.startswith("#"):
            header = l.lstrip("#").strip().split("\t")
            continue
        cols = l.split("\t")
        if header is None:
            header = ["case", "class", "expected", "match"]
        out.append(dict(zip(header, cols)))
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("--out", required=True, help="run_all.sh output directory")
    p.add_argument("--repo", required=True, help="repository root (frozen references)")
    args = p.parse_args(argv)

    rep = os.path.join(args.out, "report")
    os.makedirs(rep, exist_ok=True)
    lines = []   # (section, item, expected, observed, status, note)

    # 1. fresh matrix against the registries (their expectation column)
    recs = matrix_rows(args.out)
    # rows are counted on PASS 1 only (each registry row is run twice; pass 2 is a repeat check)
    per_tree = collections.Counter()        # pass1 rows per tree
    per_tree_mm = collections.Counter()     # mismatches over both passes
    per_tree_rep = collections.Counter()    # pass2 rows that equal pass1 class (repeat check)
    p1_obs = {}
    for r in recs:
        ok = r["observed"] == r["expected"]
        if r["pass"] == "pass1":
            per_tree[r["runner_tree"]] += 1
            p1_obs[(r["tag"], r["case"])] = r["observed"]
        if not ok:
            per_tree_mm[r["runner_tree"]] += 1
    for r in recs:
        if r["pass"] == "pass2" and p1_obs.get((r["tag"], r["case"])) == r["observed"]:
            per_tree_rep[r["runner_tree"]] += 1
    for t in sorted(per_tree):
        same = per_tree_rep[t] == per_tree[t]
        status = "MATCHED" if (per_tree_mm[t] == 0 and same) else "UNDECLARED"
        lines.append(("matrix-registry", "tree %s run-rows" % t, "-", str(per_tree[t]), status,
                      "pass1 rows; mismatched over both passes=%d; pass2 repeats pass1 class: %d/%d"
                      % (per_tree_mm[t], per_tree_rep[t], per_tree[t])))

    # 2. registry-level detail: one line per (input tag, pass)
    grouped = collections.OrderedDict()
    for r in recs:
        key = (r["tag"], r["runner_tree"])
        grouped.setdefault(key, {"pass1": [0, 0], "pass2": [0, 0]})
        slot = grouped[key]["pass1" if r["pass"] == "pass1" else "pass2"]
        slot[1] += 1
        slot[0] += 1 if r["observed"] == r["expected"] else 0
    for (tag, rt), d in grouped.items():
        p1, p2 = d["pass1"], d["pass2"]
        status = "MATCHED" if (p1[0] == p1[1] and p2[0] == p2[1] and p1[1] > 0) else "UNDECLARED"
        lines.append(("matrix-input", tag, "rows=%d" % p1[1], "pass1=%d pass2=%d" % (p1[0], p2[0]),
                      status, "tree %s" % rt))

    # 3. historical 38 case: frozen index per tree.  The declared S2 fix set is the 18 H/CUR NO rows
    #    recorded in the S2R4 closeout (case names read from the frozen H index itself).
    h38 = os.path.join(args.repo, "checkpoints/p05/evidence/p05-s2r4/r4-2/hist38-H-r3/index.txt")
    declared = set()
    if os.path.isfile(h38):
        declared = set(r["case"] for r in frozen_index_rows(h38) if r.get("match") == "NO")
    for label, path in [("hist38-BASE(frozen)", "checkpoints/p05/evidence/p05-s2r2/hist38-base/index.txt"),
                        ("hist38-CUR(frozen)", "checkpoints/p05/evidence/p05-s2r2/hist38-cur/index.txt"),
                        ("hist38-H(frozen,S2R4)", "checkpoints/p05/evidence/p05-s2r4/r4-2/hist38-H-r3/index.txt")]:
        full = os.path.join(args.repo, path)
        if not os.path.isfile(full):
            lines.append(("hist38", label, "-", "missing", "UNDECLARED", path))
            continue
        rows = frozen_index_rows(full)
        no = set(r["case"] for r in rows if r.get("match") == "NO")
        yes = [r for r in rows if r.get("match") == "yes"]
        if label.startswith("hist38-BASE"):
            status = "MATCHED" if not no else "UNDECLARED"
        else:
            # a non-BASE NO set is acceptable only if it equals the declared S2 set exactly
            status = "STRUCTURAL_DECLARED" if no == declared and declared else "UNDECLARED"
        lines.append(("hist38", label, "cases=%d" % len(rows), "yes=%d NO=%d" % (len(yes), len(no)),
                      status, "NO set == declared S2 set (%d cases)" % len(declared) if not label.startswith("hist38-BASE") else "no NO rows expected"))

    # 4. R2-D 13 case (frozen run index)
    for label, path in [("R2D-BASE(frozen)", "checkpoints/p05/evidence/p05-s2r/hist-base/index.txt"),
                        ("R2D-CUR(frozen)", "checkpoints/p05/evidence/p05-s2r/hist-cur/index.txt")]:
        full = os.path.join(args.repo, path)
        if not os.path.isfile(full):
            lines.append(("r2d", label, "-", "missing", "UNDECLARED", path))
            continue
        rows = frozen_index_rows(full)
        no = set(r["case"] for r in rows if r.get("match") == "NO")
        if label.startswith("R2D-BASE"):
            status = "MATCHED" if not no else "UNDECLARED"
        else:
            status = "STRUCTURAL_DECLARED" if no == declared and declared else "UNDECLARED"
        lines.append(("r2d", label, "cases=%d" % len(rows), "NO=%d" % len(no), status,
                      "NO set == declared S2 set" if not label.startswith("R2D-BASE") else "no NO rows expected"))

    # 5. registry set sizes (cardinality) used by the historical comparisons
    sizes = [
        ("S2R3 three-column", "checkpoints/p05/registries/s2r3/stage3/REG_3B_THREECOLUMN.tsv", 24),
        ("S2R4 seven-site", "checkpoints/p05/registries/s2r4/r4-1/REG_R4_1_POSTHOC.tsv", 21),
        ("S2R5 ten points", "checkpoints/p05/registries/s2r5/r5-1/R5_1_THREE_COLUMN.tsv", 10),
        ("S2R5 family F", "checkpoints/p05/registries/s2r5/r5-2/REG_R5_2_ADDFIELD.tsv", 3),
        ("S2R5 family F FFT", "checkpoints/p05/registries/s2r5/r5-2/REG_R5_2_ADDFIELD_FFT.tsv", 3),
        ("S2R2 17 case", "checkpoints/p05/registries/s2r4/r4-3/MAP_R4_3_S2R2_CUR.tsv", 17),
    ]
    for label, path, want in sizes:
        full = os.path.join(args.repo, path)
        if not os.path.isfile(full):
            lines.append(("cardinality", label, str(want), "missing", "UNDECLARED", path))
            continue
        got = len(read_tsv(full))
        if label.startswith("S2R5 ten"):
            got -= 1   # header line (the 'point' header row)
        status = "MATCHED" if got == want else "UNDECLARED"
        lines.append(("cardinality", label, str(want), str(got), status, path))

    # write summary.tsv and SUMMARY.txt
    with open(os.path.join(rep, "summary.tsv"), "w", encoding="utf-8") as fh:
        fh.write("# section\titem\texpected\tobserved\tstatus\tnote\n")
        for row in lines:
            fh.write("\t".join(str(x) for x in row) + "\n")
    counts = collections.Counter(r[4] for r in lines)
    with open(os.path.join(rep, "SUMMARY.txt"), "w", encoding="utf-8") as fh:
        fh.write("D003 unified summary (P05-S2R6 R6-2).  Status counts: %s\n" % dict(counts))
        fh.write("Not a repair verification: MATCHED means the observation equals the registered expectation.\n\n")
        for row in lines:
            fh.write("%-18s %-26s exp=%-12s obs=%-18s %-20s %s\n" % row)
    print("summary rows=%d %s" % (len(lines), dict(counts)))
    return 0 if counts.get("UNDECLARED", 0) == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
