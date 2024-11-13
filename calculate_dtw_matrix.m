load orbit_series.mat
X = orbit_series;
clear orbit_series;

n = size(X, 1);
D = zeros(n, n);

% Main parallel loop
for i = 1:n
    parfor j = i+1:n
        D(i,j) = dtw(X(i,:), X(j,:)); % Calculate DTW distance
    end
    if mod(i,10)==0
        fprintf("Passo %d de %d concluído\n",i,n);
    end
end

% Preencher entradas simétricas
for i = 2:n
    for j = 1:i-1
        D(i, j) = D(j, i);
    end
end

save("dtw_matrix","D","-v7.3");

fprintf('Cálculo concluído!\n');
