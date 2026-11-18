# -*- coding: utf-8 -*-
"""
Created on Mon Jan 12 19:18:08 2026

@author: fbrev
"""

# evaluate_cluster_relabeling.py

import os
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, adjusted_rand_score  # [web:18][web:19]

def validate_row_alignment(original: pd.DataFrame, refined: pd.DataFrame) -> int:
    """Reject comparisons that would silently truncate or misalign orbit records.

    This validates sample identity in the original order; it deliberately
    does not reorder rows, remap cluster IDs, or alter scientific results.
    """
    required = ("file_name", "cluster_index")
    for name, frame in (("original", original), ("refined", refined)):
        missing = [column for column in required if column not in frame.columns]
        if missing:
            raise ValueError(f"{name} CSV lacks required columns: {missing}")
        if frame["file_name"].isna().any():
            raise ValueError(f"{name} CSV has missing orbit identifiers")
        if frame["file_name"].duplicated().any():
            raise ValueError(f"{name} CSV has duplicate orbit identifiers")

    if len(original) != len(refined):
        raise ValueError(
            f"Row count mismatch: original={len(original)}, refined={len(refined)}"
        )

    if not original["file_name"].equals(refined["file_name"]):
        mismatches = (
            original["file_name"].to_numpy() != refined["file_name"].to_numpy()
        )
        first = int(np.flatnonzero(mismatches)[0])
        raise ValueError(
            f"Orbit identifier/order mismatch at data row {first + 1}: "
            f"original={original['file_name'].iloc[first]!r}, "
            f"refined={refined['file_name'].iloc[first]!r}"
        )

    return len(original)


def evaluate_phi(phi: int):
    orig_dataset   = f'K-Means_dynamic_map_phi_{phi}_reordered.csv'
    result_dataset = f'results/K-Means_dynamic_map_phi_{phi}_reordered_k=24.csv'

    print(f'=== Avaliando phi_{phi} ===')
    print(f'Original: {orig_dataset}')
    print(f'Resultado: {result_dataset}')

    # Ler CSVs (colunas: semimajor_axis,eccentricity,file_name,cluster_index)
    Torig   = pd.read_csv(orig_dataset)
    Tresult = pd.read_csv(result_dataset)

    # Check row identities and equal lengths before comparing labels.
    # Unlike the legacy min(length) behavior, never silently truncate.
    n = validate_row_alignment(Torig, Tresult)

    # The existing numerical convention is retained: labels 0..K-1 -> 1..K.
    orig_label   = Torig["cluster_index"].to_numpy(dtype=int) + 1
    result_label = Tresult["cluster_index"].to_numpy(dtype=int) + 1

    # órbitas re-rotuladas
    relabeled = (orig_label != result_label)
    relabeled_count = int(relabeled.sum())
    perc = 100.0 * relabeled_count / n

    print(f'Total de órbitas (phi_{phi}): {n}')
    print(f'Órbitas re-rotuladas (phi_{phi}): {relabeled_count} ({perc:.4f} %)')
    
    # matriz de confusão
    C = confusion_matrix(orig_label, result_label)  # [web:18]
    print(f'Matriz de confusão phi_{phi} (linhas = original, colunas = PCC):')
    print(C)

    # ARI
    ari = adjusted_rand_score(orig_label, result_label)  # [web:19]
    print(f'Adjusted Rand Index (ARI) phi_{phi}: {ari:.6f}\n')

    # log
    os.makedirs('logs', exist_ok=True)
    log_filename = os.path.join('logs', f'phi_{phi}_eval_python.log')
    with open(log_filename, 'a', encoding='utf-8') as f:
        f.write(f'==== Avaliação phi_{phi} em {datetime.now()} ====\n')
        f.write(f'Total: {n}\n')
        f.write(f'Re-rotuladas: {relabeled_count} ({perc:.4f} %)\n')
        f.write(f'ARI: {ari:.6f}\n')
        f.write('Matriz de confusão (linhas = original, colunas = PCC):\n')
        f.write(np.array2string(C) + '\n\n')

if __name__ == '__main__':
    for phi in (1, 2):
        evaluate_phi(phi)
