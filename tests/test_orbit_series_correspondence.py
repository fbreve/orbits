"""Offline fixture checks for the orbit_series.mat/source CSV correspondence tool."""
import csv
from pathlib import Path
import tempfile
import unittest

import numpy as np
from scipy.io import savemat

from validate_orbit_series_correspondence import analyze, InputValidationError


class MatCorrespondenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.dataset = self.root / "orbits-dataset"
        self.dataset.mkdir()
        self.p1 = np.empty((4, 400), dtype=np.float64)
        self.p2 = np.empty_like(self.p1)
        for i in range(4):
            self.p1[i] = i * 10 + np.arange(400) / 7
            self.p2[i] = i * 100 + np.arange(400) / 11
            with (self.dataset / f"{i}.csv").open("w", encoding="utf-8") as f:
                f.write(f"{1000+i:.17g} {i/100:.17g}\n")
                for a, b in zip(self.p1[i], self.p2[i]):
                    f.write(f"{a:.17g} {b:.17g}\n")
        self.write_maps()
        self.save(self.p1)

    def write_maps(self, *, reverse_phi2=False):
        for phi in (1, 2):
            with (self.root / f"K-Means_dynamic_map_phi_{phi}_reordered.csv").open(
                "w", newline="", encoding="utf-8"
            ) as f:
                writer = csv.writer(f)
                writer.writerow(["semimajor_axis","eccentricity","file_name","cluster_index"])
                ids = [0, 1, 2, 3]
                if reverse_phi2 and phi == 2:
                    ids.reverse()
                for i in ids:
                    writer.writerow([1000+i, i/100, f"{i}.csv", i % 2])

    def save(self, matrix):
        savemat(self.root / "orbit_series.mat", {"orbit_series": matrix})

    def check(self):
        return analyze(
            self.root / "orbit_series.mat", self.dataset,
            self.root, expected_count=4
        )

    def test_exact_first_channel_numeric(self):
        r = self.check()
        self.assertTrue(r["any_exact_match"])
        self.assertEqual(r["best_hypothesis"], "first column / numeric filename order")

    def test_exact_second_channel_numeric(self):
        self.save(self.p2)
        r = self.check()
        self.assertTrue(r["any_exact_match"])
        self.assertIn("second column", r["best_hypothesis"])

    def test_permuted_map_order_is_explicitly_tested(self):
        self.write_maps(reverse_phi2=True)
        # The first map controls its own saved row order; the two maps may
        # be differently sorted but must agree on identity/coordinates.
        r = self.check()
        self.assertTrue(r["any_exact_match"])

    def test_matrix_transpose_is_detected(self):
        self.save(self.p1.T)
        r = self.check()
        self.assertTrue(r["any_exact_match"])
        self.assertTrue(r["mat_transposed_for_comparison"])

    def test_matrix_with_different_values_is_not_matched(self):
        self.save(np.full((4, 400), -999.0))
        r = self.check()
        self.assertFalse(r["any_close_match"])

    def test_header_corruption_is_rejected(self):
        path = self.dataset / "3.csv"
        rows = path.read_text().splitlines()
        rows[0] = "9999 9999"
        path.write_text("\n".join(rows) + "\n")
        with self.assertRaisesRegex(InputValidationError, "disagree"):
            self.check()

    def test_missing_orbit_is_rejected(self):
        (self.dataset / "3.csv").unlink()
        with self.assertRaisesRegex(InputValidationError, "coverage"):
            self.check()

    def test_short_series_is_rejected(self):
        path = self.dataset / "3.csv"
        rows = path.read_text().splitlines()
        path.write_text("\n".join(rows[:-1]) + "\n")
        with self.assertRaisesRegex(InputValidationError, "expected 2 header values"):
            self.check()

    def test_nonfinite_series_is_rejected(self):
        path = self.dataset / "2.csv"
        rows = path.read_text().splitlines()
        rows[-1] = "NaN 42"
        path.write_text("\n".join(rows) + "\n")
        with self.assertRaisesRegex(InputValidationError, "non-finite"):
            self.check()

    def test_constant_eccentricity_diagnostic(self):
        from validate_orbit_series_correspondence import inspect_mat_structure
        matrix = np.repeat(np.array([[0.0], [0.01], [0.02], [0.03]]), 400, axis=1)
        coordinates = {f"{i}.csv": (1000+i, i/100) for i in range(4)}
        d = inspect_mat_structure(matrix, coordinates)
        self.assertEqual(d["constant_rows_exact"], 4)
        self.assertEqual(
            d["initial_condition_hypotheses"]["eccentricity / numeric order"]
            ["constant_parameter_exact_rows"], 4
        )
        self.assertEqual(
            d["initial_condition_hypotheses"]["semimajor_axis / numeric order"]
            ["constant_parameter_exact_rows"], 0
        )

    def test_wrong_mat_shape_is_rejected(self):
        self.save(np.ones((3, 4)))
        with self.assertRaisesRegex(InputValidationError, "Unexpected"):
            self.check()


if __name__ == "__main__":
    unittest.main()
