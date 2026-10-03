#!/usr/bin/env python3
"""Validate the test-suite scaffolding itself before it is used for real.

Runs every isolation probe and prints the classification, so we can confirm the
harness correctly distinguishes ok / exception / native crash.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import isolation_cases
from s4test_common import run_isolated

names = sorted(isolation_cases.CASES)
print("probes registered: %d" % len(names))
print()
width = max(len(n) for n in names)
counts = {"ok": 0, "exception": 0, "crash": 0, "timeout": 0, "startup": 0}
for name in names:
    res = run_isolated(name)
    counts[res["verdict"]] = counts.get(res["verdict"], 0) + 1
    detail = res["result"]
    if res["verdict"] == "exception":
        detail = "%s: %s" % (res["exception_type"], res["exception_message"])
    elif res["verdict"] == "crash":
        detail = "rc=%s %s" % (res["returncode"], res["stderr_tail"].splitlines()[-1:] or "")
    print("  %-*s %-9s %s" % (width, name, res["verdict"], detail))

print()
print("verdict counts:", counts)
