#!/usr/bin/env python3
"""P05-S4 R7 M2a: do the plancall injections of G2b/G3/G4 land inside the RNV1 window? (new file; read only).

The RNV1 window (Pattern_GenerateFlowField) makes mallocs of fixed sizes that were measured for nv/fft/jones at NG 9 and
NG 1 (RNV1_JONES_MAP_R7.tsv, RNV1_SOURCE_R6d.md section 4): rect 7168 / 2048 / 4096 B, tri 19968 / 7680 / 6144 B.
A plancall hit prints "S4FMM HIT real malloc failure: plan call K malloc M, N B" on stderr (read from each run.out).
This script reads the stored run.out of every M2a point and records the malloc size N of its hit.  If N is one of the window
sizes the point is flagged POSSIBLY_IN_WINDOW; otherwise NOT_IN_WINDOW_BY_SIZE.  It is a size test, not a proof of position,
and is reported as such.  Read only; writes one new file.

Usage (through safe_run):  python3 -I -B testing/d003/stage_s4r7/check_hit_bytes_m2a_r7.py EVDIR OUT.tsv
"""
import os
import re
import sys

WINDOW_BYTES = {7168, 2048, 4096, 19968, 7680, 6144}
RE_HIT = re.compile(r"S4FMM HIT real malloc failure: plan call (\d+) malloc (\d+), (\d+) B")


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: check_hit_bytes_m2a_r7.py EVDIR OUT.tsv")
    ev, out = argv[1], argv[2]
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    base = os.path.join(ev, "m2")
    lines = ["# HIT size check, M2a: plancall hits of G2b, G3, G4 against the RNV1 window malloc sizes (size test, not position).",
             "# window sizes (bytes): %s" % sorted(WINDOW_BYTES),
             "group\tpoint_id\tpass\tplan_call\tmalloc_index\tbytes\tverdict"]
    n = in_window = missing = 0
    for g in ("G2b", "G3", "G4"):
        gdir = os.path.join(base, g)
        if not os.path.isdir(gdir):
            missing += 1
            continue
        for pid in sorted(os.listdir(gdir)):
            for pas in ("pass1_run4", "pass2_run4"):
                fn = os.path.join(gdir, pid, pas, "run.out")
                if not os.path.isfile(fn):
                    missing += 1
                    continue
                with open(fn, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
                m = RE_HIT.search(text)
                if not m:
                    lines.append("\t".join([g, pid, pas[:5], "-", "-", "-", "NO_HIT_LINE"]))
                    missing += 1
                    continue
                n += 1
                nb = int(m.group(3))
                v = "POSSIBLY_IN_WINDOW" if nb in WINDOW_BYTES else "NOT_IN_WINDOW_BY_SIZE"
                if v == "POSSIBLY_IN_WINDOW":
                    in_window += 1
                lines.append("\t".join([g, pid, pas[:5], m.group(1), m.group(2), str(nb), v]))
    lines.append("# hits read=%d possibly_in_window=%d missing_or_no_hit=%d" % (n, in_window, missing))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("hits=%d possibly_in_window=%d missing=%d -> %s" % (n, in_window, missing, out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
