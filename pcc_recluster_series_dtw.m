% dataset name
dataset = 'dynamic_map_phi_1.csv';
% read the dataset and convert it to PCC format
dynamicmap = read_data(dataset);
label = table2array(dynamicmap(:,4)+1);

load dtw_matrix

% set the seed for reproducibility of the folds
rng('default')
% split the dataset in 10 folds with 100 repetitions
n = size(D,1);
for j=1:100
    cv(j) = cvpartition(n,"KFold",10);
end

% create log file
[~, input_filename_no_ext] = fileparts(dataset);
log_filename = "logs\" + input_filename_no_ext + ".log";
fileID = fopen(log_filename,'w');
fclose(fileID);

for k_index=1:10
    % PCC k-nearest neighbors to generate the graph
    k = k_index*5;
    fprintf("Running PCC for k=%d.\n",k)

    tic;    
    % itialize the accumulated domain count
    owndeg_acc = zeros(n,max(label));
    
    % generate the PCC graph
    graph = pcc_buildgraph_dwt(D, k);
    fprintf("Graph generation completed.\n");
    
    % Wait bar implementation
    fprintf('Progress:');
    fprintf(['\n' repmat('.',1,100) '\n\n']);

    % for each repetition and each fold, run PCC and get the accumulated
    % domains. No early stop to get more reliable results.
    parfor j=1:100        
        for i=1:10
            slabel = label .* cv(j).test(i);
            [~, ~, owndeg] = pcc(graph, slabel, maxiter=50000, earlystop=false, Xgraph=true, seed=j, useseed=true);
            owndeg_acc = owndeg_acc + owndeg;
        end
        fprintf('\b|\n');
    end

    % get the new labels
    [~,owner] = max(owndeg_acc,[],2);

    elapsedTime = toc;
    
    % Converte o tempo decorrido em horas, minutos e segundos
    hours = floor(elapsedTime / 3600);
    minutes = floor(mod(elapsedTime, 3600) / 60);
    seconds = mod(elapsedTime, 60);
    time_string = sprintf('Time spent: %d hours, %d minutes and %.2f seconds.\n', hours, minutes, seconds);
    fprintf(time_string);

    % count how many elements were relabeled and show
    relabeled_count = sum(owner ~= label);
    fprintf("Results: k=%d - %d elements re-labeled.\n",k,relabeled_count)
    
    % write log file
    fileID = fopen(log_filename,'a');
    fprintf(fileID,time_string);
    fprintf(fileID,"Results: k=%d - %d elements re-labeled.\n",k,relabeled_count);
    fclose(fileID);

    % write the results to a CSV file   
    output_filename = "results\" + input_filename_no_ext + "_k=" + k + ".csv";
    dynamicmap(:,4) = array2table(owner-1);
    writetable(dynamicmap,output_filename)
end

function pcc_graph = pcc_buildgraph_dwt(D, k)
    n = size(D, 1);
    KNN = zeros(n, k);    

    for i = 1:n
        % Ordenar as distâncias e pegar os índices dos k mais próximos
        [~, sorted_idx] = sort(D(i, :));
        KNN(i, :) = sorted_idx(2:k+1); % Pular o primeiro, que é a própria distância zero
    end

    KNN = uint32(KNN);
    k = uint16(k);

    % make room for reciprocal connections
    KNN(:,end+1:end+k) = 0; 
    % itialize vector holding the amount of neighbors of each node.
    % before the reciprocal connections, all nodes have k neighbors.
    knns = repmat(k,n,1);
    
    for i=1:n
        % adding i as neighbor of its neighbors (creating reciprocity)
        KNN(sub2ind(size(KNN),KNN(i,1:k),(knns(KNN(i,1:k))+1)'))=i; 
        % increasing neighbors counter for nodes that had neighbors added
        knns(KNN(i,1:k))=knns(KNN(i,1:k))+1; 
        % if any node has as many neighbors as the matrix width
        if max(knns)==size(KNN,2)
            % increase the matrix width by 10% + 1
            KNN(:,max(knns)+1:round(max(knns)*1.1)+1) = zeros(n,round(max(knns)*0.1)+1,'uint32');
        end
    end
    % for all nodes
    for i=1:n
        % remove duplicate neighbors
        knnrow = unique(KNN(i,:),'stable'); 
        % update the neighbors amount (and discard the zero at the end)
        knns(i) = size(knnrow,2)-1; 
        % copy the results to the KNN matrix
        KNN(i,1:knns(i)) = knnrow(1:end-1);
        %KNN(i,knns(i)+1:end) = 0; % fill non-used spaces with zero,
        % only for debugging since knns will tell which positions are valid
        % in the list        
    end    
    % eliminating columns without valid neighbors
    KNN = KNN(:,1:max(knns)); 
    % save the matrix of neighbors and the vector of the amount of
    % neighbors in the structure to be returned.
    pcc_graph.KNN = KNN;
    pcc_graph.knns = knns;
    pcc_graph.k = k;
end