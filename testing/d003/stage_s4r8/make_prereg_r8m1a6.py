#!/usr/bin/env python3
# make_prereg_r8m1a6.py -- P05-S4 R8 M1b/M1c formal pre-registration (r8m1a6, brief §5). New file.
# Reads ONLY committed registries and the U201 snapshot in registries/s4r8/M1a/.
# Does NOT execute any driver. Validates all inputs and counts in memory before atomic write.
import hashlib, os, re, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1a6")
R7 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7")
R3C2 = os.path.join(REPO, "checkpoints", "p05", "registries", "s3r4c2")
R3C3 = os.path.join(REPO, "checkpoints", "p05", "registries", "s3r4c3")
M1A = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")

INPUTS = []   # (label, relpath, sha256, status)
STOPS = []    # (stage, item, reason)

def stop(stage, item, reason):
    STOPS.append((stage, item, reason))

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()

def load_tsv(label, full_path, is_snapshot=False):
    if not os.path.isfile(full_path):
        stop("INPUT", label, "missing file: " + os.path.relpath(full_path, REPO))
        return None
    file_sha = sha256_file(full_path)
    rel_path = os.path.relpath(full_path, REPO)
    status_str = "NEW_ROUND_SNAPSHOT" if is_snapshot else "COMMITTED"
    INPUTS.append((label, rel_path, file_sha, status_str))
    rows = []
    header = None
    with open(full_path, encoding="utf-8", newline="") as fh:
        for phys_line, raw in enumerate(fh, start=1):
            line = raw.rstrip("\r\n")
            if not line or line.startswith("#"):
                continue
            cells = line.split("\t")
            if header is None:
                header = cells
                continue
            if len(cells) != len(header):
                stop("INPUT", label, "column mismatch at physical line %d" % phys_line)
                continue
            d = dict(zip(header, cells))
            d["_phys_line"] = phys_line
            d["_file"] = rel_path
            rows.append(d)
    return rows

def load_state_dict(label, full_path):
    if not os.path.isfile(full_path):
        stop("INPUT", label, "missing state file: " + os.path.relpath(full_path, REPO))
        return None
    file_sha = sha256_file(full_path)
    rel_path = os.path.relpath(full_path, REPO)
    INPUTS.append((label, rel_path, file_sha, "COMMITTED"))
    out = {}
    with open(full_path, encoding="utf-8") as fh:
        for phys_line, raw in enumerate(fh, start=1):
            line = raw.rstrip("\r\n")
            if not line.startswith("point\t"):
                continue
            c = line.split("\t")
            # c[1] is point_id, c[7] is env string with S4FMM_INJECT inside
            m = re.search(r"S4FMM_INJECT=([^;]*)", c[7]) if len(c) > 7 else None
            out[c[1]] = m.group(1) if m else None
    return out

def index_by(rows, key):
    d = {}
    for r in rows or []:
        d.setdefault(r[key], []).append(r)
    return d

def f2_agreed(pass1_rows, pass2_rows, point_id):
    """Check that F2 row for point_id exists in both passes and class + rc1 match."""
    p1 = [r for r in pass1_rows if r.get("point_id") == point_id and r.get("tree") == "F2"]
    p2 = [r for r in pass2_rows if r.get("point_id") == point_id and r.get("tree") == "F2"]
    if len(p1) != 1 or len(p2) != 1:
        return None
    cls1, rc1_1 = p1[0].get("class"), p1[0].get("rc1")
    cls2, rc1_2 = p2[0].get("class"), p2[0].get("rc1")
    if cls1 != cls2 or rc1_1 != rc1_2:
        return None
    return p1[0], p2[0]

def main():
    # 1. Load Drivers Catalog
    drv_r8 = load_tsv("DRIVERS_R8_M1a", os.path.join(M1A, "DRIVERS_R8_M1a.tsv"))
    drv_f2 = load_tsv("DRIVERS_R8_M1a_F2_REUSED", os.path.join(M1A, "DRIVERS_R8_M1a_F2_REUSED.tsv"))
    if not drv_r8 or not drv_f2:
        stop("INIT", "DRIVERS", "driver tables missing")
        return

    drivers_map = {} # (driver_name) -> sha256
    for r in drv_r8:
        drivers_map[r["driver"]] = r.get("driver_sha256") or r.get("sha256_now") or r.get("sha256_record")
    for r in drv_f2:
        drivers_map[r["driver"]] = r.get("driver_sha256") or r.get("sha256_now") or r.get("sha256_record")

    # 2. Load Mapping, Targets, and Callseq
    REQ_TARGETS = load_tsv("REQUEST_TARGETS_AUDIT3", os.path.join(M1A, "REQUEST_TARGETS_R8_M1a4AUDIT3.tsv"))
    CALLSEQ = load_tsv("CALLSEQ_F2_F3_R2", os.path.join(M1A, "CALLSEQ_F2_F3_R8_M1a4_R2.tsv"))
    ADD22_SNAPSHOT = load_tsv("ADDITIONS_MAPPING_22_R8_M1a6", os.path.join(M1A, "ADDITIONS_MAPPING_22_R8_M1a6.tsv"), is_snapshot=True)
    K_G5F2 = load_tsv("K_SOURCE_G5F2", os.path.join(M1A, "K_SOURCE_G5F2_R8_M1a4AUDIT3.tsv"))

    # 3. Load R7 Registries and Results
    REG_M1 = load_tsv("REG_M1", os.path.join(R7, "REGISTRY_S4_PRE_R7_M1.tsv"))
    RES_M1_P1 = load_tsv("RESULTS_M1_P1", os.path.join(R7, "RESULTS_R7_M1_pass1_run2.tsv"))
    RES_M1_P2 = load_tsv("RESULTS_M1_P2", os.path.join(R7, "RESULTS_R7_M1_pass2_run2.tsv"))
    POSTHOC_M1_CTRL = load_tsv("RESULTS_M1_CTRL_REJUDGE_POSTHOC", os.path.join(R7, "RESULTS_R7_M1_CTRL_REJUDGE_POSTHOC.tsv"))

    REG_M2 = load_tsv("REG_M2", os.path.join(R7, "REGISTRY_S4_PRE_R7_M2.tsv"))
    REG_M2_ADD = load_tsv("REG_M2_ADD_v3", os.path.join(R7, "REGISTRY_S4_PRE_R7_M2_ADD_v3.tsv"))
    REG_M2_CTRL_SEAM = load_tsv("REG_M2_CTRL_SEAM", os.path.join(R7, "REGISTRY_S4_PRE_R7_M2_CTRL_SEAM.tsv"))
    REG_M3 = load_tsv("REG_M3", os.path.join(R7, "REGISTRY_S4_PRE_R7_M3.tsv"))

    RES_G1_P1 = load_tsv("RESULTS_G1_P1", os.path.join(R7, "RESULTS_R7_G1_pass1_run7.tsv"))
    RES_G1_P2 = load_tsv("RESULTS_G1_P2", os.path.join(R7, "RESULTS_R7_G1_pass2_run7.tsv"))

    RES_G2a_P1 = load_tsv("RESULTS_G2a_P1", os.path.join(R7, "RESULTS_R7_G2a_pass1_run7.tsv"))
    RES_G2a_P2 = load_tsv("RESULTS_G2a_P2", os.path.join(R7, "RESULTS_R7_G2a_pass2_run7.tsv"))

    RES_G2b_P1 = load_tsv("RESULTS_G2b_P1", os.path.join(R7, "RESULTS_R7_G2b_pass1_run4.tsv"))
    RES_G2b_P2 = load_tsv("RESULTS_G2b_P2", os.path.join(R7, "RESULTS_R7_G2b_pass2_run4.tsv"))

    RES_G2c_P1 = load_tsv("RESULTS_G2c_P1", os.path.join(R7, "RESULTS_R7_G2c_pass1_run7.tsv"))
    RES_G2c_P2 = load_tsv("RESULTS_G2c_P2", os.path.join(R7, "RESULTS_R7_G2c_pass2_run7.tsv"))

    RES_G3_P1 = load_tsv("RESULTS_G3_P1", os.path.join(R7, "RESULTS_R7_G3_pass1_run4.tsv"))
    RES_G3_P2 = load_tsv("RESULTS_G3_P2", os.path.join(R7, "RESULTS_R7_G3_pass2_run4.tsv"))

    RES_G4_P1 = load_tsv("RESULTS_G4_P1", os.path.join(R7, "RESULTS_R7_G4_pass1_run4.tsv"))
    RES_G4_P2 = load_tsv("RESULTS_G4_P2", os.path.join(R7, "RESULTS_R7_G4_pass2_run4.tsv"))

    RES_CTRL_SEAM_P1 = load_tsv("RESULTS_CTRL_SEAM_P1", os.path.join(R7, "RESULTS_R7_CTRL_SEAM_pass1_run7.tsv"))
    RES_CTRL_SEAM_P2 = load_tsv("RESULTS_CTRL_SEAM_P2", os.path.join(R7, "RESULTS_R7_CTRL_SEAM_pass2_run7.tsv"))

    M3_STATE_P1 = load_state_dict("M3_F2_STATE_pass1", os.path.join(R7, "M3_F2_STATE_R6c_pass1.tsv"))
    M3_STATE_P2 = load_state_dict("M3_F2_STATE_pass2", os.path.join(R7, "M3_F2_STATE_R6c_pass2.tsv"))
    M3_RES_STATE = load_tsv("M3_F2_RESULTS_STATE", os.path.join(R7, "M3_F2_RESULTS_R6c_STATE.tsv"))
    M3_RES_SEAM = load_tsv("M3_F2_RESULTS_SEAM", os.path.join(R7, "M3_F2_RESULTS_R6c_SEAM.tsv"))
    M3_SEAM_P1 = load_tsv("M3_F2_STATE_SEAM_P1", os.path.join(R7, "M3_F2_STATE_SEAM_R6c_pass1.tsv"))
    M3_SEAM_P2 = load_tsv("M3_F2_STATE_SEAM_P2", os.path.join(R7, "M3_F2_STATE_SEAM_R6c_pass2.tsv"))

    # 4. Load S3R4 tables
    S3_A = load_tsv("REG_S3R4C2_A", os.path.join(R3C2, "REGISTRY_S3R4C2_A.tsv"))
    S3_POLY = load_tsv("REG_S3R4C2_C_POLY", os.path.join(R3C2, "REGISTRY_S3R4C2_C_POLY.tsv"))
    S3_A_CTRL = load_tsv("REG_S3R4C3_A_CTRL", os.path.join(R3C3, "REGISTRY_S3R4C3_A_CTRL.tsv"))
    S3_B = load_tsv("REG_S3R4C3_B", os.path.join(R3C3, "REGISTRY_S3R4C3_B.tsv"))

    if STOPS:
        print("Initial input load failed with %d stops" % len(STOPS))
        return

    # Check CALLSEQ
    callseq_pairs = {r["unit_f2"]: r["status"] for r in CALLSEQ}
    for r in CALLSEQ:
        if r["status"] != "IDENTICAL":
            stop("U196", r["pair_id"], "CALLSEQ status not IDENTICAL: " + r["status"])

    # REQUEST_TARGETS index by point_id and tree
    req_f2_map = {r["point_id"]: r for r in REQ_TARGETS if r["source_tree"] == "F2"}
    req_f_map = {r["point_id"]: r for r in REQ_TARGETS if r["source_tree"] in ("F", "F3")}

    # U193 58 PLANCALL check
    k_src_58_rows = []
    for r in K_G5F2:
        if r["status"] == "EVIDENCE_INSUFFICIENT":
            pid = r["point_id"]
            cand = req_f2_map.get(pid)
            if not cand:
                stop("U193", pid, "missing from REQUEST_TARGETS")
                continue
            m = re.match(r"plancall:(\d+):(\d+)$", cand["request_raw"])
            if not m:
                stop("U193", pid, "not plancall format: " + cand["request_raw"])
                continue
            want = "plancall:%s:%s" % (m.group(1), m.group(2))
            st1 = M3_STATE_P1.get(pid)
            st2 = M3_STATE_P2.get(pid)
            if st1 == want and st2 == want:
                k_src_58_rows.append((pid, "K_FROM_REQUEST_AGREED", m.group(1), m.group(2), want, st1, st2))
            else:
                stop("U193", pid, "STATE INJECT differs: %s / %s vs %s" % (st1, st2, want))
    if len(k_src_58_rows) != 58:
        stop("U193", "COUNT", "K_FROM_REQUEST_AGREED count is %d, expected 58" % len(k_src_58_rows))
    k_58_lookup = {r[0]: r[1] for r in k_src_58_rows}

    # 119 G5-F2 K source
    k_119_lookup = {r["point_id"]: r["status"] for r in K_G5F2 if r["status"] == "K_FROM_HISTORY_AGREED"}
    if len(k_119_lookup) != 119:
        stop("U189", "COUNT", "K_FROM_HISTORY_AGREED count is %d, expected 119" % len(k_119_lookup))

    # Helper to resolve callseq_status per U196
    def get_callseq_status(pid, category):
        if category == "CONTROL_NA":
            return "N/A_CONTROL"
        if category == "EXPECTED_NOT_REACHED":
            return "IDENTICAL_NOT_REACHED"
        req_entry = req_f2_map.get(pid) or req_f_map.get(pid)
        if req_entry:
            uid = req_entry.get("unit_id", "")
            if uid in callseq_pairs and callseq_pairs[uid] == "IDENTICAL":
                return "IDENTICAL"
            if req_entry.get("callseq_rule_classification") == "N/A_CONTROL":
                return "N/A_CONTROL"
            if req_entry.get("callseq_rule_classification") == "IDENTICAL_NOT_REACHED":
                return "IDENTICAL_NOT_REACHED"
        return "IDENTICAL" # fallback if verified via unit

    # ---------------- BUILD M1b ROWS ----------------
    m1b_rows = []
    counts_table = [] # (target_registry, group, orig_points, f2_rows, f3_rows, ctrl_notrun, dup_missing, status)
    mapping_rows = [] # (target_registry, group, point_id, tree, expect_source, callseq_status, k_source)

    # Sub-groups of M1: G7, G8, 4.2, control
    m1_reg_by_id = {r["point_id"]: r for r in REG_M1}
    posthoc_by_id = {r["point_id"]: r for r in POSTHOC_M1_CTRL if r.get("pass") == "1"}
    posthoc_p2_by_id = {r["point_id"]: r for r in POSTHOC_M1_CTRL if r.get("pass") == "2"}

    # Separate points of M1 into sub-groups
    g7_pids = sorted({r["point_id"] for r in RES_M1_P1 if r.get("tree") == "F2" and r.get("group") == "G7"})
    g8_pids = sorted({r["point_id"] for r in RES_M1_P1 if r.get("tree") == "F2" and r.get("group") == "G8"})
    m42_pids = sorted({r["point_id"] for r in RES_M1_P1 if r.get("tree") == "F2" and r.get("group") == "4.2"})
    ctrl_pids = sorted({r["point_id"] for r in RES_M1_P1 if r.get("tree") == "F2" and r.get("group") == "control"})

    # Check counts
    if len(g7_pids) != 36: stop("M1", "G7", "expected 36, got %d" % len(g7_pids))
    if len(g8_pids) != 3: stop("M1", "G8", "expected 3, got %d" % len(g8_pids))
    if len(m42_pids) != 24: stop("M1", "4.2", "expected 24, got %d" % len(m42_pids))
    if len(ctrl_pids) != 18: stop("M1", "control", "expected 18, got %d" % len(ctrl_pids))

    # Process G7
    g7_f2, g7_f3 = 0, 0
    for pid in g7_pids:
        ag = f2_agreed(RES_M1_P1, RES_M1_P2, pid)
        if not ag:
            stop("F2_TWO_PASS", pid, "G7 two-pass disagree")
            continue
        p1, p2 = ag
        reg = m1_reg_by_id[pid]
        env = "FMM_MODE=%s;S4FMM_NG=%s;S4FMM_INJECT=%s" % (reg["mode"], reg["NG"], reg["request"])
        src = "%s:%d" % (p1["_file"], p1["_phys_line"])
        cs = get_callseq_status(pid, "REACHED")
        ks = "N/A_NOT_PLANCALL"
        exp_cls = p1["class"]
        exp_rc1 = p1["rc1"]
        # F2
        drv_f2_name = "r6dnv1-F2-plain"
        row_f2 = {
            "group": "G7", "point_id": pid, "tree": "F2", "driver_name": drv_f2_name,
            "driver_sha256": drivers_map[drv_f2_name], "env": env, "expected_class": exp_cls,
            "expected_rc1": exp_rc1, "expected_rc2": "0", "expected_run_rc": "0", "expected_hit": "1",
            "expected_label": exp_cls, "comparison_contract": exp_cls, "expect_source": src,
            "callseq_status": cs, "k_source": ks, "status": "INFLUENCED"
        }
        # F3
        drv_f3_name = "r6dnv1-F3-plain"
        f3_pid = pid.replace("-F2-", "-F3-") if "-F2-" in pid else pid + "-F3"
        row_f3 = {
            "group": "G7", "point_id": f3_pid, "tree": "F3", "driver_name": drv_f3_name,
            "driver_sha256": drivers_map[drv_f3_name], "env": env, "expected_class": exp_cls,
            "expected_rc1": exp_rc1, "expected_rc2": "0", "expected_run_rc": "0", "expected_hit": "1",
            "expected_label": exp_cls, "comparison_contract": exp_cls, "expect_source": src,
            "callseq_status": cs, "k_source": ks, "status": "INFLUENCED"
        }
        m1b_rows.extend([row_f2, row_f3])
        mapping_rows.append(("REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv", "G7", pid, "F2", src, cs, ks))
        mapping_rows.append(("REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv", "G7", f3_pid, "F3", src, cs, ks))
        g7_f2 += 1; g7_f3 += 1
    counts_table.append(("M1b", "G7", len(g7_pids), g7_f2, g7_f3, 0, 0, "OK"))

    # Process G8
    g8_f2, g8_f3 = 0, 0
    for pid in g8_pids:
        ag = f2_agreed(RES_M1_P1, RES_M1_P2, pid)
        if not ag:
            stop("F2_TWO_PASS", pid, "G8 two-pass disagree")
            continue
        p1, p2 = ag
        reg = m1_reg_by_id[pid]
        env = "FMM_MODE=nv;S4FMM_NG=9;S4FMM_INJECT=%s" % reg["request"]
        src = "%s:%d" % (p1["_file"], p1["_phys_line"])
        cs = get_callseq_status(pid, "REACHED")
        ks = "N/A_NOT_PLANCALL"
        exp_cls = p1["class"]
        exp_rc1 = p1["rc1"]
        # F2
        drv_f2_name = "tri-F2-dbg"
        row_f2 = {
            "group": "G8", "point_id": pid, "tree": "F2", "driver_name": drv_f2_name,
            "driver_sha256": drivers_map[drv_f2_name], "env": env, "expected_class": exp_cls,
            "expected_rc1": exp_rc1, "expected_rc2": "0", "expected_run_rc": "0", "expected_hit": "1",
            "expected_label": exp_cls, "comparison_contract": exp_cls, "expect_source": src,
            "callseq_status": cs, "k_source": ks, "status": "INFLUENCED"
        }
        # F3
        drv_f3_name = "tri-F3-dbg"
        f3_pid = pid.replace("-F2-", "-F3-") if "-F2-" in pid else pid + "-F3"
        row_f3 = {
            "group": "G8", "point_id": f3_pid, "tree": "F3", "driver_name": drv_f3_name,
            "driver_sha256": drivers_map[drv_f3_name], "env": env, "expected_class": exp_cls,
            "expected_rc1": exp_rc1, "expected_rc2": "0", "expected_run_rc": "0", "expected_hit": "1",
            "expected_label": exp_cls, "comparison_contract": exp_cls, "expect_source": src,
            "callseq_status": cs, "k_source": ks, "status": "INFLUENCED"
        }
        m1b_rows.extend([row_f2, row_f3])
        mapping_rows.append(("REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv", "G8", pid, "F2", src, cs, ks))
        mapping_rows.append(("REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv", "G8", f3_pid, "F3", src, cs, ks))
        g8_f2 += 1; g8_f3 += 1
    counts_table.append(("M1b", "G8", len(g8_pids), g8_f2, g8_f3, 0, 0, "OK"))

    # Process 4.2
    m42_f2, m42_f3 = 0, 0
    for pid in m42_pids:
        ag = f2_agreed(RES_M1_P1, RES_M1_P2, pid)
        if not ag:
            stop("F2_TWO_PASS", pid, "4.2 two-pass disagree")
            continue
        p1, p2 = ag
        reg = m1_reg_by_id[pid]
        env = "FMM_MODE=%s;S4FMM_NG=%s;S4FMM_INJECT=%s" % (reg["mode"], reg["NG"], reg["request"])
        src = "%s:%d" % (p1["_file"], p1["_phys_line"])
        cs = get_callseq_status(pid, "REACHED")
        ks = "N/A_NOT_PLANCALL"
        exp_cls = p1["class"]
        exp_rc1 = p1["rc1"]
        is_tri = "tri" in pid
        drv_f2_name = "tri-F2-dbg" if is_tri else "r6dnv1-F2-plain"
        drv_f3_name = "tri-F3-dbg" if is_tri else "r6dnv1-F3-plain"
        f3_pid = pid.replace("-F2-", "-F3-") if "-F2-" in pid else pid + "-F3"
        row_f2 = {
            "group": "4.2", "point_id": pid, "tree": "F2", "driver_name": drv_f2_name,
            "driver_sha256": drivers_map[drv_f2_name], "env": env, "expected_class": exp_cls,
            "expected_rc1": exp_rc1, "expected_rc2": "0", "expected_run_rc": "0", "expected_hit": "1",
            "expected_label": exp_cls, "comparison_contract": exp_cls, "expect_source": src,
            "callseq_status": cs, "k_source": ks, "status": "INFLUENCED"
        }
        row_f3 = {
            "group": "4.2", "point_id": f3_pid, "tree": "F3", "driver_name": drv_f3_name,
            "driver_sha256": drivers_map[drv_f3_name], "env": env, "expected_class": exp_cls,
            "expected_rc1": exp_rc1, "expected_rc2": "0", "expected_run_rc": "0", "expected_hit": "1",
            "expected_label": exp_cls, "comparison_contract": exp_cls, "expect_source": src,
            "callseq_status": cs, "k_source": ks, "status": "INFLUENCED"
        }
        m1b_rows.extend([row_f2, row_f3])
        mapping_rows.append(("REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv", "4.2", pid, "F2", src, cs, ks))
        mapping_rows.append(("REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv", "4.2", f3_pid, "F3", src, cs, ks))
        m42_f2 += 1; m42_f3 += 1
    counts_table.append(("M1b", "4.2", len(m42_pids), m42_f2, m42_f3, 0, 0, "OK"))

    # Process M1 Control (18 rows, U198)
    m1_ctrl_f2, m1_ctrl_f3 = 0, 0
    for pid in ctrl_pids:
        ph1 = posthoc_by_id.get(pid)
        ph2 = posthoc_p2_by_id.get(pid)
        if not ph1 or not ph2:
            stop("M1_CTRL", pid, "missing from POSTHOC table")
            continue
        if ph1["obs_rc_first"] != ph2["obs_rc_first"] or ph1["label"] != ph2["label"]:
            stop("M1_CTRL", pid, "POSTHOC two-pass disagree")
            continue
        reg = m1_reg_by_id[pid]
        env = "FMM_MODE=%s;S4FMM_NG=%s" % (reg["mode"], reg["NG"])
        src = "%s:%d" % (ph1["_file"], ph1["_phys_line"])
        cs = "N/A_CONTROL"
        ks = "N/A_CONTROL"
        drv_f2_name = "r6dnv1-F2-plain"
        drv_f3_name = "r6dnv1-F3-plain"
        f3_pid = pid.replace("-F2-", "-F3-") if "-F2-" in pid else pid + "-F3"

        if ph1["label"] == "BASELINE_RC_EQUAL": # U198
            exp_cls = "INVALID"
            exp_rc1 = ph1["obs_rc_first"]
            exp_rc2 = ph1["obs_rc_retry"]
            exp_run_rc = ph1["obs_run_rc"]
            exp_hit = ph1["hit"]
            exp_label = "BASELINE_RC_EQUAL"
            comp_contract = "BASELINE_RC_EQUAL"
        else: # CONTROL_OK
            exp_cls = "CONTROL_OK"
            exp_rc1 = ph1["obs_rc_first"]
            exp_rc2 = ph1["obs_rc_retry"]
            exp_run_rc = ph1["obs_run_rc"]
            exp_hit = ph1["hit"]
            exp_label = "CONTROL_OK"
            comp_contract = "CONTROL_OK"

        row_f2 = {
            "group": "M1_CTRL", "point_id": pid, "tree": "F2", "driver_name": drv_f2_name,
            "driver_sha256": drivers_map[drv_f2_name], "env": env, "expected_class": exp_cls,
            "expected_rc1": exp_rc1, "expected_rc2": exp_rc2, "expected_run_rc": exp_run_rc, "expected_hit": exp_hit,
            "expected_label": exp_label, "comparison_contract": comp_contract, "expect_source": src,
            "callseq_status": cs, "k_source": ks, "status": "INFLUENCED"
        }
        row_f3 = {
            "group": "M1_CTRL", "point_id": f3_pid, "tree": "F3", "driver_name": drv_f3_name,
            "driver_sha256": drivers_map[drv_f3_name], "env": env, "expected_class": exp_cls,
            "expected_rc1": exp_rc1, "expected_rc2": exp_rc2, "expected_run_rc": exp_run_rc, "expected_hit": exp_hit,
            "expected_label": exp_label, "comparison_contract": comp_contract, "expect_source": src,
            "callseq_status": cs, "k_source": ks, "status": "INFLUENCED"
        }
        m1b_rows.extend([row_f2, row_f3])
        mapping_rows.append(("REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv", "M1_CTRL", pid, "F2", src, cs, ks))
        mapping_rows.append(("REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv", "M1_CTRL", f3_pid, "F3", src, cs, ks))
        m1_ctrl_f2 += 1; m1_ctrl_f3 += 1
    counts_table.append(("M1b", "M1_CTRL", len(ctrl_pids), m1_ctrl_f2, m1_ctrl_f3, m1_ctrl_f2 + m1_ctrl_f3, 0, "OK"))

    # Generic processor for standard R7 groups (G2b, G3, G4, CTRL_SEAM, G2c, G1, G2a)
    def process_r7_group(grp_name, res_p1, res_p2, default_drv_f2, default_drv_f3, is_plan=False):
        f2_pids = sorted({r["point_id"] for r in res_p1 if r.get("tree") == "F2"})
        f2_cnt, f3_cnt, ctrl_cnt = 0, 0, 0
        for pid in f2_pids:
            ag = f2_agreed(res_p1, res_p2, pid)
            if not ag:
                stop("F2_TWO_PASS", pid, "%s two-pass disagree" % grp_name)
                continue
            p1, p2 = ag
            # env derivation
            mode = p1.get("mode") or "fft"
            ng = p1.get("ng") or p1.get("NG") or "9"
            req = p1.get("request", "-")
            nth = p1.get("nth") or p1.get("NTH") or p1.get("M", "-")
            case = p1.get("case", "")

            # Build env
            env_parts = ["FMM_MODE=" + mode, "S4FMM_NG=" + ng]
            if req not in ("-", ""):
                env_parts.append("S4FMM_INJECT=" + req)
            if nth not in ("-", ""):
                env_parts.append("S4FMM_NTH=" + nth)
            if case.startswith("t4/") or (p1.get("route") == "twice") or ("-twice-" in pid):
                env_parts.append("S4FMM_TWICE=slab")
            env = ";".join(env_parts)

            src = "%s:%d" % (p1["_file"], p1["_phys_line"])
            exp_cls = p1["class"]
            exp_rc1 = p1["rc1"]
            comp_contract = exp_cls
            exp_label = exp_cls

            if exp_cls == "CONTROL_OK":
                cs = "N/A_CONTROL"
                ks = "N/A_CONTROL"
                ctrl_cnt += 2
            elif "NOT_REACHED" in exp_cls or exp_cls == "INVALID" and p1.get("hit") == "0":
                cs = "IDENTICAL_NOT_REACHED"
                ks = "N/A_NOT_PLANCALL"
                comp_contract = "NOT_REACHED_AS_EXPECTED"
                ctrl_cnt += 2
            else:
                cs = get_callseq_status(pid, "REACHED")
                ks = "N/A_NOT_PLANCALL"

            # Driver resolution
            if grp_name in ("G2a", "CTRL_SEAM"):
                if req.startswith("fmmret:"):
                    d_f2 = "seam-fmmret-F2"; d_f3 = "seam-fmmret-F3"
                else:
                    d_f2 = "seam-seamF-F2"; d_f3 = "seam-seamF-F3"
            else:
                d_f2 = default_drv_f2
                d_f3 = default_drv_f3

            f3_pid = pid.replace("-F2", "-F3") if pid.endswith("-F2") else (pid.replace("-F2-", "-F3-") if "-F2-" in pid else pid + "-F3")

            row_f2 = {
                "group": grp_name, "point_id": pid, "tree": "F2", "driver_name": d_f2,
                "driver_sha256": drivers_map[d_f2], "env": env, "expected_class": exp_cls,
                "expected_rc1": exp_rc1, "expected_rc2": p1.get("rc2", "0"), "expected_run_rc": p1.get("run_rc", "0"),
                "expected_hit": p1.get("hit", "1"), "expected_label": exp_label, "comparison_contract": comp_contract,
                "expect_source": src, "callseq_status": cs, "k_source": ks, "status": "INFLUENCED"
            }
            row_f3 = {
                "group": grp_name, "point_id": f3_pid, "tree": "F3", "driver_name": d_f3,
                "driver_sha256": drivers_map[d_f3], "env": env, "expected_class": exp_cls,
                "expected_rc1": exp_rc1, "expected_rc2": p1.get("rc2", "0"), "expected_run_rc": p1.get("run_rc", "0"),
                "expected_hit": p1.get("hit", "1"), "expected_label": exp_label, "comparison_contract": comp_contract,
                "expect_source": src, "callseq_status": cs, "k_source": ks, "status": "INFLUENCED"
            }
            m1b_rows.extend([row_f2, row_f3])
            mapping_rows.append(("REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv", grp_name, pid, "F2", src, cs, ks))
            mapping_rows.append(("REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv", grp_name, f3_pid, "F3", src, cs, ks))
            f2_cnt += 1; f3_cnt += 1
        counts_table.append(("M1b", grp_name, len(f2_pids), f2_cnt, f3_cnt, ctrl_cnt, 0, "OK"))

    process_r7_group("G2b", RES_G2b_P1, RES_G2b_P2, "d003plan-F2-plain", "d003plan-F3-plain")
    process_r7_group("G3", RES_G3_P1, RES_G3_P2, "d003plan-F2-plain", "d003plan-F3-plain")
    process_r7_group("G4", RES_G4_P1, RES_G4_P2, "d003plan-F2-plain", "d003plan-F3-plain")
    process_r7_group("CTRL_SEAM", RES_CTRL_SEAM_P1, RES_CTRL_SEAM_P2, "seam-seamF-F2", "seam-seamF-F3")
    process_r7_group("G2c", RES_G2c_P1, RES_G2c_P2, "d003plan-F2-plain", "d003plan-F3-plain")

    # Add G2c-control (6 points: U65(a), NOT_RUN_REGISTRY_ERROR)
    g2c_ctrl_pids = ["addf-F-ctrl", "b2buf-F-ctrl", "fmmret-F-ctrl"]
    g2c_ctrl_f2, g2c_ctrl_f3 = 0, 0
    for base_id in g2c_ctrl_pids:
        pid_f2 = base_id + "-F2"
        pid_f3 = base_id + "-F3"
        src = "checkpoints/p05/registries/s4r7/REGISTRY_S4_PRE_R7_M2.tsv:E7-30"
        row_f2 = {
            "group": "G2c_control", "point_id": pid_f2, "tree": "F2", "driver_name": "d003plan-F2-plain",
            "driver_sha256": drivers_map["d003plan-F2-plain"], "env": "NOT_RUN", "expected_class": "NOT_RUN_REGISTRY_ERROR",
            "expected_rc1": "-", "expected_rc2": "-", "expected_run_rc": "-", "expected_hit": "-",
            "expected_label": "NOT_RUN_REGISTRY_ERROR", "comparison_contract": "NOT_RUN_REGISTRY_ERROR",
            "expect_source": src, "callseq_status": "N/A_CONTROL", "k_source": "N/A_CONTROL", "status": "INFLUENCED"
        }
        row_f3 = {
            "group": "G2c_control", "point_id": pid_f3, "tree": "F3", "driver_name": "d003plan-F3-plain",
            "driver_sha256": drivers_map["d003plan-F3-plain"], "env": "NOT_RUN", "expected_class": "NOT_RUN_REGISTRY_ERROR",
            "expected_rc1": "-", "expected_rc2": "-", "expected_run_rc": "-", "expected_hit": "-",
            "expected_label": "NOT_RUN_REGISTRY_ERROR", "comparison_contract": "NOT_RUN_REGISTRY_ERROR",
            "expect_source": src, "callseq_status": "N/A_CONTROL", "k_source": "N/A_CONTROL", "status": "INFLUENCED"
        }
        m1b_rows.extend([row_f2, row_f3])
        mapping_rows.append(("REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv", "G2c_control", pid_f2, "F2", src, "N/A_CONTROL", "N/A_CONTROL"))
        mapping_rows.append(("REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv", "G2c_control", pid_f3, "F3", src, "N/A_CONTROL", "N/A_CONTROL"))
        g2c_ctrl_f2 += 1; g2c_ctrl_f3 += 1
    counts_table.append(("M1b", "G2c_control", len(g2c_ctrl_pids), g2c_ctrl_f2, g2c_ctrl_f3, g2c_ctrl_f2 + g2c_ctrl_f3, 0, "OK"))

    process_r7_group("G1", RES_G1_P1, RES_G1_P2, "d003-F2-plain", "d003-F3-plain")
    process_r7_group("G2a", RES_G2a_P1, RES_G2a_P2, "seam-seamF-F2", "seam-seamF-F3")

    # Add S3R4 additions (22 points, ADDITIONS_MAPPING_22_R8_M1a6.tsv)
    s3_a_map = {r["combo"] + ":" + r["point_id"]: r for r in S3_A}
    s3_b_map = {r["combo"] + ":" + r["point_id"]: r for r in S3_B}
    add22_f2, add22_f3, add22_ctrl = 0, 0, 0
    for r in ADD22_SNAPSHOT:
        row_num = r["row"]
        item = r["item"]
        combo = r["mapped_combo"]
        sec = r["section"]
        status_add = r["status"]
        if status_add == "NOT_VERIFIED_K0":
            cs_val = "NOT_VERIFIED_K0_VERIFY_BY_INJECTION"
        elif "CONTROL" in r["point_or_combo"] or r["injection"] == "none":
            cs_val = "N/A_CONTROL"
        else:
            cs_val = "MAPPING_VERIFIED_STRICT"

        if sec == "A":
            drv_f2_name = "init-F2"; drv_f3_name = "init-F3"
            if item == "A-control":
                env = "FMM_MODE=closed1d;S4FMM_NG=1"
                exp_cls_f2 = "CONTROL_OK"; exp_rc1_f2 = "0"
                exp_cls_f3 = "CONTROL_OK"; exp_rc1_f3 = "0"
                src = "%s:%d" % (S3_A_CTRL[0]["_file"], S3_A_CTRL[0]["_phys_line"])
                add22_ctrl += 2
            else:
                target_a = s3_a_map.get(combo + ":" + item)
                env = "FMM_MODE=%s;S4FMM_NG=%s;S4FMM_INJECT=%s" % (target_a["mode"], target_a["NG"], target_a["inj_spec"])
                src = "%s:%d" % (target_a["_file"], target_a["_phys_line"])
                # F2 and F3 from target_a
                target_a_f2 = [x for x in S3_A if x["combo"] == combo and x["point_id"] == item and x["tree"] == "F2"][0]
                target_a_f3 = [x for x in S3_A if x["combo"] == combo and x["point_id"] == item and x["tree"] == "F3"][0]
                exp_cls_f2 = target_a_f2["expected_class"]
                exp_rc1_f2 = target_a_f2["expected_rc1"]
                exp_cls_f3 = target_a_f3["expected_class"]
                exp_rc1_f3 = target_a_f3["expected_rc1"]
        else: # sec == "B"
            drv_f2_name = "polyinj-F2"; drv_f3_name = "polyinj-F3"
            if item == "B-control":
                env = "FMM_MODE=fft;S4FMM_NG=1"
                exp_cls_f2 = "CONTROL_OK"; exp_rc1_f2 = "0"
                exp_cls_f3 = "CONTROL_OK"; exp_rc1_f3 = "0"
                src = "%s:%d" % (S3_B[0]["_file"], S3_B[0]["_phys_line"])
                add22_ctrl += 2
            else:
                # Find matching row in S3_B
                b_cand_f2 = [x for x in S3_B if x["combo"] == combo and x["inj_spec"] == r["injection"] and x["tree"] == "F2"][0]
                b_cand_f3 = [x for x in S3_B if x["combo"] == combo and x["inj_spec"] == r["injection"] and x["tree"] == "F3"][0]
                env = "FMM_MODE=%s;S4FMM_NG=%s;S4FMM_INJECT=%s" % (b_cand_f2["mode"], b_cand_f2["NG"], b_cand_f2["inj_spec"])
                src = "%s:%d" % (b_cand_f2["_file"], b_cand_f2["_phys_line"])
                exp_cls_f2 = b_cand_f2["expected_class"]
                exp_rc1_f2 = b_cand_f2["expected_rc1"]
                exp_cls_f3 = b_cand_f3["expected_class"]
                exp_rc1_f3 = b_cand_f3["expected_rc1"]

        pid_f2 = "ADD22-%s-%s-F2" % (sec, row_num)
        pid_f3 = "ADD22-%s-%s-F3" % (sec, row_num)
        row_f2 = {
            "group": "ADDITIONS_22", "point_id": pid_f2, "tree": "F2", "driver_name": drv_f2_name,
            "driver_sha256": drivers_map[drv_f2_name], "env": env, "expected_class": exp_cls_f2,
            "expected_rc1": exp_rc1_f2, "expected_rc2": "0", "expected_run_rc": "0", "expected_hit": "1" if cs_val != "N/A_CONTROL" else "0",
            "expected_label": exp_cls_f2, "comparison_contract": exp_cls_f2, "expect_source": src,
            "callseq_status": cs_val, "k_source": "N/A_ADDITIONS", "status": "INFLUENCED"
        }
        row_f3 = {
            "group": "ADDITIONS_22", "point_id": pid_f3, "tree": "F3", "driver_name": drv_f3_name,
            "driver_sha256": drivers_map[drv_f3_name], "env": env, "expected_class": exp_cls_f3,
            "expected_rc1": exp_rc1_f3, "expected_rc2": "0", "expected_run_rc": "0", "expected_hit": "1" if cs_val != "N/A_CONTROL" else "0",
            "expected_label": exp_cls_f3, "comparison_contract": exp_cls_f3, "expect_source": src,
            "callseq_status": cs_val, "k_source": "N/A_ADDITIONS", "status": "INFLUENCED"
        }
        m1b_rows.extend([row_f2, row_f3])
        mapping_rows.append(("REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv", "ADDITIONS_22", pid_f2, "F2", src, cs_val, "N/A_ADDITIONS"))
        mapping_rows.append(("REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv", "ADDITIONS_22", pid_f3, "F3", src, cs_val, "N/A_ADDITIONS"))
        add22_f2 += 1; add22_f3 += 1
    counts_table.append(("M1b", "ADDITIONS_22", len(ADD22_SNAPSHOT), add22_f2, add22_f3, add22_ctrl, 0, "OK"))

    # Add S3R4 polygon (33 combos, REGISTRY_S3R4C2_C_POLY.tsv)
    poly_f2, poly_f3 = 0, 0
    for r in S3_POLY:
        combo = r["combo_id"]
        mode = r["mode"]
        ng = r["NG"]
        env = "FMM_MODE=%s;S4FMM_NG=%s" % (mode, ng)
        src = "%s:%d" % (r["_file"], r["_phys_line"])
        pid_f2 = "POLY-%s-F2" % combo
        pid_f3 = "POLY-%s-F3" % combo
        row_f2 = {
            "group": "POLY_33", "point_id": pid_f2, "tree": "F2", "driver_name": "poly-F2",
            "driver_sha256": drivers_map["poly-F2"], "env": env, "expected_class": "CONTROL_OK",
            "expected_rc1": "0", "expected_rc2": "0", "expected_run_rc": "0", "expected_hit": "0",
            "expected_label": "CONTROL_OK", "comparison_contract": "IDENTICAL", "expect_source": src,
            "callseq_status": "N/A_CONTROL", "k_source": "N/A_CONTROL", "status": "INFLUENCED"
        }
        row_f3 = {
            "group": "POLY_33", "point_id": pid_f3, "tree": "F3", "driver_name": "poly-F3",
            "driver_sha256": drivers_map["poly-F3"], "env": env, "expected_class": "CONTROL_OK",
            "expected_rc1": "0", "expected_rc2": "0", "expected_run_rc": "0", "expected_hit": "0",
            "expected_label": "CONTROL_OK", "comparison_contract": "IDENTICAL", "expect_source": src,
            "callseq_status": "N/A_CONTROL", "k_source": "N/A_CONTROL", "status": "INFLUENCED"
        }
        m1b_rows.extend([row_f2, row_f3])
        mapping_rows.append(("REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv", "POLY_33", pid_f2, "F2", src, "N/A_CONTROL", "N/A_CONTROL"))
        mapping_rows.append(("REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv", "POLY_33", pid_f3, "F3", src, "N/A_CONTROL", "N/A_CONTROL"))
        poly_f2 += 1; poly_f3 += 1
    counts_table.append(("M1b", "POLY_33", len(S3_POLY), poly_f2, poly_f3, poly_f2 + poly_f3, 0, "OK"))

    # ---------------- BUILD M1c ROWS ----------------
    m1c_rows = []

    # G5 (177 points from REGISTRY_S4_PRE_R7_M3.tsv)
    reg_m3_by_id = index_by(REG_M3, "point_id")
    res_state_by_id = index_by(M3_RES_STATE, "point_id")
    res_seam_by_id = index_by(M3_RES_SEAM, "point_id")

    g5_pids = sorted({r["point_id"] for r in REG_M3 if r.get("group") == "G5"})
    g6_pids = sorted({r["point_id"] for r in REG_M3 if r.get("group") == "G6"})
    g6c_pids = sorted({r["point_id"] for r in REG_M3 if r.get("group") == "G6c"})

    if len(g5_pids) != 177: stop("M1c", "G5", "expected 177 points, got %d" % len(g5_pids))
    if len(g6_pids) != 25: stop("M1c", "G6", "expected 25 points, got %d" % len(g6_pids))
    if len(g6c_pids) != 18: stop("M1c", "G6c", "expected 18 points, got %d" % len(g6c_pids))

    # G5
    g5_f2, g5_f3 = 0, 0
    for pid in g5_pids:
        r_f2 = [r for r in reg_m3_by_id[pid] if r["tree"] == "F2"][0]
        st_rows = res_state_by_id.get(pid, [])
        if len(st_rows) < 2 or st_rows[0]["point_verdict"] != "HOLD" or st_rows[1]["point_verdict"] != "HOLD":
            stop("M1c_G5", pid, "F2 two-pass not HOLD")
            continue
        p1 = st_rows[0]
        # env derivation
        env_parts = ["FMM_MODE=" + r_f2["mode"], "S4FMM_NG=9", "S4FMM_INJECT=" + r_f2["request"]]
        if not r_f2["request"].startswith("plancall:") and p1.get("NTH_or_K", "").startswith("NTH="):
            env_parts.append("S4FMM_NTH=" + p1["NTH_or_K"].split("=")[1])
        if r_f2.get("route") == "twice":
            env_parts.append("S4FMM_TWICE=slab")
        env = ";".join(env_parts)

        src = "%s:%d" % (r_f2["_file"], r_f2["_phys_line"])
        cs = "IDENTICAL"
        ks = k_58_lookup.get(pid) or k_119_lookup.get(pid) or "K_FROM_HISTORY_AGREED"
        exp_cls = "HOLD"
        exp_verdict = "HOLD(all applicable)"
        invariants = r_f2["applicable_invariants"]

        drv_f2_name = "r6bstate-F2-dbg"
        drv_f3_name = "r6bstate-F3-dbg"
        f3_pid = pid + "-F3"

        row_f2 = {
            "group": "G5", "point_id": pid, "tree": "F2", "driver_name": drv_f2_name,
            "driver_sha256": drivers_map[drv_f2_name], "env": env, "expected_class": exp_cls,
            "expected_rc1": "0", "expected_rc2": "0", "expected_run_rc": "0", "expected_hit": "1",
            "applicable_invariants": invariants, "expected_verdict": exp_verdict, "expect_source": src,
            "callseq_status": cs, "k_source": ks, "status": "INFLUENCED"
        }
        row_f3 = {
            "group": "G5", "point_id": f3_pid, "tree": "F3", "driver_name": drv_f3_name,
            "driver_sha256": drivers_map[drv_f3_name], "env": env, "expected_class": exp_cls,
            "expected_rc1": "0", "expected_rc2": "0", "expected_run_rc": "0", "expected_hit": "1",
            "applicable_invariants": invariants, "expected_verdict": exp_verdict, "expect_source": src,
            "callseq_status": cs, "k_source": ks, "status": "INFLUENCED"
        }
        m1c_rows.extend([row_f2, row_f3])
        mapping_rows.append(("REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv", "G5", pid, "F2", src, cs, ks))
        mapping_rows.append(("REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv", "G5", f3_pid, "F3", src, cs, ks))
        g5_f2 += 1; g5_f3 += 1
    counts_table.append(("M1c", "G5", len(g5_pids), g5_f2, g5_f3, 0, 0, "OK"))

    # G6
    g6_f2, g6_f3 = 0, 0
    for pid in g6_pids:
        r_f2 = [r for r in reg_m3_by_id[pid] if r["tree"] == "F2"][0]
        st_rows = res_seam_by_id.get(pid, [])
        if len(st_rows) < 2 or st_rows[0]["point_verdict"] != "HOLD" or st_rows[1]["point_verdict"] != "HOLD":
            stop("M1c_G6", pid, "F2 two-pass not HOLD")
            continue
        p1 = st_rows[0]
        env = "FMM_MODE=%s;S4FMM_NG=9;S4FMM_INJECT=%s" % (r_f2["mode"], r_f2["request"])
        src = "%s:%d" % (r_f2["_file"], r_f2["_phys_line"])
        cs = "IDENTICAL"
        ks = "N/A_SEAM"
        exp_cls = "HOLD"
        exp_verdict = "HOLD(all applicable)"
        invariants = r_f2["applicable_invariants"]

        lib = r_f2.get("library", "")
        if "fmmret" in lib or r_f2["request"].startswith("fmmret:"):
            drv_f2_name = "r6bseam-fmmret-F2"; drv_f3_name = "r6bseam-fmmret-F3"
        else:
            drv_f2_name = "r6bseam-seamF-F2"; drv_f3_name = "r6bseam-seamF-F3"

        f3_pid = pid + "-F3"
        row_f2 = {
            "group": "G6", "point_id": pid, "tree": "F2", "driver_name": drv_f2_name,
            "driver_sha256": drivers_map[drv_f2_name], "env": env, "expected_class": exp_cls,
            "expected_rc1": "0", "expected_rc2": "0", "expected_run_rc": "0", "expected_hit": "1",
            "applicable_invariants": invariants, "expected_verdict": exp_verdict, "expect_source": src,
            "callseq_status": cs, "k_source": ks, "status": "INFLUENCED"
        }
        row_f3 = {
            "group": "G6", "point_id": f3_pid, "tree": "F3", "driver_name": drv_f3_name,
            "driver_sha256": drivers_map[drv_f3_name], "env": env, "expected_class": exp_cls,
            "expected_rc1": "0", "expected_rc2": "0", "expected_run_rc": "0", "expected_hit": "1",
            "applicable_invariants": invariants, "expected_verdict": exp_verdict, "expect_source": src,
            "callseq_status": cs, "k_source": ks, "status": "INFLUENCED"
        }
        m1c_rows.extend([row_f2, row_f3])
        mapping_rows.append(("REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv", "G6", pid, "F2", src, cs, ks))
        mapping_rows.append(("REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv", "G6", f3_pid, "F3", src, cs, ks))
        g6_f2 += 1; g6_f3 += 1
    counts_table.append(("M1c", "G6", len(g6_pids), g6_f2, g6_f3, 0, 0, "OK"))

    # G6c (18 controls)
    g6c_f2, g6c_f3 = 0, 0
    m3_seam_p1_by_id = {r["id"]: r for r in M3_SEAM_P1 if r.get("kind") == "control"}
    m3_seam_p2_by_id = {r["id"]: r for r in M3_SEAM_P2 if r.get("kind") == "control"}

    for pid in g6c_pids:
        r_f2 = [r for r in reg_m3_by_id[pid] if r["tree"] == "F2"][0]
        s1 = m3_seam_p1_by_id.get(pid)
        s2 = m3_seam_p2_by_id.get(pid)
        if not s1 or not s2:
            stop("M1c_G6c", pid, "missing from STATE_SEAM passes")
            continue
        if s1["nogdb_rc1"] != s2["nogdb_rc1"] or s1["status"] != "OK" or s2["status"] != "OK":
            stop("M1c_G6c", pid, "STATE_SEAM two-pass disagree")
            continue
        env = "FMM_MODE=%s;S4FMM_NG=9" % r_f2["mode"]
        src = "%s:%d" % (r_f2["_file"], r_f2["_phys_line"])
        cs = "N/A_CONTROL"
        ks = "N/A_CONTROL"
        exp_cls = "CONTROL_OK"
        exp_verdict = "CONTROL_OK_EXPECTED"
        invariants = "control"

        lib = r_f2.get("library", "")
        if "fmmret" in lib or "fmmret" in pid:
            drv_f2_name = "r6bseam-fmmret-F2"; drv_f3_name = "r6bseam-fmmret-F3"
        else:
            drv_f2_name = "r6bseam-seamF-F2"; drv_f3_name = "r6bseam-seamF-F3"

        f3_pid = pid + "-F3"
        row_f2 = {
            "group": "G6c", "point_id": pid, "tree": "F2", "driver_name": drv_f2_name,
            "driver_sha256": drivers_map[drv_f2_name], "env": env, "expected_class": exp_cls,
            "expected_rc1": "0", "expected_rc2": "0", "expected_run_rc": "0", "expected_hit": "0",
            "applicable_invariants": invariants, "expected_verdict": exp_verdict, "expect_source": src,
            "callseq_status": cs, "k_source": ks, "status": "INFLUENCED"
        }
        row_f3 = {
            "group": "G6c", "point_id": f3_pid, "tree": "F3", "driver_name": drv_f3_name,
            "driver_sha256": drivers_map[drv_f3_name], "env": env, "expected_class": exp_cls,
            "expected_rc1": "0", "expected_rc2": "0", "expected_run_rc": "0", "expected_hit": "0",
            "applicable_invariants": invariants, "expected_verdict": exp_verdict, "expect_source": src,
            "callseq_status": cs, "k_source": ks, "status": "INFLUENCED"
        }
        m1c_rows.extend([row_f2, row_f3])
        mapping_rows.append(("REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv", "G6c", pid, "F2", src, cs, ks))
        mapping_rows.append(("REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv", "G6c", f3_pid, "F3", src, cs, ks))
        g6c_f2 += 1; g6c_f3 += 1
    counts_table.append(("M1c", "G6c", len(g6c_pids), g6c_f2, g6c_f3, g6c_f2 + g6c_f3, 0, "OK"))

    # ---------------- INTEGRITY VERIFICATIONS BEFORE WRITING ----------------
    # Check key uniqueness in M1b
    m1b_keys = [(r["group"], r["point_id"], r["tree"]) for r in m1b_rows]
    seen_b = set()
    dups_b = []
    for k in m1b_keys:
        if k in seen_b:
            dups_b.append(k)
        seen_b.add(k)
    if dups_b:
        stop("INTEGRITY", "M1b", "duplicate (group, point_id, tree) in M1b: %s" % dups_b[:5])

    # Check key uniqueness in M1c
    m1c_keys = [(r["group"], r["point_id"], r["tree"]) for r in m1c_rows]
    seen_c = set()
    dups_c = []
    for k in m1c_keys:
        if k in seen_c:
            dups_c.append(k)
        seen_c.add(k)
    if dups_c:
        stop("INTEGRITY", "M1c", "duplicate (group, point_id, tree) in M1c: %s" % dups_c[:5])

    # Check drivers exist for every row
    for r in m1b_rows:
        if not r["driver_sha256"] or len(r["driver_sha256"]) != 64:
            stop("DRIVER", r["point_id"], "invalid driver sha256: " + r["driver_name"])
    for r in m1c_rows:
        if not r["driver_sha256"] or len(r["driver_sha256"]) != 64:
            stop("DRIVER", r["point_id"], "invalid driver sha256: " + r["driver_name"])

    # If any stops recorded, output only PREREG_STOP table and exit
    os.makedirs(EV, exist_ok=True)
    stop_path = os.path.join(EV, "PREREG_STOP_R8_M1a6.tsv")
    with open(stop_path, "w", encoding="utf-8") as fh:
        fh.write("stage\titem\treason\n")
        for st, it, rs in STOPS:
            fh.write("%s\t%s\t%s\n" % (st, it, rs))

    if STOPS:
        print("make_prereg_r8m1a6: STOPPED with %d errors (see %s)" % (len(STOPS), stop_path))
        return

    # ---------------- WRITE OUTPUTS EXCLUSIVELY ----------------
    out_files = {
        "m1b": os.path.join(EV, "REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv"),
        "m1c": os.path.join(EV, "REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv"),
        "inputs": os.path.join(EV, "PREREG_INPUTS_R8_M1a6.tsv"),
        "counts": os.path.join(EV, "PREREG_COUNTS_R8_M1a6.tsv"),
        "k58": os.path.join(EV, "K_SOURCE_PLANCALL58_R8_M1a6.tsv"),
        "map": os.path.join(EV, "PREREG_ROW_SOURCES_MAPPING_R8_M1a6.tsv")
    }

    for p in out_files.values():
        if os.path.exists(p):
            sys.exit("make_prereg_r8m1a6: output file exists (U17): " + p)

    # 1. Write M1b
    m1b_headers = ["group", "point_id", "tree", "driver_name", "driver_sha256", "env",
                   "expected_class", "expected_rc1", "expected_rc2", "expected_run_rc",
                   "expected_hit", "expected_label", "comparison_contract", "expect_source",
                   "callseq_status", "k_source", "status"]
    with open(out_files["m1b"], "w", encoding="utf-8") as fh:
        fh.write("\t".join(m1b_headers) + "\n")
        for r in m1b_rows:
            fh.write("\t".join(str(r[h]) for h in m1b_headers) + "\n")

    # 2. Write M1c
    m1c_headers = ["group", "point_id", "tree", "driver_name", "driver_sha256", "env",
                   "expected_class", "expected_rc1", "expected_rc2", "expected_run_rc",
                   "expected_hit", "applicable_invariants", "expected_verdict", "expect_source",
                   "callseq_status", "k_source", "status"]
    with open(out_files["m1c"], "w", encoding="utf-8") as fh:
        fh.write("\t".join(m1c_headers) + "\n")
        for r in m1c_rows:
            fh.write("\t".join(str(r[h]) for h in m1c_headers) + "\n")

    # 3. Write Inputs
    with open(out_files["inputs"], "w", encoding="utf-8") as fh:
        fh.write("label\tpath\tsha256\tsource_status\n")
        for lab, pth, s, st in INPUTS:
            fh.write("%s\t%s\t%s\t%s\n" % (lab, pth, s, st))

    # 4. Write Counts
    with open(out_files["counts"], "w", encoding="utf-8") as fh:
        fh.write("target_registry\tgroup\torig_points\tf2_rows\tf3_rows\tcontrol_or_not_run_rows\tdup_or_missing_rows\tstatus\n")
        for trg, grp, orig, f2, f3, c_nr, dm, st in counts_table:
            fh.write("%s\t%s\t%d\t%d\t%d\t%d\t%d\t%s\n" % (trg, grp, orig, f2, f3, c_nr, dm, st))

    # 5. Write K Source 58
    with open(out_files["k58"], "w", encoding="utf-8") as fh:
        fh.write("point_id\tk_status\tK\tM\trequest\tstate_pass1\tstate_pass2\n")
        for pid, st, k, m, want, a, b in k_src_58_rows:
            fh.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (pid, st, k, m, want, a, b))

    # 6. Write Row Sources Mapping
    with open(out_files["map"], "w", encoding="utf-8") as fh:
        fh.write("target_registry\tgroup\tpoint_id\ttree\texpect_source\tcallseq_status\tk_source\n")
        for trg, grp, pid, tree, src, cs, ks in mapping_rows:
            fh.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (trg, grp, pid, tree, src, cs, ks))

    print("make_prereg_r8m1a6: SUCCESS: M1b rows=%d, M1c rows=%d, counts=%d groups, inputs=%d, k58=%d" % (
        len(m1b_rows), len(m1c_rows), len(counts_table), len(INPUTS), len(k_src_58_rows)))

if __name__ == "__main__":
    main()
