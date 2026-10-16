#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m0; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# run_m2_r9.py -- P05-S4 R9 runner and command planner.
# Supports --dry-run and --execute.
# Options: --prereg, --ev, --out-plan, --pass, --subset, --dry-run, --execute.
# Enforces:
#  - Driver and gdb script sha verification before running; any IDENTITY_FAIL rejects execution.
#  - Clears inherited FMM_*, S4FMM_*, ASAN_*, UBSAN_*, S4_FAIL_ALLOC_* environment variables before execution.
#  - Expands $EV to absolute path in san_options and asserts no '$' character in any planned command.
#  - dbg rows are executed in pairs per U256: (a) in gdb -> gdb.log & dump, (b) without gdb -> stdout/stderr/exitcode.
#  - Output directory must not exist (or be empty) when executing; refuses overwrite.
#  - Command timeout: 600s.
import argparse
import csv
import hashlib
import os
import shutil
import subprocess
import sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
TIMEOUT_S = 600


def get_driver_search_dirs(ev_dir=None):
    dirs = []
    if ev_dir:
        dirs.append(os.path.join(ev_dir, "build"))
        dirs.append(os.path.join(ev_dir, "build", "san"))
    dirs.extend([
        os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m0", "build"),
        os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s3r5", "build"),
        os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2c", "build"),
        os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2e", "build"),
        os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2d", "build"),
        os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2c", "build"),
        os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2b", "build"),
        os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build_R3", "drivers"),
        os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build", "B-dbg"),
        os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build", "san"),
        os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build"),
        os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "drivers_r8"),
        os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "drivers_r8m1"),
        os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r7", "drivers_r7"),
    ])
    return dirs


def sha256_file(path):
    if not path or not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def find_driver_binary(name, ev_dir=None):
    """Find binary executable for given driver name across search directories."""
    for d in get_driver_search_dirs(ev_dir):
        p1 = os.path.join(d, name)
        if os.path.isfile(p1) and os.access(p1, os.X_OK):
            return p1
        p2 = os.path.join(d, name, "driver")
        if os.path.isfile(p2) and os.access(p2, os.X_OK):
            return p2
    return None


def clean_base_env():
    """Return a clean copy of os.environ without any FMM_*, S4FMM_*, ASAN_*, UBSAN_*, S4_FAIL_ALLOC_* variables."""
    cleaned = {}
    for k, v in os.environ.items():
        if k.startswith("FMM_") or k.startswith("S4FMM_") or k.startswith("ASAN_") or k.startswith("UBSAN_") or k.startswith("S4_FAIL_ALLOC"):
            continue
        cleaned[k] = v
    return cleaned


def build_env_dict(r, pas, pid, ev_abs, dump_dir):
    """Construct process environment dictionary, expanding $EV and setting dump dir."""
    env = clean_base_env()
    env["S4FMM_DUMP_DIR"] = dump_dir

    if r.get("env") not in (None, "", "-"):
        for tok in r["env"].split(";"):
            tok = tok.strip()
            if not tok:
                continue
            if "=" in tok:
                k, v = tok.split("=", 1)
                env[k] = v

    if r.get("san_options") not in (None, "", "-"):
        san_opts = r["san_options"].replace("{pass}", str(pas)).replace("{point_id}", pid)
        san_opts = san_opts.replace("$EV", ev_abs)
        for tok in san_opts.split(";"):
            tok = tok.strip()
            if not tok:
                continue
            if "=" in tok:
                k, v = tok.split("=", 1)
                env[k] = v

    return env


def env_dict_to_string(env_dict):
    """Convert only the point-specific environment tokens to a space-separated string."""
    tokens = []
    for k in sorted(env_dict.keys()):
        if k in ("S4FMM_DUMP_DIR",) or k.startswith("FMM_") or k.startswith("S4FMM_") or k.startswith("ASAN_") or k.startswith("UBSAN_") or k.startswith("S4_FAIL_ALLOC"):
            tokens.append(f"{k}={env_dict[k]}")
    return " ".join(tokens)


def main():
    parser = argparse.ArgumentParser(description="P05-S4 M2 runner v5")
    parser.add_argument("--prereg", required=True, help="Path to effective preregistration table")
    parser.add_argument("--ev", required=True, help="Evidence directory root (for dumps, runs, logs)")
    parser.add_argument("--out-plan", required=True, help="Output COMMAND_PLAN tsv path")
    parser.add_argument("--pass", dest="pass_filter", type=int, choices=[1, 2], default=None,
                        help="Filter by pass 1 or 2 (default: both passes)")
    parser.add_argument("--subset", default=None, help="Path to subset file listing point_ids")
    parser.add_argument("--dry-run", action="store_true", help="Only plan commands without executing")
    parser.add_argument("--execute", action="store_true", help="Execute the planned commands")

    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        sys.exit("FATAL: Either --dry-run or --execute must be specified.")
    if args.dry_run and args.execute:
        sys.exit("FATAL: Cannot specify both --dry-run and --execute.")

    ev_abs = os.path.abspath(args.ev)

    # Read prereg
    with open(args.prereg, encoding="utf-8") as fh:
        prereg_rows = list(csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"))

    # Subset filter
    if args.subset:
        subset_pids = set()
        with open(args.subset, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                subset_pids.add(line.split("\t")[0])
        prereg_rows = [r for r in prereg_rows if r["point_id"] in subset_pids]

    passes = [args.pass_filter] if args.pass_filter else [1, 2]

    plan_headers = [
        "command_id", "point_id", "pass", "item", "driver_name", "driver_path",
        "driver_sha_status", "gdb_script", "gdb_script_sha_status",
        "identity_status", "env_as_run", "full_command_a", "full_command_b",
        "dump_dir", "stdout_file", "stderr_file", "exitcode_file", "gdb_log_file", "timeout_s"
    ]

    planned_items = []
    identity_fails = 0
    cmd_id = 1

    for pas in passes:
        for r in prereg_rows:
            pid = r["point_id"]
            item = r.get("item", "")
            drv_name = r["driver"]
            exp_drv_sha = r["driver_sha256"]
            gdb_script_rel = r.get("gdb_script", "-")
            exp_gdb_sha = r.get("gdb_script_sha256", "-")

            # 1. Driver verification
            drv_path = find_driver_binary(drv_name, ev_abs)
            act_drv_sha = sha256_file(drv_path) if drv_path else None
            if act_drv_sha == exp_drv_sha:
                drv_status = "DRIVER_SHA_PASS"
            else:
                drv_status = f"DRIVER_SHA_FAIL({act_drv_sha}!=exp)"
                identity_fails += 1

            # 2. GDB script verification
            if gdb_script_rel not in (None, "", "-"):
                gdb_path = os.path.join(REPO, gdb_script_rel) if not os.path.isabs(gdb_script_rel) else gdb_script_rel
                act_gdb_sha = sha256_file(gdb_path)
                if act_gdb_sha == exp_gdb_sha:
                    gdb_status = "GDB_SHA_PASS"
                else:
                    gdb_status = f"GDB_SHA_FAIL({act_gdb_sha}!=exp)"
                    identity_fails += 1
            else:
                gdb_path = "-"
                gdb_status = "N/A"

            ident_status = "IDENTITY_PASS" if (drv_status == "DRIVER_SHA_PASS" and gdb_status in ("GDB_SHA_PASS", "N/A")) else "IDENTITY_FAIL"

            # 3. Directories and files
            pt_run_dir = os.path.join(ev_abs, "run", f"pass{pas}", pid)
            dump_dir = pt_run_dir
            stdout_f = os.path.join(pt_run_dir, "stdout.txt")
            stderr_f = os.path.join(pt_run_dir, "stderr.txt")
            exitcode_f = os.path.join(pt_run_dir, "exitcode.txt")
            gdb_log_f = os.path.join(pt_run_dir, "gdb.log")

            # 4. Environment
            env_dict = build_env_dict(r, pas, pid, ev_abs, dump_dir)
            env_as_run = env_dict_to_string(env_dict)

            # Assert no unexpanded '$' in environment or arguments
            if "$" in env_as_run:
                sys.exit(f"FATAL: Command plan contains unexpanded '$' in env for {pid}: {env_as_run}")

            # 5. Full commands
            argv = r.get("argv", "")
            drv_target = os.path.relpath(drv_path, REPO) if drv_path else drv_name
            has_gdb = (gdb_script_rel not in (None, "", "-"))

            if has_gdb:
                cmd_a = f"gdb -batch -x {gdb_script_rel} --args {drv_target} {argv}".strip()
                cmd_b = f"{drv_target} {argv}".strip()
            else:
                cmd_a = "-"
                cmd_b = f"{drv_target} {argv}".strip()

            if "$" in cmd_a or "$" in cmd_b:
                sys.exit(f"FATAL: Command plan contains unexpanded '$' in command for {pid}: {cmd_a} / {cmd_b}")

            planned_items.append({
                "command_id": str(cmd_id),
                "point_id": pid,
                "pass": str(pas),
                "item": item,
                "driver_name": drv_name,
                "driver_path": drv_path or "NOT_FOUND",
                "driver_sha_status": drv_status,
                "gdb_script": gdb_script_rel,
                "gdb_script_sha_status": gdb_status,
                "identity_status": ident_status,
                "env_as_run": env_as_run,
                "full_command_a": cmd_a,
                "full_command_b": cmd_b,
                "dump_dir": dump_dir,
                "stdout_file": stdout_f,
                "stderr_file": stderr_f,
                "exitcode_file": exitcode_f,
                "gdb_log_file": gdb_log_f if has_gdb else "-",
                "timeout_s": str(TIMEOUT_S),
                "pt_run_dir": pt_run_dir,
                "env_dict": env_dict,
                "has_gdb": has_gdb,
                "drv_path": drv_path,
                "argv": argv,
                "gdb_script_path": gdb_path,
            })
            cmd_id += 1

    # Write plan TSV
    os.makedirs(os.path.dirname(os.path.abspath(args.out_plan)), exist_ok=True)
    with open(args.out_plan, "w", encoding="utf-8") as fh:
        fh.write("\t".join(plan_headers) + "\n")
        for p in planned_items:
            row = [p[h] for h in plan_headers]
            fh.write("\t".join(row) + "\n")

    print(f"run_m2_r8m2d: planned {len(planned_items)} runs. Identity check failures: {identity_fails}.")
    print(f"Plan written to: {args.out_plan}")

    if identity_fails > 0:
        if args.execute:
            sys.exit(f"FATAL: {identity_fails} identity verification failure(s) detected. Execution refused.")
        else:
            print(f"NOTE: {identity_fails} identity failure(s) recorded in dry-run plan.")

    if args.dry_run:
        print("run_m2_r8m2d: dry-run completed successfully.")
        return

    # Execute mode
    print(f"run_m2_r8m2d: starting execution of {len(planned_items)} runs...")
    executed_count = 0

    for p in planned_items:
        pt_dir = p["pt_run_dir"]
        if os.path.exists(pt_dir) and os.listdir(pt_dir):
            sys.exit(f"FATAL: Output directory exists and is non-empty (U17): {pt_dir}")

        os.makedirs(pt_dir, exist_ok=True)
        env = p["env_dict"]
        has_gdb = p["has_gdb"]
        drv_path = p["drv_path"]
        argv_list = p["argv"].split() if p["argv"] else []

        if has_gdb:
            gdb_log_path = p["gdb_log_file"]
            gdb_cmd = ["gdb", "-batch", "-x", p["gdb_script_path"], "--args", drv_path] + argv_list
            try:
                res_a = subprocess.run(gdb_cmd, env=env, cwd=REPO,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       timeout=TIMEOUT_S, text=True)
                with open(gdb_log_path, "w", encoding="utf-8") as fh:
                    fh.write(res_a.stdout)
            except subprocess.TimeoutExpired as te:
                with open(gdb_log_path, "w", encoding="utf-8") as fh:
                    if te.stdout:
                        fh.write(te.stdout if isinstance(te.stdout, str) else te.stdout.decode("utf-8", "replace"))
                    fh.write("\nTIMEOUT: execution exceeded 600s\n")

        nogdb_cmd = [drv_path] + argv_list
        stdout_path = p["stdout_file"]
        stderr_path = p["stderr_file"]
        exitcode_path = p["exitcode_file"]

        try:
            res_b = subprocess.run(nogdb_cmd, env=env, cwd=REPO,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   timeout=TIMEOUT_S, text=True)
            with open(stdout_path, "w", encoding="utf-8") as fh:
                fh.write(res_b.stdout)
            with open(stderr_path, "w", encoding="utf-8") as fh:
                fh.write(res_b.stderr)
            with open(exitcode_path, "w", encoding="utf-8") as fh:
                fh.write(str(res_b.returncode) + "\n")
        except subprocess.TimeoutExpired as te:
            with open(stdout_path, "w", encoding="utf-8") as fh:
                if te.stdout:
                    fh.write(te.stdout if isinstance(te.stdout, str) else te.stdout.decode("utf-8", "replace"))
            with open(stderr_path, "w", encoding="utf-8") as fh:
                if te.stderr:
                    fh.write(te.stderr if isinstance(te.stderr, str) else te.stderr.decode("utf-8", "replace"))
                fh.write("\nTIMEOUT: execution exceeded 600s\n")
            with open(exitcode_path, "w", encoding="utf-8") as fh:
                fh.write("TIMEOUT\n")

        executed_count += 1
        if executed_count % 25 == 0 or executed_count == len(planned_items):
            print(f"run_m2_r8m2d: executed {executed_count}/{len(planned_items)} runs.")

    print(f"run_m2_r8m2d: execution completed ({executed_count} runs).")


if __name__ == "__main__":
    main()
