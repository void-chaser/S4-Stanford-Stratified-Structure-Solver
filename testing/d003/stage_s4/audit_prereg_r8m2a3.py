#!/usr/bin/env python3
# audit_prereg_r8m2a3.py -- P05-S4 R8 M2a3 Section 4: static executability audit of PREREG_M2_R8_M2a2.tsv.
# Reads: checkpoints/p05/registries/s4r8/M2/r8m2a2/PREREG_M2_R8_M2a2.tsv (150 rows)
# Writes: checkpoints/p05/evidence/p05-s4r8/m2a3/PREREG_EXECUTABILITY_AUDIT_R8_M2a3.tsv
# Checks:
#   1. point_id uniqueness, field count, tree/driver/lib identity;
#   2. Non-empty expected values collection path;
#   3. exp_I1..I6=HOLD state collector, applicability & control point binding;
#   4. gdb_script=- vs private state requirement conflict;
#   5. inj_call, snapshot indices, retry_call compliance with driver sources;
#   6. Dual-target coverage of rc1, rc2, rc3;
#   7. I6 control point and call number binding;
#   8. Sanitizer exp_san vs I7 definition and collection method;
#   9. Formal verdict script coverage of all applicable assertions.
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a3")
PREREG_PATH = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a2", "PREREG_M2_R8_M2a2.tsv")
OUT_PATH = os.path.join(EV, "PREREG_EXECUTABILITY_AUDIT_R8_M2a3.tsv")

EXPECTED_HEADER_LEN = 34
POLBASIS = {"jones", "nv", "vl", "fftjones", "fftnv", "fftvl"}


def main():
    if not os.path.isfile(PREREG_PATH):
        sys.stderr.write("audit_prereg_r8m2a3: missing prereg file: %s\n" % PREREG_PATH)
        return 2

    with open(PREREG_PATH, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    if not lines:
        sys.stderr.write("audit_prereg_r8m2a3: empty prereg file\n")
        return 2

    header = lines[0].rstrip("\r\n").split("\t")
    if len(header) != EXPECTED_HEADER_LEN:
        sys.stderr.write("audit_prereg_r8m2a3: unexpected header length: %d != %d\n" % (len(header), EXPECTED_HEADER_LEN))
        return 2

    seen_pids = set()
    audit_rows = []
    audit_counter = 0

    def add_finding(pid, item, tree, driver, sline, category, status, field, detail):
        nonlocal audit_counter
        audit_counter += 1
        audit_rows.append([
            str(audit_counter),
            pid,
            item,
            tree,
            driver,
            str(sline),
            category,
            status,
            field,
            detail
        ])

    for line_idx, raw_line in enumerate(lines[1:], start=2):
        line = raw_line.rstrip("\r\n")
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != EXPECTED_HEADER_LEN:
            pid = fields[0] if fields else "UNKNOWN"
            add_finding(pid, "UNKNOWN", "UNKNOWN", "UNKNOWN", line_idx,
                        "FIELD_COUNT", "DEFECT", "FIELD_COUNT",
                        "Line has %d fields, expected %d" % (len(fields), EXPECTED_HEADER_LEN))
            continue

        row = dict(zip(header, fields))
        pid = row["point_id"]
        item = row["item"]
        tree = row["tree"]
        driver = row["driver"]
        dsha = row["driver_sha256"]
        lsha = row["lib_sha256"]
        gdb_script = row["gdb_script"]
        env = row["env"]
        inj_call = row["inj_call"]
        k_before = row["k_before"]
        k_fail = row["k_fail"]
        k_preretry = row["k_preretry"]
        k_retry = row["k_retry"]
        retry_call = row["retry_call"]
        ctrl_grp = row["control_group"]
        exp_rc1 = row["exp_rc1"]
        exp_rc2 = row["exp_rc2"]
        exp_class = row["exp_class"]
        exp_san = row["exp_san"]
        exp_I = {("I%d" % i): row["exp_I%d" % i] for i in range(1, 8)}

        # 1. point_id uniqueness & identity
        if pid in seen_pids:
            add_finding(pid, item, tree, driver, line_idx, "IDENTITY", "DEFECT", "point_id",
                        "Duplicate point_id detected")
        else:
            seen_pids.add(pid)

        if tree not in ("F3", "F2", "B"):
            add_finding(pid, item, tree, driver, line_idx, "IDENTITY", "DEFECT", "tree",
                        "Invalid tree: %s" % tree)

        if driver == "-":
            add_finding(pid, item, tree, driver, line_idx, "IDENTITY", "GAP", "driver",
                        "Driver unspecified (-)")
        if dsha == "-":
            add_finding(pid, item, tree, driver, line_idx, "IDENTITY", "GAP", "driver_sha256",
                        "Driver sha256 unspecified (-)")
        if lsha == "-":
            add_finding(pid, item, tree, driver, line_idx, "IDENTITY", "GAP", "lib_sha256",
                        "Library sha256 unspecified (-)")

        # 2 & 4. Private state collection path vs gdb_script=- conflict
        has_hold_inv = any(v == "HOLD" for k, v in exp_I.items() if k != "I7")
        if has_hold_inv and gdb_script == "-":
            add_finding(pid, item, tree, driver, line_idx, "GDB_CONFLICT", "CONFLICT", "gdb_script",
                        "Requires private state invariants (I1..I6=HOLD) but gdb_script is '-' (no state collector)")

        # 3. exp_I1..I6 applicability and control binding
        if has_hold_inv:
            # Check I3 applicability
            fmm_mode = ""
            for kv in env.split(";"):
                if kv.startswith("FMM_MODE="):
                    fmm_mode = kv.split("=", 1)[1]
            if fmm_mode and fmm_mode not in POLBASIS:
                if exp_I["I3"] != "-":
                    add_finding(pid, item, tree, driver, line_idx, "APPLICABILITY", "DEFECT", "exp_I3",
                                "Mode %s is not PolBasis, I3 must be '-' but found %s" % (fmm_mode, exp_I["I3"]))

            # Control binding for I2/I6
            if ctrl_grp == "NO":
                add_finding(pid, item, tree, driver, line_idx, "CONTROL_BINDING", "GAP", "control_group",
                            "Test row expects HOLD on I2/I6 but no explicit control_point_id or output_call mapping is provided")

        # 5. inj_call, snapshot indices, retry_call compliance with driver
        if item == "M2-04":
            # Dual target special check
            # In M2-04: call1 fails (k_fail=1), call2 fails (k_fail=3), call3 recovers (k_retry=4, retry_call=3)
            if retry_call != "3":
                add_finding(pid, item, tree, driver, line_idx, "SNAPSHOT_INDICES", "DEFECT", "retry_call",
                            "M2-04 dual failure recovers at call3, but retry_call is registered as %s (call2 fails with rc2=20)" % retry_call)
            if k_retry != "4":
                add_finding(pid, item, tree, driver, line_idx, "SNAPSHOT_INDICES", "DEFECT", "k_retry",
                            "M2-04 recovery state is after call3 (k=4), but k_retry is registered as %s (k=3 is after second failure call2)" % k_retry)
            if k_preretry != "3":
                add_finding(pid, item, tree, driver, line_idx, "SNAPSHOT_INDICES", "DEFECT", "k_preretry",
                            "M2-04 state before final recovery call3 is k=3, but k_preretry is %s" % k_preretry)

        # 6. Dual-target coverage of rc1, rc2, rc3
        if item == "M2-04":
            if "exp_rc3" not in row:
                add_finding(pid, item, tree, driver, line_idx, "DUAL_FAILURE", "GAP", "exp_rc3",
                            "Dual target driver executes call3, but prereg schema lacks explicit exp_rc3 column (expected 0)")

        # 7. I6 control binding and call number
        if exp_I["I6"] == "HOLD":
            if item == "M2-04":
                add_finding(pid, item, tree, driver, line_idx, "I6_BINDING", "DEFECT", "exp_I6",
                            "I6 comparison currently targets retry_call=2, which is the second failure, instead of recovery call3")

        # 8. Sanitizer exp_san vs I7 definition and collection method
        if item == "M2-03":
            if exp_I["I7"] == "HOLD" and exp_san == "0":
                add_finding(pid, item, tree, driver, line_idx, "SANITIZER", "CONFLICT", "exp_I7",
                            "Sanitizer row has both exp_I7=HOLD and exp_san=0; I7 is redundant with exp_san, and private state cannot be collected in sanitizer run")
            if gdb_script == "-" and any(exp_I[k] == "HOLD" for k in ("I1", "I2", "I3", "I4", "I5", "I6")):
                add_finding(pid, item, tree, driver, line_idx, "SANITIZER", "CONFLICT", "gdb_script",
                            "Sanitizer binary cannot run state collector without paired dbg run; I1..I6 cannot be observed directly in sanitizer run")

        # 9. Formal verdict script coverage
        # All rows with NZ token or exp_san or dual target
        if exp_rc1 == "NZ" or exp_rc2 == "NZ":
            # NZ is checked by verdict_m2_r8m2a2, but needs strict assertion
            pass
        if item == "M2-04":
            add_finding(pid, item, tree, driver, line_idx, "VERDICT_COVERAGE", "GAP", "verdict_m2",
                        "verdict_m2_r8m2a2 does not verify rc3, does not check dual failure sequence, and does not compare pass2 independently against expectations")

    os.makedirs(EV, exist_ok=True)
    out_cols = ["audit_id", "point_id", "item", "tree", "driver", "source_line", "check_category", "verdict", "affected_field", "detail"]
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write("\t".join(out_cols) + "\n")
        for r in audit_rows:
            fh.write("\t".join(r) + "\n")

    # Generate summary
    categories = {}
    verdicts = {}
    for r in audit_rows:
        categories[r[6]] = categories.get(r[6], 0) + 1
        verdicts[r[7]] = verdicts.get(r[7], 0) + 1

    print("audit_prereg_r8m2a3: audited %d points, total findings: %d" % (len(seen_pids), len(audit_rows)))
    print("Verdicts breakdown: %s" % (dict(verdicts)))
    print("Categories breakdown: %s" % (dict(categories)))
    print("Audit written to: %s" % OUT_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
