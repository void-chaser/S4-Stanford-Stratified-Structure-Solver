#!/usr/bin/env python3
# facts_m2_r8m2c.py -- P05-S4 R8 M2c facts extractor v4.
# Enhancements:
#  - Adds san_crash fact (1 if ASAN SEGV or ABORTING in stderr/san logs; 0/-, U269)
#  - Adds init_clean fact (HOLD if all layers modes_null=1, solution null, cache_count 0 at k_fail; VIOLATED otherwise; U268)
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
        elif is_ctrl or "INJECT" not in env_str or item == "M2-10":
            hit = "0"

    return rc1, rc2, rc3, hit


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
                san_count += len(RE_ASAN_ERR.findall(ltxt))
                san_count += len(RE_UBSAN_ERR.findall(ltxt))
                if RE_ASAN_SEGV.search(ltxt) or RE_ABORTING.search(ltxt):
                    san_crash_found = True

        facts["san_reports"] = str(san_count)
        facts["san_crash"] = "1" if san_crash_found else "0"
    else:
        facts["san_reports"] = "-"
        facts["san_crash"] = "-"

    # 3. GDB log inspection and cross-checking (U256) & init_clean (U268)
    has_gdb = (prereg_row.get("gdb_script") not in (None, "", "-"))
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
            facts["notes"] = "missing gdb.log"
    else:
        facts["gdb_divergent"] = "-"
        facts["m210_hits"] = "-"
        facts["init_clean"] = "-"

    # Dump file inspection
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

    return facts


def main():
    parser = argparse.ArgumentParser(description="P05-S4 facts extractor v4")
    parser.add_argument("--prereg", required=True, help="Path to effective preregistration table")
    parser.add_argument("--run-dir", required=True, help="Path to pass run directory (e.g. EV/run/pass1)")
    parser.add_argument("--pass", dest="pass_num", type=int, required=True, help="Pass index (1 or 2)")
    parser.add_argument("--out", required=True, help="Output FACTS tsv path")

    args = parser.parse_args()

    if os.path.exists(args.out):
        sys.exit(f"REFUSED: {args.out} already exists (U17)")

    with open(args.prereg, encoding="utf-8") as fh:
        prereg_rows = list(csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"))

    facts_rows = []
    for r in prereg_rows:
        pid = r["point_id"]
        p_dir = os.path.join(args.run_dir, pid)
        facts = extract_point_facts(p_dir, r, args.pass_num)
        facts_rows.append(facts)

    fieldnames = [
        "point_id", "pass", "tree", "rc", "signal", "rc1", "rc2", "rc3",
        "hit", "hit1", "hit2", "inject2_invalid", "inject2_suppressed", "san_reports",
        "san_crash", "init_clean",
        "gdb_divergent", "m210_hits",
        "call1_sha256", "call2_sha256", "call3_sha256",
        "call1_nonfinite", "call2_nonfinite", "call3_nonfinite",
        "status", "notes"
    ]

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\t".join(fieldnames) + "\n")
        for f in facts_rows:
            fh.write("\t".join([f.get(col, "-") for col in fieldnames]) + "\n")

    print(f"facts_m2_r8m2c: extracted facts for {len(facts_rows)} points to {args.out}")


if __name__ == "__main__":
    main()
