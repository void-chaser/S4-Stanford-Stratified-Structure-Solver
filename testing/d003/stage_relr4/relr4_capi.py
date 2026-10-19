#!/usr/bin/env python3
# relr4_capi.py -- T4 of REL-R4 (P13 early check, NOT a P13 fix; task brief section 5.5).
#   build --tree T : compile testing/d003/stage_relr4/capi_fig12_relr4.c against tree T's build/libS4.a
#                    with the Linux link line from the task brief; and run the shipped
#                    examples/C_api/Makefile unchanged (expected rc=2 on Linux).
#   spec --tree T  : run the UNMODIFIED examples/C_api/spec.awk in a cwd that contains ./fig12, and compare
#                    its 35 rows with the committed examples/C_api/spec.awk.out.
#   posctrl --tree T : C --lua-sweep vs the tree's Lua tree/fig12.lua forward flux at 0.25..0.268 step 0.003.
#   report         : assemble CAPI_RELR4.tsv from the per-step observations.
# Pre-registered tolerances: reference |c-r| <= 5e-6*|r| + 1e-6 (5e-6 relative plus one %g last digit),
# frequency column identical, 35 rows; positive control relative difference <= 1e-10; B vs F4 byte identical.
import os, sys, subprocess, hashlib, datetime, time

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r4")
TREES = {"U": os.path.join(EV, "upstream", "S4"),
         "B": os.path.join(EV, "trees", "B"),
         "F4": os.path.join(EV, "trees", "F4"),
         "M": os.path.join(EV, "trees", "M"),
         "M2": os.path.join(EV, "trees", "M2"),
         "M3": os.path.join(EV, "trees", "M3")}
CAPI = os.path.join(EV, "capi")
UNITS = os.path.join(EV, "units_t4")
SRC = os.path.join(REPO, "testing/d003/stage_relr4/capi_fig12_relr4.c")
SPEC = os.path.join(REPO, "examples/C_api/spec.awk")
REFDATA = os.path.join(REPO, "examples/C_api/spec.awk.out")
LUA_SCRIPT = "examples/2d/Fan_PRB_65_2002/fig12.lua"
TAB = chr(9)
NL = chr(10)
TOL_REL = 5e-6
TOL_ABS = 1e-6
TOL_POS = 1e-10


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def write_unit(rec):
    os.makedirs(UNITS, exist_ok=True)
    keys = ["unit_id", "suite", "tree", "status", "rc", "detail", "extra", "utc"]
    out = os.path.join(UNITS, rec["unit_id"] + ".tsv")
    lines = ["# per-unit observation for REL-R4 T4; read by column name by relr4_verdict.py"]
    for k in keys:
        lines.append(k + TAB + str(rec.get(k, "")))
    open(out, "w", encoding="utf-8").write(NL.join(lines) + NL)


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build(tree):
    tdir = TREES[tree]
    outdir = os.path.join(CAPI, tree)
    os.makedirs(outdir, exist_ok=True)
    exe = os.path.join(outdir, "fig12")
    log = os.path.join(outdir, "build.log")
    cmd = ["gcc", "-O0", "-g", "-IS4", SRC, "-o", exe, "-Lbuild", "-lS4", "-llapack", "-lblas", "-lstdc++", "-lm"]
    with open(log, "w", encoding="utf-8") as fh:
        fh.write("# cwd=%s cmd=%s" % (tdir, " ".join(cmd)) + NL)
        p = subprocess.run(cmd, cwd=tdir, stdout=fh, stderr=subprocess.STDOUT)
    rc = p.returncode
    ok = rc == 0 and os.path.isfile(exe)
    write_unit({"unit_id": "T4_%s_build_capi" % tree, "suite": "T4_capi", "tree": tree,
                "status": "BUILD_OK" if ok else "BUILD_FAIL", "rc": rc,
                "detail": "gcc -O0 -g -IS4 capi_fig12_relr4.c -o fig12 -Lbuild -lS4 -llapack -lblas -lstdc++ -lm",
                "extra": "log=%s log_sha256=%s exe_sha256=%s" % (os.path.relpath(log, REPO), sha_f(log),
                                                                 sha_f(exe) if ok else "missing"),
                "utc": utcnow()})
    print("CAPI_BUILD %-2s rc=%d status=%s" % (tree, rc, "OK" if ok else "FAIL"))
    return 0 if ok else 1


def makefile(tree):
    tdir = os.path.join(TREES[tree], "examples", "C_api")
    outdir = os.path.join(CAPI, tree)
    os.makedirs(outdir, exist_ok=True)
    log = os.path.join(outdir, "original_makefile.log")
    with open(log, "w", encoding="utf-8") as fh:
        fh.write("# cwd=%s cmd=make (shipped examples/C_api/Makefile, unchanged)" % tdir + NL)
        p = subprocess.run(["make"], cwd=tdir, stdout=fh, stderr=subprocess.STDOUT)
    rc = p.returncode
    write_unit({"unit_id": "T4_%s_original_makefile" % tree, "suite": "T4_capi", "tree": tree,
                "status": "RC2" if rc == 2 else "RC%d" % rc, "rc": rc,
                "detail": "make in examples/C_api with the shipped macOS-only Makefile",
                "extra": "log=%s log_sha256=%s" % (os.path.relpath(log, REPO), sha_f(log)), "utc": utcnow()})
    print("CAPI_MAKEFILE %-2s rc=%d" % (tree, rc))
    return 0


def run_spec(tree):
    outdir = os.path.join(CAPI, tree)
    exe = os.path.join(outdir, "fig12")
    outp = os.path.join(outdir, "spec.awk.out")
    errp = os.path.join(outdir, "spec.awk.err")
    if not os.path.isfile(exe):
        write_unit({"unit_id": "T4_%s_spec_sweep" % tree, "suite": "T4_capi", "tree": tree,
                    "status": "UNAVAILABLE", "rc": "", "detail": "fig12 not built", "extra": "", "utc": utcnow()})
        print("CAPI_SPEC %-2s UNAVAILABLE (no binary)" % tree)
        return 0
    with open(outp, "wb") as fo, open(errp, "wb") as fe:
        p = subprocess.run(["awk", "-f", SPEC], cwd=outdir, stdin=subprocess.DEVNULL, stdout=fo, stderr=fe)
    rc = p.returncode
    # compare with the committed 2015 reference
    ref = []
    for line in open(REFDATA, encoding="utf-8"):
        f = line.split()
        if len(f) >= 2:
            ref.append((f[0], float(f[0]), float(f[1])))
    cur = []
    for line in open(outp, encoding="utf-8", errors="replace"):
        f = line.split()
        if len(f) >= 2:
            cur.append((f[0], float(f[0]), float(f[1])))
    rows_ok = len(cur) == 35 and len(ref) == 35
    freq_ok = rows_ok and all((a[0] == b[0] or abs(a[1] - b[1]) == 0.0) for a, b in zip(cur, ref))
    max_abs = 0.0
    max_rel = 0.0
    n_out = 0
    if rows_ok and freq_ok:
        for (_, _, cv), (_, _, rv) in zip(cur, ref):
            d = abs(cv - rv)
            max_abs = max(max_abs, d)
            if rv != 0:
                max_rel = max(max_rel, d / abs(rv))
            if d > TOL_REL * abs(rv) + TOL_ABS:
                n_out += 1
    ok = rc == 0 and rows_ok and freq_ok and n_out == 0
    write_unit({"unit_id": "T4_%s_spec_sweep" % tree, "suite": "T4_capi", "tree": tree,
                "status": "PASS_REF" if ok else ("REF_DRIFT" if rows_ok and freq_ok and rc == 0 else "FAIL"),
                "rc": rc,
                "detail": "rows=%d/35 freq_col_identical=%s rows_out_of_tol=%d max_abs_diff=%.6e max_rel_diff=%.6e"
                          % (len(cur), freq_ok, n_out, max_abs, max_rel),
                "extra": "out=%s sha=%s ref=%s" % (os.path.relpath(outp, REPO), sha_f(outp) if os.path.isfile(outp) else "missing",
                                                   os.path.relpath(REFDATA, REPO)),
                "utc": utcnow()})
    print("CAPI_SPEC %-2s rc=%d rows=%d freq_ok=%s out_of_tol=%d max_abs=%.3e max_rel=%.3e"
          % (tree, rc, len(cur), freq_ok, n_out, max_abs, max_rel))
    return 0


def run_posctrl(tree):
    tdir = TREES[tree]
    outdir = os.path.join(CAPI, tree)
    exe = os.path.join(outdir, "fig12")
    os.makedirs(outdir, exist_ok=True)
    lua_out = os.path.join(outdir, "lua_fig12.out")
    c_out = os.path.join(outdir, "c_lua_sweep.out")
    if not os.path.isfile(exe) or not os.path.isfile(os.path.join(tdir, "build", "S4")):
        write_unit({"unit_id": "T4_%s_posctrl_c_vs_lua" % tree, "suite": "T4_capi", "tree": tree,
                    "status": "UNAVAILABLE", "rc": "", "detail": "missing binary", "extra": "", "utc": utcnow()})
        print("CAPI_POSCTRL %-2s UNAVAILABLE" % tree)
        return 0
    with open(lua_out, "wb") as fo, open(os.path.join(outdir, "lua_fig12.err"), "wb") as fe:
        p = subprocess.run([os.path.join(tdir, "build", "S4"), os.path.join(tdir, LUA_SCRIPT)],
                           cwd=outdir, stdin=subprocess.DEVNULL, stdout=fo, stderr=fe)
    lua_rc = p.returncode
    with open(c_out, "wb") as fo, open(os.path.join(outdir, "c_lua_sweep.err"), "wb") as fe:
        p2 = subprocess.run([exe, "--lua-sweep"], cwd=outdir, stdin=subprocess.DEVNULL, stdout=fo, stderr=fe)
    c_rc = p2.returncode
    lua = []
    for line in open(lua_out, encoding="utf-8", errors="replace"):
        f = line.replace("\t", " ").split()
        if len(f) >= 2:
            try:
                lua.append((float(f[0]), float(f[1])))
            except ValueError:
                pass
    crows = []
    for line in open(c_out, encoding="utf-8", errors="replace"):
        f = line.split()
        if len(f) >= 2:
            crows.append((float(f[0]), float(f[1])))
    ok = lua_rc == 0 and c_rc == 0 and len(lua) == len(crows) == 7
    max_rel = 0.0
    max_freq_diff = 0.0
    if ok:
        for (lf, lv), (cf, cv) in zip(lua, crows):
            max_freq_diff = max(max_freq_diff, abs(lf - cf))
            d = abs(lv - cv) / max(abs(lv), abs(cv), 1e-300)
            max_rel = max(max_rel, d)
            if d > TOL_POS:
                ok = False
    write_unit({"unit_id": "T4_%s_posctrl_c_vs_lua" % tree, "suite": "T4_capi", "tree": tree,
                "status": "PASS" if ok else "FAIL", "rc": "%d/%d" % (c_rc, lua_rc),
                "detail": "lua_rows=%d c_rows=%d max_rel_diff=%.6e max_freq_abs_diff=%.3e"
                          % (len(lua), len(crows), max_rel, max_freq_diff),
                "extra": "lua_out=%s c_out=%s" % (os.path.relpath(lua_out, REPO), os.path.relpath(c_out, REPO)),
                "utc": utcnow()})
    print("CAPI_POSCTRL %-2s lua_rc=%d c_rc=%d lua_rows=%d c_rows=%d max_rel=%.3e"
          % (tree, lua_rc, c_rc, len(lua), len(crows), max_rel))
    return 0


def orig_example():
    """try to compile the ORIGINAL examples/C_api/main.c against each tree's headers; records rc and first errors"""
    outs = {}
    for tree, tdir in TREES.items():
        log = os.path.join(CAPI, tree, "original_main_compile.log")
        os.makedirs(os.path.dirname(log), exist_ok=True)
        with open(log, "w", encoding="utf-8") as fh:
            fh.write("# gcc -c -IS4 examples/C_api/main.c (original example, unchanged)" + NL)
            p = subprocess.run(["gcc", "-c", "-IS4", os.path.join(tdir, "examples", "C_api", "main.c"),
                                "-o", os.path.join(CAPI, tree, "original_main.o")],
                               cwd=tdir, stdout=fh, stderr=subprocess.STDOUT)
        errs = [l.strip() for l in open(log, encoding="utf-8", errors="replace") if ": error:" in l]
        outs[tree] = (p.returncode, errs[:3], log)
        write_unit({"unit_id": "T4_%s_original_main_compile" % tree, "suite": "T4_capi", "tree": tree,
                    "status": "RC%d" % p.returncode, "rc": p.returncode,
                    "detail": (errs[0][:220] if errs else "no error line"),
                    "extra": "log=%s log_sha256=%s" % (os.path.relpath(log, REPO), sha_f(log)), "utc": utcnow()})
        print("CAPI_ORIG_MAIN %-2s rc=%d first_error=%s" % (tree, p.returncode, errs[0][:120] if errs else "none"))
    return 0


def read_units():
    rows = {}
    if not os.path.isdir(UNITS):
        return rows
    for n in sorted(os.listdir(UNITS)):
        if not n.endswith(".tsv"):
            continue
        d = {}
        for line in open(os.path.join(UNITS, n), encoding="utf-8"):
            if not line.strip() or line.startswith("#"):
                continue
            k, _, v = line.rstrip(NL).partition(TAB)
            d[k] = v
        rows[d.get("unit_id", n)] = d
    return rows


def spec_values(tree):
    p = os.path.join(CAPI, tree, "spec.awk.out")
    vals = []
    if os.path.isfile(p):
        for line in open(p, encoding="utf-8", errors="replace"):
            f = line.split()
            if len(f) >= 2:
                try:
                    vals.append((float(f[0]), float(f[1])))
                except ValueError:
                    pass
    return vals


def report():
    u = read_units()
    rows = ["# CAPI_RELR4.tsv -- T4 C API results (P13 early check; not a completion or fix of P13)",
            "# Reference tolerance (pre-registered): |c - r| <= 5e-6*|r| + 1e-6, 35 rows, frequency column identical.",
            "# Positive control tolerance: relative difference <= 1e-10 at the seven fig12.lua frequency points.",
            TAB.join(["unit_id", "kind", "tree", "status", "rc", "detail"])]
    def kind_of(uid):
        for suf, kind in (("_build_capi", "build_new"), ("_original_makefile", "original_makefile"),
                          ("_original_main_compile", "original_example"), ("_spec_sweep", "spec_reference"),
                          ("_posctrl_c_vs_lua", "positive_control")):
            if uid.endswith(suf):
                return kind
        return "record"
    for uid in sorted(u):
        d = u[uid]
        tree = uid.split("_")[1]
        rows.append(TAB.join([uid, kind_of(uid), tree, d.get("status", ""), d.get("rc", ""), d.get("detail", "")]))
    # B vs F4 byte identical on the spec sweep output
    pb, pf = os.path.join(CAPI, "B", "spec.awk.out"), os.path.join(CAPI, "F4", "spec.awk.out")
    same = os.path.isfile(pb) and os.path.isfile(pf) and sha_f(pb) == sha_f(pf)
    rows.append(TAB.join(["T4CMP_B_vs_F4_byte_identical", "byte_identical", "B_vs_F4",
                          "SAME" if same else "DIFF", "", "sha_B=%s sha_F4=%s" % (
                              sha_f(pb) if os.path.isfile(pb) else "missing",
                              sha_f(pf) if os.path.isfile(pf) else "missing")]))
    # U vs F4 numeric comparison on the spec sweep (same output file format as the reference comparison)
    uv, fv = spec_values("U"), spec_values("F4")
    if uv and fv and len(uv) == len(fv):
        mx = 0.0
        for (uf, uval), (ff, fval) in zip(uv, fv):
            mx = max(mx, abs(uval - fval) / max(abs(uval), abs(fval), 1e-300))
        rows.append(TAB.join(["T4CMP_U_vs_F4_numeric", "u_vs_f4", "U_vs_F4", "OBSERVED", "",
                              "rows=%d max_rel_diff=%.6e" % (len(uv), mx)]))
    else:
        rows.append(TAB.join(["T4CMP_U_vs_F4_numeric", "u_vs_f4", "U_vs_F4", "UNAVAILABLE", "",
                              "U_rows=%d F4_rows=%d" % (len(uv), len(fv))]))
    for tree in ("U", "B", "F4"):
        d = u.get("T4_%s_original_main_compile" % tree, {})
        rows.append(TAB.join(["T4_%s_original_main_compile" % tree, "original_example", tree, d.get("status", "MISSING"),
                              d.get("rc", ""), d.get("detail", "")]))
    rows.append(TAB.join(["T4_RECORD_U_CAPI_EXAMPLE", "record", "U", "RECORD_ONLY", "",
                          "the shipped examples/C_api/main.c is written against the pre-P04 C API names; its compile attempts are recorded, not judged"]))
    out = os.path.join(EV, "CAPI_RELR4.tsv")
    if not os.path.realpath(out).startswith(os.path.join(REPO, "checkpoints/p05") + os.sep):
        raise SystemExit("WRITE_OUTSIDE " + out)
    open(out, "w", encoding="utf-8").write(NL.join(rows) + NL)
    print("WROTE " + os.path.relpath(out, REPO))
    return 0 if same else 1


def main():
    a = sys.argv[1:]
    if not a:
        print("usage: relr4_capi.py build|makefile|spec|posctrl --tree T | report")
        return 2
    if a[0] == "report":
        return report()
    if a[0] == "orig-example":
        return orig_example()
    tree = a[a.index("--tree") + 1]
    if a[0] == "build":
        return build(tree)
    if a[0] == "makefile":
        return makefile(tree)
    if a[0] == "spec":
        return run_spec(tree)
    if a[0] == "posctrl":
        return run_posctrl(tree)
    print("unknown mode " + a[0])
    return 2


if __name__ == "__main__":
    sys.exit(main())