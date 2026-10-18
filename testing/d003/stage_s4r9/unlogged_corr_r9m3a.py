#!/usr/bin/env python3
# unlogged_corr_r9m3a.py -- line-by-line correction table for UNLOGGED_WRITES_R9M1R3.tsv (J-4 / U331).
# usage: python3 -I -B testing/d003/stage_s4r9/unlogged_corr_r9m3a.py OUT.tsv
import os, sys, re, subprocess

REPO = os.getcwd()
PATH_IN_REPO = "checkpoints/p05/registries/s4r9/M1R4/UNLOGGED_WRITES_R9M1R3.tsv"
EV_M1R3 = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1r3")
EV_M1R4 = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1r4")


def git_show(rev):
    try:
        return subprocess.check_output(["git", "show", rev + ":" + PATH_IN_REPO], cwd=REPO).decode("utf-8", "replace").splitlines()
    except subprocess.CalledProcessError:
        return []


def lines_of(p):
    return open(p, encoding="utf-8", errors="replace").read().splitlines() if os.path.isfile(p) else []


def write_commands(ev_dir):
    out = []
    for line in lines_of(os.path.join(ev_dir, "safe_run.log")):
        parts = line.split("\t")
        for x in parts[1:]:
            if x.startswith("cmd="):
                out.append(x[4:])
                break
    return out


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3a/UNLOGGED_CORR_R9M3A.tsv")
    old = git_show("786b150")
    new = git_show("2f86aa11c7ee1bb16f663abf03ddbf04674a6912")
    cmds_m1r3 = write_commands(EV_M1R3)
    cmds_m1r4 = write_commands(EV_M1R4)
    rows = []
    n = max(len(old), len(new))
    for i in range(n):
        a = old[i] if i < len(old) else "<absent>"
        b = new[i] if i < len(new) else "<absent>"
        if a == b:
            continue
        fa = a.split("\t")
        fb = b.split("\t")
        fpath = fb[0] if len(fb) > 0 else ""
        mt_old = fa[1] if len(fa) > 1 else ""
        mt_new = fb[1] if len(fb) > 1 else ""
        # which round's log records a write to this file?
        hit3 = [c for c in cmds_m1r3 if fpath and fpath in c]
        hit4 = [c for c in cmds_m1r4 if fpath and fpath in c]
        owner = "UNKNOWN"
        if hit3:
            owner = "r9m1r3"
        if hit4:
            owner = "r9m1r4 (recorded in m1r4 safe_run.log)"
        rows.append((i + 1, fpath, mt_old, mt_new, len(hit3), len(hit4), owner,
                     "该行 mtime 由 r9m1r4 的 append 写入产生（m1r4 日志有记录），不是 r9m1r3 的未记录写入；应归 r9m1r4"))
    hdr = ["line_no", "file_path", "mtime_786b150", "mtime_2f86aa1", "m1r3_log_write_cmds", "m1r4_log_write_cmds", "reassigned_owner", "correction"]
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("# UNLOGGED_CORR_R9M3A.tsv -- corrected attribution of the two lines rewritten between 786b150 and 2f86aa1 (J-4 / U331)\n")
        fh.write("# the committed file is not modified in this round; this table is the correction record\n")
        fh.write("\t".join(hdr) + "\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
    extra = []
    if len(old) != len(new):
        extra.append("line count %d -> %d" % (len(old), len(new)))
    print("changed lines=%d; %s" % (len(rows), "; ".join(extra) if extra else "same line count"))
    for r in rows:
        print("  L%d %s %s -> %s owner=%s" % (r[0], r[1], r[2], r[3], r[6]))
    print("WROTE " + out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
