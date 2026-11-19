"""Create two NEW, independently checked MATLAB matrices from published orbit CSVs.

Never edits the historical orbit_series.mat or any raw input. Rows are in
numeric orbit-ID order (0.csv through 22287.csv), *not* in K-Means map
lexicographic row order. The first/second raw CSV time-series columns define
phi1/phi2 respectively, matching the coauthor's feature-reading scripts.

Only creates files in --output-dir. Does not run PCC, DTW or clustering.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat, savemat

from validate_orbit_series_correspondence import _read_source_arrays, UPSTREAM_SHA
from validate_upstream_orbit_inputs import (
    EXPECTED_ORBITS, EXPECTED_SAMPLES, InputValidationError, read_map
)

FORMAT_VERSION = 1
FILES = {
    1: ("orbit_series_phi1_numeric_ids.mat", "orbit_series_phi1"),
    2: ("orbit_series_phi2_numeric_ids.mat", "orbit_series_phi2"),
}
MANIFEST_NAME = "DERIVED_ORBIT_SERIES_MANIFEST.json"


def _file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(2 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _value_sha256(matrix):
    """Hash row-major IEEE 754 little-endian binary64 values, not MAT bytes."""
    return hashlib.sha256(
        np.asarray(matrix, dtype="<f8", order="C").tobytes(order="C")
    ).hexdigest()


def _read_maps(maps_dir, expected_count):
    maps_dir = Path(maps_dir)
    names = [f"{i}.csv" for i in range(expected_count)]
    expected = set(names)
    first_file = maps_dir / "K-Means_dynamic_map_phi_1_reordered.csv"
    second_file = maps_dir / "K-Means_dynamic_map_phi_2_reordered.csv"
    first = read_map(first_file)
    second = read_map(second_file)
    if set(first) != expected or set(second) != expected:
        raise InputValidationError(
            "The two cluster maps must contain each numeric orbit ID exactly once"
        )
    for name in names:
        if first[name] != second[name]:
            raise InputValidationError(
                f"Initial coordinates disagree between angle maps: {name}"
            )
    initial = np.array([first[name] for name in names], dtype=np.float64)
    return first, initial, {
        first_file.name: _file_sha256(first_file),
        second_file.name: _file_sha256(second_file),
    }


def _check_saved_mat(path, variable, expected, ids, coordinates, column):
    """Read back each exported MAT and verify all source values EXACTLY."""
    saved = loadmat(path)
    if variable not in saved:
        raise InputValidationError(f"{path}: missing MATLAB variable {variable}")
    actual = saved[variable]
    if actual.shape != expected.shape or actual.dtype != np.dtype("float64"):
        raise InputValidationError(f"{path}: incorrect series dtype/shape")
    exact_rows = int(np.count_nonzero(np.all(actual == expected, axis=1)))
    if exact_rows != len(ids):
        raise InputValidationError(
            f"{path}: only {exact_rows}/{len(ids)} rows equal source samples"
        )
    for key, target in (
        ("orbit_ids", ids[:, None]),
        ("semimajor_axis", coordinates[:, 0:1]),
        ("eccentricity", coordinates[:, 1:2]),
    ):
        if key not in saved or not np.array_equal(saved[key], target):
            raise InputValidationError(f"{path}: incorrect {key} metadata")
    if (int(saved["source_series_column"].item()) != column
            or str(saved["source_commit"].item()) != UPSTREAM_SHA
            or str(saved["row_order"].item()) != "numeric_file_id_ascending"):
        raise InputValidationError(f"{path}: incorrect provenance metadata")
    if not np.all(np.isfinite(actual)):
        raise InputValidationError(f"{path}: non-finite series values")
    return exact_rows


def derive(source_dir, maps_dir, output_dir, *, expected_count=EXPECTED_ORBITS):
    """Build, reload and cross-check both channels; fail without overwrites."""
    source_dir, maps_dir, output_dir = (
        Path(source_dir), Path(maps_dir), Path(output_dir)
    )
    if expected_count < 1:
        raise InputValidationError("Expected orbit count must be positive")
    targets = [output_dir / item[0] for item in FILES.values()]
    manifest_path = output_dir / MANIFEST_NAME
    if any(p.exists() for p in targets + [manifest_path]):
        raise FileExistsError("Refusing to overwrite an existing derived matrix or manifest")
    first_map, coords, map_hashes = _read_maps(maps_dir, expected_count)
    phi1, phi2 = _read_source_arrays(
        source_dir, first_map, expected_count=expected_count
    )
    ids = np.arange(expected_count, dtype=np.int64)
    if phi1.shape != (expected_count, EXPECTED_SAMPLES) or phi2.shape != phi1.shape:
        raise InputValidationError("Source series matrix has unexpected shape")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    for column, series in ((1, phi1), (2, phi2)):
        filename, variable = FILES[column]
        target = output_dir / filename
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite {target}")
        savemat(
            target,
            {
                variable: series,
                "orbit_ids": ids[:, None],
                "semimajor_axis": coords[:, 0:1],
                "eccentricity": coords[:, 1:2],
                "source_series_column": np.array([[column]], dtype=np.int64),
                "source_commit": UPSTREAM_SHA,
                "row_order": "numeric_file_id_ascending",
            },
            format="5",
            do_compression=True,
            oned_as="column",
        )
        checked = _check_saved_mat(
            target, variable, series, ids, coords, column
        )
        results[f"phi{column}"] = {
            "file": filename,
            "matlab_variable": variable,
            "source_series_column_zero_based": column - 1,
            "number_of_rows": expected_count,
            "time_steps_per_orbit": EXPECTED_SAMPLES,
            "exact_source_rows_after_readback": checked,
            "all_values_finite": True,
            "variable_values_sha256_le_float64_row_major": _value_sha256(series),
            "mat_file_sha256": _file_sha256(target),
            "mat_file_bytes": target.stat().st_size,
        }

    manifest = {
        "format_version": FORMAT_VERSION,
        "description": "Derived input matrices; NOT historical experiment outputs",
        "upstream_repository": "epmarinho/ts-saturn-orbits",
        "upstream_commit": UPSTREAM_SHA,
        "upstream_series_folder": "orbits-dataset",
        "map_repository": "fbreve/orbits",
        "map_file_sha256": map_hashes,
        "row_order": "numeric_file_id_ascending",
        "row_identity_rule": "row i (0-based) corresponds to i.csv",
        "source_header": ["semimajor_axis", "eccentricity"],
        "source_time_columns": {
            "phi1": "first column after initial-parameter header",
            "phi2": "second column after initial-parameter header",
        },
        "validated_inputs": {
            "per_orbit_csv_files": expected_count,
            "total_time_series_values": expected_count * EXPECTED_SAMPLES * 2,
        },
        "generated": results,
        "scientific_limit": (
            "Inputs/values verified; neither PCC nor the published clustering "
            "or dimensionality-reduction pipelines were rerun. The archived "
            "orbit_series.mat remains unchanged and is NOT either derived matrix."
        ),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument(
        "--maps-dir", type=Path, default=Path(__file__).resolve().parent
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = derive(args.source, args.maps_dir, args.output_dir)
    except (InputValidationError, OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Matrix derivation failed: {exc}\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
