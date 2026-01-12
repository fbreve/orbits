%% Avaliar resultados PCC para phi_1 e phi_2

phis = [1 2];

for phi = phis

    %% Monta nomes de arquivos
    orig_dataset   = sprintf('K-Means_dynamic_map_phi_%d_reordered.csv', phi);
    result_dataset = sprintf('results/K-Means_dynamic_map_phi_%d_reordered_k=24.csv', phi);

    fprintf('=== Avaliando phi_%d ===\n', phi);
    fprintf('Original: %s\n', orig_dataset);
    fprintf('Resultado: %s\n', result_dataset);

    %% Ler CSVs
    Torig   = readtable(orig_dataset);        % semimajor_axis, eccentricity, file_name, cluster_index [file:1][file:2]
    Tresult = readtable(result_dataset);      % mesma estrutura com novos rótulos

    % Coluna 4 = cluster_index; no pipeline original é 0..K-1, converte para 1..K
    orig_label   = table2array(Torig(:,4))   + 1;
    result_label = table2array(Tresult(:,4)) + 1;

    %% Garantir mesmo tamanho
    n = min(numel(orig_label), numel(result_label));
    orig_label   = orig_label(1:n);
    result_label = result_label(1:n);

    %% Quantos foram re-rotulados
    relabeled_count = sum(orig_label ~= result_label);
    fprintf('Total de órbitas (phi_%d): %d\n', phi, n);
    fprintf('Órbitas re-rotuladas (phi_%d): %d (%.4f %%)\n', ...
            phi, relabeled_count, 100*relabeled_count/n);

    %% Matriz de confusão
    C = confusionmat(orig_label, result_label);    % [web:18]
    fprintf('Matriz de confusão phi_%d (linhas = original, colunas = PCC):\n', phi);
    disp(C);

    %% ARI
    ARI = adjustedRandIndex(orig_label, result_label);
    fprintf('Adjusted Rand Index (ARI) phi_%d: %g\n\n', phi, ARI);

    %% Log por phi
    log_filename = sprintf('logs/phi_%d_eval.log', phi);
    fid = fopen(log_filename, 'a');
    if fid ~= -1
        fprintf(fid, '==== Avaliação phi_%d em %s ====\n', phi, datestr(now));
        fprintf(fid, 'Total: %d\n', n);
        fprintf(fid, 'Re-rotuladas: %d (%.4f %%)\n', ...
                relabeled_count, 100*relabeled_count/n);
        fprintf(fid, 'ARI: %g\n', ARI);
        fprintf(fid, 'Matriz de confusão (linhas = original, colunas = PCC):\n');
        fprintf(fid, '%s\n\n', mat2str(C));
        fclose(fid);
    else
        warning('Não foi possível abrir o arquivo de log %s.', log_filename);
    end

end
