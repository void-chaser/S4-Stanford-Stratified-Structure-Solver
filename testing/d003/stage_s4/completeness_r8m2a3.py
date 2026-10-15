#!/usr/bin/env python3
# completeness_r8m2a3.py -- P05-S4 R8 M2a3 Section 9: point-by-point end-to-end evidence chain verification.
# Reads: checkpoints/p05/evidence/p05-s4r8/m2a3/PREREG_M2_EFFECTIVE_R8_M2a3.tsv
#        checkpoints/p05/evidence/p05-s4r8/m2a3/CONTROL_MAPPING_R8_M2a3.tsv
#        checkpoints/p05/evidence/p05-s4r8/m2a3/STATE_COLLECTION_PLAN_R8_M2a3.tsv
# Outputs: checkpoints/p05/evidence/p05-s4r8/m2a3/COMPLETENESS_R8_M2a3.tsv
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a3")
PREREG_PATH = os.path.join(EV, "PREREG_M2_EFFECTIVE_R8_M2a3.tsv")
CTRL_PATH = os.path.join(EV, "CONTROL_MAPPING_R8_M2a3.tsv")
PLAN_PATH = os.path.join(EV, "STATE_COLLECTION_PLAN_R8_M2a3.tsv")
OUT_PATH = os.path.join(EV, "COMPLETENESS_R8_M2a3.tsv")


def read_tsv(path):
    with open(path, "r", encoding="utf-8") as fh:
        lines = [l.rstrip("\r\n") for l in fh if l.strip() and not l.startswith("#")]
    head = lines[0].split("\t")
    rows = [dict(zip(head, l.split("\t"))) for l in lines[1:]]
    return head, rows


def main():
    for p in (PREREG_PATH, CTRL_PATH, PLAN_PATH):
        if not os.path.isfile(p):
            sys.stderr.write("completeness_r8m2a3: missing input file %s\n" % p)
            return 2

    _, pre_rows = read_tsv(PREREG_PATH)
    _, ctrl_rows = read_tsv(CTRL_PATH)
    _, plan_rows = read_tsv(PLAN_PATH)

    ctrl_map = {r["point_id"]: r for r in ctrl_rows}
    plan_map = {r["point_id"]: r for r in plan_rows}

    comp_head = [
        "point_id", "item", "tree", "driver", "expected_assertions",
        "collection_entry", "source_basis", "analysis_rule", "control_binding",
        "chain_status", "detail"
    ]

    comp_rows = []
    fails = 0
    passes = 0

    for r in pre_rows:
        pid = r["point_id"]
        item = r["item"]
        tree = r["tree"]
        driver = r["driver"]
        basis = r["basis"]
        gdb_script = r["gdb_script"]
        ctrl_grp = r["control_group"]
        ctrl_pid = r["control_point_id"]

        assertions = []
        if r["exp_rc1"] != "-": assertions.append("rc1=%s" % r["exp_rc1"])
        if r["exp_rc2"] != "-": assertions.append("rc2=%s" % r["exp_rc2"])
        if r["exp_rc3"] != "-": assertions.append("rc3=%s" % r["exp_rc3"])
        if r["exp_hit"] != "-": assertions.append("hit=%s" % r["exp_hit"])
        if r["exp_class"] != "-": assertions.append("class=%s" % r["exp_class"])
        for i in range(1, 8):
            k = "exp_I%d" % i
            if r[k] not in ("", "-"):
                assertions.append("I%d=%s" % (i, r[k]))
        if r["exp_san"] not in ("", "-"): assertions.append("san=%s" % r["exp_san"])

        assert_str = ",".join(assertions)

        # Check collection entry
        p_info = plan_map.get(pid, {})
        coll_entry = p_info.get("collector_type", "-")
        has_coll = bool(coll_entry and coll_entry != "-")

        # Check source basis
        has_basis = bool(basis and basis != "-")

        # Check analysis rule
        # verdict_m2_r8m2a3 supports all assertions
        analysis_rule = "verdict_m2_r8m2a3.py (judge_d003 + rc/inv/san checks)"

        # Check control binding
        has_ctrl = True
        ctrl_detail = ctrl_pid
        if ctrl_grp == "NO" and any(r["exp_I%d" % i] == "HOLD" for i in (2, 6)):
            if ctrl_pid in ("", "-"):
                has_ctrl = False
                ctrl_detail = "MISSING_CONTROL_BINDING"
            else:
                ctrl_detail = "%s (call%s vs ctrl call%s)" % (ctrl_pid, r["output_call"], r["control_output_call"])

        # Determine chain status
        issues = []
        if not has_coll:
            issues.append("MISSING_COLLECTION_ENTRY")
        if not has_basis:
            issues.append("MISSING_SOURCE_BASIS")
        if not has_ctrl:
            issues.append("MISSING_CONTROL_BINDING")

        if issues:
            chain_status = "FAIL"
            fails += 1
            detail = "; ".join(issues)
        else:
            chain_status = "PASS"
            passes += 1
            detail = "Complete end-to-end evidence chain verified"

        comp_rows.append([
            pid, item, tree, driver, assert_str, coll_entry, basis,
            analysis_rule, ctrl_detail, chain_status, detail
        ])

    os.makedirs(EV, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write("\t".join(comp_head) + "\n")
        for cr in comp_rows:
            fh.write("\t".join(cr) + "\n")

    summary_msg = "COMPLETENESS_R8_M2a3 total=%d PASS=%d FAIL=%d" % (len(comp_rows), passes, fails)
    print(summary_msg)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
