#!/usr/bin/env python3
"""Offline reconciliation of the frozen regression cost table against the phase records,
and of the non-zero call exits against the registered expectations.  Stdlib only.
Usage: python3 -I reconcile_regression.py <RUN> <out.json>
"""
import glob
import json
import os
import re
import sys

RUN, OUT = sys.argv[1], sys.argv[2]
EV = os.path.join(RUN, "evidence")
LOGS = os.path.join(RUN, "logs")


def jload(p):
    with open(p) as f:
        return json.load(f)


cost_ids = [it["id"] for it in jload(os.path.join(EV, "REGRESSION_COST_TABLE.json"))["items"]]
executed, passed, observed, positive, phase_of = set(), set(), set(), set(), {}
phase_pass_map = {}
for p in sorted(glob.glob(os.path.join(EV, "PHASE_*.json"))):
    d = jload(p)
    ph = d.get("phase", os.path.basename(p))
    phase_pass_map[ph] = {"executed": len(d["executed"]), "verdict": d.get("verdict")}
    for x in d["executed"]:
        phase_of.setdefault(x, []).append(ph)
    executed.update(d["executed"])
    passed.update(d["scientific_pass"])
    observed.update(d["contract_probe_recorded"])
    positive.update(d["registered_expected_failure"])

cost_set = set(cost_ids)
rec = {
    "cost_items": len(cost_ids), "cost_unique": len(cost_set),
    "executed_items": len(executed),
    "missing_from_execution": sorted(cost_set - executed),
    "extra_in_execution": sorted(executed - cost_set),
    "scientific_pass": len(passed), "contract_probe_recorded": sorted(observed),
    "registered_expected_failure": sorted(positive),
    "pass_and_observed_overlap": sorted(passed & observed),
    "pass_and_expected_failure_overlap": sorted(passed & positive),
    "observed_and_expected_failure_overlap": sorted(observed & positive),
    "unclassified": sorted(cost_set - passed - observed - positive),
    "identity_137_eq_132_2_3": (len(passed) + len(observed) + len(positive) == len(cost_set) == 137),
    "phase_verdicts": phase_pass_map,
}

# Registered positive controls: stderr must carry the registered signature and the verifier verdict.
controls = []
for item in sorted(positive):
    suffix = item.removeprefix("B-POS-")
    v = jload(os.path.join(EV, "pos_" + suffix + ".verify.json"))
    stderr_txt = open(os.path.join(LOGS, item + ".stderr"), errors="replace").read()
    controls.append({"id": item, "exit": open(os.path.join(LOGS, item + ".exit")).read().strip(),
                     "signature": v.get("signature"), "verdict": v.get("verdict"),
                     "signature_in_stderr": bool(v.get("signature")) and v["signature"] in stderr_txt})
rec["positive_controls"] = controls

# Walk the registered command table: map each call id to its registered expectation.
reg = jload(os.path.join(RUN, "REGRESSION_COMMANDS.json"))
calls = []


def walk(x):
    if isinstance(x, dict):
        if "id" in x and "argv" in x:
            calls.append(x)
        for v in x.values():
            walk(v)
    elif isinstance(x, list):
        for v in x:
            walk(v)


walk(reg["phases"])
expect_of = {c["id"]: c.get("expect") for c in calls}
exits = {}
for p in glob.glob(os.path.join(LOGS, "*.exit")):
    name = os.path.basename(p)[:-5]
    exits[name] = open(p).read().strip()


def call_id_of(name):
    # log names replace ':' with '_' (e.g. D1_partial-analysis -> D1:partial-analysis)
    cand = [name, re.sub(r"^(D\d+)_", r"\1:", name)]
    for c in cand:
        if c in expect_of:
            return c
    return None


nonzero = {k: v for k, v in exits.items() if v != "0"}
nz_rows = []
for name in sorted(nonzero):
    cid = call_id_of(name)
    exp = expect_of.get(cid) if cid else None
    nz_rows.append({"log": name, "call_id": cid, "exit": nonzero[name], "registered_expect": exp,
                    "matches_registration": (exp is not None and exp.get("exit") == int(nonzero[name]))
                    if isinstance(exp, dict) and "exit" in exp else None})
rec["exit_files"] = len(exits)
rec["nonzero_exits"] = len(nonzero)
rec["nonzero_rows"] = nz_rows

# Partial-analysis aggregate: explain the exit-1 of each Dk partial from its own stdout.
partial = {}
for k in range(1, 12):
    p = os.path.join(LOGS, "D%d_partial-analysis.stdout" % k)
    if not os.path.exists(p):
        continue
    txt = open(p).read()
    own = re.search(r"^D%d\s+PASS ok$" % k, txt, re.M) is not None
    summary = re.search(r"^PASS (\d+)/11$", txt, re.M)
    fails = re.findall(r"^(D\d+)\s+FAIL EXIT: exit file missing", txt, re.M)
    partial["D%d" % k] = {"own_wave_ok": own, "aggregate": summary.group(0) if summary else None,
                          "waves_missing_exit_file": fails,
                          "exit": open(os.path.join(LOGS, "D%d_partial-analysis.exit" % k)).read().strip()}
p11 = os.path.join(LOGS, "D11_partial-analysis.stdout")
if os.path.exists(p11):
    partial["D11"] = {"aggregate": re.search(r"^PASS \d+/11$", open(p11).read(), re.M).group(0),
                      "exit": open(os.path.join(LOGS, "D11_partial-analysis.exit")).read().strip()}
rec["partial_analysis"] = partial

with open(OUT, "w") as f:
    json.dump(rec, f, indent=1, sort_keys=True, default=str)
print(json.dumps({k: v for k, v in rec.items() if k not in ("nonzero_rows", "phase_verdicts", "partial_analysis")},
                 indent=1, sort_keys=True, default=str))
print("nonzero rows:")
for r in nz_rows:
    print("  ", r["log"], r["exit"], "expect=", r["registered_expect"], "match=", r["matches_registration"])
print("partial:")
for k, v in partial.items():
    print("  ", k, v)
