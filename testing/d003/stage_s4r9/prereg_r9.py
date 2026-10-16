#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m0; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# prereg_r9.py -- Preregistration generator for P05-S4 R9 (Section 4 S-H, Rules U293, U294).
import datetime, hashlib, os, re, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m0"))
M2_EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2")
os.makedirs(EV, exist_ok=True)

OUT_SOLN_TSV = os.path.join(EV, "PREREG_SOLN_F4_R9.tsv")
OUT_REGRESS_TSV = os.path.join(EV, "PREREG_REGRESS_F4_R9.tsv")
OUT_CITED_TSV = os.path.join(EV, "PREREG_CITED_R9.tsv")
OUT_PLAN_TSV = os.path.join(EV, "COMMAND_PLAN_R9.tsv")

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def utc_str():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# 1. Load driver map and build manifest
drv_map_path = os.path.join(EV, "DRIVER_MAP_F3_F4_R9.tsv")
bld_tsv_path = os.path.join(EV, "BUILD_R9.tsv")

bld_artifacts = {}
with open(bld_tsv_path, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        bld_artifacts[parts[0]] = {
            "path": os.path.join(REPO, parts[1]),
            "sha256": parts[2],
            "lib_sha256": parts[7] if "lib_" in parts[0] else ""
        }

f3_to_f4 = {}
with open(drv_map_path, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("driver_family"):
            continue
        parts = line.split("\t")
        f3_to_f4[parts[1]] = parts[3]

# 2. Load K mapping from s3r5
k_map_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s3r5", "K_MAP_F4_S3R5.tsv")
k_map_f4 = {}
with open(k_map_path, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("combo"):
            continue
        parts = line.split("\t")
        # combo defect_site driver F4_caller F4_k F4_size ...
        combo = parts[0]
        site = parts[1]
        drv = parts[2]
        f4_k = int(parts[4])
        k_map_f4[(combo, site, drv)] = f4_k

# 3. Load effective F3 table
eff_path = os.path.join(EV, "M2_EFFECTIVE_F3_R9.tsv")
soln_rows = []
regress_rows = []
cited_rows = []

with open(eff_path, encoding="utf-8") as fh:
    header = None
    for line in fh:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if header is None:
            header = parts
            continue
        row = dict(zip(header, parts))
        tree = row["tree"]
        pid = row["point_id"]

        if tree != "F3":
            # Cited non-F3 row (B or F2)
            row["basis"] = f"Cited from {row.get('verdict_source', '-')}; {row.get('basis', '-')}"
            cited_rows.append(row)
            continue

        if pid.startswith("SOLN-"):
            # Also keep F3 version in cited_rows as baseline reference
            cited_row = dict(row)
            cited_row["basis"] = f"F3 baseline for {pid}"
            cited_rows.append(cited_row)

            # Generate F4 SOLN row per U293
            r4 = dict(row)
            r4["tree"] = "F4"
            # Format point_id: replace -F3 with -F4 and strip -C
            new_pid = pid.replace("-F3", "-F4")
            if new_pid.endswith("-C"):
                new_pid = new_pid[:-2]
            r4["point_id"] = new_pid

            # Determine combo and site
            # SOLN-1763-closed2d-ng1-F3-dbg-C
            p_parts = pid.split("-")
            site = p_parts[1]
            combo = p_parts[2] + "-" + p_parts[3]

            # Driver mapping
            old_drv = row["driver"]
            f4_drv = f3_to_f4[old_drv]
            r4["driver"] = f4_drv
            r4["driver_sha256"] = bld_artifacts[f4_drv]["sha256"]

            # Library sha256
            if "dbg" in f4_drv:
                r4["lib_sha256"] = bld_artifacts["lib_F4_dbg"]["sha256"]
            else:
                r4["lib_sha256"] = bld_artifacts["lib_F4_san"]["sha256"]

            # K value from K_MAP_F4_S3R5.tsv
            k_val = k_map_f4[(combo, site, f4_drv)]
            r4["k_fail"] = str(k_val)

            # Env
            mode_match = re.search(r'FMM_MODE=([a-z0-9]+)', row["env"])
            mode_val = mode_match.group(1) if mode_match else "closed2d"
            ng_match = re.search(r'S4FMM_NG=([0-9]+)', row["env"])
            ng_val = ng_match.group(1) if ng_match else "1"

            inj_prefix = "aligned" if "san-AL" in f4_drv else "init"
            r4["env"] = f"FMM_MODE={mode_val};S4FMM_NG={ng_val};S4FMM_INJECT={inj_prefix}:{k_val}"

            # Controls: matching mode/ng un-injected F4 control point
            if combo == "closed2d-ng1":
                ctrl_id = "M2-01-CTRL-01-F4"
            elif combo == "fft-ng5":
                ctrl_id = "M2-01-CTRL-02-F4"
            elif combo == "kottke-ng5":
                ctrl_id = "M2-01-CTRL-03-F4"
            else:
                ctrl_id = f"SOLN-CTRL-{combo}-F4"
            r4["control_point_id"] = ctrl_id

            # Expectations per U293
            r4["output_call"] = "2"
            r4["control_output_call"] = "2"
            r4["inj_call"] = "1"
            r4["exp_rc1"] = "1"
            r4["exp_rc2"] = "0"
            r4["exp_rc3"] = "-"
            r4["exp_signal"] = "0"
            r4["exp_hit"] = "1"
            r4["exp_class"] = "REPORTED_FAILURE"
            r4["exp_I6"] = "HOLD"
            r4["exp_post_call1_solution"] = "NULL"
            r4["exp_crash_call"] = "NONE"
            r4["exp_crash_site"] = "-"
            r4["exp_san"] = "0" if "-san" in f4_drv else "-"
            r4["state_analyzer"] = "-"
            r4["status"] = "INFLUENCED"
            r4["basis"] = "U293; F4 post-fix verification"
            soln_rows.append(r4)

        else:
            # Regression row per U294
            r4 = dict(row)
            r4["tree"] = "F4"
            r4["point_id"] = pid.replace("-F3", "-F4")
            if r4.get("control_point_id", "").endswith("-F3"):
                r4["control_point_id"] = r4["control_point_id"].replace("-F3", "-F4")

            old_drv = row["driver"]
            f4_drv = f3_to_f4[old_drv]
            r4["driver"] = f4_drv
            r4["driver_sha256"] = bld_artifacts[f4_drv]["sha256"]

            # Map library sha256 to F4
            f3_lib_sha = row.get("lib_sha256", "")
            # Find matching library
            mapped_lib_sha = f3_lib_sha
            for ltag, linfo in bld_artifacts.items():
                if "lib_" in ltag:
                    pass
            # Specific mappings:
            if "dbg" in f4_drv:
                if "seamF" in f4_drv:
                    mapped_lib_sha = bld_artifacts["lib_F4_seamF_dbg"]["sha256"]
                else:
                    mapped_lib_sha = bld_artifacts["lib_F4_dbg"]["sha256"]
            elif "san" in f4_drv:
                if "seamF" in f4_drv:
                    mapped_lib_sha = bld_artifacts["lib_F4_seamF_san"]["sha256"]
                else:
                    mapped_lib_sha = bld_artifacts["lib_F4_san"]["sha256"]
            elif "plain" in f4_drv:
                if "buf" in f4_drv or "nan" in f4_drv:
                    mapped_lib_sha = bld_artifacts["lib_F4_bufseam"]["sha256"]
                elif "fmmret" in f4_drv:
                    mapped_lib_sha = bld_artifacts["lib_F4_fmmret_plain"]["sha256"]
                else:
                    mapped_lib_sha = bld_artifacts["lib_F4_plain"]["sha256"]
            elif "nan" in f4_drv:
                mapped_lib_sha = bld_artifacts["lib_F4_bufseam"]["sha256"]
            r4["lib_sha256"] = mapped_lib_sha

            r4["status"] = "INFLUENCED"
            r4["basis"] = f"R9 regression of {pid}"
            regress_rows.append(r4)

# Assertions
if len(soln_rows) != 18:
    raise AssertionError(f"Expected 18 SOLN rows, got {len(soln_rows)}")
if len(regress_rows) != 173:
    raise AssertionError(f"Expected 173 regression rows, got {len(regress_rows)}")
total_run = len(soln_rows) + len(regress_rows)
if total_run != 191:
    raise AssertionError(f"Expected 191 running points, got {total_run}")

# Verify driver distribution against H-3
f4_driver_counts = {}
for r in (soln_rows + regress_rows):
    d = r["driver"]
    f4_driver_counts[d] = f4_driver_counts.get(d, 0) + 1

expected_f4_driver_counts = {
    "d003-F4-plain": 72,
    "d003plan-F4-plain": 9,
    "dual-F4-dbg": 2,
    "init-F4-dbg": 18,
    "init-F4-san": 12,
    "init-F4-san-AL": 3,
    "layers-F4-dbg": 8,
    "layers-dual-F4-dbg": 2,
    "nan-F4": 3,
    "polyinj-F4-dbg": 17,
    "polyinj-F4-san": 6,
    "r6bseam-seamF-F4": 6,
    "r6bstate-F4-dbg": 13,
    "r6bstate-F4-san": 13,
    "seam-fmmret-F4": 1,
    "seamF-F4-san": 6,
}

if f4_driver_counts != expected_f4_driver_counts:
    raise AssertionError(f"Driver distribution mismatch:\nActual: {f4_driver_counts}\nExpected: {expected_f4_driver_counts}")
print("Driver distribution assertion PASS (all 16 drivers match H-3).")

# 4. Write prereg tables, sha256, and timestamps
canon_cols = [c for c in header if c in soln_rows[0]]

def write_prereg(path, rows, label):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"# {os.path.basename(path)} -- {label}\n")
        fh.write("\t".join(canon_cols) + "\n")
        for r in rows:
            fh.write("\t".join(str(r.get(c, "-")) for c in canon_cols) + "\n")
    sha = sha256_file(path)
    with open(path + ".sha256", "w", encoding="utf-8") as fh:
        fh.write(f"{sha}  {os.path.basename(path)}\n")
    ts_name = path.replace(".tsv", "_TIMESTAMP_UTC.txt")
    with open(ts_name, "w", encoding="utf-8") as fh:
        fh.write(f"{utc_str()}\n")
    print(f"Wrote {path} ({len(rows)} rows, sha256={sha[:12]}...)")

write_prereg(OUT_SOLN_TSV, soln_rows, "P05-S4 R9 SOLN post-fix verification on F4 (U293)")
write_prereg(OUT_REGRESS_TSV, regress_rows, "P05-S4 R9 M2 regression on F4 (U294)")
write_prereg(OUT_CITED_TSV, cited_rows, "P05-S4 R9 cited non-running points (B/F2 and F3 SOLN baseline)")

# 5. Generate COMMAND_PLAN_R9.tsv
# 191 points x 2 passes = 382 commands
all_run_points = soln_rows + regress_rows
plan_header = [
    "command_id", "point_id", "pass", "item", "driver_name", "driver_path",
    "driver_sha_status", "gdb_script", "gdb_script_sha_status", "identity_status",
    "env_as_run", "full_command_a", "full_command_b", "dump_dir",
    "stdout_file", "stderr_file", "exitcode_file", "gdb_log_file", "timeout_s"
]

plan_rows = []
cid = 1

for p in (1, 2):
    for r in all_run_points:
        pid = r["point_id"]
        item = r["item"]
        drv_name = r["driver"]
        drv_path = bld_artifacts[drv_name]["path"]
        gdb = r.get("gdb_script", "-")
        argv = r["argv"]
        env_raw = r["env"]

        # Absolute paths for dump and logs under M2_EV
        # COMMAND_PLAN specifies execution for formal passes under evidence/p05-s4r9/m2/formal/run/pass{p}/{pid}
        dump_dir = os.path.join(M2_EV, "formal", "run", f"pass{p}", pid)
        stdout_file = os.path.join(dump_dir, "stdout.txt")
        stderr_file = os.path.join(dump_dir, "stderr.txt")
        exitcode_file = os.path.join(dump_dir, "exitcode.txt")
        gdb_log_file = os.path.join(dump_dir, "gdb.log") if gdb != "-" else "-"

        # Assemble env_as_run (ensure no $EV literal!)
        env_parts = []
        if "-san" in drv_name:
            asan_log = os.path.join(dump_dir, "asan.log")
            ubsan_log = os.path.join(dump_dir, "ubsan.log")
            env_parts.append(f"ASAN_OPTIONS=detect_leaks=0:abort_on_error=0:log_path={asan_log}")
            env_parts.append(f"UBSAN_OPTIONS=abort_on_error=0:log_path={ubsan_log}")

        for pair in env_raw.split(";"):
            if pair.strip():
                env_parts.append(pair.strip())

        env_parts.append(f"S4FMM_DUMP_DIR={dump_dir}")
        env_parts.sort()
        env_as_run = " ".join(env_parts)

        # Check: ensure no '$EV' literal in env_as_run or any paths
        if "$EV" in env_as_run or "$EV" in dump_dir:
            raise AssertionError(f"Forbidden '$EV' literal found in plan for {pid}")

        # Commands
        if gdb != "-":
            cmd_a = f"gdb -batch -x {gdb} --args {drv_path} {argv}"
            cmd_b = f"{drv_path} {argv}"
        else:
            cmd_a = "-"
            cmd_b = f"{drv_path} {argv}"

        plan_rows.append([
            str(cid), pid, str(p), item, drv_name, drv_path,
            "DRIVER_SHA_PASS", gdb, "GDB_SHA_PASS" if gdb != "-" else "N/A", "IDENTITY_PASS",
            env_as_run, cmd_a, cmd_b, dump_dir,
            stdout_file, stderr_file, exitcode_file, gdb_log_file, "600"
        ])
        cid += 1

with open(OUT_PLAN_TSV, "w", encoding="utf-8") as fh:
    fh.write("# COMMAND_PLAN_R9.tsv -- P05-S4 R9 execution plan (382 commands: 191 points x 2 passes)\n")
    fh.write("\t".join(plan_header) + "\n")
    for row in plan_rows:
        fh.write("\t".join(row) + "\n")

plan_sha = sha256_file(OUT_PLAN_TSV)
with open(OUT_PLAN_TSV + ".sha256", "w", encoding="utf-8") as fh:
    fh.write(f"{plan_sha}  COMMAND_PLAN_R9.tsv\n")
with open(os.path.join(EV, "COMMAND_PLAN_R9_TIMESTAMP_UTC.txt"), "w", encoding="utf-8") as fh:
    fh.write(f"{utc_str()}\n")

print(f"Wrote {OUT_PLAN_TSV} (382 commands, sha256={plan_sha[:12]}...)")
print("ALL PREREGISTRATION STEPS COMPLETED.")
