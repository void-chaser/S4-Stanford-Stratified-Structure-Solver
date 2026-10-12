#!/usr/bin/env python3
"""P05-S4 R7 cont8 (U75a): generate REGISTRY_S4_PRE_R7_M2_ADD_v3.tsv (new file; writes OUT only; refuses if OUT exists).

Supersedes ADD_v2 for the ENVIRONMENT columns only (route, twice_env, and for G1 controls request and nth).  point_id, tree,
group, expected_class and inj_call are copied from ADD_v2 unchanged and checked line by line; any difference refuses the write.
v2 (REGISTRY_S4_PRE_R7_M2.tsv) is read only for its sha256 and its point_id/tree/group/expected_class set; it is not edited.

Rules (cont8 U75a):
  G1, G2c injection rows : route = run_r3_sweep.route_of(point_id) (imported, not copied); twice_env = slab if route == twice else "-".
  G1 control rows CTL-*  : route = "control", twice_env = "-", request = "-", nth = "-".  (route_of is not defined for CTL ids.)
  G2a rows               : unchanged from ADD_v2 (run_r4_matrix.py:101-102: nth "-"; no route change is registered for G2a).
  request, ng, stack, inj_call_source of G1/G2c injection rows: unchanged from ADD_v2.

Usage (through safe_run; absolute OUT under the evidence directory):
  python3 -I -B testing/d003/stage_s4r7/make_prereg_m2_add_v3_r7.py ADD_V2.tsv OUT_ADD_V3.tsv DIFF_COUNT.txt
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "testing", "d003", "stage_s4"))
from run_r3_sweep import route_of  # noqa: E402  imported, not copied (U75a); guarded by __main__ in run_r3_sweep

V2 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7", "REGISTRY_S4_PRE_R7_M2.tsv")
V2_SHA = "e4dd2c8779887f57044253a7e1674923a0fb34a0c6fcd437459572ae8d92ba2c"
KEEP = ("point_id", "tree", "group", "expected_class", "inj_call")
ENV = ("request", "nth", "route", "twice_env")


def read_table(path):
    header, rows, comments = None, [], []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if line.startswith("#"):
                comments.append(line)
                continue
            if not line:
                continue
            f = line.split("\t")
            if header is None:
                header = f
                continue
            rows.append(dict(zip(header, f)))
    return header, rows, comments


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def v3_row(r):
    """The environment columns of one ADD_v2 row under the U75a rules.  Returns a dict with ENV keys."""
    out = {k: r[k] for k in ENV}
    if r["group"] in ("G1", "G2c") and r["point_id"].startswith("CTL-"):
        if r["group"] != "G1":
            raise SystemExit("REFUSED: CTL row outside G1: %s" % r["point_id"])
        out.update({"request": "-", "nth": "-", "route": "control", "twice_env": "-"})
    elif r["group"] in ("G1", "G2c"):
        route = route_of(r["point_id"])
        if route not in ("once", "twice"):
            raise SystemExit("REFUSED: route_of(%s) = %r" % (r["point_id"], route))
        out["route"] = route
        out["twice_env"] = "slab" if route == "twice" else "-"
    # G2a: unchanged (the historical run_r4_matrix rule; no route change is registered)
    return out


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: make_prereg_m2_add_v3_r7.py ADD_V2.tsv OUT_ADD_V3.tsv DIFF_COUNT.txt")
    add2, out, diff_out = argv[1], argv[2], argv[3]
    for p in (out, diff_out):
        if not os.path.isabs(p):
            raise SystemExit("REFUSED: output paths must be absolute: %s" % p)
        if os.path.exists(p):
            raise SystemExit("REFUSED: exists (U17): %s" % p)
    if sha256(V2) != V2_SHA:
        raise SystemExit("REFUSED: v2 sha256 differs from the registered value")
    header, rows, comments = read_table(add2)
    v2_header, v2_rows, _ = read_table(V2)
    # the key set of ADD_v2 must match v2 (group-aware key, E7-21(a))
    v2_keys = sorted((r["point_id"], r["tree"], r["group"], r["expected_class"]) for r in v2_rows
                     if r["group"] in ("G1", "G2c", "G2a", "G2c-control"))
    add_keys = sorted((r["point_id"], r["tree"], r["group"], r["expected_class"]) for r in rows)
    if v2_keys and add_keys and len(add_keys) != len(v2_keys):
        raise SystemExit("REFUSED: ADD_v2 row count %d differs from v2 %d" % (len(add_keys), len(v2_keys)))
    counts = {}
    lines = list(comments)
    lines[0:0] = ["# REGISTRY_S4_PRE_R7_M2_ADD_v3.tsv -- P05-S4 R7 cont8 (U75a).  Supersedes ADD_v2 for the environment columns only:",
                  "# route and twice_env (G1, G2c) from run_r3_sweep.route_of; G1 control rows request and nth '-'.",
                  "# point_id, tree, group, expected_class, inj_call copied from ADD_v2 and checked.  generator: make_prereg_m2_add_v3_r7.py"]
    body = ["\t".join(header)]
    for r in rows:
        env = v3_row(r)
        for k in ENV:
            if env[k] != r[k]:
                counts[(r["group"], k)] = counts.get((r["group"], k), 0) + 1
        new = dict(r)
        new.update(env)
        body.append("\t".join(new[c] for c in header))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines + body) + "\n")
    with open(diff_out, "w", encoding="utf-8") as fh:
        fh.write("# ADD_v3 vs ADD_v2: number of changed environment cells per (group, column).  Expected (cont8 2.1):\n")
        fh.write("# G2c route 30, G2c twice_env 30 (15 twice points x 2 trees), G1 request 16, G1 nth 16, nothing else.\n")
        for (g, k) in sorted(counts):
            fh.write("%s\t%s\t%d\n" % (g, k, counts[(g, k)]))
        fh.write("# total changed cells: %d\n" % sum(counts.values()))
    print("wrote %s rows=%d changed=%d" % (out, len(rows), sum(counts.values())))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
