"""Direct numerical tests for zlahqr_'s single-element and empty ranges.

Why this file exists
--------------------
A guard added to ``zlahqr_`` to stop an out-of-bounds write also skipped the
legal single-element range: it returned early for ``ilo >= ihi`` and dropped the

    w[ilo-1] = h[(ilo-1)+(ilo-1)*ldh];

that the original ``ilo == ihi`` branch performed. Energy-conservation tests
cannot see that, because they never inspect an eigenvalue, so these cases assert
on W directly, with a sentinel in W to catch a branch that writes nothing.

How the routine is reached
--------------------------
``zlahqr_`` has C++ linkage, so it is exported with a mangled name:

    _Z7zlahqr_bbmmmPSt7complexIdEiS1_mmS1_m

ctypes is pointed at that name in the loaded S4 extension. No C test binary is
needed and no source changes are required to make the symbol visible.

Asymmetry worth recording
-------------------------
``zlahqr_`` is exported, but ``zhseqr_`` is file-local (``t`` in nm), so the
larger plumbing cannot be driven the same way. The empty-range case is therefore
exercised directly on zlahqr_, which is where the underflow occurred.
"""

import ctypes
import unittest

import S4

#: Mangled name of ``zlahqr_`` as exported by the extension.
ZLAHQR_MANGLED = "_Z7zlahqr_bbmmmPSt7complexIdEiS1_mmS1_m"

_SENTINEL_RE = -12345.0
_SENTINEL_IM = -6789.0


class _Cplx(ctypes.Structure):
    _fields_ = [("re", ctypes.c_double), ("im", ctypes.c_double)]


def _make(values):
    arr = (_Cplx * len(values))()
    for i, v in enumerate(values):
        arr[i].re = v.real
        arr[i].im = v.imag
    return arr


def _make_sentinel(count):
    arr = (_Cplx * count)()
    for i in range(count):
        arr[i].re = _SENTINEL_RE
        arr[i].im = _SENTINEL_IM
    return arr


class ZlahqrDirectTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.lib = ctypes.CDLL(S4.__file__)
        try:
            cls.zlahqr = getattr(cls.lib, ZLAHQR_MANGLED)
        except AttributeError as exc:
            # A missing symbol must FAIL, not skip. This is the only direct check
            # on zlahqr_'s single-element and empty-range behaviour, and a silent
            # skip would let a regression return unnoticed -- which is how the
            # earlier ilo >= ihi guard shipped having dropped the eigenvalue
            # write for n = ilo = ihi = 1.
            raise AssertionError(
                "zlahqr_ (%s) is not exported by %s (%s). If the signature "
                "changed, update ZLAHQR_MANGLED; do not let this test skip."
                % (ZLAHQR_MANGLED, S4.__file__, exc))
        cls.zlahqr.restype = ctypes.c_size_t
        cls.zlahqr.argtypes = [
            ctypes.c_bool, ctypes.c_bool, ctypes.c_size_t, ctypes.c_size_t,
            ctypes.c_size_t, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p,
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t,
        ]

    def _run(self, n, ilo, ihi, h_values, w_len=None):
        h = _make(h_values)
        w = _make_sentinel(w_len if w_len is not None else n)
        rc = self.zlahqr(True, False, n, ilo, ihi, h, n, w, ilo, ihi,
                         None, 1)
        return rc, w

    def test_single_element_1x1_returns_the_diagonal(self):
        """n = ilo = ihi = 1: W[0] must become H[0] = 3+4i.

        This is exactly the case the earlier guard broke by returning before the
        assignment. It asserts on the eigenvalue, not on energy conservation.
        """
        rc, w = self._run(1, 1, 1, [complex(3.0, 4.0)])
        self.assertEqual(rc, 0, "zlahqr_ reported failure: rc=%r" % rc)
        self.assertNotEqual((w[0].re, w[0].im), (_SENTINEL_RE, _SENTINEL_IM),
                            "W[0] still holds the sentinel: the ilo == ihi "
                            "branch returned without writing the eigenvalue")
        self.assertAlmostEqual(w[0].re, 3.0, places=12)
        self.assertAlmostEqual(w[0].im, 4.0, places=12)

    def test_single_element_real(self):
        rc, w = self._run(1, 1, 1, [complex(2.5, 0.0)])
        self.assertEqual(rc, 0, "rc=%r" % rc)
        self.assertAlmostEqual(w[0].re, 2.5, places=12)
        self.assertAlmostEqual(w[0].im, 0.0, places=12)

    def test_single_element_inside_a_larger_matrix(self):
        """ilo == ihi in the middle: that entry must be written."""
        h = [complex(1, 0), complex(0, 0), complex(0, 0),
             complex(0, 0), complex(5, 0), complex(0, 0),
             complex(0, 0), complex(0, 0), complex(9, 0)]
        rc, w = self._run(3, 2, 2, h, w_len=3)
        self.assertEqual(rc, 0, "rc=%r" % rc)
        self.assertAlmostEqual(w[1].re, 5.0, places=12,
                               msg="W[1] = %r; sentinel means the single-element "
                                   "branch did not write" % w[1].re)

    def test_two_by_two_produces_both_eigenvalues(self):
        """n = 2, ilo = 1, ihi = 2: an upper triangular matrix keeps its diagonal."""
        h = [complex(1, 0), complex(7, 0), complex(0, 0), complex(2, 0)]
        rc, w = self._run(2, 1, 2, h)
        self.assertEqual(rc, 0, "rc=%r" % rc)
        got = sorted((round(w[0].re, 9), round(w[1].re, 9)))
        self.assertEqual(got, [1.0, 2.0],
                         "eigenvalues of an upper triangular 2x2 are its "
                         "diagonal; got %r" % (got,))

    def test_empty_range_does_not_write(self):
        """ilo > ihi must return without touching memory.

        A normal build can only check the return value and the sentinel; the
        out-of-bounds write is visible to AddressSanitizer alone, which is why
        the sanitizer run is part of the acceptance for this file.
        """
        rc, w = self._run(2, 2, 1, [complex(1, 0)] * 4)
        self.assertEqual(rc, 0, "rc=%r" % rc)
        for i in range(2):
            self.assertEqual((w[i].re, w[i].im), (_SENTINEL_RE, _SENTINEL_IM),
                             "W[%d] was written for an empty range" % i)

    def test_empty_range_with_zero_ihi(self):
        """ihi = 0 is the shape whose ihi-2 underflows."""
        rc, w = self._run(2, 1, 0, [complex(1, 0)] * 4)
        self.assertEqual(rc, 0, "rc=%r" % rc)
        for i in range(2):
            self.assertEqual((w[i].re, w[i].im), (_SENTINEL_RE, _SENTINEL_IM),
                             "W[%d] was written for ihi=0" % i)


if __name__ == "__main__":
    unittest.main()
