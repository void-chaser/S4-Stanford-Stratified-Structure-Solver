#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# run_smoke_r9m1r2_R2.py -- Smoke test execution for P05-S4 R9 M1R2 (Step S-G, Rule U316). New file.
import argparse, csv, hashlib, os, re, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r2"))
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
    for k in list(env.keys()):
        if k.startswith("S4FMM_"):
            del env[k]
    for pair in env_str.split(";"):
        if "=" in pair:
            k, v = pair.split("=", 1)
            k = k.strip()
            v = v.strip()
            if k == "S4FMM_INJECT" and v == "none":
                continue
            env[k] = v
    return env

def main():
    parser = argparse.ArgumentParser(description="Run smoke test for M1 F4")
    parser.add_argument("--prereg", default=os.path.join(EV, "PREREG_M1_F4_R9M1R2.tsv"))
    parser.add_argument("--out", default=os.path.join(EV, "SMOKE_M1_F4_R9M1R2.tsv"))
    parser.add_argument("--out-summary", default=os.path.join(EV, "SMOKE_SUMMARY_R9M1R2.txt"))
    args = parser.parse_args()

    lines = [l.strip().split("\t") for l in open(args.prereg, encoding="utf-8") if l.strip() and not l.startswith("#")]
    h = lines[0]
    all_rows = [dict(zip(h, l)) for l in lines[1:]]

    # Selection: >= 1 row per (section, group, driver_name), plus homonymous point_id in G1 and G2b
    selected = []
    seen_combos = set()
    homonymous_g1_g2b = {"M-once-fft-plan-3-F4", "M-once-fft-exec-1-F4"}

    for r in all_rows:
        sec, grp, drv, pid = r["section"], r["group"], r["driver_name"], r["point_id"]
        combo = (sec, grp, drv)
        is_homonymous = (grp in ("G1", "G2b") and pid in homonymous_g1_g2b)

        if combo not in seen_combos or is_homonymous:
            seen_combos.add(combo)
            selected.append(r)

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
        rc1 = int(m_rc1.group(1)) if m_rc1 else None

        m_rc2 = re.search(r"^RC retry (-?[0-9]+)", stdout, re.M)
        rc2 = int(m_rc2.group(1)) if m_rc2 else None

        m_rc3 = re.search(r"^R6CALLS 3 (-?[0-9]+)", stdout, re.M)
        rc3 = int(m_rc3.group(1)) if m_rc3 else None

        m_hitc = re.search(r"^S4FMM HITCOUNT ([0-9]+)", stderr, re.M)
        if m_hitc: hit = int(m_hitc.group(1))
        else: hit = len(re.findall(r"^S4FMM HIT ", stderr, re.M))

        exp_c = r["exp_class"]
        exp_rc1_val = None if r["exp_rc1"] in ("-", "") else int(r["exp_rc1"])
        exp_rc2_val = None if r["exp_rc2"] in ("-", "") else int(r["exp_rc2"])
        exp_hit_val = None if r["exp_hit"] in ("-", "") else int(r["exp_hit"])

        is_ctrl = (exp_c in ("CONTROL_OK", "CLEAN") or "none" in r["env"] or exp_hit_val == 0 or grp in ("CTRL_SEAM", "M1_CTRL", "G2c_control", "CTRL_AUX", "G6c", "POLY_33"))
        is_real = ("exec" not in r["env"])
        inj_call = 2 if ("TWICE" in r["env"] or (exp_rc1_val == 0 and exp_rc2_val is not None and exp_rc2_val != 0)) else 1

        cls, _, _ = judge_d003.classify(raw_rc, rc1, rc2, hit, control=is_ctrl, real=is_real, inj_call=inj_call)

        diff_fields = []
        if exp_rc1_val is not None and rc1 != exp_rc1_val:
            diff_fields.append(f"rc1({rc1}!={exp_rc1_val})")
        if exp_rc2_val is not None and rc2 != exp_rc2_val:
            diff_fields.append(f"rc2({rc2}!={exp_rc2_val})")
        if exp_hit_val is not None and hit != exp_hit_val:
            diff_fields.append(f"hit({hit}!={exp_hit_val})")

        if sec == "M1c":
            exp_judge_class = "REPORTED_FAILURE" if exp_c == "HOLD" else "CONTROL_OK"
        else:
            exp_judge_class = exp_c

        if r["f3_effective_verdict"] == "NOT_RUN_AS_EXPECTED":
            point_verdict = "NOT_RUN_AS_EXPECTED"
        elif r["f3_effective_verdict"] == "NOT_REACHED_AS_EXPECTED":
            if cls == "INVALID":
                point_verdict = "NOT_REACHED_AS_EXPECTED"
            else:
                point_verdict = "MISMATCH"
                diff_fields.append("not_reached_mismatch")
        elif diff_fields or (exp_judge_class != "-" and cls != exp_judge_class):
            point_verdict = "MISMATCH"
            fails += 1
        else:
            point_verdict = "MATCH"

        smoke_results.append([
            sec, grp, pid, drv_name, exp_sha,
            str(rc1) if rc1 is not None else "-",
            str(rc2) if rc2 is not None else "-",
            str(rc3) if rc3 is not None else "-",
            str(hit), cls, point_verdict,
            ";".join(diff_fields) if diff_fields else "NONE"
        ])
        print(f"[{idx:02d}/{len(selected)}] {sec} {grp} {pid} -> {point_verdict} (rc1={rc1}, hit={hit}, class={cls})")

    # Write output
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("# SMOKE_M1_F4_R9M1R2.tsv -- Smoke test results for P05-S4 R9 M1R2 (Rule U316)\n")
        f.write("section\tgroup\tpoint_id\tdriver_name\tdriver_sha256\trc1\trc2\trc3\thit\tcomputed_class\tverdict\tdifference_fields\n")
        for row in smoke_results:
            f.write("\t".join(row) + "\n")

    summary_text = f"Smoke Test Summary (P05-S4 R9 M1R2):\nTotal points tested: {len(smoke_results)}\nFAILS: {fails}\n"
    with open(args.out_summary, "w", encoding="utf-8") as f:
        f.write(summary_text)

    if fails != 0:
        print(f"Smoke test FAILED with {fails} failures! Stopping per Rule §6-7.", file=sys.stderr)
        sys.exit(fails)

    print(f"Smoke test PASSED ({len(smoke_results)}/{len(smoke_results)} MATCH/EXPECTED).")

if __name__ == "__main__":
    main()
