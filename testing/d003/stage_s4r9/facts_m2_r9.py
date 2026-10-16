#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m0; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# facts_m2_r9.py -- P05-S4 R9 facts extractor.
# Enhancements:
#  - Adds crash_call fact in {1, 2, 3, NONE, UNKNOWN, -} (from GDB bt or ASAN stack driver line)
#  - Adds crash_site fact (first S4/ frame file:line, skipping libc frames)
#  - Adds post_call1_solution fact in {NULL, NONNULL, -} (from R6BSTATE 1)
#  - Retains all v4 facts (san_crash, init_clean, gdb_divergent, m210_hits, etc.)
import argparse
import csv
import hashlib
import os
import re
import sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))

# Regexes for return codes
RE_R6CALLS1 = re.compile(r"^R6CALLS 1 (-?\d+)\s*$", re.M)
RE_R6CALLS2 = re.compile(r"^R6CALLS 2 (-?\d+)\s*$", re.M)
RE_R6CALLS3 = re.compile(r"^R6CALLS 3 (-?\d+)\s*$", re.M)

RE_RC_FIRST = re.compile(r"^RC first (-?\d+)\s*$", re.M)
RE_RC_RETRY = re.compile(r"^RC retry (-?\d+)\s*$", re.M)

RE_HITCOUNT = re.compile(r"^S4FMM HITCOUNT (-?\d+)\s*$", re.M)
RE_HIT_LINE = re.compile(r"^S4FMM HIT ", re.M)

RE_HIT2 = re.compile(r"hit2=(\d+)")
RE_INJECT2_INVALID = re.compile(r"^S4FMM INJECT2 INVALID", re.M)
RE_INJECT2_SUPPRESSED = re.compile(r"^S4FMM INJECT2 SUPPRESSED", re.M)

# GDB inferior exit parsing
RE_GDB_EXIT_OCTAL = re.compile(r"exited with code (\d+)")
RE_GDB_EXIT_NORMAL = re.compile(r"exited normally")
RE_GDB_SIGNAL = re.compile(r"(?:received signal|Program terminated with signal)\s+SIG([A-Z0-9]+)")

# M2-10 breakpoint hits
RE_M210_HIT = re.compile(r"^M210_HIT:.*line\s+(\d+)", re.M)

# Sanitizer report patterns
RE_ASAN_ERR = re.compile(r"^==\d+==ERROR: AddressSanitizer:", re.M)
RE_ASAN_SEGV = re.compile(r"ERROR:\s*AddressSanitizer:\s*SEGV", re.M)
RE_ABORTING = re.compile(r"ABORTING", re.M)
RE_UBSAN_ERR = re.compile(r": runtime error: ", re.M)

SIG_MAP = {
    "SEGV": 11, "ABRT": 6, "BUS": 7, "ILL": 4, "FPE": 8, "TRAP": 5, "KILL": 9, "TERM": 15
}


def sha256_file(path):
    if not path or not os.path.isfile(path):
        return "-"
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def check_file_nonfinite(path):
    if not path or not os.path.isfile(path):
        return "-"
    has_nonfinite = 0
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line_lower = line.lower()
            if "nan" in line_lower or "inf" in line_lower:
                has_nonfinite = 1
                break
    return str(has_nonfinite)


def parse_output_rcs_and_hits(text, is_ctrl=False, env_str="", item=""):
    rc1, rc2, rc3 = "MISSING", "MISSING", "-"
    m_c1 = RE_R6CALLS1.search(text)
    m_c2 = RE_R6CALLS2.search(text)
    m_c3 = RE_R6CALLS3.search(text)

    if m_c1:
        rc1 = m_c1.group(1)
    else:
        m_rf = RE_RC_FIRST.search(text)
        if m_rf:
            rc1 = m_rf.group(1)

    if m_c2:
        rc2 = m_c2.group(1)
    else:
        m_rr = RE_RC_RETRY.search(text)
        if m_rr:
            rc2 = m_rr.group(1)

    if m_c3:
        rc3 = m_c3.group(1)

    hit = "MISSING"
    hit_matches = RE_HITCOUNT.findall(text)
    if hit_matches:
        hit = hit_matches[-1]
    else:
        hit_lines = len(RE_HIT_LINE.findall(text))
        if hit_lines > 0:
            hit = str(hit_lines)
        elif is_ctrl or ("INJECT" not in env_str and "FAIL_ALLOC" not in env_str) or item == "M2-10":
            hit = "0"

    return rc1, rc2, rc3, hit


def parse_crash_info(gdb_text, san_text, is_crashed):
    if not is_crashed:
        return "NONE", "-"

    combined_lines = (gdb_text + "\n" + san_text).splitlines()

    # 1. Identify driver line for crash_call
    crash_call = "UNKNOWN"
    for line in combined_lines:
        m_drv = re.search(r"driver_r6b_state\.cpp:(\d+)", line)
        if m_drv:
            lno = int(m_drv.group(1))
            if lno <= 216:
                crash_call = "1"
            elif lno <= 232:
                crash_call = "2"
            else:
                crash_call = "3"
            break

    # 2. Identify first S4 frame for crash_site, skipping libc
    frame_lines = []
    for line in combined_lines:
        if re.match(r"^\s*#\d+\s+", line):
            frame_lines.append(line)

    libc_keywords = [
        "libc.so", "ld-linux", "__memset", "memset-vec", "memcpy", "malloc",
        "free", "posix_memalign", "abort", "raise", "__GI_",
        "__asan_memset", "__interceptor_memset", "___interceptor_memset",
        "asan_memset", "interceptor_memset", "__asan_", "__interceptor_"
    ]

    crash_site = "-"
    for fl in frame_lines:
        is_libc = any(kw in fl for kw in libc_keywords)
        if is_libc:
            continue
        m_s4 = re.search(r"(?:^|/)(S4\.cpp|fmm_[^/:\s]+\.cpp|numalloc\.c):(\d+)", fl)
        if m_s4:
            crash_site = f"{m_s4.group(1)}:{m_s4.group(2)}"
            break

    return crash_call, crash_site


def extract_point_facts(p_dir, prereg_row, pass_num):
    facts = {
        "point_id": prereg_row["point_id"],
        "pass": str(pass_num),
        "tree": prereg_row.get("tree", "-"),
        "rc": "MISSING",
        "signal": "MISSING",
        "rc1": "MISSING",
        "rc2": "MISSING",
        "rc3": "MISSING",
        "hit": "MISSING",
        "hit1": "-",
        "hit2": "-",
        "inject2_invalid": "-",
        "inject2_suppressed": "-",
        "san_reports": "-",
        "san_crash": "-",
        "init_clean": "-",
        "gdb_divergent": "-",
        "m210_hits": "-",
        "crash_call": "NONE",
        "crash_site": "-",
        "post_call1_solution": "-",
        "call1_sha256": "-",
        "call2_sha256": "-",
        "call3_sha256": "-",
        "call1_nonfinite": "-",
        "call2_nonfinite": "-",
        "call3_nonfinite": "-",
        "status": "OK",
        "notes": "",
    }

    if not os.path.isdir(p_dir):
        facts["status"] = "MISSING_DIR"
        facts["notes"] = f"Directory not found: {p_dir}"
        return facts

    # 1. Exit code and signal strictly from run (b)
    exit_path = os.path.join(p_dir, "exitcode.txt")
    if os.path.isfile(exit_path):
        with open(exit_path, "r", encoding="utf-8") as fh:
            raw_ec = fh.read().strip()
        if raw_ec:
            if raw_ec == "TIMEOUT":
                facts["rc"] = "TIMEOUT"
                facts["signal"] = "0"
            else:
                try:
                    ec = int(raw_ec.split()[0])
                    if ec < 0:
                        sig = -ec
                        facts["signal"] = str(sig)
                        facts["rc"] = str(128 + sig)
                    elif ec > 128:
                        facts["signal"] = str(ec - 128)
                        facts["rc"] = str(ec)
                    else:
                        facts["signal"] = "0"
                        facts["rc"] = str(ec)
                except ValueError:
                    facts["rc"] = raw_ec
                    facts["signal"] = "0"

    # 2. stdout and stderr from run (b)
    out_path = os.path.join(p_dir, "stdout.txt")
    err_path = os.path.join(p_dir, "stderr.txt")

    out_text = ""
    err_text = ""
    if os.path.isfile(out_path):
        with open(out_path, "r", encoding="utf-8", errors="replace") as fh:
            out_text = fh.read()
    if os.path.isfile(err_path):
        with open(err_path, "r", encoding="utf-8", errors="replace") as fh:
            err_text = fh.read()

    combined_text = out_text + "\n" + err_text
    is_ctrl = (prereg_row.get("control_group") == "YES")
    env_str = prereg_row.get("env", "")
    item = prereg_row.get("item", "")

    rc1, rc2, rc3, hit = parse_output_rcs_and_hits(combined_text, is_ctrl, env_str, item)

    if rc1 == "MISSING" and is_ctrl and facts["rc"] == "0":
        rc1 = "0"
        rc2 = "0"

    facts["rc1"] = rc1
    facts["rc2"] = rc2
    facts["rc3"] = rc3
    facts["hit"] = hit

    # Dual failure details & hit1 computation
    is_dual = (item == "M2-04" or prereg_row.get("exp_hit2") not in (None, "", "-"))
    if is_dual:
        m_h2 = RE_HIT2.findall(combined_text)
        hit2_str = m_h2[-1] if m_h2 else "0"
        facts["hit2"] = hit2_str
        facts["inject2_invalid"] = str(len(RE_INJECT2_INVALID.findall(combined_text)))
        facts["inject2_suppressed"] = str(len(RE_INJECT2_SUPPRESSED.findall(combined_text)))
        if hit not in ("MISSING", "-"):
            try:
                facts["hit1"] = str(int(hit) - int(hit2_str))
            except ValueError:
                facts["hit1"] = hit
        else:
            facts["hit1"] = "-"
    else:
        facts["hit1"] = hit if hit not in ("MISSING", "-") else "-"
        facts["hit2"] = "-"

    # Sanitizer reports & san_crash (U269)
    is_san = (item == "M2-03" or "san" in prereg_row.get("driver", "") or prereg_row.get("exp_class") == "SAN_CRASH")
    san_text = ""
    if is_san:
        san_count = 0
        san_crash_found = False

        if RE_ASAN_SEGV.search(combined_text) or RE_ABORTING.search(combined_text):
            san_crash_found = True

        san_count += len(RE_ASAN_ERR.findall(combined_text))
        san_count += len(RE_UBSAN_ERR.findall(combined_text))

        for fname in os.listdir(p_dir):
            if fname.startswith("asan.log") or fname.startswith("ubsan.log"):
                log_f = os.path.join(p_dir, fname)
                with open(log_f, "r", encoding="utf-8", errors="replace") as fh:
                    ltxt = fh.read()
                san_text += "\n" + ltxt
                san_count += len(RE_ASAN_ERR.findall(ltxt))
                san_count += len(RE_UBSAN_ERR.findall(ltxt))
                if RE_ASAN_SEGV.search(ltxt) or RE_ABORTING.search(ltxt):
                    san_crash_found = True

        facts["san_reports"] = str(san_count)
        facts["san_crash"] = "1" if san_crash_found else "0"
    else:
        facts["san_reports"] = "-"
        facts["san_crash"] = "-"

    # 3. GDB log inspection and cross-checking (U256) & init_clean (U268) & post_call1_solution (U272)
    has_gdb = (prereg_row.get("gdb_script") not in (None, "", "-"))
    gdb_text = ""
    if has_gdb:
        gdb_log_path = os.path.join(p_dir, "gdb.log")
        if os.path.isfile(gdb_log_path):
            with open(gdb_log_path, "r", encoding="utf-8", errors="replace") as fh:
                gdb_text = fh.read()

            # Parse inferior rc and signal from gdb
            gdb_inf_rc = "MISSING"
            gdb_inf_sig = "0"

            m_oct = RE_GDB_EXIT_OCTAL.search(gdb_text)
            if m_oct:
                gdb_inf_rc = str(int(m_oct.group(1), 8))
                gdb_inf_sig = "0"
            elif RE_GDB_EXIT_NORMAL.search(gdb_text):
                gdb_inf_rc = "0"
                gdb_inf_sig = "0"
            else:
                m_sig = RE_GDB_SIGNAL.search(gdb_text)
                if m_sig:
                    sig_name = m_sig.group(1)
                    sig_val = SIG_MAP.get(sig_name, 128)
                    gdb_inf_sig = str(sig_val)
                    gdb_inf_rc = str(128 + sig_val)

            gdb_rc1, gdb_rc2, gdb_rc3, gdb_hit = parse_output_rcs_and_hits(gdb_text, is_ctrl, env_str, item)

            # M2-10 breakpoint hits
            m210_matches = RE_M210_HIT.findall(gdb_text)
            if m210_matches:
                facts["m210_hits"] = ",".join(sorted(set(m210_matches)))
            else:
                facts["m210_hits"] = "0"

            # init_clean derivation (U268): fail call snapshot check
            k_fail = prereg_row.get("k_fail", "1")
            if k_fail in ("-", "", None):
                k_fail = "1"
            layer_modes_null = re.findall(rf"^R6BSTATE\s+{k_fail}\s+layer\s+\d+\s+modes_null\s+(\d)", gdb_text, re.M)
            soln_match = re.search(rf"^R6BSTATE\s+{k_fail}\s+solution\s+(\S+)", gdb_text, re.M)
            cache_match = re.search(rf"^R6BSTATE\s+{k_fail}\s+cache_count\s+(\d+)", gdb_text, re.M)

            if layer_modes_null and soln_match and cache_match:
                all_modes_null = all(m == "1" for m in layer_modes_null)
                soln_is_null = soln_match.group(1) in ("null", "solved_null")
                cache_is_zero = (int(cache_match.group(1)) == 0)
                if all_modes_null and soln_is_null and cache_is_zero:
                    facts["init_clean"] = "HOLD"
                else:
                    facts["init_clean"] = "VIOLATED"
            elif any(f"R6BSTATE {k_fail}" in l for l in gdb_text.splitlines()):
                facts["init_clean"] = "VIOLATED"
            else:
                facts["init_clean"] = "-"

            # post_call1_solution extraction (U272)
            m_sol1 = re.search(r"^R6BSTATE\s+1\s+solution\s+(\S+)", gdb_text, re.M)
            if m_sol1:
                val1 = m_sol1.group(1)
                if val1 in ("null", "NULL"):
                    facts["post_call1_solution"] = "NULL"
                else:
                    facts["post_call1_solution"] = "NONNULL"
            else:
                m_sol_std = re.search(r"^R6STATE\s+1\s+solution_null\s+(\d+)", combined_text, re.M)
                if m_sol_std:
                    facts["post_call1_solution"] = "NULL" if m_sol_std.group(1) == "1" else "NONNULL"
                else:
                    facts["post_call1_solution"] = "-"

            # Check divergence
            div_reasons = []
            if gdb_inf_rc != "MISSING" and facts["rc"] != "MISSING" and gdb_inf_rc != facts["rc"]:
                div_reasons.append(f"rc({gdb_inf_rc}!=nogdb:{facts['rc']})")
            if gdb_inf_sig != facts["signal"]:
                div_reasons.append(f"signal({gdb_inf_sig}!=nogdb:{facts['signal']})")
            if gdb_rc1 != "MISSING" and facts["rc1"] != "MISSING" and gdb_rc1 != facts["rc1"]:
                div_reasons.append(f"rc1({gdb_rc1}!=nogdb:{facts['rc1']})")
            if gdb_rc2 != "MISSING" and facts["rc2"] != "MISSING" and gdb_rc2 != facts["rc2"]:
                div_reasons.append(f"rc2({gdb_rc2}!=nogdb:{facts['rc2']})")
            if gdb_rc3 != "-" and facts["rc3"] != "-" and gdb_rc3 != facts["rc3"]:
                div_reasons.append(f"rc3({gdb_rc3}!=nogdb:{facts['rc3']})")
            if gdb_hit != "MISSING" and facts["hit"] != "MISSING" and gdb_hit != facts["hit"]:
                div_reasons.append(f"hit({gdb_hit}!=nogdb:{facts['hit']})")

            if div_reasons:
                facts["gdb_divergent"] = "1"
                facts["notes"] = f"GDB_DIVERGENT: {';'.join(div_reasons)}"
            else:
                facts["gdb_divergent"] = "0"
        else:
            facts["gdb_divergent"] = "-"
            facts["m210_hits"] = "-"
            facts["init_clean"] = "-"
            facts["post_call1_solution"] = "-"
            facts["notes"] = "missing gdb.log"
    else:
        facts["gdb_divergent"] = "-"
        facts["m210_hits"] = "-"
        facts["init_clean"] = "-"
        m_sol_std = re.search(r"^R6STATE\s+1\s+solution_null\s+(\d+)", combined_text, re.M)
        if m_sol_std:
            facts["post_call1_solution"] = "NULL" if m_sol_std.group(1) == "1" else "NONNULL"
        else:
            facts["post_call1_solution"] = "-"

    # 4. Crash call and crash site extraction (U272)
    is_crashed = (
        facts["signal"] not in ("0", "MISSING", "-")
        or facts["san_crash"] == "1"
        or facts["rc"] in ("139", "134", "SIGSEGV", "SIGABRT")
        or (prereg_row.get("exp_class") in ("CRASH", "SAN_CRASH") and facts["rc"] not in ("0", "MISSING"))
    )
    crash_call, crash_site = parse_crash_info(gdb_text, san_text, is_crashed)
    facts["crash_call"] = crash_call
    facts["crash_site"] = crash_site

    # 5. Dump file inspection
    for call_n in (1, 2, 3):
        call_f = os.path.join(p_dir, f"call{call_n}.txt")
        if os.path.isfile(call_f):
            facts[f"call{call_n}_sha256"] = sha256_file(call_f)
            facts[f"call{call_n}_nonfinite"] = check_file_nonfinite(call_f)
        else:
            if call_n == 1:
                d1_f = os.path.join(p_dir, "S4FMM_DUMP1")
                if os.path.isfile(d1_f):
                    facts["call1_sha256"] = sha256_file(d1_f)
                    facts["call1_nonfinite"] = check_file_nonfinite(d1_f)
            elif call_n == 2:
                d2_f = os.path.join(p_dir, "S4FMM_DUMP")
                if os.path.isfile(d2_f):
                    facts["call2_sha256"] = sha256_file(d2_f)
                    facts["call2_nonfinite"] = check_file_nonfinite(d2_f)
            elif call_n == 3:
                d3_f = os.path.join(p_dir, "S4FMM_DUMP3")
                if os.path.isfile(d3_f):
                    facts["call3_sha256"] = sha256_file(d3_f)
                    facts["call3_nonfinite"] = check_file_nonfinite(d3_f)

    return facts


def main():
    parser = argparse.ArgumentParser(description="P05-S4 facts extractor v5")
    parser.add_argument("--run-dir", required=True, help="Path to run directory for one pass (contains point subdirectories)")
    parser.add_argument("--prereg", required=True, help="Path to effective preregistration table")
    parser.add_argument("--pass", dest="pass_num", type=int, required=True, help="Pass number (1 or 2)")
    parser.add_argument("--out", required=True, help="Output facts TSV path")

    args = parser.parse_args()

    if os.path.exists(args.out):
        sys.exit(f"REFUSED: Output file already exists (U17): {args.out}")

    with open(args.prereg, encoding="utf-8") as fh:
        prereg_rows = list(csv.DictReader((line for line in fh if not line.startswith("#")), delimiter="\t"))

    facts_rows = []
    for r in prereg_rows:
        pid = r["point_id"]
        p_dir = os.path.join(args.run_dir, pid)
        facts = extract_point_facts(p_dir, r, args.pass_num)
        facts_rows.append(facts)

    cols = [
        "point_id", "pass", "tree", "rc", "signal", "rc1", "rc2", "rc3",
        "hit", "hit1", "hit2", "inject2_invalid", "inject2_suppressed",
        "san_reports", "san_crash", "init_clean", "gdb_divergent", "m210_hits",
        "crash_call", "crash_site", "post_call1_solution",
        "call1_sha256", "call2_sha256", "call3_sha256",
        "call1_nonfinite", "call2_nonfinite", "call3_nonfinite",
        "status", "notes"
    ]

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=cols, delimiter="\t")
        fh.write(f"# FACTS_R8_M2d pass {args.pass_num}\n")
        writer.writeheader()
        for f in facts_rows:
            writer.writerow(f)

    print(f"Extracted facts for {len(facts_rows)} points -> {args.out}")


if __name__ == "__main__":
    main()
