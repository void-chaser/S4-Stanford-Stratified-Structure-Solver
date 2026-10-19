#!/usr/bin/env python3
# relr1_registry.py -- copy the round's small result tables to checkpoints/p05/registries/rel-r1/,
# assemble RESULTS_RELR1.tsv from the per-unit observation files, and write SHA256SUMS.txt.
# Every copy is verified byte-identical (sha256) to its evidence original; files larger than 1 MB
# are never copied (they stay in the evidence directory and are named in the report instead).
import os, sys, hashlib, shutil

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r1")
REG = os.path.join(REPO, "checkpoints/p05/registries/rel-r1")
TAB = chr(9)
NL = chr(10)
MAXB = 1024 * 1024
FILES = ["PREREG_RELR1.tsv", "PREREG_RELR1.tsv.sha256.txt", "BUILD_RELR1.tsv", "TREES_RELR1.tsv",
         "WRITE_TARGETS_RELR1.tsv", "VERDICT_RELR1.tsv", "SUMMARY_RELR1.txt", "WARN_DIFF_RELR1.txt",
         "U_DIFF_RELR1.tsv", "POSCTRL_RELR1.txt", "POSCTRL_MAKETEST_RELR1.txt",
         "GATE_RELR1_start.txt", "MAKETEST_UNITS_RELR1.tsv", "MAKETEST_RECON_RELR1.tsv",
         "MAKETEST_VERDICT_RELR1.tsv", "RESULTS_RELR1.tsv"]
OPTIONAL = ["GATE_RELR1_end.txt", "ERRATA_RELR1.txt"]


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def assemble_results():
    ud = os.path.join(EV, "units")
    keys = ["unit_id", "suite", "tree", "pass", "status", "rc", "signal", "timed_out",
            "stdout_sha256", "stderr_sha256", "numdiff_rc", "numdiff_relmax", "dur_s", "extra"]
    rows = []
    if os.path.isdir(ud):
        for n in sorted(os.listdir(ud)):
            if not n.endswith(".tsv"):
                continue
            d = {}
            for line in open(os.path.join(ud, n), encoding="utf-8"):
                if not line.strip() or line.startswith("#"):
                    continue
                k, _, v = line.rstrip(NL).partition(TAB)
                d[k] = v
            rows.append(d)
    out = os.path.join(EV, "RESULTS_RELR1.tsv")
    lines = ["# RESULTS_RELR1.tsv -- consolidated per-unit observations of REL-R1 (T2/T3/T5/T6/T7; T1 is in",
             "# MAKETEST_*.tsv, T4 is in this table, T8/MPI/U rows are declared in PREREG_RELR1.tsv).",
             "# Every row was written by the round's own runners from rc, signals and file sha256 only.",
             TAB.join(keys)]
    for d in rows:
        lines.append(TAB.join([d.get(k, "") for k in keys]))
    open(out, "w", encoding="utf-8").write(NL.join(lines) + NL)
    return out, len(rows)


def u_diff():
    p = os.path.join(EV, "U_DIFF_RELR1.tsv")
    rows = ["# U_DIFF_RELR1.tsv -- REL-R1 record of the upstream reference tree U (7fd00a2), record only",
            "# Task brief section 5: U is the upstream original master; any U vs B difference belongs to P04 and",
            "# is not a failure of this round.  U could not be built in this environment.",
            TAB.join(["item", "value"])]
    b = os.path.join(EV, "BUILD_RELR1.tsv")
    status = "MISSING"
    reason = ""
    if os.path.isfile(b):
        for line in open(b, encoding="utf-8"):
            if line.startswith("U" + TAB):
                f = line.rstrip(NL).split(TAB)
                if f[1] == "lua_frontend":
                    status = f[5]
                    log = f[6]
                    if os.path.isfile(os.path.join(REPO, log)):
                        for l in open(os.path.join(REPO, log), encoding="utf-8", errors="replace"):
                            if ": error:" in l:
                                reason = l.strip()[:220]
                                break
    rows.append(TAB.join(["U_STATUS", "U_BUILD_UNAVAILABLE" if status == "U_BUILD_UNAVAILABLE" else status]))
    rows.append(TAB.join(["U_FIRST_COMPILE_ERROR", reason or "none recorded"]))
    rows.append(TAB.join(["U_T2", "not run: build unavailable"]))
    rows.append(TAB.join(["U_T3", "not run: build unavailable"]))
    rows.append(TAB.join(["U_VS_B_DIFFERENCE", "not observed; recorded only"]))
    open(p, "w", encoding="utf-8").write(NL.join(rows) + NL)
    return p


def main():
    os.makedirs(REG, exist_ok=True)
    res, nres = assemble_results()
    ud = u_diff()
    print("RESULTS_RELR1.tsv rows=%d" % nres)
    todo = FILES + [f for f in OPTIONAL if os.path.isfile(os.path.join(EV, f))]
    seen = set()
    todo = [x for x in todo if not (x in seen or seen.add(x))]
    sums = []
    bad = []
    for name in todo:
        src = os.path.join(EV, name)
        if not os.path.isfile(src):
            bad.append(("MISSING_EVIDENCE", name))
            continue
        size = os.path.getsize(src)
        if size > MAXB:
            bad.append(("TOO_LARGE_NOT_COPIED", "%s %d bytes" % (name, size)))
            continue
        dst = os.path.join(REG, name)
        shutil.copyfile(src, dst)
        a, b = sha_f(src), sha_f(dst)
        if a != b:
            bad.append(("SHA_MISMATCH", name))
        sums.append((a, name))
        print("COPY %-40s %d bytes %s %s" % (name, size, a[:16], "OK" if a == b else "MISMATCH"))
    with open(os.path.join(REG, "SHA256SUMS.txt"), "w", encoding="utf-8") as fh:
        fh.write("# SHA256SUMS.txt -- P05 delivery round REL-R1 registry (copies verified against the evidence originals)" + NL)
        for a, name in sums:
            fh.write("%s  %s" % (a, name) + NL)
    print("REGISTRY_FILES=%d" % len(sums))
    for k, v in bad:
        print("PROBLEM" + TAB + k + TAB + v)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
