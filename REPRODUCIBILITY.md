# Reproducibility and execution status

**Originally documented: November 18, 2026; upstream data rechecked: November 19, 2026.** This guide is a source review and recovery checklist. **The scientific PCC simulations, MATLAB/DTW computations and plotting workflow were not executed or experimentally validated during this maintenance.**

The original outputs are kept intact on `main` and in [`archive/2026-01-12-results`](https://github.com/fbreve/orbits/tree/archive/2026-01-12-results).

## What is available locally?

| Workflow | Main entry point | Required inputs | Status |
| --- | --- | --- | --- |
| Python comparison of old vs. new labels | `evaluate_cluster_relabeling.py` | Both root `K-Means_*_reordered.csv` files and matching `results/*_k=24.csv` | **Validated on all 22,288 records for both angles**, including row identifiers, confusion matrices, relabel counts and ARI. No PCC rerun. |
| MATLAB comparison | `evaluate_cluster_relabeling.m` | Same CSV files and `adjustedRandIndex.m` | All named files **tracked**. Requires suitable MATLAB toolboxes; runtime not retested. |
| PCC on 2D orbit conditions | `pcc_recluster.m` | Root CSV, external `pcc` / `pcc_buildgraph` functions | Data **tracked**, PCC dependency **not vendored or pinned**. No new run performed. |
| PCC on time series | `pcc_recluster_series.m` | `orbit_series.mat` plus `dynamic_map_phi_1.csv` | First tracked, second **absent**. |
| PCC on DTW graph | `pcc_recluster_series_dtw.m` | `dynamic_map_phi_1.csv`, `dtw_matrix.mat` | Both absent; matrix generator exists but is costly. |
| Recreate raw `orbit_series.mat` | `read_series_csv.m` | `series/<index>.csv` for 22,288 records | **Raw orbit CSVs now available externally**, but the current importer expects a different folder and data layout. **Not rerun; adaptation required.** |
| Generate entropy maps | `generate_entropy_maps.m` | `dynamic_map_phi_{1,2}.csv` and soft labels | Original-map CSVs **absent**. Saved entropy outputs are tracked. |
| Reorder original clusters | `reorder_clusters.py` | `dynamic_map_phi_1.csv`, `dynamic_map_phi_2.csv` | Both **absent**. Output naming does not match the checked-in root tables exactly. |
| Gnuplot maps | `plot_map*.gp` | Corresponding CSV result and Gnuplot | Scripts and many PNG results tracked. Plots not regenerated. |

Note: `calculate_dtw_matrix.m` computes a dense symmetric distance matrix over all series and saves `dtw_matrix.mat` as `-v7.3`. For 22,288 series, the matrix alone would contain approximately **496.8 million double-precision elements (~3.97 GB uncompressed)**, before overhead or temporary arrays. **Do not run casually on a workstation without a resource plan**.

## Software dependencies

### MATLAB workflows

The sources use:

- MATLAB table/data import, `cvpartition`, `confusionmat`, `parfor`, `dtw` and `writetable`/`writematrix`.
- A compatible graph-based **PCC** implementation providing `pcc()` and `pcc_buildgraph()`: see [the MATLAB/C-MEX PCC repository](https://github.com/fbreve/Particle-Competition-and-Cooperation), which contains both functions. The code is **not vendored** into `orbits`, and the exact source commit, MEX build, toolbox installation and version used for the stored results are **not pinned**. Do not assume its current `master` reproduces the archived output.
- Parallel execution support for `parfor`; MATLAB's Parallel Computing Toolbox is required for supported parallel execution, and other functions may require additional toolboxes.
- Gnuplot for plot generation. The current `pcc_recluster.m` contains a hard-coded Windows executable path `d:\tools\gnuplot\bin\gnuplot`; users on other installations must adapt this path if they choose to rerun and create figures.

A `LICENSE` in this repository is **not a license for MATLAB, its toolboxes, or the external PCC implementation**.

### Python evaluation

`evaluate_cluster_relabeling.py` imports `numpy`, `pandas`, and `sklearn.metrics`. The `reorder_clusters.py` utility uses only Python's standard library.

From a suitable Python virtual environment, the **stored-result evaluation** can be attempted with:

```bash
python -m pip install numpy pandas scikit-learn
python evaluate_cluster_relabeling.py
```

This command **does not rerun PCC**; it compares checked-in labels. It appends evaluation logs to `logs/` and may update tracked files. Work from a copy or discard intentionally generated changes. This command has not been revalidated as a standalone historical run; the automated, read-only comparison regression uses dependency versions pinned in `.github/workflows/validate-orbit-evaluation.yml`.

### Stored-output regression validation — November 18, 2026

The Python evaluator was checked against the complete **22,288-row φ₁ and φ₂ CSV pairs**, after first comparing the original and refined orbit identifiers and verifying that all IDs are unique and in the same order.

A new automated integration test, `tests/test_real_orbit_data.py`, checks the saved relabel totals, entire 4×4 confusion matrices and Adjusted Rand Index for both angles against the historical logs. The ten synthetic tests cover row misalignment, invalid identities, empty identifiers and distinct DataFrame indexes. **All eleven tests passed on GitHub Actions** with Python 3.12; no scientific files were modified during the workflow.

This validation confirms **stored-output comparison**, not rerunning the historical 100×10 PCC experiments or independently reproducing the neural/astronomical feature extraction pipeline.

## Original configured PCC study

The current `pcc_recluster.m` script:

1. Reads `K-Means_dynamic_map_phi_1_reordered.csv`; the user must edit this line to select φ₂.
2. Uses the first **two** numerical features and the original labels (converted from zero-based to one-based).
3. Initializes the random generator with `rng('default')` and constructs **100 repeats of 10-fold partitions** via `cvpartition`.
4. Builds a graph using `pcc_buildgraph(X, k=24, disttype='seuclidean')` in the current version.
5. Runs `pcc(graph, slabel, maxiter=50000, earlystop=false, Xgraph=true, seed=j, useseed=true)` for each fold and repetition, accumulating node ownership values.
6. Converts the summed ownership matrix into hard assignments using `max` and exports soft-label values scaled by `0.001`.
7. Writes CSVs and a log, and invokes Gnuplot to produce a map.

**Version sensitivity:** the behavior of `pcc()`, seeding, `Xgraph`, and standardized Euclidean distance scaling can change between PCC implementations or revisions. The script's explicit options alone do **not** guarantee scientific equivalence if a different PCC version is supplied. Before a rerun, identify and freeze the exact external code revision and any MEX dependencies.

The script's output names are assembled from a dataset stem and `k`. Existing outputs for `k = 4, 8, 12, 20, 24` do not establish how many historical runs were executed with any one version of the script.

## Validation and evaluation cautions

- **Python evaluator (merged PR #1):** checks `file_name` existence, uniqueness, non-null/non-blank values, equal table lengths and identical identifier order before comparing `cluster_index` values. It raises an error on mismatch and no longer truncates input records.
- **MATLAB evaluator (unchanged):** still compares the column-4 labels by row position and uses `min(original_row_count, result_row_count)`, potentially truncating longer tables. This needs a separate MATLAB-validated correction.
- Numeric relabel count assumes labels have comparable IDs; **ARI is invariant to label permutation**, but raw relabel count and confusion matrices are not.
- The MATLAB and Python implementations both write logs in append mode. Preserve the original `logs/` as evidence, rather than treating each subsequent append as the original published output.
- The absolute `d:\tools\gnuplot` path, `logs\...` and `results\...` paths may not be portable outside Windows.
- `adjustedRandIndex.m` has no explicit defined result for some degenerate label inputs (e.g., a denominator of zero). That is an edge-case review item, not an asserted error in the archived experiments.
- The entropy generator reads files named `dynamic_map_phi_1.csv` and `dynamic_map_phi_2.csv`, absent from the current repository; do not silently substitute the K-Means-derived files without a scientifically grounded mapping.
- The main script exports a new graph refinement based on the *current* external PCC implementation; no assertion is made that current upstream changes preserve the 2025/2026 scientific output.

## External data availability

The paper's Data Availability statement links to [`epmarinho/ts-saturn-orbits`](https://github.com/epmarinho/ts-saturn-orbits). **This gap was resolved on November 19, 2026:** the coauthor added the [`orbits-dataset/` CSV directory](https://github.com/epmarinho/ts-saturn-orbits/tree/3c0982175952075fabb0257f0954514b0082f89a/orbits-dataset) and [historical saved outputs](https://github.com/epmarinho/ts-saturn-orbits/tree/3c0982175952075fabb0257f0954514b0082f89a/results), at Git commit [`3c0982175952075fabb0257f0954514b0082f89a`](https://github.com/epmarinho/ts-saturn-orbits/tree/3c0982175952075fabb0257f0954514b0082f89a). The dataset directory contains **22,288 files**, with contiguous numerical identifiers from `0.csv` to `22287.csv` (approximately **437.9 MB** of raw tracked content). Each checked example begins with two initial orbital parameters followed by rows of time-series values; the upstream README describes **400 time steps** per orbit. These files need **not** be copied into this repository.

The coauthor also published `results/README.md`, `results/manifest.json`, and `results/validate_results.py`, providing descriptions, SHA-256 checksums and consistency checks for the archived result files. These materials have **not** been treated as a successful fresh regeneration of the published experiment. Local Git-tree comparison identified **24 matching result/input filenames** in both repositories, of which **22 are byte-identical Git blobs** (including all same-named CSVs); the **two saved `k=24` PNGs differ**. Neither version was replaced.

**Direct importer compatibility is not established:** `read_series_csv.m` currently looks for `series/<index>.csv` and reads `serie(1,2:end)'`, while upstream datasets live under `orbits-dataset/<index>.csv` and the inspected `0.csv` has the initial-parameter line followed by time samples arranged in **two columns**. Renaming a directory alone will **not** correctly recreate `orbit_series.mat`; a separately validated importer and an identified time-series column would be required. Also, `dynamic_map_phi_1.csv`, `dynamic_map_phi_2.csv`, and `dtw_matrix.mat` are **still absent by those exact filenames** from these repositories. Upstream includes other archived K-Means maps, but they must not be silently substituted as equivalent intermediates.

**Evidence level:** upstream file availability and Git metadata were verified; the upstream archive validator and full MATLAB/PCC/feature-extraction experiments were **not executed** during this documentation change. For a later scientific reproduction, pin this upstream commit, confirm file-to-record/series alignment, and separately pin the PCC/MEX source revision.

## Optional read-only upstream orbit checker

The standalone [`validate_upstream_orbit_inputs.py`](validate_upstream_orbit_inputs.py) verifies input **identity and structure** without changing the original `read_series_csv.m`, `orbit_series.mat` or any scientific output. Only Python's **standard library** is required.

If you already have local checkouts of both repositories:

```bash
# From the fbreve/orbits checkout; adjust the sibling checkout path as needed.
python validate_upstream_orbit_inputs.py ../ts-saturn-orbits/orbits-dataset
python validate_upstream_orbit_inputs.py ../ts-saturn-orbits/orbits-dataset --sample 32 --full-series

# Optional, substantially more I/O: check every orbit's 400 two-column samples.
python validate_upstream_orbit_inputs.py ../ts-saturn-orbits/orbits-dataset --all --full-series
```

The checker always validates **22,288 unique, contiguous orbit identifiers**, matching `file_name` coverage across both saved input maps, consistent finite initial conditions between φ₁ and φ₂, and the complete set of numeric source CSV filenames. By default it opens only **32 deterministically selected** orbit files and validates their **first lines** against map coordinates. `--full-series` checks exactly 400 finite two-column samples in each selected file; `--all` selects **every** source orbit. A header-only sampled success **does not prove** the 400-row structure of unsampled files; a full-series check validates syntax and finite values, **not** agreement with the old binary `orbit_series.mat` or with published model outputs.

The coauthor's phi1 and phi2 feature-extraction scripts respectively select the **first** and **second** columns of the time-series rows, while the first line has two **orbital initial conditions**. The existing local `read_series_csv.m` expects a **different rectangular layout** and must not be used directly on these files.

**Important ordering caveat:** `K-Means_dynamic_map_phi_1_reordered.csv` and `K-Means_dynamic_map_phi_2_reordered.csv` are **lexicographically sorted by `file_name`**, starting `0.csv`, `1.csv`, `10.csv`, `100.csv` ...; the numeric series order `0.csv`, `1.csv`, `2.csv` ... is different. Use identifiers when joining series and maps, not row position. The checker does not reorder or write a replacement `.mat` file.

The [unit tests](tests/test_validate_upstream_orbit_inputs.py) use tiny generated offline fixtures (15 cases). They exercise file coverage, sample selection, row ordering, duplicates, coordinate mismatches, short or malformed time series, and non-finite values. These fixtures can run in CI **without fetching the external 438 MB dataset**. The full external dataset was **not checked end-to-end** by adding this tool.

## Full matrix correspondence audit (November 19, 2026)

A [full GitHub Actions analysis](https://github.com/fbreve/orbits/actions/runs/44546306548) used the coauthor's pinned raw dataset commit `3c0982175952075fabb0257f0954514b0082f89a`. The dataset checkout, 11 offline matrix-analysis tests, full 22,288-file CSV structure/coordinate checks and preserved scientific-file guard **succeeded**. The attempted **raw time-series equivalence gate correctly failed**, because the archived MATLAB matrix contains something different. The [machine-readable report](https://github.com/fbreve/orbits/actions/runs/44546306548/artifacts/14539987690) records the comparison and structural checks.

| Directly checked property | Outcome |
| --- | --- |
| MATLAB variable and shape | `orbit_series`, 22,288 × 400; MATLAB v5-format file |
| Rows with a single repeated value in all 400 columns | **22,288 / 22,288 (exact)** |
| Rows equal to the source-map **initial eccentricity**, in numeric orbit-file order | **22,288 / 22,288 (exact)** |
| Rows equal to the initial semimajor axis, in numeric order | 0 / 22,288 |
| Rows identical to time-series column 1, numeric or saved-map order | 0 / 22,288 |
| Rows identical to time-series column 2, numeric or saved-map order | 0 / 22,288 |
| Correspondence of all restored raw CSV initial coordinates and map IDs | **22,288 / 22,288**, checked with full raw CSV reading |

The repeated eccentricity values are **bitwise equal** to the corresponding decimal-parsed initial eccentricities in the input K-Means maps. This is a complete characterization of the stored numeric matrix, **not** an inference from the first few rows. The current file cannot serve as a faithful `22,288 × 400` time-varying angular-series matrix without generating a **new** data artifact. How the archived matrix obtained this content has **not** been established; its original generator refers to a different, now absent `series/<id>.csv` layout.

**Scope of impact:** `pcc_recluster_series.m` directly loads the diagnosed matrix. `pcc_recluster_series_dtw.m` instead expects an unavailable `dtw_matrix.mat`. The primary `pcc_recluster.m` uses **two orbital coordinates from the saved CSV**, not `orbit_series.mat`; its stored 2D PCC results are not invalidated by this diagnosis. No existing PCC/DTW experiment was rerun, and the publication's larger feature-extraction workflow was not re-executed.

**Meaning of the optional workflow:** the audit's main goal is to **characterize and detect discrepancies in preserved inputs**, not to claim a matched time-series reproduction. A successful audit run means that the known historical repeated-eccentricity structure was verified against the pinned upstream source. A separate explicit `--require-full-match` CLI option remains available to reject the archived matrix as a raw-series substitute. An all-green audit must **never** be described as full scientific reproduction.

To pursue time-series PCC or DTW experiments later, create **new, distinctly named** matrices from each upstream time-series column with their numeric IDs/order recorded, and validate those derived files without overwriting the preserved `orbit_series.mat`.

## Suggested verification gates before scientific rerun

1. **Source identification:** record the exact code commits for `orbits` and the PCC/MEX implementation, and the original sample list/ordering.
2. **Environment:** document MATLAB version, required toolboxes, external PCC version, Gnuplot version, compiler/MEX details and available parallel workers.
3. **Input integrity:** verify expected Git hashes from [`RESEARCH_MANIFEST.csv`](RESEARCH_MANIFEST.csv), then validate CSV row IDs, row counts and class distribution.
4. **Low-cost checks:** run Python stored-label evaluation on a copy and compare the existing confusion matrices and ARI with the archived logs.
5. **Scientific run only with authorization/resources:** start with a tiny diagnostic fixture and progress to the full 100×10 PCC experiment only if the baseline outputs and computation budget warrant it.
6. **Report:** distinguish *manifest integrity*, *stored-output comparison*, *new algorithm execution*, and *replication of published results* as different levels of evidence.


## Full historical MATLAB-matrix correspondence (opt-in)

The newly published source series can be compared with the preserved `orbit_series.mat` using [`validate_orbit_series_correspondence.py`](validate_orbit_series_correspondence.py). This is a **read-only full-data audit**. Unlike the small fixture tests and sampled-input checks above, it parses all **22,288** source orbit files and compares the complete **400-value series** against the named MATLAB variable. It tests both time-series columns (φ₁/φ₂) and both **numeric filename order** and **the stored input-map order**; no channel or ordering is assumed in advance.

```bash
python -m pip install numpy scipy h5py
python validate_orbit_series_correspondence.py \
  --source ../ts-saturn-orbits/orbits-dataset \
  --report orbit-series-matrix-report.json --require-full-match
```

The script checks every raw source orbit's initial parameters against the matching `file_name` entry in the stored maps, requires 400 finite two-column observations in each file, loads the existing `orbit_series` MATLAB variable, and reports **exact-match rows**, **numerically close rows**, and maximum/mean absolute error for each candidate. The numerical criterion uses `abs(diff) <= 1e-8 + 1e-10 * abs(reference)`; it distinguishes this from bitwise equality. A missing full match is **reported as a scientific correspondence gate failure**, not repaired by reordering or modifying the original dataset. It does not establish how the matrix was originally generated, or reproduce the published clustering experiments.

The workflow [`verify-orbit-series-correspondence.yml`](.github/workflows/verify-orbit-series-correspondence.yml) pins Eraldo's dataset commit `3c0982175952075fabb0257f0954514b0082f89a` and can run as a **manual GitHub Actions workflow**. It checks all raw files using a separate sparse checkout (approximately 438 MB of uncompressed CSV content), runs offline fixture tests, and uploads only a small JSON report; no bulk data are added to this repository. The normal, lightweight pull-request regression workflow is unaffected.
