#!/usr/bin/env python3
# relr4_expect_scan.py -- source-reading aid for the REL-R4 pre-registration (task brief section 4:
# "expectations must be formed from source reading").  Read-only scan of the three reference trees:
#   * every S4 Lua API method/global an example calls (comments stripped), checked against the functions
#     the U, B and F4 frontends actually register (S4/main_lua.c luaL_Reg tables + S4 globals);
#   * uses of Lua 5.1-only loadstring (nil in Lua 5.2) and of GetRealMaterial (registered by no tree);
#   * whether the U tree's own testing manifest references files that exist in the U clone.
# Writes EXPECT_SCAN_RELR4.tsv under $EV.  No expectation is written by this script.
import os, sys, re

REPO = "/srv/nvme/projects/S4-Stanford-Stratified-Structure-Solver"
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r4")
TREES = {"U": os.path.join(EV, "upstream", "S4"),
         "B": os.path.join(EV, "trees", "B"),
         "F4": os.path.join(EV, "trees", "F4")}
TAB = chr(9)
NL = chr(10)
GLOBALS = {"MPIRank", "MPISize"}


def registered(tree):
    txt = open(os.path.join(tree, "S4", "main_lua.c"), encoding="utf-8", errors="replace").read()
    return set(re.findall(r'\{"([A-Za-z_][A-Za-z0-9_]*)",', txt))


def lua_files(tree):
    out = []
    for root, dirs, files in os.walk(os.path.join(tree, "examples")):
        dirs.sort()
        for f in sorted(files):
            if f.endswith(".lua"):
                out.append(os.path.relpath(os.path.join(root, f), tree))
    return sorted(out)


def strip_comments(txt):
    # remove -- line comments; no example has a string literal containing '--'
    return re.sub(r"--[^\n]*", "", txt)


def main():
    reg = {name: registered(t) for name, t in TREES.items()}
    union_api = set().union(*reg.values()) | GLOBALS
    rows = ["# EXPECT_SCAN_RELR4.tsv -- source-reading scan used to form the REL-R4 expectations (no expectation here)",
            "# registered = functions the Lua frontend S4/main_lua.c registers; missing = called by the example but",
            "# not registered in that tree.  Comments are stripped before scanning.  loadstring is nil under Lua",
            "# 5.2; GetRealMaterial is registered by no tree.",
            TAB.join(["example", "in_U", "in_B", "in_F4", "calls_loadstring", "calls_GetRealMaterial",
                      "U_missing_api", "F4_missing_api", "B_missing_api", "U_expected_txt", "F4_expected_txt"])]
    f4files = lua_files(TREES["F4"])
    ufiles = set(lua_files(TREES["U"]))
    bfiles = set(lua_files(TREES["B"]))
    for rel in f4files:
        raw = open(os.path.join(TREES["F4"], rel), encoding="utf-8", errors="replace").read()
        txt = strip_comments(raw)
        methods = set(re.findall(r":[ \t]*([A-Za-z_][A-Za-z0-9_]*)[ \t]*\(", txt))
        s4glob = set(re.findall(r"S4\.([A-Za-z_][A-Za-z0-9_]*)", txt))
        called = (methods | s4glob) & union_api
        miss = {name: sorted(called - reg[name]) for name in ("U", "B", "F4")}
        has_load = "loadstring" in txt
        has_grm = "GetRealMaterial" in txt
        expected_txt = rel[:-4] + ".txt"
        rows.append(TAB.join([rel, "yes" if rel in ufiles else "no", "yes" if rel in bfiles else "no", "yes",
                              "yes" if has_load else "no", "yes" if has_grm else "no",
                              ",".join(miss["U"]) or "none", ",".join(miss["F4"]) or "none",
                              ",".join(miss["B"]) or "none",
                              "yes" if os.path.isfile(os.path.join(TREES["U"], expected_txt)) else "no",
                              "yes" if os.path.isfile(os.path.join(TREES["F4"], expected_txt)) else "no"]))
        if miss["U"]:
            print("U_MISSING " + rel + " " + ",".join(miss["U"]))
        if has_load:
            print("LOADSTRING " + rel)
        if has_grm:
            print("GETREALMATERIAL " + rel)
    man = os.path.join(TREES["U"], "testing", "testcases.txt")
    if os.path.isfile(man):
        n = missing_script = missing_base = 0
        for line in open(man, encoding="utf-8"):
            if not line.strip() or line.startswith("#"):
                continue
            f = line.split()
            n += 1
            if not os.path.isfile(os.path.join(TREES["U"], "examples", f[0])):
                missing_script += 1
            if not os.path.isfile(os.path.join(TREES["U"], "examples", f[1])):
                missing_base += 1
        rows.append(TAB.join(["U_TESTCASES", str(n), "missing_script=%d" % missing_script,
                              "missing_baseline=%d" % missing_base, "manifest=testing/testcases.txt"]))
        print("U_TESTCASES n=%d missing_script=%d missing_baseline=%d" % (n, missing_script, missing_base))
    out = os.path.join(EV, "EXPECT_SCAN_RELR4.tsv")
    open(out, "w", encoding="utf-8").write(NL.join(rows) + NL)
    print("WROTE " + os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
