# Data inventory and provenance

This is a **read-only catalog of the GitHub snapshot from January 12, 2026**. It does not claim that the original generation process has been rerun or that every upstream input is present.

Frozen reference: [`archive/2026-01-12-results`](https://github.com/fbreve/orbits/tree/archive/2026-01-12-results), commit `dfa5992b81065164733e441345cf7112407dd7c6`. The archive contains **54 tracked files totaling 41,213,206 bytes**. Of these, **50** are MATLAB/Python/Gnuplot code, data, saved results, figures and logs, enumerated in [`RESEARCH_MANIFEST.csv`](RESEARCH_MANIFEST.csv).

## File types

| Category | Files | Total bytes | Contents |
| --- | ---: | ---: | --- |
| MATLAB `*.m` | 9 | 16,336 | PCC, DTW, imports, evaluation |
| Python `*.py` | 2 | 3,736 | Cluster reordering and evaluation |
| Gnuplot `*.gp` | 2 | 2,043 | Plotting |
| MATLAB binary `*.mat` | 2 | 21,939,941 | Stored MATLAB workspace/time series |
| CSV `*.csv` | 16 | 18,951,450 | Initial cluster labels, maps, soft labels and entropy |
| PNG `*.png` | 10 | 286,249 | Maps for various k values |
| Log `*.log` | 9 | 2,040 | Prior-run outputs |
| **Research files** | **50** | **41,201,795** | |

The remaining four files in the archived snapshot are `.gitattributes`, `.gitignore`, `LICENSE`, and the original short `README.md`.

## Input tables

`K-Means_dynamic_map_phi_1_reordered.csv` and `K-Means_dynamic_map_phi_2_reordered.csv` are stored at the repository root, one per resonant angle.

The MATLAB import function `read_data.m` explicitly expects four columns with the following names and types:

| Position | Field | Interpreted as |
| --- | --- | --- |
| 1 | `semimajor_axis` | Numeric orbital semi-major-axis coordinate |
| 2 | `eccentricity` | Numeric initial eccentricity |
| 3 | `file_name` | String identifying the corresponding orbit record |
| 4 | `cluster_index` | Integer-valued initial cluster identifier (zero-based in the scripts) |

The main PCC script constructs its graph from **columns 1–2**, reads the initial labels from **column 4**, and writes a copy of the table after replacing column 4 with the refined cluster assignments.

**Important:** row identity must be preserved. The evaluation scripts currently compare the two label columns **by row position**, not by joining on `file_name`.

## Stored results

The `results/` folder contains:

- **10 discrete clustering CSVs**: two resonant angles (φ₁, φ₂) × graph neighborhood sizes **k = 4, 8, 12, 20, 24**.
- **10 PNG maps**, corresponding to these CSVs.
- **2 soft-label CSVs**, one for each angle with **k = 24**. In `pcc_recluster.m`, `owndeg_acc` accumulates domain/ownership values over the configured **100 repetitions × 10 folds**, and `owndeg_acc * 0.001` is exported to the soft-label file.
- **2 entropy maps**: `results/entropy_map_phi1.csv` and `results/entropy_map_phi2.csv`; the generator uses `-sum(softlabels .* log(softlabels + eps), 2)` after loading soft-label values.

The `k` suffix is **graph connectivity**, not a cluster count. The values of `k` in stored results go beyond the **currently hard-coded `k=24`** in the main MATLAB script. No execution history is asserted for each older configuration.

### Logs and measurements

The `logs/` directory contains nine committed text logs, including MATLAB PCC elapsed times and the January 12, 2026 evaluation results from both MATLAB and Python.

| Recorded metric (`k=24`) | φ₁ | φ₂ |
| --- | ---: | ---: |
| Orbit records | 22,288 | 22,288 |
| Relabeled records | 978 | 998 |
| Relabel rate | 4.3880% | 4.4777% |
| Adjusted Rand Index | 0.881361 | 0.875158 |

These values came from `logs/phi_1_eval_python.log` and `logs/phi_2_eval_python.log`. They have **not** been independently recomputed during this repository maintenance.

ARI compares the two stored partitions; it is **not a ground-truth classification metric**.

## Binary MATLAB files

The repository retains:

- `orbit_series.mat` (17,033,684 bytes)
- `matlab_workspace.mat` (4,906,257 bytes)

The script `read_series_csv.m` indicates an intended arrangement of **22,288 rows × 400 time steps** for the `orbit_series` variable. The actual internal variables, dimensionality, MATLAB serialization version and correspondence between these binary files and individual source orbit trajectories were **not independently inspected** here. Do not infer those properties from the file names alone.

## Missing or external inputs

Some existing scripts refer to inputs **not tracked** in the January 2026 branch:

- `dynamic_map_phi_1.csv` (and, for other utility scripts, `dynamic_map_phi_2.csv`)
- `dtw_matrix.mat`, which is an output of `calculate_dtw_matrix.m` rather than a committed artifact
- `series/0.csv`, `series/1.csv`, etc., expected by `read_series_csv.m`
- External MATLAB definitions of `pcc()` and `pcc_buildgraph()` and the related PCC implementation/environment

The main article links to [`epmarinho/ts-saturn-orbits`](https://github.com/epmarinho/ts-saturn-orbits) as a reproducibility repository. **On November 18, 2026**, its current Git tree contains eight tracked files and **does not contain the `orbits-dataset/` directory described in its README**. Its internal code/configuration is still useful, but the full dataset's availability should be confirmed with the source maintainer; this repository should not be described as independently providing all upstream raw inputs.

## Checksums

[`RESEARCH_MANIFEST.csv`](RESEARCH_MANIFEST.csv) provides a byte size and **Git blob SHA-1** for every tracked scientific file in the frozen snapshot. These are Git object hashes calculated from:

`SHA1("blob " + decimal_byte_length + NUL + file_bytes)`.

They are **not ordinary file-content SHA-1 hashes**, and **not SHA-256**. For example, from a checked-out copy:

```bash
git hash-object orbit_series.mat
git hash-object results/K-Means_dynamic_map_phi_1_reordered_k=24.csv
```

Compare the results to `git_blob_sha1` in the manifest. The `main` branch retains the same scientific blobs after documentation updates.

## Licensing

The code repository includes an existing `LICENSE` containing Apache-2.0 terms. The ownership and permitted redistribution of external data, coauthor-generated simulation materials and third-party outputs were not separately established by this inventory. The journal article's CC BY 4.0 license does not automatically apply to those datasets.
