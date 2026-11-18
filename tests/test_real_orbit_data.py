"""Regression checks against the tracked, published orbital cluster tables.

These are stored-output consistency checks, NOT PCC re-execution.
They do not write to logs or modify experimental files.
"""
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score, confusion_matrix

from evaluate_cluster_relabeling import validate_row_alignment


ROOT = Path(__file__).resolve().parents[1]
CASES = (
    (
        1,
        978,
        0.881361,
        np.array([
            [9315, 367, 3, 0],
            [262, 5222, 129, 12],
            [4, 137, 4312, 0],
            [1, 63, 0, 2461],
        ]),
    ),
    (
        2,
        998,
        0.875158,
        np.array([
            [8804, 369, 1, 9],
            [355, 5248, 82, 12],
            [0, 112, 4795, 0],
            [14, 44, 0, 2443],
        ]),
    ),
)


class RealOrbitalDataTests(unittest.TestCase):
    def test_stored_outputs_match_archived_comparison_logs(self):
        for phi, expected_changes, expected_ari, expected_matrix in CASES:
            with self.subTest(phi=phi):
                original = pd.read_csv(
                    ROOT / f"K-Means_dynamic_map_phi_{phi}_reordered.csv"
                )
                refined = pd.read_csv(
                    ROOT / "results" /
                    f"K-Means_dynamic_map_phi_{phi}_reordered_k=24.csv"
                )

                n = validate_row_alignment(original, refined)
                self.assertEqual(n, 22288)

                orig_labels = original["cluster_index"].to_numpy(dtype=int) + 1
                refined_labels = refined["cluster_index"].to_numpy(dtype=int) + 1

                changes = int(np.count_nonzero(orig_labels != refined_labels))
                self.assertEqual(changes, expected_changes)

                matrix = confusion_matrix(orig_labels, refined_labels)
                np.testing.assert_array_equal(matrix, expected_matrix)

                ari = adjusted_rand_score(orig_labels, refined_labels)
                self.assertAlmostEqual(ari, expected_ari, places=6)


if __name__ == "__main__":
    unittest.main()
