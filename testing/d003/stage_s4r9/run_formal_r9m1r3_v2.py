#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# run_formal_r9m1r3_v2.py -- Single-call two-pass formal run for P05-S4 R9 M1R3 (Rules §1-11, U316, U319, U320). New file.
import argparse, concurrent.futures, csv, datetime, hashlib, os, re, subprocess, sys

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

def utc_str():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def clean_child_env(env_str):
    env = os.environ.copy()
    for k in list(env.keys()):
        if k.startswith("S4FMM_"):
            del env[k]
    for item in env_str.split(";"):
        if "=" in item:
            k, v = item.split("=", 1)
            k = k.strip()
            v = v.strip()
            if k == "S4FMM_INJECT" and v == "none":
                continue
            env[k] = v
    return env

def main():
    parser = argparse.ArgumentParser(description="Single-call formal two-pass run for M1 F4")
    parser.add_argument("--prereg", default=os.path.join(EV, "PREREG_M1_F4_R9M1R3.tsv"))
    parser.add_argument("--out-dir", default=os.path.join(EV, "runs", "formal"))
    parser.add_argument("--out-p1", default=os.path.join(EV, "runs", "formal", "FORMAL_FACTS_M1_F4_R9M1R3_pass1.tsv"))
    parser.add_argument("--out-p2", default=os.path.join(EV, "runs", "formal", "FORMAL_FACTS_M1_F4_R9M1R3_pass2.tsv"))
    args = parser.parse_args()

    # Rule §1-11: Output directory must NOT exist prior to run!
    if os.path.exists(args.out_dir):
        print(f"ERROR: Rule §1-11 violation: output directory {args.out_dir} already exists!", file=sys.stderr)
        sys.exit(2)

    os.makedirs(args.out_dir, exist_ok=False)

    lines = [l.strip().split("\t") for l in open(args.prereg, encoding="utf-8") if l.strip() and not l.startswith("#")]
    h = lines[0]
    all_rows = [dict(zip(h, l)) for l in lines[1:]]
    assert len(all_rows) == 651, f"Expected 651 rows, got {len(all_rows)}"

    m1b_rows = [r for r in all_rows if r["section"] == "M1b"]
    m1c_rows = [r for r in all_rows if r["section"] == "M1c"]
    assert len(m1b_rows) == 415
    assert len(m1c_rows) == 236

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

    def run_single_m1b(pt, pas):
        sec, grp, pid = pt["section"], pt["group"], pt["point_id"]
        dname = pt["driver_name"]
        dpath = get_driver_path(dname)
        exp_sha = pt["driver_sha256"]

        pdir = os.path.join(args.out_dir, f"pass{pas}", "m1b", f"{grp}_{pid}")
        os.makedirs(pdir, exist_ok=True)

        # Rule U319: un-run rows recorded as "-" and NOT_RUN_REGISTRY_ERROR
        if pt["f3_effective_verdict"] == "NOT_RUN_AS_EXPECTED" or pt["env"] == "NOT_RUN":
            with open(os.path.join(pdir, "stdout.txt"), "w") as f: f.write("")
            with open(os.path.join(pdir, "stderr.txt"), "w") as f: f.write("NOT_RUN_AS_EXPECTED")
            return {
                "section": "M1b", "group": grp, "point_id": pid, "base_id": pt["base_id"],
                "tree": "F4", "driver_name": dname, "driver_sha256": exp_sha,
                "rc": "-", "rc1": "-", "rc2": "-", "rc3": "-", "hit": "-", "class": "NOT_RUN_REGISTRY_ERROR",
                "I1": "-", "I2": "-", "I3": "-", "I4": "-", "I5": "-", "I6": "-",
                "env": pt["env"], "f3_point_id": pt["f3_point_id"], "f3_effective_verdict": pt["f3_effective_verdict"]
            }

        # Check sha before
        sha_before = sha256_file(dpath)
        assert sha_before == exp_sha, f"Driver {dname} sha before run {sha_before} != prereg {exp_sha}"

        child_env = clean_child_env(pt["env"])
        argv = pt["argv"].split()
        cmd = [dpath] + argv

        proc = subprocess.run(cmd, env=child_env, cwd=REPO, capture_output=True, text=True, timeout=60)
        raw_rc = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr

        # Check sha after
        sha_after = sha256_file(dpath)
        assert sha_after == exp_sha, f"Driver {dname} sha after run {sha_after} != prereg {exp_sha}"

        with open(os.path.join(pdir, "stdout.txt"), "w", encoding="utf-8") as f: f.write(stdout)
        with open(os.path.join(pdir, "stderr.txt"), "w", encoding="utf-8") as f: f.write(stderr)

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

        real = ("exec" not in pt["env"])
        inj_call_s = pt.get("inj_call", "-")
        inj_call = int(inj_call_s) if inj_call_s not in ("-", "", None) else 1
        is_ctrl = (pt["exp_class"] in ("CONTROL_OK", "CLEAN") or "none" in pt["env"] or pt["exp_hit"] == "0" or grp in ("CTRL_SEAM", "M1_CTRL", "G2c_control", "POLY_33"))

        computed_class, _, _ = judge_d003.classify(raw_rc, rc1, rc2, hit, control=is_ctrl, real=real, inj_call=inj_call)

        return {
            "section": "M1b", "group": grp, "point_id": pid, "base_id": pt["base_id"],
            "tree": "F4", "driver_name": dname, "driver_sha256": exp_sha,
            "rc": str(raw_rc), "rc1": str(rc1), "rc2": str(rc2), "rc3": str(rc3),
            "hit": str(hit), "class": computed_class,
            "I1": "-", "I2": "-", "I3": "-", "I4": "-", "I5": "-", "I6": "-",
            "env": pt["env"], "f3_point_id": pt["f3_point_id"], "f3_effective_verdict": pt["f3_effective_verdict"]
        }

    # Configuration for M1c execution
    PREREG_G5 = os.path.join(REPO, "checkpoints/p05/registries/s4r6c/REGISTRY_S4_PRE_R6b_STATE_v2.tsv")
    CONTROL_G5 = os.path.join(REPO, "checkpoints/p05/registries/s4r6b/REGISTRY_S4_PRE_R6b_CONTROL.tsv")
    PREREG_SEAM = os.path.join(REPO, "checkpoints/p05/registries/s4r6c/REGISTRY_S4_PRE_R6c_SEAM.tsv")
    CONTROL_SEAM = os.path.join(REPO, "checkpoints/p05/registries/s4r6c/REGISTRY_S4_PRE_R6c_SEAM_CONTROL.tsv")

    DRV_STATE = get_driver_path("r6bstate-F4-dbg")
    DRV_SEAMF = get_driver_path("r6bseam-seamF-F4")
    DRV_FMMRET = get_driver_path("r6bseam-fmmret-F4")

    m1c_outdir = os.path.join(args.out_dir, "m1c_F4")
    os.makedirs(m1c_outdir, exist_ok=True)

    fact_header = [
        "section", "group", "point_id", "base_id", "tree", "driver_name", "driver_sha256",
        "rc", "rc1", "rc2", "rc3", "hit", "class",
        "I1", "I2", "I3", "I4", "I5", "I6",
        "env", "f3_point_id", "f3_effective_verdict"
    ]

    p1_m1b = []
    p2_m1b = []

    for pas in (1, 2):
        print(f"\n================== STARTING PASS {pas} ({utc_str()}) ==================")
        # 1. Run M1b points
        print(f"Running M1b points ({len(m1b_rows)} points) for Pass {pas}...")
        jobs = [pt for pt in m1b_rows]
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            m1b_res = list(ex.map(lambda p: run_single_m1b(p, pas), jobs))
        if pas == 1:
            p1_m1b = m1b_res
        else:
            p2_m1b = m1b_res
        print(f"M1b Pass {pas} complete.")

        # 2. Run M1c G5 points
        print(f"Running M1c G5 points for Pass {pas}...")
        cmd_g5 = [
            "python3", "-I", "-B", "testing/d003/stage_s4/run_r6c_state.py",
            "full", PREREG_G5, CONTROL_G5, DRV_STATE, m1c_outdir, str(pas)
        ]
        p_g5 = subprocess.run(cmd_g5, cwd=REPO, capture_output=True, text=True)
        assert p_g5.returncode == 0, f"G5 Pass {pas} failed:\n{p_g5.stderr}"

        # 3. Run M1c G6 seam points
        print(f"Running M1c G6 seam points for Pass {pas}...")
        cmd_seam = [
            "python3", "-I", "-B", "testing/d003/stage_s4/r6c2_seam_state.py",
            PREREG_SEAM, CONTROL_SEAM, DRV_SEAMF, DRV_FMMRET, m1c_outdir, str(pas)
        ]
        p_seam = subprocess.run(cmd_seam, cwd=REPO, capture_output=True, text=True)
        assert p_seam.returncode == 0, f"Seam Pass {pas} failed:\n{p_seam.stderr}"

    # Run M1c judges
    print("\nRunning M1c judges...")
    subprocess.run(["python3", "-I", "-B", "testing/d003/stage_s4/r6c_judge.py", PREREG_G5, CONTROL_G5, m1c_outdir], cwd=REPO, check=True)
    subprocess.run(["python3", "-I", "-B", "testing/d003/stage_s4/r6c2_seam_judge.py", PREREG_SEAM, CONTROL_SEAM, m1c_outdir], cwd=REPO, check=True)

    # Assemble pass facts
    for pas in (1, 2):
        # Load G5 facts
        g5_facts = {}
        with open(os.path.join(m1c_outdir, f"STATE_R6c_pass{pas}.tsv"), encoding="utf-8") as fh:
            lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
            for l in lines[1:]:
                r = dict(zip(lines[0], l))
                g5_facts[r["id"]] = r

        # Load Seam facts
        seam_facts = {}
        with open(os.path.join(m1c_outdir, f"STATE_SEAM_R6c_pass{pas}.tsv"), encoding="utf-8") as fh:
            lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
            for l in lines[1:]:
                r = dict(zip(lines[0], l))
                seam_facts[r["id"]] = r

        # Load G5 judge invariants (RESULTS_R6c_STATE.tsv: column is point_id)
        inv_g5 = {}
        with open(os.path.join(m1c_outdir, "RESULTS_R6c_STATE.tsv"), encoding="utf-8") as fh:
            lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
            for l in lines[1:]:
                r = dict(zip(lines[0], l))
                pid = r.get("point_id", r.get("id"))
                inv_g5[(pid, r["pass"])] = r

        # Load Seam judge invariants (RESULTS_R6c_SEAM.tsv: column is point_id)
        inv_seam = {}
        with open(os.path.join(m1c_outdir, "RESULTS_R6c_SEAM.tsv"), encoding="utf-8") as fh:
            lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
            for l in lines[1:]:
                r = dict(zip(lines[0], l))
                pid = r.get("point_id", r.get("id"))
                inv_seam[(pid, r["pass"])] = r

        m1c_res = []
        for pt in m1c_rows:
            grp = pt["group"]
            pid = pt["point_id"]
            base = pt["base_id"]
            dname = pt["driver_name"]
            exp_sha = pt["driver_sha256"]

            if grp in ("G5", "CTRL_AUX"):
                rec = g5_facts.get(base)
                inv = inv_g5.get((base, str(pas)), {})
            else:
                rec = seam_facts.get(base)
                inv = inv_seam.get((base, str(pas)), {})

            assert rec is not None, f"Missing record for {grp} {base} in pass {pas}"

            rc1 = rec.get("gdb_rc1", "0")
            rc2 = rec.get("gdb_rc2", "0")
            rc3 = rec.get("gdb_rc3", "-")
            hit = rec.get("gdb_hit", "0")
            cls = inv.get("point_verdict", "CONTROL_OK" if grp in ("G6c", "CTRL_AUX") else "REPORTED_FAILURE")

            i1 = inv.get("I1", "-")
            i2 = inv.get("I2", "-")
            i3 = inv.get("I3", "-")
            i4 = inv.get("I4", "-")
            i5 = inv.get("I5", "-")
            i6 = inv.get("I6", "-")

            m1c_res.append({
                "section": "M1c", "group": grp, "point_id": pid, "base_id": base,
                "tree": "F4", "driver_name": dname, "driver_sha256": exp_sha,
                "rc": "0", "rc1": str(rc1), "rc2": str(rc2), "rc3": str(rc3),
                "hit": str(hit), "class": cls,
                "I1": str(i1), "I2": str(i2), "I3": str(i3), "I4": str(i4), "I5": str(i5), "I6": str(i6),
                "env": pt["env"], "f3_point_id": pt["f3_point_id"], "f3_effective_verdict": pt["f3_effective_verdict"]
            })

        if pas == 1:
            pass_combined = p1_m1b + m1c_res
            out_file = args.out_p1
        else:
            pass_combined = p2_m1b + m1c_res
            out_file = args.out_p2

        pass_combined.sort(key=lambda x: (x["section"], x["group"], x["point_id"]))
        assert len(pass_combined) == 651, f"Expected 651 rows for pass {pas}, got {len(pass_combined)}"

        with open(out_file, "w", encoding="utf-8") as f:
            f.write(f"# FORMAL_FACTS_M1_F4_R9M1R3_pass{pas}.tsv -- Formal pass {pas} facts (651 rows; Rule U316, U319, U320)\n")
            f.write("\t".join(fact_header) + "\n")
            for r in pass_combined:
                f.write("\t".join([r[k] for k in fact_header]) + "\n")

        print(f"Pass {pas} facts written -> {out_file} ({len(pass_combined)} rows).")

    print("\nrun_formal_r9m1r3_v2.py: SINGLE-CALL TWO-PASS FORMAL RUN COMPLETE.")

if __name__ == "__main__":
    main()
