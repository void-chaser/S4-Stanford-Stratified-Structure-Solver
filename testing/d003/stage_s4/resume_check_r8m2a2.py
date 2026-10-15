#!/usr/bin/env python3
# resume_check_r8m2a2.py -- P05-S4 R8 M2a2: Resume check (Part A).
# Does NOT replace start baseline. Records status, hashes, prefix checks, backfill equivalence, and existing products.
# Output: checkpoints/p05/evidence/p05-s4r8/m2a2/RESUME_CHECK_R8_M2a2.tsv
import hashlib, os, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
OUT = os.path.join(EV, "RESUME_CHECK_R8_M2a2.tsv")

EXPECTED_BASE = "6a4f0031afeda0a3105c9983d5a65a2d847f1488"
EXPECTED_S4_TREE = "6cff923a02baf19e01966b2339755cbf3a5deeef"
EXPECTED_JUDGE_SHA = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"

START_RUL_BYTES = 92855
START_RUL_SHA = "c1632c0f518ff20d3139891230b379772ad6757ef16e60cc7564abf71c19813c"
START_ERR_BYTES = 67104
START_ERR_SHA = "e559b0110a26f3f039b27a39c1a08924eee4b43e394ddf799cee347706cf7520"

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    if os.path.exists(OUT):
        print("resume_check_r8m2a2: REFUSED exists (U17): %s" % OUT)
        return 2

    records = []
    fails = 0
    def check(name, ok, exp, act):
        nonlocal fails
        st = "PASS" if ok else "FAIL"
        if not ok:
            fails += 1
        records.append("%s\t%s\texpected=%s\tactual=%s" % (st, name, exp, act))

    # 1. Base hashes
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    check("HEAD_IS_BASE", head == EXPECTED_BASE, EXPECTED_BASE, head)
    head_s4 = subprocess.check_output(["git", "rev-parse", "HEAD:S4"], cwd=REPO, text=True).strip()
    check("HEAD_S4_TREE", head_s4 == EXPECTED_S4_TREE, EXPECTED_S4_TREE, head_s4)
    judge_p = os.path.join(REPO, "testing", "d003", "judge_d003.py")
    j_sha = sha256_file(judge_p)
    check("JUDGE_SHA256", j_sha == EXPECTED_JUDGE_SHA, EXPECTED_JUDGE_SHA, j_sha)

    # 2. Prefixes of RULINGS and ERRATA_8
    rul_p = os.path.join(REPO, "checkpoints", "p05", "registries", "RULINGS.tsv")
    with open(rul_p, "rb") as fh:
        rul_b = fh.read()
    rul_pfx_sha = hashlib.sha256(rul_b[:START_RUL_BYTES]).hexdigest()
    check("RULINGS_START_PREFIX_MATCH", (len(rul_b) >= START_RUL_BYTES and rul_pfx_sha == START_RUL_SHA), START_RUL_SHA, "%d bytes, %s" % (len(rul_b), rul_pfx_sha))

    err_p = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "ERRATA_8.txt")
    with open(err_p, "rb") as fh:
        err_b = fh.read()
    err_pfx_sha = hashlib.sha256(err_b[:START_ERR_BYTES]).hexdigest()
    check("ERRATA_8_START_PREFIX_MATCH", (len(err_b) >= START_ERR_BYTES and err_pfx_sha == START_ERR_SHA), START_ERR_SHA, "%d bytes, %s" % (len(err_b), err_pfx_sha))

    # 3. Backfilled r8m2a files
    reg_m2a = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a")
    ev_m2a = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a")
    bf_files = ["GATE_R8_M2a_end.txt", "GATE_R8_M2a_end_R2.txt", "GATE_R8_M2a_end_R3.txt", "POSTCOMMIT_R8_M2a.txt"]
    for f in bf_files:
        src = os.path.join(ev_m2a, f)
        dst = os.path.join(reg_m2a, f)
        if os.path.isfile(src) and os.path.isfile(dst):
            s_sha = sha256_file(src)
            d_sha = sha256_file(dst)
            check("BACKFILL_MATCH_" + f, s_sha == d_sha, s_sha, d_sha)
        else:
            check("BACKFILL_PRESENT_" + f, False, "both present", "src=%s dst=%s" % (os.path.isfile(src), os.path.isfile(dst)))
    man_p = os.path.join(reg_m2a, "SHA256SUMS_END.txt")
    check("BACKFILL_MANIFEST_PRESENT", os.path.isfile(man_p), "present", "present" if os.path.isfile(man_p) else "absent")

    # 4. Existing products in m2a2 evidence
    start_gate = os.path.join(EV, "GATE_R8_M2a2_start.txt")
    start_ok = False
    if os.path.isfile(start_gate):
        with open(start_gate, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
            if lines and lines[-1] == "FAILS=0":
                start_ok = True
    check("START_GATE_FAILS_0", start_ok, "FAILS=0", "ok" if start_ok else "not ok")

    stray_base = os.path.join(EV, "STRAY_BASELINE_R8_M2a2.tsv")
    check("STRAY_BASELINE_PRESENT", os.path.isfile(stray_base), "present", "present" if os.path.isfile(stray_base) else "absent")

    san_probe = os.path.join(EV, "SAN_PROBE_R8_M2a2.txt")
    san_ok = False
    if os.path.isfile(san_probe):
        with open(san_probe, "r", encoding="utf-8") as fh:
            content = fh.read()
            if "SAN_TOOLCHAIN=USABLE" in content:
                san_ok = True
    check("SAN_PROBE_USABLE", san_ok, "SAN_TOOLCHAIN=USABLE", "usable" if san_ok else "not usable")

    k1_anchor = os.path.join(EV, "K1_ANCHOR_R8_M2a2.tsv")
    check("K1_ANCHOR_PRESENT", os.path.isfile(k1_anchor), "present", "present" if os.path.isfile(k1_anchor) else "absent")

    nm_check = os.path.join(EV, "NM_CHECK_R8_M2a2_R2.tsv")
    check("NM_CHECK_R2_PRESENT", os.path.isfile(nm_check), "present", "present" if os.path.isfile(nm_check) else "absent")

    # 5. Git status check
    st_proc = subprocess.check_output(["git", "status", "--short"], cwd=REPO, text=True).strip()
    check("GIT_STATUS_NON_EMPTY", len(st_proc) > 0, "non-empty", "lines=%d" % len(st_proc.splitlines()))

    os.makedirs(EV, exist_ok=True)
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("# RESUME_CHECK_R8_M2a2 -- P05-S4 R8 M2a2 Resume check (Part A)\n")
        fh.write("# columns: status\tname\texpected\tactual\n")
        for r in records:
            fh.write(r + "\n")
        fh.write("RESUME_CHECK_FAILS=%d\n" % fails)

    print("resume_check_r8m2a2: wrote %s, fails=%d" % (OUT, fails))
    return fails

if __name__ == "__main__":
    sys.exit(main())
