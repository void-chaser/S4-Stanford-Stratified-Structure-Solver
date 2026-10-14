#!/usr/bin/env python3
# gate14_check_r8m1b1.py -- P05-S4 R8 M1b1 gate helper (brief §3). New file.
import hashlib, os, re, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))

EXPECTED_BASE = "43c650dfe98ae3e20753ff63c0cca5a14467c6a2"
EXPECTED_M1B_SHA = "66696e831b18a98c1bad30903a45a39e525b6b1c0f9563b01b0f135f343829e2"
EXPECTED_M1C_SHA = "e1e555ee4ca20421b6e5681e18be6cd1b873fc7cff06d246c01fad65d8d3a562"

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def load_tsv_rows(path):
    rows = []
    header = None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\r\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if header is None:
                header = parts
                continue
            rows.append(dict(zip(header, parts)))
    return header, rows

def run_checks(mode, start_records=None):
    results = [] # (status, check_name, expected, actual)
    fails = 0

    def check(name, cond, exp, act):
        nonlocal fails
        st = "PASS" if cond else "FAIL"
        if not cond:
            fails += 1
        results.append((st, name, str(exp), str(act)))

    # 1. Commit existence
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    check("HEAD_IS_M1A6", head == EXPECTED_BASE, EXPECTED_BASE, head)

    m1a6_log = subprocess.check_output(["git", "log", "-1", "--format=%H", EXPECTED_BASE], cwd=REPO, text=True).strip()
    check("M1A6_COMMIT_EXISTS", m1a6_log == EXPECTED_BASE, EXPECTED_BASE, m1a6_log)

    # 2. Prep pack in checkpoints/p05/registries/s4r8/M1a/
    m1a_dir = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")
    m1a_sums = os.path.join(m1a_dir, "SHA256SUMS_R8_M1a6.txt")
    check("M1A6_SUMS_EXISTS", os.path.isfile(m1a_sums), "exists", "exists" if os.path.isfile(m1a_sums) else "missing")
    if os.path.isfile(m1a_sums):
        m1a_ok = True
        with open(m1a_sums, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                exp_sha, fname = line.split(None, 1)
                fpath = os.path.join(m1a_dir, fname)
                if not os.path.isfile(fpath) or sha256_file(fpath) != exp_sha:
                    m1a_ok = False
                    break
        check("M1A6_ALL_FILES_MATCH_SHA256", m1a_ok, "all 16 OK", "all 16 OK" if m1a_ok else "mismatch")

    # 3. Prereg hashes
    m1b_path = os.path.join(m1a_dir, "REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv")
    m1c_path = os.path.join(m1a_dir, "REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv")
    m1b_act_sha = sha256_file(m1b_path) if os.path.isfile(m1b_path) else "missing"
    m1c_act_sha = sha256_file(m1c_path) if os.path.isfile(m1c_path) else "missing"
    check("M1B_SHA256", m1b_act_sha == EXPECTED_M1B_SHA, EXPECTED_M1B_SHA, m1b_act_sha)
    check("M1C_SHA256", m1c_act_sha == EXPECTED_M1C_SHA, EXPECTED_M1C_SHA, m1c_act_sha)

    # 4. Check PREREG_RECORD_R8_M1a6.txt matches
    prereg_rec_path = os.path.join(m1a_dir, "PREREG_RECORD_R8_M1a6.txt")
    prereg_rec_text = open(prereg_rec_path, encoding="utf-8").read() if os.path.isfile(prereg_rec_path) else ""
    check("PREREG_RECORD_M1B_MATCH", EXPECTED_M1B_SHA in prereg_rec_text, "contains m1b sha", "matched" if EXPECTED_M1B_SHA in prereg_rec_text else "not found")
    check("PREREG_RECORD_M1C_MATCH", EXPECTED_M1C_SHA in prereg_rec_text, "contains m1c sha", "matched" if EXPECTED_M1C_SHA in prereg_rec_text else "not found")

    # 5. Row counts: M1b 830 (F2 415, F3 415)
    _, m1b_rows = load_tsv_rows(m1b_path)
    check("M1B_TOTAL_ROWS", len(m1b_rows) == 830, 830, len(m1b_rows))
    m1b_f2 = [r for r in m1b_rows if r.get("tree") == "F2"]
    m1b_f3 = [r for r in m1b_rows if r.get("tree") == "F3"]
    check("M1B_F2_ROWS", len(m1b_f2) == 415, 415, len(m1b_f2))
    check("M1B_F3_ROWS", len(m1b_f3) == 415, 415, len(m1b_f3))
    m1b_keys = [(r["group"], r["point_id"], r["tree"]) for r in m1b_rows]
    check("M1B_KEYS_UNIQUE", len(m1b_keys) == len(set(m1b_keys)), "unique", "unique" if len(m1b_keys) == len(set(m1b_keys)) else "duplicate")

    # 6. Row counts: M1c 440 (F2 220, F3 220)
    _, m1c_rows = load_tsv_rows(m1c_path)
    check("M1C_TOTAL_ROWS", len(m1c_rows) == 440, 440, len(m1c_rows))
    m1c_f2 = [r for r in m1c_rows if r.get("tree") == "F2"]
    m1c_f3 = [r for r in m1c_rows if r.get("tree") == "F3"]
    check("M1C_F2_ROWS", len(m1c_f2) == 220, 220, len(m1c_f2))
    check("M1C_F3_ROWS", len(m1c_f3) == 220, 220, len(m1c_f3))
    m1c_keys = [(r["group"], r["point_id"], r["tree"]) for r in m1c_rows]
    check("M1C_KEYS_UNIQUE", len(m1c_keys) == len(set(m1c_keys)), "unique", "unique" if len(m1c_keys) == len(set(m1c_keys)) else "duplicate")

    # 7. Two BASELINE_RC_EQUAL controls: original basis & contract
    posthoc_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7", "RESULTS_R7_M1_CTRL_REJUDGE_POSTHOC.tsv")
    _, posthoc_rows = load_tsv_rows(posthoc_path)
    p_fftvl = [r for r in posthoc_rows if r.get("point_id") == "M1-CTRL-F2-fftvl-ng1"]
    p_vl = [r for r in posthoc_rows if r.get("point_id") == "M1-CTRL-F2-vl-ng1"]
    posthoc_valid = (len(p_fftvl) == 2 and len(p_vl) == 2 and
                     all(r.get("obs_rc_first") == "20" and r.get("obs_rc_retry") == "20" and
                         r.get("obs_run_rc") == "0" and r.get("hit") == "0" and
                         r.get("label") == "BASELINE_RC_EQUAL" for r in p_fftvl + p_vl))
    check("POSTHOC_BASELINE_RC_EQUAL_ORIGIN", posthoc_valid, "rc1=20 rc2=20 run_rc=0 hit=0 label=BASELINE_RC_EQUAL", "valid" if posthoc_valid else "invalid")

    bl_rows = [r for r in m1b_rows if r.get("comparison_contract") == "BASELINE_RC_EQUAL"]
    check("M1B_BASELINE_RC_EQUAL_COUNT", len(bl_rows) == 4, 4, len(bl_rows))
    bl_facts_ok = all(r.get("expected_class") == "INVALID" and r.get("expected_rc1") == "20" and
                      r.get("expected_rc2") == "20" and r.get("expected_run_rc") == "0" and
                      r.get("expected_hit") == "0" and r.get("expected_label") == "BASELINE_RC_EQUAL"
                      for r in bl_rows)
    check("M1B_BASELINE_RC_EQUAL_FACTS", bl_facts_ok, "class=INVALID rc1=20 rc2=20 run_rc=0 hit=0", "matched" if bl_facts_ok else "mismatch")

    # 8. STOP-EXP-1 (U198) and STOP-EXP-2 (U199 + E8-70)
    rulings_path = os.path.join(REPO, "checkpoints", "p05", "registries", "RULINGS.tsv")
    u198_found = False
    u199_found = False
    with open(rulings_path, encoding="utf-8") as fh:
        for line in fh:
            parts = line.strip().split("\t")
            if len(parts) >= 5:
                if parts[0] == "U198" and parts[4] == "生效":
                    u198_found = True
                if parts[0] == "U199" and parts[4] == "生效":
                    u199_found = True
    check("RULING_U198_EFFECTIVE", u198_found, True, u198_found)
    check("RULING_U199_EFFECTIVE", u199_found, True, u199_found)

    errata8_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "ERRATA_8.txt")
    err8_text = open(errata8_path, encoding="utf-8").read() if os.path.isfile(errata8_path) else ""
    check("ERRATA_E8_70_EXISTS", "E8-70" in err8_text, True, "E8-70" in err8_text)

    prereg_stop_path = os.path.join(m1a_dir, "PREREG_STOP_R8_M1a6.tsv")
    _, stop_rows = load_tsv_rows(prereg_stop_path)
    check("PREREG_STOP_COUNT", len(stop_rows) == 0, 0, len(stop_rows))

    # 9. STATE <= 8192 UTF-8 bytes
    state_path = os.path.join(REPO, "checkpoints", "p05", "STATE.md")
    state_bytes = len(open(state_path, "rb").read()) if os.path.isfile(state_path) else 999999
    check("STATE_BYTES_LE_8192", state_bytes <= 8192, "<= 8192", state_bytes)

    # 10. RULINGS & ERRATA_8 prefix checks
    rul_head = subprocess.check_output(["git", "show", "HEAD:checkpoints/p05/registries/RULINGS.tsv"], cwd=REPO)
    rul_now = open(rulings_path, "rb").read()
    check("RULINGS_HEAD_PREFIX_UNCHANGED", rul_now.startswith(rul_head), True, rul_now.startswith(rul_head))
    check("RULINGS_LINES_5_FIELDS", all(len(l.split("\t")) == 5 for l in rul_now.decode("utf-8").splitlines() if l.strip() and not l.startswith("#")), True, True)

    err_head = subprocess.check_output(["git", "show", "HEAD:checkpoints/p05/registries/s4r8/ERRATA_8.txt"], cwd=REPO)
    err_now = open(errata8_path, "rb").read()
    check("ERRATA_8_HEAD_PREFIX_UNCHANGED", err_now.startswith(err_head), True, err_now.startswith(err_head))

    if mode == "end" and start_records:
        start_rul_sha = start_records.get("RULINGS_SHA256")
        start_rul_bytes = int(start_records.get("RULINGS_BYTES", "0"))
        start_err_sha = start_records.get("ERRATA_8_SHA256")
        start_err_bytes = int(start_records.get("ERRATA_8_BYTES", "0"))
        if start_rul_bytes > 0:
            rul_pfx_sha = hashlib.sha256(rul_now[:start_rul_bytes]).hexdigest()
            check("RULINGS_PREFIX_OF_START_UNCHANGED", rul_pfx_sha == start_rul_sha, start_rul_sha, rul_pfx_sha)
            check("RULINGS_NOT_TRUNCATED", len(rul_now) >= start_rul_bytes, True, len(rul_now) >= start_rul_bytes)
        if start_err_bytes > 0:
            err_pfx_sha = hashlib.sha256(err_now[:start_err_bytes]).hexdigest()
            check("ERRATA_8_PREFIX_OF_START_UNCHANGED", err_pfx_sha == start_err_sha, start_err_sha, err_pfx_sha)
            check("ERRATA_8_NOT_TRUNCATED", len(err_now) >= start_err_bytes, True, len(err_now) >= start_err_bytes)

    return fails, results

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "startA"
    fails, results = run_checks(mode)
    for st, name, exp, act in results:
        print("%s\t%s\texpected=%s\tactual=%s" % (st, name, exp, act))
    print("PYTHON_CHECKS_FAILS=%d" % fails)
    sys.exit(fails)
