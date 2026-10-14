#!/usr/bin/env python3
# check_m1c_envlog_r8m1b3.py -- P05-S4 R8 M1b3 section 4: read-only M1c call-log env check. New file.
# Reads REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv (planned env) and the R7 state tables (env_as_run).
# Writes $EV/ENV_LOGCHECK_M1C_R8_M1b3.tsv only. Runs no driver.
# Only FMM_* and S4FMM_* keys are compared; S4FMM_DUMP* keys are excluded.
import os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1b3")
PREREG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a", "REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv")
R7 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7")
LOGS = [
    os.path.join(R7, "M3_F2_STATE_R6c_pass1.tsv"),
    os.path.join(R7, "M3_F2_STATE_R6c_pass2.tsv"),
    os.path.join(R7, "M3_F2_STATE_SEAM_R6c_pass1.tsv"),
    os.path.join(R7, "M3_F2_STATE_SEAM_R6c_pass2.tsv"),
]
OUT = os.path.join(EV, "ENV_LOGCHECK_M1C_R8_M1b3.tsv")


def read_table(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip("\r\n") for l in fh if not l.startswith("#")]
    header = lines[0].split("\t")
    for l in lines[1:]:
        if not l:
            continue
        rows.append(dict(zip(header, l.split("\t"))))
    return rows


def env_dict(env_str):
    d = {}
    for part in env_str.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        k, v = part.split("=", 1)
        d[k] = v
    return d


def keep(d):
    out = {}
    for k, v in d.items():
        if k.startswith("S4FMM_DUMP"):
            continue
        if k.startswith("FMM_") or k.startswith("S4FMM_"):
            out[k] = v
    return out


def key_str(d):
    return ";".join("%s=%s" % (k, d[k]) for k in sorted(d))


def main():
    prereg = read_table(PREREG)
    # base id -> list of (pass_file, env_as_run)
    log_env = {}
    for path in LOGS:
        name = os.path.basename(path)
        for r in read_table(path):
            if r.get("kind") not in ("point", "control"):
                continue
            base = r["id"]
            log_env.setdefault(base, []).append((name, r["env_as_run"]))

    lines = ["row_id\tgroup\tpoint_id\ttree\tbase_id\tplanned_env\tlogged_env\tlog_sources\tresult"]
    counts = {}
    for i, r in enumerate(prereg, 1):
        pid = r["point_id"]
        base = pid[:-3] if pid.endswith("-F3") else pid
        planned = keep(env_dict(r["env"]))
        entries = log_env.get(base, [])
        if not entries:
            result = "NO_LOG"
            logged_key = ""
            srcs = ""
        else:
            keys = sorted(set(key_str(keep(env_dict(e[1]))) for e in entries))
            srcs = ",".join(e[0] for e in entries)
            if len(keys) > 1:
                result = "LOG_INCONSISTENT"
                logged_key = " | ".join(keys)
            else:
                logged_key = keys[0]
                result = "AGREE" if key_str(planned) == logged_key else "DIFF"
        counts[result] = counts.get(result, 0) + 1
        lines.append("\t".join([str(i), r["group"], pid, r["tree"], base, key_str(planned), logged_key, srcs, result]))

    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    os.replace(tmp, OUT)
    print("rows=%d" % len(prereg))
    for k in sorted(counts):
        print("%s=%d" % (k, counts[k]))


if __name__ == "__main__":
    sys.exit(main())
