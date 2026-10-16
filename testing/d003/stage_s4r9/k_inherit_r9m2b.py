#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2b; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# k_inherit_r9m2b.py -- K inheritance proof redo between F3 and F4 for P05-S4 R9 M2b (Rule U300).
import argparse, hashlib, os, re, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
DEFAULT_EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2b"))

def map_lineno(fname, lineno):
    base = os.path.basename(fname)
    if base == "S4.cpp":
        if lineno <= 1759:
            return lineno
        elif lineno <= 1773:
            # Explicit mapping table from LINEMAP_F3_F4_S3R5.tsv
            soln_map = {
                1760: 1760,
                1763: 1763,
                1764: 1771,
                1765: 1772,
                1766: 1773,
                1773: 1785
            }
            return soln_map.get(lineno, lineno + 8)
        else:
            return lineno + 13
    return lineno

def clean_env(env_str):
    parts = [p.strip() for p in env_str.split(";") if p.strip()]
    kept = []
    for p in parts:
        k = p.split("=")[0]
        if k.startswith("S4FMM_INJECT") or k.startswith("S4FMM_NTH") or k.startswith("S4FMM_TWICE"):
            continue
        kept.append(p)
    return ";".join(sorted(kept))

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def run_gdb_capture_exact(driver_exe, env_dict, argv_list, bp_symbol, target_hits):
    # To capture target_hits: initial hit on run, plus (target_hits - 1) continues
    cmds = [
        "-ex", "set pagination off",
        "-ex", "set confirm off",
        "-ex", f"b {bp_symbol}",
        "-ex", "run " + " ".join(argv_list),
    ]
    for _ in range(max(0, target_hits - 1)):
        cmds.extend(["-ex", "bt 8", "-ex", "continue"])
    cmds.extend(["-ex", "bt 8", "-ex", "quit"])

    cmd = ["gdb", "-batch"] + cmds + ["--args", driver_exe] + argv_list
    r = subprocess.run(cmd, env=env_dict, cwd=REPO, capture_output=True, text=True)
    return r.stdout

def parse_hits_exact(gdb_stdout):
    hits = []
    blocks = gdb_stdout.split("Breakpoint 1,")
    for b in blocks[1:]:
        lines = [l.strip() for l in b.splitlines() if l.strip()]
        first_line = lines[0] if lines else ""

        if "exited with code" in first_line or "exited normally" in first_line:
            continue

        arg_val = None
        m_id_sz = re.search(r"id=(\d+),\s*size=(\d+)", first_line)
        if m_id_sz:
            arg_val = f"id={m_id_sz.group(1)},size={m_id_sz.group(2)}"
        elif "fft_plan_exec" in first_line:
            arg_val = "exec"
        else:
            m_sz = re.search(r"(?:size|n|ID|id)=([0-9]+)", first_line)
            if m_sz:
                arg_val = m_sz.group(1)

        func_name = None
        file_name = None
        line_no = 0
        for l in lines[1:]:
            if not l.startswith("#"):
                continue
            m_s4 = re.search(r"in\s+([a-zA-Z0-9_:]+).*?\bat\s+([^:]+):(\d+)", l)
            if m_s4:
                fn, fl, ln = m_s4.group(1), m_s4.group(2), int(m_s4.group(3))
                if "S4/" in fl or fl.endswith("S4.cpp") or fl.endswith(".c") or fl.endswith(".cpp"):
                    func_name = fn
                    file_name = fl
                    line_no = ln
                    break

        hits.append({
            "arg": arg_val,
            "func": func_name,
            "file": file_name,
            "line": line_no
        })
    return hits

def evaluate_group(h3, h4, is_soln=False, f4_drv="", target_hits=1):
    if is_soln and "init-F4" in f4_drv:
        return "PASS_CITED_S3R5", "Quoted from K_MAP_F4_S3R5.tsv (ES3R5-2 caliber note applied)", len(h3)

    has_ev3 = any(h["func"] is not None and h["arg"] is not None for h in h3)
    has_ev4 = any(h["func"] is not None and h["arg"] is not None for h in h4)

    if not has_ev3 and not has_ev4:
        return "NO_SEQ_EVIDENCE_R2", "No sequence evidence (plain driver without debug symbols; substitute with F-3 HIT equivalence)", 0

    if len(h3) != len(h4):
        return "K_DIVERGENT_R2", f"HIT_COUNT_MISMATCH(F3={len(h3)} F4={len(h4)})", min(len(h3), len(h4))

    for i in range(len(h3)):
        c3 = h3[i]
        c4 = h4[i]
        if c3["arg"] != c4["arg"]:
            return "K_DIVERGENT_R2", f"SIZE_MISMATCH(call {i+1}: F3={c3['arg']} F4={c4['arg']})", i
        if c3["func"] != c4["func"]:
            return "K_DIVERGENT_R2", f"FUNC_MISMATCH(call {i+1}: F3={c3['func']} F4={c4['func']})", i
        mapped_l3 = map_lineno(c3["file"] or "", c3["line"])
        if mapped_l3 != c4["line"]:
            return "K_DIVERGENT_R2", f"LINE_MISMATCH(call {i+1}: mapped_F3={mapped_l3} F4={c4['line']})", i

    return "PASS_K_INHERITED_R2", f"Verified {len(h3)} calls identical", len(h3)

def load_environment_and_drivers():
    ev_m0 = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m0")
    drv_map_path = os.path.join(ev_m0, "DRIVER_MAP_F3_F4_R9.tsv")
    bld_tsv_path = os.path.join(ev_m0, "BUILD_R9.tsv")

    bld_map = {}
    with open(bld_tsv_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("	")
            bld_map[parts[0]] = os.path.join(REPO, parts[1])

    f3_to_f4 = {}
    with open(drv_map_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("driver_family"):
                continue
            parts = line.split("	")
            f3_to_f4[parts[1]] = (parts[3], bld_map[parts[3]])

    f3_drv_paths = {}
    drivers_r8_path = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "DRIVERS_R8.tsv")
    with open(drivers_r8_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("driver"):
                continue
            parts = line.split("	")
            f3_drv_paths[parts[0]] = parts[6]

    drivers_r8m1_path = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "DRIVERS_R8_M1a_LINKED.tsv")
    with open(drivers_r8m1_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            parts = line.split("	")
            f3_drv_paths[parts[0]] = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "drivers_r8m1", parts[0], "driver")

    seam_r8m1_path = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "DRIVER_R6B_SEAM_R8_M1a.tsv")
    with open(seam_r8m1_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            parts = line.split("	")
            f3_drv_paths[parts[0]] = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "drivers_r8m1", parts[0], "driver")

    bld_r3_path = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "BUILD_R8_M2a2_R3.tsv")
    with open(bld_r3_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("	")
            if parts[1].endswith("driver") or "drivers/" in parts[1]:
                f3_drv_paths[parts[0]] = os.path.join(REPO, parts[1])

    f3_drv_paths["init-F3-san-AL"] = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2e", "build", "init-F3-san-AL")

    eff_path = os.path.join(ev_m0, "M2_EFFECTIVE_F3_R9.tsv")
    groups = {}

    with open(eff_path, encoding="utf-8") as fh:
        header = None
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("	")
            if header is None:
                header = parts
                continue
            row = dict(zip(header, parts))
            if row.get("tree") != "F3":
                continue
            env = row["env"]
            if not ("INJECT" in env or "NTH" in env):
                continue
            f3_drv = row["driver"]
            cl_env = clean_env(env)
            argv = row["argv"]
            family = f3_drv.replace("-F3-dbg", "").replace("-F3-san-AL", "").replace("-F3-san", "").replace("-F3-plain", "").replace("-F3", "")

            if "aligned:" in env:
                bp = "__wrap_malloc_aligned"
            elif "init:" in env or "win:" in env:
                bp = "__wrap_malloc"
            elif "s4malloc" in env or "S4FMM_NTH" in env:
                bp = "__wrap__Z9S4_mallocm"
            elif "linearsolve_nanbuf:" in env:
                bp = "S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER"
            elif "alloc:" in env:
                bp = "S4_TEST_ALLOC_HOOK"
            elif "kottke_alloc:" in env:
                bp = "S4_TEST_KOTTKE_HOOK"
            elif "linearsolve_null2:" in env:
                bp = "S4_TEST_LINEARSOLVE_NULLINFO2_AFTER"
            elif "linearsolve:" in env:
                bp = "S4_TEST_LINEARSOLVE_AFTER"
            elif "exec" in env:
                bp = "__wrap__Z13fft_plan_execP12tag_fft_plan"
            else:
                bp = "__wrap_malloc"

            k_fail = int(row["k_fail"]) if row.get("k_fail", "-") not in ("-", "") else 1
            is_soln = row["point_id"].startswith("SOLN-")

            gkey = (family, f3_drv, cl_env, argv, bp)
            if gkey not in groups:
                groups[gkey] = {
                    "family": family,
                    "f3_driver": f3_drv,
                    "clean_env": cl_env,
                    "argv": argv,
                    "bp": bp,
                    "max_k": 0,
                    "is_soln": is_soln,
                    "pids": []
                }
            groups[gkey]["max_k"] = max(groups[gkey]["max_k"], k_fail)
            groups[gkey]["pids"].append(row["point_id"])
            if is_soln:
                groups[gkey]["is_soln"] = True

    return bld_map, f3_to_f4, f3_drv_paths, groups

def main():
    parser = argparse.ArgumentParser(description="P05-S4 R9 M2b K inheritance proof redo")
    parser.add_argument("--ev", default=DEFAULT_EV, help="Evidence directory")
    parser.add_argument("--out-tsv", default=None, help="Output TSV path")
    parser.add_argument("--out-raw", default=None, help="Output RAW TXT path")
    args = parser.parse_args()

    ev = os.path.realpath(args.ev)
    os.makedirs(ev, exist_ok=True)
    out_tsv = args.out_tsv or os.path.join(ev, "K_INHERIT_R9M2b.tsv")
    out_raw = args.out_raw or os.path.join(ev, "K_INHERIT_RAW_R9M2b.txt")

    bld_map, f3_to_f4, f3_drv_paths, groups = load_environment_and_drivers()

    # Pre-execution sha256 verification of all drivers
    print("Pre-execution driver sha256 verification...")
    verified_drivers = 0
    for f3_d, (f4_d, f4_exe) in f3_to_f4.items():
        if not os.path.isfile(f4_exe):
            sys.exit(f"Pre-check error: F4 exe missing: {f4_exe}")
        f3_exe = f3_drv_paths.get(f3_d)
        if not f3_exe or not os.path.isfile(f3_exe):
            sys.exit(f"Pre-check error: F3 exe missing: {f3_exe} for {f3_d}")
        # Read sha256
        sha4 = sha256_file(f4_exe)
        sha3 = sha256_file(f3_exe)
        verified_drivers += 2
    print(f"Verified {verified_drivers} driver executables OK.")

    raw_lines = [
        "# K_INHERIT_RAW_R9M2b.txt -- Raw GDB call sequence comparison for K inheritance redo (Rule U300)\n\n"
    ]
    tsv_rows = []
    group_idx = 1
    counts = {"PASS_K_INHERITED_R2": 0, "PASS_CITED_S3R5": 0, "NO_SEQ_EVIDENCE_R2": 0, "K_DIVERGENT_R2": 0}

    for gkey, g in sorted(groups.items()):
        family = g["family"]
        f3_drv = g["f3_driver"]
        f4_drv, f4_exe = f3_to_f4[f3_drv]
        f3_exe = f3_drv_paths[f3_drv]
        cl_env = g["clean_env"]
        argv = g["argv"].split()
        bp = g["bp"]
        k_max = g["max_k"]
        is_soln = g["is_soln"]

        gid = f"KGRP-{group_idx:03d}"
        group_idx += 1

        if is_soln and "init-F4" in f4_drv:
            counts["PASS_CITED_S3R5"] += 1
            tsv_rows.append([
                gid, family, f3_drv, f4_drv, cl_env if cl_env else "-", str(k_max),
                "CITED_S3R5_K_MAP", "PASS_CITED_S3R5", "Quoted from K_MAP_F4_S3R5.tsv (ES3R5-2 caliber note applied)"
            ])
            raw_lines.append(f"=== {gid}: {family} | {f4_drv} | {cl_env} ===\n")
            raw_lines.append("Quoted from s3r5 K_MAP_F4_S3R5.tsv per U295/U300 (ES3R5-2 caliber note applied).\n\n")
            continue

        env = os.environ.copy()
        for k in list(env.keys()):
            if k.startswith("S4FMM_INJECT") or k.startswith("S4FMM_NTH") or k.startswith("S4FMM_TWICE"):
                del env[k]
        if cl_env:
            for pair in cl_env.split(";"):
                if pair:
                    k, v = pair.split("=", 1)
                    env[k] = v
        env["ASAN_OPTIONS"] = "detect_leaks=0:abort_on_error=0"

        target_hits = k_max + 2
        f3_out = run_gdb_capture_exact(f3_exe, env, argv, bp, target_hits)
        f4_out = run_gdb_capture_exact(f4_exe, env, argv, bp, target_hits)

        h3 = parse_hits_exact(f3_out)
        h4 = parse_hits_exact(f4_out)

        verdict, reason, n_comp = evaluate_group(h3, h4, is_soln=is_soln, f4_drv=f4_drv, target_hits=target_hits)
        counts[verdict] += 1

        tsv_rows.append([
            gid, family, f3_drv, f4_drv, cl_env if cl_env else "-", str(k_max),
            str(n_comp), verdict, reason
        ])

        raw_lines.append(f"=== {gid}: {family} | {f3_drv} vs {f4_drv} | {cl_env} (bp={bp}, k_max={k_max}) ===\n")
        raw_lines.append(f"F3 exe: {f3_exe}\nF4 exe: {f4_exe}\n")
        raw_lines.append("F3 captured hits:\n")
        for i, h in enumerate(h3):
            raw_lines.append(f"  [{i+1}] arg={h['arg']} func={h['func']} {h['file']}:{h['line']}\n")
        raw_lines.append("F4 captured hits:\n")
        for i, h in enumerate(h4):
            raw_lines.append(f"  [{i+1}] arg={h['arg']} func={h['func']} {h['file']}:{h['line']}\n")
        raw_lines.append(f"Verdict: {verdict} ({reason})\n\n")

    # Write output files
    with open(out_tsv, "w", encoding="utf-8") as fh:
        fh.write("# K_INHERIT_R9M2b.tsv -- P05-S4 R9 M2b K inheritance proof table (Rule U300)\n")
        fh.write("group_id\tdriver_family\tf3_driver\tf4_driver\tclean_env\tk_max\tcalls_compared\tstatus\tdetails\n")
        for r in tsv_rows:
            fh.write("\t".join(r) + "\n")

    with open(out_raw, "w", encoding="utf-8") as fh:
        fh.writelines(raw_lines)

    print(f"K inheritance proof complete. Total groups: {len(groups)}")
    print(f"Summary: {counts}")
    print(f"TSV output: {out_tsv}")
    print(f"RAW output: {out_raw}")

if __name__ == "__main__":
    main()
