function h = mutual_info(state, x_vars, y_vars, n_chains, n_pred_samples, n_mcmc_iter)
%
% approximate H(Y | X) using n_chains*n_pred_samples predictive samples
%
% input:
%
% state          : an initial crosscat state, e.g. from initialize_from_csv
% x_vars         : a vector of column indices for X (conditioning variables)
% y_vars         : a vector of column indicies for Y (target variables)
% n_chains       : number of mcmc chains to draw samples from
% n_pred_samples : number of predictive samples to draw from each chain
% n_mcmc_iter    : number of mcmc steps to run each mcmc chain for
%

n = n_mcmc*n_pred;

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
        
        indices = x_vars;
        values = s(indices);
        Q = struct('indices', indices, 'values', values);
        p_x = simple_predictive_probability_newRows(state, [], Q);
        
        indices = y_vars;
        values = s(indices);
        Q = struct('indices', indices, 'values', values);
        p_y = simple_predictive_probability_newRows(state, [], Q);
        
        indices = [x_vars, y_vars];
        values = s(indices);
        Q = struct('indices', indices, 'values', values);     
        p_joint = simple_predictive_probability_newRows(state, [], Q);
        
        h = h + log(p_joint) - log(p_x) - log(p_y);
    
    end
end

h = h/n;
