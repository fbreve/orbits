for phi = 1:2
    data = readtable(sprintf('dynamic_map_phi_%d.csv', phi));
    X = data{:,1:2};

    data = readtable(sprintf('results\\K-Means_dynamic_map_phi_%d_reordered_k=24_softlabels.csv', phi));
    softlabels = data{:,:};

    ENTROPY = -sum(softlabels .* log(softlabels + eps), 2);
    entropy_map = [X ENTROPY];

    writematrix(entropy_map, sprintf('results/entropy_map_phi%d.csv', phi));
end

% % para plotar:
% scatter(X(:,1), X(:,2), 50, ENTROPY, 'filled'); colorbar;