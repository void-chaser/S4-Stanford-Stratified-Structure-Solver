#!/usr/bin/env python3
# r3_sitemap.py -- P05-S4 R3-2 site map generator (new file, R3).  Reads CALLSEQ.tsv (written by
# r3_callseq_parse.py from the no-injection discovery) and writes SITEMAP.tsv: one row per distinct
# (route, mode, category, nth) point.  The map is generated, not typed by hand.
#
#   python3 -I -B testing/d003/stage_s4/r3_sitemap.py CALLSEQ_TSV SITEMAP_TSV
#
# Rules (fixed before any injection run; see P05_S4R3_REPORT.md):
#   * one point per (mode, category, nth) that is seen in the discovery on tree B AND tree F with identical
#     caller_function and size.  A point seen on one tree only, or with differing caller, is an error (exit 1).
#   * route: the set of routes in which the point appears.  Points appearing only under route twice are
#     route-specific (cache-hit / second-call) and are labelled so.
#   * in_D003_scope=YES: caller_function is an FMM epsilon function (FMMGetEpsilon_*), i.e. the caller is in
#     S4/fmm/.  in_D003_scope=NO: any other caller (GetFieldOnGrid in S4/rcwa.cpp, already checked; it is not an
#     FMM file and is counted, not treated as a red point).
#   * the category, nth and size come from the discovery; they are not inferred from source line numbers.
#   * r1_id is filled from the R1 map below (point identity by source site; the R1 registry is not edited).
import collections
import sys

FMM_CALLERS = {
    "FMMGetEpsilon_FFT", "FMMGetEpsilon_Kottke", "FMMGetEpsilon_PolBasisJones",
    "FMMGetEpsilon_PolBasisNV", "FMMGetEpsilon_PolBasisVL", "FMMGetEpsilon_ClosedForm",
    "FMMGetEpsilon_Experimental",
}

# Mapping of discovered FMM-side malloc points to R1 registry ids.  Key = (caller, category, size).  The
# sizes are checked against the allocation formulas at HEAD (NG=9, n=9, nn=81, ng2=64; see the R3 report).
# The R1 line numbers are the B-tree (37a82e8) lines and are used only as the B anchor; they are not
# used as keys.  Points with a size shared by two sites of the same caller are NOT mapped (NONE) here.
# Cache-hit (second-call) mallocs are mapped to the R1 cache-hit ids where the caller and size match.
R1_MAP = {
    ("FMMGetEpsilon_ClosedForm", "malloc", "192"): "AL01",                     # closed.cpp:40 ivalues (R1 AL01 by site)
    ("FMMGetEpsilon_Experimental", "malloc", "192"): "EXP40",                  # experimental.cpp:40 ivalues
    ("FMMGetEpsilon_FFT", "malloc", "6144"): "AL03",                           # FFT.cpp:75 work (R1 B line 74)
    ("FMMGetEpsilon_FFT", "malloc", "16"): "AL04",                             # FFT.cpp:83 discval (R1 B line 81)
    ("FMMGetEpsilon_Kottke", "malloc", "16"): "AL05",                          # kottke.cpp:87 discval (R1 B 85)
    ("FMMGetEpsilon_PolBasisJones", "malloc", "10720"): "AL07",                # Jones work (R1 B 153)
    ("FMMGetEpsilon_PolBasisJones", "malloc", "1024"): "AL08",                 # Jones vfield (R1 B 167)
    ("FMMGetEpsilon_PolBasisJones", "malloc", "1296"): "AL09",                 # Jones cache-hit work 16*nn (R1 B 337)
    ("FMMGetEpsilon_PolBasisNV", "malloc", "11872"): "AL11",                   # NV work (R1 B 110)
    ("FMMGetEpsilon_PolBasisNV", "malloc", "1024"): "AL12",                    # NV vfield (R1 B 122)
    ("FMMGetEpsilon_PolBasisNV", "malloc", "2592"): "AL13",                    # NV cache-hit work (R1 B 225)
    ("FMMGetEpsilon_PolBasisVL", "malloc", "11872"): "AL15",                   # VL work (R1 B 115)
    ("FMMGetEpsilon_PolBasisVL", "malloc", "1024"): "AL16",                    # VL vfield (R1 B 127)
    ("FMMGetEpsilon_PolBasisVL", "malloc", "2592"): "AL17",                    # VL cache-hit work (R1 B 234)
    # PolBasis ivalues (192 B, the second malloc of each PolBasis call): R1 AL06/AL10/AL14 (B lines 107/58/57)
    ("FMMGetEpsilon_PolBasisJones", "malloc", "192"): "AL06",                  # Jones ivalues (B 107)
    ("FMMGetEpsilon_PolBasisNV", "malloc", "192"): "AL10",                     # NV ivalues (B 58)
    ("FMMGetEpsilon_PolBasisVL", "malloc", "192"): "AL14",                     # VL ivalues (B 57)
}

# plan and exec sites (fft_plan_dft_2d / fft_plan_exec), keyed by (caller, category, call order inside the
# caller).  Each R1 point is a source line; a loop site (FFT/kottke plans[i], exec in a per-layer loop) is
# executed several times and therefore maps several NTH to one r1_id.  Keys below are by caller and category
# only, and the r1_id is chosen by the source line that the NTH belongs to (see R1_PLAN_EXEC_NOTE).
R1_PLAN_EXEC = {
    ("FMMGetEpsilon_FFT", "plan"): "P01",          # FFT.cpp:85 (B), loop plans[i], 5 calls
    ("FMMGetEpsilon_Kottke", "plan"): "P02",       # kottke.cpp:89 (B), loop plans[i], 5 calls
    ("FMMGetEpsilon_PolBasisJones", "plan"): "P03",  # Jones.cpp:245 (B)
    ("FMMGetEpsilon_PolBasisNV", "plan"): "P04",     # NV.cpp:190 (B)
    ("FMMGetEpsilon_PolBasisVL", "plan"): "P05",     # VL.cpp:200 (B)
    ("FMMGetEpsilon_FFT", "exec"): "EX02",         # FFT.cpp:212 (B), plans[w] (NTH 2..5); NTH 1 is EX01 (plans[4], :183)
    ("FMMGetEpsilon_Kottke", "exec"): "EX04",      # kottke.cpp:287 (B), plans[w]; NTH 1 is EX03 (plans[4], :263)
    ("FMMGetEpsilon_PolBasisJones", "exec"): "EX05",  # Jones.cpp:258 (B), first of four exec sites; see note
    ("FMMGetEpsilon_PolBasisNV", "exec"): "EX10",    # NV.cpp:206 (B)
    ("FMMGetEpsilon_PolBasisVL", "exec"): "EX09",    # VL.cpp:215 (B)
}
R1_PLAN_EXEC_NOTE = (
    "FFT exec: NTH1 = return address of plans[4] (R1 EX01, FFT.cpp:183); NTH2..5 = return address of plans[w] "
    "(EX02, FFT.cpp:212).  kottke: NTH1 = EX03 (:263); NTH2..5 = EX04 (:287).  NV exec: NTH1..4 share ONE return "
    "address (a loop site), r1_id EX10 (NV.cpp:206).  VL exec: r1_id EX09 (VL.cpp:215).  Jones exec: NTH1..4 have four "
    "distinct return addresses, ordered ascending in both trees, which the R3 discovery does NOT tie to the four "
    "source lines 258/277/296/315 one by one.  Jones NTH1..4 are therefore labelled EX05-EX08 as a set (not "
    "individually confirmed).  This is an unconfirmed correspondence and is written as such."
)


def plan_exec_r1(caller, cat, nth, mode):
    """r1_id for a plan or exec point of an FMM caller.  Decided by caller, category and NTH (see the note).
    Returns NONE when the R1 registry has no point for it."""
    n = int(nth)
    if cat == "plan":
        return R1_PLAN_EXEC.get((caller, "plan"), "NONE")
    # exec
    if caller == "FMMGetEpsilon_FFT":
        return "EX01" if n == 1 else "EX02"
    if caller == "FMMGetEpsilon_Kottke":
        return "EX03" if n == 1 else "EX04"
    if caller == "FMMGetEpsilon_PolBasisJones":
        # four distinct return addresses; NTH1..4 -> EX05..EX08 as a set, not confirmed individually
        return "EX05-EX08(unconfirmed)" if n <= 4 else "NONE"
    if caller == "FMMGetEpsilon_PolBasisNV":
        return "EX10" if n <= 4 else "NONE"
    if caller == "FMMGetEpsilon_PolBasisVL":
        return "EX09" if n <= 4 else "NONE"
    return "NONE"


def load(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#") or line.startswith("route\t"):
                continue
            f = line.rstrip("\n").split("\t")
            if len(f) != 10:
                raise SystemExit("CALLSEQ row has %d fields: %r" % (len(f), line[:80]))
            rows.append(dict(zip(["route", "mode", "tree", "rep", "category", "nth", "size",
                                  "caller", "file", "ra"], f)))
    return rows


def main(argv):
    if len(argv) != 3:
        print("usage: r3_sitemap.py CALLSEQ_TSV SITEMAP_TSV", file=sys.stderr)
        return 2
    rows = load(argv[1])
    # key by route, mode, category, nth; collect per tree the (caller, size) seen
    seen = collections.defaultdict(lambda: collections.defaultdict(set))
    for r in rows:
        key = (r["route"], r["mode"], r["category"], int(r["nth"]))
        seen[key][r["tree"]].add((r["caller"], r["size"]))
    problems = []
    points = []
    for key in sorted(seen, key=lambda k: (k[1], k[0] != "once", k[2], k[3])):
        route, mode, cat, nth = key
        per = seen[key]
        if set(per) != {"B", "F"}:
            problems.append("point %s seen on trees %s only" % (key, sorted(per)))
            continue
        if per["B"] != per["F"]:
            problems.append("point %s: B=%s F=%s differ" % (key, sorted(per["B"]), sorted(per["F"])))
            continue
        (caller, size), = per["B"]  # exactly one (caller,size) per point per tree
        in_scope = "YES" if caller in FMM_CALLERS else "NO"
        size_out = size if cat == "malloc" else "-"
        r1 = "NONE"
        if in_scope == "YES":
            if cat == "malloc":
                r1 = R1_MAP.get((caller, cat, size), "NONE")
            else:
                r1 = plan_exec_r1(caller, cat, nth, mode)
        points.append((route, mode, cat, str(nth), size_out, caller, in_scope, r1))
    if problems:
        for p in problems:
            print("PROBLEM: " + p, file=sys.stderr)
        return 1
    # Merge the two routes into one row per (mode, category, nth): a point seen under route once is "first";
    # a point seen only under route twice is "second" (second field call / cache-hit route).  A point seen
    # under both routes with the same caller and size is "first" (the first call is the same site).
    # The two routes are NOT merged: the same NTH under route twice can be a different call than under route
    # once (route twice makes a second field call, so NTH 12-16 are FFT plans/execs there and GetFieldOnGrid
    # plans/execs under route once).  Each route therefore gets its own point_id, prefixed by the route.
    out_rows = []
    for route, mode, cat, nth, size_out, caller, in_scope, r1 in points:
        pid = "M-%s-%s-%s-%s" % (route, mode, cat, nth)
        note = ("route once: first field call" if route == "once"
                else "route twice: second field call / cache-hit path present")
        if in_scope == "NO":
            note += "; non-FMM caller (GetFieldOnGrid, rcwa.cpp), counted only"
        out_rows.append((pid, mode, cat, nth, size_out, caller, in_scope, r1, note))
    with open(argv[2], "w", encoding="utf-8") as fh:
        fh.write("# SITEMAP.tsv -- P05-S4 R3-2.  Generated by r3_sitemap.py from CALLSEQ.tsv (no injection).\n")
        fh.write("# point_id = M-<mode>-<category>-<NTH>.  NTH is the gdb global call index (equal to the injector counter).\n")
        fh.write("# in_D003_scope: YES = caller is an FMM epsilon function (S4/fmm/); NO = other caller, counted only.\n")
        fh.write("# r1_id: R1 registry id by source site (R1_MAP in r3_sitemap.py); NONE when no R1 point corresponds.\n")
        fh.write("point_id\tmode\tcategory\tNTH\tsize\tcaller_function\tin_D003_scope\tr1_id\tnote\n")
        for r in out_rows:
            fh.write("\t".join(r) + "\n")
    cnt = collections.Counter(r[6] for r in out_rows)
    print("points=%d in_scope_YES=%d in_scope_NO=%d" % (len(out_rows), cnt["YES"], cnt["NO"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
