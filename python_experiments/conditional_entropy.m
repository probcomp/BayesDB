function h = conditional_entropy(state, given_vars, target_vars, n_chains, n_pred_samples, n_mcmc_iter)
%
% approximate H(Y | X) using n_chains*n_pred_samples predictive samples
%
% input:
%
% state          : an initial crosscat state, e.g. from initialize_from_csv
% given_vars     : a vector of column indices for X (conditioning variables)
% target_vars    : a vector of column indicies for Y (target variables)
% n_chains       : number of mcmc chains to draw samples from
% n_pred_samples : number of predictive samples to draw from each chain
% n_mcmc_iter    : number of mcmc steps to run each mcmc chain for
%

n = n_mcmc_iter*n_pred_samples;

Y = struct('indices', [], 'values', []);

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
        
        indices = given_vars;
        values = s(indices);
        
        Q = struct('indices', indices, 'values', values);
        
        p_marg = simple_predictive_probability_newRows(state, Y, Q);
        
        indices = [given_vars, target_vars];
        values = s(indices);
        
        Q = struct('indices', indices, 'values', values);
        
        p_joint = simple_predictive_probability_newRows(state, Y, Q);
        
        h = h + log(p_marg/p_joint);
    
    end
end

h = h/n;
