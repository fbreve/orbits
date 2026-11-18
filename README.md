# Saturn orbits — PCC-based cluster refinement and results

This repository preserves **MATLAB/Python scripts, intermediate data, figures, logs, and results** associated with the **Outlier Repositioning via Graph Diffusion (ORG-D)** / **Particle Competition and Cooperation (PCC)** refinement stage of the following article:

> **Eraldo Pereira Marinho, Nelson Callegari Junior, Fabricio Aparecido Breve, and Caetano Mazzoni Ranieri.** "Clustering astronomical orbital synthetic data using advanced feature extraction and dimensionality reduction techniques." *Neural Computing and Applications*, **38**, article **340** (2026). Published April 22, 2026. [doi:10.1007/s00521-026-12057-4](https://doi.org/10.1007/s00521-026-12057-4).

[Published article](https://doi.org/10.1007/s00521-026-12057-4) · [arXiv:2603.13177](https://arxiv.org/abs/2603.13177) · [Main feature-extraction/clustering code repository](https://github.com/epmarinho/ts-saturn-orbits) · [Citation metadata](CITATION.cff)

**Scope:** this is a **supplementary research repository** focused on the PCC-based refinement of orbital clusters, plotting, evaluation, and related intermediate results. **It does not independently package the complete feature extraction, dimensionality reduction, clustering, or original orbit simulation pipeline.**

## Scientific context

The study examines **22,288 synthetic orbital time series**, each with **400 time steps**, in Saturn's satellite system. Two resonant angles, **φ₁** and **φ₂**, are analyzed. The larger pipeline generates initial clusters using feature extraction, dimensionality reduction, and clustering. The scripts here investigate the **PCC/ORG-D refinement** of those assignments.

The `K-Means_dynamic_map_phi_{1,2}_reordered.csv` files contain the **initial K-Means-derived cluster assignments** and two orbital-condition coordinates. `pcc_recluster.m` uses these input labels to initialize the PCC process on a graph built from the two coordinates (rather than retraining the original feature extractor).

The `k` in result names such as `_k=24` refers to the **number of nearest neighbors used to build the PCC graph**, **not** the number of target clusters.

## Repository layout

| Path | Contents |
| --- | --- |
| `K-Means_dynamic_map_phi_1_reordered.csv`, `K-Means_dynamic_map_phi_2_reordered.csv` | Initial cluster assignments for φ₁ / φ₂, with coordinates and orbit identifiers |
| `pcc_recluster.m` | Main PCC refinement using 2D orbital coordinates; current script configuration uses `k=24` |
| `pcc_recluster_series.m` | Experimental refinement using the time-series matrix |
| `pcc_recluster_series_dtw.m`, `calculate_dtw_matrix.m` | Experimental DTW-based workflow; additional input generation needed |
| `orbit_series.mat`, `matlab_workspace.mat` | Original MATLAB binary data/workspace files; variable-level contents not independently inspected during this documentation update |
| `results/` | Previously generated cluster maps (CSV/PNG), soft labels and entropy maps |
| `logs/` | Historical execution timings, relabel counts, and cluster-comparison evaluations |
| `evaluate_cluster_relabeling.py`, `.m`, `adjustedRandIndex.m` | Comparing initial and refined partitions using counts, confusion matrices and Adjusted Rand Index |
| `generate_entropy_maps.m`, `plot_map*.gp` | Entropy computation and Gnuplot figures |
| `read_data.m`, `read_series_csv.m`, `reorder_clusters.py` | Input conversion and preparation utilities |
| [`DATA_INVENTORY.md`](DATA_INVENTORY.md) | Description and provenance of the stored inputs/outputs |
| [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) | Required dependencies, missing inputs and execution caveats |
| [`RESEARCH_MANIFEST.csv`](RESEARCH_MANIFEST.csv) | Git object checksums and sizes of the 50 original scientific files |

**Preservation:** the branch [`archive/2026-01-12-results`](https://github.com/fbreve/orbits/tree/archive/2026-01-12-results) is pinned to commit [`dfa5992b810651`](https://github.com/fbreve/orbits/commit/dfa5992b81065164733e441345cf7112407dd7c6) from **January 12, 2026**, before documentation maintenance. It is a frozen GitHub snapshot, **not independently authenticated as the exact runtime or data state of every experiment reported in the 2026 journal publication**.

## Recorded results for `k=24`

The following values are **from the checked-in evaluation logs** dated January 12, 2026. They are preserved observations, **not results re-executed in this documentation update**.

| Metric | φ₁ | φ₂ |
| --- | ---: | ---: |
| Orbit records compared | 22,288 | 22,288 |
| Cluster labels changed | 978 | 998 |
| Percentage changed | 4.3880% | 4.4777% |
| Adjusted Rand Index (ARI) | 0.881361 | 0.875158 |

See `logs/phi_1_eval_python.log` and `logs/phi_2_eval_python.log` for the saved confusion matrices, and the MATLAB logs for recorded execution times.

**Interpretation:** ARI here compares the **initial K-Means partition with the PCC-refined partition**. It measures agreement between clusterings and **is not classification accuracy against ground-truth astronomical labels**.

Other checked-in result files cover `k = 4, 8, 12, 20, 24`. The **current** `pcc_recluster.m` is set to `k=24`; the presence of other outputs does **not** mean this version was rerun for all those configurations.

## Reading and evaluating stored files

For the **stored `k=24` labels**, the Python comparison script can be invoked from the repository root in an environment with `numpy`, `pandas`, and `scikit-learn`:

```bash
python evaluate_cluster_relabeling.py
```

It compares the two original CSVs against `results/K-Means_dynamic_map_phi_{1,2}_reordered_k=24.csv` and prints the relabel counts, confusion matrices and ARI. **Caution:** it appends to `logs/phi_*_eval_python.log`; run it on a separate copy if you want to preserve the archived logs.

The **Python evaluator on this branch** now requires the original and refined tables to have the same length and identical, non-missing, unique `file_name` identifiers in the same order. It stops rather than silently comparing mismatched rows. The separate **MATLAB evaluator still compares by row position and can truncate mismatched lengths**; it has not been changed. See [REPRODUCIBILITY.md](REPRODUCIBILITY.md) and the regression tests in `tests/`.

**Do not launch the long PCC run solely as a documentation check.** The MATLAB simulation uses 100 repetitions of 10 folds, `maxiter=50000`, and disables early stopping. It needs a compatible PCC implementation and a parallel MATLAB environment; the exact historical software configuration is not pinned. See [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Integrity and retention

All original scientific files remain unchanged in the maintained branch. [`RESEARCH_MANIFEST.csv`](RESEARCH_MANIFEST.csv) enumerates each of the 50 scientific files with its **relative path**, **file size**, and **Git blob SHA-1**. Git blob hashes can be checked with:

```bash
git hash-object path/to/file
```

A **Git blob SHA-1 is not an ordinary SHA-1 of file bytes or a SHA-256 checksum**. Binary `.mat` contents were preserved but were not parsed or re-serialized. No experimental data or figures were removed.

## Licensing and data provenance

The repository contains an existing [Apache License 2.0](LICENSE), applicable to source materials covered by the repository's copyright grant. **The license terms and redistribution rights of the underlying coauthor-generated orbit data and any third-party inputs have not been independently established here.** Do not assume that the code license grants rights to all external datasets or tooling.

The journal article is open access under its own **CC BY 4.0** terms, which are distinct from the software and data in this repository.

For scientific citation, use the **2026 journal article**; see [`CITATION.cff`](CITATION.cff).

## Validation status (November 18, 2026)

This maintenance documents and preserves the repository. It **does not claim a successful MATLAB/PCC scientific rerun, re-creation of the figures or experimental validation**. Some legacy/experimental scripts reference absent inputs; their status is documented in [REPRODUCIBILITY.md](REPRODUCIBILITY.md). There is no assertion that the current external code/data repository contains every dataset listed in the published paper.
