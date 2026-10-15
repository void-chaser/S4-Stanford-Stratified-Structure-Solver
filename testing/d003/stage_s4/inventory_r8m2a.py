#!/usr/bin/env python3
# inventory_r8m2a.py -- P05-S4 R8 M2a section 4.2: apparatus inventory (read-only on sources).
# Writes $EV/APPARATUS_INVENTORY_R8_M2a.tsv with three kinds of rows:
#   GETENV   each getenv("NAME") in the scanned C/C++ sources: file:line, the variable, the source text [源码];
#   INJECT   each injection prefix recognised by an injector source (S4FMM_INJECT value pattern) [源码];
#   MODE     each FMM_MODE value compared in a driver source (strcmp literal) [源码];
#   SHA      each library/driver recorded in registries/s4r8/BUILD_R8.tsv, DRIVERS_R8.tsv,
#            DRIVERS_R8_F2_REUSED.tsv: recorded sha256 vs recomputed sha256 -> SAME / DIFFERENT / MISSING.
# Output is a plain TSV; no source file is modified.  Refuses to overwrite (U17).
import hashlib
import os
import re
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a")
OUT = os.path.join(EV, "APPARATUS_INVENTORY_R8_M2a.tsv")
SCAN_DIRS = [
    "testing/d003/src",
    "testing/d003/seam",
    "testing/d003/stage_s4",
    "testing/d003/stage_s4r7",
    "testing/d003/stage_s4r8",
]
SRC_EXT = (".cpp", ".c", ".h", ".hpp", ".cc")
S4R8 = "checkpoints/p05/registries/s4r8"
GETENV_RE = re.compile(r'getenv\("([A-Za-z0-9_]+)"\)')
MODE_RE = re.compile(r'strcmp\(\s*(?:mode|getenv\("FMM_MODE"\))\s*,\s*"([a-z0-9]+)"\s*\)')
INJECT_RE = re.compile(r'"(plan|exec|alloc|win|init|fmmret|linearsolve_null2buf|linearsolve_null2|linearsolve_null|linearsolve|s4malloc|scratch|plancall|kottke_alloc|polyinj|malloc)[:"]')


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def iter_sources():
    for d in SCAN_DIRS:
        base = os.path.join(REPO, d)
        if not os.path.isdir(base):
            continue
        for root, dirs, files in os.walk(base):
            dirs.sort()
            for f in sorted(files):
                if f.endswith(SRC_EXT):
                    yield os.path.join(root, f)


def read_tsv(path):
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]
    head = lines[0].split("\t")
    return [dict(zip(head, l.split("\t"))) for l in lines[1:]]


def main():
    if os.path.exists(OUT):
        print("inventory_r8m2a: REFUSED exists (U17): %s" % OUT)
        return 2
    rows = []
    rows.append(["kind", "file", "line", "item", "detail", "basis"])
    n_getenv = n_mode = n_inject = 0
    for path in iter_sources():
        rel = os.path.relpath(path, REPO)
        with open(path, encoding="utf-8", errors="replace") as fh:
            for i, text in enumerate(fh, 1):
                for m in GETENV_RE.finditer(text):
                    rows.append(["GETENV", rel, str(i), m.group(1), text.strip()[:160], "[源码]"])
                    n_getenv += 1
                for m in MODE_RE.finditer(text):
                    rows.append(["MODE", rel, str(i), m.group(1), text.strip()[:160], "[源码]"])
                    n_mode += 1
                if "S4FMM_INJECT" in text or "linearsolve" in text or "polyinj" in text:
                    for m in INJECT_RE.finditer(text):
                        rows.append(["INJECT", rel, str(i), m.group(1), text.strip()[:160], "[源码]"])
                        n_inject += 1

    # SHA check of the R8 builds and drivers.  Recorded hash vs recomputed hash of the file on disk.
    sha_rows = 0
    sha_diff = 0
    for name, recs in (("BUILD_R8.tsv", None), ("DRIVERS_R8.tsv", "drivers"), ("DRIVERS_R8_F2_REUSED.tsv", "reused")):
        if recs is None:
            continue
        tsv = read_tsv(os.path.join(REPO, S4R8, name))
        for r in tsv:
            if recs == "drivers":
                rec = r["driver_sha256"]
                path = r["driver_path"]
                ident = r["driver"]
            else:
                rec = r["recorded_driver_sha256"]
                path = r["path"]
                ident = r["driver"]
            if os.path.isfile(path):
                now = sha256_file(path)
                status = "SAME" if now == rec else "DIFFERENT"
            else:
                now = "-"
                status = "MISSING"
            if status != "SAME":
                sha_diff += 1
            sha_rows += 1
            rows.append(["SHA", S4R8 + "/" + name, "-", ident, "recorded=%s;now=%s;status=%s" % (rec, now, status), "[registry]"])
    rows.append(["SUMMARY", "-", "-", "counts", "getenv=%d;mode=%d;inject=%d;sha_rows=%d;sha_not_same=%d" % (
        n_getenv, n_mode, n_inject, sha_rows, sha_diff), "-"])

    os.makedirs(EV, exist_ok=True)
    with open(OUT, "x", encoding="utf-8") as fh:
        for row in rows:
            fh.write("\t".join(row) + "\n")
    print("INVENTORY getenv=%d mode=%d inject=%d sha_rows=%d sha_not_same=%d out=%s" % (
        n_getenv, n_mode, n_inject, sha_rows, sha_diff, OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
