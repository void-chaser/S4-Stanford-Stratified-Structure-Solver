#!/usr/bin/env python3
"""Offline independent check of the frozen D002 raw outputs.

Reads only the RUN evidence, the spec / matrix / raw out.txt / attempt records they
name, and the frozen thresholds (copied from d002_shim/tools/case_table.py TH).
It never imports S4, never runs a driver, and never writes into RUN.
Usage: python3 -I d002_independent_check.py <RUN> <out.json>
"""
import hashlib
import json
import os
import sys

import numpy as np
from scipy.optimize import linear_sum_assignment

RUN, OUT = sys.argv[1], sys.argv[2]
EV = os.path.join(RUN, "evidence")
SH = os.path.join(RUN, "d002_shim")

# Frozen in d002_shim/tools/case_table.py (TH). Copied, not imported.
TOL_EIG = 1e-10
TOL_RES = 1e-10
TOL_NORM = 1e-12
PAD_INIT_API = (0.0, 0.0)     # padding untouched for API vr/vl (judge TH padding_init_value)
PAD_INIT_HELPER = (-777.0, 0.0)  # helper marker padding (judge check)
MARKER_BASE = 1000            # helper marker = 1000 + original row index
BUILD_OF = {"ord_candidate": "d002_ord_candidate", "asan_candidate": "d002_asan_candidate",
            "seam_candidate": "d002_seam_candidate"}


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def jload(p):
    with open(p) as f:
        return json.load(f)


def parse_spec(path):
    s = {}
    for line in open(path):
        p = line.split()
        if len(p) >= 2:
            s[p[0]] = p[1]
    return s


def parse_out(path):
    """Independent parser of out.txt (format read from the raw files, not from judge.py)."""
    d = {"w": {}, "vl": {}, "vr": {}, "v": {}, "scalars": {}, "scale": None, "work0": None}
    multi = {"w": "w", "vl_flat": "vl", "vr_flat": "vr", "v_flat": "v"}
    for line in open(path):
        p = line.split()
        if not p:
            continue
        k = p[0]
        if k in multi:
            d[multi[k]][int(p[1])] = (float(p[2]), float(p[3]))
        elif k == "work0":
            d["work0"] = complex(float(p[2]), float(p[3]))
        elif k == "scale":
            d["scale"] = [float(x) for x in p[1:]]
        else:
            d["scalars"][k] = p[1] if len(p) == 2 else " ".join(p[1:])
    return d


def load_matrix_text(path):
    rows = [l.split() for l in open(path) if l.strip()]
    mid, n = rows[0][1], int(rows[1][0])
    vals = rows[2:]
    assert len(vals) == n * n, (path, len(vals), n)
    A = np.zeros((n, n), dtype=complex)
    for idx, (re, im) in enumerate(vals):
        A[idx % n, idx // n] = complex(float(re), float(im))   # column-major
    return mid, n, A


MJ = jload(os.path.join(SH, "cases", "matrices.json"))


def json_matrix(mid):
    m = MJ["matrices"][mid]
    n = m["n"]
    A = np.zeros((n, n), dtype=complex)
    for idx, (re, im) in enumerate(m["values"]):
        A[idx % n, idx // n] = complex(float(re), float(im))
    ref = np.array([complex(float(a), float(b)) for a, b in MJ["eigenvalue_reference"][mid]["values"]],
                   dtype=complex)
    return A, ref


def lapack_zgebak_rows(n, ilo, ihi, scale):
    """Reference LAPACK zgebak, job='P' (permutation only), 1-based indices.
    Returns rows[p] = original row now at position p (0-based)."""
    rows = list(range(n))
    for ii in range(1, n + 1):
        i = ii
        if ilo <= i <= ihi:
            continue
        if i < ilo:
            i = ilo - ii
        k = int(scale[i - 1])
        if k == i:
            continue
        rows[i - 1], rows[k - 1] = rows[k - 1], rows[i - 1]
    return rows


def rel_resid(M, lam_s, cols, left):
    nAf = float(np.linalg.norm(M, "fro"))
    out = []
    for j, col in enumerate(cols):
        nv = float(np.linalg.norm(col))
        if nv == 0.0:
            out.append(float("inf"))
            continue
        if left:
            r = M.conj().T @ col - np.conj(lam_s[j]) * col
        else:
            r = M @ col - lam_s[j] * col
        out.append(float(np.linalg.norm(r)) / (nAf * nv))
    return out


def vec_cols(dct, n, ld, j_count):
    return [np.array([complex(*dct[i + j * ld]) for i in range(n)]) for j in range(j_count)]


def sanitizer_markers(stderr_path):
    txt = open(stderr_path, errors="replace").read() if os.path.exists(stderr_path) else ""
    return {"AddressSanitizer": "AddressSanitizer" in txt,
            "runtime_error": "runtime error:" in txt,
            "N1_nonzero_offset_null": ("applying non-zero offset" in txt and "null pointer" in txt),
            "bytes": len(txt)}


def check_api(rec, spec, out, n, A_txt, ref, s_max):
    res = {}
    want = spec.get("want", "none")
    wm = spec.get("work_mode", "internal")
    info = int(out["scalars"]["info"])
    res["info"] = info
    res["want"], res["work_mode"] = want, wm
    lam = np.array([out["w"][j][0] + 1j * out["w"][j][1] for j in range(n)], dtype=complex) \
        if len(out["w"]) == n else None
    if lam is None:
        res["w_count_ok"] = False
        return res
    res["w_count_ok"] = True
    if wm == "query":
        w0 = out["work0"]
        res["query_work0"] = [w0.real, w0.imag] if w0 is not None else None
        res["query_ok"] = bool(w0 is not None and abs(w0.real - 2 * n) < 1e-12 and abs(w0.imag) < 1e-12)
        return res
    # eigenvalue error: optimal pairing of computed to analytic reference, scaled by max|A|
    s = s_max if s_max > 0 else 1.0
    cost = np.abs(lam[:, None] - ref[None, :]) / s
    r_idx, c_idx = linear_sum_assignment(cost)
    eig_err = float(np.max(cost[r_idx, c_idx])) if n else 0.0
    res["eig_rel_err_hungarian"] = eig_err
    res["eig_ok"] = eig_err <= TOL_EIG
    As = A_txt / s
    lam_s = lam / s
    if want in ("vr", "both"):
        ld = int(out["scalars"]["ldvr"])
        cols = vec_cols(out["vr"], n, ld, n)
        rr = rel_resid(As, lam_s, cols, left=False)
        res["right_res_max"] = max(rr)
        res["right_norm_dev"] = max(abs(float(np.linalg.norm(c)) - 1.0) for c in cols)
        res["right_res_ok"] = max(rr) <= TOL_RES and res["right_norm_dev"] <= TOL_NORM
        pad_bad = [idx for idx, (re, im) in out["vr"].items() if (idx % ld) >= n and (re, im) != PAD_INIT_API]
        res["right_padding_touched"] = len(pad_bad)
    if want in ("vl", "both"):
        ld = int(out["scalars"]["ldvl"])
        cols = vec_cols(out["vl"], n, ld, n)
        lr = rel_resid(As, lam_s, cols, left=True)
        res["left_res_max"] = max(lr)
        res["left_norm_dev"] = max(abs(float(np.linalg.norm(c)) - 1.0) for c in cols)
        res["left_res_ok"] = max(lr) <= TOL_RES and res["left_norm_dev"] <= TOL_NORM
        pad_bad = [idx for idx, (re, im) in out["vl"].items() if (idx % ld) >= n and (re, im) != PAD_INIT_API]
        res["left_padding_touched"] = len(pad_bad)
    return res


def check_helper(spec, out, n):
    ilo = int(out["scalars"]["ilo_1based"])
    ihi = int(out["scalars"]["ihi_1based"])
    ldv = int(out["scalars"]["ldv"])
    m = int(out["scalars"]["m"])
    job, side = out["scalars"].get("job"), out["scalars"].get("side")
    rows = lapack_zgebak_rows(n, ilo, ihi, out["scale"])
    expect = {(i, j): MARKER_BASE + rows[i] for i in range(n) for j in range(m)}
    mism = []
    for (i, j), e in expect.items():
        got = out["v"].get(i + j * ldv)
        if got is None or got != (float(e), 0.0):
            mism.append((i, j, got))
    pad_bad = [idx for idx, val in out["v"].items()
               if ((idx % ldv) >= n or (idx // ldv) >= m) and val != PAD_INIT_HELPER]
    return {"job": job, "side": side, "ilo": ilo, "ihi": ihi, "scale": out["scale"],
            "lapack_rows": rows, "observed_rows_col0": [int(round(out["v"][i][0])) - MARKER_BASE
                                                       for i in range(n)],
            "perm_mismatches": len(mism), "perm_ok": len(mism) == 0,
            "padding_untouched": len(pad_bad) == 0, "padding_bad": len(pad_bad)}


def check_seam(spec, out):
    mode = int(spec.get("seam_mode", 0))
    forced = int(spec.get("seam_info", 0))
    expect = forced if mode else 0
    info = int(out["scalars"]["info"])
    ret = int(out["scalars"].get("seam_onlyvalues_returned_info", "0"))
    res = {"info": info, "expected_info": expect, "info_ok": info == expect,
           "seam_mode": mode, "seam_forced": forced,
           "seam_onlyvalues_real_info": int(out["scalars"].get("seam_onlyvalues_real_info", "-99999")),
           "seam_onlyvalues_returned_info": ret}
    if spec.get("case_id") == "C-03":
        res["C03_real_status_passthrough_ok"] = (info == 0 and res["seam_onlyvalues_real_info"] == 0)
    return res


def main():
    out_all = {"schema": "p04.d002.independent_offline_check.v1", "run": RUN,
               "thresholds": {"eig_rel_tol": TOL_EIG, "residual_tol": TOL_RES, "vector_norm_tol": TOL_NORM},
               "records": {}, "observations": {}, "problems": []}
    judge = {(r["case_id"], r["identity"], r["variant"]): r
             for r in jload(os.path.join(SH, "results", "JUDGEMENT.json"))["runs"]}
    final_rows = {r["case_key"]: r for r in jload(os.path.join(EV, "FINAL_JUDGEMENT.json"))["rows"]}

    case_files = sorted(os.path.join(EV, f) for f in os.listdir(EV) if f.startswith("case_"))
    obs_files = sorted(os.path.join(EV, f) for f in os.listdir(EV) if f.startswith("judgement_run_A-10r"))
    assert len(case_files) == 48 and len(obs_files) == 2, (len(case_files), len(obs_files))

    for p in case_files:
        rec = jload(p)
        key = "%s/%s/%s" % (rec["case_id"], rec["identity"], rec["variant"])
        att = rec["attempt"]
        argv = att["argv"]
        binary, spec_path, out_path = argv[0], argv[1], argv[-1]
        spec = parse_spec(spec_path)
        spec["case_id"] = rec["case_id"]
        out = parse_out(out_path)
        pins = rec["pin"]
        r = {"key": key, "mode": rec["mode"], "status": rec["status"], "problems": []}

        # identity / consumption chain
        build = BUILD_OF[rec["identity"]]
        bld = {b["name"]: b for b in jload(os.path.join(SH, "logs", "build", "BUILDS.json"))}[build]
        bin_sha = sha(binary)
        r["binary_sha256"] = bin_sha
        meta_p = os.path.join(SH, "results", rec["identity"], rec["variant"], rec["case_id"],
                              "attempt-1", "meta.json")
        meta = jload(meta_p)
        r["identity_ok"] = bin_sha == bld["binary_sha256"] == meta["binary_sha256"]
        # The judge consumes meta.json, whose argv[1] is the spec COPY inside the attempt dir
        # (the runner argv names the cases/ spec); both must carry the pinned spec bytes.
        r["judge_meta_consumed"] = bool(
            meta["argv"][0] == argv[0] and meta["argv"][-1] == out_path
            and meta["exit"] == att["exit"] and meta["binary_sha256"] == bld["binary_sha256"]
            and sha(meta["argv"][1]) == pins["spec_sha256"])
        r["spec_sha_ok"] = sha(spec_path) == pins["spec_sha256"]
        mpath = os.path.join(RUN, spec["matrix_file"].lstrip("./"))
        r["matrix_sha_ok"] = sha(mpath) == pins["matrix_sha256"]
        r["out_sha_ok"] = sha(out_path) == rec["output_sha256"]
        r["attempt_record_sha_ok"] = sha(att["record"]) == att["sha256"]
        r["exit"] = att["exit"]
        r["stderr"] = sanitizer_markers(os.path.join(SH, "results", rec["identity"], rec["variant"],
                                                     rec["case_id"], "attempt-1", "stderr.txt"))

        mid, n, A_txt = load_matrix_text(mpath)
        A_json, ref = json_matrix(mid)
        r["matrix_text_vs_json_maxdiff"] = float(np.max(np.abs(A_txt - A_json))) if n else 0.0
        s_max = float(np.max(np.abs(A_txt))) if A_txt.size else 1.0
        r["matrix_id"], r["n"] = mid, n
        r["scalea"] = out["scalars"].get("scalea")
        r["n_out_ok"] = int(out["scalars"]["n"]) == n

        if rec["mode"] == "helper":
            hres = check_helper(spec, out, n)
            r.update(hres)
            r["pass"] = bool(hres["perm_ok"] and hres["padding_untouched"] and r["n_out_ok"]
                             and int(out["scalars"]["info"] if "info" in out["scalars"] else 0) == 0)
        elif rec["mode"] == "seam":
            sres = check_seam(spec, out)
            r.update(sres)
            r["pass"] = bool(sres["info_ok"] and sres.get("C03_real_status_passthrough_ok", True))
        else:
            ares = check_api(rec, spec, out, n, A_txt, ref, s_max)
            r.update(ares)
            crit = [ares.get("info") == 0, ares.get("w_count_ok", False)]
            if spec.get("work_mode") == "query":
                crit.append(ares.get("query_ok", False))
            else:
                crit.append(ares.get("eig_ok", False))
                if "right_res_ok" in ares:
                    crit.append(ares["right_res_ok"] and ares.get("right_padding_touched", 0) == 0)
                if "left_res_ok" in ares:
                    crit.append(ares["left_res_ok"] and ares.get("left_padding_touched", 0) == 0)
            r["pass"] = bool(all(crit))
            # cross-check with the frozen judge record conditions (same raw file)
            cond = rec.get("conditions", {})
            diffs = {}
            for name, mine in (("eig_rel_err", ares.get("eig_rel_err_hungarian")),
                               ("right_res_max", ares.get("right_res_max")),
                               ("left_res_max", ares.get("left_res_max")),
                               ("right_norm_dev", ares.get("right_norm_dev")),
                               ("left_norm_dev", ares.get("left_norm_dev"))):
                if name in cond and mine is not None:
                    diffs[name] = {"record": cond[name]["value"], "independent": mine,
                                   "record_ok": cond[name]["ok"]}
            r["record_vs_independent"] = diffs
        r["judge_state"] = judge[(rec["case_id"], rec["identity"], rec["variant"])]["state"]
        r["final_classification"] = final_rows[key]["classification"]
        if not r["pass"]:
            out_all["problems"].append(key)
        r["identity_ok"] = bool(r["identity_ok"] and r["judge_meta_consumed"] and r["spec_sha_ok"]
                                and r["matrix_sha_ok"] and r["out_sha_ok"] and r["attempt_record_sha_ok"])
        if not r["identity_ok"]:
            out_all["problems"].append(key + ":consumption")
        out_all["records"][key] = r

    for p in obs_files:
        rec = jload(p)
        key = "%s/%s/%s" % (rec["case_id"], rec["identity"], rec["variant"])
        out_path = rec["argv"][-1]
        raw_nonempty = os.path.exists(out_path) and os.path.getsize(out_path) > 0
        out_all["observations"][key] = {
            "exit": rec["exit"], "signal_exit": rec["exit"] < 0, "raw_nonempty": raw_nonempty,
            "raw_sha256": sha(out_path) if os.path.exists(out_path) else None,
            "record_output_sha256": rec.get("output_sha256"),
            "stderr": sanitizer_markers(os.path.join(SH, "results", rec["identity"], rec["variant"],
                                                     rec["case_id"], "attempt-1", "stderr.txt")),
            "judge_state": judge[(rec["case_id"], rec["identity"], rec["variant"])]["state"],
            "final_classification": final_rows[key]["classification"]}
    out_all["summary"] = {
        "non_probe_records": len(out_all["records"]),
        "pass": sum(1 for v in out_all["records"].values() if v["pass"]),
        "fail": sum(1 for v in out_all["records"].values() if not v["pass"]),
        "consumption_ok": sum(1 for v in out_all["records"].values() if v["identity_ok"]),
        "observations": len(out_all["observations"]),
        "by_mode": {m: sum(1 for v in out_all["records"].values() if v["mode"] == m)
                    for m in ("numeric", "helper", "seam")},
        "judge_state_counts": {s: sum(1 for v in out_all["records"].values() if v["judge_state"] == s)
                               for s in set(v["judge_state"] for v in out_all["records"].values())},
    }
    with open(OUT, "w") as f:
        json.dump(out_all, f, indent=1, sort_keys=True, default=lambda x: str(x))
    print(json.dumps(out_all["summary"], indent=1, sort_keys=True))
    print("problems:", out_all["problems"])


if __name__ == "__main__":
    main()
