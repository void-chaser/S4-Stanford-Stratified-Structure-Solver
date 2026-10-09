#!/usr/bin/env python3
"""D002 native RNP contract runner: real Eigensystems.cpp, frozen PLAN.json.

The driver (tools/d002_driver.cpp) #includes the real S4/RNP/Eigensystems.cpp from
a chosen source tree (-DD002_SRC) and calls the real RNP entry points.  This runner
only compiles, feeds the frozen case table, and judges the raw output against the
frozen thresholds in PLAN.json (eig_rel_tol, residual_tol, vector_norm_tol).
Thresholds are never changed here.

Variants (source tree x build identity):
  ord_*   project flags (-O3 -march=native ...), production-like
  asan_*  ASan+UBSan diagnostic build (-O1 -g)
  seam_*  asan build plus -DD002_TEST_SEAM (RNP-level zhseqr_ status override,
          test-only; never present in a normal build)

Judging rules (fixed here, applied identically to every variant):
  API cases, seam_mode 0:
    driver rc 0, no error line, info == 0, eigenvalues match the analytic
    reference as a multiset with error / max|lambda_ref| <= eig_rel_tol,
    right vectors: residual max|A v - lambda v| / (max|A| * ||v||_2) <= residual_tol,
    left vectors:  residual max|A^H y - conj(lambda) y| / (max|A| * ||y||_2) <= residual_tol,
    and | ||v||_2 - 1 | <= vector_norm_tol for every returned vector.
  API cases, seam_mode != 0:
    info == seam_info (the forced status) and the real status seam_last_real_info == 0.
  HELPER_GEBAK cases: the zgebak output equals an independent 1-based LAPACK
    model (scaling then permutation) applied to the zgebal ilo/ihi/scale that the
    driver reports; unused padding keeps its sentinel.  Tolerance 1e-12 relative.
  Any run whose stderr shows a sanitizer report counts as a failure.

Usage:
  python3 -I -B run_d002.py build --src-root SRC --variant NAME --out-dir DIR
  python3 -I -B run_d002.py run   --variant NAME --bin BIN --run-dir DIR [--cases all|ID,ID]
  python3 -I -B run_d002.py judge --variant NAME --run-dir DIR
  python3 -I -B run_d002.py positives --out-dir DIR
"""

import argparse
import cmath
import datetime
import hashlib
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVER = os.path.join(HERE, "tools", "d002_driver.cpp")
PLAN_PATH = os.path.join(HERE, "PLAN.json")
MATRICES_PATH = os.path.join(HERE, "cases", "matrices.json")

PROJ_FLAGS = ["-O3", "-Wall", "-march=native", "-fcx-limited-range", "-fno-exceptions", "-fPIC"]
SAN_FLAGS = ["-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
             "-fcx-limited-range"]

VARIANTS = {
    "ord": (PROJ_FLAGS, []),
    "asan": (SAN_FLAGS, []),
    "seam_asan": (SAN_FLAGS, ["-DD002_TEST_SEAM"]),
}
SANITIZER_MARKERS = ("AddressSanitizer", "runtime error:", "LeakSanitizer")
CASE_TIMEOUT_S = 60
# Registered in PLAN.json as contract-boundary probes: recorded, not judged.
CONTRACT_PROBES = {"A-10r"}


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_plan():
    with open(PLAN_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def load_matrices():
    with open(MATRICES_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def cplx_of(pair):
    return complex(float(pair[0]), float(pair[1]))


def matrix_of(mats, mid):
    m = mats["matrices"][mid]
    n, lda = m["n"], m["lda"]
    vals = [cplx_of(v) for v in m["values"]]
    A = [[0j] * n for _ in range(n)]
    for j in range(n):
        for i in range(n):
            A[i][j] = vals[i + j * lda]
    return A, n, lda


def cmd_build(args):
    src_root = os.path.realpath(args.src_root)
    cpp = os.path.join(src_root, "S4", "RNP", "Eigensystems.cpp")
    if variant_kind(args.variant) is None:
        sys.exit("unknown variant %r" % args.variant)
    flags, defs = VARIANTS[variant_kind(args.variant)]
    os.makedirs(args.out_dir, exist_ok=True)
    out = os.path.join(args.out_dir, "d002_%s" % args.variant)
    src_for_build = cpp
    derived = None
    if "-DD002_TEST_SEAM" in defs:
        # Seam tree: only the single file-scope DEFINITION is renamed; the three
        # call sites keep the name zhseqr_, which the driver's wrapper provides.
        raw = open(cpp, "rb").read()
        needle = b"static int zhseqr_(char job, char compz"
        if raw.count(needle) != 1:
            sys.exit("seam derivation: expected exactly one zhseqr_ definition, found %d"
                     % raw.count(needle))
        derived_bytes = raw.replace(needle, b"static int d002_inner_zhseqr_(char job, char compz")
        seam_dir = os.path.join(args.out_dir, "seam_src_%s" % args.variant)
        os.makedirs(seam_dir, exist_ok=True)
        src_for_build = os.path.join(seam_dir, "Eigensystems.cpp")
        open(src_for_build, "wb").write(derived_bytes)
        derived = {"derived_from": cpp, "derived_path": src_for_build,
                   "derived_sha256": sha256_file(src_for_build),
                   "rule": "rename the single definition zhseqr_ -> d002_inner_zhseqr_"}
    argv = (["g++"] + flags +
            ["-I", os.path.join(src_root, "S4", "RNP"), "-I", os.path.join(src_root, "S4"),
             '-DD002_SRC="%s"' % src_for_build] + defs + [DRIVER, "-o", out])
    pr = subprocess.run(argv, capture_output=True, text=True)
    rec = {"variant": args.variant, "src_root": src_root, "eigensystems": cpp,
           "eigensystems_sha256": sha256_file(cpp), "argv": argv, "exit": pr.returncode,
           "stderr": pr.stderr, "built_utc": utcnow(), "seam_derivation": derived}
    if pr.returncode == 0:
        rec["binary"] = out
        rec["binary_sha256"] = sha256_file(out)
    with open(os.path.join(args.out_dir, "BUILD_%s.json" % args.variant), "w") as fh:
        json.dump(rec, fh, indent=1, sort_keys=True)
    print("build %s exit=%d sha=%s" % (args.variant, pr.returncode, rec.get("binary_sha256", "-")))
    return pr.returncode


def variant_kind(variant):
    for kind in ("seam_asan", "asan", "ord"):
        if variant == kind or variant.startswith(kind + "_"):
            return kind
    return None


def write_spec(path, case, matrix_file, variant):
    lines = ["case_id %s" % case["case_id"], "entry %s" % case["entry"],
             "matrix %s" % case["matrix"], "matrix_file %s" % matrix_file,
             "variant %s" % variant]
    if case["entry"] == "API":
        n = case.get("_n")
        lines += ["want %s" % case["want"], "work_mode %s" % case["work_mode"],
                  "rwork_mode %s" % case["rwork_mode"],
                  "seam_mode %s" % case.get("seam_mode", 0),
                  "seam_info %s" % case.get("seam_info", 0),
                  "ldvl %d" % (case.get("ldvl") or n), "ldvr %d" % (case.get("ldvr") or n)]
    else:
        lines += ["side %s" % case["side"], "job %s" % case["job"],
                  "m %d" % case["m"], "ldv %d" % case["ldv"]]
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def write_matrix_file(path, mid, mats):
    m = mats["matrices"][mid]
    lines = ["matrix %s" % mid, "%d %d" % (m["n"], m["lda"])]
    for v in m["values"]:
        lines.append("%s %s" % (v[0], v[1]))
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def parse_out(path):
    rows = {}
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            parts = line.split()
            if not parts:
                continue
            key = parts[0]
            if len(parts) == 2:
                rows.setdefault(key, parts[1])
            elif len(parts) == 4 and key in ("w", "vl_flat", "vr_flat", "work0", "v_flat"):
                rows.setdefault(key, []).append((int(parts[1]), complex(float(parts[2]), float(parts[3]))))
            else:
                rows.setdefault(key, " ".join(parts[1:]))
    return rows


def cmd_run(args):
    plan = load_plan()
    mats = load_matrices()
    run_dir = os.path.realpath(args.run_dir)
    vdir = os.path.join(run_dir, args.variant)
    os.makedirs(os.path.join(vdir, "specs"), exist_ok=True)
    os.makedirs(os.path.join(vdir, "outs"), exist_ok=True)
    os.makedirs(os.path.join(vdir, "matrices"), exist_ok=True)
    wanted = None if args.cases in (None, "all") else set(args.cases.split(","))
    summary = []
    for case in plan["cases"]:
        if wanted is not None and case["case_id"] not in wanted:
            continue
        mid = case["matrix"]
        mfile = os.path.join(vdir, "matrices", "%s.txt" % mid)
        if not os.path.exists(mfile):
            write_matrix_file(mfile, mid, mats)
        case = dict(case)
        case["_n"] = mats["matrices"][mid]["n"]
        spec = os.path.join(vdir, "specs", "%s.spec" % case["case_id"])
        out = os.path.join(vdir, "outs", "%s.out" % case["case_id"])
        write_spec(spec, case, mfile, args.variant)
        if os.path.exists(out):
            os.remove(out)
        try:
            pr = subprocess.run([args.bin, spec, out], capture_output=True, text=True,
                                timeout=CASE_TIMEOUT_S, cwd=vdir)
            rc, err = pr.returncode, pr.stderr
        except subprocess.TimeoutExpired as exc:
            rc = "timeout"
            err = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        open(os.path.join(vdir, "outs", "%s.stderr" % case["case_id"]), "w").write(err or "")
        summary.append({"case_id": case["case_id"], "rc": rc})
    with open(os.path.join(vdir, "RUN_INDEX.json"), "w") as fh:
        json.dump({"variant": args.variant, "bin": args.bin,
                   "bin_sha256": sha256_file(args.bin), "run_utc": utcnow(),
                   "cases": summary}, fh, indent=1, sort_keys=True)
    print("run %s: %d cases executed" % (args.variant, len(summary)))
    return 0


def check_eigs(w_list, n, ref_vals, tol):
    if n == 0:
        return True, 0.0
    w = [z for _, z in sorted(w_list)]
    ref = [complex(float(a), float(b)) for a, b in ref_vals]
    scale = max([abs(z) for z in ref] + [1e-300])
    left = list(w)
    worst = 0.0
    for r in ref:
        best = min(range(len(left)), key=lambda k: abs(left[k] - r))
        worst = max(worst, abs(left[best] - r) / scale)
        del left[best]
    return worst <= tol, worst


def check_vectors(flat, n, ld, w, A, side, tol_res, tol_norm):
    """flat: list of (idx, value) column-major with leading dimension ld."""
    if n == 0:
        return True, 0.0, 0.0
    arr = {i: z for i, z in flat}
    amax = max(abs(A[i][j]) for i in range(n) for j in range(n)) or 1e-300
    worst_res = 0.0
    worst_norm = 0.0
    for j in range(n):
        v = [arr.get(i + j * ld, 0j) for i in range(n)]
        nv = math.sqrt(sum(abs(x) ** 2 for x in v))
        worst_norm = max(worst_norm, abs(nv - 1.0))
        lam = w[j]
        if side == "R":
            r = [sum(A[i][k] * v[k] for k in range(n)) - lam * v[i] for i in range(n)]
        else:
            r = [sum(A[k][i].conjugate() * v[k] for k in range(n)) - lam.conjugate() * v[i]
                 for i in range(n)]
        worst_res = max(worst_res, max(abs(x) for x in r) / (amax * max(nv, 1e-300)))
    return (worst_res <= tol_res and worst_norm <= tol_norm), worst_res, worst_norm


def lapack_helper_model(n, ilo, ihi, scale, side, job, v_init, m, ldv):
    """Independent 1-based LAPACK zgebak model: scaling, then permutation."""
    V = [[v_init(i) for _ in range(m)] for i in range(n)]
    if ilo != ihi and job in ("S", "B"):
        for i in range(ilo, ihi + 1):
            f = scale[i] if side == "R" else 1.0 / scale[i]
            V[i - 1] = [x * f for x in V[i - 1]]
    if job in ("P", "B"):
        for ii in range(1, n + 1):
            i = ii
            if ilo <= i <= ihi:
                continue
            if i < ilo:
                i = ilo - ii
            k = int(scale[i])
            if k != i:
                V[i - 1], V[k - 1] = V[k - 1], V[i - 1]
    return V


def judge_helper(case, rows, mats, plan_th):
    n = mats["matrices"][case["matrix"]]["n"]
    m, ldv = case["m"], case["ldv"]
    if ldv < n:
        ldv = n
    if "ilo_1based" not in rows:
        return False, "no zgebal output"
    ilo, ihi = int(rows["ilo_1based"]), int(rows["ihi_1based"])
    scale = [0.0] + [float(x) for x in rows["scale"].split()]
    got = {i: z for i, z in rows.get("v_flat", [])}
    alloc = max(n, 1) * ldv
    ref_V = lapack_helper_model(n, ilo, ihi, scale, case["side"], case["job"],
                                lambda i: 1000.0 + i, m, ldv)
    worst = 0.0
    for idx in range(alloc):
        col, row = divmod(idx, ldv)
        if row < n and col < m:
            expect = ref_V[row][col]
        else:
            expect = -777.0
        g = got.get(idx, None)
        if g is None:
            return False, "missing element %d" % idx
        worst = max(worst, abs(g.real - expect) / max(1.0, abs(expect)))
    return worst <= 1e-12, "max_rel_err=%.3g" % worst


def cmd_judge(args):
    plan = load_plan()
    mats = load_matrices()
    th = plan["thresholds"]
    run_dir = os.path.realpath(args.run_dir)
    vdir = os.path.join(run_dir, args.variant)
    results = []
    try:
        ran = {c["case_id"] for c in json.load(open(os.path.join(vdir, "RUN_INDEX.json")))["cases"]}
    except (OSError, KeyError, ValueError):
        ran = None
    for case in plan["cases"]:
        cid = case["case_id"]
        if ran is not None and cid not in ran:
            continue
        out_path = os.path.join(vdir, "outs", "%s.out" % cid)
        err_path = os.path.join(vdir, "outs", "%s.stderr" % cid)
        err = open(err_path, encoding="utf-8", errors="replace").read() if os.path.exists(err_path) else ""
        rows = parse_out(out_path)
        rec = {"case_id": cid, "entry": case["entry"], "matrix": case["matrix"],
               "group": case["group"], "pass": False, "detail": "", "status": "judged"}
        sanit = [mk for mk in SANITIZER_MARKERS if mk in err]
        if cid in CONTRACT_PROBES:
            # Registered contract-boundary probe: recorded, never part of pass/fail.
            rec["status"] = "recorded"
            rec["detail"] = "contract probe; rc=%s sanitizer=%s" % (
                rec_rc(vdir, cid), ",".join(sanit) or "none")
            results.append(rec)
            continue
        if int(case.get("seam_mode", 0)) != 0 and "seam" not in args.variant:
            rec["status"] = "not_applicable"
            rec["detail"] = "seam case; this build has no seam"
            results.append(rec)
            continue
        if not rows:
            rec["detail"] = "no output"
            results.append(rec)
            continue
        if rows.get("driver_rc") not in (None, "0"):
            rec["detail"] = "driver_rc=%s" % rows.get("driver_rc")
        elif "error" in rows:
            rec["detail"] = "error=%s" % rows["error"]
        elif sanit:
            rec["detail"] = "sanitizer report: %s" % ",".join(sanit)
        elif case["entry"] == "HELPER_GEBAK":
            ok, det = judge_helper(case, rows, mats, th)
            rec["pass"], rec["detail"] = ok, det
        else:
            n = int(rows.get("n", "0"))
            info = int(rows.get("info", "-999"))
            if int(case.get("seam_mode", 0)) != 0:
                exp_info = int(case.get("seam_info", 0))
                ok = info == exp_info and rows.get("seam_last_real_info") == "0"
                rec["pass"] = ok
                rec["detail"] = "info=%d expected_forced=%d real_last=%s" % (
                    info, exp_info, rows.get("seam_last_real_info"))
            elif case.get("work_mode") == "query":
                # RNP returns after the workspace query: the contract is work[0] == 2n.
                w0 = rows.get("work0", [])
                want0 = complex(2 * n, 0)
                ok_q = bool(w0) and abs(w0[0][1] - want0) == 0.0
                rec["pass"] = bool(info == 0 and ok_q)
                rec["detail"] = "info=%d work0=%s expected=%s" % (
                    info, w0[0][1] if w0 else None, want0)
            else:
                ref = mats["eigenvalue_reference"][case["matrix"]]["values"]
                w = rows.get("w", [])
                ok_e, err_e = check_eigs(w, n, ref, th["eig_rel_tol"])
                ok_v = True
                det = "info=%d eig_rel_err=%.3g" % (info, err_e)
                want = case["want"]
                A, _, _ = matrix_of(mats, case["matrix"])
                wl = [z for _, z in sorted(w)]
                if want in ("vr", "both"):
                    ok_r, rr, rn = check_vectors(rows.get("vr_flat", []), n,
                                                 int(case.get("ldvr") or n), wl, A, "R",
                                                 th["residual_tol"], th["vector_norm_tol"])
                    ok_v = ok_v and ok_r
                    det += " vr_res=%.3g vr_norm_err=%.3g" % (rr, rn)
                if want in ("vl", "both"):
                    ok_l, lr, ln = check_vectors(rows.get("vl_flat", []), n,
                                                 int(case.get("ldvl") or n), wl, A, "L",
                                                 th["residual_tol"], th["vector_norm_tol"])
                    ok_v = ok_v and ok_l
                    det += " vl_res=%.3g vl_norm_err=%.3g" % (lr, ln)
                rec["pass"] = bool(info == 0 and ok_e and ok_v)
                rec["detail"] = det
        results.append(rec)
    judged = [r for r in results if r["status"] == "judged"]
    passed = sum(1 for r in judged if r["pass"])
    summary = {"variant": args.variant, "judged_utc": utcnow(), "thresholds": th,
               "cases_total": len(results), "cases_judged": len(judged),
               "cases_pass": passed, "cases_fail": len(judged) - passed,
               "cases_not_applicable": sum(1 for r in results if r["status"] == "not_applicable"),
               "cases_recorded_probe": sum(1 for r in results if r["status"] == "recorded"),
               "results": results}
    with open(os.path.join(vdir, "JUDGE_%s.json" % args.variant), "w") as fh:
        json.dump(summary, fh, indent=1, sort_keys=True)
    print("judge %s: pass=%d fail=%d judged=%d not_applicable=%d probes_recorded=%d" % (
        args.variant, passed, len(judged) - passed, len(judged),
        summary["cases_not_applicable"], summary["cases_recorded_probe"]))
    for r in results:
        if r["status"] == "judged" and not r["pass"]:
            print("  FAIL %-6s %-8s %s" % (r["case_id"], r["entry"], r["detail"]))
    return 0 if passed == len(judged) else 1


def rec_rc(vdir, cid):
    try:
        idx = json.load(open(os.path.join(vdir, "RUN_INDEX.json")))
        return [c["rc"] for c in idx["cases"] if c["case_id"] == cid][0]
    except (OSError, IndexError, KeyError, ValueError):
        return "unknown"


def cmd_positives(args):
    """Sanitizer positive controls: each must report its registered signature."""
    os.makedirs(args.out_dir, exist_ok=True)
    cases = [
        ("pos_asan", ["-O1", "-g", "-fsanitize=address", "-fno-omit-frame-pointer"],
         os.path.join(HERE, "tools", "pos_asan.cpp"), "AddressSanitizer: heap-buffer-overflow"),
        ("pos_ubsan", ["-O1", "-g", "-fsanitize=undefined", "-fno-omit-frame-pointer"],
         os.path.join(HERE, "tools", "pos_ubsan.cpp"), "runtime error: signed integer overflow"),
        ("pos_asan_ubsan", SAN_FLAGS, os.path.join(HERE, "tools", "pos_asan.cpp"),
         "AddressSanitizer: heap-buffer-overflow"),
    ]
    results = []
    for name, flags, src, signature in cases:
        exe = os.path.join(args.out_dir, name)
        pr = subprocess.run(["g++"] + flags + [src, "-o", exe], capture_output=True, text=True)
        if pr.returncode != 0:
            results.append({"control": name, "pass": False, "detail": "build failed"})
            continue
        run = subprocess.run([exe], capture_output=True, text=True, timeout=CASE_TIMEOUT_S)
        hit = signature in run.stderr
        results.append({"control": name, "signature": signature, "exit": run.returncode,
                        "signature_seen": hit, "pass": bool(hit and run.returncode != 0 or
                                                           (name == "pos_ubsan" and hit))})
        open(os.path.join(args.out_dir, name + ".stderr"), "w").write(run.stderr)
    with open(os.path.join(args.out_dir, "POSITIVES.json"), "w") as fh:
        json.dump(results, fh, indent=1, sort_keys=True)
    ok = all(r["pass"] for r in results)
    print("positives: %s" % ("PASS" if ok else "FAIL"))
    for r in results:
        print("  %-16s pass=%s exit=%s signature_seen=%s" % (
            r["control"], r["pass"], r.get("exit"), r.get("signature_seen")))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="D002 native RNP contract runner")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--src-root", required=True)
    b.add_argument("--variant", required=True)
    b.add_argument("--out-dir", required=True)
    r = sub.add_parser("run")
    r.add_argument("--variant", required=True)
    r.add_argument("--bin", required=True)
    r.add_argument("--run-dir", required=True)
    r.add_argument("--cases", default="all")
    pz = sub.add_parser("positives")
    pz.add_argument("--out-dir", required=True)
    j = sub.add_parser("judge")
    j.add_argument("--variant", required=True)
    j.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    if args.cmd == "build":
        return cmd_build(args)
    if args.cmd == "run":
        return cmd_run(args)
    if args.cmd == "positives":
        return cmd_positives(args)
    return cmd_judge(args)


if __name__ == "__main__":
    raise SystemExit(main())
