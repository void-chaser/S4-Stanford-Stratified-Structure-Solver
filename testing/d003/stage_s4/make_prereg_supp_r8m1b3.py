#!/usr/bin/env python3
# make_prereg_supp_r8m1b3.py -- P05-S4 R8 M1b3 section 5: supplementary preregistration. New file.
# Writes $EV/PREREG_SUPP_R8_M1b3.tsv and $EV/PREREG_SUPP_RECORD_R8_M1b3.txt. Runs no driver, reads no observation file of M1b1.
# Source of every expected value: the R7 RESULTS F2 rows (pass1; pass2 must agree).
# Source of env: expected_env_independent_r7.expected_env_from_history (imported, not copied).
# Source of inj_call: REGISTRY_S4_PRE_R7_M2_ADD_v3.tsv inj_call column.
# Source of real: run_m2_r7.real_of (imported, not copied).
import csv, hashlib, importlib.util, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1b3")
REG = os.path.join(REPO, "checkpoints", "p05", "registries")
R7 = os.path.join(REG, "s4r7")
R8A = os.path.join(REG, "s4r8", "M1a")
R8B2 = os.path.join(REG, "s4r8", "M1b", "r8m1b2")
S4R7_DIR = os.path.join(REPO, "testing", "d003", "stage_s4r7")

AUDIT = os.path.join(R8B2, "ENV_AUDIT_M1B_R8_M1b2.tsv")
PREREG_M1B = os.path.join(R8A, "REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv")
ADD_V3 = os.path.join(R7, "REGISTRY_S4_PRE_R7_M2_ADD_v3.tsv")
RES = {
    "G1": (os.path.join(R7, "RESULTS_R7_G1_pass1_run7.tsv"), os.path.join(R7, "RESULTS_R7_G1_pass2_run7.tsv")),
    "G2c": (os.path.join(R7, "RESULTS_R7_G2c_pass1_run7.tsv"), os.path.join(R7, "RESULTS_R7_G2c_pass2_run7.tsv")),
}

EXPECTED_ROWS = {("G1", "F2"): 141, ("G1", "F3"): 141, ("G2c", "F2"): 30, ("G2c", "F3"): 30}
# preregistered distribution (task section 5), checked after the table is built.
# The task writes "INVALID 22"; the R7 field value of those 22 rows is "INVALID_NOT_REACHED" (verdict column "INVALID").
# The count is 22 as preregistered; only the field-value spelling is corrected here (disclosed in the record).
EXPECTED_DIST = {
    ("G1", "F2"): {"REPORTED_FAILURE": 119, "INVALID_NOT_REACHED": 22},
    ("G1", "F3"): {"REPORTED_FAILURE": 119, "INVALID_NOT_REACHED": 22},
    ("G2c", "F2"): {"REPORTED_FAILURE": 30},
    ("G2c", "F3"): {"REPORTED_FAILURE": 30},
}
EXPECTED_INJ2 = {("G1", "F2"): 35, ("G1", "F3"): 35}  # inj_call=2: 25 REPORTED_FAILURE + 10 INVALID_NOT_REACHED
STOP = []


def stop(msg):
    print("STOP: " + msg)
    sys.exit(1)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_tsv(path):
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]
    header = lines[0].split("\t")
    return [dict(zip(header, l.split("\t"))) for l in lines[1:]]


def base_id(pid):
    """Strip the tree suffix: M1b uses -F2/-F3, R7 uses -F/-F2. The base id is shared."""
    for suf in ("-F3", "-F2", "-F"):
        if pid.endswith(suf):
            return pid[: -len(suf)]
    return pid


def main():
    sys.path.insert(0, S4R7_DIR)
    env_mod = load_module("expected_env_independent_r7", os.path.join(S4R7_DIR, "expected_env_independent_r7.py"))
    m2_mod = load_module("run_m2_r7", os.path.join(S4R7_DIR, "run_m2_r7.py"))

    # ---- 1. audit rows: audit_verdict != ENV_AGREE -> must be exactly 342 ----
    audit = read_tsv(AUDIT)
    sel = [r for r in audit if r["audit_verdict"] != "ENV_AGREE"]
    dist = {}
    for r in sel:
        k = (r["group"], r["tree"])
        dist[k] = dist.get(k, 0) + 1
    if len(sel) != 342 or dist != EXPECTED_ROWS:
        stop("audit selection %d rows, distribution %s (expected 342 %s)" % (len(sel), dist, EXPECTED_ROWS))
    # group names in ENV_AUDIT: G1 / G2c ; only these two groups allowed
    if set(r["group"] for r in sel) != {"G1", "G2c"}:
        stop("unexpected groups in selection")

    # ---- 2. M1a6 preregistration rows (driver name, driver sha, comparison contract, k_source) ----
    prereg = read_tsv(PREREG_M1B)
    prereg_by = {}
    for r in prereg:
        prereg_by[(r["group"], r["point_id"], r["tree"])] = r

    # ---- 3. R7 RESULTS F2 rows, pass1 and pass2 (must agree) ----
    res_f2 = {}
    for grp, (p1, p2) in RES.items():
        t1 = [r for r in read_tsv(p1) if r["tree"] == "F2"]
        t2 = [r for r in read_tsv(p2) if r["tree"] == "F2"]
        m1 = {base_id(r["point_id"]): r for r in t1}
        m2 = {base_id(r["point_id"]): r for r in t2}
        if set(m1) != set(m2) or len(m1) != len(t1) or len(m2) != len(t2):
            stop("R7 %s F2 pass1/pass2 id sets differ" % grp)
        for b in m1:
            a, c = m1[b], m2[b]
            for fld in ("expected_class", "class", "verdict", "rc", "rc1", "rc2", "hit", "inj_call", "request", "mode"):
                if a[fld] != c[fld]:
                    stop("R7 %s pass1/pass2 differ on %s for %s" % (grp, fld, b))
        res_f2[grp] = m1
    # pass2 identity check across the two runs
    for grp, (p1, p2) in RES.items():
        pass_rows1 = read_tsv(p1)
        pass_rows2 = read_tsv(p2)
        if len(pass_rows1) != len(pass_rows2):
            stop("R7 %s pass row count differs" % grp)

    # ---- 4. ADD_v3 inj_call (table keyed by point id with tree suffix -F / -F2) ----
    add = read_tsv(ADD_V3)
    add_by = {}
    for r in add:
        if r["tree"] != "F2":
            continue
        add_by[base_id(r["point_id"])] = r

    # ---- 5. ENV_AUDIT hist_call_env keyed by (point, tree) ----
    audit_by = {(r["point_id"], r["tree"]): r for r in sel}

    rows = []
    for r in sel:
        grp, pid, tree = r["group"], r["point_id"], r["tree"]
        b = base_id(pid)
        # driver from M1a6 prereg of this row (G1: d003-<tree>-plain, G2c: d003plan-<tree>-plain)
        pr = prereg_by.get((grp, pid, tree))
        if pr is None:
            stop("prereg row missing for %s %s %s" % (grp, pid, tree))
        dname, dsha = pr["driver_name"], pr["driver_sha256"]
        exp_dn = ("d003-F2-plain" if grp == "G1" else "d003plan-F2-plain")
        # the driver of a F3 point is the F3 driver of the same group
        exp_dn = exp_dn.replace("F2", tree)
        if dname != exp_dn:
            stop("driver name %s != %s for %s %s" % (dname, exp_dn, grp, pid))
        # env from history
        env_hist = env_mod.expected_env_from_history(grp, b, "F2")
        # compare with ENV_AUDIT hist_call_env (key-by-key)
        audit_env = {}
        for part in r["hist_call_env"].split(";"):
            if "=" in part:
                k, v = part.split("=", 1)
                audit_env[k] = v
        if env_hist != audit_env:
            stop("env mismatch vs ENV_AUDIT hist_call_env for %s %s: %s vs %s" % (grp, pid, env_hist, audit_env))
        env_str = ";".join("%s=%s" % (k, env_hist[k]) for k in sorted(env_hist))
        # inj_call and real
        a = add_by.get(b)
        if a is None:
            stop("ADD_v3 row missing for %s" % b)
        inj_call = a["inj_call"]
        real = m2_mod.real_of(grp, b)
        # expected values from R7 F2 row
        rr = res_f2[grp].get(b)
        if rr is None:
            stop("R7 %s F2 row missing for %s" % (grp, b))
        rows.append({
            "row_id": "", "group": grp, "point_id": pid, "tree": tree, "base_id": b,
            "driver_name": dname, "driver_sha256": dsha, "env": env_str,
            "inj_call": inj_call, "real": "True" if real else "False",
            "expected_class": rr["expected_class"],
            "expected_rc1": rr["rc1"], "expected_rc2": rr["rc2"], "expected_run_rc": rr["rc"],
            "expected_hit": rr["hit"],
            "comparison_contract": pr["comparison_contract"],
            "status": "INFLUENCED",
            "expect_source": "%s:%s" % (os.path.relpath(RES[grp][0], REPO), "row_of_%s" % b),
            "add_v3_source": "REGISTRY_S4_PRE_R7_M2_ADD_v3.tsv:%s" % a.get("inj_call_source", ""),
            "audit_verdict": r["audit_verdict"],
        })

    # ---- physical line numbers of the R7 source rows (expect_source) ----
    line_of = {}
    for grp, (p1, _) in RES.items():
        with open(p1, encoding="utf-8") as fh:
            for ln, raw in enumerate(fh, 1):
                if raw.startswith("#") or not raw.strip():
                    continue
                f = raw.rstrip("\n").split("\t")
                if f[0] == "point_id":
                    continue
                if f[2] == "F2":
                    line_of[(grp, base_id(f[0]))] = ln
    for r in rows:
        ln = line_of.get((r["group"], r["base_id"]))
        if ln is None:
            stop("line number missing for %s %s" % (r["group"], r["base_id"]))
        rel = os.path.relpath(RES[r["group"]][0], REPO)
        r["expect_source"] = "%s:%d" % (rel, ln)

    # ---- distribution check ----
    got = {}
    for r in rows:
        k = (r["group"], r["tree"])
        got.setdefault(k, {})
        got[k][r["expected_class"]] = got[k].get(r["expected_class"], 0) + 1
    dist_ok = True
    for k, want in EXPECTED_DIST.items():
        if got.get(k, {}) != want:
            dist_ok = False
    ic2_now = {}
    for r in rows:
        if r["inj_call"] == "2":
            k = (r["group"], r["tree"])
            ic2_now[k] = ic2_now.get(k, 0) + 1
    if ic2_now != EXPECTED_INJ2:
        dist_ok = False
    print("DIST_OK=%s" % dist_ok)
    if not dist_ok:
        print("DIST_ACTUAL=%s" % got)
        print("INJ2_ACTUAL=%s" % ic2_now)
        stop("preregistered distribution differs; report differences and stop (task section 5)")

    # ---- write table ----
    rows.sort(key=lambda x: (x["group"], x["tree"], x["point_id"]))
    for i, r in enumerate(rows, 1):
        r["row_id"] = str(i)
    cols = ["row_id", "group", "point_id", "tree", "base_id", "driver_name", "driver_sha256", "env", "inj_call", "real",
            "expected_class", "expected_rc1", "expected_rc2", "expected_run_rc", "expected_hit",
            "comparison_contract", "status", "expect_source", "add_v3_source", "audit_verdict"]
    out = os.path.join(EV, "PREREG_SUPP_R8_M1b3.tsv")
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write("# PREREG_SUPP_R8_M1b3.tsv -- P05-S4 R8 M1b3 supplementary preregistration (U205). Frozen before any run.\n")
        fh.write("# Rows: ENV_AUDIT_M1B_R8_M1b2.tsv audit_verdict != ENV_AGREE (342). Sources: R7 only (U203). status INFLUENCED.\n")
        w = csv.writer(fh, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE, escapechar=None)
        w.writerow(cols)
        for r in rows:
            w.writerow([r[c] for c in cols])
    os.replace(tmp, out)

    # ---- record ----
    sha = sha256_file(out)
    grp_counts = {}
    for r in rows:
        k = "%s_%s" % (r["group"], r["tree"])
        grp_counts[k] = grp_counts.get(k, 0) + 1
    cls_counts = {}
    for r in rows:
        k = "%s_%s_%s" % (r["group"], r["tree"], r["expected_class"])
        cls_counts[k] = cls_counts.get(k, 0) + 1
    ic2 = {}
    for r in rows:
        if r["inj_call"] == "2":
            k = "%s_%s" % (r["group"], r["tree"])
            ic2[k] = ic2.get(k, 0) + 1
    rec = os.path.join(EV, "PREREG_SUPP_RECORD_R8_M1b3.txt")
    tmp = rec + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write("# PREREG_SUPP_RECORD_R8_M1b3 -- P05-S4 R8 M1b3 (written by make_prereg_supp_r8m1b3.py)\n")
        fh.write("file\tPREREG_SUPP_R8_M1b3.tsv\n")
        fh.write("sha256\t%s\n" % sha)
        fh.write("rows\t%d\n" % len(rows))
        fh.write("group_counts\t%s\n" % grp_counts)
        fh.write("expected_class_counts\t%s\n" % cls_counts)
        fh.write("inj_call_2_counts\t%s\n" % ic2)
        fh.write("status_values\t%s\n" % sorted(set(r["status"] for r in rows)))
    os.replace(tmp, rec)
    print("ROWS=%d" % len(rows))
    print("SHA256=%s" % sha)
    print("GROUP_COUNTS=%s" % grp_counts)
    print("CLASS_COUNTS=%s" % cls_counts)
    print("INJ_CALL_2=%s" % ic2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
