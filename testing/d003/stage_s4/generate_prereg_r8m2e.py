#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2e; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# generate_prereg_r8m2e.py -- Generate and freeze PREREG_M2_DELTA_R8_M2e.tsv and PREREG_EFFECTIVE_FORMAL_R8_M2e.tsv (S-E).
import datetime, hashlib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2e")
EV = os.path.join(REPO, EV_REL)

M2D_DELTA = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2d", "PREREG_M2_DELTA_R8_M2d.tsv")
OUT_DELTA = os.path.join(EV, "PREREG_M2_DELTA_R8_M2e.tsv")
OUT_DELTA_SHA = os.path.join(EV, "PREREG_M2_DELTA_R8_M2e.tsv.sha256")
OUT_DELTA_TIME = os.path.join(EV, "PREREG_M2_DELTA_R8_M2e_TIMESTAMP_UTC.txt")

OUT_FORMAL = os.path.join(EV, "PREREG_EFFECTIVE_FORMAL_R8_M2e.tsv")
OUT_FORMAL_SHA = os.path.join(EV, "PREREG_EFFECTIVE_FORMAL_R8_M2e.tsv.sha256")
OUT_FORMAL_TIME = os.path.join(EV, "PREREG_EFFECTIVE_FORMAL_R8_M2e_TIMESTAMP_UTC.txt")

DRV_SHA_AL = "90f4445330773c13c569bd15a0e1fd5cfa5a735070d4442523bed2b1636841b3"
LIB_SHA_SAN = "2775b9b2c279f51f1be0594c6ea9f635c96e3ba37e9d1638174fa380b45a6986"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    if not os.path.isfile(M2D_DELTA):
        sys.stderr.write("REFUSED: M2d delta prereg not found: %s\n" % M2D_DELTA)
        return 2

    with open(M2D_DELTA, "r", encoding="utf-8") as fh:
        m2d_lines = fh.read().splitlines()

    comment_line = m2d_lines[0]
    header_line = m2d_lines[1]
    headers = header_line.split("\t")
    data_lines_d = m2d_lines[2:]

    # Separate 25 non-FA lines and 3 FA lines
    v5_25_lines = []
    fa_lines = []
    for line in data_lines_d:
        if not line.strip():
            continue
        pid = line.split("\t")[0]
        if pid.endswith("-san-FA"):
            fa_lines.append(line)
        else:
            v5_25_lines.append(line)

    if len(v5_25_lines) != 25:
        sys.stderr.write("ERROR: Expected 25 non-FA lines, found %d\n" % len(v5_25_lines))
        return 2
    if len(fa_lines) != 3:
        sys.stderr.write("ERROR: Expected 3 FA lines, found %d\n" % len(fa_lines))
        return 2

    # Define the 3 v6 AL rows
    v6_combos = [
        ("closed2d-ng1", "closed2d", "1", 3),
        ("fft-ng5", "fft", "5", 3),
        ("kottke-ng5", "kottke", "5", 3),
    ]

    v6_rows = []
    for cname, mode, ng, k_fail in v6_combos:
        pid = "SOLN-1764-%s-F3-san-AL" % cname
        row = {
            "point_id": pid,
            "item": "SOLN-1764",
            "tree": "F3",
            "driver": "init-F3-san-AL",
            "driver_sha256": DRV_SHA_AL,
            "lib_sha256": LIB_SHA_SAN,
            "gdb_script": "-",
            "gdb_script_sha256": "-",
            "argv": "pattern both 4 3",
            "env": "FMM_MODE=%s;S4FMM_NG=%s;S4FMM_INJECT=aligned:%d" % (mode, ng, k_fail),
            "n_G_actual": ng,
            "passes": "2",
            "target_layer": "1",
            "control_point_id": "-",
            "output_call": "2",
            "control_output_call": "2",
            "inj_call": "1",
            "k_before": "0",
            "k_fail": str(k_fail),
            "k_preretry": "2",
            "k_retry": "3",
            "retry_call": "2",
            "control_group": "NO",
            "exp_rc1": "-",
            "exp_rc2": "-",
            "exp_rc3": "-",
            "exp_signal": "0",
            "exp_hit": "1",
            "exp_class": "SAN_CRASH",
            "exp_I1": "-",
            "exp_I2": "-",
            "exp_I3": "-",
            "exp_I4": "-",
            "exp_I5": "-",
            "exp_I6": "-",
            "exp_I7": "-",
            "exp_san": "1",
            "exp_stage": "-",
            "class_rule": "JUDGE_D003",
            "output_assertion": "NONE",
            "exp_hit1": "-",
            "exp_hit2": "-",
            "exp_inject2_invalid": "-",
            "exp_inject2_suppressed": "-",
            "k_before2": "-",
            "k_fail2": "-",
            "fail_layer1": "-",
            "fail_layer2": "-",
            "san_ref_point_id": "-",
            "san_options": "ASAN_OPTIONS=detect_leaks=0:abort_on_error=0:log_path=$EV/run/pass{pass}/{point_id}/asan.log;UBSAN_OPTIONS=abort_on_error=0:log_path=$EV/run/pass{pass}/{point_id}/ubsan.log",
            "state_analyzer": "-",
            "basis": "U277, U278, U279; G-3, G-8; ALIGNED_MAP_R8_M2e.tsv:k=%d; test_noinj_control_r8m2e.txt; generate_aligned_map_r8m2e.txt; supersedes SOLN-1764-%s-F3-san-FA" % (k_fail, cname),
            "status": "INFLUENCED",
            "exp_init_clean": "-",
            "exp_crash_call": "2",
            "exp_crash_site": "S4.cpp:1995",
            "exp_post_call1_solution": "-",
        }
        v6_rows.append("\t".join(row[h] for h in headers))

    # 1. Write PREREG_M2_DELTA_R8_M2e.tsv (3 rows)
    delta_content = "# PREREG_M2_DELTA_R8_M2e.tsv -- P05-S4 R8 M2e delta preregistration table (3 rows)\n"
    delta_content += header_line + "\n"
    for r in v6_rows:
        delta_content += r + "\n"

    with open(OUT_DELTA, "w", encoding="utf-8") as fh:
        fh.write(delta_content)

    delta_sha = sha256_file(OUT_DELTA)
    with open(OUT_DELTA_SHA, "w", encoding="utf-8") as fh:
        fh.write("%s  PREREG_M2_DELTA_R8_M2e.tsv\n" % delta_sha)

    t_now = utc_now()
    with open(OUT_DELTA_TIME, "w", encoding="utf-8") as fh:
        fh.write(t_now + "\n")

    # 2. Write PREREG_EFFECTIVE_FORMAL_R8_M2e.tsv (28 rows: 25 v5 + 3 v6)
    # Order: same order as M2d, replacing the 3 -FA rows with the corresponding 3 -AL rows
    formal_rows = []
    idx_v6 = 0
    for line in data_lines_d:
        if not line.strip():
            continue
        pid = line.split("\t")[0]
        if pid.endswith("-san-FA"):
            formal_rows.append(v6_rows[idx_v6])
            idx_v6 += 1
        else:
            formal_rows.append(line)

    if len(formal_rows) != 28:
        sys.stderr.write("ERROR: Expected 28 formal rows, got %d\n" % len(formal_rows))
        return 2

    formal_content = "# PREREG_EFFECTIVE_FORMAL_R8_M2e.tsv -- P05-S4 R8 M2e formal effective preregistration table (28 rows)\n"
    formal_content += header_line + "\n"
    for r in formal_rows:
        formal_content += r + "\n"

    with open(OUT_FORMAL, "w", encoding="utf-8") as fh:
        fh.write(formal_content)

    formal_sha = sha256_file(OUT_FORMAL)
    with open(OUT_FORMAL_SHA, "w", encoding="utf-8") as fh:
        fh.write("%s  PREREG_EFFECTIVE_FORMAL_R8_M2e.tsv\n" % formal_sha)

    with open(OUT_FORMAL_TIME, "w", encoding="utf-8") as fh:
        fh.write(t_now + "\n")

    # Verification: check byte-for-byte consistency of the 25 rows
    non_v6_in_formal = [r for r in formal_rows if not r.split("\t")[0].endswith("-san-AL")]
    if non_v6_in_formal != v5_25_lines:
        sys.stderr.write("ERROR: 25 non-AL rows in formal table do not match v5 source lines byte-for-byte!\n")
        return 2

    print("generate_prereg_r8m2e: SUCCESS")
    print("  DELTA: %s (%s, 3 rows)" % (OUT_DELTA, delta_sha))
    print("  FORMAL: %s (%s, 28 rows, 25 byte-identical with v5)" % (OUT_FORMAL, formal_sha))
    return 0


if __name__ == "__main__":
    sys.exit(main())
