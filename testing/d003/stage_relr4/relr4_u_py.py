#!/usr/bin/env python3
# relr4_u_py.py -- task brief section 3: the original U tree's Python interface is attempted exactly once,
# without changing any file by hand: 'sh gensetup.py.sh build build/libS4.a' then 'python3 setup.py build'.
# rc and errors are recorded verbatim and the attempt is classified U_PY_UNAVAILABLE or SUCCESS.
# Every output stays under $EV; only the U clone itself is written by the project's own generator.
import os, sys, subprocess, hashlib

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r4")
U = os.path.join(EV, "upstream", "S4")
LOG = os.path.join(EV, "u_probe")
TAB = chr(9)
NL = chr(10)


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    os.makedirs(LOG, exist_ok=True)
    env = dict(os.environ)
    env["TMPDIR"] = os.path.join(EV, "tmp")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    rows = ["# U_PY_RELR4.tsv -- the single attempt at the original U tree's Python interface (task brief section 3)",
            TAB.join(["step", "command", "cwd", "rc", "log", "log_sha256", "first_error", "classification"])]
    log1 = os.path.join(LOG, "u_py_gensetup.log")
    with open(log1, "w", encoding="utf-8") as fh:
        fh.write("# cwd=%s cmd=sh gensetup.py.sh build build/libS4.a" % os.path.relpath(U, REPO) + NL)
        p1 = subprocess.run(["sh", "gensetup.py.sh", "build", "build/libS4.a"], cwd=U, env=env, stdout=fh, stderr=subprocess.STDOUT)
    e1 = [l.strip() for l in open(log1, encoding="utf-8", errors="replace") if ": error:" in l or "Error" in l or "error" in l.lower()][:1]
    rows.append(TAB.join(["gensetup", "sh gensetup.py.sh build build/libS4.a", os.path.relpath(U, REPO), str(p1.returncode),
                          os.path.relpath(log1, REPO), sha_f(log1), e1[0][:220] if e1 else "none", ""]))
    log2 = os.path.join(LOG, "u_py_setup_build.log")
    with open(log2, "w", encoding="utf-8") as fh:
        fh.write("# cwd=%s cmd=python3 setup.py build" % os.path.relpath(U, REPO) + NL)
        p2 = subprocess.run(["python3", "setup.py", "build"], cwd=U, env=env, stdout=fh, stderr=subprocess.STDOUT)
    e2 = [l.strip() for l in open(log2, encoding="utf-8", errors="replace") if "error:" in l or "Error" in l or "error" in l.lower()][:1]
    ok = (p1.returncode == 0 and p2.returncode == 0)
    cls = "SUCCESS" if ok else "U_PY_UNAVAILABLE"
    rows.append(TAB.join(["setup_build", "python3 setup.py build", os.path.relpath(U, REPO), str(p2.returncode),
                          os.path.relpath(log2, REPO), sha_f(log2), e2[0][:220] if e2 else "none", cls]))
    # record what the generator touched inside the U clone (evidence only; the U clone is never committed)
    st = subprocess.run(["git", "-C", U, "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
    rows.append(TAB.join(["u_clone_status", "git status --porcelain (after the attempt)", os.path.relpath(U, REPO), "", "", "",
                          st.replace(NL, "; ")[:400] or "clean", ""]))
    out = os.path.join(EV, "U_PY_RELR4.tsv")
    open(out, "w", encoding="utf-8").write(NL.join(rows) + NL)
    print("U_PY gensetup_rc=%d setup_rc=%d classification=%s" % (p1.returncode, p2.returncode, cls))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
