function run_crosscat(data_dir, file_base, experiment, n_chains, n_pred_samples, ...
    n_mcmc_iter)
%
% run mutual information or conditional entropy experiment
%
% input:
%
% file_base  : data set should be in files ../../data/file_base-data.csv 
%              and ../../data/file_base-labels.csv
% experiment : either correlation to compute the mutual information for 
%              each pair of columns or regression to compute
%              the conditional mutual information of the last variable 
%              and each other predictor given the remaining predictor

n_chains = str2num(n_chains);
n_pred_samples = str2num(n_pred_samples);
n_mcmc_iter = str2num(n_mcmc_iter);

data_file = strcat(data_dir, file_base, '-data');
label_file = strcat(data_dir, file_base, '-labels');

state = initialize_from_csv(data_file, label_file, 'fromThePrior');

switch experiment 
case 'correlation'
    for i = 1:(state.F - 1)
        for j = (i + 1):state.F
            h = mutual_info(state, i, j, [], n_chains, n_pred_samples, n_mcmc_iter);
            fprintf(1, '#####%i, %i,%f#####\n', [i, j, h]);
        end
    end
case 'regression'
    %h = conditional_entropy(state, 1, 3, n_chains, n_pred_samples, n_mcmc_iter);
    %fprintf(1, 'H(Z|X): %f\n', h);
    %h = conditional_entropy(state, 2, 3, n_chains, n_pred_samples, n_mcmc_iter);
    %fprintf(1, 'H(Z|Y): %f\n', h);
    %h = conditional_entropy(state, [1,2], 3, n_chains, n_pred_samples, n_mcmc_iter);
    %fprintf(1, 'H(Z|X,Y): %f\n', h);
    h = mutual_info(state, 1, 3, 2, n_chains, n_pred_samples, n_mcmc_iter);
    fprintf(1, 'I(Z,X|Y): #####%f#####\n', h);
    h = mutual_info(state, 2, 3, 1, n_chains, n_pred_samples, n_mcmc_iter);
    fprintf(1, 'I(Z,Y|X): #####%f#####\n', h);
end
