#!/usr/bin/env python3
# reverify_sums_r9m3c.py -- read-only re-verification of the M3b evidence/registry manifests and of the 8 make-test
# reconcile rows (column names read from the header comment). New file (r9m3c).
# usage: reverify_sums_r9m3c.py OUT.tsv
import os, sys, hashlib
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3c")
M3B_EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b")
M3B_REG = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M3b")
MKV = os.path.join(M3B_EV, "MAKETEST_VERDICT_R9M3B.tsv")
TAB = chr(9)
NL = chr(10)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            b = fh.read(65536)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def verify_dir(d):
    man = os.path.join(d, "SHA256SUMS.txt")
    rows = []
    if not os.path.isfile(man):
        return False, 0, "missing manifest", rows
    for line in open(man, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        exp, name = parts[0], parts[1].strip()
        fp = os.path.join(d, name)
        got = sha(fp) if os.path.isfile(fp) else "MISSING"
        ok = (got == exp)
        rows.append((name, exp, got, "OK" if ok else "FAIL"))
    allok = all(r[3] == "OK" for r in rows) and len(rows) > 0
    return allok, len(rows), ("all %d OK" % len(rows) if allok else "FAIL"), rows


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(EV, "REVERIFY_R9M3B_R9M3C.tsv")
    rows = []
    for label, d in (("m3b_evidence", M3B_EV), ("registries_M3b", M3B_REG)):
        ok, n, det, items = verify_dir(d)
        rows.append(("manifest", label, "items=%d" % n, "OK" if ok else "FAIL", det))
        for name, exp, got, res in items:
            rows.append(("manifest_item", label + "/" + name, exp[:16], res, got[:16]))
    # recompute the 8 reconcile rows from the header names
    hdr_names = None
    for line in open(MKV, encoding="utf-8"):
        if line.startswith("# reconciliation rows:"):
            hdr_names = [x.strip() for x in line.split(":", 1)[1].split("/")]
    rec = []
    for line in open(MKV, encoding="utf-8"):
        if line.startswith("reconcile" + TAB):
            rec.append(line.rstrip("\r\n").split(TAB))
    if hdr_names is None:
        rows.append(("reconcile", "header", "reconciliation header comment", "FAIL", "missing header names"))
    else:
        for f in rec:
            d = dict(zip(["item"] + hdr_names, f))
            try:
                ok = (d.get("units") == d.get("Ran_N") and d.get("skipped_got") == d.get("skipped_expected") and d.get("ok") == "OK")
            except Exception:
                ok = False
            rows.append(("reconcile", "%s/%s" % (d.get("log"), d.get("stage")),
                         "units=%s Ran_N=%s skipped=%s/%s" % (d.get("units"), d.get("Ran_N"), d.get("skipped_got"), d.get("skipped_expected")),
                         "OK" if ok else "FAIL", "ok_col=" + str(d.get("ok"))))
    fails = len([r for r in rows if r[3] == "FAIL"])
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# REVERIFY_R9M3B_R9M3C.tsv -- independent read-only re-verification of the M3b formal results" + NL)
        fh.write(TAB.join(["kind", "target", "recomputed", "result", "detail"]) + NL)
        for r in rows:
            fh.write(TAB.join(str(x) for x in r) + NL)
        fh.write("# FAILS=%d" % fails + NL)
    man_ok = all(r[3] == "OK" for r in rows if r[0] in ("manifest", "manifest_item"))
    rec_ok = all(r[3] == "OK" for r in rows if r[0] == "reconcile")
    print("manifests_all_ok=%s reconcile_all_ok=%s fails=%d" % (man_ok, rec_ok, fails))
    print("WROTE " + out)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
