function run_crosscat(file_base, experiment)
%
% run mutual information or conditional entropy experiment
%
% input:
%
% file_base  : data set should be in files ../../data/file_base-data.csv 
%              and ../../data/file_base-labels.csv
% experiment : either mutual_info to compute the mutual information for 
%              each pair of columns or conditional_entropy to compute
%              the conditional entropy of the last variable given subsets
%              of the other variables. conditional entropy assumes the 
%              data set has only three columns.

n_chains = 2;
n_pred_samples = 10;
n_mcmc_iter = 10;

addpath ../matlab_code/

data_file = strcat('../../data/', file_base, '-data');
label_file = strcat('../../data/', file_base, '-labels');

state = initialize_from_csv(data_file, label_file, 'fromThePrior');

switch experiment 
case 'mutual_info'
    for i = 1:(state.F - 1)
        for j = (i + 1):state.F
            h = mutual_info(state, i, j, n_chains, n_pred_samples, n_mcmc_iter);
            fprintf(1, '%i, %i, %f', [i, j, h]);
        end
    end
case 'conditional_entropy'
    h = conditional_entropy(state, [1,2], 3, n_chains, n_pred_samples, n_mcmc_iter);
    fprintf(1, 'H(Z|X,Y): %f', h);
end
