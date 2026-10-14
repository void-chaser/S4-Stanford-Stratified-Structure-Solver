#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a: runner for no-injection callseq tracing across all 198 units.  New file.

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/callseq_runner_r8m1a4.py OUTDIR
Reads CALLSEQ_UNITS_R8_M1a4_R3.tsv, executes F2 then F3 per pair under gdb -batch -nx.
Clean environment: env -i, PATH, LANG=C, LC_ALL=C, PYTHONDONTWRITEBYTECODE=1, plus specified FMM_MODE/S4FMM_NG/S4FMM_TWICE.
Writes individual logs to OUTDIR/callseq_r8m1a4/<unit_id>/
Writes aggregate log to OUTDIR/CALLSEQ_RUNS_R8_M1a4.tsv.
Stops immediately on RUN_ERROR or TRACE_ERROR.
"""
import datetime
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
GDB_SCRIPT = os.path.join(HERE, "callseq_r8m1a4_gdb.py")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_units(path):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    hdr = lines[0].split("\t")
    units = []
    for line in lines[1:]:
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        units.append(dict(zip(hdr, cols)))
    return units


def main(argv):
    if len(argv) not in (2, 3, 4):
        raise SystemExit("usage: callseq_runner_r8m1a4.py OUTDIR [SUBDIR_NAME] [RUNS_TSV_NAME]")
    out_dir = argv[1]
    subdir_name = argv[2] if len(argv) >= 3 else "callseq_r8m1a4_r2"
    tsv_name = argv[3] if len(argv) >= 4 else "CALLSEQ_RUNS_R8_M1a4.tsv"

    units_file = os.path.join(out_dir, "CALLSEQ_UNITS_R8_M1a4_R3.tsv")
    if not os.path.isfile(units_file):
        raise SystemExit("REFUSED: units file missing: %s" % units_file)

    runs_tsv = os.path.join(out_dir, tsv_name)
    if os.path.exists(runs_tsv):
        raise SystemExit("REFUSED: exists (U17): %s" % runs_tsv)

    units = read_units(units_file)
    print("Loaded %d units from %s" % (len(units), units_file))

    # Sort units so that per pair_id, F2 runs strictly before F3
    units_sorted = sorted(units, key=lambda u: (u["pair_id"], 0 if u["run_tree"] == "F2" else 1))

    callseq_dir = os.path.join(out_dir, subdir_name)
    os.makedirs(callseq_dir, exist_ok=True)

    run_records = []
    stop_reason = None

    for idx, u in enumerate(units_sorted, 1):
        uid = u["unit_id"]
        pid = u["pair_id"]
        tree = u["run_tree"]
        drv_path = u["driver_path"]
        drv_sha = u["driver_sha256"]
        mode = u["mode"]
        ng = u["NG"]
        twice = u["twice_env"]
        argv_list = u["argv"].split(" ")
        fams = u["families"]

        # Check driver hash
        if not os.path.isfile(drv_path):
            stop_reason = "RUN_ERROR: driver file not found: %s (unit %s)" % (drv_path, uid)
            break
        actual_sha = sha256_file(drv_path)
        if actual_sha != drv_sha:
            stop_reason = "RUN_ERROR: driver sha256 mismatch for %s (unit %s): expected %s, got %s" % (
                drv_path, uid, drv_sha, actual_sha)
            break

        # Output dir for this unit
        u_out = os.path.join(callseq_dir, uid)
        if os.path.exists(u_out):
            stop_reason = "REFUSED: unit dir already exists (U17): %s" % u_out
            break
        os.makedirs(u_out, exist_ok=True)

        # Build clean environment
        clean_env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "LANG": "C",
            "LC_ALL": "C",
            "PYTHONDONTWRITEBYTECODE": "1",
            "FMM_MODE": mode,
            "S4FMM_NG": ng,
            "CALLSEQ_OUT_DIR": u_out,
            "CALLSEQ_FAMILIES": fams,
            "CALLSEQ_TREE": tree,
            "CALLSEQ_UNIT_ID": uid,
        }
        if twice == "slab":
            clean_env["S4FMM_TWICE"] = "slab"

        cmd = ["gdb", "-batch", "-nx", "-x", GDB_SCRIPT, "--args", drv_path] + argv_list

        t_start = datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            p = subprocess.run(cmd, env=clean_env, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
            gdb_rc = p.returncode
            stdout_txt = p.stdout.decode("utf-8", errors="replace")
            stderr_txt = p.stderr.decode("utf-8", errors="replace")
        except Exception as e:
            stop_reason = "RUN_ERROR: subprocess failed for %s: %s" % (uid, e)
            break
        t_end = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Save gdb raw output
        with open(os.path.join(u_out, "gdb.stdout.txt"), "w", encoding="utf-8") as fh:
            fh.write(stdout_txt)
        with open(os.path.join(u_out, "gdb.stderr.txt"), "w", encoding="utf-8") as fh:
            fh.write(stderr_txt)

        # Read summary.json
        summary_file = os.path.join(u_out, "summary.json")
        inferior_exit = None
        inferior_sig = None
        trace_err = None
        if os.path.isfile(summary_file):
            try:
                with open(summary_file, encoding="utf-8") as fh:
                    sdata = json.load(fh)
                inferior_exit = sdata.get("exit_code")
                inferior_sig = sdata.get("signal")
                trace_err = sdata.get("trace_error")
            except Exception as e:
                trace_err = "summary_read_error: %s" % e
        else:
            trace_err = "summary_file_missing"

        if gdb_rc != 0:
            trace_err = ("gdb_rc_%d; " % gdb_rc) + (trace_err or "")

        rec = {
            "unit_id": uid,
            "pair_id": pid,
            "run_tree": tree,
            "driver_tag": u["driver_tag"],
            "driver_sha256": drv_sha,
            "cmd_env": u["env"],
            "start_utc": t_start,
            "end_utc": t_end,
            "gdb_rc": gdb_rc,
            "inferior_exit": str(inferior_exit if inferior_exit is not None else "-"),
            "signal": str(inferior_sig if inferior_sig is not None else "-"),
            "trace_error": trace_err or "NONE",
        }
        run_records.append(rec)

        if idx % 20 == 0 or idx == len(units_sorted):
            print("  Progress: %d / %d units completed (last %s, rc=%d, err=%s)" % (
                idx, len(units_sorted), uid, gdb_rc, trace_err or "NONE"))

        # Stop if error occurred
        if trace_err and "REQUIRED_SYMBOL_MISSING" in trace_err:
            stop_reason = "REQUIRED_SYMBOL_MISSING in unit %s: %s" % (uid, trace_err)
            break
        if trace_err and trace_err != "NONE":
            stop_reason = "TRACE_ERROR in unit %s: %s" % (uid, trace_err)
            break

    # Write aggregate table
    with open(runs_tsv, "w", encoding="utf-8") as fh:
        fh.write("unit_id\tpair_id\trun_tree\tdriver_tag\tdriver_sha256\tcmd_env\tstart_utc\tend_utc\tgdb_rc\tinferior_exit\tsignal\ttrace_error\n")
        for r in run_records:
            fh.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%s\t%s\t%s\n" % (
                r["unit_id"], r["pair_id"], r["run_tree"], r["driver_tag"], r["driver_sha256"],
                r["cmd_env"], r["start_utc"], r["end_utc"], r["gdb_rc"], r["inferior_exit"],
                r["signal"], r["trace_error"]))

    if stop_reason:
        print("STOPPED: %s" % stop_reason, file=sys.stderr)
        raise SystemExit(stop_reason)

    print("ALL %d UNITS EXECUTED SUCCESSFULLY without trace error" % len(run_records))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
