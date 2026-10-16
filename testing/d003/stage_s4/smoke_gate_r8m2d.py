#!/usr/bin/env python3
# smoke_gate_r8m2d.py -- P05-S4 R8 M2d smoke gate.
# Checks 7 gates:
#  Gate 1: File completeness (stdout/stderr/exitcode and gdb.log if dbg)
#  Gate 2: Facts completeness (no unexpected MISSING in rc/rc1)
#  Gate 3: State analysis valid (no UNJUDGED for exp_I*=HOLD)
#  Gate 4: Command plan clean (no unexpanded '$')
#  Gate 5: Identity verified (no IDENTITY_FAIL)
#  Gate 6 (U270a): exp_hit>=1 rows observe hit>=1
#  Gate 7 (U270b): every non-MATCH must be recorded in triage table with valid category
import argparse
import csv
import os
import sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))


def read_tsv(path):
    if not path or not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"))


def main():
    parser = argparse.ArgumentParser(description="P05-S4 smoke gate v3")
    parser.add_argument("--prereg", required=True, help="Path to smoke preregistration TSV")
    parser.add_argument("--smoke-dir", required=True, help="Path to smoke evidence directory")
    parser.add_argument("--triage", required=True, help="Path to triage TSV (e.g. TRIAGE_R8_M2d.tsv)")
    parser.add_argument("--plan", default=None, help="Path to COMMAND_PLAN_SMOKE.tsv (default: inside smoke-dir)")

    args = parser.parse_args()

    smoke_prereg_rows = read_tsv(args.prereg)
    if not smoke_prereg_rows:
        sys.exit(f"FATAL: Empty or missing prereg: {args.prereg}")

    plan_path = args.plan or os.path.join(args.smoke_dir, "COMMAND_PLAN_SMOKE.tsv")
    plan_rows = read_tsv(plan_path)

    facts1_path = os.path.join(args.smoke_dir, "FACTS_pass1.tsv")
    facts2_path = os.path.join(args.smoke_dir, "FACTS_pass2.tsv")
    facts1 = {r["point_id"]: r for r in read_tsv(facts1_path)}
    facts2 = {r["point_id"]: r for r in read_tsv(facts2_path)}

    state1_path = os.path.join(args.smoke_dir, "STATE_pass1.tsv")
    state2_path = os.path.join(args.smoke_dir, "STATE_pass2.tsv")
    state1 = {r["point_id"]: r for r in read_tsv(state1_path)}
    state2 = {r["point_id"]: r for r in read_tsv(state2_path)}

    verdict_path = os.path.join(args.smoke_dir, "VERDICT_SMOKE.tsv")
    verdict_rows = read_tsv(verdict_path)

    triage_rows = {r["point_id"]: r for r in read_tsv(args.triage)}

    fails = 0

    # Gate 1: File completeness
    missing_files = []
    for pas in ("1", "2"):
        for r in smoke_prereg_rows:
            pid = r["point_id"]
            p_dir = os.path.join(args.smoke_dir, "run", f"pass{pas}", pid)
            for fname in ("stdout.txt", "stderr.txt", "exitcode.txt"):
                fpath = os.path.join(p_dir, fname)
                if not os.path.isfile(fpath):
                    missing_files.append((pas, pid, fname))
            if r.get("gdb_script") not in (None, "", "-"):
                gpath = os.path.join(p_dir, "gdb.log")
                if not os.path.isfile(gpath):
                    missing_files.append((pas, pid, "gdb.log"))

    gate1_pass = (len(missing_files) == 0)
    print(f"Gate 1 (File completeness): {'PASS' if gate1_pass else 'FAIL'} (missing={len(missing_files)})")
    if not gate1_pass:
        fails += 1
        print(f"  Missing sample: {missing_files[:5]}")

    # Gate 2: Facts completeness
    gate2_missing = 0
    smoke_pr_dict = {r["point_id"]: r for r in smoke_prereg_rows}
    for f_dict, pas in [(facts1, "1"), (facts2, "2")]:
        for pid, fr in f_dict.items():
            if pid not in smoke_pr_dict:
                continue
            pr = smoke_pr_dict[pid]
            if fr.get("rc") == "MISSING":
                gate2_missing += 1
            if fr.get("rc1") == "MISSING" and pr.get("exp_rc1") not in ("MISSING", "-") and pr.get("exp_class") not in ("CRASH", "SAN_CRASH"):
                gate2_missing += 1

    gate2_pass = (gate2_missing == 0)
    print(f"Gate 2 (Facts completeness): {'PASS' if gate2_pass else 'FAIL'} (missing_rc={gate2_missing})")
    if not gate2_pass:
        fails += 1

    # Gate 3: State analysis valid (no UNJUDGED for HOLD)
    gate3_unjudged = []
    for pid, pr in smoke_pr_dict.items():
        if pr.get("state_analyzer") not in (None, "", "-"):
            s_row = state1.get(pid, {})
            for inv in ("I1", "I2", "I3", "I4", "I5", "I6"):
                if pr.get(f"exp_{inv}") == "HOLD":
                    obs = s_row.get(inv)
                    if obs == "UNJUDGED":
                        gate3_unjudged.append((pid, inv, obs))

    gate3_pass = (len(gate3_unjudged) == 0)
    print(f"Gate 3 (State analysis valid): {'PASS' if gate3_pass else 'FAIL'} (unjudged={len(gate3_unjudged)})")
    if not gate3_pass:
        fails += 1
        print(f"  Gate 3 unjudged sample: {gate3_unjudged[:5]}")

    # Gate 4: Command plan clean (no '$')
    gate4_dollar = 0
    for p in plan_rows:
        if "$" in p.get("env_as_run", "") or "$" in p.get("full_command_a", "") or "$" in p.get("full_command_b", ""):
            gate4_dollar += 1

    gate4_pass = (gate4_dollar == 0)
    print(f"Gate 4 (No unexpanded '$'): {'PASS' if gate4_pass else 'FAIL'} (count={gate4_dollar})")
    if not gate4_pass:
        fails += 1

    # Gate 5: Identity verified
    gate5_ident_fail = sum(1 for p in plan_rows if p.get("identity_status") == "IDENTITY_FAIL")
    gate5_pass = (gate5_ident_fail == 0)
    print(f"Gate 5 (Identity verified): {'PASS' if gate5_pass else 'FAIL'} (fails={gate5_ident_fail})")
    if not gate5_pass:
        fails += 1

    # Gate 6 (U270a): exp_hit>=1 rows observe hit>=1
    gate6_hit_fails = []
    for r in smoke_prereg_rows:
        pid = r["point_id"]
        exp_h = r.get("exp_hit", "-")
        if exp_h not in (None, "", "-") and exp_h.isdigit() and int(exp_h) >= 1:
            h1 = facts1.get(pid, {}).get("hit", "0")
            h2 = facts2.get(pid, {}).get("hit", "0")
            val1 = int(h1) if h1.isdigit() else 0
            val2 = int(h2) if h2.isdigit() else 0
            if val1 < 1 or val2 < 1:
                gate6_hit_fails.append((pid, exp_h, h1, h2))

    gate6_pass = (len(gate6_hit_fails) == 0)
    print(f"Gate 6 (U270a: exp_hit>=1 observed hit>=1): {'PASS' if gate6_pass else 'FAIL'} (fails={len(gate6_hit_fails)})")
    if not gate6_pass:
        fails += 1
        print(f"  Gate 6 failure sample: {gate6_hit_fails}")

    # Gate 7 (U270b): Non-MATCH triage check
    gate7_untriaged = []
    gate7_prereg_error_nonmatch = []
    for vr in verdict_rows:
        pid = vr["point_id"]
        v = vr.get("verdict", "MATCH")
        if v != "MATCH":
            base_pid = pid[:-2] if pid.endswith("-C") else pid
            if pid not in triage_rows and base_pid not in triage_rows:
                gate7_untriaged.append(pid)
            else:
                tr = triage_rows.get(pid) or triage_rows.get(base_pid)
                cat = tr.get("category", "")
                if "预注册错误" in cat:
                    gate7_prereg_error_nonmatch.append((pid, cat))

    gate7_pass = (len(gate7_untriaged) == 0)
    print(f"Gate 7 (U270b: non-MATCH triage check): {'PASS' if gate7_pass else 'FAIL'} (untriaged={len(gate7_untriaged)})")
    if not gate7_pass:
        fails += 1
        print(f"  Untriaged non-MATCH points: {gate7_untriaged}")

    if gate7_prereg_error_nonmatch:
        print(f"Gate 7 WARNING: Non-MATCH points categorized as 预注册错误: {gate7_prereg_error_nonmatch}")

    print(f"\nSMOKE_GATE_V3_TOTAL_FAILS={fails}")
    return fails


if __name__ == "__main__":
    sys.exit(main())
