#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2b; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# events_r9m2b.py -- Reconstruct complete events table for R9 M0, M2, M2b (Step S-G).
import argparse, os, re, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
DEFAULT_EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2b"))

LOGS = [
    ("r9m0", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m0", "safe_run.log")),
    ("r9m2", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2", "safe_run.log")),
    ("r9m2b", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2b", "safe_run.log")),
]

ISO_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\tcwd=[^\t]+\tout=[^\t]+\tcmd=(.*)$")

def get_script_key(cmd):
    # Normalize command to identify tool
    parts = cmd.strip().split()
    if not parts:
        return cmd
    if parts[0] == "rm" or cmd.startswith("rm "):
        return "rm"
    if "gate_" in cmd:
        return "gate"
    # Look for python script name or shell script name
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

def main():
    parser = argparse.ArgumentParser(description="Reconstruct EVENTS_R9_ALL_R9M2b.tsv")
    parser.add_argument("--ev", default=DEFAULT_EV, help="Evidence directory")
    parser.add_argument("--out", default=None, help="Output TSV path")
    args = parser.parse_args()

    ev = os.path.realpath(args.ev)
    os.makedirs(ev, exist_ok=True)
    out_tsv = args.out or os.path.join(ev, "EVENTS_R9_ALL_R9M2b.tsv")

    all_events = []
    seq = 1

    for round_tag, log_path in LOGS:
        entries = parse_log(round_tag, log_path)
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

    # Extract git reflog for F-4 amend
    reflog_out = subprocess.check_output(["git", "reflog", "-n", "10"], cwd=REPO, text=True)
    amend_line = None
    for l in reflog_out.splitlines():
        if "(amend)" in l and "closeout(p05-s4r9)" in l:
            amend_line = l.strip()
            break

    # Get amend commit timestamp
    amend_ts = subprocess.check_output(["git", "show", "-s", "--format=%cI", "ebf3d00"], cwd=REPO, text=True).strip()

    if amend_line:
        amend_cmd = f"git commit --amend (a7f6044 -> ebf3d00: closeout(p05-s4r9)) [reflog: {amend_line[:60]}]"
    else:
        amend_cmd = "git commit --amend (a7f6044 -> ebf3d00: closeout(p05-s4r9))"

    all_events.append([
        str(seq),
        "r9m2",
        "git_reflog",
        amend_ts,
        amend_cmd[:120],
        "amend(历史改写)"
    ])

    with open(out_tsv, "w", encoding="utf-8") as fh:
        fh.write("# EVENTS_R9_ALL_R9M2b.tsv -- Complete safe_run event table for R9 M0, M2, M2b and git reflog amend (Step S-G)\n")
        fh.write("序号\t轮次\t日志行号\t时间\t命令前120字符\t类别\n")
        for row in all_events:
            fh.write("\t".join(row) + "\n")

    print(f"EVENTS table generated. Total entries: {len(all_events)}")
    print(f"Output written to {out_tsv}")

if __name__ == "__main__":
    main()
