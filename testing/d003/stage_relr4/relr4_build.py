#!/usr/bin/env python3
# relr4_build.py -- build the Lua frontend build/S4 inside each REL-R4 reference clone with the project's
# own Makefiles and the SAME compiler/flags for all trees (task brief section 3):
#   command: make -j16 build/S4       (identical for U, B, F4)
#   U only:  environment CFLAGS=-Wno-error=int-conversion  (U401 ruling; no source or Makefile is modified)
# Records rc, a sha256 of every build log, the artifact hashes, and the compiler-warning differences
# between the three trees in WARN_DIFF_RELR4.txt.  Writes only under $EV.
import os, sys, subprocess, hashlib, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r4")
LOGS = os.path.join(EV, "build_logs")
TAB = chr(9)
NL = chr(10)
TREES = {"U": os.path.join(EV, "upstream", "S4"),
         "B": os.path.join(EV, "trees", "B"),
         "F4": os.path.join(EV, "trees", "F4")}
ORDER = ("U", "B", "F4")
CMD = ["make", "-j16", "build/S4"]


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    os.makedirs(LOGS, exist_ok=True)
    rows = ["# BUILD_RELR4.tsv -- P05 delivery round REL-R4 Lua frontend builds",
            "# Every tree was built with its own Makefile and the same command, compiler, LAPACK and Lua 5.2.",
            "# U additionally got the environment variable CFLAGS=-Wno-error=int-conversion (ruling U401);",
            "# no source file and no Makefile was modified.",
            TAB.join(["tree", "step", "clone_dir", "command", "env_extra", "rc", "status", "log", "log_sha256",
                      "artifact", "artifact_sha256", "note"])]
    bad = 0
    for name in ORDER:
        tree = TREES[name]
        if not os.path.isdir(os.path.join(tree, "S4")):
            print("HARD_STOP missing tree " + tree)
            return 2
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["TMPDIR"] = os.path.join(EV, "tmp")
        env_extra = ""
        if name == "U":
            env["CFLAGS"] = "-Wno-error=int-conversion"
            env_extra = "CFLAGS=-Wno-error=int-conversion"
        log = os.path.join(LOGS, "%s_lua_frontend.log" % name)
        with open(log, "w", encoding="utf-8") as fh:
            fh.write("# %s: %s (cwd=%s, utc=%s, env_extra=%s)" % (
                name, " ".join(CMD), os.path.relpath(tree, REPO),
                datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), env_extra) + NL)
            p = subprocess.run(CMD, cwd=tree, env=env, stdout=fh, stderr=subprocess.STDOUT)
        rc = p.returncode
        status = "OK" if rc == 0 else "FAIL"
        if rc != 0:
            bad += 1
        exe = os.path.join(tree, "build", "S4")
        lib = os.path.join(tree, "build", "libS4.a")
        arts = []
        if os.path.isfile(exe):
            arts.append(("build/S4", sha_f(exe)))
        if os.path.isfile(lib):
            arts.append(("build/libS4.a", sha_f(lib)))
        if not arts:
            arts = [("none", "none")]
        for apath, asha in arts:
            rows.append(TAB.join([name, "lua_frontend", os.path.relpath(tree, REPO), " ".join(CMD), env_extra,
                                  str(rc), status, os.path.relpath(log, REPO), sha_f(log), apath, asha,
                                  "" if status == "OK" else "build failed; see log"]))
        print("BUILD %-2s rc=%d status=%s artifacts=%s" % (name, rc, status,
              ",".join(a.split("/")[-1] + "=" + s[:12] for a, s in arts)))
    # --- compiler warnings per tree; identity = source basename + message (line/column dropped so that
    #     shifted line numbers are not counted as new warnings)
    def warnings(name):
        w = set()
        errlines = []
        p = os.path.join(LOGS, "%s_lua_frontend.log" % name)
        if not os.path.isfile(p):
            return w, errlines
        for line in open(p, encoding="utf-8", errors="replace"):
            s = line.strip()
            if ": warning:" in s:
                head, _, msg = s.partition(": warning:")
                src = head.split(":")[0].split("/")[-1]
                w.add(src + ": warning:" + msg.strip())
            if ": error:" in s or s.startswith("make: ***"):
                errlines.append(s[:220])
        return w, errlines
    sets = {}
    errsets = {}
    for name in ORDER:
        sets[name], errsets[name] = warnings(name)
    lines = ["# WARN_DIFF_RELR4.txt -- compiler warnings in the U, B and F4 build logs (task brief section 3)",
             "# Identity drops line/column numbers (source basename + message) so shifted lines are not 'new'.",
             "# All trees used the same compiler and the same Makefile flags; U additionally got",
             "# CFLAGS=-Wno-error=int-conversion in the environment (ruling U401).",
             "# Warning lines and compile-error lines are counted from the full build logs.",
             "LOG_FILES" + TAB + "U=%s B=%s F4=%s" % (
                 os.path.relpath(os.path.join(LOGS, "U_lua_frontend.log"), REPO),
                 os.path.relpath(os.path.join(LOGS, "B_lua_frontend.log"), REPO),
                 os.path.relpath(os.path.join(LOGS, "F4_lua_frontend.log"), REPO))]
    for name in ORDER:
        lines.append("%s_warnings=%d" % (name, len(sets[name])))
        lines.append("%s_error_lines=%d" % (name, len(errsets[name])))
    for a, b in (("U", "B"), ("B", "F4"), ("U", "F4")):
        new = sorted(sets[b] - sets[a])
        gone = sorted(sets[a] - sets[b])
        lines.append("%s_to_%s_new=%d" % (a, b, len(new)))
        lines.append("%s_to_%s_gone=%d" % (a, b, len(gone)))
        for x in new:
            lines.append("NEW" + TAB + a + "->" + b + TAB + x)
        for x in gone:
            lines.append("GONE" + TAB + a + "->" + b + TAB + x)
    for name in ORDER:
        for x in sorted(sets[name]):
            lines.append("WARN" + TAB + name + TAB + x)
        for x in errsets[name]:
            lines.append("ERRORLINE" + TAB + name + TAB + x)
    outw = os.path.join(EV, "WARN_DIFF_RELR4.txt")
    open(outw, "w", encoding="utf-8").write(NL.join(lines) + NL)
    outb = os.path.join(EV, "BUILD_RELR4.tsv")
    if not os.path.realpath(outb).startswith(os.path.join(REPO, "checkpoints/p05") + os.sep):
        raise SystemExit("WRITE_OUTSIDE " + outb)
    open(outb, "w", encoding="utf-8").write(NL.join(rows) + NL)
    print("WARNINGS " + " ".join("%s=%d" % (n, len(sets[n])) for n in ORDER))
    print("WRITE " + os.path.relpath(outb, REPO) + " and " + os.path.relpath(outw, REPO))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
