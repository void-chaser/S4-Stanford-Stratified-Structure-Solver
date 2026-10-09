#!/usr/bin/env python3
"""Read-only three-way comparison for the production adoption plan.

For every change in package/engineering/LANDING_MANIFEST.json (102 entries, base 963ccf1):
  prod  = production repo working file (must equal `before_sha256` if still at base)
  src   = package/source file            (should equal `after_sha256`)
  cand  = package/object-RUN/candidate   (the integrated run tree)
Writes nothing into the repo, the package or RUN.
Usage: python3 -I production_adoption_compare.py <REPO> <WORK> <out.json>
"""
import hashlib
import json
import os
import sys

REPO, WORK, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
PKG = os.path.join(WORK, "package")


def sha(p):
    if not os.path.isfile(p):
        return None
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


man = json.load(open(os.path.join(PKG, "engineering", "LANDING_MANIFEST.json")))
patch_sha = sha(os.path.join(PKG, "engineering", "PRODUCTION_ENGINEERING.patch"))
rows = []
for c in man["changes"]:
    rel = c["path"]
    prod = sha(os.path.join(REPO, rel))
    src = sha(os.path.join(PKG, "source", rel))
    cand = sha(os.path.join(PKG, "object-RUN", "candidate", rel))
    row = {"path": rel, "operation": c["operation"],
           "prod_at_base": prod == c["before_sha256"] if c["operation"] != "add" else prod is None,
           "prod_sha": prod, "src_is_after": src == c["after_sha256"],
           "cand_is_after": cand == c["after_sha256"], "cand_present": cand is not None,
           "src_sha": src, "cand_sha": cand, "after_sha": c["after_sha256"],
           "before_sha": c.get("before_sha256")}
    rows.append(row)

summary = {
    "patch_sha256": patch_sha,
    "patch_sha_expected": "1adef26caf8765eb9392091a26548cfce3318e4b9f82f6c1442cba07b621076e",
    "manifest_changes": len(rows),
    "base_commit": man["base_commit"],
    "prod_at_base": sum(1 for r in rows if r["prod_at_base"]),
    "src_is_after": sum(1 for r in rows if r["src_is_after"]),
    "cand_is_after": sum(1 for r in rows if r["cand_is_after"]),
    "prod_not_at_base": [r["path"] for r in rows if not r["prod_at_base"]],
    "src_not_after": [r["path"] for r in rows if not r["src_is_after"]],
    "cand_not_after": [r["path"] for r in rows if not r["cand_is_after"]],
    "rows": rows,
}
with open(OUT, "w") as f:
    json.dump(summary, f, indent=1, sort_keys=True)
print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=1))
