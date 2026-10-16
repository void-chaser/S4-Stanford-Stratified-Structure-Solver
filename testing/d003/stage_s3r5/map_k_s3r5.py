#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# map_k_s3r5.py -- Map K values for SOLN sites on F4 drivers via GDB (S-H, U286).
import os, re, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s3r5")
EV = os.path.join(REPO, EV_REL)
TMP_DIR = os.path.join(EV, "tmp")
PROBE_DIR = os.path.join(EV, "probe")
OUT_TSV = os.path.join(EV, "K_MAP_F4_S3R5.tsv")
RAW_TXT = os.path.join(EV, "K_MAP_RAW_S3R5.txt")
PROBE_TXT = os.path.join(PROBE_DIR, "map_k_s3r5.txt")

COMBOS = [
    ("closed2d-ng1", "closed2d", "1", 192),
    ("fft-ng5", "fft", "5", 960),
    ("kottke-ng5", "kottke", "5", 960),
]

DRV_DBG = os.path.join(EV, "build", "init-F4-dbg")
DRV_SAN = os.path.join(EV, "build", "init-F4-san")
DRV_SAN_AL = os.path.join(EV, "build", "init-F4-san-AL")

# Known F3 K and size mapping for comparison:
F3_K_MAP = {
    ("closed2d-ng1", 1763, "init-F4-dbg"): (1763, 9, 16),
    ("closed2d-ng1", 1764, "init-F4-dbg"): (1764, 10, 192),
    ("closed2d-ng1", 1765, "init-F4-dbg"): (1765, 11, 12),
    ("closed2d-ng1", 1763, "init-F4-san"): (1763, 7, 16),
    ("closed2d-ng1", 1765, "init-F4-san"): (1765, 8, 12),
    ("closed2d-ng1", 1764, "init-F4-san-AL"): (1764, 3, 192),
    ("fft-ng5", 1763, "init-F4-dbg"): (1763, 10, 16),
    ("fft-ng5", 1764, "init-F4-dbg"): (1764, 11, 960),
    ("fft-ng5", 1765, "init-F4-dbg"): (1765, 12, 12),
    ("fft-ng5", 1763, "init-F4-san"): (1763, 8, 16),
    ("fft-ng5", 1765, "init-F4-san"): (1765, 9, 12),
    ("fft-ng5", 1764, "init-F4-san-AL"): (1764, 3, 960),
    ("kottke-ng5", 1763, "init-F4-dbg"): (1763, 10, 16),
    ("kottke-ng5", 1764, "init-F4-dbg"): (1764, 11, 960),
    ("kottke-ng5", 1765, "init-F4-dbg"): (1765, 12, 12),
    ("kottke-ng5", 1763, "init-F4-san"): (1763, 8, 16),
    ("kottke-ng5", 1765, "init-F4-san"): (1765, 9, 12),
    ("kottke-ng5", 1764, "init-F4-san-AL"): (1764, 3, 960),
}

GDB_MALLOC_SCRIPT = """set pagination off
set confirm off
set $count = 0
break inject_s3r4_init.cpp:79
commands
silent
set $count = $count + 1
printf "CALL_MALLOC k=%ld n=%zu\\n", $count, n
bt 4
continue
end
run pattern both 4 3
quit
"""

GDB_ALIGNED_SCRIPT = """set pagination off
set confirm off
set $count = 0
break __wrap_malloc_aligned
commands
silent
set $count = $count + 1
printf "CALL_ALIGNED k=%ld size=%zu alignment=%zu\\n", $count, size, alignment
bt 4
continue
end
run pattern both 4 3
quit
"""

def run_gdb(drv, script_content, cname, mode, ng, is_san):
    os.makedirs(TMP_DIR, exist_ok=True)
    script_path = os.path.join(TMP_DIR, "gdb_map_%s_%s.gdb" % (os.path.basename(drv), cname))
    with open(script_path, "w", encoding="utf-8") as fh:
        fh.write(script_content)
    env = os.environ.copy()
    env["FMM_MODE"] = mode
    env["S4FMM_NG"] = ng
    if is_san:
        env["ASAN_OPTIONS"] = "detect_leaks=0:abort_on_error=0"
        env["UBSAN_OPTIONS"] = "abort_on_error=0"
    env.pop("S4FMM_INJECT", None)
    env.pop("S4_FAIL_ALLOC_AT", None)
    cmd = ["gdb", "-batch", "-x", script_path, "--args", drv, "pattern", "both", "4", "3"]
    p = subprocess.run(cmd, cwd=REPO, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return p.stdout, p.stderr

def parse_malloc_blocks(raw_out):
    # Returns list of dict: {k, size, frames: [frame_text, ...]}
    blocks = raw_out.split("CALL_MALLOC ")
    results = []
    for b in blocks[1:]:
        lines = b.splitlines()
        if not lines:
            continue
        m = re.match(r"^k=(\d+)\s+n=(\d+)", lines[0])
        if not m:
            continue
        k = int(m.group(1))
        sz = int(m.group(2))
        frames = lines[1:]
        results.append({"k": k, "size": sz, "frames": frames})
    return results

def parse_aligned_blocks(raw_out):
    blocks = raw_out.split("CALL_ALIGNED ")
    results = []
    for b in blocks[1:]:
        lines = b.splitlines()
        if not lines:
            continue
        m = re.match(r"^k=(\d+)\s+size=(\d+)\s+alignment=(\d+)", lines[0])
        if not m:
            continue
        k = int(m.group(1))
        sz = int(m.group(2))
        frames = lines[1:]
        results.append({"k": k, "size": sz, "frames": frames})
    return results

def find_call_by_line(entries, target_line):
    matches = []
    for e in entries:
        frame_text = " ".join(e["frames"])
        if ("S4.cpp:%d" % target_line) in frame_text and "Simulation_InitSolution" in frame_text:
            matches.append(e)
    return matches

def main():
    os.makedirs(PROBE_DIR, exist_ok=True)
    raw_blocks = []
    tsv_rows = []
    hard_stop = False

    # F4 lines in S4/S4.cpp:
    # 1763: sol = (Solution_*)malloc(sizeof(Solution_));
    # 1771: sol->ab = S4_malloc(...);
    # 1772: sol->solved = (int*)malloc(...);
    F4_LINES = {1763: 1763, 1764: 1771, 1765: 1772}

    for cname, mode, ng, exp_ab_sz in COMBOS:
        raw_blocks.append("================================================================================")
        raw_blocks.append("COMBO: %s (mode=%s, ng=%s)" % (cname, mode, ng))
        raw_blocks.append("================================================================================")

        # 1. init-F4-dbg (mapped via malloc: 1763, 1764, 1765)
        out_dbg, err_dbg = run_gdb(DRV_DBG, GDB_MALLOC_SCRIPT, cname, mode, ng, False)
        raw_blocks.append("--- DRIVER: init-F4-dbg ---")
        raw_blocks.append(out_dbg)
        if err_dbg:
            raw_blocks.append("STDERR: " + err_dbg)
        entries_dbg = parse_malloc_blocks(out_dbg)

        for site in [1763, 1764, 1765]:
            f4_line = F4_LINES[site]
            m = find_call_by_line(entries_dbg, f4_line)
            if len(m) != 1:
                print("ERROR: %s %d init-F4-dbg found %d matches (expected 1)" % (cname, site, len(m)))
                hard_stop = True
                k_val, sz_val = -1, -1
            else:
                k_val = m[0]["k"]
                sz_val = m[0]["size"]
            f3_line, f3_k, f3_sz = F3_K_MAP[(cname, site, "init-F4-dbg")]
            match_k = (k_val == f3_k)
            status = "PASS_EXACT_MATCH" if match_k else "DIVERGENT_K"
            tsv_rows.append((cname, str(site), "init-F4-dbg", "S4.cpp:%d" % f4_line, str(k_val), str(sz_val),
                             "S4.cpp:%d" % f3_line, str(f3_k), str(f3_sz), str(match_k), status))

        # 2. init-F4-san (mapped via malloc: 1763, 1765)
        out_san, err_san = run_gdb(DRV_SAN, GDB_MALLOC_SCRIPT, cname, mode, ng, True)
        raw_blocks.append("--- DRIVER: init-F4-san ---")
        raw_blocks.append(out_san)
        if err_san:
            raw_blocks.append("STDERR: " + err_san)
        entries_san = parse_malloc_blocks(out_san)

        for site in [1763, 1765]:
            f4_line = F4_LINES[site]
            m = find_call_by_line(entries_san, f4_line)
            if len(m) != 1:
                print("ERROR: %s %d init-F4-san found %d matches (expected 1)" % (cname, site, len(m)))
                hard_stop = True
                k_val, sz_val = -1, -1
            else:
                k_val = m[0]["k"]
                sz_val = m[0]["size"]
            f3_line, f3_k, f3_sz = F3_K_MAP[(cname, site, "init-F4-san")]
            match_k = (k_val == f3_k)
            status = "PASS_EXACT_MATCH" if match_k else "DIVERGENT_K"
            tsv_rows.append((cname, str(site), "init-F4-san", "S4.cpp:%d" % f4_line, str(k_val), str(sz_val),
                             "S4.cpp:%d" % f3_line, str(f3_k), str(f3_sz), str(match_k), status))

        # 3. init-F4-san-AL (mapped via malloc_aligned: 1764)
        out_al, err_al = run_gdb(DRV_SAN_AL, GDB_ALIGNED_SCRIPT, cname, mode, ng, True)
        raw_blocks.append("--- DRIVER: init-F4-san-AL ---")
        raw_blocks.append(out_al)
        if err_al:
            raw_blocks.append("STDERR: " + err_al)
        entries_al = parse_aligned_blocks(out_al)

        site = 1764
        f4_line = F4_LINES[site]
        m = find_call_by_line(entries_al, f4_line)
        if len(m) != 1:
            print("ERROR: %s %d init-F4-san-AL found %d matches (expected 1)" % (cname, site, len(m)))
            hard_stop = True
            k_val, sz_val = -1, -1
        else:
            k_val = m[0]["k"]
            sz_val = m[0]["size"]
        f3_line, f3_k, f3_sz = F3_K_MAP[(cname, site, "init-F4-san-AL")]
        match_k = (k_val == f3_k)
        status = "PASS_EXACT_MATCH" if match_k else "DIVERGENT_K"
        tsv_rows.append((cname, str(site), "init-F4-san-AL", "S4.cpp:%d" % f4_line, str(k_val), str(sz_val),
                         "S4.cpp:%d" % f3_line, str(f3_k), str(f3_sz), str(match_k), status))

    # Write raw output and probe
    raw_text = "\n".join(raw_blocks) + "\n"
    with open(RAW_TXT, "w", encoding="utf-8") as fh:
        fh.write(raw_text)
    with open(PROBE_TXT, "w", encoding="utf-8") as fh:
        fh.write(raw_text)
    print("Wrote raw GDB trace to %s and %s" % (RAW_TXT, PROBE_TXT))

    # Write TSV table
    headers = ["combo", "defect_site", "driver", "F4_caller", "F4_k", "F4_size", "F3_caller", "F3_k", "F3_size", "k_match", "status"]
    with open(OUT_TSV, "w", encoding="utf-8") as fh:
        fh.write("# K_MAP_F4_S3R5.tsv -- GDB K-mapping on F4 apparatus (U286)\n")
        fh.write("\t".join(headers) + "\n")
        for r in tsv_rows:
            fh.write("\t".join(r) + "\n")
    print("Wrote %s (%d rows)" % (OUT_TSV, len(tsv_rows)))

    if hard_stop:
        sys.stderr.write("HARD STOP: Failed to find unique caller for one or more combo x site\n")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
