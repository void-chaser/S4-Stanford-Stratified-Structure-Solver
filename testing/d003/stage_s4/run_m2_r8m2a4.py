#!/usr/bin/env python3
# run_m2_r8m2a4.py -- P05-S4 R8 M2a4 runner and command planner.
# In r8m2a4, only --dry-run is permitted (formal execution disabled by protocol boundary §1).
# Generates COMMAND_PLAN_R8_M2a4.tsv (300 rows = 150 points * 2 passes).
# Verifies driver_sha256, lib_sha256, and gdb_script_sha256 before generating plans.
import argparse
import csv
import hashlib
import os
import sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
TIMEOUT_S = 600

# Search directories for compiled driver binaries
DRIVER_SEARCH_DIRS = [
    os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build_R3", "drivers"),
    os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build", "B-dbg"),
    os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build", "san"),
    os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build"),
    os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "drivers_r8"),
    os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "drivers_r8m1"),
    os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r7", "drivers_r7"),
]


def sha256_file(path):
    if not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def find_driver_binary(name):
    """Find binary executable for given driver name across known evidence directories."""
    for d in DRIVER_SEARCH_DIRS:
        # Check direct executable
        p1 = os.path.join(d, name)
        if os.path.isfile(p1) and os.access(p1, os.X_OK):
            return p1
        # Check subfolder/driver
        p2 = os.path.join(d, name, "driver")
        if os.path.isfile(p2) and os.access(p2, os.X_OK):
            return p2
    return None


def main():
    parser = argparse.ArgumentParser(description="P05-S4 M2 runner / command planner")
    parser.add_argument("--prereg", required=True, help="Path to effective preregistration table")
    parser.add_argument("--ev", required=True, help="Evidence directory root (for dump and logs)")
    parser.add_argument("--out-plan", required=True, help="Output COMMAND_PLAN_R8_M2a4.tsv path")
    parser.add_argument("--dry-run", action="store_true", required=True,
                        help="Only command planning permitted in r8m2a4")

    args = parser.parse_args()

    if not args.dry_run:
        sys.exit("FATAL: Formal execution disabled in r8m2a4 by protocol boundary §1. Only --dry-run is permitted.")

    with open(args.prereg, encoding="utf-8") as fh:
        prereg_rows = list(csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"))

    if len(prereg_rows) != 150:
        sys.exit(f"FATAL: prereg rows count {len(prereg_rows)} != 150")

    plan_rows = []
    cmd_id = 1
    identity_fails = 0

    plan_headers = [
        "command_id", "point_id", "pass", "item", "driver_name", "driver_path",
        "driver_sha_status", "gdb_script", "gdb_script_sha_status",
        "identity_status", "env_vars", "full_command",
        "dump_dir", "stdout_file", "stderr_file", "exitcode_file", "timeout_s"
    ]

    for pas in (1, 2):
        for r in prereg_rows:
            pid = r["point_id"]
            item = r.get("item", "")
            drv_name = r["driver"]
            exp_drv_sha = r["driver_sha256"]
            gdb_script_rel = r.get("gdb_script", "-")
            exp_gdb_sha = r.get("gdb_script_sha256", "-")

            # 1. Driver binary verification
            drv_path = find_driver_binary(drv_name)
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
            pt_run_dir = os.path.join(args.ev, "run", f"pass{pas}", pid)
            dump_dir = pt_run_dir
            stdout_f = os.path.join(pt_run_dir, "stdout.txt")
            stderr_f = os.path.join(pt_run_dir, "stderr.txt")
            exitcode_f = os.path.join(pt_run_dir, "exitcode.txt")

            # 4. Environment
            env_tokens = []
            if r.get("env") not in (None, "", "-"):
                env_tokens.extend(r["env"].split(";"))
            env_tokens.append(f"S4FMM_DUMP_DIR={dump_dir}")

            # Sanitizer options
            if r.get("san_options") not in (None, "", "-"):
                san_opts = r["san_options"].replace("{pass}", str(pas)).replace("{point_id}", pid)
                env_tokens.extend(san_opts.split(";"))

            env_vars_str = " ".join(env_tokens)

            # 5. Full command
            argv = r.get("argv", "")
            drv_target = os.path.relpath(drv_path, REPO) if drv_path else drv_name
            if gdb_script_rel not in (None, "", "-"):
                cmd_str = f"env {env_vars_str} gdb -batch -x {gdb_script_rel} --args {drv_target} {argv}"
            else:
                cmd_str = f"env {env_vars_str} {drv_target} {argv}"

            plan_rows.append([
                str(cmd_id),
                pid,
                str(pas),
                item,
                drv_name,
                drv_path or "NOT_FOUND",
                drv_status,
                gdb_script_rel,
                gdb_status,
                ident_status,
                env_vars_str,
                cmd_str,
                dump_dir,
                stdout_f,
                stderr_f,
                exitcode_f,
                str(TIMEOUT_S)
            ])
            cmd_id += 1

    os.makedirs(os.path.dirname(os.path.abspath(args.out_plan)), exist_ok=True)
    with open(args.out_plan, "w", encoding="utf-8") as fh:
        fh.write("\t".join(plan_headers) + "\n")
        for row in plan_rows:
            fh.write("\t".join(row) + "\n")

    print(f"run_m2_r8m2a4: dry-run completed successfully.")
    print(f"Total commands planned: {len(plan_rows)} (150 points * 2 passes = 300).")
    print(f"Identity check failures: {identity_fails}.")
    print(f"Command plan written to: {args.out_plan}")


if __name__ == "__main__":
    main()
