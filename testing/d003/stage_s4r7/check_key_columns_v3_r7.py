#!/usr/bin/env python3
"""P05-S4 R7 cont8 ADD1 (U78): key-column check of ADD_v3 against ADD_v2 (new file; read only except OUT).

Compares, row by row, the five key columns point_id, tree, group, expected_class, inj_call.  Any difference is a key-column
difference; U78 requires 0.  The environment columns are not compared here (they are reported by ADD_V3_VS_V2_DIFF.txt).
Usage (through safe_run, absolute paths):  python3 -I -B testing/d003/stage_s4r7/check_key_columns_v3_r7.py ADD_V2 ADD_V3 OUT.txt
Exit status 0 only if the row counts match and the key-column difference count is 0.
"""
import os
import sys

KEY = ("point_id", "tree", "group", "expected_class", "inj_call")


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
            rows.append(dict(zip(header, f)))
    return rows


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: check_key_columns_v3_r7.py ADD_V2 ADD_V3 OUT.txt")
    a2, a3, out = argv[1], argv[2], argv[3]
    if not (os.path.isabs(a2) and os.path.isabs(a3) and os.path.isabs(out)):
        raise SystemExit("REFUSED: all paths must be absolute")
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    r2, r3 = read_table(a2), read_table(a3)
    lines = ["# key-column check (U78): ADD_v3 vs ADD_v2 on %s.  Environment columns are not compared here." % ", ".join(KEY)]
    diffs = 0
    if len(r2) != len(r3):
        lines.append("ROW_COUNT_DIFFERS\t%d\t%d" % (len(r2), len(r3)))
        diffs += 1
    for i, (x, y) in enumerate(zip(r2, r3), 1):
        for k in KEY:
            if x.get(k) != y.get(k):
                diffs += 1
                lines.append("KEY_DIFF\trow=%d\t%s\t%r\t%r" % (i, k, x.get(k), y.get(k)))
    lines.append("# rows=%d key_column_differences=%d" % (len(r3), diffs))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("rows=%d key_column_differences=%d -> %s" % (len(r3), diffs, out))
    return 0 if diffs == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
