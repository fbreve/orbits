"""Read-only validation of coauthor-published Saturn-orbit CSV inputs.

Checks that a local external orbit directory and two stored initial maps refer
to the same orbit IDs and initial conditions. This is NOT a PCC/feature
extraction rerun. By default, map entries and directory filenames are checked
exhaustively, while orbit file contents are checked on a deterministic sample.
"""

import argparse
import csv
import math
import os
from pathlib import Path
import re

EXPECTED_ORBITS = 22288
EXPECTED_SAMPLES = 400
COLUMNS = ("semimajor_axis", "eccentricity", "file_name", "cluster_index")
FILE_ID = re.compile(r"(0|[1-9][0-9]*)\.csv\Z")


class InputValidationError(ValueError):
    """Inconsistent mapping or malformed source orbit data."""


def _orbit_id(name):
    match = FILE_ID.fullmatch(name)
    if not match:
        raise InputValidationError(f"Invalid orbit identifier: {name!r}")
    return int(match.group(1))


def _numbers(text, count, source):
    tokens = text.strip().split()
    if len(tokens) != count:
        raise InputValidationError(f"{source}: expected {count} numbers, got {len(tokens)}")
    try:
        values = tuple(float(v) for v in tokens)
    except ValueError as exc:
        raise InputValidationError(f"{source}: nonnumeric value") from exc
    if not all(math.isfinite(v) for v in values):
        raise InputValidationError(f"{source}: non-finite value")
    return values


def _close_coordinates(actual, expected):
    return all(math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12)
               for a, b in zip(actual, expected))


def read_map(path):
    """Read initial cluster map as orbit filename -> initial conditions."""
    data = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(COLUMNS):
            raise InputValidationError(f"{path}: unexpected map columns {reader.fieldnames!r}")
        for row_number, row in enumerate(reader, start=2):
            source = f"{path}:{row_number}"
            if None in row:
                raise InputValidationError(f"{source}: extra CSV fields")
            name = row["file_name"]
            _orbit_id(name)
            if name in data:
                raise InputValidationError(f"{source}: duplicate orbit {name}")
            coordinates = _numbers(
                f"{row['semimajor_axis']} {row['eccentricity']}", 2, source
            )
            try:
                label = int(row["cluster_index"])
            except (ValueError, TypeError) as exc:
                raise InputValidationError(f"{source}: invalid cluster index") from exc
            if label < 0:
                raise InputValidationError(f"{source}: negative cluster index")
            data[name] = coordinates
    if not data:
        raise InputValidationError(f"{path}: map is empty")
    return data


def _select(names, sample_size):
    """Stable selection across numeric orbit IDs, including both endpoints."""
    if sample_size is None or sample_size >= len(names):
        return names
    if sample_size < 1:
        raise InputValidationError("Sample size must be a positive integer")
    if sample_size == 1:
        return names[:1]
    return [names[i * (len(names) - 1) // (sample_size - 1)]
            for i in range(sample_size)]


def validate_directory(data_dir, maps_dir, *, sample_size=32,
                       full_series=False, expected_count=EXPECTED_ORBITS):
    """Validate a local upstream dataset without changing source/result files.

    Map membership, map coordinates, numeric ID range and the complete directory
    filename list are always checked. Header/time-series checks apply to the
    selected subset, or to every orbit when sample_size is None.
    """
    data_dir, maps_dir = Path(data_dir), Path(maps_dir)
    if not data_dir.is_dir():
        raise InputValidationError(f"Orbit directory does not exist: {data_dir}")
    first = read_map(maps_dir / "K-Means_dynamic_map_phi_1_reordered.csv")
    second = read_map(maps_dir / "K-Means_dynamic_map_phi_2_reordered.csv")
    if len(first) != expected_count or len(second) != expected_count:
        raise InputValidationError(
            f"Expected {expected_count} records in each map; "
            f"found {len(first)} and {len(second)}"
        )
    if set(first) != set(second):
        raise InputValidationError("Phi1 and phi2 maps cover different orbit identifiers")
    for name, a in first.items():
        if not _close_coordinates(a, second[name]):
            raise InputValidationError(f"Initial conditions differ between maps: {name}")

    names = sorted(first, key=_orbit_id)
    if [_orbit_id(n) for n in names] != list(range(expected_count)):
        raise InputValidationError("Orbit identifiers are not contiguous 0..N-1")
    expected, actual = set(first), set()
    with os.scandir(data_dir) as entries:
        for entry in entries:
            if not entry.is_file() or not entry.name.endswith(".csv"):
                continue
            _orbit_id(entry.name)
            actual.add(entry.name)
    if actual != expected:
        missing = sorted(expected - actual, key=_orbit_id)[:5]
        extra = sorted(actual - expected, key=_orbit_id)[:5]
        raise InputValidationError(
            f"Source CSV coverage mismatch: missing={missing}, extra={extra}"
        )

    selected = _select(names, sample_size)
    for name in selected:
        with (data_dir / name).open(encoding="utf-8") as handle:
            header = handle.readline()
            if not header:
                raise InputValidationError(f"{name}: empty orbit input")
            coordinates = _numbers(header, 2, f"{name}:header")
            if not _close_coordinates(coordinates, first[name]):
                raise InputValidationError(f"{name}: orbit header disagrees with maps")
            if full_series:
                for index in range(1, EXPECTED_SAMPLES + 1):
                    line = handle.readline()
                    if not line:
                        raise InputValidationError(
                            f"{name}: only {index-1} time steps (expected {EXPECTED_SAMPLES})"
                        )
                    _numbers(line, 2, f"{name}:time-step-{index}")
                if handle.read().strip():
                    raise InputValidationError(
                        f"{name}: extra nonempty samples after {EXPECTED_SAMPLES}"
                    )
    return {
        "map_records": len(first),
        "source_filenames": len(actual),
        "headers_checked": len(selected),
        "series_checked": len(selected) if full_series else 0,
        "time_steps_per_series": EXPECTED_SAMPLES if full_series else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=Path,
                        help="Local ts-saturn-orbits/orbits-dataset/ directory")
    parser.add_argument("--maps-dir", type=Path, default=Path(__file__).resolve().parent,
                        help="Directory holding both K-Means_*_reordered.csv maps")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--sample", type=int, default=32,
                       help="Number of orbit headers to check (default: 32)")
    group.add_argument("--all", action="store_true",
                       help="Check every orbit header")
    parser.add_argument("--full-series", action="store_true",
                        help="Also validate 400 two-column samples per selected orbit")
    args = parser.parse_args()
    try:
        results = validate_directory(
            args.data_dir, args.maps_dir,
            sample_size=None if args.all else args.sample,
            full_series=args.full_series
        )
    except (InputValidationError, OSError, UnicodeError) as exc:
        parser.exit(1, f"Input validation failed: {exc}\n")
    print("Orbit input validation OK (metadata checks, not PCC reproduction):")
    for key, value in results.items():
        if value is not None:
            print(f"  {key}: {value}")
    if not args.all:
        print("  NOTE: orbit file contents checked on a deterministic sample only")
    if not args.full_series:
        print("  NOTE: temporal samples were not read; add --full-series to check them")


if __name__ == "__main__":
    main()
