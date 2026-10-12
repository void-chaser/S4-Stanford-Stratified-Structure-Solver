#!/usr/bin/env python3
"""P05-S4 R7 cont8 ADD1 step 2 (U75b): independent expected environment from the history rules (new file).

expected_env_from_history(group, point_id, tree, request_from_source=None) returns the environment the driver must receive.
It derives everything from the point id and the historical rules, NOT from REGISTRY_S4_PRE_R7_M2_ADD_v2/v3:
  G1 injection  : category, NTH and route parsed from the point id "M-<route>-<mode>-<category>-<NTH>-<tree>".
                  request = {malloc: s4malloc, plan: plan, exec: exec}[category]   (run_r3_sweep.py:32)
                  case    = ("t4/" if route == twice else "r3/") + source id     (run_r3_sweep.py:117-118)
                  S4FMM_TWICE = slab iff route == twice                          (matrix_r2.py:107-108 via case t4/)
                  S4FMM_NTH   = NTH                                              (matrix_r2.py:102-103)
  G1 control    : CTL-<mode>-<tree>; no S4FMM_INJECT and no S4FMM_NTH           (run_r3_sweep.py:129-133: request "-", nth "-")
  G2c injection : same parsing rule as G1 (run_r4_regress.py:74-81)
  G2a           : request from registries/s4r4/RESULTS_R4.tsv (request column, matched by source id); nth "-" and no TWICE
                  (run_r4_matrix.py:101-102; matrix_r2.py:102 sets NTH only for nth not "-").
  CTRL_SEAM     : FMM_MODE from the registered mode (fft), S4FMM_NG 9; no INJECT, NTH or TWICE.

The module imports matrix_r2 only to CHECK the rule (the expected value is written here, from the history, and compared with
matrix_r2.build_env(row) by the caller).  It does not read any ADD file.
Usage: imported by run_m2b_all_r7.py; also runnable on its own for a self-test (read only).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
REG = os.path.join(REPO, "checkpoints", "p05", "registries")
R4_RESULTS = os.path.join(REG, "s4r4", "RESULTS_R4.tsv")
REQUEST_OF_CATEGORY = {"malloc": "s4malloc", "plan": "plan", "exec": "exec"}  # run_r3_sweep.py:32
CATEGORIES = ("malloc", "plan", "exec")


def parse_injection_id(point_id):
    """Parse M-<route>-<mode>-<category>-<NTH>-<tree> (tree suffix stripped by the caller or here).
    Returns (route, mode, category, nth).  Refuses any id that does not match the historical shape."""
    parts = point_id.split("-")
    if len(parts) < 5 or parts[0] != "M":
        raise ValueError("not an injection id: %r" % point_id)
    if parts[-1] in ("F", "F2"):
        parts = parts[:-1]  # the tree suffix (ADD point ids end in -F or -F2)
    route, mode, category, nth = parts[1], parts[2], parts[3], parts[4]
    if route not in ("once", "twice"):
        raise ValueError("route %r in %r" % (route, point_id))
    if category not in CATEGORIES:
        raise ValueError("category %r in %r" % (category, point_id))
    if not nth.isdigit():
        raise ValueError("NTH %r in %r" % (nth, point_id))
    return route, mode, category, int(nth)


def source_id(point_id):
    """The source id without the tree suffix (point ids of the v2 table end in -F or -F2)."""
    if point_id.endswith("-F2"):
        return point_id[:-3]
    if point_id.endswith("-F"):
        return point_id[:-2]
    return point_id


def r4_request_table():
    """{source id: request} from RESULTS_R4.tsv (G2a).  Keyed by the point id without its tree suffix.  Read only."""
    out = {}
    header = None
    with open(R4_RESULTS, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                header = f
                continue
            d = dict(zip(header, f))
            if d["tree"] != "F":
                continue  # G2a runs tree F only (U61); B and A rows of the same source id carry other requests
            pid = d["point_id"]
            # RESULTS_R4 rows: point_id "R4-SI01-F" with tree "F"; the base id drops the trailing "-F"
            base = pid[:-len("-F")] if pid.endswith("-F") else pid
            if base in out and out[base] != d["request"]:
                raise ValueError("two F rows with different requests for %r" % base)  # not expected; refuse
            out[base] = d["request"]
    return out


_R4 = None


def expected_env_from_history(group, point_id, tree, mode=None):
    """The expected driver environment, derived from the history (U75b).  Keys: FMM_MODE, S4FMM_NG, and the optional
    S4FMM_INJECT, S4FMM_NTH, S4FMM_TWICE.  A key absent from the dict means the variable must be absent in the environment."""
    global _R4
    if group == "CTRL_SEAM":
        return {"FMM_MODE": mode or "fft", "S4FMM_NG": "9"}
    if group in ("G1", "G2c") and point_id.startswith("CTL-"):
        mode_name = point_id.split("-")[1]
        return {"FMM_MODE": mode_name, "S4FMM_NG": "9"}
    if group in ("G1", "G2c"):
        route, pmode, category, nth = parse_injection_id(point_id)
        env = {"FMM_MODE": pmode, "S4FMM_NG": "9",
               "S4FMM_INJECT": REQUEST_OF_CATEGORY[category],
               "S4FMM_NTH": str(nth)}
        if route == "twice":
            env["S4FMM_TWICE"] = "slab"
        return env
    if group == "G2a":
        if _R4 is None:
            _R4 = r4_request_table()
        # ADD id "R4-SI01-F-F" (two tree suffixes: the source point "R4-SI01-F" and the tree "F") -> source "R4-SI01".
        # RESULTS_R4 rows are keyed the same way (point_id "R4-SI01-F" with tree F, base "R4-SI01").
        base = point_id[:-len("-" + tree)] if point_id.endswith("-" + tree) else point_id
        base = base[:-len("-F")] if base.endswith("-F") else base
        if base not in _R4:
            raise ValueError("G2a source id %r not in RESULTS_R4" % base)
        req = _R4[base]
        if req in ("-", ""):
            raise ValueError("G2a request missing for %r" % base)
        # run_r4_matrix.py:101-102: nth "-", no TWICE (case = point id, no t4/ prefix)
        return {"FMM_MODE": mode or "fft", "S4FMM_NG": "9", "S4FMM_INJECT": req}
    raise ValueError("no history rule for group %r" % group)


def self_test(argv):
    """Read-only check of the rule on three ids (no S4 run).  Prints the expected environments."""
    for g, pid, t in (("G2c", "M-twice-fft-plan-2-F", "F"), ("G1", "M-once-fft-plan-3-F", "F"),
                      ("G1", "CTL-closed1d-F", "F"), ("G2a", "R4-SI01-F-F", "F")):
        print("%s %s %s -> %s" % (g, pid, t, expected_env_from_history(g, pid, t)))
    return 0


if __name__ == "__main__":
    sys.exit(self_test(sys.argv))
