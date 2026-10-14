#!/usr/bin/env python3
"""P05-S4 R8 M1a, section 5.2: compile-option comparison of the F3 builds with the R7 builds (new file).

Copy of the method of testing/d003/stage_s4r7/build_option_diff_r7.sh (committed, not modified): the g++ command lines of
two build logs are compared after the absolute path prefixes are removed and the -o operand is replaced.  The method is
written in Python here so that no shell redirection or temporary file is needed.  The normalisation is the same as the
sed expressions of build_option_diff_r7.sh:
  s#/srv/[^ ]*/\\(S4\\|build\\|checkpoints\\|testing\\)#<P>/\\1#g   and   s#-o [^ ]*#-o <OUT>#g

Output (new file, refused if it exists): $EV/BUILD_OPTION_DIFF_R8_M1a.txt
One line per pair: lines compared on each side and the number of differing lines.  The expectation is 0 differing lines.
Usage (through safe_run):  python3 -I -B testing/d003/stage_s4r8/build_option_diff_r8m1.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
EV7 = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r7")
OUT = os.path.join(EV, "BUILD_OPTION_DIFF_R8_M1a.txt")

RE_PATH = re.compile(r"/srv/[^ ]*/(S4|build|checkpoints|testing)")
RE_OUT = re.compile(r"-o [^ ]*")

# (name, R7 log, R8 log).  R7 logs are read from the R7 evidence; R8 logs from M0 (plain, seam plain) and this round (seam dbg).
PAIRS = [
    ("G5 R7-F-dbg vs R8-F3-dbg (M0 build)",
     os.path.join(EV7, "build_r7", "build-F-dbg.log"),
     os.path.join(EV, "build_r8", "build-F3-dbg.log")),
    ("G6 R7-seamF-F vs R8-seamF-F3 (seam dbg, M1a build)",
     os.path.join(EV7, "build_r7", "seam", "build-seamF-F.log"),
     os.path.join(EV, "build_r8m1", "seam_dbg", "build-seamF-F3.log")),
    ("G6 R7-fmmret-F vs R8-fmmret-F3 (seam dbg, M1a build)",
     os.path.join(EV7, "build_r7", "seam", "build-fmmret-F.log"),
     os.path.join(EV, "build_r8m1", "seam_dbg", "build-fmmret-F3.log")),
    ("plain R7-F-plain vs R8-F3-plain (M0 build)",
     os.path.join(EV7, "build_r7", "build-F-plain.log"),
     os.path.join(EV, "build_r8", "build-F3-plain.log")),
    ("seam plain R7-seamF-F-plain vs R8-seamF-F3-plain (M0 build)",
     os.path.join(EV7, "build_r7", "seam_plain", "build-seamF-F-plain.log"),
     os.path.join(EV, "build_r8", "seam_plain", "build-seamF-F3-plain.log")),
    ("seam plain R7-fmmret-F-plain vs R8-fmmret-F3-plain (M0 build)",
     os.path.join(EV7, "build_r7", "seam_plain", "build-fmmret-F-plain.log"),
     os.path.join(EV, "build_r8", "seam_plain", "build-fmmret-F3-plain.log")),
]


def norm(line):
    line = RE_PATH.sub(lambda m: "<P>/" + m.group(1), line)
    return RE_OUT.sub("-o <OUT>", line)


def gxx_lines(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return [norm(l.rstrip("\n")) for l in fh if l.startswith("g++ ")]


def main(argv):
    if len(argv) != 1:
        raise SystemExit("usage: build_option_diff_r8m1.py  (no arguments)")
    if os.path.exists(OUT):
        raise SystemExit("REFUSED: exists (U17): %s" % OUT)
    total_diff = 0
    lines = ["BUILD_OPTION_DIFF_R8_M1a (P05-S4 R8 M1a section 5.2): g++ command lines, path prefixes removed; expected diff_lines=0",
             "pair\tlines_r7\tlines_r8\tdiff_lines"]
    for name, a, b in PAIRS:
        for p in (a, b):
            if not os.path.isfile(p):
                raise SystemExit("REFUSED: missing input %s" % p)
        la, lb = gxx_lines(a), gxx_lines(b)
        # set-free positional comparison: line i of R7 against line i of R8 (both are the compile commands in build order)
        diff = 0
        for i in range(max(len(la), len(lb))):
            x = la[i] if i < len(la) else ""
            y = lb[i] if i < len(lb) else ""
            if x != y:
                diff += 1
        total_diff += diff
        lines.append("%s\t%d\t%d\t%d" % (name, len(la), len(lb), diff))
    lines.append("total_diff_lines=%d" % total_diff)
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if total_diff == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
