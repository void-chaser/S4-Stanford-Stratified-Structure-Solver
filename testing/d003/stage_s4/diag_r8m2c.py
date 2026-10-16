#!/usr/bin/env python3
# diag_r8m2c.py -- P05-S4 R8 M2c diagnostic execution (INFLUENCED).
# Output strictly under EV/diag/.
#  1. Diagnostic for REP-INIT-*-C on init-F3-san (k=5 for closed2d-ng1, k=6 for fft-ng5, k=6 for kottke-ng5)
#  2. Diagnostic for SOLN probes (1763, 1764, 1765) on init-F3-dbg, init-B-dbg, init-F3-san
#  3. Diagnostic for M2-06 under GDB (location of return 20 and NaN reachability)
import os, subprocess, sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2c")
EV = os.environ.get("EV", os.path.join(REPO, EV_REL))
DIAG_DIR = os.path.join(EV, "diag")

DRV_INIT_F3_DBG = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build_R3", "drivers", "init-F3-dbg")
DRV_INIT_F3_SAN = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build_R3", "drivers", "init-F3-san")
DRV_INIT_B_DBG = os.path.join(EV, "build", "init-B-dbg")
DRV_NAN_F3 = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build_R3", "drivers", "nan-F3")

def run_cmd(cmd, env, out_prefix):
    os.makedirs(os.path.dirname(out_prefix), exist_ok=True)
    res = subprocess.run(cmd, env=env, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    with open(out_prefix + ".stdout", "w", encoding="utf-8") as fh:
        fh.write(res.stdout)
    with open(out_prefix + ".stderr", "w", encoding="utf-8") as fh:
        fh.write(res.stderr)
    with open(out_prefix + ".exitcode", "w", encoding="utf-8") as fh:
        fh.write(f"{res.returncode}\n")
    return res.returncode, res.stdout, res.stderr

def diag_rep_init_san():
    print("=== Diag 1: REP-INIT-*-C on init-F3-san ===")
    cases = [
        ("closed2d-ng1", "closed2d", "1", "5"),
        ("fft-ng5", "fft", "5", "6"),
        ("kottke-ng5", "kottke", "5", "6"),
    ]
    results = []
    for cname, mode, ng, k in cases:
        out_pfx = os.path.join(DIAG_DIR, "rep_init_san", f"{cname}_k{k}")
        env = os.environ.copy()
        env["FMM_MODE"] = mode
        env["S4FMM_NG"] = ng
        env["S4FMM_INJECT"] = f"init:{k}"
        env["ASAN_OPTIONS"] = f"detect_leaks=0:abort_on_error=0:log_path={out_pfx}.asan.log"
        env["UBSAN_OPTIONS"] = f"abort_on_error=0:log_path={out_pfx}.ubsan.log"
        rc, out, err = run_cmd([DRV_INIT_F3_SAN, "pattern", "both", "4", "3"], env, out_pfx)
        hit = ("S4FMM HIT real malloc failure" in err)
        print(f"  {cname} init:{k} -> rc={rc}, hit={hit}")
        results.append((cname, k, rc, hit))
    return results

def diag_soln_probes():
    print("\n=== Diag 2: SOLN probes (1763, 1764, 1765) ===")
    # Format: (driver_label, driver_path, combo_name, mode, ng, is_san, k_1763, k_1764, k_1765)
    matrix = [
        ("init-F3-dbg", DRV_INIT_F3_DBG, "closed2d-ng1", "closed2d", "1", False, 9, 10, 11),
        ("init-F3-dbg", DRV_INIT_F3_DBG, "fft-ng5", "fft", "5", False, 10, 11, 12),
        ("init-F3-dbg", DRV_INIT_F3_DBG, "kottke-ng5", "kottke", "5", False, 10, 11, 12),
        ("init-B-dbg", DRV_INIT_B_DBG, "closed2d-ng1", "closed2d", "1", False, 9, 10, 11),
        ("init-B-dbg", DRV_INIT_B_DBG, "fft-ng5", "fft", "5", False, 10, 11, 12),
        ("init-B-dbg", DRV_INIT_B_DBG, "kottke-ng5", "kottke", "5", False, 10, 11, 12),
        ("init-F3-san", DRV_INIT_F3_SAN, "closed2d-ng1", "closed2d", "1", True, 7, 0, 8),
        ("init-F3-san", DRV_INIT_F3_SAN, "fft-ng5", "fft", "5", True, 8, 0, 9),
        ("init-F3-san", DRV_INIT_F3_SAN, "kottke-ng5", "kottke", "5", True, 8, 0, 9),
    ]
    results = []
    for dlabel, dpath, cname, mode, ng, is_san, k_1763, k_1764, k_1765 in matrix:
        for site_label, k_val in [("1763", k_1763), ("1764", k_1764), ("1765", k_1765)]:
            if k_val == 0:
                print(f"  {dlabel} {cname} site={site_label} -> skipped (not reachable via outside malloc in san)")
                results.append((dlabel, cname, site_label, 0, "NOT_REACHABLE", False))
                continue
            out_pfx = os.path.join(DIAG_DIR, "soln_probes", f"{dlabel}_{cname}_{site_label}_k{k_val}")
            env = os.environ.copy()
            env["FMM_MODE"] = mode
            env["S4FMM_NG"] = ng
            env["S4FMM_INJECT"] = f"init:{k_val}"
            if is_san:
                env["ASAN_OPTIONS"] = f"detect_leaks=0:abort_on_error=0:log_path={out_pfx}.asan.log"
                env["UBSAN_OPTIONS"] = f"abort_on_error=0:log_path={out_pfx}.ubsan.log"
            rc, out, err = run_cmd([dpath, "pattern", "both", "4", "3"], env, out_pfx)
            hit = ("S4FMM HIT real malloc failure" in err)
            print(f"  {dlabel} {cname} site={site_label} (k={k_val}) -> rc={rc}, hit={hit}")
            results.append((dlabel, cname, site_label, k_val, rc, hit))
    return results

def diag_m206():
    print("\n=== Diag 3: M2-06 on nan-F3 under GDB ===")
    out_pfx = os.path.join(DIAG_DIR, "m206", "m206_diag")
    gdb_script = os.path.join(DIAG_DIR, "m206", "m206_trace.gdb")
    os.makedirs(os.path.dirname(gdb_script), exist_ok=True)
    with open(gdb_script, "w") as fh:
        fh.write("""set pagination off
set confirm off
break S4/S4.cpp:2445
commands
silent
printf "M206_BP at line 2445\\n"
info line
continue
end
break S4/fmm/fmm_closed.cpp:244
commands
silent
printf "M206_BP at fmm_closed.cpp:244\\n"
info line
continue
end
run pattern both 4 3
quit
""")
    env = os.environ.copy()
    env["FMM_MODE"] = "tensor"
    env["S4FMM_NG"] = "5"
    env["S4FMM_INJECT"] = "linearsolve_nanbuf:244:1"
    rc, out, err = run_cmd(["gdb", "-batch", "-x", gdb_script, "--args", DRV_NAN_F3, "pattern", "both", "4", "3"], env, out_pfx)
    print(f"  nan-F3 under GDB -> rc={rc}")
    print(f"  stderr snippet: {err.strip()[:150]}")
    return rc, out, err

def main():
    os.makedirs(DIAG_DIR, exist_ok=True)
    diag_rep_init_san()
    diag_soln_probes()
    diag_m206()
    print("\nAll diagnostics completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
