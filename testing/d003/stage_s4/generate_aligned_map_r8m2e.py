#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2e; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# generate_aligned_map_r8m2e.py -- Map malloc_aligned calls via GDB for P05-S4 R8 M2e (U278).
import os, re, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2e")
EV = os.path.join(REPO, EV_REL)
DRV = os.path.join(EV, "build", "init-F3-san-AL")
RAW_TXT = os.path.join(EV, "ALIGNED_MAP_RAW_R8_M2e.txt")
OUT_TSV = os.path.join(EV, "ALIGNED_MAP_R8_M2e.tsv")
PROBE_TXT = os.path.join(EV, "probe", "generate_aligned_map_r8m2e.txt")

COMBOS = [
    ("closed2d-ng1", "closed2d", "1", 192),
    ("fft-ng5", "fft", "5", 960),
    ("kottke-ng5", "kottke", "5", 960),
]

GDB_CMDS = r"""set pagination off
set confirm off
set $count = 0

break __wrap_malloc_aligned
commands
silent
set $count = $count + 1
printf "CALL_MALLOC_ALIGNED k=%ld size=%zu alignment=%zu\n", $count, size, alignment
bt 4
continue
end

run pattern both 4 3
quit
"""


def main():
    tmp_dir = os.path.join(EV, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    os.makedirs(os.path.join(EV, "probe"), exist_ok=True)
    gdb_script = os.path.join(tmp_dir, "map_aligned.gdb")
    with open(gdb_script, "w") as fh:
        fh.write(GDB_CMDS)

    raw_output_blocks = []
    rows = []
    found_1764 = {}

    for cname, mode, ng, exp_sz in COMBOS:
        env = os.environ.copy()
        env["FMM_MODE"] = mode
        env["S4FMM_NG"] = ng
        env["ASAN_OPTIONS"] = "detect_leaks=0:abort_on_error=0"
        env["UBSAN_OPTIONS"] = "abort_on_error=0"
        env.pop("S4FMM_INJECT", None)
        env.pop("S4_FAIL_ALLOC_AT", None)

        cmd = ["gdb", "-batch", "-x", gdb_script, "--args", DRV, "pattern", "both", "4", "3"]
        p = subprocess.run(cmd, env=env, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        raw_output_blocks.append("================================================================================")
        raw_output_blocks.append("COMBO: %s (mode=%s, ng=%s)" % (cname, mode, ng))
        raw_output_blocks.append("================================================================================")
        raw_output_blocks.append(p.stdout)
        if p.stderr:
            raw_output_blocks.append("--- STDERR ---")
            raw_output_blocks.append(p.stderr)

        # Parse GDB stdout
        blocks = p.stdout.split("CALL_MALLOC_ALIGNED ")
        combo_1764_calls = []

        for b in blocks[1:]:
            b_lines = b.splitlines()
            header = b_lines[0]
            m_hdr = re.match(r"^k=(\d+)\s+size=(\d+)\s+alignment=(\d+)", header)
            if not m_hdr:
                continue
            k = int(m_hdr.group(1))
            sz = int(m_hdr.group(2))
            align = int(m_hdr.group(3))

            frames = []
            for l in b_lines[1:]:
                if l.startswith("CALL_MALLOC_ALIGNED ") or l.startswith("[Inferior ") or l.startswith("Program exited"):
                    break
                m_fr = re.match(r"^#(\d+)\s+(?:0x[0-9a-fA-F]+\s+in\s+)?([^\s(]+).*?(?:at\s+([^:]+):(\d+))?$", l.strip())
                if m_fr:
                    fnum = int(m_fr.group(1))
                    func = m_fr.group(2)
                    fpath = os.path.basename(m_fr.group(3)) if m_fr.group(3) else "unknown"
                    fline = int(m_fr.group(4)) if m_fr.group(4) else -1
                    frames.append((fnum, func, fpath, fline, l.strip()))

            # Check if this call originates from S4.cpp:1764
            # Look through frames #1, #2, #3
            caller_file = "unknown"
            caller_line = -1
            caller_func = "unknown"
            is_1764 = False

            for fnum, func, fpath, fline, full_l in frames:
                if fnum == 0:
                    continue
                if fpath == "S4.cpp" and fline == 1764:
                    is_1764 = True
                    caller_file = fpath
                    caller_line = fline
                    caller_func = func
                    break
                # If not 1764, pick the first non-wrap frame as caller
                if caller_file == "unknown" and fnum >= 1:
                    caller_file = fpath
                    caller_line = fline
                    caller_func = func

            tag = "other"
            notes = "-"
            if is_1764:
                tag = "1764_ab"
                notes = "S->solution->ab via malloc_aligned (F3 S4.cpp:1764; target site for -AL injection)"
                combo_1764_calls.append((k, sz))
            elif caller_file == "S4.cpp" and caller_line in (311, 381):
                tag = "S4_Simulation_New_%d" % caller_line
                notes = "lattice / grid setup in S4_Simulation_New (S4.cpp:%d)" % caller_line
            elif caller_file == "S4.cpp" and caller_line == 2310:
                tag = "ComputeLayerModes_2310"
                notes = "LayerModes allocation in Simulation_ComputeLayerModes"

            rows.append({
                "driver": "init-F3-san-AL",
                "combo": cname,
                "k": str(k),
                "size": str(sz),
                "caller_file": caller_file,
                "caller_line": str(caller_line),
                "caller_func": caller_func,
                "tag": tag,
                "notes": notes,
            })

        found_1764[cname] = combo_1764_calls

    # Write raw output
    raw_str = "\n".join(raw_output_blocks) + "\n"
    with open(RAW_TXT, "w", encoding="utf-8") as fh:
        fh.write(raw_str)
    with open(PROBE_TXT, "w", encoding="utf-8") as fh:
        fh.write(raw_str)

    # Write TSV
    headers = ["driver", "combo", "k", "size", "caller_file", "caller_line", "caller_func", "tag", "notes"]
    with open(OUT_TSV, "w", encoding="utf-8") as fh:
        fh.write("# ALIGNED_MAP_R8_M2e.tsv -- malloc_aligned call mapping across 3 combinations (init-F3-san-AL)\n")
        fh.write("\t".join(headers) + "\n")
        for r in rows:
            fh.write("\t".join(r[h] for h in headers) + "\n")

    print("generate_aligned_map_r8m2e: wrote %s and %s" % (RAW_TXT, OUT_TSV))
    print("Found 1764 calls:", found_1764)

    # Hard stop verification (U278)
    for cname, mode, ng, exp_sz in COMBOS:
        calls = found_1764.get(cname, [])
        if len(calls) != 1:
            sys.stderr.write("HARD STOP: Combo %s has %d calls to 1764 (expected exactly 1 unique call)\n" % (cname, len(calls)))
            return 2
        k_val, sz_val = calls[0]
        if sz_val != exp_sz:
            sys.stderr.write("HARD STOP: Combo %s size %d != expected %d\n" % (cname, sz_val, exp_sz))
            return 2
        print("Combo %s: UNIQUE 1764 confirmed at K=%d, size=%d (matches expected %d)" % (cname, k_val, sz_val, exp_sz))

    return 0


if __name__ == "__main__":
    sys.exit(main())
