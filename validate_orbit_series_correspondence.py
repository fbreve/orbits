"""Compare the historical MATLAB orbit_series matrix against upstream raw CSVs.

This tool reads existing scientific files and writes only its optional JSON
report. It does not execute PCC, feature extraction, or update any experiments.
It examines both time-series channels and both numeric-file and saved-map
row order. A close numerical match is not mislabeled as bitwise equality.
"""
import argparse
import json
import math
import os
from pathlib import Path

import numpy as np

from validate_upstream_orbit_inputs import (
    EXPECTED_ORBITS, EXPECTED_SAMPLES, InputValidationError, read_map
)

UPSTREAM_SHA = "3c0982175952075fabb0257f0954514b0082f89a"
MAT_SHA = "0ebb3569fcff22b7179935e88c15580ceb4306c4"


def load_historical_mat(path, *, expected_count=EXPECTED_ORBITS):
    """Load the named variable from MATLAB v5/v7.3, accepting either orientation."""
    try:
        from scipy.io import loadmat
        values = loadmat(path, variable_names=["orbit_series"])["orbit_series"]
        format_name = "MAT v5 or earlier"
    except NotImplementedError:
        import h5py
        with h5py.File(path, "r") as handle:
            if "orbit_series" not in handle:
                raise InputValidationError("MAT file has no orbit_series variable")
            values = np.asarray(handle["orbit_series"])
        format_name = "MAT v7.3 (HDF5)"
    except KeyError as exc:
        raise InputValidationError("MAT file has no orbit_series variable") from exc

    if values.ndim != 2:
        raise InputValidationError(f"orbit_series is not 2-D: {values.shape}")
    original_shape = list(values.shape)
    expected_shape = (expected_count, EXPECTED_SAMPLES)
    if values.shape == tuple(reversed(expected_shape)):
        values = values.T
        transposed = True
    elif values.shape == expected_shape:
        transposed = False
    else:
        raise InputValidationError(
            f"Unexpected orbit_series shape {values.shape}; expected "
            f"{expected_shape} or its transpose"
        )
    if not np.issubdtype(values.dtype, np.number):
        raise InputValidationError("orbit_series is not numeric")
    values = np.asarray(values, dtype=np.float64)
    if not np.all(np.isfinite(values)):
        raise InputValidationError("orbit_series contains non-finite values")
    return values, {
        "mat_format": format_name,
        "mat_original_shape": original_shape,
        "mat_transposed_for_comparison": transposed,
    }


def _read_source_arrays(source_dir, initial_coordinates, *, expected_count):
    source_dir = Path(source_dir)
    if not source_dir.is_dir():
        raise InputValidationError(f"Missing input directory: {source_dir}")
    actual = {f.name for f in os.scandir(source_dir) if f.is_file() and f.name.endswith(".csv")}
    expected = {f"{i}.csv" for i in range(expected_count)}
    if actual != expected:
        raise InputValidationError(
            f"Raw orbit filename coverage differs: "
            f"{len(expected-actual)} missing, {len(actual-expected)} extra"
        )

    first = np.empty((expected_count, EXPECTED_SAMPLES), dtype=np.float64)
    second = np.empty_like(first)
    for orbit_id in range(expected_count):
        name = f"{orbit_id}.csv"
        path = source_dir / name
        # fromstring interprets the whitespace-only numeric files without
        # allocating large Python lists or relying on the file's row ordering.
        with path.open("rt", encoding="utf-8") as stream:
            contents = stream.read()
        numbers = np.fromstring(contents, sep=" ", dtype=np.float64)
        if numbers.size != 2 + 2 * EXPECTED_SAMPLES:
            raise InputValidationError(
                f"{name}: expected 2 header values + "
                f"{EXPECTED_SAMPLES} pairs; got {numbers.size} values"
            )
        if not np.all(np.isfinite(numbers)):
            raise InputValidationError(f"{name}: non-finite input data")
        expected_coordinates = initial_coordinates[name]
        if not all(math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12)
                   for a, b in zip(numbers[:2], expected_coordinates)):
            raise InputValidationError(f"{name}: orbital parameters disagree with maps")
        rows = numbers[2:].reshape(EXPECTED_SAMPLES, 2)
        first[orbit_id] = rows[:, 0]
        second[orbit_id] = rows[:, 1]
    return first, second


def _compare(mat, candidate, label, *, rtol=1e-10, atol=1e-8):
    difference = np.abs(mat - candidate)
    close = difference <= atol + rtol * np.abs(candidate)
    exact_rows = int(np.count_nonzero(np.all(mat == candidate, axis=1)))
    close_rows = int(np.count_nonzero(np.all(close, axis=1)))
    return {
        "candidate": label,
        "exact_rows": exact_rows,
        "close_rows": close_rows,
        "total_rows": int(mat.shape[0]),
        "full_exact_match": exact_rows == mat.shape[0],
        "full_close_match": close_rows == mat.shape[0],
        "max_absolute_error": float(np.max(difference)),
        "mean_absolute_error": float(np.mean(difference)),
        "sample_mat_first_row": mat[0, :5].tolist(),
        "sample_candidate_first_row": candidate[0, :5].tolist(),
    }


def analyze(mat_path, source_dir, maps_dir, *, expected_count=EXPECTED_ORBITS):
    """Analyze four named hypotheses rather than guessing the MATLAB origin."""
    maps_dir = Path(maps_dir)
    phi1 = read_map(maps_dir / "K-Means_dynamic_map_phi_1_reordered.csv")
    phi2 = read_map(maps_dir / "K-Means_dynamic_map_phi_2_reordered.csv")
    if len(phi1) != expected_count or len(phi2) != expected_count:
        raise InputValidationError("The initial cluster maps have the wrong row count")
    if set(phi1) != {f"{i}.csv" for i in range(expected_count)} or set(phi2) != set(phi1):
        raise InputValidationError("The initial maps do not cover identical 0..N-1 orbit IDs")
    if any(phi1[name] != phi2[name] for name in phi1):
        raise InputValidationError("The maps disagree about initial orbit coordinates")

    mat, metadata = load_historical_mat(mat_path, expected_count=expected_count)
    raw1, raw2 = _read_source_arrays(source_dir, phi1, expected_count=expected_count)
    ids_in_map_order = [int(name.removesuffix(".csv")) for name in phi1.keys()]
    result = {
        "source_commit": UPSTREAM_SHA,
        "local_historical_mat_blob_sha": MAT_SHA,
        "expected_orbits": expected_count,
        "time_steps": EXPECTED_SAMPLES,
        "input_csvs_checked": expected_count,
        "map_row_order_is_numeric": ids_in_map_order == list(range(expected_count)),
        "map_first_ids": list(phi1)[:8],
        **metadata,
        "hypotheses": [],
    }
    for channel, values in (("first", raw1), ("second", raw2)):
        result["hypotheses"].append(
            _compare(mat, values, f"{channel} column / numeric filename order")
        )
        result["hypotheses"].append(
            _compare(mat, values[ids_in_map_order], f"{channel} column / saved map row order")
        )
    result["any_exact_match"] = any(h["full_exact_match"] for h in result["hypotheses"])
    result["any_close_match"] = any(h["full_close_match"] for h in result["hypotheses"])
    result["best_hypothesis"] = max(
        result["hypotheses"], key=lambda x: (x["close_rows"], x["exact_rows"])
    )["candidate"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True,
                        help="Checkout of upstream orbits-dataset/")
    parser.add_argument("--mat", type=Path,
                        default=Path(__file__).resolve().parent / "orbit_series.mat")
    parser.add_argument("--maps-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--report", type=Path, help="Write result summary JSON here")
    parser.add_argument("--require-full-match", action="store_true",
                        help="Fail if the matrix matches no tested channel/order hypothesis")
    args = parser.parse_args()
    try:
        report = analyze(args.mat, args.source, args.maps_dir)
    except (InputValidationError, OSError, ValueError, UnicodeError) as exc:
        parser.exit(1, f"Invalid or unreadable input: {exc}\n")
    print(json.dumps(report, indent=2))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.require_full_match and not report["any_close_match"]:
        parser.exit(
            2, "No raw time-series channel/order reproduces orbit_series.mat "
            "within the documented numerical tolerance.\n"
        )


if __name__ == "__main__":
    main()
