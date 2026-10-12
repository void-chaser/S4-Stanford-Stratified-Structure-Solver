#!/usr/bin/env python3
"""P05-S4 R7 cont3: list EVERY v2/ADD expected_class disagreement, joined on (point_id, tree, group) (new file; read only).

The runner refuses at the first disagreement only.  This script prints all of them, so the cause is visible at once.
It writes nothing.  Usage (no safe_run needed for a read-only print):
  python3 -I -B testing/d003/stage_s4r7/list_v2_add_mismatch_r7.py
"""
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r7")
V2 = os.path.join(EV, "REGISTRY_S4_PRE_R7_M2.tsv")
ADD = os.path.join(EV, "REGISTRY_S4_PRE_R7_M2_ADD.tsv")


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


def main():
    add = {(r["point_id"], r["tree"], r["group"]): r for r in table(ADD)}
    n_pairs = n_diff = n_unmatched_add = 0
    for r in table(V2):
        key = (r["point_id"], r["tree"], r["group"])
        a = add.get(key)
        if a is None:
            continue
        n_pairs += 1
        if a["expected_class"] != r["expected_class"]:
            n_diff += 1
            print("DIFF %s  group=%s  v2=%s  add=%s" % (r["point_id"], r["group"], r["expected_class"], a["expected_class"]))
    add_keys_in_v2 = {(r["point_id"], r["tree"], r["group"]) for r in table(V2)}
    for k in add:
        if k not in add_keys_in_v2:
            n_unmatched_add += 1
            print("ADD_ONLY %s" % (k,))
    print("joined pairs=%d expected_class differences=%d ADD rows without v2 match=%d" % (n_pairs, n_diff, n_unmatched_add))
    return 0


if __name__ == "__main__":
    sys.exit(main())
