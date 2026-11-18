"""Synthetic unit tests for read-only orbit row-alignment validation.

These tests do NOT execute PCC or read the 22,288-row scientific CSVs.
Run: python -m unittest discover -s tests -v
"""

import unittest

import pandas as pd

from evaluate_cluster_relabeling import validate_row_alignment


class RowAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.original = pd.DataFrame({
            "semimajor_axis": [1.0, 2.0, 3.0],
            "eccentricity": [0.1, 0.2, 0.3],
            "file_name": ["orbit-000", "orbit-001", "orbit-002"],
            "cluster_index": [0, 0, 1],
        })
        self.refined = self.original.copy()
        self.refined["cluster_index"] = [0, 1, 1]

    def test_matching_rows_with_changed_labels_pass(self):
        self.assertEqual(validate_row_alignment(self.original, self.refined), 3)

    def test_reordered_rows_raise(self):
        changed = self.refined.iloc[[2, 0, 1]].reset_index(drop=True)
        with self.assertRaisesRegex(ValueError, "identifier/order mismatch"):
            validate_row_alignment(self.original, changed)

    def test_shorter_refined_table_raises(self):
        with self.assertRaisesRegex(ValueError, "Row count mismatch"):
            validate_row_alignment(self.original, self.refined.iloc[:2])

    def test_longer_refined_table_raises(self):
        extra = pd.concat([self.refined, self.refined.iloc[:1]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "duplicate orbit identifiers"):
            validate_row_alignment(self.original, extra)

    def test_duplicate_identifier_raises(self):
        changed = self.refined.copy()
        changed.loc[2, "file_name"] = changed.loc[1, "file_name"]
        with self.assertRaisesRegex(ValueError, "duplicate orbit identifiers"):
            validate_row_alignment(self.original, changed)

    def test_missing_identifier_raises(self):
        changed = self.refined.copy()
        changed.loc[1, "file_name"] = None
        with self.assertRaisesRegex(ValueError, "missing orbit identifiers"):
            validate_row_alignment(self.original, changed)

    def test_missing_required_column_raises(self):
        changed = self.refined.drop(columns=["file_name"])
        with self.assertRaisesRegex(ValueError, "required columns"):
            validate_row_alignment(self.original, changed)

    def test_different_id_same_row_count_raises(self):
        changed = self.refined.copy()
        changed.loc[2, "file_name"] = "orbit-X"
        with self.assertRaisesRegex(ValueError, "identifier/order mismatch"):
            validate_row_alignment(self.original, changed)


if __name__ == "__main__":
    unittest.main()
