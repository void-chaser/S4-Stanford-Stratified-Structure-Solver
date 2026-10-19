#!/usr/bin/env python3
# relr1_build.py -- build the Lua frontend (build/S4) and the Python extension (make S4_pyext) inside
# each exported tree with the project's own Makefiles, record rc and artifact hashes in BUILD_RELR1.tsv,
# and write WARN_DIFF_RELR1.txt with the compiler warnings that are new in F4 relative to B.
# Same compiler and flags for every tree (Makefile.Linux is the only platform selection).
# U is attempted but a failure is recorded as U_BUILD_UNAVAILABLE (task brief section 3.2) and does not block.
import os, sys, subprocess, hashlib, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r1")
TREES = os.path.join(EV, "trees")
LOGS = os.path.join(EV, "build_logs")
TAB = chr(9)
NL = chr(10)
TREE_NAMES = ("B", "F4", "U")
STEPS = (("lua_frontend", ["make", "-j16", "build/S4"]),
         ("pyext", ["make", "S4_pyext", "PYTHON=python3"]))


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def glob_sha(tree, pattern_dir, prefix):
    d = os.path.join(tree, pattern_dir)
    if not os.path.isdir(d):
        return []
    out = []
    for n in sorted(os.listdir(d)):
        if n.startswith(prefix) and n.endswith(".so"):
            out.append((os.path.join(pattern_dir, n), sha_f(os.path.join(d, n))))
    return out


def main():
    os.makedirs(LOGS, exist_ok=True)
    rows = ["# BUILD_RELR1.tsv -- P05 delivery round REL-R1 builds (same compiler and flags for all trees)",
            "# Each step command ran with cwd = the exported tree, via safe_run.sh p05-rel-r1; full log sha256 recorded.",
            TAB.join(["tree", "step", "cwd", "command", "rc", "status", "log", "log_sha256",
                      "artifact", "artifact_sha256", "note"])]
    bad = 0
    for name in TREE_NAMES:
        tree = os.path.join(TREES, name)
        if not os.path.isdir(tree):
            print("HARD_STOP missing tree " + tree)
            return 2
        for step, cmd in STEPS:
            log = os.path.join(LOGS, "%s_%s.log" % (name, step))
            env = dict(os.environ)
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            with open(log, "w", encoding="utf-8") as fh:
                fh.write("# %s %s: %s (cwd=%s, utc=%s)" % (name, step, " ".join(cmd), os.path.relpath(tree, REPO),
                         datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")) + NL)
                p = subprocess.run(cmd, cwd=tree, env=env, stdout=fh, stderr=subprocess.STDOUT)
            rc = p.returncode
            if name == "U" and rc != 0:
                status = "U_BUILD_UNAVAILABLE"
            else:
                status = "OK" if rc == 0 else "FAIL"
            if status == "FAIL":
                bad += 1
            arts = []
            if step == "lua_frontend":
                ap = os.path.join(tree, "build", "S4")
                if os.path.isfile(ap):
                    arts.append(("build/S4", sha_f(ap)))
            else:
                ap = os.path.join(tree, "build", "libS4.a")
                if os.path.isfile(ap):
                    arts.append(("build/libS4.a", sha_f(ap)))
                arts.extend(glob_sha(tree, ".", "S4."))
            if not arts:
                arts = [("none", "none")]
            for apath, asha in arts:
                rows.append(TAB.join([name, step, os.path.relpath(tree, REPO), " ".join(cmd), str(rc), status,
                                      os.path.relpath(log, REPO), sha_f(log), apath, asha,
                                      "U failure recorded as U_BUILD_UNAVAILABLE" if status == "U_BUILD_UNAVAILABLE" else ""]))
            print("BUILD %-2s %-14s rc=%d status=%s artifacts=%s" % (name, step, rc, status, ",".join("=".join(a) for a in arts)))
    # --- compiler warnings per tree, from the two B/F4 step logs
    def warnings(name):
        w = set()
        err = 0
        for step, _ in STEPS:
            p = os.path.join(LOGS, "%s_%s.log" % (name, step))
            if not os.path.isfile(p):
                continue
            for line in open(p, encoding="utf-8", errors="replace"):
                s = line.strip()
                if ": warning:" in s:
                    # keep source basename + message, drop line/column so shifts are not "new warnings"
                    head, _, msg = s.partition(": warning:")
                    src = head.split(":")[0].split("/")[-1]
                    w.add(src + ": warning:" + msg.strip())
                if ": error:" in s or s.startswith("make: ***"):
                    err += 1
        return w, err
    wb, eb = warnings("B")
    wf, ef = warnings("F4")
    new = sorted(wf - wb)
    gone = sorted(wb - wf)
    lines = ["# WARN_DIFF_RELR1.txt -- compiler warnings in the B and F4 build logs (task brief section 3.3)",
             "# Warning identity drops line/column numbers (source basename + message) so shifted lines are not counted as new.",
             "# B and F4 were built by the same compiler with the same Makefile.Linux flags.",
             "B_warnings=%d" % len(wb),
             "F4_warnings=%d" % len(wf),
             "NEW_IN_F4=%d" % len(new),
             "ONLY_IN_B=%d" % len(gone),
             "B_compile_error_lines=%d" % eb,
             "F4_compile_error_lines=%d" % ef]
    for x in new:
        lines.append("NEW" + TAB + x)
    for x in gone:
        lines.append("GONE" + TAB + x)
    outw = os.path.join(EV, "WARN_DIFF_RELR1.txt")
    open(outw, "w", encoding="utf-8").write(NL.join(lines) + NL)
    outb = os.path.join(EV, "BUILD_RELR1.tsv")
    open(outb, "w", encoding="utf-8").write(NL.join(rows) + NL)
    print("WARNINGS B=%d F4=%d new_in_F4=%d only_in_B=%d errors B=%d F4=%d" % (len(wb), len(wf), len(new), len(gone), eb, ef))
    print("WROTE " + os.path.relpath(outb, REPO) + " and " + os.path.relpath(outw, REPO))
    if ef != 0:
        print("HARD_STOP F4 build log contains compile error lines")
        bad += 1
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
