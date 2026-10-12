#!/usr/bin/env python3
# run_r5_san_inject.py -- P05-S4 R5-5 (V4): run every F injection point on the SANITIZER builds and record
#   (a) the class (judge_d003.classify on facts rc, rc1, rc2, hit) -- compared with the non-sanitizer run of the same point;
#   (b) the sanitizer findings (ASan / LSan / UBSan report lines, with the first S4 frame of each report).
# New file.  judge_d003.py and matrix_r2.py are IMPORTED / read, not modified.
#
#   python3 -I -B testing/d003/stage_s4/run_r5_san_inject.py SAN_DIR EV_DIR OUT_TSV
#     SAN_DIR : $EV/san  (drivers in $EV/san/drivers/<name>/driver-d003)
#     EV_DIR  : $EV      (inputs: p05-s3r... no: p05-s4r3/REGISTRY_S4_PRE_R3.tsv etc. are read from checkpoints/p05/evidence)
# Four point sets (every F injection point of R3, R4 and R5-3):
#   R3   : 141 in-scope points, F rows.  Driver san-plain-F.  case "t4/" for twice (TWICE=slab), "r3/" for once.
#   R4M  : 25 F rows of the R4 main matrix.  Driver by run_r4_matrix.library_for (fmmret-F for family E, seamF otherwise).
#          Once route (no TWICE), as in R4.
#   R4PC : 22 R3-INVALID plan points, F, plancall:K:M (R4 plancall, no TWICE, as in R4).  Driver san-plain-F.
#   M2   : 36 M=2 plan points, F, plancall:K:2 (R5-3, TWICE=slab for twice, as in run_r5_planm.py).  Driver san-plain-F.
import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
D003 = os.path.join(REPO, "testing", "d003")
sys.path.insert(0, D003)
sys.path.insert(0, HERE)

import judge_d003 as J  # noqa: E402
import matrix_r2 as M  # noqa: E402
import run_r4_matrix as R4M  # noqa: E402  (library_for only; the module is not executed)

GRID = ["pattern", "both", "4", "3"]
TIMEOUT_S = 600
EVR = os.path.join(REPO, "checkpoints", "p05", "evidence")

SAN_CAT = {"malloc": "s4malloc", "plan": "plan", "exec": "exec"}


def read_tsv(path):
    rows, header = [], None
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                header = f
                continue
            rows.append(dict(zip(header, f)))
    return rows


def sanitizer_findings(prefix_dir, name):
    """Parse ASan/LSan/UBSan reports written to log_path=<dir>/<name> (ASan appends .<pid>)."""
    out = []
    for path in sorted(glob.glob(os.path.join(prefix_dir, name + "*"))):
        with open(path, "rb") as fh:
            text = fh.read().decode("utf-8", errors="replace")
        for m in re.finditer(r"ERROR: (AddressSanitizer|LeakSanitizer): ([^\n]+)", text):
            kind = m.group(1)
            what = m.group(2).split(" on address")[0].split(" ")[0]
            if kind == "LeakSanitizer":
                bm = re.search(r"Direct leak of (\d+) byte", text)
                nb = bm.group(1) if bm else "?"
                out.append(("leak", nb, first_s4_frame(text)))
            else:
                out.append((what, "", first_s4_frame(text)))
        for m in re.finditer(r"runtime error: ([^\n]+)", text):
            out.append(("ubsan", m.group(1)[:60], first_s4_frame(text)))
    return out


def first_s4_frame(text):
    m = re.search(r"#\d+ 0x[0-9a-f]+ in (\S+)", text)
    return m.group(1) if m else "-"


def run(driver, row, runs_dir, logdir, env_extra):
    name = row["case"].replace("/", "__") + "__" + row["tree"]
    env = dict(os.environ)
    env.pop("S4FMM_TWICE", None)
    env["FMM_MODE"] = row["mode"]
    env["S4FMM_NG"] = row.get("ng", "9")
    if row.get("request") not in (None, "", "-"):
        env["S4FMM_INJECT"] = row["request"]
    if row.get("nth") not in (None, "", "-"):
        env["S4FMM_NTH"] = row["nth"]
    env.update(env_extra)
    env["ASAN_OPTIONS"] = "detect_leaks=1:halt_on_error=0:log_path=%s" % os.path.join(logdir, name)
    env["UBSAN_OPTIONS"] = "print_stacktrace=1"
    rc = None
    out = b""
    try:
        proc = subprocess.run([driver] + GRID, env=env, cwd=runs_dir, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=TIMEOUT_S)
        rc = proc.returncode
        out = proc.stdout
    except subprocess.TimeoutExpired as exc:
        rc = 124
        out = exc.stdout or b""
    except OSError as exc:
        out = ("RUNNER: could not start driver: %s\n" % exc).encode()
    if rc is not None and rc < 0:
        rc = 128 - rc
    logp = os.path.join(runs_dir, name + ".log")
    with open(logp, "wb") as fh:
        fh.write(out)
    return rc, logp, name


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: run_r5_san_inject.py SAN_DIR EV_DIR OUT_TSV")
    san, evdir, out_tsv = argv[1], argv[2], argv[3]
    drv = {n: os.path.join(san, "drivers", n, "driver-d003") for n in
           ("san-plain-F", "seamF", "fmmret-F")}
    for n, p in drv.items():
        if not (os.path.isfile(p) and os.access(p, os.X_OK)):
            raise SystemExit("REFUSED: sanitizer driver missing: %s" % p)
    runs_dir = os.path.join(evdir, "san", "runs")
    logdir = os.path.join(evdir, "san", "logs")
    os.makedirs(runs_dir, exist_ok=True)
    os.makedirs(logdir, exist_ok=True)

    items = []   # (set, row-dict-for-run, driver-name, expected-from-prereg, nonsan_class, inj_call, real, tag)

    # R3: 141 F rows
    r3 = os.path.join(EVR, "p05-s4r3")
    pre3 = read_tsv(os.path.join(r3, "REGISTRY_S4_PRE_R3.tsv"))
    fcm = read_tsv(os.path.join(r3, "FIELDCALL_MAP.tsv"))
    fcmap = {(r["route"], r["mode"], r["category"], r["nth"]): int(r["field_call"]) for r in fcm}
    res3 = {(r["point_id"], r["tree"]): r for r in read_tsv(os.path.join(r3, "RESULTS_R3.tsv"))}
    for p in pre3:
        if p["tree"] != "F":
            continue
        pid = p["point_id"]
        cat, nth, mode = p["category"], p["NTH"], p["mode"]
        route = "twice" if pid.startswith("M-twice") else "once"
        ic = fcmap.get((route, mode, cat, nth))
        if ic is None:
            raise SystemExit("no field_call for %s" % pid)
        case = ("t4/" if route == "twice" else "r3/") + pid
        row = {"case": case, "tree": "F", "mode": mode, "request": SAN_CAT[cat], "nth": nth, "ng": "9"}
        env_extra = {"S4FMM_TWICE": "slab"} if route == "twice" else {}
        ns = res3.get((pid, "F"), {})
        items.append(("R3", row, "san-plain-F", p["expected_class"] if "expected_class" in p else p.get("expected_class", ""),
                      ns.get("observed_class", "-"), ic, cat != "exec", pid, env_extra))

    # R4 main matrix: 25 F rows, library by run_r4_matrix.library_for
    r4 = os.path.join(EVR, "p05-s4r4")
    pre4 = read_tsv(os.path.join(r4, "REGISTRY_S4_PRE_R4.tsv"))
    res4 = {r["point_id"]: r for r in read_tsv(os.path.join(r4, "RESULTS_R4.tsv"))}
    for p in pre4:
        if p["tree"] != "F":
            continue
        lib = R4M.library_for(p)
        row = {"case": p["point_id"], "tree": "F", "mode": p["mode"], "request": p["request"], "nth": "-", "ng": "9"}
        ic = 1
        items.append(("R4M", row, lib, p["expected_class"], res4.get(p["point_id"], {}).get("obs_pass1", "-"), ic,
                      True, p["point_id"], {}))

    # R4 plancall: 22 R3-INVALID plan points, F rows, pass1 result as non-sanitizer reference
    pc = read_tsv(os.path.join(r4, "plancall", "RESULTS_R4_PLANCALL_pass1.tsv"))
    for r in pc:
        if r["tree"] != "F":
            continue
        row = {"case": "R4B-" + r["point_id"], "tree": "F", "mode": r["mode"], "request": r["request"], "nth": "-", "ng": "9"}
        items.append(("R4PC", row, "san-plain-F", r["expected"], r["observed"], int(r["inj_call"]), True, r["point_id"], {}))

    # R5-3: 36 M=2 plan points, F rows, pass1 result as non-sanitizer reference
    m2 = read_tsv(os.path.join(EVR, "p05-s4r5", "planm", "RESULTS_R5_PLANM_pass1.tsv"))
    for r in m2:
        if r["tree"] != "F":
            continue
        env_extra = {"S4FMM_TWICE": "slab"} if r["route"] == "twice" else {}
        row = {"case": "R5M2-" + r["point_id"], "tree": "F", "mode": r["mode"], "request": r["request"], "nth": "-", "ng": "9"}
        items.append(("M2", row, "san-plain-F", r["expected"], r["observed"], int(r["inj_call"]), True, r["point_id"], env_extra))

    header = ["set", "point_id", "driver", "rc", "rc1", "rc2", "hit", "class_san", "class_nonsan", "same_class",
              "san_findings", "log"]
    lines = ["# SAN_R5.tsv -- P05-S4 R5-5 (V4): every F injection point on the sanitizer builds.",
             "# class_san: judge_d003.classify on the sanitizer run.  class_nonsan: observed class of the same point in the",
             "# non-sanitizer run of the same round (R3 RESULTS_R3 / R4 RESULTS_R4 or plancall pass1 / R5-3 pass1).",
             "# san_findings: kind:detail:first_S4_frame, ';'-separated.  kind = leak (bytes), heap-buffer-overflow, heap-use-after-free,",
             "# double-free, ubsan (runtime error text).  Sanitizer report files: san/logs/<point>.<pid>."]
    lines.append("\t".join(header))
    n_run = 0
    for setname, row, lib, _exp, nonsan, ic, real, pid, env_extra in items:
        driver = drv[lib]
        rc, logp, name = run(driver, row, runs_dir, logdir, env_extra)
        with open(logp, "rb") as fh:
            text = fh.read().decode("utf-8", errors="replace")
        facts = J.facts_from_log(text)
        cls, label, reason = J.classify(rc, facts["rc1"], facts["rc2"], facts["hit"],
                                        control=False, real=real, inj_call=ic)
        if cls == "UNDECLARED":
            raise SystemExit("UNDECLARED for %s: stop" % pid)
        findings = sanitizer_findings(logdir, name)
        fstr = ";".join("%s:%s:%s" % (k, d, f) for k, d, f in findings) if findings else "none"
        same = "SAME" if cls == nonsan else "DIFF"
        lines.append("\t".join([setname, pid, lib, str(rc), str(facts["rc1"]), str(facts["rc2"]), str(facts["hit"]),
                                cls, nonsan, same, fstr, os.path.relpath(logp, evdir)]))
        n_run += 1
    with open(out_tsv, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("runs=%d -> %s" % (n_run, out_tsv))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
