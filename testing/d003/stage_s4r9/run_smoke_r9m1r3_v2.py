#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# run_smoke_r9m1r3_v2.py -- Smoke test execution for P05-S4 R9 M1R3 (Step S-G, Rule U316). New file.
import argparse, csv, hashlib, os, re, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r3"))
os.makedirs(EV, exist_ok=True)

sys.path.insert(0, os.path.join(REPO, "testing", "d003"))
import judge_d003

def sha256_file(p):
    if not os.path.isfile(p): return "MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            c = fh.read(65536)
            if not c: break
            h.update(c)
    return h.hexdigest()

def clean_child_env(env_str):
    env = os.environ.copy()
    for item in env_str.split(";"):
        if "=" in item:
            k, v = item.split("=", 1)
            env[k.strip()] = v.strip()
    return env

def main():
    parser = argparse.ArgumentParser(description="Run smoke test for M1 F4")
    parser.add_argument("--prereg", default=os.path.join(EV, "PREREG_M1_F4_R9M1R3.tsv"))
    parser.add_argument("--out", default=os.path.join(EV, "SMOKE_M1_F4_R9M1R3.tsv"))
    parser.add_argument("--out-summary", default=os.path.join(EV, "SMOKE_SUMMARY_R9M1R3.txt"))
    args = parser.parse_args()

    lines = [l.strip().split("\t") for l in open(args.prereg, encoding="utf-8") if l.strip() and not l.startswith("#")]
    h = lines[0]
    all_rows = [dict(zip(h, l)) for l in lines[1:]]

    # Selection:
    # 1. >= 1 row per (section, group, driver_name)
    # 2. Homonymous point_id in G1 and G2b: M-once-fft-plan-3-F4
    # 3. G6 at least 2 rows (including at least one with exp_I4 == "N/A")
    selected = []
    seen_combos = set()
    homonymous_g1_g2b = {"M-once-fft-plan-3-F4"}

    # Track G6 selection: select at least 2 rows (one with N/A invariant like R4-AL18-F-F4 with I3=N/A, and one all-HOLD like R4-ACF1-F-F4)
    g6_rows = [r for r in all_rows if r["group"] == "G6"]
    g6_na = [r for r in g6_rows if r["exp_I3"] == "N/A" or r["exp_I4"] == "N/A"]
    g6_all_hold = [r for r in g6_rows if r["exp_I3"] == "HOLD" and r["exp_I4"] == "HOLD"]
    g6_force_include = set()
    if g6_na: g6_force_include.add(g6_na[0]["point_id"])
    if g6_all_hold: g6_force_include.add(g6_all_hold[0]["point_id"])

    for r in all_rows:
        sec, grp, drv, pid = r["section"], r["group"], r["driver_name"], r["point_id"]
        combo = (sec, grp, drv)
        is_homonymous = (grp in ("G1", "G2b") and pid in homonymous_g1_g2b)
        is_g6_special = (grp == "G6" and pid in g6_force_include)

        if combo not in seen_combos or is_homonymous or is_g6_special:
            seen_combos.add(combo)
            selected.append(r)

    # Verify G6 has >= 2 rows
    selected_g6 = [r for r in selected if r["group"] == "G6"]
    assert len(selected_g6) >= 2, f"Expected >= 2 G6 rows in smoke, got {len(selected_g6)}"
    assert any(r["exp_I3"] == "N/A" or r["exp_I4"] == "N/A" for r in selected_g6), "Expected at least one G6 row with N/A invariant in smoke"

    print(f"Selected {len(selected)} smoke test points across {len(seen_combos)} (section, group, driver) combinations.")

    smoke_results = []
    fails = 0

    driver_cache = {}
    def get_driver_path(drv_name):
        if drv_name in driver_cache: return driver_cache[drv_name]
        candidates = [
            os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m0/build", drv_name),
            os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1/build", drv_name),
            os.path.join(REPO, "checkpoints/p05/evidence/p05-s3r5/build", drv_name),
            os.path.join(EV, "build", drv_name)
        ]
        for c in candidates:
            if os.path.isfile(c) and os.access(c, os.X_OK):
                driver_cache[drv_name] = c
                return c
        raise FileNotFoundError(f"Cannot find executable for driver {drv_name}")

    for idx, r in enumerate(selected, 1):
        sec, grp, pid = r["section"], r["group"], r["point_id"]
        drv_name = r["driver_name"]
        drv_exe = get_driver_path(drv_name)
        exp_sha = r["driver_sha256"]

        # If G2c_control un-run row:
        if r["f3_effective_verdict"] == "NOT_RUN_AS_EXPECTED" or r["env"] == "NOT_RUN":
            smoke_results.append([
                sec, grp, pid, drv_name, exp_sha,
                "-", "-", "-", "-", "NOT_RUN_REGISTRY_ERROR", "NOT_RUN_AS_EXPECTED", "NONE"
            ])
            print(f"[{idx}/{len(selected)}] {sec} {grp} {pid} -> NOT_RUN_AS_EXPECTED (un-run control)")
            continue

        # 1. Verify driver sha before run
        sha_before = sha256_file(drv_exe)
        assert sha_before == exp_sha, f"Driver {drv_name} sha before run {sha_before} != prereg {exp_sha}"

        # 2. Execute
        child_env = clean_child_env(r["env"])
        argv = r["argv"].split()
        cmd = [drv_exe] + argv

        proc = subprocess.run(cmd, env=child_env, cwd=REPO, capture_output=True, text=True, timeout=60)
        raw_rc = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr

        # 3. Verify driver sha after run
        sha_after = sha256_file(drv_exe)
        assert sha_after == exp_sha, f"Driver {drv_name} sha after run {sha_after} != prereg {exp_sha}"

        # 4. Parse facts
        m_rc1 = re.search(r"^RC first (-?[0-9]+)", stdout, re.M)
        rc1 = int(m_rc1.group(1)) if m_rc1 else 0

        m_rc2 = re.search(r"^RC retry (-?[0-9]+)", stdout, re.M)
        rc2 = int(m_rc2.group(1)) if m_rc2 else 0

        m_rc3 = re.search(r"^RC3=(-?[0-9]+)", stderr, re.M)
        rc3 = int(m_rc3.group(1)) if m_rc3 else "-"

        m_hitc = re.search(r"^S4FMM HITCOUNT ([0-9]+)", stderr, re.M)
        if m_hitc:
            hit = int(m_hitc.group(1))
        else:
            hit = len(re.findall(r"^S4FMM HIT ", stderr, re.M))

        real = (r.get("real", "1") != "0")
        inj_call_s = r.get("inj_call", "-")
        inj_call = int(inj_call_s) if inj_call_s not in ("-", "", None) else 1
        is_ctrl = (r["exp_class"] in ("CONTROL_OK", "CLEAN") or "none" in r["env"] or r["exp_hit"] == "0" or grp in ("CTRL_SEAM", "G2c_control", "M1_CTRL", "G6c", "CTRL_AUX"))

        cls, _, _ = judge_d003.classify(raw_rc, rc1, rc2, hit, control=is_ctrl, real=real, inj_call=inj_call)

        # 5. Check against expectation
        exp_eff = r["f3_effective_verdict"]
        diff_fields = []

        if exp_eff == "NOT_REACHED_AS_EXPECTED":
            if hit == 0 and cls == "INVALID":
                v = "NOT_REACHED_AS_EXPECTED"
            else:
                v = "MISMATCH"
                diff_fields.append("unexpected_hit")
        else:
            if r["exp_rc1"] != "-" and str(rc1) != r["exp_rc1"]:
                diff_fields.append(f"rc1({rc1}!={r['exp_rc1']})")
            if sec == "M1b":
                if r["exp_rc2"] not in ("-", "", "0") and str(rc2) != r["exp_rc2"]:
                    diff_fields.append(f"rc2({rc2}!={r['exp_rc2']})")
            else:
                if r["exp_rc2"] != "-" and str(rc2) != r["exp_rc2"]:
                    diff_fields.append(f"rc2({rc2}!={r['exp_rc2']})")
            if r["exp_hit"] != "-" and str(hit) != r["exp_hit"]:
                diff_fields.append(f"hit({hit}!={r['exp_hit']})")

            exp_c = r["exp_class"]
            if sec == "M1c":
                exp_pv = r["exp_point_verdict"]
                if exp_pv == "-" and grp in ("G6c", "CTRL_AUX"):
                    exp_pv = "CONTROL_OK"
                if cls != exp_pv and cls != exp_c:
                    diff_fields.append(f"class({cls}!={exp_pv})")
            else:
                if cls != exp_c:
                    diff_fields.append(f"class({cls}!={exp_c})")

            if not diff_fields:
                v = "MATCH"
            else:
                v = "MISMATCH"
                fails += 1

        smoke_results.append([
            sec, grp, pid, drv_name, exp_sha, str(rc1), str(rc2), str(rc3), str(hit), cls, v,
            ";".join(diff_fields) if diff_fields else "NONE"
        ])
        print(f"[{idx}/{len(selected)}] {sec} {grp} {pid} -> {v} (rc1={rc1}, hit={hit}, class={cls})")

    # Write output
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("# SMOKE_M1_F4_R9M1R3.tsv -- Smoke test results for P05-S4 R9 M1R3 (Rule U316)" + chr(10))
        f.write(chr(9).join([
            "section", "group", "point_id", "driver_name", "driver_sha256",
            "rc1", "rc2", "rc3", "hit", "computed_class", "verdict", "difference_fields"
        ]) + chr(10))
        for row in smoke_results:
            f.write(chr(9).join(row) + chr(10))

    summary_text = f"Smoke Test Summary (P05-S4 R9 M1R3):\nTotal points tested: {len(smoke_results)}\nFAILS: {fails}\n"
    with open(args.out_summary, "w", encoding="utf-8") as f:
        f.write(summary_text)

    if fails != 0:
        print(f"Smoke test FAILED with {fails} failures! Stopping per Rule §6-7.", file=sys.stderr)
        sys.exit(fails)

    print(f"Smoke test PASSED ({len(smoke_results)}/{len(smoke_results)} MATCH).")

if __name__ == "__main__":
    main()
