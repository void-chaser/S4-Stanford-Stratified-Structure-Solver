# r6c_state_gdb_r8m2a3.py -- P05-S4 R8 M2a3 gdb-internal python. Read-only: reads memory, never assigns.
# Loaded by r6c_state_r8m2a3.gdb. At each r6_probe(k) stop it prints machine-readable lines:
#   R6BSTATE <k> layer <i> modes_null <0|1> q_len <n> q_sha256 <hex|NA>
#   R6BSTATE <k> solution <null|ptr> solved <i>=<v> ...
#   R6BSTATE <k> cache node <j> layer <i> n <n> plen <p> P_sha256 <hex> layer_ptr <hex>
#   R6BSTATE <k> cache_count <c> cache_layers <list>
#   R6BSTATE <k> req_layer <i> solved <v>
# and at ComputeLayerModes entry/return (FinishBreakpoint) the R6BCLM lines.
#
# Byte counts (read from source):
#   q length   : LayerModes.q has length 2*glist.n (S4.cpp:187 comment). glist.n == S->n_G,
#                16 * 2*n_G (std::complex<double>), read as q[0..2*n_G) with n_G = S->n_G.
#   solved     : int array of length n_layers (S4.cpp:1756 allocation with sizeof(int)*S->n_layers).
#   cache P    : FieldCache.P (S4.cpp:203-208); length Plen per AddFieldToCache call site:
#                Jones : 4*nn+2*n  (fmm_PolBasisJones.cpp:340; nn = n*n at :104, n = S->n_G)
#                VL    : 4*nn      (fmm_PolBasisVL.cpp:237; nn at :54)
#                NV    : 4*nn      (fmm_PolBasisNV.cpp:230; nn at :55)
#                FieldCache has no Plen field, so the node's Plen is taken from the call site for its mode.
import hashlib
import gdb

try:
    import re
except ImportError:
    re = None


def _sha(buf):
    return hashlib.sha256(buf).hexdigest()


def _read_complex_bytes(ptr, count):
    """Read `count` std::complex<double> (16 bytes each) from a gdb pointer value. Returns bytes."""
    inf = gdb.selected_inferior()
    nbytes = 16 * int(count)
    if nbytes == 0:
        return b""
    addr = int(ptr)
    return bytes(inf.read_memory(addr, nbytes))


def _read_ints(ptr, count):
    inf = gdb.selected_inferior()
    addr = int(ptr)
    out = []
    for i in range(count):
        raw = bytes(inf.read_memory(addr + 4*i, 4))
        out.append(int.from_bytes(raw, "little", signed=True))
    return out


def _env(name):
    import os
    return os.environ.get(name, "")


def _mode():
    return _env("FMM_MODE")


def _plen_for_mode(mode, n_G):
    nn = n_G * n_G
    if mode in ("jones", "fftjones"):
        return 4*nn + 2*n_G
    if mode in ("vl", "fftvl", "nv", "fftnv"):
        return 4*nn
    return None


def _state_at(k):
    """Print the private state at current stop (r6_probe(k))."""
    f = gdb.selected_frame()
    while f is not None and f.name() != "main":
        f = f.older()
    if f is None:
        raise gdb.GdbError("main frame not found")
    f.select()
    S = f.read_var("S")
    n_layers = int(S["n_layers"])
    n_G = int(S["n_G"])
    print("R6BSTATE %d n_layers %d n_G %d" % (k, n_layers, n_G))
    # layers: modes and q
    for i in range(n_layers):
        L = S["layer"][i]
        modes = L["modes"]
        if int(modes) == 0:
            print("R6BSTATE %d layer %d modes_null 1 q_len NA q_sha256 NA" % (k, i))
        else:
            qlen = 2 * n_G
            qptr = modes.dereference()["q"]
            if int(qptr) == 0:
                print("R6BSTATE %d layer %d modes_null 0 q_len %d q_sha256 NULLQ" % (k, i, qlen))
            else:
                buf = _read_complex_bytes(qptr, qlen)
                print("R6BSTATE %d layer %d modes_null 0 q_len %d q_sha256 %s" % (k, i, qlen, _sha(buf)))
    # solution
    sol = S["solution"]
    if int(sol) == 0:
        print("R6BSTATE %d solution null" % k)
    else:
        solved_ptr = sol.dereference()["solved"]
        if int(solved_ptr) == 0:
            print("R6BSTATE %d solution solved_null" % k)
        else:
            vals = _read_ints(solved_ptr, n_layers)
            print("R6BSTATE %d solution solved %s" % (k, " ".join("%d=%d" % (i, v) for i, v in enumerate(vals))))
    # field cache list
    mode = _mode()
    plen_mode = _plen_for_mode(mode, n_G)
    node = S["field_cache"]
    nodes = []
    j = 0
    while int(node) != 0 and j < 64:
        nd = node.dereference()
        layer_ptr = nd["layer"]
        li = -1
        for i in range(n_layers):
            if int(layer_ptr) == int(S["layer"][i].address):
                li = i
                break
        n = int(nd["n"])
        if plen_mode is None:
            print("R6BSTATE %d cache node %d layer %d n %d plen NA P_sha256 NA(mode %s has no PolBasis cache)" % (k, j, li, n, mode))
        else:
            Pptr = nd["P"]
            buf = _read_complex_bytes(Pptr, plen_mode)
            print("R6BSTATE %d cache node %d layer %d n %d plen %d P_sha256 %s" % (k, j, li, n, plen_mode, _sha(buf)))
        nodes.append(li)
        node = nd["next"]
        j += 1
    print("R6BSTATE %d cache_count %d cache_layers %s" % (k, j, ",".join(str(x) for x in nodes) if nodes else "none"))


class R6BProbe(gdb.Breakpoint):
    """Stop at r6_probe(k); print snapshot; continue."""

    def stop(self):
        frame = gdb.selected_frame()
        k = int(frame.read_var("k"))
        orig = frame
        _state_at(k)
        orig.select()
        return False


class R6BClmReturn(gdb.FinishBreakpoint):
    def __init__(self, frame, idx, name):
        super(R6BClmReturn, self).__init__(frame, internal=True)
        self.idx = idx
        self.name = name

    def stop(self):
        rv = int(self.return_value) if self.return_value is not None else None
        print("R6BCLM RETURN idx %d name %s rc %s" % (self.idx, self.name, rv))
        return False

    def out_of_scope(self):
        print("R6BCLM RETURN idx %d name %s rc NA (out of scope)" % (self.idx, self.name))


class R6BClmTrace(gdb.Breakpoint):
    """Breakpoint at Simulation_ComputeLayerModes entry."""

    def stop(self):
        frame = gdb.selected_frame()
        Lp = frame.read_var("L")
        S = frame.read_var("S")
        Lv = Lp.dereference()
        nm = Lv["name"]
        name = nm.string() if int(nm) != 0 else "?"
        idx = (int(Lp) - int(S["layer"][0].address)) // int(Lv.type.sizeof)
        print("R6BCLM ENTER idx %d name %s" % (idx, name))
        R6BClmReturn(frame, idx, name)
        return False


class R6CReqTrace(gdb.Breakpoint):
    """Breakpoint at Simulation_GetLayerSolution entry."""
    count = 0

    def stop(self):
        frame = gdb.selected_frame()
        S = frame.read_var("S")
        Lp = frame.read_var("layer")
        R6CReqTrace.count += 1
        base = int(S["layer"][0].address)
        size = int(Lp.dereference().type.sizeof)
        idx = (int(Lp) - base) // size
        print("R6CREQ %d %d" % (R6CReqTrace.count, idx))
        return False


def install():
    R6BProbe("r6_probe", internal=False)
    R6BClmTrace("Simulation_ComputeLayerModes", internal=False)
    R6CReqTrace("Simulation_GetLayerSolution", internal=False)


install()
