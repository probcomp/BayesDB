function h = conditional_entropy(state, given_vars, target_var, n_chains, n_pred_samples, n_mcmc_iter)
%
% approximate H(Y | X) using n_chains*n_pred_samples predictive samples
%
% input:
%
% state          : an initial crosscat state, e.g. from initialize_from_csv
% given_vars     : a vector of column indices for X (conditioning variables)
% target_var     : a column index for Y (target variable)
% n_chains       : number of mcmc chains to draw samples from
% n_pred_samples : number of predictive samples to draw from each chain
% n_mcmc_iter    : number of mcmc steps to run each mcmc chain for
%

n = n_chains*n_pred_samples;

h = 0;

k = 0;
for i = 1:n_chains
    
    state = analyze(state, {'columnPartitionHyperparameter',...
        'columnPartitionAssignments', 'componentHyperparameters',...
        'rowPartitionHyperparameters', 'rowPartitionAssignments'},...
        n_mcmc_iter, 'all', 'all');

    for j = 1:n_pred_samples
        
        k = k + 1;
    
        s = simple_predictive_sample_newRow(state, [], [given_vars target_var]);                                                                              
                
        Y = struct('indices', given_vars, 'values', s(given_vars));
        Q = struct('indices', target_var, 'values', s(target_var));
        p_conditional = simple_predictive_probability_newRows(state, Y, Q);
        
        h = h - log(p_conditional);
    
    end
end

h = h/n;
