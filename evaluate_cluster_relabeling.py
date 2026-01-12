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

def evaluate_phi(phi: int):
    orig_dataset   = f'K-Means_dynamic_map_phi_{phi}_reordered.csv'
    result_dataset = f'results/K-Means_dynamic_map_phi_{phi}_reordered_k=24.csv'

    print(f'=== Avaliando phi_{phi} ===')
    print(f'Original: {orig_dataset}')
    print(f'Resultado: {result_dataset}')

    # Ler CSVs (colunas: semimajor_axis,eccentricity,file_name,cluster_index) [file:1][file:3]
    Torig   = pd.read_csv(orig_dataset)
    Tresult = pd.read_csv(result_dataset)

    # coluna 4 (índice 3) = cluster_index em 0..K-1, converte para 1..K para ficar equivalente ao MATLAB
    orig_label   = Torig.iloc[:, 3].to_numpy(dtype=int) + 1
    result_label = Tresult.iloc[:, 3].to_numpy(dtype=int) + 1

    # garantir mesmo tamanho
    n = min(len(orig_label), len(result_label))
    orig_label   = orig_label[:n]
    result_label = result_label[:n]

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
