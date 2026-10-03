"""zlahqr_ was entered with an empty range and wrote out of bounds.

Resolved: the guard is in S4/RNP/Eigensystems.cpp. The "workspace is
too small" explanation that this file originally carried was disproved
by measurement and is kept below only as a warning.

This is an AddressSanitizer-only defect, recorded here so the reproduction is
not lost. What is known, all measured:

  * ``WRITE of size 16`` reported at ``S4/RNP/Eigensystems.cpp:1054`` inside
    ``zlahqr_``, reached as
    ``rcwa.cpp:827 RNP::Eigensystem -> zhseqr_ -> zlaqr0_ -> zlaqr3_ -> zlahqr_``;
  * the address is **64 bytes before** the allocation, so the write underflows
    rather than overruns;
  * the allocation is the eigensolver work buffer,
    ``malloc_aligned <- S4_malloc <- Simulation_ComputeLayerModes``
    (``S4/S4.cpp:2339``);
  * it needs a **patterned** layer: a plain slab never enters the layer
    eigensolver and is clean;
  * it reproduces at ``NumBasis`` 1, 2, 3 and 4, and not at 9 or above;
  * it does **not** need ``Clone`` -- a single ``GetPowerFlux`` on a freshly
    built simulation is sufficient, which is why this is **not** a Clone defect;
  * it does not reproduce in a normal (non-sanitized) build: the write lands in
    reusable heap memory and the returned numbers are unchanged.

Root cause and fix
------------------
Instrumenting ``zlahqr_`` measured the entry state at the failing write::

    [ZLAQR] n=2 ilo=2 ihi=1 ldh=2 h_off=0 idx=-4 byte_off=-64  <== BEFORE BUFFER

``ilo > ihi``, an empty range, which the routine did not guard -- it tested only
``ilo == ihi``. The write is guarded by

    if( ilo <= ihi-2 ) h[(ihi-1)+(( ihi-2 )-1)*ldh] = zero;

and ``ihi-2`` is computed in ``size_t``, so with ``ihi < 2`` it wraps to
``SIZE_MAX``, the guard passes, and the index evaluates to -4.

An earlier hypothesis -- that the workspace query answer of ``2*n`` was simply
too small -- was **disproved**: raising it to ``n*(n+1)`` left the report
unchanged. It is recorded here because it is the intuitive explanation and it is
wrong.

The fix clamps the range on entry and returns for an empty one, detecting
emptiness *before* clamping upwards (raising ``ihi`` to ``n`` first would turn
``ilo=2, ihi=1`` into the legal-looking ``ilo == ihi == 2`` and let the routine
proceed into the underflowing code). After the fix the minimal case reports zero
AddressSanitizer errors at every basis from 1 to 49, and R+T stays 1.0.

How to reproduce the sanitizer run
----------------------------------
There is no ``make test-sanitize`` target. Sanitizer builds use a separate object
directory so the normal build is untouched::

    FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g -O1 -fPIC"
    make -j16 OBJDIR=build-asan CFLAGS="$FLAGS" CXXFLAGS="$FLAGS" build-asan/libS4.a
    # setup.py must point at build-asan/libS4.a for extra_objects
    rm -f S4.cpython-*.so && rm -rf build/temp.linux-x86_64-cpython-314
    CFLAGS="$FLAGS" LDFLAGS="-fsanitize=address,undefined" \
        python3 setup.py build_ext --inplace
    export LD_PRELOAD=$(gcc -print-file-name=libasan.so):$(gcc -print-file-name=libubsan.so)
    export ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:print_stacktrace=1
    export UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=0

Removing the existing ``S4.cpython-*.so`` and ``build/temp.*`` before
``build_ext`` is required, not optional: ``setup.py`` does not relink when
``libS4.a`` is newer, so without it the extension silently keeps the previous
build and a fixed source appears to still fail. That mistake was made twice
during this investigation.
"""

import unittest

import S4

from s4test_common import run_isolated

#: Bases where the sanitizer report reproduces. 9 and above are clean.
OVERFLOWING_BASES = (1, 2, 3, 4)
CLEAN_BASES = (9, 16, 25)


def build(num_basis, patterned=True):
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=num_basis)
    sim.AddMaterial("Air", 1)
    sim.AddMaterial("Si", 12)
    sim.AddLayer("Top", 0, "Air")
    sim.AddLayer("Slab", 0.5, "Si")
    if patterned:
        sim.SetRegionCircle("Slab", "Air", (0.0, 0.0), 0.2)
    sim.AddLayerCopy("Bot", 0, "Top")
    sim.SetFrequency(0.5)
    sim.SetExcitationPlanewave((0, 0), 1, 0)
    return sim


def rt(num_basis, patterned=True):
    sim = build(num_basis, patterned)
    inc, refl = sim.GetPowerFlux("Top", 0.0)
    trans, _ = sim.GetPowerFlux("Bot", 0.0)
    return -refl.real / inc.real, trans.real / inc.real


class EigensolverSmallBasisTests(unittest.TestCase):
    """Characterisation of the defect in a normal build.

    These pass today. They are here to pin the inputs that reach the defect (the
    patterned, small-basis configuration) and to state plainly that a normal
    build does not reveal it, so that nobody mistakes a green run for evidence
    that the workspace is adequate.
    """

    def test_patterned_small_bases_solve(self):
        """The overflowing configuration completes and returns sane numbers.

        Deliberately *not* an assertion that the memory access is sound: in a
        normal build this succeeds whether or not the write is out of bounds.
        """
        for nb in OVERFLOWING_BASES:
            with self.subTest(num_basis=nb):
                R, T = rt(nb)
                self.assertTrue(0.0 <= R <= 1.0 + 1e-9, "R out of range: %r" % R)
                self.assertTrue(0.0 <= T <= 1.0 + 1e-9, "T out of range: %r" % T)

    def test_unpatterned_slab_never_enters_the_layer_eigensolver(self):
        """Control: the defect needs a patterned layer."""
        for nb in OVERFLOWING_BASES:
            with self.subTest(num_basis=nb):
                R, T = rt(nb, patterned=False)
                self.assertAlmostEqual(R + T, 1.0, delta=1e-9)

    def test_solve_survives_in_isolation(self):
        """Isolated so that a future hard failure is attributable to this input."""
        res = run_isolated("eigensolver_small_basis")
        self.assertNotEqual(
            res["verdict"], "crash",
            "solving at a small basis aborted the interpreter (rc=%s, %s)"
            % (res["returncode"], res["stderr_tail"]))
        self.assertEqual(res["verdict"], "ok", res)
        # The shared isolation template reports result as repr(result), so it
        # arrives as a string here; the dedicated probe modules return dicts.
        payload = res.get("result")
        if isinstance(payload, str):
            self.assertIn("solved", payload)
            self.assertIn("True", payload)
        else:
            self.assertTrue((payload or {}).get("solved", False), payload)

if __name__ == "__main__":
    unittest.main()
