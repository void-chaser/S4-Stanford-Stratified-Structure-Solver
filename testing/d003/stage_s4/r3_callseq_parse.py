#!/usr/bin/env python3
# r3_callseq_parse.py -- P05-S4 R3-1 parser (new file, R3).  Reads the gdb discovery logs written by
# run_r3_discovery.sh and writes one CALLSEQ.tsv row per recorded call.  Read-only on the logs; it writes only
# the single output file named on the command line.  No driver PASS/FAIL line is read or used.
#
#   python3 -I -B testing/d003/stage_s4/r3_callseq_parse.py DISCOVERY_DIR OUT_TSV
#
# Each R3EV line is followed by one line from gdb "info symbol <ra>" that names the function containing the
# return address.  The caller function name is taken from that line; file and line are not available (no debug
# information in the R2 driver), so caller_file is written as NONE.
import glob
import os
import re
import sys

R3EV = re.compile(r"^R3EV cat=(malloc|plan|exec) nth=(\d+) size=(\S+) grid=(\S+) ra=0x([0-9a-f]+)\s*$")
SYM = re.compile(r"^(?P<fn>[^+]+?)\s*(?:\(.*?\))?\s*\+\s*\d+\s+in section ")
LOGNAME = re.compile(r"^(?P<route>once|twice)-(?P<tree>[BF])-(?P<mode>[a-z0-9]+)-r(?P<rep>\d+)\.log$")


def caller_of(sym_line):
    """Return the function name from 'info symbol' output, or UNKNOWN."""
    m = SYM.match(sym_line.strip())
    if m:
        fn = m.group("fn").strip()
        # drop a C++ argument list that gdb may print inside the name
        fn = re.sub(r"\(.*$", "", fn).strip()
        return fn
    return "UNKNOWN"


def parse_log(path):
    events = []
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    for i, line in enumerate(lines):
        m = R3EV.match(line)
        if not m:
            continue
        cat, nth, size, grid, ra = m.group(1), int(m.group(2)), m.group(3), m.group(4), m.group(5)
        sym = lines[i + 1] if i + 1 < len(lines) else ""
        events.append({"cat": cat, "nth": nth, "size": size, "grid": grid, "ra": ra,
                       "caller": caller_of(sym)})
    return events


def main(argv):
    if len(argv) != 3:
        print("usage: r3_callseq_parse.py DISCOVERY_DIR OUT_TSV", file=sys.stderr)
        return 2
    disc, out = argv[1], argv[2]
    rows = []
    for path in sorted(glob.glob(os.path.join(disc, "*-r*.log"))):
        name = os.path.basename(path)
        m = LOGNAME.match(name)
        if not m:
            continue
        route, tree, mode, rep = m.group("route"), m.group("tree"), m.group("mode"), m.group("rep")
        for ev in parse_log(path):
            size = ev["size"] if ev["cat"] == "malloc" else "-"
            rows.append((route, mode, tree, rep, ev["cat"], str(ev["nth"]), size, ev["caller"], "NONE", ev["ra"]))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# CALLSEQ.tsv -- P05-S4 R3-1 discovery, NO injection.  Produced by r3_callseq_parse.py from\n")
        fh.write("# checkpoints/p05/evidence/p05-s4r3/discovery/*.log.  Columns: route, mode, tree, rep, category,\n")
        fh.write("# nth (gdb global call index, equal to the injector counter), size (S4_malloc only, bytes),\n")
        fh.write("# caller_function (from info symbol of the return address), caller_file (NONE: no debug info),\n")
        fh.write("# return_address (hex).  The discovery measures call order only; it is not repair evidence.\n")
        fh.write("route\tmode\ttree\trep\tcategory\tnth\tsize\tcaller_function\tcaller_file\treturn_address\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
    print("rows=%d" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
