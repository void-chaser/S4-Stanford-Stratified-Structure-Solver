#!/usr/bin/env python3
# generate_prereg_delta_r8m2c.py -- Generate v4 delta preregistration table and diff audit.
import csv, datetime, hashlib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2c")
EV = os.path.join(REPO, EV_REL)

DELTA_TSV = os.path.join(EV, "PREREG_M2_DELTA_R8_M2c.tsv")
DIFF_TSV = os.path.join(EV, "PREREG_DIFF_R8_M2c.tsv")
SHA_FILE = os.path.join(EV, "PREREG_M2_DELTA_R8_M2c.tsv.sha256")
TIME_FILE = os.path.join(EV, "PREREG_M2_DELTA_R8_M2c_TIMESTAMP_UTC.txt")

MAIN_V3 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2b", "PREREG_M2_EFFECTIVE_R8_M2b.tsv")
SANREF_V3 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2b", "PREREG_M2_SANREF_R8_M2b.tsv")

def read_tsv_dict(path):
    with open(path, encoding="utf-8") as fh:
        return {r["point_id"]: r for r in csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t")}

def main():
    os.makedirs(EV, exist_ok=True)
    main_v3 = read_tsv_dict(MAIN_V3)
    sanref_v3 = read_tsv_dict(SANREF_V3)

    delta_rows = []
    diff_records = []

    # 1. G6-C (5 rows) & SANREF-G6-C (5 rows) (U262, F2)
    g6_map = {
        "M2-03-G6-01-F3": ("alloc:21:1", "fft", "9", "370"),
        "M2-03-G6-03-F3": ("linearsolve_null2:134:1", "closed1d", "9", "362"),
        "M2-03-G6-04-F3": ("kottke_alloc:31:1", "kottke", "9", "360"),
        "M2-03-G6-05-F3": ("alloc:25:1", "jones", "9", "358"),
        "M2-03-G6-06-F3": ("alloc:23:1", "fft", "9", "374"),
    }

    for orig_id, (inj, mode, ng, src_line) in sorted(g6_map.items()):
        new_id = orig_id + "-C"
        orig_row = main_v3[orig_id]
        r = dict(orig_row)
        r["point_id"] = new_id
        r["env"] = f"FMM_MODE={mode};S4FMM_INJECT={inj};S4FMM_NG={ng}"
        r["n_G_actual"] = ng
        san_ref_c = f"M2-03-SANREF-{orig_id[6:]}-C"
        r["san_ref_point_id"] = san_ref_c
        r["basis"] = f"U262; F2 correction from PREREG_M1C_FACTS_R8_M1c2.tsv:{src_line}; supersedes {orig_id}"
        r["status"] = "INFLUENCED"
        r["exp_init_clean"] = "-"
        delta_rows.append(r)

        diff_records.append((new_id, orig_id, "env", orig_row["env"], r["env"], "U262", f"PREREG_M1C_FACTS_R8_M1c2.tsv:{src_line}"))
        diff_records.append((new_id, orig_id, "n_G_actual", orig_row["n_G_actual"], r["n_G_actual"], "U262", f"PREREG_M1C_FACTS_R8_M1c2.tsv:{src_line}"))
        diff_records.append((new_id, orig_id, "san_ref_point_id", orig_row["san_ref_point_id"], r["san_ref_point_id"], "U262", "points to SANREF-C"))

        # Corresponding SANREF row
        orig_sanref_id = f"M2-03-SANREF-{orig_id[6:]}"
        orig_sanref_row = sanref_v3[orig_sanref_id]
        sr = dict(orig_sanref_row)
        sr["point_id"] = san_ref_c
        sr["env"] = f"FMM_MODE={mode};S4FMM_INJECT={inj};S4FMM_NG={ng}"
        sr["n_G_actual"] = ng
        sr["basis"] = f"U262; F2 non-sanitizer reference correction from PREREG_M1C_FACTS_R8_M1c2.tsv:{src_line}; supersedes {orig_sanref_id}"
        sr["status"] = "INFLUENCED"
        sr["exp_init_clean"] = "-"
        delta_rows.append(sr)

        diff_records.append((san_ref_c, orig_sanref_id, "env", orig_sanref_row["env"], sr["env"], "U262", f"PREREG_M1C_FACTS_R8_M1c2.tsv:{src_line}"))
        diff_records.append((san_ref_c, orig_sanref_id, "n_G_actual", orig_sanref_row["n_G_actual"], sr["n_G_actual"], "U262", f"PREREG_M1C_FACTS_R8_M1c2.tsv:{src_line}"))

    # 2. M2-01-01..06-C (6 rows) (U262, U268, F1, F6)
    for i in range(1, 7):
        orig_id = f"M2-01-0{i}-F3"
        new_id = orig_id + "-C"
        orig_row = main_v3[orig_id]
        r = dict(orig_row)
        r["point_id"] = new_id
        r["exp_rc1"] = "1"
        r["exp_I1"] = "N/A"
        r["exp_I2"] = "N/A"
        r["exp_init_clean"] = "HOLD"
        r["basis"] = f"U262, U268; F1 rc1=1 from ADDITIONS_MAPPING_22_R8_M1a6.tsv:{i+1}; U268 exp_I=N/A & INIT_CLEAN=HOLD; supersedes {orig_id}"
        r["status"] = "INFLUENCED"
        delta_rows.append(r)

        diff_records.append((new_id, orig_id, "exp_rc1", orig_row["exp_rc1"], r["exp_rc1"], "U262", f"ADDITIONS_MAPPING_22_R8_M1a6.tsv:{i+1}"))
        diff_records.append((new_id, orig_id, "exp_I1", orig_row["exp_I1"], r["exp_I1"], "U268", "U268 InitSolution failure no failing layer"))
        diff_records.append((new_id, orig_id, "exp_I2", orig_row["exp_I2"], r["exp_I2"], "U268", "U268 InitSolution failure no retained layer"))
        diff_records.append((new_id, orig_id, "exp_init_clean", "-", r["exp_init_clean"], "U268", "U268 INIT_CLEAN assertion"))

    # 3. M2-03-REP-INIT-01..03-C (3 rows) (U262, U268, F1)
    for i in range(1, 4):
        orig_id = f"M2-03-REP-INIT-0{i}-F3"
        new_id = orig_id + "-C"
        orig_row = main_v3[orig_id]
        r = dict(orig_row)
        r["point_id"] = new_id
        r["exp_rc1"] = "1"
        r["exp_I1"] = "N/A"
        r["exp_I2"] = "N/A"
        r["exp_init_clean"] = "HOLD"
        r["san_ref_point_id"] = f"M2-01-0{i}-F3-C"
        r["basis"] = f"U262, U268; F1 rc1=1 from ADDITIONS_MAPPING_22_R8_M1a6.tsv:{i+1}; san_ref=M2-01-0{i}-F3-C; supersedes {orig_id}"
        r["status"] = "INFLUENCED"
        delta_rows.append(r)

        diff_records.append((new_id, orig_id, "exp_rc1", orig_row["exp_rc1"], r["exp_rc1"], "U262", f"ADDITIONS_MAPPING_22_R8_M1a6.tsv:{i+1}"))
        diff_records.append((new_id, orig_id, "exp_I1", orig_row["exp_I1"], r["exp_I1"], "U268", "U268 InitSolution failure no failing layer"))
        diff_records.append((new_id, orig_id, "exp_I2", orig_row["exp_I2"], r["exp_I2"], "U268", "U268 InitSolution failure no retained layer"))
        diff_records.append((new_id, orig_id, "exp_init_clean", "-", r["exp_init_clean"], "U268", "U268 INIT_CLEAN assertion"))
        diff_records.append((new_id, orig_id, "san_ref_point_id", orig_row["san_ref_point_id"], r["san_ref_point_id"], "U262", f"M2-01-0{i}-F3-C"))

    # 4. M2-03-REP-INIT-04..06-C (3 rows) (U262, U266, U268, F5)
    rep_k_map = {
        4: ("5", "closed2d", "1"),
        5: ("6", "fft", "5"),
        6: ("6", "kottke", "5")
    }
    for i in (4, 5, 6):
        orig_id = f"M2-03-REP-INIT-0{i}-F3"
        new_id = orig_id + "-C"
        orig_row = main_v3[orig_id]
        r = dict(orig_row)
        new_k, mode, ng = rep_k_map[i]
        r["point_id"] = new_id
        r["k_fail"] = new_k
        r["env"] = f"FMM_MODE={mode};S4FMM_NG={ng};S4FMM_INJECT=init:{new_k}"
        r["exp_rc1"] = "1"
        r["exp_I1"] = "N/A"
        r["exp_I2"] = "N/A"
        r["exp_init_clean"] = "HOLD"
        r["san_ref_point_id"] = f"M2-01-0{i}-F3-C"
        r["basis"] = f"U262, U266, U268; U266 K confirmed by caller line 1729 from MALLOC_MAP_R8_M2c.tsv (k={new_k}); san_ref=M2-01-0{i}-F3-C; supersedes {orig_id}"
        r["status"] = "INFLUENCED"
        delta_rows.append(r)

        diff_records.append((new_id, orig_id, "k_fail", orig_row["k_fail"], r["k_fail"], "U266", "MALLOC_MAP_R8_M2c.tsv"))
        diff_records.append((new_id, orig_id, "env", orig_row["env"], r["env"], "U266", "MALLOC_MAP_R8_M2c.tsv"))
        diff_records.append((new_id, orig_id, "exp_rc1", orig_row["exp_rc1"], r["exp_rc1"], "U262", f"ADDITIONS_MAPPING_22_R8_M1a6.tsv:{i+1}"))
        diff_records.append((new_id, orig_id, "exp_I1", orig_row["exp_I1"], r["exp_I1"], "U268", "U268 InitSolution failure"))
        diff_records.append((new_id, orig_id, "exp_I2", orig_row["exp_I2"], r["exp_I2"], "U268", "U268 InitSolution failure"))
        diff_records.append((new_id, orig_id, "exp_init_clean", "-", r["exp_init_clean"], "U268", "U268 INIT_CLEAN assertion"))
        diff_records.append((new_id, orig_id, "san_ref_point_id", orig_row["san_ref_point_id"], r["san_ref_point_id"], "U262", f"M2-01-0{i}-F3-C"))

    # 5. M2-07-CTRL-vl-ng2/3/4-C (3 rows) (U263, F3)
    for ng in (2, 3, 4):
        orig_id = f"M2-07-CTRL-vl-ng{ng}-F3"
        new_id = orig_id + "-C"
        orig_row = main_v3[orig_id]
        r = dict(orig_row)
        r["point_id"] = new_id
        r["class_rule"] = "NATIVE_FAIL_CONTROL"
        r["exp_rc1"] = "20"
        r["exp_rc2"] = "20"
        r["exp_init_clean"] = "-"
        r["basis"] = f"U263; F3 native failure control (n_G_actual=1, rc1=20, rc2=20); supersedes {orig_id}"
        r["status"] = "INFLUENCED"
        delta_rows.append(r)

        diff_records.append((new_id, orig_id, "class_rule", orig_row["class_rule"], r["class_rule"], "U263", "U263 / U255 NATIVE_FAIL_CONTROL"))
        diff_records.append((new_id, orig_id, "exp_rc1", orig_row["exp_rc1"], r["exp_rc1"], "U263", "U263 / M0 RESULTS_R8_NOINJECT_run1.tsv"))
        diff_records.append((new_id, orig_id, "exp_rc2", orig_row["exp_rc2"], r["exp_rc2"], "U263", "U263 / M0 RESULTS_R8_NOINJECT_run1.tsv"))

    # 6. M2-05-P0-F3-C (1 row) (U268, F6)
    orig_id = "M2-05-P0-F3"
    new_id = orig_id + "-C"
    orig_row = main_v3[orig_id]
    r = dict(orig_row)
    r["point_id"] = new_id
    r["exp_I2"] = "N/A"
    r["exp_init_clean"] = "-"
    r["basis"] = f"U268; F6 exp_I2=N/A because failing layer is 0 and no retained layer before 0; supersedes {orig_id}"
    r["status"] = "INFLUENCED"
    delta_rows.append(r)

    diff_records.append((new_id, orig_id, "exp_I2", orig_row["exp_I2"], r["exp_I2"], "U268", "U268 failing layer 0 has no retained layer"))

    # 7. SOLN probes (27 rows) (U265)
    # Sites: 1763 Solution_, 1764 ab, 1765 solved
    # Combos: closed2d-ng1, fft-ng5, kottke-ng5
    # Drivers: init-F3-dbg, init-B-dbg, init-F3-san
    drv_info = {
        "F3-dbg": ("init-F3-dbg", "d5200355c23f26a99715673a25a35ffe8ec8fe75c72d70ebbf13d0d865759d52", "56f72c5882d4293bbb2d45a272d7c7727e401085b900854b1f49b851effd897a", "testing/d003/stage_s4/r6c_state_r8m2a3.gdb", "5afecd95cc5a914e7ce8d7d6f054daea0d3942b294503833ae28ac59b7ce7221", "F3"),
        "B-dbg": ("init-B-dbg", "3ccc2897fae2ce293d3c656e2a334dad05e53fe7f622b749a71e19bfd021b0b8", "90cebb0907c400ad318e833a2ebb1c1a24ccc2cdbb3a932864a4281504593ee1", "testing/d003/stage_s4/r6c_state_r8m2a3.gdb", "5afecd95cc5a914e7ce8d7d6f054daea0d3942b294503833ae28ac59b7ce7221", "B"),
        "F3-san": ("init-F3-san", "16a27ac27649118e534aea6998de7a4144b9539c8e8fd4f2d6c5439d116f7d48", "2775b9b2c279f51f1be0594c6ea9f635c96e3ba37e9d1638174fa380b45a6986", "-", "-", "F3"),
    }

    # k mapping determined from MALLOC_MAP_R8_M2c.tsv
    k_soln_map = {
        ("F3-dbg", "closed2d-ng1"): {"1763": 9, "1764": 10, "1765": 11},
        ("F3-dbg", "fft-ng5"): {"1763": 10, "1764": 11, "1765": 12},
        ("F3-dbg", "kottke-ng5"): {"1763": 10, "1764": 11, "1765": 12},
        ("B-dbg", "closed2d-ng1"): {"1763": 9, "1764": 10, "1765": 11},
        ("B-dbg", "fft-ng5"): {"1763": 10, "1764": 11, "1765": 12},
        ("B-dbg", "kottke-ng5"): {"1763": 10, "1764": 11, "1765": 12},
        ("F3-san", "closed2d-ng1"): {"1763": 7, "1764": 8, "1765": 8},
        ("F3-san", "fft-ng5"): {"1763": 8, "1764": 9, "1765": 9},
        ("F3-san", "kottke-ng5"): {"1763": 8, "1764": 9, "1765": 9},
    }

    combo_info = [
        ("closed2d-ng1", "closed2d", "1"),
        ("fft-ng5", "fft", "5"),
        ("kottke-ng5", "kottke", "5"),
    ]

    for site in ("1763", "1764", "1765"):
        for cname, mode, ng in combo_info:
            for dkey in ("F3-dbg", "B-dbg", "F3-san"):
                pid = f"SOLN-{site}-{cname}-{dkey}"
                dname, dsha, lsha, gscript, gsha, tree = drv_info[dkey]
                k_val = k_soln_map[(dkey, cname)][site]

                is_san = (dkey == "F3-san")
                is_b = (dkey == "B-dbg")

                exp_cls = "SAN_CRASH" if is_san else "CRASH"
                exp_sig = "0" if is_san else "11"
                exp_san_val = "1" if is_san else "-"
                class_rule = "BASELINE_ONLY" if is_b else "JUDGE_D003"
                exp_rc1 = "MISSING" if site == "1763" else "1"

                san_opts = "ASAN_OPTIONS=detect_leaks=0:abort_on_error=0:log_path=$EV/run/pass{pass}/{point_id}/asan.log;UBSAN_OPTIONS=abort_on_error=0:log_path=$EV/run/pass{pass}/{point_id}/ubsan.log" if is_san else "-"

                soln_row = {
                    "point_id": pid,
                    "item": f"SOLN-{site}",
                    "tree": tree,
                    "driver": dname,
                    "driver_sha256": dsha,
                    "lib_sha256": lsha,
                    "gdb_script": gscript,
                    "gdb_script_sha256": gsha,
                    "argv": "pattern both 4 3",
                    "env": f"FMM_MODE={mode};S4FMM_NG={ng};S4FMM_INJECT=init:{k_val}",
                    "n_G_actual": ng,
                    "passes": "2",
                    "target_layer": "1",
                    "control_point_id": "-",
                    "output_call": "2",
                    "control_output_call": "2",
                    "inj_call": "1",
                    "k_before": "0",
                    "k_fail": str(k_val),
                    "k_preretry": "2",
                    "k_retry": "3",
                    "retry_call": "2",
                    "control_group": "NO",
                    "exp_rc1": exp_rc1,
                    "exp_rc2": "MISSING" if site == "1763" else "0",
                    "exp_rc3": "-",
                    "exp_signal": exp_sig,
                    "exp_hit": "1",
                    "exp_class": exp_cls,
                    "exp_I1": "-",
                    "exp_I2": "-",
                    "exp_I3": "-",
                    "exp_I4": "-",
                    "exp_I5": "-",
                    "exp_I6": "-",
                    "exp_I7": "DEFERRED" if not is_san else "HOLD",
                    "exp_san": exp_san_val,
                    "exp_stage": "-",
                    "class_rule": class_rule,
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
                    "san_options": san_opts,
                    "state_analyzer": "-",
                    "basis": "[源码] 未验证" + ("; BASELINE_ONLY 非修复证据" if is_b else ""),
                    "status": "INFLUENCED",
                    "exp_init_clean": "-"
                }
                delta_rows.append(soln_row)

    # 8. M2-06-DIAG-01-F3 (1 row) (U264)
    m206_row = dict(main_v3["M2-06-01-F3"])
    m206_row["point_id"] = "M2-06-DIAG-01-F3"
    m206_row["item"] = "M2-06-DIAG"
    m206_row["exp_rc1"] = "20"
    m206_row["exp_class"] = "REPORTED_FAILURE"
    m206_row["output_assertion"] = "RECORD_ONLY"
    m206_row["basis"] = "U264; M2-06 record-only diagnosis for return 20 location and NaN eigensystem reachability"
    m206_row["status"] = "INFLUENCED"
    m206_row["exp_init_clean"] = "-"
    delta_rows.append(m206_row)

    # Assert row counts
    assert len(delta_rows) == 54, f"Delta rows {len(delta_rows)} != 54"
    print(f"generate_prereg_delta_r8m2c: generated {len(delta_rows)} delta rows.")

    # Write PREREG_M2_DELTA_R8_M2c.tsv
    with open(MAIN_V3, encoding="utf-8") as fh:
        base_headers = list(csv.DictReader(fh, delimiter="\t").fieldnames)
    headers = base_headers + ["exp_init_clean"]

    with open(DELTA_TSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers, delimiter="\t")
        writer.writeheader()
        for r in delta_rows:
            writer.writerow({h: r.get(h, "-") for h in headers})

    delta_sha = hashlib.sha256(open(DELTA_TSV, "rb").read()).hexdigest()
    with open(SHA_FILE, "w", encoding="utf-8") as fh:
        fh.write(f"{delta_sha}  PREREG_M2_DELTA_R8_M2c.tsv\n")

    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(TIME_FILE, "w", encoding="utf-8") as fh:
        fh.write(f"{now_utc}\n")

    print(f"Wrote {DELTA_TSV} (sha256: {delta_sha})")
    print(f"Timestamp: {now_utc}")

    # Write PREREG_DIFF_R8_M2c.tsv
    diff_headers = ["point_id", "orig_point_id", "column", "old_value", "new_value", "ruling_id", "source_reference"]
    with open(DIFF_TSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(diff_headers)
        for rec in diff_records:
            writer.writerow(rec)

    print(f"Wrote {DIFF_TSV} ({len(diff_records)} diff records).")

    # Assert all diff rulings are within allowed {U262, U263, U266, U268}
    allowed_rulings = {"U262", "U263", "U266", "U268"}
    unauthorized = [r for r in diff_records if r[5] not in allowed_rulings]
    assert len(unauthorized) == 0, f"Unauthorized diffs detected: {unauthorized}"
    print("Diff audit assertion PASSED: 0 unauthorized column changes.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
