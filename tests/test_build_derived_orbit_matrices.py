"""Offline source fixtures for the two nonhistorical orbit-series MAT exports."""
import csv
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from scipy.io import loadmat

from build_derived_orbit_matrices import derive, MANIFEST_NAME
from validate_upstream_orbit_inputs import InputValidationError


class DerivedOrbitMatricesTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / "orbits-dataset"
        self.source.mkdir()
        self.output = self.root / "derived"
        self.phi1 = np.empty((4, 400), dtype=np.float64)
        self.phi2 = np.empty_like(self.phi1)
        for i in range(4):
            self.phi1[i] = 10 * i + np.arange(400) / 7
            self.phi2[i] = 100 * i + np.arange(400) / 11
            with (self.source / f"{i}.csv").open("w", encoding="utf-8") as stream:
                stream.write(f"{1000+i:.17g} {i/100:.17g}\n")
                for a, b in zip(self.phi1[i], self.phi2[i]):
                    stream.write(f"{a:.17g} {b:.17g}\n")
        self.write_maps()

    def write_maps(self, *, backwards_phi2=False, invalid_phi2=False, omit_phi1=False):
        for phi in (1, 2):
            with (self.root / f"K-Means_dynamic_map_phi_{phi}_reordered.csv").open(
                "w", newline="", encoding="utf-8"
            ) as f:
                writer = csv.writer(f)
                writer.writerow([
                    "semimajor_axis", "eccentricity", "file_name", "cluster_index"
                ])
                ids = list(reversed(range(4))) if backwards_phi2 else list(range(4))
                for i in ids:
                    if omit_phi1 and phi == 1 and i == 1:
                        continue
                    axis = 1000 + i + (1 if invalid_phi2 and phi == 2 and i == 2 else 0)
                    writer.writerow([axis, i / 100, f"{i}.csv", i % 2])

    def build(self):
        return derive(self.source, self.root, self.output, expected_count=4)

    def test_both_matrices_have_exact_source_rows_and_numeric_ids(self):
        result = self.build()
        self.assertEqual(result["validated_inputs"]["per_orbit_csv_files"], 4)
        for angle, expected in ((1, self.phi1), (2, self.phi2)):
            filename = f"orbit_series_phi{angle}_numeric_ids.mat"
            self.assertTrue((self.output / filename).is_file())
            saved = loadmat(self.output / filename)
            np.testing.assert_array_equal(saved[f"orbit_series_phi{angle}"], expected)
            np.testing.assert_array_equal(saved["orbit_ids"].ravel(), np.arange(4))
            np.testing.assert_array_equal(
                saved["semimajor_axis"].ravel(), np.arange(4) + 1000
            )
            np.testing.assert_allclose(
                saved["eccentricity"].ravel(), np.arange(4) / 100
            )
            self.assertEqual(int(saved["source_series_column"].item()), angle)
            self.assertEqual(result["generated"][f"phi{angle}"][
                "exact_source_rows_after_readback"], 4)
        self.assertNotEqual(
            result["generated"]["phi1"]["variable_values_sha256_le_float64_row_major"],
            result["generated"]["phi2"]["variable_values_sha256_le_float64_row_major"],
        )
        self.assertEqual(
            json.loads((self.output / MANIFEST_NAME).read_text())["row_order"],
            "numeric_file_id_ascending",
        )

    def test_phi2_map_reverse_order_does_not_change_export_row_order(self):
        self.write_maps(backwards_phi2=True)
        self.build()
        saved = loadmat(self.output / "orbit_series_phi2_numeric_ids.mat")
        np.testing.assert_array_equal(saved["orbit_series_phi2"], self.phi2)

    def test_source_header_coordinate_corruption_is_rejected(self):
        path = self.source / "2.csv"
        rows = path.read_text().splitlines()
        rows[0] = "99 99"
        path.write_text("\n".join(rows) + "\n")
        with self.assertRaisesRegex(InputValidationError, "disagree"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_missing_source_series_is_rejected(self):
        (self.source / "1.csv").unlink()
        with self.assertRaisesRegex(InputValidationError, "coverage"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_missing_map_id_is_rejected(self):
        self.write_maps(omit_phi1=True)
        with self.assertRaisesRegex(InputValidationError, "numeric orbit ID"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_cross_phi_coordinate_mismatch_is_rejected(self):
        self.write_maps(invalid_phi2=True)
        with self.assertRaisesRegex(InputValidationError, "disagree"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_nonfinite_series_is_rejected(self):
        file = self.source / "0.csv"
        text = file.read_text().splitlines()
        text[-1] = "NaN 44"
        file.write_text("\n".join(text) + "\n")
        with self.assertRaisesRegex(InputValidationError, "non-finite"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_short_series_is_rejected(self):
        file = self.source / "0.csv"
        rows = file.read_text().splitlines()
        file.write_text("\n".join(rows[:-1]) + "\n")
        with self.assertRaisesRegex(InputValidationError, "expected 2 header values"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_refuses_to_overwrite_original_output(self):
        self.output.mkdir()
        dest = self.output / "orbit_series_phi1_numeric_ids.mat"
        dest.write_text("MUST NOT OVERWRITE", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            self.build()
        self.assertEqual(dest.read_text(encoding="utf-8"), "MUST NOT OVERWRITE")

    def test_manifest_includes_hashes_and_source_revision(self):
        report = self.build()
        self.assertEqual(
            report["upstream_commit"],
            "3c0982175952075fabb0257f0954514b0082f89a",
        )
        for name in ("phi1", "phi2"):
            self.assertEqual(len(report["generated"][name]["mat_file_sha256"]), 64)
            self.assertGreater(report["generated"][name]["mat_file_bytes"], 0)
        self.assertNotIn("orbit_series.mat", [x.name for x in self.output.iterdir()])


if __name__ == "__main__":
    unittest.main()
