load orbit_series.mat
% dataset name
dataset = 'dynamic_map_phi_1.csv';
X = orbit_series;
clear orbit_series;
% read the dataset and convert it to PCC format
dynamicmap = read_data(dataset);
label = table2array(dynamicmap(:,4)+1);

% set the seed for reproducibility of the folds
rng('default')
% split the dataset in 10 folds with 100 repetitions
n = size(X,1);
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
    graph = pcc_buildgraph(X,k=k,disttype='seuclidean');
    fprintf("Graph generation completed.\n")
    
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