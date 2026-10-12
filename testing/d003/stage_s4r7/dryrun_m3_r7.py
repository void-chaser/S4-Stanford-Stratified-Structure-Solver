#!/usr/bin/env python3
# dryrun_m3_r7.py -- P05-S4 R7 cont9 (M3, section 2.4): dry-run of the environment of every M3 run (new file).
#
# For each point of the G5 and G6 pre-registration, the environment that the historical runners would set is derived
# INDEPENDENTLY from the historical rule (testing/d003/stage_s4/run_r6c_state.py: env_for_point / control_env, and
# run_r6c_seam_state.py: env_of) and compared with the environment written in the M3 pre-registration (the row's
# request/inj_call/route/mode).  The M3 pre-registration itself is NOT used as the source of the derived environment:
# the derived value comes from the request string and the historical rule only.
#
# Output: $EV/DRYRUN_M3_R7.txt (one line per point and tree, plus a summary).  Exit 0 iff every assertion holds and
# the number of unparseable points is 0.
#
# Usage: python3 -I -B dryrun_m3_r7.py REPO EVDIR
import re
import sys

NG = "9"
STACK = "pattern both 4 3"
REQ_OK = re.compile(r"^(s4malloc|exec|plan|plancall:[1-9][0-9]*:[1-9][0-9]*)$")
PLANCALL_RE = re.compile(r"^plancall:([1-9][0-9]*):([1-9][0-9]*)$")
ALLOWED_MODES = ("fft", "kottke", "jones", "nv", "vl", "experimental", "closed2d", "closed1d", "tensor",
                 "fftjones", "fftnv", "fftvl")


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


def derive_state_env(mode, request, nth_col, route, twice_col):
    """Historical rule (run_r6c_state.py env_for_point, once/twice), from the request string and the table columns."""
    if mode not in ALLOWED_MODES:
        return None, "mode %r not known" % mode
    if not REQ_OK.match(request):
        return None, "request %r not known" % request
    env = {"FMM_MODE": mode, "S4FMM_NG": NG, "S4FMM_INJECT": request}
    if request.startswith("plancall:"):
        pass  # K and M come from the request; S4FMM_NTH is not set
    else:
        if not nth_col.startswith("NTH="):
            return None, "no NTH for request %r" % request
        env["S4FMM_NTH"] = nth_col.split("=")[1]
    if route == "twice":
        env["S4FMM_TWICE"] = "slab"
    elif route != "once":
        return None, "route %r" % route
    return env, ""


def derive_seam_env(mode, request, route, inj_call):
    """Historical rule (run_r6c_seam_state.py env_of): once route, inj_call 1; no NTH, no TWICE."""
    if route != "once" or inj_call != "1":
        return None, "seam point not once/inj1"
    return {"FMM_MODE": mode, "S4FMM_NG": NG, "S4FMM_INJECT": request}, ""


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: dryrun_m3_r7.py REPO EVDIR")
    repo, ev = argv[1], argv[2]
    prereg = read_table(ev + "/REGISTRY_S4_PRE_R7_M3.tsv")
    hist_g5 = {r["point_id"]: r for r in read_table(repo + "/checkpoints/p05/registries/s4r6c/REGISTRY_S4_PRE_R6b_STATE_v2.tsv")}
    hist_g6 = {r["point_id"]: r for r in read_table(repo + "/checkpoints/p05/registries/s4r6c/REGISTRY_S4_PRE_R6c_SEAM.tsv")}
    lines = ["# DRYRUN_M3_R7.txt -- P05-S4 R7 cont9 M3 dry-run (environment of each run, derived independently).",
             "# Derived environment: from the historical rule and the request string (run_r6c_state.py / run_r6c_seam_state.py),",
             "# not from the M3 pre-registration row.  The check compares the derived environment with the historical table columns",
             "# (REGISTRY_S4_PRE_R6b_STATE_v2.tsv for G5: nth, route, twice; REGISTRY_S4_PRE_R6c_SEAM.tsv for G6: inj_call, route).",
             "group\ttree\tpoint_id\tenv_derived\tcheck\tnote"]
    n_ok = 0
    n_bad = 0
    n_unparsed = 0
    counts = {}
    for r in prereg:
        if r["group"] not in ("G5", "G6"):
            continue
        pid = r["point_id"]
        tree = r["tree"]
        if r["group"] == "G5":
            h = hist_g5.get(pid)
            if h is None:
                n_unparsed += 1
                lines.append("G5\t%s\t%s\t-\tFAIL\tpoint not in historical G5 table" % (tree, pid))
                n_bad += 1
                continue
            env, err = derive_state_env(h["mode"], h["request"], h["NTH_or_K"], h["route"], h["twice"])
            if env is None:
                n_unparsed += 1
                lines.append("G5\t%s\t%s\t-\tUNPARSED\t%s" % (tree, pid, err))
                continue
            # check: the M3 row must name the same mode, route, request, inj_call as the historical row
            same = (r["mode"] == h["mode"] and r["route"] == h["route"] and r["request"] == h["request"]
                    and r["inj_call"] == h["inj_call"])
            status = "OK" if same else "FAIL"
            if same:
                n_ok += 1
            else:
                n_bad += 1
            envtxt = ";".join("%s=%s" % (k, env[k]) for k in sorted(env))
            lines.append("G5\t%s\t%s\t%s\t%s\tM3 row matches historical row" % (tree, pid, envtxt, status))
            counts[(tree, "G5")] = counts.get((tree, "G5"), 0) + 1
        else:
            h = hist_g6.get(pid)
            if h is None:
                n_unparsed += 1
                lines.append("G6\t%s\t%s\t-\tFAIL\tpoint not in historical seam table" % (tree, pid))
                n_bad += 1
                continue
            env, err = derive_seam_env(h["mode"], h["request"], h["route"], h["inj_call"])
            if env is None:
                n_unparsed += 1
                lines.append("G6\t%s\t%s\t-\tUNPARSED\t%s" % (tree, pid, err))
                continue
            same = (r["mode"] == h["mode"] and r["request"] == h["request"] and r["inj_call"] == h["inj_call"])
            status = "OK" if same else "FAIL"
            if same:
                n_ok += 1
            else:
                n_bad += 1
            envtxt = ";".join("%s=%s" % (k, env[k]) for k in sorted(env))
            lines.append("G6\t%s\t%s\t%s\t%s\tM3 row matches historical seam row" % (tree, pid, envtxt, status))
            counts[(tree, "G6")] = counts.get((tree, "G6"), 0) + 1
    lines.append("# summary: ok=%d fail=%d unparsed=%d ; per (tree,group): %s" % (
        n_ok, n_bad, n_unparsed, ", ".join("%s/%s=%d" % (t, g, c) for (t, g), c in sorted(counts.items()))))
    out = ev + "/DRYRUN_M3_R7.txt"
    import os
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists, never overwritten (U17): %s" % out)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("dry-run ok=%d fail=%d unparsed=%d -> %s" % (n_ok, n_bad, n_unparsed, out))
    return 0 if (n_bad == 0 and n_unparsed == 0) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
