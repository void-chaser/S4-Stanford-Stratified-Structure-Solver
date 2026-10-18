#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# run_smoke_r9m1r2.py -- Smoke test execution for P05-S4 R9 M1R2 (Step S-G, Rule U316). New file.
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
    for item in env_str.split(";"):
        if "=" in item:
            k, v = item.split("=", 1)
            env[k.strip()] = v.strip()
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
        # Search known paths
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
        rc = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr

        # 3. Verify driver sha after run
        sha_after = sha256_file(drv_exe)
        assert sha_after == exp_sha, f"Driver {drv_name} sha after run {sha_after} != prereg {exp_sha}"

        # 4. Parse facts
        rc1, rc2, rc3, hit = 0, 0, "-", 0
        m_rc1 = re.search(r"RC1=(-?\d+)", stderr)
        if m_rc1: rc1 = int(m_rc1.group(1))
        m_rc2 = re.search(r"RC2=(-?\d+)", stderr)
        if m_rc2: rc2 = int(m_rc2.group(1))
        m_rc3 = re.search(r"RC3=(-?\d+)", stderr)
        if m_rc3: rc3 = int(m_rc3.group(1))
        m_hit = re.search(r"HITCOUNT=(\d+)", stderr)
        if m_hit: hit = int(m_hit.group(1))

        # Classify
        real = r.get("real", "1") != "0"
        inj_call_s = r.get("inj_call", "-")
        inj_call = int(inj_call_s) if inj_call_s not in ("-", "", None) else None
        is_ctrl = (grp in ("CTRL_SEAM", "G2c_control", "M1_CTRL", "G6c", "CTRL_AUX"))
        cls, reason = judge_d003.classify(rc, rc1, rc2, hit, control=is_ctrl, real=real, inj_call=inj_call)

        # 5. Check against expectation
        exp_eff = r["f3_effective_verdict"]
        diff_fields = []
        if exp_eff == "NOT_RUN_AS_EXPECTED":
            v = "NOT_RUN_AS_EXPECTED"
        elif exp_eff == "NOT_REACHED_AS_EXPECTED":
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
                if cls != exp_pv:
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

    print(f"Smoke test PASSED ({len(smoke_results)}/{len(smoke_results)} MATCH).")

if __name__ == "__main__":
    main()
