#!/usr/bin/env python3
# relr4_mpi.py -- T3 of REL-R4: MPI precheck, S4mpi builds and runs (task brief section 5.4).
#   precheck : mpirun -np 2 true + a minimal MPI program that prints its rank
#   build --tree T : make build/S4mpi CC=mpicc CXX=mpicxx MPI_INC=... MPI_LIB=... (U adds CFLAGS=-Wno-error=int-conversion)
#                    and checks 'With MPI support' in the version banner
#   run --example E --tree T --np N --pass P : one independent cwd per run
#   compare : criteria a (merged -np 4 vs -np 1 and vs T1 non-MPI), b (B vs F4 byte identical),
#             c (U vs F4 categories), d (missing ../1d/binary_grating.txt recorded only)
# Every write stays under $EV.
import os, sys, subprocess, hashlib, datetime, time

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r4")
TREES = {"U": os.path.join(EV, "upstream", "S4"),
         "B": os.path.join(EV, "trees", "B"),
         "F4": os.path.join(EV, "trees", "F4"),
         "M": os.path.join(EV, "trees", "M"),
         "M2": os.path.join(EV, "trees", "M2"),
         "M3": os.path.join(EV, "trees", "M3")}
MPI = os.path.join(EV, "mpi")
UNITS = os.path.join(EV, "units_t3")
TAB = chr(9)
NL = chr(10)
EXAMPLES = ["examples/MPI_example/binary_grating_mpi.lua", "examples/MPI_example/mpi_simple.lua"]
TIMEOUT_S = 1800


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def eid(rel):
    s = rel[len("examples/"):].replace("/", "__")
    return s[:-4] if s.endswith(".lua") else s


def write_unit(rec):
    os.makedirs(UNITS, exist_ok=True)
    keys = ["unit_id", "suite", "tree", "pass", "status", "rc", "signal", "timed_out", "stdout_sha256",
            "stderr_sha256", "stdout_path", "stderr_path", "files", "dur_s", "utc", "extra"]
    out = os.path.join(UNITS, rec["unit_id"] + ".tsv")
    lines = ["# per-unit observation for REL-R4 T3; read by column name by relr4_verdict.py"]
    for k in keys:
        lines.append(k + TAB + str(rec.get(k, "")))
    open(out, "w", encoding="utf-8").write(NL.join(lines) + NL)


def mpi_flags():
    c = subprocess.run(["mpicc", "--showme:compile"], capture_output=True, text=True).stdout.strip()
    l = subprocess.run(["mpicc", "--showme:link"], capture_output=True, text=True).stdout.strip()
    return c, l


def precheck():
    os.makedirs(MPI, exist_ok=True)
    rows = []
    # 1. mpirun -np 2 true
    p = subprocess.run(["mpirun", "-np", "2", "true"], capture_output=True, text=True)
    rows.append(TAB.join(["T3_PRECHECK_MPIRUN_TRUE", "PASS" if p.returncode == 0 else "FAIL", "rc=%d" % p.returncode,
                          (p.stdout + p.stderr).strip()[:200] or "no output"]))
    with open(os.path.join(MPI, "PRE_MPIRUN_TRUE.log"), "w", encoding="utf-8") as fh:
        fh.write("cmd=mpirun -np 2 true rc=%d" % p.returncode + NL + p.stdout + p.stderr)
    # 2. minimal rank-printing MPI program
    src = os.path.join(REPO, "testing/d003/stage_relr4/mpi_probe_relr4.c")
    exe = os.path.join(MPI, "mpi_probe_relr4")
    cc = subprocess.run(["mpicc", "-O0", "-g", src, "-o", exe], capture_output=True, text=True)
    if cc.returncode != 0:
        rows.append(TAB.join(["T3_PRECHECK_RANK_PROBE", "FAIL", "compile rc=%d" % cc.returncode,
                              (cc.stdout + cc.stderr).strip()[:200]]))
    else:
        p2 = subprocess.run(["mpirun", "-np", "2", exe], capture_output=True, text=True)
        ranks = sorted(l.strip() for l in p2.stdout.splitlines() if l.strip().isdigit())
        ok = p2.returncode == 0 and ranks == ["0", "1"]
        rows.append(TAB.join(["T3_PRECHECK_RANK_PROBE", "PASS" if ok else "FAIL", "ranks=" + ",".join(ranks),
                              "rc=%d" % p2.returncode]))
        with open(os.path.join(MPI, "PRE_RANK_PROBE.log"), "w", encoding="utf-8") as fh:
            fh.write("compile: mpicc -O0 -g %s -o %s rc=%d" % (src, exe, cc.returncode) + NL)
            fh.write("run: mpirun -np 2 %s rc=%d" % (exe, p2.returncode) + NL + p2.stdout + p2.stderr)
    out = os.path.join(MPI, "PRECHECK_RELR4.tsv")
    open(out, "w", encoding="utf-8").write(NL.join(["# PRECHECK_RELR4.tsv -- T3 MPI precheck (task brief section 5.4.1)"] + rows) + NL)
    for r in rows:
        print(r)
    print("WROTE " + os.path.relpath(out, REPO))
    return 0 if all(r.split(TAB)[1] == "PASS" for r in rows) else 1


def build(tree):
    tdir = TREES[tree]
    logdir = os.path.join(EV, "build_logs")
    os.makedirs(logdir, exist_ok=True)
    inc, lib = mpi_flags()
    log = os.path.join(logdir, "%s_s4mpi.log" % tree)
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["TMPDIR"] = os.path.join(EV, "tmp")
    env_extra = ""
    if tree == "U":
        env["CFLAGS"] = "-Wno-error=int-conversion"
        env_extra = "CFLAGS=-Wno-error=int-conversion"
    cmd = ["make", "build/S4mpi", "CC=mpicc", "CXX=mpicxx", "MPI_INC=" + inc, "MPI_LIB=" + lib]
    with open(log, "w", encoding="utf-8") as fh:
        fh.write("# %s: %s (env_extra=%s)" % (tree, " ".join(cmd), env_extra) + NL)
        p = subprocess.run(cmd, cwd=tdir, env=env, stdout=fh, stderr=subprocess.STDOUT)
    rc = p.returncode
    exe = os.path.join(tdir, "build", "S4mpi")
    ok = rc == 0 and os.path.isfile(exe)
    status = "BUILD_OK" if ok else "BUILD_FAIL"
    banner = ""
    if ok:
        b = subprocess.run([exe, "-v"], capture_output=True, text=True)
        banner = (b.stdout + b.stderr)
        with open(os.path.join(MPI, "BANNER_%s.txt" % tree), "w", encoding="utf-8") as fh:
            fh.write(banner)
    with_mpi = "With MPI support" in banner
    rec = {"unit_id": "T3_%s_build_s4mpi" % tree, "suite": "T3_mpi", "tree": tree, "pass": "1",
           "status": status, "rc": rc, "signal": "NONE", "timed_out": "NO",
           "stdout_sha256": "", "stderr_sha256": "", "stdout_path": "", "stderr_path": "",
           "files": "", "dur_s": "", "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "extra": "log=%s log_sha256=%s exe_sha256=%s With_MPI_support=%s cmd=%s env_extra=%s" % (
               os.path.relpath(log, REPO), sha_f(log), sha_f(exe) if os.path.isfile(exe) else "missing",
               "yes" if with_mpi else "no", " ".join(cmd), env_extra)}
    write_unit(rec)
    rec2 = {"unit_id": "T3_%s_banner" % tree, "suite": "T3_mpi", "tree": tree, "pass": "1",
            "status": "WITH_MPI" if with_mpi else "NO_MPI", "rc": rc, "signal": "NONE", "timed_out": "NO",
            "stdout_sha256": "", "stderr_sha256": "", "stdout_path": "", "stderr_path": "", "files": "",
            "dur_s": "", "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "extra": "banner=" + banner.strip().replace(NL, " | ")[:200]}
    write_unit(rec2)
    print("MPI_BUILD %-2s rc=%d status=%s with_mpi=%s" % (tree, rc, status, with_mpi))
    return 0 if (ok and with_mpi) else 1


def run_unit(rel, tree, np_, pas):
    tdir = TREES[tree]
    exe = os.path.join(tdir, "build", "S4mpi")
    script = os.path.join(tdir, rel)
    unit_id = "T3_%s_%s_np%s_p%s" % (eid(rel), tree, np_, pas)
    done = os.path.join(UNITS, unit_id + ".tsv")
    cwd = os.path.join(MPI, "run", eid(rel), tree, "np" + np_, "p" + pas)
    if os.path.isfile(done):
        print("SKIP " + unit_id)
        return 0
    os.makedirs(cwd, exist_ok=True)
    outp = os.path.join(cwd, "out.stdout")
    errp = os.path.join(cwd, "out.stderr")
    t0 = time.time()
    timed_out = "NO"
    try:
        with open(outp, "wb") as fo, open(errp, "wb") as fe:
            p = subprocess.run(["mpirun", "-np", np_, exe, script], cwd=cwd, stdin=subprocess.DEVNULL,
                               stdout=fo, stderr=fe, timeout=TIMEOUT_S)
        rc = p.returncode
        signal = "NONE" if rc >= 0 else str(-rc)
    except subprocess.TimeoutExpired:
        rc, signal, timed_out = "TIMEOUT", "TIMEOUT", "YES"
    files = []
    for root, dirs, fs in os.walk(cwd):
        for f in sorted(fs):
            full = os.path.join(root, f)
            base = os.path.relpath(full, cwd)
            if base in ("out.stdout", "out.stderr"):
                continue
            files.append(base + ":" + sha_f(full))
    status = "TIMEOUT" if timed_out == "YES" else ("RAN_OK" if rc == 0 else "RAN_FAIL")
    rec = {"unit_id": unit_id, "suite": "T3_mpi", "tree": tree, "pass": pas, "status": status, "rc": rc,
           "signal": signal, "timed_out": timed_out, "stdout_sha256": sha_f(outp), "stderr_sha256": sha_f(errp),
           "stdout_path": os.path.relpath(outp, REPO), "stderr_path": os.path.relpath(errp, REPO),
           "files": ";".join(files) if files else "none", "dur_s": "%.3f" % (time.time() - t0),
           "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "extra": "mpirun -np %s build/S4mpi %s" % (np_, rel)}
    write_unit(rec)
    print("MPI_RUN %-60s rc=%s timeout=%s dur=%ss files=%d" % (unit_id, rc, timed_out, rec["dur_s"], len(files)))
    return 0 if status == "RAN_OK" and len(files) >= 1 else 1


def read_pairs(path):
    out = []
    if not os.path.isfile(path):
        return out
    for line in open(path, encoding="utf-8", errors="replace"):
        f = line.split()
        if len(f) >= 2:
            try:
                out.append((float(f[0]), float(f[1]), line.rstrip(NL)))
            except ValueError:
                continue
    return out


def relclose(a, b):
    return abs(a - b) <= 1e-12 * max(abs(a), abs(b), 1e-300)


def match_merge(merged, ref):
    """match merged [(f,v,line)] against ref by frequency; returns (max_rel_value_diff, matched, only_m, only_r)"""
    used = set()
    mx = 0.0
    matched = 0
    for f, v, _ in merged:
        best = None
        for j, (rf, rv, _) in enumerate(ref):
            if j in used:
                continue
            if relclose(f, rf):
                best = j
                break
        if best is None:
            continue
        used.add(best)
        rv = ref[best][1]
        matched += 1
        if max(abs(v), abs(rv)) > 0:
            mx = max(mx, abs(v - rv) / max(abs(v), abs(rv)))
        else:
            mx = max(mx, abs(v - rv))
    return "%.6e" % mx, matched, len(merged) - matched, len(ref) - matched


def merged_pairs(cwd, np_):
    rows = []
    for r in range(int(np_)):
        rows.extend(read_pairs(os.path.join(cwd, "out%d.txt" % r)))
    rows.sort(key=lambda x: x[0])
    return rows


def t1_nonmpi_path(tree, rel):
    # T1 non-MPI run cwd; the script itself writes out0.txt there
    return os.path.join(EV, "run", tree, "1", eid(rel), "out0.txt")


def fseq(start, end, step):
    """replicate a Lua numeric for loop's IEEE-754 double sequence (init, init+step, ... accumulated)"""
    out = []
    f = start
    while f <= end:
        out.append(f)
        f += step
    return out


def out_values(path):
    """the second column of an out<N>.txt file in line order (the script writes increasing frequencies)"""
    vals = []
    if not os.path.isfile(path):
        return vals
    for line in open(path, encoding="utf-8", errors="replace"):
        f = line.split()
        if len(f) >= 2:
            try:
                vals.append(float(f[1]))
            except ValueError:
                pass
    return vals


def compare():
    rows = ["# MPI_RELR4.tsv -- T3 MPI comparisons (task brief section 5.4.5)",
            "# a. merged out0..3 of -np 4 vs out0.txt of -np 1 and vs the T1 non-MPI out0.txt, compared on",
            "#    frequencies that are the SAME IEEE double (the Lua numeric for loops accumulate differently per",
            "#    rank, so most rank frequencies differ from the single-process grid in the last bits; frequency",
            "#    coverage is recorded, not judged - see ERRATA ER4-2).",
            "# b. B vs F4 same-named output files must be byte-identical.  c. U vs F4 categorised per section 4.",
            "# d. README's ../1d/binary_grating.txt is absent; recorded, not judged.",
            TAB.join(["unit_id", "comparison", "example", "tree_or_pair", "np", "pass", "result", "detail",
                      "matched", "only_merged", "only_reference", "max_rel_diff"])]
    bad = 0
    np1_seq = fseq(0.25, 0.7, 0.005)
    rank_seqs = []
    for _r in range(4):
        _st = 0.25 + _r / 4 * (0.7 - 0.25)
        _en = _st + (0.7 - 0.25) / 4
        rank_seqs.append(fseq(_st, _en, 0.005))
    all_rank_freqs = set()
    for _seq in rank_seqs:
        all_rank_freqs |= set(_seq)
    for rel in EXAMPLES:
        e = eid(rel)
        # ---- a. per tree, identical-double comparison
        for tree in ("U", "B", "F4"):
            cwd4 = os.path.join(MPI, "run", e, tree, "np4", "p1")
            cwd1 = os.path.join(MPI, "run", e, tree, "np1", "p1")
            rank_vals = [out_values(os.path.join(cwd4, "out%d.txt" % r)) for r in range(4)]
            np1_vals = out_values(os.path.join(cwd1, "out0.txt"))
            t1_vals = out_values(t1_nonmpi_path(tree, rel))
            merged_parsed = []
            for r in range(4):
                merged_parsed.extend(read_pairs(os.path.join(cwd4, "out%d.txt" % r)))
            merged_parsed.sort(key=lambda x: x[0])
            for label, ref_vals, ref_pairs in (
                    ("np4_merged_vs_np1", np1_vals, read_pairs(os.path.join(cwd1, "out0.txt"))),
                    ("np4_merged_vs_t1", t1_vals, read_pairs(t1_nonmpi_path(tree, rel)))):
                refmap = {}
                for i, f in enumerate(np1_seq):
                    if i < len(ref_vals):
                        refmap.setdefault(f, ref_vals[i])
                matched, only_rank, mx = 0, 0, 0.0
                for r in range(4):
                    for i, f in enumerate(rank_seqs[r]):
                        if i >= len(rank_vals[r]):
                            continue
                        if f in refmap:
                            matched += 1
                            rv = refmap[f]
                            mx = max(mx, abs(rank_vals[r][i] - rv) / max(abs(rank_vals[r][i]), abs(rv), 1e-300))
                        else:
                            only_rank += 1
                only_ref = len([f for f in np1_seq if f not in all_rank_freqs])
                nom_mx, nom_matched, _, _ = match_merge(merged_parsed, ref_pairs)
                ok = matched > 0 and mx <= 1e-12
                result = "PASS" if ok else "FAIL"
                if not ok:
                    bad += 1
                uid = "T3CMP_%s_%s_%s" % (e, tree, label)
                rows.append(TAB.join([uid, label, rel, tree, "4", "1", result,
                                      "identical-double matched=%d max_rel=%.3e; coverage only_rank=%d only_ref=%d; "
                                      "observation: nominal printed-frequency matching matched=%d max_rel=%.3e"
                                      % (matched, mx, only_rank, only_ref, nom_matched, float(nom_mx)),
                                      str(matched), str(only_rank), str(only_ref), "%.6e" % mx]))
                print("MPI_CMP %-52s %s matched=%d max_rel=%.3e only_rank=%d only_ref=%d nominal=%d/%.3e"
                      % (uid, result, matched, mx, only_rank, only_ref, nom_matched, float(nom_mx)))
        # ---- b. B vs F4 byte identical (pass 1)
        for np_ in ("1", "4"):
            files = ["out0.txt"] if np_ == "1" else ["out%d.txt" % i for i in range(4)]
            diffs = []
            for fn in files:
                pb = os.path.join(MPI, "run", e, "B", "np" + np_, "p1", fn)
                pf = os.path.join(MPI, "run", e, "F4", "np" + np_, "p1", fn)
                if not (os.path.isfile(pb) and os.path.isfile(pf)):
                    diffs.append(fn + ":missing")
                elif sha_f(pb) != sha_f(pf):
                    diffs.append(fn + ":differs")
            ok = not diffs
            if not ok:
                bad += 1
            rows.append(TAB.join(["T3CMP_%s_B_vs_F4_np%s" % (e, np_), "byte_identical", rel, "B_vs_F4", np_, "1",
                                  "SAME" if ok else "DIFF", ";".join(diffs) or "all same-named files identical",
                                  str(len(files)), "", "", ""]))
            print("MPI_CMP %-52s %s" % ("T3CMP_%s_B_vs_F4_np%s" % (e, np_), "SAME" if ok else "DIFF"))
        # ---- c. U vs F4, pass 1, np1 and np4 (merged): numeric comparison at identical frequencies
        for np_ in ("1", "4"):
            pu = os.path.join(MPI, "run", e, "U", "np" + np_, "p1")
            pf = os.path.join(MPI, "run", e, "F4", "np" + np_, "p1")
            nranks = int(np_)
            seq = [np1_seq] if np_ == "1" else rank_seqs
            uvals = []
            fvals = []
            for r in range(nranks):
                uvals.append(out_values(os.path.join(pu, "out%d.txt" % r)))
                fvals.append(out_values(os.path.join(pf, "out%d.txt" % r)))
            matched, only_u, mx = 0, 0, 0.0
            same_bytes = 0
            for r in range(nranks):
                pb = os.path.join(pu, "out%d.txt" % r)
                pfb = os.path.join(pf, "out%d.txt" % r)
                if os.path.isfile(pb) and os.path.isfile(pfb) and sha_f(pb) == sha_f(pfb):
                    same_bytes += 1
                for i, f in enumerate(seq[r] if nranks > 1 else np1_seq):
                    if i >= len(uvals[r]) or i >= len(fvals[r]):
                        continue
                    # for np4 rank r the r-th sequence is the rank's own frequency grid; identical doubles are
                    # compared only when both files list the same position (same grid by construction per rank)
                    if nranks > 1:
                        a, b = uvals[r][i], fvals[r][i]
                        matched += 1
                        mx = max(mx, abs(a - b) / max(abs(a), abs(b), 1e-300))
            if nranks == 1:
                matched = min(len(uvals[0]), len(fvals[0]))
                for i in range(matched):
                    a, b = uvals[0][i], fvals[0][i]
                    mx = max(mx, abs(a - b) / max(abs(a), abs(b), 1e-300))
            if np_ == "1" and same_bytes == nranks:
                cat, detail = "SAME", "all -np 1 output files byte-identical"
            elif same_bytes == nranks:
                cat, detail = "SAME", "all -np %s output files byte-identical" % np_
            elif matched and mx <= 1e-12:
                cat, detail = "DIFF_WITHIN_TOL", "rows=%d max_rel=%.3e" % (matched, mx)
            else:
                cat, detail = "DIFF_ATTRIBUTED", "rows=%d max_rel=%.3e" % (matched, mx)
            rows.append(TAB.join(["T3CMP_%s_U_vs_F4_np%s" % (e, np_), "u_vs_f4", rel, "U_vs_F4", np_, "1",
                                  cat, detail, str(matched), "", "", "%.6e" % mx]))
            print("MPI_CMP %-52s %s rows=%d max_rel=%.3e" % ("T3CMP_%s_U_vs_F4_np%s" % (e, np_), cat, matched, mx))
    # ---- d. the missing 1d reference
    missing = []
    for tree in ("U", "B", "F4"):
        p = os.path.join(TREES[tree], "examples", "1d", "binary_grating.txt")
        missing.append("%s=%s" % (tree, "present" if os.path.isfile(p) else "absent"))
    rows.append(TAB.join(["T3_RECORD_MISSING_1D_REFERENCE", "record_only", "examples/MPI_example README",
                          "ALL", "", "", "RECORD_ONLY", "examples/1d/binary_grating.txt: " + "; ".join(missing),
                          "", "", "", ""]))
    out = os.path.join(EV, "MPI_RELR4.tsv")
    if not os.path.realpath(out).startswith(os.path.join(REPO, "checkpoints/p05") + os.sep):
        raise SystemExit("WRITE_OUTSIDE " + out)
    open(out, "w", encoding="utf-8").write(NL.join(rows) + NL)
    print("WROTE " + os.path.relpath(out, REPO))
    return 0 if bad == 0 else 1


def main():
    a = sys.argv[1:]
    if not a:
        print("usage: relr4_mpi.py precheck|build --tree T|run --example E --tree T --np N --pass P|compare")
        return 2
    if a[0] == "precheck":
        return precheck()
    if a[0] == "build":
        return build(a[a.index("--tree") + 1])
    if a[0] == "run":
        return run_unit(a[a.index("--example") + 1], a[a.index("--tree") + 1],
                        a[a.index("--np") + 1], a[a.index("--pass") + 1])
    if a[0] == "compare":
        return compare()
    print("unknown mode " + a[0])
    return 2


if __name__ == "__main__":
    sys.exit(main())