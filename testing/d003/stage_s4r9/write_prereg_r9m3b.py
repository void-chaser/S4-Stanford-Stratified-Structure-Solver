#!/usr/bin/env python3
# write_prereg_r9m3b.py -- write PREREG_E2E_R9M3B.tsv from the injection-free calibration, then record its
# sha256 and UTC time. Must run before ANY injection run (S-C7). New file (r9m3b).
import os, sys, hashlib, datetime

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b")
CALIB = os.path.join(EV, "CALIB_E2E_R9M3B.tsv")
OUT = os.path.join(EV, "PREREG_E2E_R9M3B.tsv")
SHAF = os.path.join(EV, "PREREG_E2E_R9M3B.sha256.txt")
TAB = chr(9)
NL = chr(10)
TOL = "rel<=1e-12 (element-wise, against the separate-process clean reference)"
OPTIONS = {
    "cf": "default options (ClosedForm path)",
    "fft": "DiscretizedEpsilon=True;DiscretizationResolution=8;PolarizationDecomposition=False",
    "kt": "DiscretizedEpsilon=True;DiscretizationResolution=8;SubpixelSmoothing=True;PolarizationDecomposition=False",
    "jones": "DiscretizedEpsilon=True;DiscretizationResolution=8;PolarizationDecomposition=True;PolarizationBasis=Jones",
    "nv": "DiscretizedEpsilon=True;DiscretizationResolution=8;PolarizationDecomposition=True;PolarizationBasis=Normal",
    "vl": "DiscretizedEpsilon=True;DiscretizationResolution=8;PolarizationDecomposition=True;PolarizationBasis=Default",
    "exp": "UseExperimentalFMM (Lua only)",
}
TARGET = {
    "cf": "S4/fmm/fmm_closed.cpp:40",
    "fft": {"plan": "S4/fmm/fmm_FFT.cpp:89", "exec": "S4/fmm/fmm_FFT.cpp:191", "s4malloc": "S4/fmm/fmm_FFT.cpp:75"},
    "kt": {"plan": "S4/fmm/fmm_kottke.cpp:93", "exec": "S4/fmm/fmm_kottke.cpp:271", "s4malloc": "S4/fmm/fmm_kottke.cpp:87"},
    "jones": "S4/fmm/fmm_PolBasisJones.cpp:108",
    "nv": "S4/fmm/fmm_PolBasisNV.cpp:59",
    "vl": "S4/fmm/fmm_PolBasisVL.cpp:58",
    "exp": "S4/fmm/fmm_experimental.cpp:40",
}
KGROUP = {
    "cf": "KGRP-M1-001/KGRP-M1-002",
    "fft": {"plan": "KGRP-M1-005", "exec": "KGRP-M1-004", "s4malloc": "KGRP-M1-006"},
    "kt": {"plan": "KGRP-M1-010", "exec": "KGRP-M1-009", "s4malloc": "KGRP-M1-011"},
    "jones": "KGRP-M1-008",
    "nv": "KGRP-M1-013",
    "vl": "KGRP-M1-015",
    "exp": "KGRP-M1-003",
}
VIS = {"py": 'RuntimeError:text~"GetPowerFlux"',
       "lua_batch": 'stderr_line~^"GetPoyntingFlux: "',
       "lua_repl": 'stderr_line~^"GetPoyntingFlux: " AND first solve returns nil'}
RETRY_SAME = {"py": "EQUAL_REF", "lua_batch": "NOT_APPLICABLE_PROCESS_EXIT", "lua_repl": "EQUAL_REF"}
POINTS = ([("py", "cf", "s4malloc"), ("py", "fft", "plan"), ("py", "fft", "exec"), ("py", "fft", "s4malloc"),
           ("py", "kt", "plan"), ("py", "kt", "exec"), ("py", "kt", "s4malloc"),
           ("py", "jones", "s4malloc"), ("py", "nv", "s4malloc"), ("py", "vl", "s4malloc")] +
          [("lua_batch", "cf", "s4malloc"), ("lua_batch", "fft", "plan"), ("lua_batch", "fft", "exec"),
           ("lua_batch", "fft", "s4malloc"), ("lua_batch", "kt", "plan"), ("lua_batch", "kt", "exec"),
           ("lua_batch", "kt", "s4malloc"), ("lua_batch", "jones", "s4malloc"), ("lua_batch", "nv", "s4malloc"),
           ("lua_batch", "vl", "s4malloc"), ("lua_batch", "exp", "s4malloc")] +
          [("lua_repl", "fft", "plan"), ("lua_repl", "cf", "s4malloc"), ("lua_repl", "kt", "s4malloc"),
           ("lua_repl", "vl", "s4malloc")])
CONTROL_GROUPS = {"py": ["cf", "fft", "kt", "jones", "nv", "vl"],
                  "lua_batch": ["cf", "fft", "kt", "jones", "nv", "vl", "exp"],
                  "lua_repl": ["cf", "fft", "kt", "vl"]}
COLUMNS = ["point_id", "frontend", "spec", "options", "inject_mode", "nth", "target_file_line", "calib_size",
           "exp_hit", "exp_visible", "exp_retry_same", "exp_retry_fresh", "tolerance", "m12_k_group", "is_control", "note"]


def read_calib():
    cal = {}
    for line in open(CALIB, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip(NL).split(TAB)
        if f[0] != "TARGET":
            continue
        key = (f[1], f[2], f[3])
        cal[key] = (int(f[4]), f[5], f[6])
    return cal


def target_for(spec, kind):
    t = TARGET[spec]
    return t if isinstance(t, str) else t[kind]


def kgroup_for(spec, kind):
    k = KGROUP[spec]
    return k if isinstance(k, str) else k[kind]


def main():
    cal = read_calib()
    rows = []
    missing = []
    for fe, spec, kind in POINTS:
        pid = "%s_%s_%s" % (fe, spec, kind)
        key = (fe, spec, kind)
        if key not in cal:
            missing.append(str(key))
            continue
        nth, size, site = cal[key]
        rows.append([pid, fe, spec, OPTIONS[spec], kind, str(nth), target_for(spec, kind), size, "1",
                     VIS[fe], RETRY_SAME[fe], "EQUAL_REF", TOL, kgroup_for(spec, kind), "NO", "injection point"])
    for fe in ("py", "lua_batch", "lua_repl"):
        for spec in CONTROL_GROUPS[fe]:
            pid = "%s_ctl_%s" % (fe, spec)
            rows.append([pid, fe, spec, OPTIONS[spec], "none", "0", "none (no injection)", "NA", "0",
                         "NONE (no error text, exit 0)", "EQUAL_REF", "EQUAL_REF", TOL, "CONTROL (no K needed)",
                         "YES", "no-injection control row"])
    if missing:
        print("MISSING_CALIB_TARGETS " + ",".join(missing))
        return 1
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("# PREREG_E2E_R9M3B.tsv -- pre-registration of the Python/Lua public-API E2E points (S-C7)." + NL)
        fh.write("# status: INFLUENCED. Written after the injection-free gdb calibration and BEFORE any injection run." + NL)
        fh.write("# tolerance: element-wise relative error <= 1e-12 against a clean reference obtained in a separate process; " + NL)
        fh.write("#   the same binary and code path are used, so corrupted state would move values far more than this band." + NL)
        fh.write("# exp_visible is the concrete error text, not any non-empty stderr (WITNESS/HIT lines do not count)." + NL)
        fh.write("# lua_batch retry_same is NOT_APPLICABLE_PROCESS_EXIT: S4/main_lua.c:229-239 closes the Lua state and exits" + NL)
        fh.write("#   in batch mode, so the same-object retry is observed in the REPL frontend instead (U341)." + NL)
        fh.write(TAB.join(COLUMNS) + NL)
        for r in rows:
            fh.write(TAB.join(r) + NL)
    data = open(OUT, "rb").read()
    sha = hashlib.sha256(data).hexdigest()
    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(SHAF, "w", encoding="utf-8") as fh:
        fh.write("# PREREG_E2E_R9M3B.sha256.txt -- sha256 and UTC time recorded immediately after the pre-registration" + NL)
        fh.write("file" + TAB + "sha256" + TAB + "bytes" + TAB + "rows" + TAB + "status" + TAB + "utc_recorded" + NL)
        fh.write("PREREG_E2E_R9M3B.tsv" + TAB + sha + TAB + str(len(data)) + TAB + str(len(rows)) + TAB + "INFLUENCED" + TAB + utc + NL)
    print("ROWS=%d POINTS=%d CONTROLS=%d" % (len(rows), len(POINTS), len(rows) - len(POINTS)))
    print("SHA256=%s" % sha)
    print("UTC=%s" % utc)
    print("WROTE " + OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
