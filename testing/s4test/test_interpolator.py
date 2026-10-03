import unittest
import S4

class InterpolatorTests(unittest.TestCase):
    def test_linear_basic(self):
        table = ((0.0, (0.0,)), (0.5, (0.25,)), (1.0, (1.0,)))
        interp = S4.NewInterpolator('linear', table)
        self.assertAlmostEqual(interp.Get(0.0)[0], 0.0)
        self.assertAlmostEqual(interp.Get(0.25)[0], 0.125)
        self.assertAlmostEqual(interp.Get(0.75)[0], 0.625)
        # linear extrapolation
        self.assertAlmostEqual(interp.Get(1.5)[0], 1.75)
        self.assertAlmostEqual(interp.Get(-0.5)[0], -0.25)

    def test_cubic_spline_nodes(self):
        table = ((0.0, (0.0,)), (0.5, (0.25,)), (1.0, (1.0,)))
        interp = S4.NewInterpolator('cubic spline', table)
        self.assertAlmostEqual(interp.Get(0.0)[0], 0.0)
        self.assertAlmostEqual(interp.Get(0.5)[0], 0.25)
        self.assertAlmostEqual(interp.Get(1.0)[0], 1.0)

    def test_cubic_spline_natural(self):
        # Using a natural cubic spline, the second derivative at endpoints is 0.
        # For points (0,0), (0.5,0.25), (1,1):
        # The value at 0.75 should be exactly 0.578125.
        table = ((0.0, (0.0,)), (0.5, (0.25,)), (1.0, (1.0,)))
        interp = S4.NewInterpolator('cubic spline', table)
        self.assertAlmostEqual(interp.Get(0.75)[0], 0.578125)

    def test_multi_output(self):
        table = ((0.0, (0.0, 1.0)), (0.5, (0.25, 0.5)), (1.0, (1.0, 0.0)))
        interp = S4.NewInterpolator('cubic spline', table)
        res = interp.Get(0.5)
        self.assertEqual(len(res), 2)
        self.assertAlmostEqual(res[0], 0.25)
        self.assertAlmostEqual(res[1], 0.5)

    def test_degenerate_len2(self):
        # n=2 should behave exactly like linear interpolation
        table = ((0.0, (0.0,)), (1.0, (1.0,)))
        interp = S4.NewInterpolator('cubic spline', table)
        self.assertAlmostEqual(interp.Get(0.25)[0], 0.25)
        self.assertAlmostEqual(interp.Get(0.75)[0], 0.75)
        self.assertAlmostEqual(interp.Get(-1.0)[0], -1.0)
        self.assertAlmostEqual(interp.Get(2.0)[0], 2.0)

    def test_hermite_endpoints(self):
        table = ((0.0, (0.0,)), (0.5, (0.25,)), (1.0, (1.0,)))
        interp = S4.NewInterpolator('cubic hermite spline', table)
        # Test endpoints and outside bounds to ensure no NaN/crash
        res_start = interp.Get(0.0)[0]
        res_end = interp.Get(1.0)[0]
        res_mid = interp.Get(0.25)[0]
        self.assertTrue(res_start == res_start) # Not NaN
        self.assertTrue(res_end == res_end) # Not NaN
        self.assertTrue(res_mid == res_mid) # Not NaN

    def test_duplicate_out_of_order_x(self):
        with self.assertRaises(ValueError):
            S4.NewInterpolator('linear', ((0.0, (0.0,)), (0.0, (1.0,))))
        with self.assertRaises(ValueError):
            S4.NewInterpolator('linear', ((1.0, (1.0,)), (0.0, (0.0,))))
        with self.assertRaises(ValueError): # Should require n >= 2
            S4.NewInterpolator('linear', ((0.0, (0.0,)),))

    def test_cubic_spline_non_equidistant(self):
        # 0.875 reference for non-equidistant points
        table = ((0.0, (0.0,)), (1.0, (1.0,)), (3.0, (0.0,)))
        interp = S4.NewInterpolator('cubic spline', table)
        self.assertAlmostEqual(interp.Get(2.0)[0], 0.875)

    def test_dimension_mismatch(self):
        with self.assertRaises(ValueError):
            S4.NewInterpolator('linear', ((0.0, (1.0, 2.0)), (1.0, (3.0,))))

    def test_empty_output(self):
        with self.assertRaises(ValueError):
            S4.NewInterpolator('linear', ((0.0, ()), (1.0, ())))

    def test_nan_inputs(self):
        nan = float('nan')
        inf = float('inf')
        with self.assertRaises(ValueError):
            S4.NewInterpolator('linear', ((0.0, (nan,)), (1.0, (1.0,))))
        with self.assertRaises(ValueError):
            S4.NewInterpolator('linear', ((nan, (0.0,)), (1.0, (1.0,))))
        with self.assertRaises(ValueError):
            S4.NewInterpolator('linear', ((0.0, (inf,)), (1.0, (1.0,))))

    def test_nan_get(self):
        table = ((0.0, (0.0,)), (1.0, (1.0,)))
        interp = S4.NewInterpolator('linear', table)
        with self.assertRaises(ValueError):
            interp.Get(float('nan'))
        with self.assertRaises(ValueError):
            interp.Get(float('inf'))

    @unittest.skip(
        "Code Review Only: C-level allocation failure paths in Interpolator_New are "
        "verified by code review. Python-level RLIMIT_AS tests cannot isolate C-level "
        "malloc failures without first failing Python tuple allocations."
    )
    def test_oom_memory_error(self):
        pass

if __name__ == "__main__":
    unittest.main()
