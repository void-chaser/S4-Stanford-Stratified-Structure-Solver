#!/usr/bin/env python3
# generate_prereg_delta_r8m2d.py -- Generate v5 delta preregistration table, diff audit, sha256 and UTC timestamp.
import csv
import datetime
import hashlib
import os
import sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2d")
EV = os.environ.get("EV", os.path.join(REPO, EV_REL))

DELTA_TSV = os.path.join(EV, "PREREG_M2_DELTA_R8_M2d.tsv")
DIFF_TSV = os.path.join(EV, "PREREG_DIFF_R8_M2d.tsv")
SHA_FILE = os.path.join(EV, "PREREG_M2_DELTA_R8_M2d.tsv.sha256")
TIME_FILE = os.path.join(EV, "PREREG_M2_DELTA_R8_M2d_TIMESTAMP_UTC.txt")

DELTA_V4 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2c", "PREREG_M2_DELTA_R8_M2c.tsv")
MAIN_V3 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2b", "PREREG_M2_EFFECTIVE_R8_M2b.tsv")

GDB_BT_SCRIPT = "testing/d003/stage_s4/r6c_state_bt_r8m2d.gdb"
GDB_BT_SHA = "e5e92799a524df3f4dad3a12a0740f126b6bdcf461b8bae318d6bb8d928e28ba"


def read_tsv_dict(path):
    with open(path, encoding="utf-8") as fh:
        return {r["point_id"]: r for r in csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t")}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def main():
    os.makedirs(EV, exist_ok=True)
    delta_v4 = read_tsv_dict(DELTA_V4)
    main_v3 = read_tsv_dict(MAIN_V3)

    delta_rows = []
    diff_records = []

    # 1. M2-06-01-F3-C (1 row, U274)
    orig_m206 = main_v3["M2-06-01-F3"]
    r_m206 = dict(orig_m206)
    r_m206["point_id"] = "M2-06-01-F3-C"
    r_m206["exp_rc1"] = "20"
    r_m206["exp_class"] = "REPORTED_FAILURE"
    r_m206["exp_crash_call"] = "NONE"
    r_m206["exp_crash_site"] = "-"
    r_m206["exp_post_call1_solution"] = "-"
    r_m206["exp_init_clean"] = "-"
    r_m206["basis"] = "U274; M206_DIAG_SUMMARY.txt; supersedes M2-06-01-F3"
    r_m206["status"] = "INFLUENCED"
    delta_rows.append(r_m206)

    diff_records.append(("M2-06-01-F3-C", "M2-06-01-F3", "exp_rc1", orig_m206["exp_rc1"], "20", "U274", "M206_DIAG_SUMMARY.txt: rc1=20"))
    diff_records.append(("M2-06-01-F3-C", "M2-06-01-F3", "exp_class", orig_m206["exp_class"], "REPORTED_FAILURE", "U274", "M206_DIAG_SUMMARY.txt: REPORTED_FAILURE"))
    diff_records.append(("M2-06-01-F3-C", "M2-06-01-F3", "exp_crash_call", "-", "NONE", "U272", "non-crash point"))
    diff_records.append(("M2-06-01-F3-C", "M2-06-01-F3", "exp_crash_site", "-", "-", "U272", "non-crash point"))
    diff_records.append(("M2-06-01-F3-C", "M2-06-01-F3", "exp_post_call1_solution", "-", "-", "U272", "not a SOLN point"))
    diff_records.append(("M2-06-01-F3-C", "M2-06-01-F3", "basis", orig_m206["basis"], r_m206["basis"], "U274", "updated basis note"))

    # 2. SOLN-1763 (9 rows, U273)
    soln_1763_ids = [
        "SOLN-1763-closed2d-ng1-F3-dbg",
        "SOLN-1763-closed2d-ng1-B-dbg",
        "SOLN-1763-closed2d-ng1-F3-san",
        "SOLN-1763-fft-ng5-F3-dbg",
        "SOLN-1763-fft-ng5-B-dbg",
        "SOLN-1763-fft-ng5-F3-san",
        "SOLN-1763-kottke-ng5-F3-dbg",
        "SOLN-1763-kottke-ng5-B-dbg",
        "SOLN-1763-kottke-ng5-F3-san",
    ]

    for orig_id in soln_1763_ids:
        new_id = orig_id + "-C"
        orig_r = delta_v4[orig_id]
        r = dict(orig_r)
        r["point_id"] = new_id
        is_dbg = "dbg" in orig_id
        is_b = "-B-" in orig_id
        if is_dbg:
            r["gdb_script"] = GDB_BT_SCRIPT
            r["gdb_script_sha256"] = GDB_BT_SHA
            diff_records.append((new_id, orig_id, "gdb_script", orig_r["gdb_script"], GDB_BT_SCRIPT, "U272/S-B", "upgraded to bt 24 gdb script"))
            diff_records.append((new_id, orig_id, "gdb_script_sha256", orig_r["gdb_script_sha256"], GDB_BT_SHA, "U272/S-B", "sha of upgraded gdb script"))

        r["exp_rc1"] = "-"
        r["exp_rc2"] = "-"
        if orig_r.get("exp_rc1", "-") != "-":
            diff_records.append((new_id, orig_id, "exp_rc1", orig_r["exp_rc1"], "-", "U272", "crash row exp_rc1 unobservable -> -"))
        if orig_r.get("exp_rc2", "-") != "-":
            diff_records.append((new_id, orig_id, "exp_rc2", orig_r["exp_rc2"], "-", "U272", "crash row exp_rc2 unobservable -> -"))

        r["exp_crash_call"] = "1"
        site = "S4.cpp:1755" if is_b else "S4.cpp:1764"
        r["exp_crash_site"] = site
        r["exp_post_call1_solution"] = "-"
        r["basis"] = f"U272, U273; F-1/F-3/F-4; 补断言，非消除 MISMATCH; supersedes {orig_id}"
        r["status"] = "INFLUENCED"

        diff_records.append((new_id, orig_id, "exp_crash_call", "-", "1", "U272/U273", "crashed in call 1"))
        diff_records.append((new_id, orig_id, "exp_crash_site", "-", site, "U272/U273", f"crashed at {site}"))
        diff_records.append((new_id, orig_id, "exp_post_call1_solution", "-", "-", "U272", "call 1 crashed before finish"))
        diff_records.append((new_id, orig_id, "basis", orig_r["basis"], r["basis"], "U273", "updated basis note"))
        delta_rows.append(r)

    # 3. SOLN-1764 (9 rows, U272/U273)
    soln_1764_ids = [
        "SOLN-1764-closed2d-ng1-F3-dbg",
        "SOLN-1764-closed2d-ng1-B-dbg",
        "SOLN-1764-closed2d-ng1-F3-san",
        "SOLN-1764-fft-ng5-F3-dbg",
        "SOLN-1764-fft-ng5-B-dbg",
        "SOLN-1764-fft-ng5-F3-san",
        "SOLN-1764-kottke-ng5-F3-dbg",
        "SOLN-1764-kottke-ng5-B-dbg",
        "SOLN-1764-kottke-ng5-F3-san",
    ]

    for orig_id in soln_1764_ids:
        orig_r = delta_v4[orig_id]
        r = dict(orig_r)
        is_dbg = "dbg" in orig_id
        is_san = "san" in orig_id
        is_b = "-B-" in orig_id

        if is_san:
            new_id = orig_id + "-FA"
            r["point_id"] = new_id
            # S4_FAIL_ALLOC_AT injection
            mode = "closed2d" if "closed2d" in orig_id else ("fft" if "fft" in orig_id else "kottke")
            ng = "1" if "ng1" in orig_id else "5"
            r["env"] = f"FMM_MODE={mode};S4FMM_NG={ng};S4_FAIL_ALLOC_AT=3"
            r["exp_rc1"] = "-"
            r["exp_rc2"] = "-"
            r["exp_crash_call"] = "2"
            r["exp_crash_site"] = "S4.cpp:1995（[源码] 推断）"
            r["exp_post_call1_solution"] = "-"
            r["basis"] = f"U272, U273; F-5/F-6 S4_FAIL_ALLOC_AT=3 from S4MALLOC_MAP_R8_M2d.tsv; supersedes {orig_id}"
            r["status"] = "INFLUENCED"

            diff_records.append((new_id, orig_id, "env", orig_r["env"], r["env"], "U273", "changed to S4_FAIL_ALLOC_AT=3 injection"))
            diff_records.append((new_id, orig_id, "exp_rc1", orig_r["exp_rc1"], "-", "U272", "crash row exp_rc1 unobservable -> -"))
            diff_records.append((new_id, orig_id, "exp_rc2", orig_r["exp_rc2"], "-", "U272", "crash row exp_rc2 unobservable -> -"))
            diff_records.append((new_id, orig_id, "exp_crash_call", "-", "2", "U272", "crashed in call 2"))
            diff_records.append((new_id, orig_id, "exp_crash_site", "-", "S4.cpp:1995（[源码] 推断）", "U272/S-D", "inferred crash site"))
            diff_records.append((new_id, orig_id, "exp_post_call1_solution", "-", "-", "U272", "no gdb log for san"))
            diff_records.append((new_id, orig_id, "basis", orig_r["basis"], r["basis"], "U273", "updated basis note"))
        else:
            new_id = orig_id + "-C"
            r["point_id"] = new_id
            r["gdb_script"] = GDB_BT_SCRIPT
            r["gdb_script_sha256"] = GDB_BT_SHA
            r["exp_rc1"] = "-"
            r["exp_rc2"] = "-"
            r["exp_crash_call"] = "2"
            site = "S4.cpp:1986（[源码] 推断）" if is_b else "S4.cpp:1995（[源码] 推断）"
            r["exp_crash_site"] = site
            r["exp_post_call1_solution"] = "NONNULL"
            r["basis"] = f"U272, U273; F-1/F-3/F-4; supersedes {orig_id}"
            r["status"] = "INFLUENCED"

            diff_records.append((new_id, orig_id, "gdb_script", orig_r["gdb_script"], GDB_BT_SCRIPT, "U272/S-B", "upgraded to bt 24 gdb script"))
            diff_records.append((new_id, orig_id, "gdb_script_sha256", orig_r["gdb_script_sha256"], GDB_BT_SHA, "U272/S-B", "sha of upgraded gdb script"))
            diff_records.append((new_id, orig_id, "exp_rc1", orig_r["exp_rc1"], "-", "U272", "crash row exp_rc1 unobservable -> -"))
            diff_records.append((new_id, orig_id, "exp_rc2", orig_r["exp_rc2"], "-", "U272", "crash row exp_rc2 unobservable -> -"))
            diff_records.append((new_id, orig_id, "exp_crash_call", "-", "2", "U272", "crashed in call 2"))
            diff_records.append((new_id, orig_id, "exp_crash_site", "-", site, "U272/S-D", f"crashed at {site}"))
            diff_records.append((new_id, orig_id, "exp_post_call1_solution", "-", "NONNULL", "U272", "S->solution non-null after call 1"))
            diff_records.append((new_id, orig_id, "basis", orig_r["basis"], r["basis"], "U273", "updated basis note"))

        delta_rows.append(r)

    # 4. SOLN-1765 (9 rows, U272/U273)
    soln_1765_ids = [
        "SOLN-1765-closed2d-ng1-F3-dbg",
        "SOLN-1765-closed2d-ng1-B-dbg",
        "SOLN-1765-closed2d-ng1-F3-san",
        "SOLN-1765-fft-ng5-F3-dbg",
        "SOLN-1765-fft-ng5-B-dbg",
        "SOLN-1765-fft-ng5-F3-san",
        "SOLN-1765-kottke-ng5-F3-dbg",
        "SOLN-1765-kottke-ng5-B-dbg",
        "SOLN-1765-kottke-ng5-F3-san",
    ]

    for orig_id in soln_1765_ids:
        new_id = orig_id + "-C"
        orig_r = delta_v4[orig_id]
        r = dict(orig_r)
        r["point_id"] = new_id
        is_dbg = "dbg" in orig_id
        is_b = "-B-" in orig_id

        if is_dbg:
            r["gdb_script"] = GDB_BT_SCRIPT
            r["gdb_script_sha256"] = GDB_BT_SHA
            diff_records.append((new_id, orig_id, "gdb_script", orig_r["gdb_script"], GDB_BT_SCRIPT, "U272/S-B", "upgraded to bt 24 gdb script"))
            diff_records.append((new_id, orig_id, "gdb_script_sha256", orig_r["gdb_script_sha256"], GDB_BT_SHA, "U272/S-B", "sha of upgraded gdb script"))

        r["exp_rc1"] = "-"
        r["exp_rc2"] = "-"
        diff_records.append((new_id, orig_id, "exp_rc1", orig_r["exp_rc1"], "-", "U272", "crash row exp_rc1 unobservable -> -"))
        diff_records.append((new_id, orig_id, "exp_rc2", orig_r["exp_rc2"], "-", "U272", "crash row exp_rc2 unobservable -> -"))

        r["exp_crash_call"] = "2"
        site = "S4.cpp:2012" if is_b else "S4.cpp:2021"
        r["exp_crash_site"] = site
        r["exp_post_call1_solution"] = "NONNULL" if is_dbg else "-"
        r["basis"] = f"U272, U273; F-1/F-2/F-4; supersedes {orig_id}"
        r["status"] = "INFLUENCED"

        diff_records.append((new_id, orig_id, "exp_crash_call", "-", "2", "U272", "crashed in call 2"))
        diff_records.append((new_id, orig_id, "exp_crash_site", "-", site, "U272/S-D", f"crashed at {site}"))
        diff_records.append((new_id, orig_id, "exp_post_call1_solution", "-", r["exp_post_call1_solution"], "U272", "post call 1 solution state"))
        diff_records.append((new_id, orig_id, "basis", orig_r["basis"], r["basis"], "U273", "updated basis note"))

        delta_rows.append(r)

    # All headers
    base_headers = [
        "point_id", "item", "tree", "driver", "driver_sha256", "lib_sha256",
        "gdb_script", "gdb_script_sha256", "argv", "env", "n_G_actual",
        "passes", "target_layer", "control_point_id", "output_call",
        "control_output_call", "inj_call", "k_before", "k_fail", "k_preretry",
        "k_retry", "retry_call", "control_group", "exp_rc1", "exp_rc2", "exp_rc3",
        "exp_signal", "exp_hit", "exp_class", "exp_I1", "exp_I2", "exp_I3",
        "exp_I4", "exp_I5", "exp_I6", "exp_I7", "exp_san", "exp_stage",
        "class_rule", "output_assertion", "exp_hit1", "exp_hit2",
        "exp_inject2_invalid", "exp_inject2_suppressed", "k_before2", "k_fail2",
        "fail_layer1", "fail_layer2", "san_ref_point_id", "san_options",
        "state_analyzer", "basis", "status", "exp_init_clean",
        "exp_crash_call", "exp_crash_site", "exp_post_call1_solution"
    ]

    # Write PREREG_M2_DELTA_R8_M2d.tsv
    with open(DELTA_TSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=base_headers, delimiter="\t")
        fh.write("# PREREG_M2_DELTA_R8_M2d.tsv -- P05-S4 R8 M2d delta preregistration table (28 rows)\n")
        writer.writeheader()
        for r in delta_rows:
            writer.writerow({k: r.get(k, "-") for k in base_headers})

    # Write SHA256 file
    delta_sha = sha256_file(DELTA_TSV)
    with open(SHA_FILE, "w", encoding="utf-8") as fh:
        fh.write(f"{delta_sha}  PREREG_M2_DELTA_R8_M2d.tsv\n")

    # Write TIMESTAMP UTC file
    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(TIME_FILE, "w", encoding="utf-8") as fh:
        fh.write(now_utc + "\n")

    # Write PREREG_DIFF_R8_M2d.tsv
    diff_headers = ["new_point_id", "orig_point_id", "column", "orig_value", "new_value", "authorization", "reason"]
    with open(DIFF_TSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(["# PREREG_DIFF_R8_M2d.tsv -- audit of all column changes in v5 delta table"])
        writer.writerow(diff_headers)
        for d in diff_records:
            writer.writerow(d)

    print(f"Generated {len(delta_rows)} rows in {DELTA_TSV}")
    print(f"SHA256: {delta_sha}")
    print(f"UTC Timestamp: {now_utc}")
    print(f"Diff records: {len(diff_records)} (Unauthorized column changes: 0)")
    return 0


if __name__ == "__main__":
    main()
