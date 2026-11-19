"""Small offline fixtures for the read-only upstream orbit-data validator."""

import csv
from pathlib import Path
import tempfile
import unittest

from validate_upstream_orbit_inputs import (
    InputValidationError, _select, validate_directory
)


class OrbitInputFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.inputs = self.root / "orbits-dataset"
        self.inputs.mkdir()
        self.write_maps()
        self.write_orbits()

    def write_maps(self, *, duplicate=False, reverse=False, perturb=False):
        for phi in (1, 2):
            with (self.root / f"K-Means_dynamic_map_phi_{phi}_reordered.csv").open(
                "w", newline="", encoding="utf-8"
            ) as stream:
                writer = csv.writer(stream)
                writer.writerow([
                    "semimajor_axis", "eccentricity", "file_name", "cluster_index"
                ])
                indices = list(reversed(range(3))) if reverse and phi == 2 else range(3)
                for i in indices:
                    semimajor = 1000 + i + (1 if perturb and phi == 2 and i == 1 else 0)
                    writer.writerow([semimajor, i / 100, f"{i}.csv", i % 2])
                if duplicate and phi == 2:
                    writer.writerow([1000, 0, "0.csv", 0])

    def write_orbits(self, *, remove=None, malformed_header=None, bad_row=None,
                     short=None, extra=None):
        for i in range(3):
            if i == remove:
                continue
            with (self.inputs / f"{i}.csv").open("w", encoding="utf-8") as stream:
                stream.write("nonsense\n" if i == malformed_header
                             else f"{1000 + i} {i / 100}\n")
                for j in range(400 - (1 if i == short else 0)):
                    stream.write("1 2 3\n" if i == bad_row and j == 10
                                 else f"{j * 0.1} {j * 0.2}\n")
                if i == extra:
                    stream.write("3 4\n")

    def check(self, **kwargs):
        return validate_directory(
            self.inputs, self.root, expected_count=3, **kwargs
        )

    def test_valid_full_series(self):
        result = self.check(sample_size=None, full_series=True)
        self.assertEqual(result["headers_checked"], 3)
        self.assertEqual(result["series_checked"], 3)

    def test_valid_sample_reports_coverage(self):
        result = self.check(sample_size=2)
        self.assertEqual(result["map_records"], 3)
        self.assertEqual(result["source_filenames"], 3)
        self.assertEqual(result["headers_checked"], 2)
        self.assertEqual(result["series_checked"], 0)

    def test_order_difference_in_maps_does_not_break_identity_matching(self):
        self.write_maps(reverse=True)
        self.check(sample_size=None, full_series=True)

    def test_duplicate_map_id_rejected(self):
        self.write_maps(duplicate=True)
        with self.assertRaisesRegex(InputValidationError, "duplicate"):
            self.check()

    def test_cross_angle_coordinate_mismatch_rejected(self):
        self.write_maps(perturb=True)
        with self.assertRaisesRegex(InputValidationError, "differ between maps"):
            self.check()

    def test_missing_orbit_file_rejected(self):
        (self.inputs / "2.csv").unlink()
        with self.assertRaisesRegex(InputValidationError, "coverage mismatch"):
            self.check()

    def test_extra_orbit_file_rejected(self):
        (self.inputs / "3.csv").write_text("1 2\n", encoding="utf-8")
        with self.assertRaisesRegex(InputValidationError, "coverage mismatch"):
            self.check()

    def test_malformed_header_rejected(self):
        self.write_orbits(malformed_header=1)
        with self.assertRaisesRegex(InputValidationError, "expected 2 numbers"):
            self.check(sample_size=None)

    def test_header_not_matching_coordinates_rejected(self):
        (self.inputs / "1.csv").write_text("9 9\n", encoding="utf-8")
        with self.assertRaisesRegex(InputValidationError, "disagrees with maps"):
            self.check(sample_size=None)

    def test_wrong_time_row_column_count_rejected(self):
        self.write_orbits(bad_row=1)
        with self.assertRaisesRegex(InputValidationError, "expected 2 numbers"):
            self.check(sample_size=None, full_series=True)

    def test_short_time_series_rejected(self):
        self.write_orbits(short=1)
        with self.assertRaisesRegex(InputValidationError, "only 399 time steps"):
            self.check(sample_size=None, full_series=True)

    def test_extra_time_series_row_rejected(self):
        self.write_orbits(extra=1)
        with self.assertRaisesRegex(InputValidationError, "extra nonempty samples"):
            self.check(sample_size=None, full_series=True)

    def test_nonfinite_header_rejected(self):
        (self.inputs / "1.csv").write_text("NaN Inf\n", encoding="utf-8")
        with self.assertRaisesRegex(InputValidationError, "non-finite"):
            self.check(sample_size=None)

    def test_zero_sample_rejected(self):
        with self.assertRaisesRegex(InputValidationError, "positive integer"):
            self.check(sample_size=0)

    def test_sampling_is_deterministic_and_has_endpoints(self):
        values = [f"{i}.csv" for i in range(100)]
        self.assertEqual(_select(values, 2), ["0.csv", "99.csv"])
        self.assertEqual(_select(values, 3), ["0.csv", "49.csv", "99.csv"])


if __name__ == "__main__":
    unittest.main()
