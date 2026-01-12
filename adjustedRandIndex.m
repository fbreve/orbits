function ARI = adjustedRandIndex(label, label2)
% label  e label2: vetores de rótulos (mesmo tamanho)

label  = label(:);
label2 = label2(:);

if numel(label) ~= numel(label2)
    error('label e label2 devem ter o mesmo tamanho.');
end

n = numel(label);

% Reetiquetar para rótulos 1..K
[~, ~, g1] = unique(label);
[~, ~, g2] = unique(label2);

k1 = max(g1);
k2 = max(g2);

% Matriz de contingência n_ij usando accumarray (sem for).[web:35][web:37]
Nij = accumarray([g1 g2], 1, [k1 k2]);

% C(n,2) = n*(n-1)/2
comb2 = @(x) x .* (x - 1) / 2;

a       = sum(comb2(Nij(:)));    % soma C(n_ij,2)
rowSums = sum(Nij, 2);
colSums = sum(Nij, 1);

b1 = sum(comb2(rowSums));
b2 = sum(comb2(colSums));
c  = comb2(n);

expected = (b1 * b2) / c;
maxIndex = 0.5 * (b1 + b2);

ARI = (a - expected) / (maxIndex - expected);
end
