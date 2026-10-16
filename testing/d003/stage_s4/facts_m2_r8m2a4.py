#!/usr/bin/env python3
# facts_m2_r8m2a4.py -- P05-S4 R8 M2a4 facts extractor.
# Extracts execution facts from driver stdout/stderr, gdb logs, exit codes, and field dumps.
# Does not read driver PASS/FAIL verdict line. Missing values marked as '-' or 'MISSING', never 0.
import argparse
import csv
import hashlib
import math
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

# Sanitizer report patterns
RE_ASAN_ERR = re.compile(r"^==\d+==ERROR: AddressSanitizer:", re.M)
RE_UBSAN_ERR = re.compile(r": runtime error: ", re.M)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def check_file_nonfinite(path):
    """Scan file for non-finite float strings: nan, inf, etc. Returns 1 if non-finite found, 0 if finite."""
    if not os.path.isfile(path):
        return "-"
    has_nonfinite = 0
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line_lower = line.lower()
            if "nan" in line_lower or "inf" in line_lower:
                has_nonfinite = 1
                break
    return str(has_nonfinite)


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
        "hit2": "-",
        "inject2_invalid": "-",
        "inject2_suppressed": "-",
        "san_reports": "-",
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

    # 1. Exit code and signal
    exit_path = os.path.join(p_dir, "exitcode.txt")
    if os.path.isfile(exit_path):
        with open(exit_path, "r", encoding="utf-8") as fh:
            raw_ec = fh.read().strip()
        if raw_ec:
            try:
                ec = int(raw_ec.split()[0])
                facts["rc"] = str(ec)
                if ec > 128:
                    facts["signal"] = str(ec - 128)
                else:
                    facts["signal"] = "0"
            except ValueError:
                facts["rc"] = raw_ec
                facts["signal"] = "0"

    # 2. stdout and stderr
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

    # Extract rc1, rc2, rc3
    m_c1 = RE_R6CALLS1.search(out_text)
    m_c2 = RE_R6CALLS2.search(out_text)
    m_c3 = RE_R6CALLS3.search(out_text)

    if m_c1:
        facts["rc1"] = m_c1.group(1)
    else:
        m_rf = RE_RC_FIRST.search(out_text)
        if m_rf:
            facts["rc1"] = m_rf.group(1)

    if m_c2:
        facts["rc2"] = m_c2.group(1)
    else:
        m_rr = RE_RC_RETRY.search(out_text)
        if m_rr:
            facts["rc2"] = m_rr.group(1)

    if m_c3:
        facts["rc3"] = m_c3.group(1)
    else:
        facts["rc3"] = "-"

    # If rc1 was not found but the process exited 0 without injection
    if facts["rc1"] == "MISSING" and prereg_row.get("control_group") == "YES" and facts["rc"] == "0":
        facts["rc1"] = "0"
        facts["rc2"] = "0"

    # Extract hit count
    m_hc = RE_HITCOUNT.search(combined_text)
    if m_hc:
        facts["hit"] = m_hc.group(1)
    else:
        hit_lines = len(RE_HIT_LINE.findall(combined_text))
        if hit_lines > 0:
            facts["hit"] = str(hit_lines)
        elif prereg_row.get("control_group") == "YES" or "INJECT" not in prereg_row.get("env", ""):
            facts["hit"] = "0"
        elif prereg_row.get("item") == "M2-10":
            # Baseline point without injection request
            facts["hit"] = "0"

    # Dual failure details
    is_dual = (prereg_row.get("item") == "M2-04" or prereg_row.get("exp_hit2") not in (None, "", "-"))
    if is_dual:
        m_h2 = RE_HIT2.findall(combined_text)
        if m_h2:
            facts["hit2"] = m_h2[-1]
        else:
            facts["hit2"] = "0"
        facts["inject2_invalid"] = str(len(RE_INJECT2_INVALID.findall(combined_text)))
        facts["inject2_suppressed"] = str(len(RE_INJECT2_SUPPRESSED.findall(combined_text)))

    # Sanitizer reports
    is_san = (prereg_row.get("item") == "M2-03" or "san" in prereg_row.get("driver", ""))
    if is_san:
        san_count = 0
        san_count += len(RE_ASAN_ERR.findall(combined_text))
        san_count += len(RE_UBSAN_ERR.findall(combined_text))
        # Also check any asan.log* / ubsan.log* files in directory
        for fname in os.listdir(p_dir):
            if fname.startswith("asan.log") or fname.startswith("ubsan.log"):
                log_f = os.path.join(p_dir, fname)
                with open(log_f, "r", encoding="utf-8", errors="replace") as fh:
                    ltxt = fh.read()
                san_count += len(RE_ASAN_ERR.findall(ltxt))
                san_count += len(RE_UBSAN_ERR.findall(ltxt))
        facts["san_reports"] = str(san_count)

    # Dump file inspection
    for call_n in (1, 2, 3):
        call_f = os.path.join(p_dir, f"call{call_n}.txt")
        if os.path.isfile(call_f):
            facts[f"call{call_n}_sha256"] = sha256_file(call_f)
            facts[f"call{call_n}_nonfinite"] = check_file_nonfinite(call_f)
        else:
            # Fallback for d003 legacy dump files
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
    parser = argparse.ArgumentParser(description="P05-S4 facts extractor")
    parser.add_argument("--prereg", required=True, help="Path to effective preregistration table")
    parser.add_argument("--run-dir", required=True, help="Path to pass run directory (e.g. EV/run/pass1)")
    parser.add_argument("--pass", dest="pass_num", type=int, required=True, help="Pass index (1 or 2)")
    parser.add_argument("--out", required=True, help="Output FACTS tsv path")

    args = parser.parse_args()

    if os.path.exists(args.out):
        sys.exit(f"REFUSED: {args.out} already exists (U17)")

    with open(args.prereg, encoding="utf-8") as fh:
        prereg_rows = list(csv.DictReader(fh, delimiter="\t"))

    facts_rows = []
    for r in prereg_rows:
        pid = r["point_id"]
        p_dir = os.path.join(args.run_dir, pid)
        facts = extract_point_facts(p_dir, r, args.pass_num)
        facts_rows.append(facts)

    fieldnames = [
        "point_id", "pass", "tree", "rc", "signal", "rc1", "rc2", "rc3",
        "hit", "hit2", "inject2_invalid", "inject2_suppressed", "san_reports",
        "call1_sha256", "call2_sha256", "call3_sha256",
        "call1_nonfinite", "call2_nonfinite", "call3_nonfinite",
        "status", "notes"
    ]

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\t".join(fieldnames) + "\n")
        for f in facts_rows:
            fh.write("\t".join([f.get(col, "-") for col in fieldnames]) + "\n")

    print(f"facts_m2_r8m2a4: extracted facts for {len(facts_rows)} points to {args.out}")


if __name__ == "__main__":
    main()
