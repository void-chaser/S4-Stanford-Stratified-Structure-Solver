#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2c; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# events_r9m2c.py -- Reconstruct complete events table for R9 M0, M2, M2b, M2c, reflog amend, and bare writes (Step S-C-6).
import argparse, hashlib, os, re, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
DEFAULT_EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2c"))
REG_DIR = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M2c")

LOGS = [
    ("r9m0", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m0", "safe_run.log")),
    ("r9m2", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2", "safe_run.log")),
    ("r9m2b", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2b", "safe_run.log")),
    ("r9m2c", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2c", "safe_run.log")),
]

ISO_RE = re.compile(r"^([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z)\tcwd=[^\t]+\tout=[^\t]+\tcmd=(.*)$")

BARE_WRITES = [
    {
        "round": "r9m2b",
        "line_num": "bare_write",
        "time": "2026-10-16T21:16:11Z",
        "cmd_120": "RULINGS.tsv 截断静默恢复 (fbf3054 删 U144-U298，在 42d7d97 中恢复未披露)",
        "category": "裸写(未经 safe_run)"
    },
    {
        "round": "r9m2b",
        "line_num": "bare_write",
        "time": "2026-10-16T21:17:02Z",
        "cmd_120": "gate_check_r9m2b.py 静默修改 (加入 end_R2 映射)",
        "category": "裸写(未经 safe_run)"
    },
    {
        "round": "r9m2b",
        "line_num": "bare_write",
        "time": "2026-10-16T21:17:59Z",
        "cmd_120": "gate_r9m2b.sh 静默修改 (加入 end_R2 与 BASE_MODE，改比较基准为 $BASE)",
        "category": "裸写(未经 safe_run)"
    },
    {
        "round": "r9m2b",
        "line_num": "bare_write",
        "time": "2026-10-16T21:17:59Z",
        "cmd_120": "gate_allow_r9m2b_end.txt 静默修改 (加入 M testing/d003/stage_s4r9/*)",
        "category": "裸写(未经 safe_run)"
    },
]

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def get_script_key(cmd):
    parts = cmd.strip().split()
    if not parts:
        return cmd
    if parts[0] == "rm" or cmd.startswith("rm "):
        return "rm"
    if "gate_" in cmd:
        return "gate"
    for p in parts:
        if p.endswith(".py") or p.endswith(".sh"):
            return os.path.basename(p)
    return parts[0]

def parse_log(round_tag, log_path):
    entries = []
    if not os.path.isfile(log_path):
        return entries

    seen_scripts = set()
    with open(log_path, encoding="utf-8", errors="replace") as fh:
        line_num = 0
        for line in fh:
            line_num += 1
            m = ISO_RE.match(line.rstrip("\r\n"))
            if not m:
                continue
            ts = m.group(1)
            cmd = m.group(2).strip()
            cmd_120 = cmd[:120]

            skey = get_script_key(cmd)
            if skey == "rm":
                cat = "rm"
            elif skey == "gate":
                cat = "门禁"
            else:
                if skey in seen_scripts:
                    cat = "重跑"
                else:
                    cat = "首跑"
                    seen_scripts.add(skey)

            entries.append({
                "round": round_tag,
                "line_num": line_num,
                "time": ts,
                "cmd_120": cmd_120,
                "category": cat
            })
    return entries

def update_sums(dir_path):
    sums_file = os.path.join(dir_path, "SHA256SUMS.txt")
    entries = []
    for f in sorted(os.listdir(dir_path)):
        fp = os.path.join(dir_path, f)
        if os.path.isfile(fp) and f != "SHA256SUMS.txt":
            entries.append(f"{sha256_file(fp)}  {f}")
    with open(sums_file, "w", encoding="utf-8") as fh:
        for e in entries:
            fh.write(e + "\n")
    # self-check
    for e in entries:
        exp_sha, fn = e.split(None, 1)
        act_sha = sha256_file(os.path.join(dir_path, fn))
        assert exp_sha == act_sha, f"Mismatch in {dir_path}/{fn}"

def main():
    parser = argparse.ArgumentParser(description="Generate EVENTS_R9_ALL_R9M2c.tsv")
    parser.add_argument("--ev", default=DEFAULT_EV, help="Evidence directory")
    parser.add_argument("--out", default=None, help="Output TSV path")
    args = parser.parse_args()

    ev = os.path.realpath(args.ev)
    os.makedirs(ev, exist_ok=True)
    out_tsv = args.out or os.path.join(ev, "EVENTS_R9_ALL_R9M2c.tsv")

    all_events = []
    round_counts = {}
    seq = 1

    for round_tag, log_path in LOGS:
        entries = parse_log(round_tag, log_path)
        round_counts[round_tag] = len(entries)
        for e in entries:
            all_events.append([
                str(seq),
                e["round"],
                str(e["line_num"]),
                e["time"],
                e["cmd_120"],
                e["category"]
            ])
            seq += 1

    # Git reflog amend
    reflog_out = subprocess.check_output(["git", "reflog", "-n", "20"], cwd=REPO, text=True)
    amend_line = None
    for l in reflog_out.splitlines():
        if "(amend)" in l and "closeout(p05-s4r9)" in l:
            amend_line = l.strip()
            break

    amend_ts = subprocess.check_output(["git", "show", "-s", "--format=%cI", "ebf3d00"], cwd=REPO, text=True).strip()
    amend_cmd = f"git commit --amend (a7f6044 -> ebf3d00: closeout(p05-s4r9)) [reflog: {amend_line[:60] if amend_line else 'ebf3d00'}]"

    all_events.append([
        str(seq),
        "r9m2",
        "git_reflog",
        amend_ts,
        amend_cmd[:120],
        "amend(历史改写)"
    ])
    seq += 1

    # Bare writes from G-1, G-3
    for bw in BARE_WRITES:
        all_events.append([
            str(seq),
            bw["round"],
            bw["line_num"],
            bw["time"],
            bw["cmd_120"],
            bw["category"]
        ])
        seq += 1

    # Assertions
    expected_total = sum(round_counts.values()) + 1 + len(BARE_WRITES)
    assert len(all_events) == expected_total, f"Total rows {len(all_events)} != expected {expected_total}"

    header_text = "# EVENTS_R9_ALL_R9M2c.tsv -- Complete event table for R9 M0, M2, M2b, M2c, reflog amend, and bare writes (Step S-C-6)\n"
    breakdown_text = f"# Breakdown: r9m0={round_counts.get('r9m0', 0)}, r9m2={round_counts.get('r9m2', 0)}, r9m2b={round_counts.get('r9m2b', 0)}, r9m2c={round_counts.get('r9m2c', 0)}, reflog=1, bare_writes={len(BARE_WRITES)}, total={len(all_events)}\n"
    col_header = "序号\t轮次\t日志行号\t时间\t命令前120字符\t类别\n"

    # Write to EV
    with open(out_tsv, "w", encoding="utf-8") as fh:
        fh.write(header_text)
        fh.write(breakdown_text)
        fh.write(col_header)
        for row in all_events:
            fh.write("\t".join(row) + "\n")

    # Also write directly to registries if REG_DIR exists
    reg_tsv = os.path.join(REG_DIR, "EVENTS_R9_ALL_R9M2c.tsv")
    if os.path.isdir(REG_DIR):
        with open(reg_tsv, "w", encoding="utf-8") as fh:
            fh.write(header_text)
            fh.write(breakdown_text)
            fh.write(col_header)
            for row in all_events:
                fh.write("\t".join(row) + "\n")
        update_sums(REG_DIR)
        print(f"Updated registries EVENTS table and SHA256SUMS.txt")

    update_sums(ev)
    print(f"Updated evidence SHA256SUMS.txt")

    print(f"EVENTS table generated successfully.")
    for r_tag, c in sorted(round_counts.items()):
        print(f"  {r_tag}: {c} entries")
    print(f"  git_reflog amend: 1 entry")
    print(f"  bare_writes: {len(BARE_WRITES)} entries")
    print(f"  Total events: {len(all_events)}")
    print(f"Output written to {out_tsv}")

if __name__ == "__main__":
    main()
