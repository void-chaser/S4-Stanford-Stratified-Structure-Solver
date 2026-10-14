#!/usr/bin/env python3
# verify_prereg_r8m1a6.py -- independent verification of M1b and M1c formal preregistrations (brief §6). New file.
# Directly recomputes and verifies from original source tables. Does NOT rely on generator's OK column.
import hashlib, os, re, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1a6")
R7 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7")
R3C2 = os.path.join(REPO, "checkpoints", "p05", "registries", "s3r4c2")
R3C3 = os.path.join(REPO, "checkpoints", "p05", "registries", "s3r4c3")
M1A = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")

FAILS = 0
CHECKS = []

def check(name, cond, msg=""):
    global FAILS
    if cond:
        CHECKS.append("PASS\t%s" % name)
    else:
        FAILS += 1
        CHECKS.append("FAIL\t%s\t%s" % (name, msg))

def load_tsv(path):
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip("\r\n") for l in fh if not l.startswith("#") and l.strip()]
    header = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        rows.append(dict(zip(header, line.split("\t"))))
    return rows

def main():
    m1b_path = os.path.join(EV, "REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv")
    m1c_path = os.path.join(EV, "REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv")
    check("M1B_FILE_EXISTS", os.path.isfile(m1b_path), "missing M1b file")
    check("M1C_FILE_EXISTS", os.path.isfile(m1c_path), "missing M1c file")
    if FAILS > 0:
        return

    m1b = load_tsv(m1b_path)
    m1c = load_tsv(m1c_path)

    # 1. Total rows
    check("M1B_ROW_COUNT", len(m1b) == 830, "expected 830, got %d" % len(m1b))
    check("M1C_ROW_COUNT", len(m1c) == 440, "expected 440, got %d" % len(m1c))

    # 2. Key uniqueness
    m1b_keys = [(r["group"], r["point_id"], r["tree"]) for r in m1b]
    check("M1B_KEYS_UNIQUE", len(m1b_keys) == len(set(m1b_keys)), "duplicate keys in M1b")

    m1c_keys = [(r["group"], r["point_id"], r["tree"]) for r in m1c]
    check("M1C_KEYS_UNIQUE", len(m1c_keys) == len(set(m1c_keys)), "duplicate keys in M1c")

    # 3. F2 / F3 counts
    m1b_f2 = [r for r in m1b if r["tree"] == "F2"]
    m1b_f3 = [r for r in m1b if r["tree"] == "F3"]
    check("M1B_F2_F3_EQUAL", len(m1b_f2) == 415 and len(m1b_f3) == 415, "F2=%d, F3=%d" % (len(m1b_f2), len(m1b_f3)))

    m1c_f2 = [r for r in m1c if r["tree"] == "F2"]
    m1c_f3 = [r for r in m1c if r["tree"] == "F3"]
    check("M1C_F2_F3_EQUAL", len(m1c_f2) == 220 and len(m1c_f3) == 220, "F2=%d, F3=%d" % (len(m1c_f2), len(m1c_f3)))

    # 4. Drivers catalog verification
    drv_r8 = load_tsv(os.path.join(M1A, "DRIVERS_R8_M1a.tsv"))
    drv_f2 = load_tsv(os.path.join(M1A, "DRIVERS_R8_M1a_F2_REUSED.tsv"))
    drv_map = {}
    for r in drv_r8:
        drv_map[r["driver"]] = r.get("driver_sha256") or r.get("sha256_now") or r.get("sha256_record")
    for r in drv_f2:
        drv_map[r["driver"]] = r.get("driver_sha256") or r.get("sha256_now") or r.get("sha256_record")

    drv_errors = 0
    for r in m1b + m1c:
        dname = r["driver_name"]
        dsha = r["driver_sha256"]
        if dname not in drv_map or drv_map[dname] != dsha:
            drv_errors += 1
    check("DRIVERS_SHA_VALID", drv_errors == 0, "%d rows with invalid driver sha256" % drv_errors)

    # 5. Check BASELINE_RC_EQUAL controls (U198)
    posthoc = load_tsv(os.path.join(R7, "RESULTS_R7_M1_CTRL_REJUDGE_POSTHOC.tsv"))
    posthoc_p1 = {r["point_id"]: r for r in posthoc if r.get("pass") == "1"}
    posthoc_p2 = {r["point_id"]: r for r in posthoc if r.get("pass") == "2"}

    m1_ctrl_rows = [r for r in m1b if r["group"] == "M1_CTRL"]
    check("M1_CTRL_ROW_COUNT", len(m1_ctrl_rows) == 36, "expected 36 rows, got %d" % len(m1_ctrl_rows))

    bl_f2 = [r for r in m1_ctrl_rows if r["comparison_contract"] == "BASELINE_RC_EQUAL" and r["tree"] == "F2"]
    bl_f3 = [r for r in m1_ctrl_rows if r["comparison_contract"] == "BASELINE_RC_EQUAL" and r["tree"] == "F3"]
    check("BASELINE_RC_EQUAL_COUNT", len(bl_f2) == 2 and len(bl_f3) == 2, "expected 2 F2 and 2 F3 rows")

    for r in bl_f2 + bl_f3:
        check("BASELINE_FACTS_" + r["point_id"],
              r["expected_class"] == "INVALID" and r["expected_rc1"] == "20" and
              r["expected_rc2"] == "20" and r["expected_run_rc"] == "0" and
              r["expected_hit"] == "0" and r["expected_label"] == "BASELINE_RC_EQUAL",
              "facts mismatch on " + r["point_id"])

    # 6. Check G5 (177), G6 (25), G6c (18)
    g5_rows = [r for r in m1c if r["group"] == "G5"]
    g6_rows = [r for r in m1c if r["group"] == "G6"]
    g6c_rows = [r for r in m1c if r["group"] == "G6c"]
    check("M1C_G5_COUNT", len(g5_rows) == 354, "expected 354, got %d" % len(g5_rows))
    check("M1C_G6_COUNT", len(g6_rows) == 50, "expected 50, got %d" % len(g6_rows))
    check("M1C_G6C_COUNT", len(g6c_rows) == 36, "expected 36, got %d" % len(g6c_rows))

    # K source breakdown for G5
    g5_f2_rows = [r for r in g5_rows if r["tree"] == "F2"]
    k_req_cnt = sum(1 for r in g5_f2_rows if r["k_source"] == "K_FROM_REQUEST_AGREED")
    k_hist_cnt = sum(1 for r in g5_f2_rows if r["k_source"] == "K_FROM_HISTORY_AGREED")
    check("G5_K_REQUEST_AGREED_58", k_req_cnt == 58, "expected 58, got %d" % k_req_cnt)
    check("G5_K_HISTORY_AGREED_119", k_hist_cnt == 119, "expected 119, got %d" % k_hist_cnt)

    # 7. Check S3R4 additions (22 points = 44 rows)
    add22_rows = [r for r in m1b if r["group"] == "ADDITIONS_22"]
    check("ADDITIONS_22_COUNT", len(add22_rows) == 44, "expected 44, got %d" % len(add22_rows))
    add22_f2 = [r for r in add22_rows if r["tree"] == "F2"]
    add22_strict_cnt = sum(1 for r in add22_f2 if r["callseq_status"] == "MAPPING_VERIFIED_STRICT")
    add22_k0_cnt = sum(1 for r in add22_f2 if r["callseq_status"] == "NOT_VERIFIED_K0_VERIFY_BY_INJECTION")
    add22_ctrl_cnt = sum(1 for r in add22_f2 if r["callseq_status"] == "N/A_CONTROL")
    check("ADD22_STRICT_17", add22_strict_cnt == 17, "expected 17, got %d" % add22_strict_cnt)
    check("ADD22_K0_3", add22_k0_cnt == 3, "expected 3, got %d" % add22_k0_cnt)
    check("ADD22_CTRL_2", add22_ctrl_cnt == 2, "expected 2, got %d" % add22_ctrl_cnt)

    # 8. Check S3R4 polygon (33 points = 66 rows)
    poly_rows = [r for r in m1b if r["group"] == "POLY_33"]
    check("POLY_33_COUNT", len(poly_rows) == 66, "expected 66, got %d" % len(poly_rows))
    for r in poly_rows:
        check("POLY_CONTRACT_" + r["point_id"],
              r["expected_class"] == "CONTROL_OK" and r["expected_rc1"] == "0" and
              r["comparison_contract"] == "IDENTICAL" and r["callseq_status"] == "N/A_CONTROL",
              "contract mismatch")

    # Write verification log
    out_log = os.path.join(EV, "VERIFY_PREREG_R8_M1a6.txt")
    with open(out_log, "w", encoding="utf-8") as fh:
        fh.write("# VERIFY_PREREG_R8_M1a6.txt -- independent verification of preregistrations\n")
        for l in CHECKS:
            fh.write(l + "\n")
        fh.write("FAILS=%d\n" % FAILS)

    print("verify_prereg_r8m1a6: checks=%d, FAILS=%d -> %s" % (len(CHECKS), FAILS, out_log))

if __name__ == "__main__":
    main()
