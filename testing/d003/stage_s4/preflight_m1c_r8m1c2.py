#!/usr/bin/env python3
# preflight_m1c_r8m1c2.py -- P05-S4 R8 M1c2 preflight (brief section 5). Runs BEFORE any driver run.
# Writes $EV/PREFLIGHT_M1C_R8_M1c2.txt and ends with PREFLIGHT_OK only when every check passes.
# Checks:
#   - six drivers executable; sha256 equals the M1c prereg driver_sha256 (F2 and F3, per driver name);
#   - four historical prereg sha256 values equal the header record in registries/s4r7/REGISTRY_S4_PRE_R7_M3.tsv
#     (G5, G6, G6c = the three header lines; CONTROL = the RECORD of the frozen table);
#   - runner and judge sha256 equal the start gate record (run_r6c_state.py, r6c2_seam_state.py,
#     r6c_judge.py, r6c2_seam_judge.py);
#   - frozen fact table sha256 equals PREREG_M1C_FACTS_RECORD_R8_M1c2.txt output_sha256;
#   - gdb --version first line (written by the shell wrapper in the same run);
#   - EV/m1c_f2 and EV/m1c_f3 do not exist.
# Usage: python3 -I -B preflight_m1c_r8m1c2.py
import os, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c2")
EVROOT = os.path.join(REPO, "checkpoints", "p05", "evidence")
REG = os.path.join(REPO, "checkpoints", "p05", "registries")
os.makedirs(os.path.join(EV, "tmp"), exist_ok=True)
OUT = os.path.join(EV, "PREFLIGHT_M1C_R8_M1c2.txt")

lines = []
fails = []


def sha256_file(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def rec(name, ok, detail=""):
    lines.append("%s\t%s\t%s" % ("PASS" if ok else "FAIL", name, detail))
    if not ok:
        fails.append(name)


# ---- M1c prereg: driver name -> sha256 (F2 and F3) ----
prereg_path = os.path.join(REG, "s4r8", "M1a", "REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv")
prereg_drv = {}
with open(prereg_path, encoding="utf-8") as fh:
    head = fh.readline().rstrip("\n").split("\t")
    for line in fh:
        p = dict(zip(head, line.rstrip("\n").split("\t")))
        prereg_drv[(p["driver_name"], p["tree"])] = p["driver_sha256"]

DRIVERS = [
    ("F2", "r6bstate-F2-dbg", os.path.join(EVROOT, "p05-s4r7", "drivers_r7", "r6bstate-F2-dbg", "driver")),
    ("F2", "r6bseam-seamF-F2", os.path.join(EVROOT, "p05-s4r7", "drivers_r7", "r6bseam-seamF-F2", "driver")),
    ("F2", "r6bseam-fmmret-F2", os.path.join(EVROOT, "p05-s4r7", "drivers_r7", "r6bseam-fmmret-F2", "driver")),
    ("F3", "r6bstate-F3-dbg", os.path.join(EVROOT, "p05-s4r8", "drivers_r8m1", "r6bstate-F3-dbg", "driver")),
    ("F3", "r6bseam-seamF-F3", os.path.join(EVROOT, "p05-s4r8", "drivers_r8m1", "r6bseam-seamF-F3", "driver")),
    ("F3", "r6bseam-fmmret-F3", os.path.join(EVROOT, "p05-s4r8", "drivers_r8m1", "r6bseam-fmmret-F3", "driver")),
]
for tree, name, path in DRIVERS:
    ex = os.path.isfile(path) and os.access(path, os.X_OK)
    rec("DRIVER_EXEC %s %s" % (tree, name), ex, path)
    if ex:
        got = sha256_file(path)
        want = prereg_drv.get((name, tree), "MISSING")
        rec("DRIVER_SHA256 %s %s" % (tree, name), got == want, "got=%s want=%s" % (got, want))
    else:
        rec("DRIVER_SHA256 %s %s" % (tree, name), False, "not executable")

# ---- historical prereg sha256 vs R7 header record ----
hdr = {}
with open(os.path.join(REG, "s4r7", "REGISTRY_S4_PRE_R7_M3.tsv"), encoding="utf-8") as fh:
    for line in fh:
        if not line.startswith("#"):
            break
        if line.startswith("#   "):
            parts = line.split()
            # "#   G5  <path>  sha256 <hex>"
            if len(parts) >= 5 and parts[3] == "sha256":
                hdr[parts[1]] = (parts[2], parts[4])
for grp, relp in (("G5", "s4r6c/REGISTRY_S4_PRE_R6b_STATE_v2.tsv"),
                  ("G6", "s4r6c/REGISTRY_S4_PRE_R6c_SEAM.tsv"),
                  ("G6c", "s4r6c/REGISTRY_S4_PRE_R6c_SEAM_CONTROL.tsv")):
    path = os.path.join(REG, relp)
    got = sha256_file(path) if os.path.isfile(path) else "missing"
    want = hdr.get(grp, ("?", "?"))[1]
    rec("HIST_PREREG %s" % grp, got == want, "got=%s header=%s" % (got, want))
# CONTROL is a fourth historical prereg; its frozen record is the M1c facts RECORD source line
ctrl_path = os.path.join(REG, "s4r6b", "REGISTRY_S4_PRE_R6b_CONTROL.tsv")
ctrl_got = sha256_file(ctrl_path) if os.path.isfile(ctrl_path) else "missing"
rec_path = os.path.join(EV, "PREREG_M1C_FACTS_RECORD_R8_M1c2.txt")
ctrl_rec = ""
if os.path.isfile(rec_path):
    with open(rec_path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("source CONTROL_R6B "):
                ctrl_rec = line.strip().split("sha256=")[-1]
rec("HIST_PREREG CONTROL", ctrl_got == ctrl_rec and ctrl_got != "missing",
    "got=%s record=%s" % (ctrl_got, ctrl_rec))

# ---- runner and judge sha256 vs start gate record ----
gate_start = os.path.join(EV, "GATE_R8_M1c2_START.txt")
gate_rec = {}
if os.path.isfile(gate_start):
    with open(gate_start, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("RECORD\tSHA256_"):
                parts = line.rstrip("\n").split("\t")
                gate_rec[parts[1][len("SHA256_"):]] = parts[2][len("value="):]
for name in ("run_r6c_state.py", "r6c2_seam_state.py", "r6c_judge.py", "r6c2_seam_judge.py"):
    path = os.path.join(REPO, "testing", "d003", "stage_s4", name)
    got = sha256_file(path)
    want = gate_rec.get(name, "NO_GATE_RECORD")
    rec("RUNNER_JUDGE_SHA256 %s" % name, got == want, "got=%s gate=%s" % (got, want))

# ---- frozen fact table vs RECORD ----
frozen = os.path.join(EV, "PREREG_M1C_FACTS_R8_M1c2.tsv")
got_frozen = sha256_file(frozen) if os.path.isfile(frozen) else "missing"
want_frozen = ""
if os.path.isfile(rec_path):
    with open(rec_path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("output_sha256="):
                want_frozen = line.strip().split("=", 1)[1]
rec("FROZEN_TABLE_SHA256", got_frozen == want_frozen and got_frozen != "missing",
    "got=%s record=%s" % (got_frozen, want_frozen))
with open(frozen, encoding="utf-8") as fh:
    nrows = sum(1 for l in fh if l and not l.startswith("#")) - 1  # minus header
rec("FROZEN_TABLE_ROWS", nrows == 472, "rows=%d" % nrows)

# ---- output dirs must not exist ----
for d in ("m1c_f2", "m1c_f3"):
    p = os.path.join(EV, d)
    rec("NO_OUTDIR %s" % d, not os.path.exists(p), p)

try:
    _g = subprocess.run(["gdb", "--version"], capture_output=True, text=True, timeout=60)
    _first = (_g.stdout or _g.stderr or "").splitlines()[0] if (_g.stdout or _g.stderr) else "EMPTY"
except Exception as _e:  # gdb missing or not runnable -> preflight fails
    _first = "ERROR %s" % _e
    fails.append("GDB_VERSION")
lines.append("GDB_VERSION_FIRST_LINE\t%s" % _first)
if _first.startswith("ERROR") or _first == "EMPTY":
    lines.append("FAIL\tGDB_VERSION\t%s" % _first)
lines.append("FAILS=%d" % len(fails))
lines.append("PREFLIGHT_OK" if not fails else "PREFLIGHT_FAILED")
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
print("PREFLIGHT_FAILS=%d" % len(fails))
sys.exit(1 if fails else 0)
