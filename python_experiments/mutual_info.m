function h = mutual_info(state, x_var, y_var, n_chains, n_pred_samples, n_mcmc_iter)
%
% approximate H(Y | X) using n_chains*n_pred_samples predictive samples
%
% input:
%
% state          : an initial crosscat state, e.g. from initialize_from_csv
% x_var          : a column index for X (conditioning variable)
% y_var          : a column index for Y (target variable)
% n_chains       : number of mcmc chains to draw samples from
% n_pred_samples : number of predictive samples to draw from each chain
% n_mcmc_iter    : number of mcmc steps to run each mcmc chain for
%

n = n_mcmc_iter*n_pred_samples;

h = 0;

k = 0;
for i = 1:n_chains
    
    state = analyze(state, {'columnPartitionHyperparameter',...
        'columnPartitionAssignments', 'componentHyperparameters',...
        'rowPartitionHyperparameters', 'rowPartitionAssignments'},...
        n_mcmc_iter, 'all', 'all');

    for j = 1:n_pred_samples
        
        k = k + 1;
    
        s = simple_predictive_sample_newRow(state, [], [1 2]);
        
        Y = struct('indices', [], 'values', []);
        Q = struct('indices', y_var, 'values', s(y_var));
        p_y = simple_predictive_probability_newRows(state, Y, Q);
        
        Y = struct('indices', x_var, 'values', s(x_var));
        Q = struct('indices', y_var, 'values', s(y_var));     
        p_conditional = simple_predictive_probability_newRows(state, Y, Q);
        
        h = h + log(p_conditional) - log(p_y);
    
    end
end

h = h/n;
