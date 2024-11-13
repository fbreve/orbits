# -*- coding: utf-8 -*-
"""
Created on Fri Nov  8 15:36:43 2024

@author: fbrev
"""

import csv
from collections import Counter

def reorder_clusters(input_csv, output_csv):
    # Ler o arquivo CSV e armazenar os dados
    with open(input_csv, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)
        dados = [row for row in reader]
    
    # Contar a frequência de cada cluster
    clusters = [row[3] for row in dados]
    frequencias = Counter(clusters)
    
    # Ordenar os clusters pela frequência em ordem decrescente
    clusters_ordenados = [cluster for cluster, _ in frequencias.most_common()]
    
    # Criar o mapa de clusters
    mapa_clusters = {cluster: i for i, cluster in enumerate(clusters_ordenados)}
    
    # Aplicar o mapeamento aos dados
    for row in dados:
        row[3] = mapa_clusters[row[3]]
    
    # Gravar os dados modificados de volta ao arquivo CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)
        writer.writerows(dados)

# Exemplo de uso
input_csv = 'dynamic_map_phi_1.csv'
output_csv = 'dynamic_map_phi_reordered_1.csv'
reorder_clusters(input_csv, output_csv)

input_csv = 'dynamic_map_phi_2.csv'
output_csv = 'dynamic_map_phi_reordered_2.csv'
reorder_clusters(input_csv, output_csv)
